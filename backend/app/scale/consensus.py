import numpy as np
from typing import List, Tuple
from .models import DimensionAssociation

def robust_scale_consensus(associations: List[DimensionAssociation]) -> Tuple[float, float, str]:
    """
    Given a list of scale candidates from associations, calculate a robust consensus scale.
    Returns: (scale_mm_per_px, confidence, source)
    """
    candidates = [assoc.scale_candidate_mm_per_px for assoc in associations if assoc.scale_candidate_mm_per_px is not None and assoc.scale_candidate_mm_per_px > 0]
    
    if not candidates:
        # Fallback 1: Door prior
        # Wait, if we had door masks we could do that. Since we didn't extract door candidates in this simplified version,
        # we return unavailable.
        return 0.0, 0.0, "unavailable"
        
    if len(candidates) == 1:
        return candidates[0], 0.5, "single_dimension"
        
    # Robust consensus: Median and MAD (Median Absolute Deviation)
    median_scale = float(np.median(candidates))
    
    # Calculate MAD
    candidates_arr = np.array(candidates)
    mad = float(np.median(np.abs(candidates_arr - median_scale)))
    
    # Find inliers (within 2 MADs, or a generous 15% tolerance if MAD is 0)
    tolerance = max(2 * mad, 0.15 * median_scale)
    inliers = [c for c in candidates if abs(c - median_scale) <= tolerance]
    
    if not inliers:
        inliers = candidates # fallback
        
    final_scale = float(np.mean(inliers))
    
    # Confidence based on number of inliers and variance
    confidence = min(0.95, 0.5 + 0.1 * len(inliers))
    
    # If the variance among inliers is very low, boost confidence
    if len(inliers) > 1:
        std = float(np.std(inliers))
        if std / final_scale < 0.05:
            confidence = min(0.98, confidence + 0.1)
            
    source = "multiple_agreeing_dimensions" if len(inliers) > 1 else "printed_dimension"
    
    return final_scale, confidence, source
