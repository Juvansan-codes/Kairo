from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    stage: str

class MetadataResponse(BaseModel):
    status: str
    metadata: Dict[str, Any]

class ModelResponse(BaseModel):
    model_url: str

class HealthResponse(BaseModel):
    status: str
