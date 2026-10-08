# PHASE 3 REPORT: OCR Engine

## OCR Engine Definition
*   **System Used**: `PaddleOCR` (via `paddlepaddle` CPU)
*   **Version**: 3.7.x
*   **Interface**: Defined `OCREngine` abstract class and a `PaddleOCREngine` implementation in `backend/app/ocr/engine.py`.
*   **Input**: Normalized floorplan image (or direct image path).
*   **Output Structure** (following `SCHEMA.md` format):
    ```json
    {
      "text_regions": [
        {
          "text": "10'-0\"",
          "bbox": [x, y, w, h],
          "polygon": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
          "confidence": 0.98,
          "orientation": 0.0,
          "hint": "numeric_like",
          "provenance": {"engine": "paddleocr"}
        }
      ]
    }
    ```

## Testing Performed
*   **Test Script**: `backend/test_ocr.py`
*   **Initialization**: Tested loading the CPU inference engine correctly.
*   **Basic Extraction**: Evaluated on 3 real floor-plan excerpts (`F1_extracted.png`, `F2_extracted.png`, `F3_extracted.png`).
*   **Empty Result Handling**: Created `empty_test.png` (a blank 512x512 matrix) to ensure the OCR engine returns an empty result instead of crashing.
*   **Coordinate Preservation**: Created `backend/app/ocr/transform.py` containing `inverse_transform_ocr_result()` to mathematically project letterboxed/scaled coordinates back to original SVG/Image pixel space using perception metadata. Checked via mock matrix inversion test.
*   **Serialization**: Verified `json.dumps()` compatibility for network transmission.

## Results
*   **PaddleOCR Inference**: Successful extraction of dimensions and room labels.
*   **Orientation Handling**: Extracted orientation directly from PaddleOCR polygon geometries (e.g., mapping slopes for rotated strings).
*   **Confidence Scores**: Accurately mapped for later thresholding.

## Debug Visualization
*   A tool was added at `backend/app/ocr/visualization.py` (`draw_ocr_debug`) to visually superimpose bounding polygons and detected text tags back onto the images for easy verification in `backend/outputs/debug/ocr_debug_*.png`.

## Limitations & Known Issues
*   PaddleOCR runs smoothly on the CPU but inference speed naturally scales with image resolution and text density. Future optimization might include async OCR tasks or parallel batch processing.
*   Basic hinting (`numeric_like` vs `text_like`) is highly preliminary and relies simply on string content.

## Handoff to Phase 4
Phase 4 (Dimension Parser & Unit Normalization) will receive:
1. The structured `text_regions` output from this `OCREngine`.
2. Access to both the original image and perception masks for context.
3. Provenance and confidence values to reject low-quality OCR.

**PHASE 3 IS COMPLETE.**
