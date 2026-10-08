import cv2
from pathlib import Path
from app.services.analysis import PerceptionAnalysisService

def test():
    img_path = r"d:\College Files\Kairo\evaluation\datasets\custom_real_v1\real_001.png"
    print(f"Testing {img_path}")
    
    # Run the full analysis service to get OCR, Dimensions, and Scale
    service = PerceptionAnalysisService()
    
    class DummyJob:
        stage = ""
    
    job = DummyJob()
    result = service.analyze(img_path, job)
    
    ocr = result["ocr_result"]
    texts = [r['text'] for r in ocr.get('text_regions', [])]
    print(f"\n--- OCR Result ---")
    print(f"Total texts found: {len(texts)}")
    print(f"First 10 texts: {texts[:10]}")
    
    dim = result["dimension_result"]
    print(f"\n--- Dimensions ---")
    print(f"Parsed dimension candidates: {len(dim.dimensions)}")
    for d in dim.dimensions[:5]:
        print(f"  {d.value} mm at {d.center}")
        
    scale = result["scale_result"]
    print(f"\n--- Scale ---")
    print(f"Scale: {scale.scale_mm_per_px}")
    print(f"Source: {scale.scale_source}")
    print(f"Assoc count: {len(scale.associations)}")
    
if __name__ == "__main__":
    test()
