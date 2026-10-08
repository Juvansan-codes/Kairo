import time
import json
import cv2
import numpy as np
from pathlib import Path
from backend.app.ocr.engine import PaddleOCREngine
from backend.app.ocr.visualization import draw_ocr_debug
from backend.app.ocr.transform import inverse_transform_ocr_result

def test_ocr():
    print("Initializing PaddleOCR...")
    start_init = time.time()
    try:
        engine = PaddleOCREngine(use_angle_cls=True, lang="en")
    except Exception as e:
        print(f"Failed to initialize PaddleOCR: {e}")
        return
    print(f"Initialized in {time.time() - start_init:.2f}s")
    
    test_dir = Path(r"d:\College Files\Kairo\backend\outputs\test_images")
    debug_dir = Path(r"d:\College Files\Kairo\backend\outputs\debug")
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    images = list(test_dir.glob("*.png"))
    
    # 1. Test basic extraction on real images
    for img_path in images:
        print(f"\nProcessing {img_path.name}...")
        start_inf = time.time()
        result = engine.extract(str(img_path))
        inf_time = time.time() - start_inf
        
        regions = result.get("text_regions", [])
        print(f"Inference Time: {inf_time:.4f}s")
        print(f"Number of detections: {len(regions)}")
        if regions:
            # Show top 5 detections for log
            top_regions = regions[:5]
            for r in top_regions:
                print(f" - '{r['text']}' (Conf: {r['confidence']:.2f}, Orient: {r['orientation']:.1f}°)")
        
        out_path = debug_dir / f"ocr_debug_{img_path.name}"
        draw_ocr_debug(str(img_path), result, str(out_path))
        
        # Serialization test
        try:
            json.dumps(result)
            print("Serialization check: PASSED")
        except Exception as e:
            print(f"Serialization check: FAILED - {e}")
            
    # 2. Test empty result
    empty_img_path = test_dir / "empty_test.png"
    empty_img = np.zeros((512, 512, 3), dtype=np.uint8)
    cv2.imwrite(str(empty_img_path), empty_img)
    print("\nProcessing empty image...")
    empty_result = engine.extract(str(empty_img_path))
    print(f"Empty result returned regions: {len(empty_result.get('text_regions', []))}")
    if len(empty_result.get('text_regions', [])) == 0:
        print("Empty extraction test: PASSED")
    else:
        print("Empty extraction test: FAILED")

    # 3. Test coordinate mapping
    print("\nTesting coordinate mapping utility...")
    dummy_meta = {"scale": 0.5, "pad_top": 100, "pad_left": 50}
    # Mock a result that would have been from the preprocessed image
    dummy_result = {"text_regions": [{"bbox": [150, 200, 50, 20], "polygon": [[150, 200], [200, 200], [200, 220], [150, 220]]}]}
    inv = inverse_transform_ocr_result(dummy_result, dummy_meta)
    new_bbox = inv["text_regions"][0]["bbox"]
    # expected x = (150 - 50) / 0.5 = 200
    # expected y = (200 - 100) / 0.5 = 200
    # expected w = 50 / 0.5 = 100
    # expected h = 20 / 0.5 = 40
    if new_bbox == [200.0, 200.0, 100.0, 40.0]:
        print("Coordinate mapping test: PASSED")
    else:
        print(f"Coordinate mapping test: FAILED, got {new_bbox}")

if __name__ == "__main__":
    test_ocr()
