from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
import pandas as pd
import io
from fastapi.middleware.cors import CORSMiddleware
from core.session_manager import SessionManager
from tools.profiling import extract_metadata
from tools.data_quality import analyze_data_quality
from tools.eda import run_eda

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
    session = manager.get_session(session_id)

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    file_content = await file.read()
    df = pd.read_csv(io.BytesIO(file_content))

    session.raw_dataset = df
    session.working_dataset = df.copy()

    session.metadata = extract_metadata(session.raw_dataset)
    session.data_quality = analyze_data_quality(session.metadata)

    return {
        "session_id": session.session_id,
        "metadata": session.metadata,
        "data_quality": session.data_quality
    }

@app.get("/get_eda")
async def get_eda(request: Request, session_id: str):
    manager = request.app.state.session_manager
    session = manager.get_session(session_id)

    results = run_eda(session.working_dataset, session.metadata, session.data_quality)
    return results

