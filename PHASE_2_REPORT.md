# PHASE 2 REPORT: Model Integration

## Model
*   **Model Name**: Yytsi/floorplan-to-3d-walls
*   **Source**: Hugging Face (`Yytsi/floorplan-to-3d-walls`) via Git LFS
*   **Checkpoint**: `best.safetensors`
*   **Architecture**: UNet decoder with ResNet-34 encoder (`segmentation_models_pytorch`).
*   **Class Mapping**:
    - `0`: `floor` (Background/Base)
    - `1`: `wall`
    - `2`: `door`
    - `3`: `window`
*   **Input Size**: 512x512 RGB.
*   **Preprocessing**:
    - Aspect ratio-preserving resize to fit within 512x512.
    - Letterboxing (padding) applied.
    - Normalized with ImageNet mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`.

## Environment
*   **Python version**: 3.11
*   **PyTorch version**: 2.14.1+cpu
*   **Device used**: CPU (or CUDA if automatically detected).
*   **Inference time**: ~0.25 - 0.35 seconds per image

## Test Inputs
Tested on 3 actual architectural floorplans extracted from the official model demonstration dataset:
1.  `F1_extracted.png` (Standard layout)
2.  `F2_extracted.png` (Complex, high-density walls)
3.  `F3_extracted.png` (Alternate architectural style)

## Results
*   **SUCCESS**: The adapter loaded the official complete `best.safetensors` checkpoint successfully.
*   **SUCCESS**: Inference ran without errors on all 3 images.
*   **SUCCESS**: Model output distributions correctly reflect the different layouts (e.g., F2 contained 2008 wall pixels, while F1 contained 749).
*   **SUCCESS**: The metadata accurately provides `orig_w`, `orig_h`, `scale`, `pad_top`, and `pad_left` making the mapping invertible for downstream geometry algorithms.
*   **Visualizations**: Blended RGB visualization overlays were correctly generated and saved in `outputs/debug/`.

## Problems / Limitations
*   Network constraints required fetching the weights through Git LFS instead of direct Python chunked requests, but the model behaves perfectly once loaded.
*   The raw pixel outputs are currently left as dense masks. Geometric abstraction into vectors is delegated to Member 2 (Geometry).

## Handoff
Member 2 (Geometry & Reconstruction) can safely consume the `PerceptionModel.predict(image_path)` output. They receive:
*   `metadata`: Dictionary needed to project mask coordinates back to SVG/image coordinates.
*   `semantic_regions`: High-level summary of class pixel densities.
*   `raw_mask`: The underlying `uint8` 2D NumPy array containing predicted class IDs for each pixel.

**PHASE 2 IS COMPLETE.**
