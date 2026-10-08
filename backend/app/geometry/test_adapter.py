import pytest
import numpy as np
from app.geometry.adapter import adapt_analysis_to_mgr
from app.geometry.pipeline import run_mgr_pipeline
from app.geometry.types import WallSegment, Opening, DimensionEvidence

class MockScaleResult:
    def __init__(self, scale, conf):
        self.scale_mm_per_px = scale
        self.scale_confidence = conf

def test_adapter_empty():
    analysis_result = {}
    adapted = adapt_analysis_to_mgr(analysis_result)
    assert adapted["wall_mask"] is None
    assert len(adapted["doors"]) == 0
    assert len(adapted["windows"]) == 0
    assert adapted.get("scale_mm_per_px") is None

def test_adapter_valid_mask():
    # 0=floor, 1=wall, 2=door, 3=window
    mask = np.zeros((100, 100), dtype=np.uint8)
    # Add a wall
    mask[10:90, 45:55] = 1
    # Add a door
    mask[40:60, 45:55] = 2
    # Add a window
    mask[10:30, 45:55] = 3
    
    analysis_result = {
        "perception_result": {
            "raw_mask": mask
        },
        "scale_result": MockScaleResult(20.0, 0.9)
    }
    
    adapted = adapt_analysis_to_mgr(analysis_result)
    assert adapted["wall_mask"] is not None
    assert np.any(adapted["wall_mask"])
    
    assert len(adapted["doors"]) >= 1
    assert adapted["doors"][0].type == "door"
    
    assert len(adapted["windows"]) >= 1
    assert adapted["windows"][0].type == "window"
    
    assert adapted["scale_mm_per_px"] == 20.0

def test_adapter_missing_scale():
    analysis_result = {
        "perception_result": {
            "raw_mask": np.zeros((10, 10), dtype=np.uint8)
        },
        "scale_result": MockScaleResult(None, 0.0)
    }
    adapted = adapt_analysis_to_mgr(analysis_result)
    assert adapted.get("scale_mm_per_px") is None

def test_real_mgr_execution():
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[10:90, 10:15] = 1 # wall
    mask[90:95, 10:90] = 1 # wall
    
    analysis_result = {
        "perception_result": {
            "raw_mask": mask
        },
        "scale_result": MockScaleResult(20.0, 0.9)
    }
    
    adapted = adapt_analysis_to_mgr(analysis_result)
    
    # Run the real MGR pipeline
    mgr_result = run_mgr_pipeline(**adapted)
    
    # Verify execution
    assert len(mgr_result.walls) > 0
    assert mgr_result.scale_mm_per_px == 20.0
