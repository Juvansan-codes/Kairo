import cv2
import numpy as np
from typing import Dict, Any
from pathlib import Path

def draw_ocr_debug(image_path: str, ocr_result: Dict[str, Any], output_path: str):
    """
    Draws bounding boxes, polygons, and text from the OCR result onto the image.
    Saves the output to output_path.
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image {image_path}")
        return
        
    for region in ocr_result.get("text_regions", []):
        polygon = region.get("polygon")
        text = region.get("text", "")
        confidence = region.get("confidence", 0.0)
        
        # Draw Polygon
        if polygon:
            pts = np.array(polygon, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(image, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
            
            # Text background and text
            x, y = int(polygon[0][0]), int(polygon[0][1])
            label = f"{text} ({confidence:.2f})"
            font_scale = 0.5
            thickness = 1
            font = cv2.FONT_HERSHEY_SIMPLEX
            (w, h), _ = cv2.getTextSize(label, font, font_scale, thickness)
            
            # Background rectangle for text visibility
            cv2.rectangle(image, (x, y - h - 5), (x + w, y), (0, 0, 0), -1)
            cv2.putText(image, label, (x, y - 5), font, font_scale, (0, 255, 0), thickness)
            
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_path, image)
    print(f"OCR debug visualization saved to {output_path}")

