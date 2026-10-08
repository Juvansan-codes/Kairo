import sys
import os

# Ensure backend module path is correct
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.dimensions.vlm import DimensionVerifier, DimensionVerificationResult
from app.dimensions.parser import parse_dimensions

def test_vlm_triggers():
    verifier = DimensionVerifier(api_key="mock_key")
    
    # 1. Clear case: strong confidence, no VLM needed
    should = verifier.should_verify("4200", 0.98, 0.98, "DIMENSION")
    assert not should, "Clear case should not trigger VLM"
    
    # 2. Ambiguous case: OCR conf is low and has numbers
    should = verifier.should_verify("42OO", 0.6, 0.9, "NUMERIC_ANNOTATION")
    assert should, "Ambiguous case with low OCR conf should trigger VLM"
    
    # 3. Ambiguous case: 'I' vs '1' confusion with low parse conf
    should = verifier.should_verify("I2'-6\"", 0.9, 0.5, "UNKNOWN")
    assert should, "'I2'-6\"' should trigger VLM due to 'I'/'1' confusion"
    
    print("VLM Trigger tests passed.")

def test_vlm_integration():
    verifier = DimensionVerifier(api_key="mock_key")
    
    # Text region that is ambiguous
    regions = [
        {
            "text": "I2'-6\"",
            "confidence": 0.85,
            "bbox": [0,0,10,10],
            "orientation": 0.0
        },
        {
            "text": "4200",
            "confidence": 0.99,
            "bbox": [10,10,20,20],
            "orientation": 0.0
        }
    ]
    
    # Parse without VLM
    res_no_vlm = parse_dimensions(regions, vlm_verifier=None)
    # I2'-6" probably fails to parse and becomes NUMERIC_ANNOTATION or TEXT
    assert len(res_no_vlm.ignored) + len(res_no_vlm.numeric_annotations) > 0, "I2'-6\" should not be a dimension without VLM"
    assert len(res_no_vlm.dimensions) == 1, "4200 should be parsed as DIMENSION"
    
    # Parse with VLM
    res_with_vlm = parse_dimensions(regions, vlm_verifier=verifier)
    assert len(res_with_vlm.dimensions) == 2, "Both should be DIMENSIONS now"
    
    # Find the corrected one
    corrected = [d for d in res_with_vlm.dimensions if d.raw_text == "12'-6\""]
    assert len(corrected) == 1, "VLM should have corrected the text"
    assert abs(corrected[0].values_mm[0] - 3810.0) < 0.1, f"VLM result should be correctly parsed into mm, got {corrected[0].values_mm}"
    assert corrected[0].provenance.get("vlm_verified") is True, "Provenance should track VLM usage"
    
    # Test VLM failure (no api key)
    verifier_fail = DimensionVerifier(api_key=None)
    res_fail = parse_dimensions(regions, vlm_verifier=verifier_fail)
    assert len(res_fail.dimensions) == 1, "Fallback to normal behavior on VLM failure"
    
    print("VLM Integration tests passed.")

if __name__ == "__main__":
    test_vlm_triggers()
    test_vlm_integration()
