# Custom Real Benchmark v1 (`custom_real_v1`)

## Overview
This is the official **real-world benchmarking dataset** for the Kairo Floorplan-to-3D project. 

Unlike `custom_synthetic_v1` (which mathematically generates perfect test vectors to debug the metrics engine), `custom_real_v1` contains authentic, messy floorplan imagery uploaded by users or sourced from real architectural documents.

## Dataset Rules
- **No Fabricated Ground Truth**: You may only annotate what is definitively visible and known.
- **Pending Status**: Images are added to `manifest.json` with `"status": "pending"`. Do NOT change this to `"annotated"` or `"validated"` until human review is complete.
- **Frozen Tolerances**: The evaluation parameters (IoU thresholds, geometry tolerances) are frozen to ensure unbiased evaluation.

## Annotation Workflow
We use the lightweight VGG Image Annotator (VIA). Please refer to [`../../annotation_guide.md`](../../annotation_guide.md) for the exact procedure.
Once you export the VIA CSV, convert it into the Pydantic `EvaluationSample` schema and place it in the `evaluation/ground_truth/custom_real_v1/` directory.

## Current Status
- Total images allocated: 5
- Fully annotated: 0
- Validation status: pending
