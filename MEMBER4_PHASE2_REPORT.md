# MEMBER 4 - PHASE 2 REPORT: Real Pipeline Orchestration & Member 1 Integration

## Overview
Phase 2 effectively replaced the simulated 1-second delay in the `ReconstructionService` with the **real ML-driven Perception, OCR, Dimension Parsing, and Scale Estimation modules** built by Member 1. The FastAPI backend now acts as a genuine data orchestrator moving real floorplans through the AI pipeline, while maintaining clear, strict boundaries for the upcoming Geometry and 3D generation phases.

## Pipeline Orchestration & Architecture
The orchestration happens inside `backend/app/services/reconstruction.py`, driven by asynchronous background tasks spawned directly from the `POST /api/reconstruct` endpoint.

The orchestrator leverages distinct Service classes to abstract implementation:
1. **`PerceptionAnalysisService` (REAL)**: Directly instantiated Member 1 models (`ResNetUNetPerception`, `PaddleOCREngine`, `DimensionVerifier`). Handles image ingestion, neural network predictions, OCR bounding box extraction, metric calculations, and dimension association.
2. **`MockGeometryService` (STUB)**: A placeholder for Member 2. Currently passes through Member 1's semantic mask and dimension data while returning a static `{ "geometry_status": "mock_stub" }` dictionary.
3. **`MockSceneGenerationService` (STUB)**: A placeholder for the final GLB generator. Bypasses actual scene creation and rapidly deposits a dummy `mock glb content (scene generation stub)` file into `backend/data/results/`.

## Member 1 Integration Details
- **Dependency Wrapping**: The complex initialization logic for PyTorch and PaddlePaddle was wrapped neatly inside `backend/app/services/analysis.py`.
- **Stage Tracking**: Job tracking was augmented to record atomic progression: `PREPROCESSING` $\rightarrow$ `PERCEPTION` $\rightarrow$ `OCR` $\rightarrow$ `DIMENSIONS` $\rightarrow$ `SCALE` $\rightarrow$ `GEOMETRY` $\rightarrow$ `3D_GENERATION` $\rightarrow$ `COMPLETED`.
- **Result Schema**: Real, dynamically generated metadata (e.g. wall/door pixel counts, OCR dimension lists, consensus scale values) is successfully propagated out to the `GET /api/result/{job_id}/metadata` endpoint.

## Testing & Timings
I wrote `backend/test_integration.py` to upload and test real floorplan fragments (`F1_extracted.png`, `F2_extracted.png`, `F3_extracted.png`, `empty_test.png`) through the FastAPI stack. 
**Actual Timings via Uvicorn/TestClient:**
- `empty_test.png`: ~4.41s
- `F1_extracted.png`: ~1.20s
- `F2_extracted.png`: ~0.83s
- `F3_extracted.png`: ~0.75s

The original `backend/test_api.py` was also successfully retrofitted to pass an actual `empty_test.png` through the FastAPI pipeline rather than arbitrary bytes, validating existing API constraints.

## Known Limitations & Strict Bounds
- **Raw Tensors**: Currently, the heavy raw boolean NumPy mask array from the Perception model is kept purely in memory between the Perception and Geometry steps. It is not saved to the file system during Job serialization to save immense amounts of I/O throughput. If a server reboot occurs mid-job, the mask is lost.
- **Hardware Bottlenecks**: Analysis is entirely synchronous internally inside the background task queue. The ML instances (`ResNet34-U-Net`) sit resident in memory under the `ReconstructionService`. For a local hackathon environment, this is efficient; for a scaling production cluster, this would need externalized GPU workers (e.g. Celery + Ray).

**PHASE 2 IS COMPLETE.** The backend orchestrates Member 1's completed ML analysis perfectly, exposes the structured JSON data via the frontend API, and is immediately ready to accept Member 2's Geometry engine!
