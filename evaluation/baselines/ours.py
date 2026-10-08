from typing import Dict, Any
import sys
import os
import dataclasses

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend"))

from backend.app.services.analysis import PerceptionAnalysisService
from backend.app.geometry.adapter import adapt_analysis_to_mgr
from backend.app.geometry.pipeline import run_mgr_pipeline
from backend.app.services.job_manager import Job
from .interface import ReconstructionBaseline

class OurMethod(ReconstructionBaseline):
    def __init__(self, name="OURS_v1", enable_geometric_reconciliation=True, enable_metric_calibration=True, enable_topology_validation=True):
        self._name = name
        self.enable_geometric_reconciliation = enable_geometric_reconciliation
        self.enable_metric_calibration = enable_metric_calibration
        self.enable_topology_validation = enable_topology_validation
        self.analysis_service = PerceptionAnalysisService()
        
    def reconstruct(self, input_path: str) -> Dict[str, Any]:
        # 1. Perception/OCR/Dimensions/Scale
        dummy_job = Job(job_id="eval_job")
        analysis_result = self.analysis_service.analyze(input_path, dummy_job)
        
        # 2. Convert to MGR format
        geometry_inputs = adapt_analysis_to_mgr(analysis_result)
        
        # 3. Run Real MGR Pipeline
        mgr_result = run_mgr_pipeline(
            **geometry_inputs,
            enable_geometric_reconciliation=self.enable_geometric_reconciliation,
            enable_metric_calibration=self.enable_metric_calibration,
            enable_topology_validation=self.enable_topology_validation
        )
        
        # 4. Map to dictionary for evaluation Prediction schema
        result_dict = dataclasses.asdict(mgr_result)
        
        # Map walls to include "geometry" key as expected by layout metrics
        for w in result_dict.get("walls", []):
            if "start" in w and "end" in w:
                w["geometry"] = [w["start"], w["end"]]
                
        # Map doors and windows to include "geometry" bounding box as expected by completeness metrics
        for cat in ["doors", "windows"]:
            for item in result_dict.get(cat, []):
                if "start" in item and "end" in item:
                    x1, y1 = item["start"]
                    x2, y2 = item["end"]
                    # Create a bounding box [minx, miny, maxx, maxy] with small thickness for area IoU
                    item["geometry"] = [min(x1, x2) - 2, min(y1, y2) - 2, max(x1, x2) + 2, max(y1, y2) + 2]

        # Extract dimensions from analysis_result to pass through to metrics
        dim_res_obj = analysis_result.get("dimension_result")
        dim_res = dim_res_obj.dimensions if dim_res_obj else []
        dimensions_list = [d.dict() if hasattr(d, "dict") else vars(d) if hasattr(d, "__dict__") else d for d in dim_res]
        
        # Map values_mm list to value_mm float as expected by metrics
        for d in dimensions_list:
            if "values_mm" in d and len(d["values_mm"]) > 0:
                d["value_mm"] = d["values_mm"][0]
        
        result_dict["dimensions"] = dimensions_list
        
        return result_dict
        
    @property
    def name(self) -> str:
        return self._name
