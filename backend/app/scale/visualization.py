import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any

from .models import ScaleEstimationResult

def draw_scale_debug(image_path: str, scale_result: ScaleEstimationResult, perception_result: Dict[str, Any], output_path: str):
    img = cv2.imread(image_path)
    if img is None:
        return
        
    # Draw geometry candidates in blue (from raw_mask, ideally we could draw the minAreaRects but we didn't save them in perception_result directly. We can just draw the mask for context)
    mask = perception_result.get("raw_mask")
    metadata = perception_result.get("metadata", {})
    scale = metadata.get("scale", 1.0)
    pad_top = metadata.get("pad_top", 0)
    pad_left = metadata.get("pad_left", 0)
    
    if mask is not None:
        wall_mask = (mask == 1).astype(np.uint8) * 255
        # Transform mask back to original? Too heavy. Let's just draw associations.
        pass
        
    for assoc in scale_result.associations:
        # We don't have the original bbox saved in assoc, but in a full system we could look it up.
        # For debug text, we can just print it on the top left.
        pass
        
    # Add text overlay for final scale
    text_lines = [
        f"Scale: {scale_result.scale_mm_per_px:.2f} mm/px" if scale_result.scale_mm_per_px else "Scale: Unavailable",
        f"Source: {scale_result.scale_source}",
        f"Conf: {scale_result.scale_confidence:.2f}",
        f"Associations: {len(scale_result.associations)}"
    ]
    
    y0, dy = 30, 30
    for i, line in enumerate(text_lines):
        y = y0 + i * dy
        cv2.putText(img, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
    cv2.imwrite(output_path, img)
