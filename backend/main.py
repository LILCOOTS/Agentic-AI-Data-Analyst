from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import os
import json
from fastapi.middleware.cors import CORSMiddleware
from core.session_manager import SessionManager, session_manager
from tools.profiling import extract_metadata
from tools.data_quality import analyze_data_quality
from tools.eda import run_full_analysis
from tools.data_cleaning import generate_cleaning_action_report
from tools.apply_cleaning import apply_cleaning
from tools.modeling import run_modeling
from agents.graph import agent, get_thread_config, create_initial_state, create_followup_state

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Setup Templates & Static Assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# session_manager is the module-level singleton from core/session_manager.py
# app.state still holds a reference for any future middleware that needs it
app.state.session_manager = session_manager

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/create_session")
async def create_session(request: Request):
    manager = session_manager
    session_id = manager.create_session()
    return {"session_id": session_id}


@app.get("/get_sessions")
async def get_sessions(request: Request):
    manager = session_manager
    return manager.get_all_sessions()


@app.post("/upload_dataset")
async def upload_dataset(
    request: Request,
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    manager = session_manager

    # Clean 404 if session doesn't exist (get_session raises HTTPException already)
    session = manager.get_session(session_id)

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    try:
        file_content = await file.read()
        df = pd.read_csv(io.BytesIO(file_content))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse CSV: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=422, detail="Uploaded CSV is empty.")

    session.raw_dataset = df
    session.working_dataset = df.copy()
    session.metadata = extract_metadata(session.raw_dataset)
    session.data_quality = analyze_data_quality(session.metadata)

    # Bust stale analysis cache when a new dataset is uploaded
    session.analysis_cache = None

    return {
        "session_id": session.session_id,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "metadata": session.metadata,
        "data_quality": session.data_quality
    }


