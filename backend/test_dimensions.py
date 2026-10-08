import json
import os
import sys

# Ensure backend module path is correct
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.dimensions.units import parse_dimension_string
from backend.app.dimensions.classifier import classify_dimension
from backend.app.dimensions.parser import parse_dimensions
from backend.app.ocr.engine import PaddleOCREngine

def run_unit_tests():
    print("--- RUNNING UNIT TESTS ---")
    
    test_cases = [
        # Metric
        "4200", "3500", "4200mm", "4200 mm", "3.5m", "3.5 m", "350cm", "350 cm",
        # Imperial
        "12'-6\"", "12' 6\"", "12'6\"", 
        # Compound
        "12' x 10'", "4200 x 3500", "3.5m x 4.2m",
        # Chained
        "1200 2500 1800",
        # Invalid / Ambiguous
        "ROOM 204", "A-102", "2026", "abc", "12-", "'"
    ]
    
    for case in test_cases:
        values, conf = parse_dimension_string(case)
        classification = classify_dimension(case, values, conf)
        print(f"[{case:15}] -> Class: {classification:18} | Values: {values} | ParseConf: {conf:.2f}")

    print("\nUnit tests completed.\n")

def run_real_images():
    print("--- RUNNING REAL FLOORPLAN TESTS ---")
    
    engine = PaddleOCREngine(use_angle_cls=True, lang="en")
    
    test_images = [
        "F1_extracted.png",
        "F2_extracted.png",
        "F3_extracted.png"
    ]
    
    test_dir = os.path.join(os.path.dirname(__file__), "outputs", "test_images")
    for img_name in test_images:
        img_path = os.path.join(test_dir, img_name)
        if not os.path.exists(img_path):
             print(f"Skipping {img_name}: Not found at {img_path}")
             continue
                 
        print(f"\nProcessing {img_name}...")
        
        # Run OCR
        ocr_result = engine.extract(img_path)
        text_regions = ocr_result.get("text_regions", [])
        
        # Parse Dimensions
        parse_result = parse_dimensions(text_regions)
        
        print("Dimensions:")
        for dim in parse_result.dimensions:
            print(f"  '{dim.raw_text}' -> {dim.dimension_type} -> {dim.values_mm} mm (conf={dim.parse_confidence:.2f})")
            
        print("Room Dimensions:")
        for r_dim in parse_result.room_dimensions:
            print(f"  '{r_dim.raw_text}' -> {r_dim.dimension_type} -> {r_dim.values_mm} mm")
            
        print("Numeric Annotations:")
        for num in parse_result.numeric_annotations:
            print(f"  '{num.raw_text}' -> {num.dimension_type}")
            
        print("Text / Ignored:")
        for txt in parse_result.ignored:
            print(f"  '{txt.raw_text}' -> {txt.dimension_type}")

if __name__ == "__main__":
    run_unit_tests()
    run_real_images()
