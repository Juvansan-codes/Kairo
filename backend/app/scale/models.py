from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class DimensionAssociation(BaseModel):
    dimension_id: str
    geometry_type: str  # e.g., 'wall_segment', 'room_boundary', 'door_prior'
    geometry_reference: Optional[str] = None
    dimension_value_mm: float
    pixel_length: Optional[float] = None
    scale_candidate_mm_per_px: Optional[float] = None
    association_confidence: float
    evidence: Dict[str, Any]
    provenance: Dict[str, Any]

class ScaleEstimationResult(BaseModel):
    associations: List[DimensionAssociation] = []
    scale_mm_per_px: Optional[float] = None
    scale_confidence: float = 0.0
    scale_source: str = "unavailable"
    scale_candidates: List[float] = []
    provenance: Dict[str, Any] = {}
