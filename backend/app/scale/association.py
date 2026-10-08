import math
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from .models import DimensionAssociation
from .geometry import GeometryCandidate
from ..dimensions.models import DimensionCandidate

def get_dimension_orientation(dim: DimensionCandidate) -> str:
    """Classify dimension as 'horizontal', 'vertical', or 'unknown'."""
    # Polygon is [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    # Usually p0-p1 is the top edge
    p0, p1 = dim.polygon[0], dim.polygon[1]
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    angle = math.degrees(math.atan2(dy, dx))
    
    if abs(angle) < 15 or abs(angle - 180) < 15 or abs(angle + 180) < 15:
        return 'horizontal'
    elif abs(angle - 90) < 15 or abs(angle + 90) < 15:
        return 'vertical'
    return 'unknown'

def compute_spatial_score(dim: DimensionCandidate, geom: GeometryCandidate) -> float:
    """Compute score based on distance and projection."""
    dim_cx = dim.bbox[0] + dim.bbox[2] / 2
    dim_cy = dim.bbox[1] + dim.bbox[3] / 2
    
    dist = math.sqrt((dim_cx - geom.cx)**2 + (dim_cy - geom.cy)**2)
    
    # We expect dimensions to be reasonably close to the wall (e.g., within 200 pixels in orig space)
    # Convert score to [0, 1] decay
    dist_score = max(0.0, 1.0 - (dist / 200.0))
    
    return dist_score

def associate_dimension(dim: DimensionCandidate, candidates: List[GeometryCandidate]) -> Optional[DimensionAssociation]:
    best_score = 0.0
    best_candidate = None
    
    dim_orientation = get_dimension_orientation(dim)
    
    for geom in candidates:
        # Filter by orientation
        if dim_orientation == 'horizontal' and not geom.is_horizontal():
            continue
        if dim_orientation == 'vertical' and not geom.is_vertical():
            continue
            
        score = compute_spatial_score(dim, geom)
        
        # Penalize if geometry is very small compared to what a dimension usually points to
        if max(geom.w, geom.h) < 20:
            score *= 0.5
            
        if score > best_score and score > 0.3: # minimum threshold
            best_score = score
            best_candidate = geom
            
    if best_candidate is None:
        return None
        
    pixel_len = max(best_candidate.w, best_candidate.h)
    
    # Scale = mm / px
    # Take the first value if there's one (for standard DIMENSION)
    val_mm = dim.values_mm[0] if dim.values_mm else 0.0
    
    scale_candidate = val_mm / pixel_len if pixel_len > 0 else None
    
    evidence = {
        "distance_score": best_score,
        "orientation_match": True,
        "dimension_orientation": dim_orientation
    }
    
    return DimensionAssociation(
        dimension_id=f"dim_{id(dim)}",
        geometry_type="wall_candidate",
        geometry_reference=best_candidate.id,
        dimension_value_mm=val_mm,
        pixel_length=pixel_len,
        scale_candidate_mm_per_px=scale_candidate,
        association_confidence=best_score,
        evidence=evidence,
        provenance={"source": "association_heuristics"}
    )
