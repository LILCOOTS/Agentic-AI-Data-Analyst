from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
import pandas as pd
import io
from fastapi.middleware.cors import CORSMiddleware
from core.session_manager import SessionManager
from tools.profiling import extract_metadata
from tools.data_quality import analyze_data_quality
from tools.eda import run_full_analysis
from tools.data_cleaning import generate_cleaning_action_report
from tools.apply_cleaning import apply_cleaning
from tools.modeling import run_modeling

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.state.session_manager = SessionManager()


@app.get("/")
async def home():
    return "Welcome to AI Analyst"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/create_session")
async def create_session(request: Request):
    manager = request.app.state.session_manager
    session_id = manager.create_session()
    return {"session_id": session_id}


@app.get("/get_sessions")
async def get_sessions(request: Request):
    manager = request.app.state.session_manager
    return manager.get_all_sessions()


@app.post("/upload_dataset")
async def upload_dataset(
    request: Request,
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    manager = request.app.state.session_manager

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
    manager = request.app.state.session_manager
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
    manager = request.app.state.session_manager
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
    manager = request.app.state.session_manager
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Modeling failed: {str(e)}")

    return {
        "session_id":       session.session_id,
        "problem_type":     results["problem_type"],
        "target_column":    target_col,
        "metric_name":      results["metric_name"],
        "metric_value":     results["metric_value"],
        "extra_metrics":    results["extra_metrics"],
        "rows_trained":     results["rows_trained"],
        "rows_tested":      results["rows_tested"],
        "n_features":       results["n_features"],
        "feature_importance": results["feature_importance"],  # list of dicts, JSON-safe
    }
