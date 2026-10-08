import cv2
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union
from pathlib import Path

class OCREngine(ABC):
    @abstractmethod
    def extract(self, image: Union[str, np.ndarray]) -> Dict[str, Any]:
        """
        Extract text from an image.
        Returns a dictionary containing 'text_regions' formatted according to SCHEMA.md.
        """
        pass

class PaddleOCREngine(OCREngine):
    def __init__(self, use_angle_cls: bool = True, lang: str = 'en'):
        """
        Initialize the PaddleOCR engine.
        use_angle_cls: If True, identifies text orientation/rotation.
        lang: Language for OCR.
        """
        from paddleocr import PaddleOCR
        import os
        os.environ["FLAGS_use_mkldnn"] = "0"
        # Initialize PaddleOCR
        # use_angle_cls enables rotation classification
        # show_log=False prevents excessive console spam
        self.ocr = PaddleOCR(use_angle_cls=use_angle_cls, lang=lang, show_log=False)
        self.provenance = {"engine": "paddleocr"}

    def extract(self, image: Union[str, np.ndarray]) -> Dict[str, Any]:
        # Handle empty or invalid image path
        if isinstance(image, str):
            if not Path(image).exists():
                return {"text_regions": []}
        
        # PaddleOCR returns a list of results.
        # For a single image, result is typically a list containing one element (which is a list of detections).
        try:
            result = self.ocr.ocr(image, cls=True)
        except Exception as e:
            print(f"OCR Error: {e}")
            return {"text_regions": []}
            
        regions = []
        if not result or result[0] is None:
            return {"text_regions": []}
            
        detections = result[0]
        
        for detection in detections:
            # detection format: [[[x1, y1], [x2, y2], [x3, y3], [x4, y4]], ('text', confidence)]
            polygon = detection[0]
            text_tuple = detection[1]
            text_string = text_tuple[0]
            confidence = float(text_tuple[1])
            
            # Calculate bounding box [x, y, w, h] from polygon
            # polygon format is generally [top-left, top-right, bottom-right, bottom-left] but can be rotated
            xs = [point[0] for point in polygon]
            ys = [point[1] for point in polygon]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            
            bbox = [x_min, y_min, x_max - x_min, y_max - y_min]
            
            # Optional semantic classification hint (Phase 3 only asks for basic hint, Phase 4 does proper dimension logic)
            hint = "numeric_like" if any(char.isdigit() for char in text_string) else "text_like"
            
            # We don't have exact orientation degrees from PaddleOCR's basic output unless we calculate it 
            # from the polygon slope. We can estimate orientation using top-left and top-right points.
            dx = polygon[1][0] - polygon[0][0]
            dy = polygon[1][1] - polygon[0][1]
            angle = float(np.degrees(np.arctan2(dy, dx)))
            
            region = {
                "text": text_string,
                "bbox": bbox,
                "polygon": polygon,
                "confidence": confidence,
                "orientation": angle,
                "hint": hint,
                "provenance": self.provenance
            }
            regions.append(region)
            
        return {"text_regions": regions}
