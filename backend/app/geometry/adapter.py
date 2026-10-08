import numpy as np
import cv2
from typing import Dict, Any, List
from app.geometry.types import WallSegment, Opening, DimensionEvidence
import math

def extract_openings_from_mask(mask: np.ndarray, class_idx: int, opening_type: str) -> List[Opening]:
    """Extract Openings from the semantic mask using minAreaRect."""
    binary_mask = (mask == class_idx).astype(np.uint8) * 255
    
    # Optional cleanup
    kernel = np.ones((3,3), np.uint8)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)
    
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    openings = []
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < 10:
            continue
            
        rect = cv2.minAreaRect(cnt)
        (cx, cy), (w, h), angle = rect
        
        # Calculate endpoints along the major axis
        angle_rad = math.radians(angle)
        
        # minAreaRect angle is [-90, 0). The width and height could be anything.
        # Find the major axis
        if w > h:
            dx = (w / 2) * math.cos(angle_rad)
            dy = (w / 2) * math.sin(angle_rad)
        else:
            # Add 90 degrees if height is the major axis
            angle_rad += math.pi / 2
            dx = (h / 2) * math.cos(angle_rad)
            dy = (h / 2) * math.sin(angle_rad)
            
        start = (float(cx - dx), float(cy - dy))
        end = (float(cx + dx), float(cy + dy))
        
        openings.append(Opening(
            id=f"{opening_type}_{i}",
            type=opening_type,
            start=start,
            end=end,
            confidence=0.8,
            source=["perception_mask"]
        ))
        
    return openings

def adapt_analysis_to_mgr(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapter to convert Member 1's nested dict into Member 2's MGR inputs.
    """
    perception_result = analysis_result.get("perception_result", {})
    raw_mask = perception_result.get("raw_mask")
    
    # 1. Wall Mask
    wall_mask = None
    if raw_mask is not None:
        wall_mask = (raw_mask == 1).astype(bool)
        
    # 2. Doors and Windows
    doors = []
    windows = []
    if raw_mask is not None:
        # Opening types must be "door" or "window"
        doors = extract_openings_from_mask(raw_mask, 2, "door")
        windows = extract_openings_from_mask(raw_mask, 3, "window")
        
    # 3. Dimensions (using the already resolved scale from Member 1)
    scale_result = analysis_result.get("scale_result")
    scale_mm_per_px = None
    if scale_result and hasattr(scale_result, 'scale_mm_per_px'):
        scale_mm_per_px = scale_result.scale_mm_per_px
        
    return {
        "wall_mask": wall_mask,
        "doors": doors,
        "windows": windows,
        "scale_mm_per_px": scale_mm_per_px,
    }
