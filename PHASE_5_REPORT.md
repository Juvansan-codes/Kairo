# Research Phase 5: Human Annotation Workspace

## A. Annotation Workspace

Exact files created/changed:
- Created: `evaluation/annotation/index.html` (Standalone Zero-Dependency UI Workspace)

The workspace is a plain HTML/JS application built entirely on standard browser APIs. It imposes zero complex framework dependencies and requires no server-side processing for drawing or exporting, perfectly preserving benchmark independence.

## B. Launch Instructions

To use the annotation tool, serve the repository locally to bypass browser CORS restrictions for local imagery:

```bash
cd "d:\College Files\Kairo"
python -m http.server 8000
```
Then open in any modern browser:
[http://localhost:8000/evaluation/annotation/index.html](http://localhost:8000/evaluation/annotation/index.html)

## C. Supported Annotation Types

The tool supports all explicit geometric elements safely mapped to the evaluation metric system:
* **walls**: Polylines/line segments mapped directly to `geometry`.
* **rooms**: Closed polygons generated via multiple clicks.
* **doors**: Explicit 2-point rectangles mathematically expanded to 4-point closed polygons.
* **windows**: Explicit 2-point rectangles mathematically expanded to 4-point closed polygons.
* **dimensions**: Explicit form input enforcing visible, legible metrics (mm/cm/m), skipping arbitrary spatial estimation.

## D. Coordinate Validation

The workspace guarantees coordinate safety mathematically. If a human resizes their browser window or zooms, the displayed floorplan scales visually, which would normally distort clicked positions. 

To prevent this, the workspace computes an inverse display scale matrix dynamically using the image's inherent `naturalWidth` vs its CSS `clientWidth`:
```javascript
const scaleX = img.naturalWidth / img.clientWidth;
const scaleY = img.naturalHeight / img.clientHeight;

const x = (evt.clientX - rect.left) * scaleX;
const y = (evt.clientY - rect.top) * scaleY;
```
This guarantees that the point saved in the JSON is perfectly mapped back to the original `origin=top-left` image coordinate space, completely eliminating drift or scaling corruption.

## E. Export Format

When the human clicks "Export JSON", the browser downloads a raw text file matching the exact strictly-typed `GroundTruth` Pydantic structure required by the evaluator:

```json
{
  "id": "real_001",
  "walls": [
    {
      "id": "W1",
      "geometry": [[10.0, 10.0], [100.0, 10.0]]
    }
  ],
  "rooms": [
    {
      "id": "R1",
      "polygon": [[10.0, 10.0], [100.0, 10.0], [100.0, 100.0], [10.0, 100.0]]
    }
  ],
  "doors": [
    {
      "id": "D1",
      "polygon": [[40.0, 5.0], [60.0, 5.0], [60.0, 15.0], [40.0, 15.0]]
    }
  ],
  "windows": [],
  "dimensions": [
    {
      "id": "Dim1",
      "value_mm": 2000.0
    }
  ],
  "scale_mm_per_px": null
}
```

## F. Validation

Validation test results confirm:
1. Coordinates are properly stored as floats mirroring the true resolution of the image.
2. Output JSON structures identically match the evaluation schema.
3. Supplying an exported sample to `validate_ground_truth.py` confirms that the polygons correctly close, areas are non-zero, and structures do not cause the evaluator to exception or halt.

## G. Privacy / Git Status

* **Annotation Tool**: The `index.html` tool itself is safe and trackable via Git.
* **Floorplan Images**: `real_001.png` — `real_005.png` are classified as **Private / Local Data** and should NOT be tracked or pushed unless the research team has explicit copyright clearance to host them publicly.
* **Ground Truth JSONs**: Correspondingly private until cleared.
* **Rule**: Never use `git add .` to prevent accidental inclusion of the private real-world batch.

## H. Human Action Required

The human operator must now manually annotate:
* `real_001`
* `real_002`
* `real_003`
* `real_004`
* `real_005`

Do not claim the benchmark is annotated until this is accomplished. Once you have saved the downloaded JSON files into `evaluation/ground_truth/custom_real_v1/`, run the `validate_ground_truth.py` script. Only if they pass, manually change their status to `"annotated"` in `manifest.json`.

## I. Research Status

* **Real benchmark annotations**: 0/5
* **Real benchmark metrics**: unavailable
* **Comparative real-world claims**: not yet proven

The local environment is entirely ready. Await human annotation for Phase 6.
