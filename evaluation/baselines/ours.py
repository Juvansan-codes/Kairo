from typing import Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.services.analysis import PerceptionAnalysisService
from backend.app.services.geometry import MockGeometryService
from backend.app.services.job_manager import Job
from .interface import ReconstructionBaseline

class OurMethod(ReconstructionBaseline):
    def __init__(self):
        self.analysis_service = PerceptionAnalysisService()
        self.geometry_service = MockGeometryService()
        
    def reconstruct(self, input_path: str) -> Dict[str, Any]:
        # We simulate a Job object as required by PerceptionAnalysisService
        # though ideally it should be decoupled
        dummy_job = Job(job_id="eval_job")
        
        # 1. Perception/OCR/Dimensions/Scale
        analysis_result = self.analysis_service.analyze(input_path, dummy_job)
        
        # 2. Geometry
        geometry_result = self.geometry_service.reconstruct(analysis_result)
        
        return geometry_result
        
    @property
    def name(self) -> str:
        return "OURS_v1"
