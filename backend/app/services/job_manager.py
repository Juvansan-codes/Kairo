import os
import json
import uuid
from typing import Dict, Optional, Any
from fastapi import UploadFile

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads")
RESULT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "results")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

class Job:
    def __init__(self, job_id: str, status: str = "queued", stage: str = "PREPROCESSING"):
        self.job_id = job_id
        self.status = status
        self.stage = stage
        self.file_path: Optional[str] = None
        self.metadata: Optional[Dict[str, Any]] = None
        self.model_path: Optional[str] = None

# Simple in-memory mock store
JOBS: Dict[str, Job] = {}

class JobManager:
    @staticmethod
    def create_job() -> Job:
        job_id = str(uuid.uuid4())
        job = Job(job_id)
        JOBS[job_id] = job
        return job

    @staticmethod
    def get_job(job_id: str) -> Optional[Job]:
        return JOBS.get(job_id)

    @staticmethod
    async def save_upload(job_id: str, file: UploadFile) -> str:
        ext = file.filename.split('.')[-1]
        file_path = os.path.join(UPLOAD_DIR, f"{job_id}.{ext}")
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        job = JOBS[job_id]
        job.file_path = file_path
        return file_path

    @staticmethod
    def save_result(job_id: str, metadata: dict, model_path: str):
        job = JOBS.get(job_id)
        if not job:
            return
            
        job.metadata = metadata
        job.model_path = model_path
        job.status = "completed"
        job.stage = "COMPLETED"
