from typing import List, Tuple, Dict, Any, Optional
from pydantic import BaseModel, Field

class DimensionCandidate(BaseModel):
    raw_text: str
    values_mm: List[float]
    dimension_type: str  # DIMENSION, ROOM_DIMENSION, NUMERIC_ANNOTATION, TEXT, UNKNOWN
    bbox: List[float]
    polygon: List[List[float]]
    orientation: float
    confidence: float
    parse_confidence: float
    provenance: Dict[str, Any]

class DimensionParseResult(BaseModel):
    dimensions: List[DimensionCandidate] = Field(default_factory=list)
    room_dimensions: List[DimensionCandidate] = Field(default_factory=list)
    numeric_annotations: List[DimensionCandidate] = Field(default_factory=list)
    ignored: List[DimensionCandidate] = Field(default_factory=list)

    def to_dict(self):
        return self.dict()
