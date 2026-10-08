import json
from pathlib import Path
from typing import List
from ..schema import EvaluationSample, GroundTruth

class DatasetAdapter:
    def load(self, split: str) -> List[EvaluationSample]:
        raise NotImplementedError

class CustomDatasetAdapter(DatasetAdapter):
    def __init__(self, dataset_dir: Path):
        self.dataset_dir = dataset_dir
        self.manifest_path = dataset_dir / "manifest.json"

    def load(self, split: str = "all") -> List[EvaluationSample]:
        if not self.manifest_path.exists():
            return []
            
        with open(self.manifest_path, "r") as f:
            manifest = json.load(f)
            
        samples = []
        for item in manifest.get("samples", []):
            sample_id = item["id"]
            if item.get("status") != "annotated":
                print(f"Sample {sample_id} status is '{item.get('status')}'. Skipping.")
                continue
            
            img_path = str(self.dataset_dir.parent.parent.parent / item["image"])
            gt_path = self.dataset_dir.parent.parent.parent / item.get("ground_truth", "")
            
            gt = None
            if gt_path.exists() and gt_path.is_file():
                with open(gt_path, "r") as gf:
                    gt_data = json.load(gf)
                    gt = GroundTruth(**gt_data)
                    
            samples.append(EvaluationSample(sample_id=sample_id, input_path=img_path, ground_truth=gt))
            
        return samples

class CubiCasaAdapter(DatasetAdapter):
    def load(self, split: str) -> List[EvaluationSample]:
        # TODO: Implement conversion logic for CubiCasa5K annotations
        # This acts as a stub allowing future benchmarks without breaking API
        return []
