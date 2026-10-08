import os
import sys
from pathlib import Path

# Ensure backend module path is correct
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.scale.models import DimensionAssociation, ScaleEstimationResult
from backend.app.scale.consensus import robust_scale_consensus
from backend.app.scale.service import associate_dimensions
from backend.app.dimensions.models import DimensionParseResult, DimensionCandidate
from backend.app.scale.geometry import GeometryCandidate
from backend.app.perception.adapter import ResNetUNetPerception
from backend.app.ocr.engine import PaddleOCREngine
from backend.app.dimensions.parser import parse_dimensions

def test_consensus():
    print("--- TESTING SCALE CONSENSUS ---")
    
    # Mock associations
    assocs = [
        DimensionAssociation(dimension_id="1", geometry_type="wall", dimension_value_mm=4000, pixel_length=200, scale_candidate_mm_per_px=20.0, association_confidence=0.9, evidence={}, provenance={}),
        DimensionAssociation(dimension_id="2", geometry_type="wall", dimension_value_mm=2000, pixel_length=101, scale_candidate_mm_per_px=19.8, association_confidence=0.9, evidence={}, provenance={}),
        DimensionAssociation(dimension_id="3", geometry_type="wall", dimension_value_mm=3000, pixel_length=150, scale_candidate_mm_per_px=20.0, association_confidence=0.9, evidence={}, provenance={}),
        DimensionAssociation(dimension_id="4", geometry_type="wall", dimension_value_mm=4000, pixel_length=100, scale_candidate_mm_per_px=40.0, association_confidence=0.9, evidence={}, provenance={}), # Outlier
    ]
    
    scale, conf, source = robust_scale_consensus(assocs)
    print(f"Candidates: {[a.scale_candidate_mm_per_px for a in assocs]}")
    print(f"Consensus Scale: {scale:.2f} mm/px, Conf: {conf:.2f}, Source: {source}")
    print("Residuals:")
    for a in assocs:
        predicted = a.pixel_length * scale
        error = abs(predicted - a.dimension_value_mm)
        print(f"  Dim: {a.dimension_value_mm}mm, Pixel: {a.pixel_length}px -> Predicted: {predicted:.2f}mm, Error: {error:.2f}mm")
    
    if abs(scale - 19.93) < 0.1:
        print("Consensus Test: PASSED\n")
    else:
        print("Consensus Test: FAILED\n")

def test_real_pipeline():
    print("--- TESTING REAL PIPELINE ---")
    
    try:
        run_dir = Path(r"d:\College Files\Kairo\backend\models\floorplan-to-3d-walls-repo")
        perception = ResNetUNetPerception(run_dir)
        ocr = PaddleOCREngine(use_angle_cls=True, lang="en")
    except Exception as e:
        print(f"Failed to load models: {e}")
        return
        
    test_dir = Path(r"d:\College Files\Kairo\backend\outputs\test_images")
    test_images = list(test_dir.glob("*.png"))
    
    for img_path in test_images:
        print(f"\nProcessing {img_path.name}...")
        
        # 1. Perception
        perc_res = perception.predict(img_path)
        
        # 2. OCR
        ocr_res = ocr.extract(str(img_path))
        text_regions = ocr_res.get("text_regions", [])
        
        # 3. Dimensions
        dim_res = parse_dimensions(text_regions)
        print(f"  Parsed {len(dim_res.dimensions)} pure dimensions.")
        
        # 4. Scale
        scale_res = associate_dimensions(perc_res, dim_res)
        
        print(f"  Scale: {scale_res.scale_mm_per_px} mm/px")
        print(f"  Source: {scale_res.scale_source}")
        print(f"  Associations: {len(scale_res.associations)}")
        
        # We also want to manually test a mock dimension to ensure geometry association works on a real perception mask!
        print("  Mocking a dimension candidate to test geometry association...")
        mock_dim = DimensionCandidate(
            raw_text="3500",
            values_mm=[3500.0],
            dimension_type="DIMENSION",
            bbox=[100, 100, 20, 10], # arbitrary
            polygon=[[100,100], [120,100], [120,110], [100,110]],
            orientation=0.0,
            confidence=0.9,
            parse_confidence=0.9,
            provenance={}
        )
        mock_dim_res = DimensionParseResult(dimensions=[mock_dim])
        mock_scale_res = associate_dimensions(perc_res, mock_dim_res)
        print(f"  Mock Scale associations: {len(mock_scale_res.associations)}")
        if mock_scale_res.associations:
            assoc = mock_scale_res.associations[0]
            print(f"    Mock associated with pixel length: {assoc.pixel_length:.2f}px -> {assoc.scale_candidate_mm_per_px:.2f} mm/px")
            
if __name__ == "__main__":
    test_consensus()
    test_real_pipeline()
