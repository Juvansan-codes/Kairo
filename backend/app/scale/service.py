from typing import Dict, Any
from .models import ScaleEstimationResult
from .geometry import extract_wall_candidates
from .association import associate_dimension
from .consensus import robust_scale_consensus
from ..dimensions.models import DimensionParseResult

def associate_dimensions(perception_result: Dict[str, Any], dimension_result: DimensionParseResult) -> ScaleEstimationResult:
    """
    High-level service to associate dimensions with geometry and estimate scale.
    """
    # 1. Extract lightweight geometry candidates from perception mask
    geom_candidates = extract_wall_candidates(perception_result)
    
    associations = []
    
    # 2. Associate each valid dimension
    for dim in dimension_result.dimensions:
        assoc = associate_dimension(dim, geom_candidates)
        if assoc:
            associations.append(assoc)
            
    # 3. Scale consensus
    final_scale, conf, source = robust_scale_consensus(associations)
    
    candidates_list = [a.scale_candidate_mm_per_px for a in associations if a.scale_candidate_mm_per_px]
    
    result = ScaleEstimationResult(
        associations=associations,
        scale_mm_per_px=final_scale if final_scale > 0 else None,
        scale_confidence=conf,
        scale_source=source,
        scale_candidates=candidates_list,
        provenance={"module": "phase5_association"}
    )
    
    return result
