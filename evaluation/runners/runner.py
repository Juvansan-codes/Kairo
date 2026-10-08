import time
import json
from pathlib import Path
from ..schema import EvaluationSample, Prediction
from ..baselines.interface import ReconstructionBaseline
from ..metrics.layout import compute_wall_iou, compute_room_iou
from ..metrics.completeness import compute_room_recall, compute_door_recall, compute_window_recall
from ..metrics.dimensions import compute_dimension_error, compute_scale_error
from ..metrics.system import compute_inference_time

class EvaluationRunner:
    def __init__(self, method: ReconstructionBaseline, output_dir: Path):
        self.method = method
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_sample(self, sample: EvaluationSample) -> dict:
        print(f"Evaluating {sample.sample_id} with {self.method.name}...")
        
        start = time.time()
        try:
            raw_res = self.method.reconstruct(sample.input_path)
            # Parse raw_res into our Prediction schema
            # This adapter step ensures different baselines output common format
            metadata = raw_res.get("metadata", {})
            pred = Prediction(
                walls=raw_res.get("walls", []),
                rooms=raw_res.get("rooms", []),
                doors=raw_res.get("doors", []),
                windows=raw_res.get("windows", []),
                dimensions=raw_res.get("dimensions", []),
                scale_mm_per_px=raw_res.get("scale_mm_per_px") or metadata.get("scale", {}).get("scale_mm_per_px"),
                inference_time_sec=time.time() - start
            )
            sample.prediction = pred
        except Exception as e:
            print(f"  Failed: {e}")
            sample.prediction = None
            
        # Compute individual metrics if ground truth exists
        metrics = {
            "wall_iou": None,
            "room_iou": None,
            "room_recall": None,
            "door_recall": None,
            "window_recall": None,
            "dimension_mae_mm": None,
            "dimension_mre": None,
            "scale_mae": None,
            "scale_mre": None,
            "inference_time_sec": None
        }
        
        if sample.prediction:
            metrics["inference_time_sec"] = sample.prediction.inference_time_sec
            if sample.ground_truth:
                metrics["wall_iou"] = compute_wall_iou(sample.prediction, sample.ground_truth)
                metrics["room_iou"] = compute_room_iou(sample.prediction, sample.ground_truth)
                
                rm_rec = compute_room_recall(sample.prediction, sample.ground_truth)
                metrics["room_recall"] = rm_rec[0] if rm_rec else None
                
                dr_rec = compute_door_recall(sample.prediction, sample.ground_truth)
                metrics["door_recall"] = dr_rec[0] if dr_rec else None
                
                wn_rec = compute_window_recall(sample.prediction, sample.ground_truth)
                metrics["window_recall"] = wn_rec[0] if wn_rec else None
                
                mae, mre = compute_dimension_error(sample.prediction, sample.ground_truth)
                metrics["dimension_mae_mm"] = mae
                metrics["dimension_mre"] = mre
                
                smae, smre = compute_scale_error(sample.prediction, sample.ground_truth)
                metrics["scale_mae"] = smae
                metrics["scale_mre"] = smre
            else:
                print("  Ground truth unavailable, metric not computed")
                
        return {
            "sample_id": sample.sample_id,
            "metrics": metrics
        }
        
    def run(self, dataset_name: str, samples: list[EvaluationSample]):
        results = []
        for s in samples:
            res = self.evaluate_sample(s)
            results.append(res)
            
        # Aggregate
        # For simplicity, mean of non-null values
        agg_metrics = {}
        for k in results[0]["metrics"].keys():
            vals = [r["metrics"][k] for r in results if r["metrics"][k] is not None]
            agg_metrics[k] = sum(vals) / len(vals) if vals else None
            
        final_report = {
            "experiment": self.method.name,
            "dataset": dataset_name,
            "aggregate_metrics": agg_metrics,
            "sample_results": results
        }
        
        out_file = self.output_dir / f"{self.method.name}_{dataset_name}_results.json"
        with open(out_file, "w") as f:
            json.dump(final_report, f, indent=2)
            
        print(f"Saved results to {out_file}")
        return final_report
