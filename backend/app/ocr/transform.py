from typing import Dict, Any

def inverse_transform_ocr_result(ocr_result: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inverse transform OCR coordinates from the preprocessed image coordinate system
    back to the original image coordinate system.
    
    metadata expects:
    - scale: float (the scaling factor applied during preprocessing)
    - pad_top: int (the padding added to the top)
    - pad_left: int (the padding added to the left)
    """
    scale = metadata.get("scale", 1.0)
    pad_top = metadata.get("pad_top", 0)
    pad_left = metadata.get("pad_left", 0)
    
    transformed_result = {"text_regions": []}
    
    for region in ocr_result.get("text_regions", []):
        new_region = region.copy()
        
        # Transform polygon
        if "polygon" in region:
            new_poly = []
            for point in region["polygon"]:
                x = (point[0] - pad_left) / scale
                y = (point[1] - pad_top) / scale
                new_poly.append([x, y])
            new_region["polygon"] = new_poly
            
        # Transform bbox [x, y, w, h]
        if "bbox" in region:
            bbox = region["bbox"]
            new_x = (bbox[0] - pad_left) / scale
            new_y = (bbox[1] - pad_top) / scale
            new_w = bbox[2] / scale
            new_h = bbox[3] / scale
            new_region["bbox"] = [new_x, new_y, new_w, new_h]
            
        transformed_result["text_regions"].append(new_region)
        
    return transformed_result
