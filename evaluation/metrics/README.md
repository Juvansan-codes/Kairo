# Metrics Definitions

This document rigorously defines how metrics are computed in the Kairo evaluation suite.

## Layout Metrics

### Wall IoU (Intersection over Union)
- **Input**: Predicted wall polygons vs Ground-truth wall polygons.
- **Mathematical Definition**: Area of Intersection / Area of Union between the combined rasterized wall mask of prediction and ground truth.
- **Matching Method**: Handled implicitly by comparing the rasterized binary masks of all walls simultaneously (spatial overlap).
- **Edge Cases**: Empty predictions return `0.0`. Missing ground truth returns `null`.
- **Units**: Ratio (0.0 to 1.0).
- **Output Range**: [0.0, 1.0]

### Room IoU
- **Input**: Predicted room polygons vs Ground-truth room polygons.
- **Mathematical Definition**: Averaged IoU across all matched room instances.
- **Matching Method**: Bipartite matching (Hungarian algorithm) based on maximum IoU overlap > 0.5.
- **Edge Cases**: Non-matched predictions penalize precision. Non-matched GT penalize recall.
- **Units**: Ratio (0.0 to 1.0).
- **Output Range**: [0.0, 1.0]

## Completeness Metrics

### Room / Door / Window Recall
- **Input**: Predicted entities vs GT entities.
- **Mathematical Definition**: True Positives / (True Positives + False Negatives).
- **Matching Method**: Bipartite matching. Positives are matches with IoU > 0.5.
- **Edge Cases**: 0 GT instances returns `null` (not applicable).
- **Units**: Ratio (0.0 to 1.0).
- **Output Range**: [0.0, 1.0]

## Dimension Metrics

### Absolute Dimension Error
- **Input**: Explicit numerical dimensions parsed from OCR vs GT explicit dimensions.
- **Mathematical Definition**: Mean of `|Predicted_mm - GT_mm|`.
- **Matching Method**: Nearest neighbor bounding box distance.
- **Edge Cases**: No GT dimensions -> `null`.
- **Units**: Millimeters (mm).
- **Output Range**: [0, infinity)

### Relative Dimension Error
- **Input**: Explicit numerical dimensions.
- **Mathematical Definition**: Mean of `|Predicted_mm - GT_mm| / GT_mm`.
- **Units**: Ratio / Percentage.
- **Output Range**: [0.0, infinity)

## System Metrics
- **Inference Time**: Measured in seconds per floorplan from image ingestion to final JSON/GLB output.
- **Success Rate**: % of floorplans that successfully complete the pipeline without throwing an unhandled exception.
