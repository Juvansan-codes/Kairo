from typing import Dict, Any, List
from .models import DimensionCandidate, DimensionParseResult
from .units import parse_dimension_string
from .classifier import classify_dimension
from .vlm import DimensionVerifier

def parse_dimensions(text_regions: List[Dict[str, Any]], vlm_verifier: DimensionVerifier = None) -> DimensionParseResult:
    """
    Consume the text_regions output from the OCR engine and produce a DimensionParseResult.
    """
    result = DimensionParseResult()
    
    for region in text_regions:
        raw_text = region.get("text", "")
        bbox = region.get("bbox", [])
        polygon = region.get("polygon", [])
        ocr_confidence = region.get("confidence", 0.0)
        orientation = region.get("orientation", 0.0)
        provenance = region.get("provenance", {})
        
        if not raw_text.strip():
            continue
            
        # 1. Parse unit to mm
        values_mm, parse_confidence = parse_dimension_string(raw_text)
        
        # 2. Classify based on raw text and parsed values
        dim_type = classify_dimension(raw_text, values_mm, parse_confidence)
        
        # 3. Optional VLM Verification
        if vlm_verifier and vlm_verifier.should_verify(raw_text, ocr_confidence, parse_confidence, dim_type):
            context = {
                "ocr_confidence": ocr_confidence,
                "bbox": bbox,
                "orientation": orientation
            }
            vlm_result = vlm_verifier.verify(raw_text, context)
            if vlm_result and vlm_result.confidence > parse_confidence:
                # Update with VLM insights
                raw_text = vlm_result.normalized_text
                dim_type = vlm_result.interpretation
                parse_confidence = vlm_result.confidence
                provenance["vlm_verified"] = True
                provenance["vlm_reason"] = vlm_result.reason
                
                # Re-parse units with corrected text
                values_mm, _ = parse_dimension_string(raw_text)
        
        # 4. Create candidate
        candidate = DimensionCandidate(
            raw_text=raw_text,
            values_mm=values_mm,
            dimension_type=dim_type,
            bbox=bbox,
            polygon=polygon,
            orientation=orientation,
            confidence=ocr_confidence,
            parse_confidence=parse_confidence,
            provenance=provenance
        )
        
        # 5. Route to correct bucket
        if dim_type == "DIMENSION":
            result.dimensions.append(candidate)
        elif dim_type == "ROOM_DIMENSION":
            result.room_dimensions.append(candidate)
        elif dim_type == "NUMERIC_ANNOTATION":
            result.numeric_annotations.append(candidate)
        elif dim_type == "TEXT":
            result.ignored.append(candidate)
        else:
            result.ignored.append(candidate)
            
    return result
