import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
import math

class GeometryCandidate:
    def __init__(self, rect_id: str, cx: float, cy: float, w: float, h: float, angle: float, mask_scale: float):
        self.id = rect_id
        # Coordinates in original image space
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.angle = angle # in degrees
        self.mask_scale = mask_scale
        
    def is_horizontal(self, tolerance: float = 15.0) -> bool:
        # angle is usually from minAreaRect.
        # If w > h, horizontal means angle ~ 0 or 180.
        # minAreaRect angle is between [-90, 0)
        # Let's just use bounding box dimensions roughly for horizontal/vertical if angle is close to 0/90
        # For simplicity, we just use the longer axis.
        if self.w > self.h:
            return abs(self.angle) < tolerance or abs(self.angle + 180) < tolerance
        else:
            return abs(self.angle + 90) < tolerance or abs(self.angle - 90) < tolerance
            
    def is_vertical(self, tolerance: float = 15.0) -> bool:
        if self.h > self.w:
            return abs(self.angle) < tolerance or abs(self.angle + 180) < tolerance
        else:
            return abs(self.angle + 90) < tolerance or abs(self.angle - 90) < tolerance

def extract_wall_candidates(perception_result: Dict[str, Any]) -> List[GeometryCandidate]:
    """
    Extracts lightweight geometry representations (minAreaRects) for walls from the perception mask.
    Transforms them to original image coordinate space.
    """
    mask = perception_result.get("raw_mask")
    metadata = perception_result.get("metadata", {})
    
    if mask is None:
        return []
        
    wall_mask = (mask == 1).astype(np.uint8) * 255
    
    # Optional: morph open to remove noise
    kernel = np.ones((3,3), np.uint8)
    wall_mask = cv2.morphologyEx(wall_mask, cv2.MORPH_OPEN, kernel)
    
    contours, _ = cv2.findContours(wall_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    scale = metadata.get("scale", 1.0)
    pad_top = metadata.get("pad_top", 0)
    pad_left = metadata.get("pad_left", 0)
    
    candidates = []
    
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < 20: # ignore tiny noise
            continue
            
        rect = cv2.minAreaRect(cnt)
        # rect = ((cx, cy), (w, h), angle)
        (cx, cy), (w, h), angle = rect
        
        # Transform back to original image space
        orig_cx = (cx - pad_left) / scale
        orig_cy = (cy - pad_top) / scale
        orig_w = w / scale
        orig_h = h / scale
        
        candidates.append(GeometryCandidate(
            rect_id=f"wall_candidate_{i}",
            cx=orig_cx,
            cy=orig_cy,
            w=orig_w,
            h=orig_h,
            angle=angle,
            mask_scale=scale
        ))
        
    return candidates
