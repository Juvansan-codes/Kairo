# API Contract

## Overview
This document defines the HTTP endpoints provided by the FastAPI backend to the Next.js frontend.

### 1. Reconstruct Floorplan
Initiates the reconstruction process.

**Endpoint:** `POST /api/reconstruct`

**Request:**
- `Content-Type: multipart/form-data`
- `file`: The floorplan image (PNG/JPG).

**Response:**
```json
{
  "job_id": "string",
  "status": "processing"
}
```

### 2. Check Status
Checks the status of a reconstruction job.

**Endpoint:** `GET /api/reconstruct/{job_id}`

**Response:**
```json
{
  "job_id": "string",
  "status": "processing | completed | failed"
}
```

### 3. Get Metadata
Retrieves structured statistics about the reconstructed floorplan.

**Endpoint:** `GET /api/result/{job_id}/metadata`

**Response:**
```json
{
  "status": "success",
  "metadata": {
    "rooms": "number",
    "walls": "number",
    "doors": "number",
    "windows": "number",
    "scale_mm_per_px": "number | null"
  }
}
```

### 4. Get Model
Retrieves the generated 3D model.

**Endpoint:** `GET /api/result/{job_id}/model`

**Response:**
Binary GLB file download, or JSON containing the download URL.
```json
{
  "model_url": "string"
}
```

---

## Service Architecture (Member 4 Scaffold)
The backend uses a service boundary approach to separate API/HTTP from ML/Geometry processing:
- **Endpoints (`endpoints.py`)**: API handling and payload schemas.
- **Job Manager (`job_manager.py`)**: Local-storage tracking system for mock async jobs.
- **Reconstruction Service (`reconstruction.py`)**: Orchestrator for future Perception, OCR, Dimension, Geometry and Scene Generation services.
