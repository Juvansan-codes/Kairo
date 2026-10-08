from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from ..models.api_schemas import JobStatusResponse, MetadataResponse, ModelResponse
from ..services.job_manager import JobManager
from ..services.reconstruction import ReconstructionService
import os

router = APIRouter()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

def validate_file(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    ext = file.filename.split('.')[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")
        
    # We could also check file size, but relying on server limits is okay for now.

@router.post("/reconstruct", response_model=JobStatusResponse)
async def reconstruct(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    validate_file(file)
    
    job = JobManager.create_job()
    await JobManager.save_upload(job.job_id, file)
    
    # Run the reconstruction asynchronously
    background_tasks.add_task(ReconstructionService.reconstruct, job.job_id)
    
    return {"job_id": job.job_id, "status": job.status, "stage": job.stage}

@router.get("/reconstruct/{job_id}", response_model=JobStatusResponse)
def get_reconstruct_status(job_id: str):
    job = JobManager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {"job_id": job.job_id, "status": job.status, "stage": job.stage}

@router.get("/result/{job_id}/metadata", response_model=MetadataResponse)
def get_metadata(job_id: str):
    job = JobManager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status == "failed":
        return {
            "status": "failed",
            "metadata": job.metadata or {"error": "Unknown error"}
        }
        
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Reconstruction not yet completed")
        
    if not job.metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")
        
    return {
        "status": "success",
        "metadata": job.metadata
    }

@router.get("/result/{job_id}/model")
def get_model(job_id: str):
    job = JobManager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Reconstruction not yet completed")
        
    if not job.model_path or not os.path.exists(job.model_path):
        raise HTTPException(status_code=404, detail="Model file not found")
        
    return FileResponse(job.model_path, media_type="model/gltf-binary", filename=f"reconstruction_{job_id}.glb")
