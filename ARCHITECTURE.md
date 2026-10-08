# Architecture

The system converts a 2D floorplan into a 3D GLB model through a pipeline combining neural perception, OCR, and deterministic geometry reconciliation.

## Flow

1. **Frontend**: Next.js application allows user to upload a floor plan image.
2. **FastAPI**: Receives the image and initiates the reconstruction pipeline.
3. **Perception**: A neural model (e.g., Raster2Seq or U-Net fallback) segments the layout into semantic classes.
4. **OCR**: PaddleOCR extracts room labels and numerical dimensions.
5. **MGR (Metric-Aware Geometric Reconciliation)**: 
   - Uses OpenCV and scikit-image to skeletonize walls.
   - Extracts a wall graph and an opening graph using NetworkX and Shapely.
   - Enforces collinearity, Manhattan alignment, and intersection consistency.
   - Computes robust dimension scale.
6. **Room Graph**: Polygonizes the layout to extract individual rooms.
7. **3D Generation**: Extrudes the 2D layout into a 3D scene using trimesh.
8. **GLB Output**: The output is exported as `scene.glb` and `scene.json`.
9. **Viewer**: The Next.js frontend uses React Three Fiber to display the GLB interactively.
