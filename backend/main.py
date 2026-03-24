from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
import pandas as pd
import io
from fastapi.middleware.cors import CORSMiddleware
from core.session_manager import SessionManager
from tools.profiling import extract_metadata
from tools.data_quality import analyze_data_quality
from tools.eda import run_full_analysis

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
async def get_full_analysis(request: Request, session_id: str, refresh: bool = False):
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
            session.data_quality
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    session.analysis_cache = results
    return results
