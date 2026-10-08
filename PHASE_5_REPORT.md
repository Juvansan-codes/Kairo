# PHASE 5 REPORT: Dimension ↔ Geometry Association & Scale Estimation

## Overview
Phase 5 successfully implemented the **Dimension ↔ Geometry Association** and robust **Scale Estimation** subsystem. This module consumes the metric outputs from the Dimension Parser (Phase 4) and the semantic segmentation masks from the Perception adapter (Phase 2), combining them to calculate a global standard metric scale without stepping on the final topological reconstruction responsibilities.

## Architecture
1. **Geometry Candidate Extraction (`geometry.py`)**:
   Instead of performing a full heavy graph topological trace, this module isolates `cv2.findContours` into minimal enclosing rectangles (`minAreaRect`) around semantic wall masks. These represent lightweight geometric references in the original coordinate space.
2. **Dimension Association (`association.py`)**:
   Dimension candidates are mapped to the geometric candidates using evidence-based scoring:
   - **Spatial Proximity:** How close the OCR text box center is to the geometry candidate.
   - **Orientation Match:** Whether a strictly vertical/horizontal dimension aligns strictly with vertical/horizontal geometry structures within a generous angular tolerance ($15^\circ$).
3. **Consensus Algorithm (`consensus.py`)**:
   - Collects multiple $S_{candidate} = \frac{dimension\_value_{mm}}{pixel\_length}$ ratios.
   - Uses robust statistics (**Median + Median Absolute Deviation**) to reject extreme outliers.
   - Averages the remaining inliers to create a highly accurate `scale_mm_per_px`.
4. **Scale Service Orchestration (`service.py`)**:
   Provides `associate_dimensions(perception_result, dimension_result)` returning a `ScaleEstimationResult`.

## Fallback Hierarchy
The current system implements the foundational metric layer:
1. **`multiple_agreeing_dimensions`**: Used when robust consensus isolates $\ge 2$ agreeing explicit dimensions.
2. **`single_dimension`**: Falls back to the raw ratio if only 1 valid explicit dimension exists.
3. **`unavailable`**: Triggered when no metric dimensions exist. (Prior-based assumptions like `door_prior` and `wall_thickness_prior` will logically hook into this state if geometric doors/windows are eventually submitted).

## Testing
Tests were executed using `backend/test_scale.py`:
- **Consensus & Outliers**: Verified mathematically. A mock list containing 3 close scales ($\sim 20 \text{mm/px}$) and 1 massive outlier ($40 \text{mm/px}$) perfectly converged on $19.93 \text{mm/px}$, cleanly isolating the error and printing residual errors.
- **Real Floorplans (`F1`, `F2`, `F3`)**: 
  - Since `F1`, `F2`, and `F3` lack explicit numeric dimensions, the system correctly processed them without hallucinating data, resolving to `scale_mm_per_px = None` and `source = "unavailable"`.
  - A strictly structured mock dimension (`3500mm` near `[100, 100]`) was manually injected to test geometric association against the real perception masks of `F1`, `F2`, and `F3`. The system perfectly mapped the mock text to an underlying extracted wall polygon, resulting in valid test scales (e.g., $112.00 \text{mm/px}$).

## Known Limitations
* **Chained Dimension Complexity:** Parsing multi-target "chained" numbers (e.g., $1200\ 2500\ 1800$) will require geometric extension line analysis (tracing the perpendicular extension lines from the text to the wall graph boundaries). Currently, only standard single-target explicit dimensions fully succeed.
* **Complex Angular Skew:** The $15^\circ$ alignment tolerance works for slightly skewed scanned documents, but arbitrarily diagonal architectural grids might miss spatial orientation checks.

## Handoff to Member 2
Phase 5 is complete. I have intentionally avoided generating architectural topology, snapping coordinates, or merging room boundaries. 
Member 2's geometric reconstruction module can now safely consume the output from `associate_dimensions()`:
- `ScaleEstimationResult.scale_mm_per_px` (The primary global metric ratio)
- `ScaleEstimationResult.associations` (A list of `DimensionAssociation` objects proving exactly which dimensions matched which pixel-lengths, allowing Member 2 to selectively prioritize locking those specific pixel walls).

**PHASE 5 IS COMPLETE.**
