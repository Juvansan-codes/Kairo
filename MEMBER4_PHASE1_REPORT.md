# MEMBER 4 - PHASE 1 REPORT: Backend & API Foundation

## Overview
Phase 1 successfully established the **FastAPI Backend Foundation** for the Kairo Floorplan-to-3D pipeline. This module serves as the primary orchestrator, providing clean, schema-compliant REST API endpoints to the frontend, isolating HTTP constraints from the heavy machine learning processes.

## Files Created & Changed
- `backend/app/main.py`: Configured the core FastAPI application, CORS middleware, and `/health` route.
- `backend/app/api/endpoints.py`: Built out the HTTP routes following `API_CONTRACT.md`. Includes strict request validation for allowed file formats (PNG, JPG, PDF) and proper `HTTPException` error handling.
- `backend/app/models/api_schemas.py`: Defined clean `Pydantic` request/response schemas to enforce structural guarantees between client and server.
- `backend/app/services/job_manager.py`: Implemented a localized, file-based storage paradigm that tracks job states in memory and saves artifacts to `backend/data/uploads` and `backend/data/results`. 
- `backend/app/services/reconstruction.py`: Scaffolded the asynchronous orchestrator (`ReconstructionService`) which manages background tasks and creates mock output for downstream testing.
- `backend/test_api.py`: Comprehensive test suite leveraging `fastapi.testclient.TestClient`.
- `API_CONTRACT.md`: Appended brief service architecture documentation.

## API Endpoints Implemented
- `GET /health` $\rightarrow$ Simple liveness check.
- `POST /api/reconstruct` $\rightarrow$ Uploads an image, creates a tracked Job ID, and spins off the reconstruction process asynchronously via `BackgroundTasks`.
- `GET /api/reconstruct/{job_id}` $\rightarrow$ Polling endpoint for checking job state (`queued`, `processing`, `completed`, `failed`).
- `GET /api/result/{job_id}/metadata` $\rightarrow$ Returns the structured output details of the reconstruction.
- `GET /api/result/{job_id}/model` $\rightarrow$ Streams the `.glb` model payload back to the client.

## Data Storage & Job State
To keep the application lightweight without distributed infrastructure overhead (e.g., Redis, Celery), Jobs are tracked via an in-memory dictionary mapped to a dedicated file system:
- Uploads: `backend/data/uploads/{job_id}.{ext}`
- Results: `backend/data/results/{job_id}.glb`
The jobs natively cycle through states allowing the frontend to poll synchronously while ML runs asynchronously.

## Testing Performed
Executed `python backend/test_api.py`.
- **Health Check**: Server returns `{"status": "ok"}`
- **File Validation**: Correctly rejected a `.txt` upload with a `400` status.
- **Reconstruction Flow**: Standard `POST` created an ID. Background worker transitioned ID from `processing` to `completed`.
- **Metadata/Model Fetch**: Both successfully returned mock payloads.
- **Missing Jobs**: Correctly returned a `404` status.

## How to Run
Navigate to the root directory and start the Uvicorn server:
```bash
$env:PYTHONPATH="$(pwd)"
cd backend
..\backend\.venv\Scripts\uvicorn app.main:app --reload
```
The Swagger UI will be automatically available at: `http://localhost:8000/docs`.

## Known Limitations & Future Integration
- **Mocks only**: The `ReconstructionService` simply sleeps for 1 second and then generates placeholder data. It does NOT invoke Member 1's AI/OCR stack or Member 2's Geometry generation yet.
- **In-memory Persistence**: Restarting the server wipes out knowledge of old jobs. For a hackathon, this is perfectly acceptable, but if production persistence is required, the `JOBS` dictionary can simply be swapped for a SQLite hook without altering the rest of the application interface.
- **No Rate Limiting**: The upload limits rely on internal Uvicorn bounds.

**PHASE 1 IS COMPLETE.** All teammate files (Member 1, Member 2, Member 3) were strictly preserved and isolated.
