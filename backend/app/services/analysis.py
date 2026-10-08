import os
from pathlib import Path
from app.perception.adapter import ResNetUNetPerception
from app.ocr.engine import PaddleOCREngine
from app.dimensions.parser import parse_dimensions
from app.scale.service import associate_dimensions
from app.dimensions.vlm import DimensionVerifier

class PerceptionAnalysisService:
    def __init__(self, use_raster2seq: bool = False):
        """
        Initialize perception analysis service with model selection.
        
        Parameters
        ----------
        use_raster2seq : bool
            If True, attempt to use Raster2Seq model (requires installation).
            If False or Raster2Seq unavailable, use ResNet34-U-Net fallback.
        """
        # Initialize perception model
        if use_raster2seq:
            try:
                from app.perception.raster2seq_adapter import get_raster2seq_adapter
                self.perception = get_raster2seq_adapter("cubicasa5k")
                self.model_name = "Raster2Seq"
                print("[+] Using Raster2Seq (primary model)")
            except (ImportError, ModuleNotFoundError, FileNotFoundError) as e:
                print(f"[!] Raster2Seq unavailable: {e}")
                print("[!] Falling back to ResNet34-U-Net with fragment connection")
                self._init_resnet_fallback()
        else:
            self._init_resnet_fallback()
        
        # Initialize OCR
        self.ocr = PaddleOCREngine(use_angle_cls=True, lang="en")
        
        # Initialize VLM verifier if API key available
        api_key = os.getenv("OPENAI_API_KEY")
        self.vlm_verifier = DimensionVerifier(api_key=api_key) if api_key else None

    def _init_resnet_fallback(self):
        """Initialize ResNet34-U-Net fallback model with wall improvement."""
        run_dir = Path(r"d:\College Files\Kairo\backend\models\floorplan-to-3d-walls-repo")
        self.perception = ResNetUNetPerception(run_dir, improve_walls=True)
        self.model_name = "ResNet34-U-Net"
        print(f"[+] Using {self.model_name} with fragment connection")

    def analyze(self, image_path: str, job) -> dict:
        job.stage = "PERCEPTION"
        perc_res = self.perception.predict(Path(image_path))
        
        job.stage = "OCR"
        ocr_res = self.ocr.extract(image_path)
        text_regions = ocr_res.get("text_regions", [])
        
        job.stage = "DIMENSIONS"
        dim_res = parse_dimensions(text_regions, vlm_verifier=self.vlm_verifier)
        
        job.stage = "SCALE"
        scale_res = associate_dimensions(perc_res, dim_res)
        
        # Package into a structured analysis result dict
        # We preserve the raw objects in case they're needed, but also extract serializable metadata
        return {
            "perception_result": perc_res,
            "ocr_result": ocr_res,
            "dimension_result": dim_res,
            "scale_result": scale_res,
            "metadata": {
                "analysis": {
                    "rooms": len(perc_res.get("rooms", [])),
                    "walls": len(perc_res.get("walls", [])),
                    "doors": len(perc_res.get("doors", [])),
                    "windows": len(perc_res.get("windows", []))
                },
                "scale": {
                    "scale_mm_per_px": scale_res.scale_mm_per_px,
                    "scale_confidence": scale_res.scale_confidence,
                    "scale_source": scale_res.scale_source
                },
                "provenance": {
                    "perception_model": "ResNet34-U-Net",
                    "ocr_model": "PaddleOCR",
                    "scale_associations_count": len(scale_res.associations),
                    "vlm_enabled": self.vlm_verifier is not None
                }
            }
        }
