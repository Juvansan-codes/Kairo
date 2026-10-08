from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel

class GroundTruth(BaseModel):
    walls: List[Dict[str, Any]] = []
    rooms: List[Dict[str, Any]] = []
    doors: List[Dict[str, Any]] = []
    windows: List[Dict[str, Any]] = []
    dimensions: List[Dict[str, Any]] = []
    scale_mm_per_px: Optional[float] = None

class Prediction(BaseModel):
    walls: List[Dict[str, Any]] = []
    rooms: List[Dict[str, Any]] = []
    doors: List[Dict[str, Any]] = []
    windows: List[Dict[str, Any]] = []
    dimensions: List[Dict[str, Any]] = []
    scale_mm_per_px: Optional[float] = None
    inference_time_sec: Optional[float] = None

class EvaluationSample:
    def __init__(self, sample_id: str, input_path: str, ground_truth: Optional[GroundTruth] = None):
        self.sample_id = sample_id
        self.input_path = input_path
        self.ground_truth = ground_truth
        self.prediction: Optional[Prediction] = None
