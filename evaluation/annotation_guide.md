# Kairo Custom Floorplan Annotation Workflow

To collect high-quality custom ground truth for Kairo, we use a lightweight, practical annotation workflow. 
We DO NOT require a heavy backend platform. 

## Workflow

1. **Draw Geometry (CVAT / VGG Image Annotator)**
   - Open the source floorplan image in a lightweight tool like [VGG Image Annotator (VIA)](https://www.robots.ox.ac.uk/~vgg/software/via/via.html).
   - Draw **Polygons** for rooms (Label: `room`).
   - Draw **Polygons/Boxes** for doors and windows (Labels: `door`, `window`).
   - Draw **Polylines** for walls (Label: `wall`).
   
2. **Export to JSON**
   - Export the annotations as JSON.

3. **Convert to Kairo Format**
   - Run a simple conversion script (to be added to `evaluation/annotation/`) that takes the VIA JSON and produces the strictly typed `GroundTruth` Pydantic format defined in `evaluation/schema.py`.
   - Add explicit dimensions manually by appending to the `"dimensions"` array.
   - Enter `"scale_mm_per_px"` if the floorplan has a known verifiable scale.

## Schema Standard
```json
{
  "id": "F1",
  "walls": [ { "id": "W1", "geometry": [[0,0], [100,0]] } ],
  "rooms": [ { "id": "R1", "polygon": [[0,0], [100,0], [100,100], [0,100]] } ],
  "doors": [],
  "windows": [],
  "dimensions": [ { "id": "D1", "value_mm": 3000 } ],
  "scale_mm_per_px": 20.0
}
```

Do **not** fabricate numbers. If a room has no polygon drawn, do not guess it. If scale is unknown, leave it as `null`.
