import numpy as np
from app.geometry.pipeline import run_mgr_pipeline
from app.geometry.types import WallSegment
import cv2

def test_rooms():
    # Synthetic case B: A perfect closed square
    mask = np.zeros((100, 100), dtype=np.uint8)
    cv2.rectangle(mask, (20, 20), (80, 80), 255, 3) # closed square
    
    res_b = run_mgr_pipeline(wall_mask=mask)
    print(f"Case B (Synthetic Square) -> Walls: {len(res_b.walls)}, Rooms: {len(res_b.rooms)}")
    
    # Let's inspect real_001.png
    from app.services.analysis import PerceptionAnalysisService
    from app.geometry.adapter import adapt_analysis_to_mgr
    img_path = r"d:\College Files\Kairo\evaluation\datasets\custom_real_v1\real_001.png"
    
    class DummyJob:
        stage = ""
    
    perc = PerceptionAnalysisService().analyze(img_path, DummyJob())
    inputs = adapt_analysis_to_mgr(perc)
    res_a = run_mgr_pipeline(**inputs)
    print(f"Case A (real_001) -> Walls: {len(res_a.walls)}, Rooms: {len(res_a.rooms)}")

if __name__ == "__main__":
    test_rooms()
