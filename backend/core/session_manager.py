import uuid
from datetime import datetime
from fastapi import HTTPException

class Session:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.raw_dataset = None
        self.working_dataset = None
        self.metadata = None
        self.data_quality = None
        self.profiling_results = None
        self.cleaning_log = []
        self.target_info = None
        self.modelling_results = None
        self.insights_history = []

class SessionManager:
    def __init__(self):
        self.session_store = {}

    def create_session(self):
        session = Session()
        self.session_store[session.session_id] = session
        return session.session_id
    
    def get_session(self, session_id):
        if session_id in self.session_store:
            return self.session_store[session_id]
        raise HTTPException(status_code=404, detail="Session not found")

    def delete_session(self, session_id):
        if session_id in self.session_store:
            del self.session_store[session_id]
        raise HTTPException(status_code=404, detail="Session not found")
    
    def get_all_sessions(self):
        return self.session_store