@app.get("/get_full_analysis")
async def get_full_analysis(request: Request, session_id: str, refresh: bool = False, target_col: str = None):
    manager = session_manager
    session = manager.get_session(session_id)

    if session.working_dataset is None:
        raise HTTPException(
            status_code=400,
            detail="No dataset uploaded for this session. Call /upload_dataset first."
        )

    # Return cached result unless caller explicitly asks for a refresh
    if session.analysis_cache is not None and not refresh:
        return session.analysis_cache

    try:
        results = run_full_analysis(
            session.working_dataset,
            session.metadata,
            session.data_quality,
            forced_target=target_col
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    session.analysis_cache = results
    return results

@app.post("/cleaning")
async def cleaning(request: Request, session_id: str, target_col: str = None):
    manager = session_manager
    session = manager.get_session(session_id)

    if session.working_dataset is None:
        raise HTTPException(
            status_code=400,
            detail="No dataset uploaded for this session. Call /upload_dataset first."
        )

    if not target_col and session.analysis_cache and "selected_columns" in session.analysis_cache:
        target_col = session.analysis_cache["selected_columns"].get("target_column")

    try:
        actions = generate_cleaning_action_report(session.metadata, session.data_quality, target_col=target_col)
        cleaned_df, cleaning_log = apply_cleaning(session.raw_dataset, actions)

        session.working_dataset = cleaned_df
        session.metadata = extract_metadata(cleaned_df)
        session.data_quality = analyze_data_quality(session.metadata)
        session.analysis_cache = None  # bust cache — data changed

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleaning failed: {str(e)}")

    return {
        "session_id": session.session_id,
        "rows_before": int(session.raw_dataset.shape[0]),
        "rows_after": int(cleaned_df.shape[0]),
        "columns_before": int(session.raw_dataset.shape[1]),
        "columns_after": int(cleaned_df.shape[1]),
        "cleaning_log": cleaning_log,
        "actions_applied": len([l for l in cleaning_log if l["status"] not in ("skipped — already removed",)]),
        "metadata": session.metadata,
        "data_quality": session.data_quality
    }

@app.post("/modeling")
def modeling(request: Request, session_id: str):
    manager = session_manager
    session = manager.get_session(session_id)

    if session.working_dataset is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded. Call /upload_dataset first.")

    if not session.analysis_cache or "selected_columns" not in session.analysis_cache:
        raise HTTPException(status_code=400, detail="No analysis found. Call /get_full_analysis first.")

    selected   = session.analysis_cache["selected_columns"]
    target_col = selected.get("target_column")
    prob_type  = selected.get("problem_type")

    if not target_col:
        raise HTTPException(status_code=400, detail="No target column detected. Check /get_full_analysis output.")

    try:
        results = run_modeling(session.working_dataset, target_col, prob_type)
        # Store fitted model objects in session for predict_instance tool
        session.modelling_results = results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Modeling failed: {str(e)}")

    return {
        "session_id":       session.session_id,
        "problem_type":     results.get("problem_type"),
        "target_column":    target_col,
        "model_architecture": results.get("model_architecture"),
        "best_model":       results.get("best_model"),
        "metric_name":      results.get("metric_name"),
        "metric_value":     results.get("metric_value"),
        "cv_score_mean":    results.get("cv_score_mean"),
        "cv_score_std":     results.get("cv_score_std"),
        "extra_metrics":    results.get("extra_metrics"),
        "models_performance": results.get("models_performance"),
        "rows_trained":     results.get("rows_trained"),
        "rows_tested":      results.get("rows_tested"),
        "n_features":       results.get("n_features"),
        "feature_importance_source": results.get("feature_importance_source"),
        "feature_importance": results.get("feature_importance"),
    }


# ── Agent / Chat Endpoints ────────────────────────────────────────────────────
#
# KEY CONCEPT — Server-Sent Events (SSE):
#   HTTP normally works request → response (done). SSE keeps the connection
#   open and the server pushes lines in this format:
#       data: {"type": "token", "content": "Training"}
#       (blank line)     ← signals end of one event
#   The browser uses EventSource API to listen to these events.
#   We use StreamingResponse with media_type="text/event-stream".
#
# KEY CONCEPT — astream_events(version="v2"):
#   Async generator that fires a dict for every internal LangGraph event.
#   We filter for "on_chat_model_stream" events WHERE the node is "synthesizer"
#   to get token-by-token output from only the response LLM, not the Planner.
#
# KEY CONCEPT — Interrupt detection:
#   After astream_events() ends, we call agent.get_state(config).
#   If snapshot.next is non-empty, the graph paused at a NodeInterrupt.
#   The interrupt message lives in snapshot.tasks[n].interrupts[m].value.


def _build_dataset_metadata(session) -> dict:
    """Assembles the metadata dict the Planner's prompt needs from session objects."""
    meta     = session.metadata or {}
    analysis = session.analysis_cache or {}
    selected = analysis.get("selected_columns", {})
    return {
        "columns":       meta.get("columns", []),
        "target_column": selected.get("target_column"),
        "problem_type":  selected.get("problem_type"),
        "num_rows":      meta.get("num_rows", 0),
        "num_columns":   meta.get("num_columns", 0),
    }


def _sse(payload: dict) -> str:
    """Format a dict as a single SSE event line."""
    return f"data: {json.dumps(payload)}\n\n"


@app.post("/chat")
async def chat(request: Request):
    """
    Main chat endpoint. Streams the agent's response token-by-token via SSE.
    On destructive actions (clean/model), the stream ends with a
    'confirmation_required' event instead of 'done'.
    """
    body       = await request.json()
    session_id = body.get("session_id", "").strip()
    message    = body.get("message", "").strip()

    if not session_id or not message:
        raise HTTPException(status_code=400, detail="session_id and message are required.")

    try:
        session = session_manager.get_session(session_id)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Session not found. Upload a dataset first.")

    config   = get_thread_config(session_id)
    metadata = _build_dataset_metadata(session)

    # Decide initial vs follow-up state ──────────────────────────────────────
    # get_state returns a snapshot; if .values is empty, this is the first message
    existing = agent.get_state(config)
    if existing.values:
        state_input = create_followup_state(message)
        # Always refresh metadata so Planner sees latest cleaning/modeling state
        state_input["dataset_metadata"] = metadata
        state_input["analysis_cache"]   = session.analysis_cache
    else:
        state_input = create_initial_state(
            session_id, message, metadata, session.analysis_cache
        )

    async def generate():
        try:
            async for event in agent.astream_events(
                state_input, config=config, version="v2"
            ):
                # Only stream tokens from the Synthesizer — not the Planner LLM
                if (
                    event["event"] == "on_chat_model_stream"
                    and event.get("metadata", {}).get("langgraph_node") == "synthesizer"
                ):
                    chunk = event["data"].get("chunk")
                    if chunk and getattr(chunk, "content", None):
                        yield _sse({"type": "token", "content": chunk.content})

        except Exception as e:
            yield _sse({"type": "error", "message": str(e)})
            return

        # After stream ends — check if graph paused at a NodeInterrupt ────────
        snapshot = agent.get_state(config)
        if snapshot.next:  # non-empty → graph is paused
            interrupt_msg = "Please confirm this action."
            interrupt_action = ""
            try:
                for task in snapshot.tasks:
                    for intr in getattr(task, "interrupts", []):
                        interrupt_msg    = intr.value
                        interrupt_action = snapshot.values.get("planned_action", "")
                        break
            except Exception:
                pass
            yield _sse({
                "type":    "confirmation_required",
                "message": interrupt_msg,
                "action":  interrupt_action,
            })
        else:
            final  = snapshot.values.get("final_response", "")
            action = snapshot.values.get("planned_action", "")
            yield _sse({
                "type":           "done",
                "response":       final,
                "action":         action,
                "refresh_needed": action in ("run_clean", "profile"),
                "model_updated":  action == "run_model",
            })

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/chat/confirm")
async def chat_confirm(request: Request):
    """
    Resume or cancel a paused agent graph.

    KEY CONCEPT — Resume after NodeInterrupt:
        Passing None as state_input tells LangGraph:
        "Don't create new state — read from the checkpointer and continue."
        The graph picks up exactly at the Executor node (right after Critic).

    Cancellation:
        We use agent.update_state() to write a final_response directly into
        the checkpoint, then the graph stays paused (no resume).
    """
    body       = await request.json()
    session_id = body.get("session_id", "").strip()
    confirmed  = body.get("confirmed", True)

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")

    config = get_thread_config(session_id)

    # ── Cancelled ─────────────────────────────────────────────────────────────
    if not confirmed:
        cancel_msg = "❌ Action cancelled. Nothing was changed."
        agent.update_state(
            config,
            {"final_response": cancel_msg, "planned_action": "answer"},
            as_node="synthesizer",
        )
        return {"type": "cancelled", "response": cancel_msg}

    # ── Confirmed — resume the graph ──────────────────────────────────────────
    # CRITICAL: set confirmed=True in the checkpoint BEFORE resuming.
    # When astream_events(None) replays the Critic, it reads confirmed=True
    # and returns {} instead of raising NodeInterrupt again.
    agent.update_state(config, {"confirmed": True})

    async def generate():
        try:
            # None input = continue from checkpoint, don't inject new state
            async for event in agent.astream_events(
                None, config=config, version="v2"
            ):
                if (
                    event["event"] == "on_chat_model_stream"
                    and event.get("metadata", {}).get("langgraph_node") == "synthesizer"
                ):
                    chunk = event["data"].get("chunk")
                    if chunk and getattr(chunk, "content", None):
                        yield _sse({"type": "token", "content": chunk.content})

        except Exception as e:
            yield _sse({"type": "error", "message": str(e)})
            return

        snapshot = agent.get_state(config)
        final  = snapshot.values.get("final_response", "")
        action = snapshot.values.get("planned_action", "")
        yield _sse({
            "type":           "done",
            "response":       final,
            "action":         action,
            "refresh_needed": action in ("run_clean", "profile"),
            "model_updated":  action == "run_model",
        })

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
