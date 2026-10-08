from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uuid

app = FastAPI(title="Metric-Aware Geometric Reconciliation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/api/reconstruct")
async def reconstruct(file: UploadFile = File(...)):
    # Mock reconstruction endpoint
    job_id = str(uuid.uuid4())
    return {"job_id": job_id, "status": "processing"}

@app.get("/api/reconstruct/{job_id}")
def get_reconstruct_status(job_id: str):
    # Mock status endpoint
    return {"job_id": job_id, "status": "completed"}

@app.get("/api/result/{job_id}/metadata")
def get_metadata(job_id: str):
    # Mock metadata response
    return {
        "status": "success",
        "metadata": {
            "rooms": 2,
            "walls": 8,
            "doors": 2,
            "windows": 3,
            "scale_mm_per_px": 19.82
        }
    }

@app.get("/api/result/{job_id}/model")
def get_model(job_id: str):
    # This would return a GLB file. Mocking a FileResponse or direct download URL
    return {"model_url": f"/mock-model-{job_id}.glb"}
