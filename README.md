# HNX26EPS06 — Floor Plan to Metric 3D Reconstruction

This is the canonical project repository for our hackathon project.

## Purpose

Converting a static architectural floor plan (Mode A) into a topologically consistent, metric-aware 3D representation. Our research contribution is **Metric-Aware Geometric Reconciliation (MGR)**, which fuses neural semantic predictions with explicit geometry and OCR dimension parsing to create robust 3D outputs.

## Tech Stack
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS, shadcn/ui
- **3D Viewer**: Three.js, React Three Fiber, Drei, GLTFLoader
- **Backend**: Python 3.11, FastAPI, Pydantic, uv
- **AI/CV**: Raster2Seq, PaddleOCR, OpenCV
- **Geometry**: Shapely, NetworkX, SciPy
- **3D Generation**: trimesh

## Local Setup

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
# Recommended: use uv for python management
uv venv
source .venv/bin/activate # or .venv\\Scripts\\activate on Windows
uv pip install -e .
uvicorn app.main:app --reload
```

## Repository Structure
- `/frontend`: Next.js web application and 3D viewer
- `/backend`: FastAPI service handling MGR, OCR, perception, and geometry
- `/evaluation`: Ground truth datasets, metrics, and ablation results
- `ARCHITECTURE.md`: Pipeline design
- `API_CONTRACT.md`: Data exchange schema
- `SCHEMA.md`: Shared data structures

## Current Status
- ✅ Project Scaffold created
- ✅ Frontend Next.js initialized
- ✅ FastAPI Backend initialized
- ✅ API Contracts defined
- ⏳ Core MGR and perception engines pending
