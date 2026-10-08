# MEMBER 4 - PHASE 7 REPORT: Real Benchmark Dataset Preparation

## Overview
Phase 7 effectively establishes the official **Real-World Benchmark** for the project (`custom_real_v1`). Moving past the mathematical debugging of `custom_synthetic_v1`, this phase organizes and prepares actual, messy uploaded floorplan images for strict human annotation without fabricating any unearned ground-truth. 

## Dataset Structure & Real Sources
The structural framework for the real dataset was fully scaffolded:
- Extracted 5 distinct, real user-uploaded floorplan images from `backend/data/uploads` into `evaluation/datasets/custom_real_v1/` (`real_001.png` - `real_005.png`).
- Fully scaffolded the official `manifest.json` indexing these five images.
- Implemented strict dataset protocol in `evaluation/datasets/custom_real_v1/README.md`.

## Strict Annotation Policy
Because no human has legally/accurately verified the exact coordinate bounds of these 5 uploaded images yet, they have been rigorously marked in `manifest.json` with `"status": "pending"`. 
- **No Fabricated Data**: I did not generate any mock polygons.
- **Workflow Ready**: The dataset relies on the established `evaluation/annotation_guide.md` (via VGG Image Annotator).
- **Validation**: Once humans create `real_001.json`, they will use the existing `validate_ground_truth.py` script to automatically check schema compatibility before officially flipping the manifest status to `"annotated"`.

## Evaluator Compatibility Verified
The evaluation runner (`cli.py` + `manifest.py`) was augmented to natively respect the `"pending"` flag. When executing the final test command:
```bash
python -m evaluation.cli --dataset custom_real_v1 --all-methods
```
The evaluator correctly parsed the manifest, explicitly logged that it recognized the 5 samples as `pending`, and gracefully skipped executing metrics without crashing or substituting zeroes. 

## Status
- **Real Plans Prepared**: 5
- **Annotation Status**: Pending human review.
- **Validation Readiness**: 100% prepared.
- **Evaluator Status**: End-to-end framework fully accepts the dataset and respects the annotation quarantine.

**PHASE 7 IS COMPLETE.** The Evaluation team has finished all infrastructural, statistical, and dataset scaffolding required for the project. Everything currently rests on Member 2 (Geometry) and the final human annotation of `custom_real_v1`!
