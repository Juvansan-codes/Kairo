import argparse
import json
from pathlib import Path
from .datasets.manifest import CustomDatasetAdapter, CubiCasaAdapter, EvaluationSample
from .baselines.registry import METHODS, get_method
from .runners.runner import EvaluationRunner

def get_dataset(dataset_name: str):
    base_dir = Path(__file__).parent / "datasets"
    if dataset_name == "custom_synthetic_v1":
        return CustomDatasetAdapter(base_dir / "custom_synthetic_v1")
    elif dataset_name == "custom_real_v1":
        return CustomDatasetAdapter(base_dir / "custom_real_v1")
    elif dataset_name == "cubicasa":
        return CubiCasaAdapter()
    else:
        raise ValueError(f"Unknown dataset {dataset_name}")

def print_research_table(results_dir: Path, dataset_name: str):
    print("\nExperiment:")
    print(dataset_name)
    print("\nMethod                             WallIoU   RoomIoU   DimMAE    Runtime  ")
    print("-" * 75)
    
    # We want to print in a specific ablation order
    order = ["B0_Baseline", "B1_GeometryReconciled", "B2_MetricCalibrated", "B3_TopologyValidated", "OURS_v1", "Raster2Seq"]
    
    # Gather all JSONs
    data = {}
    for f in results_dir.glob(f"*_{dataset_name}_results.json"):
        with open(f, "r") as json_f:
            res = json.load(json_f)
            data[res["experiment"]] = res
            
    for method_name in order:
        if method_name not in data:
            # If not run, mark N/A
            print(f"{method_name:<34} {'N/A':<9} {'N/A':<9} {'N/A':<9} {'N/A':<9}")
            continue
            
        res = data[method_name]
        if "error" in res and res["error"] == "METHOD_UNAVAILABLE":
            print(f"{method_name:<34} {'UNAVAIL':<9} {'UNAVAIL':<9} {'UNAVAIL':<9} {'UNAVAIL':<9}")
            continue
            
        agg = res.get("aggregate_metrics", {})
        
        wiou = f"{agg.get('wall_iou', 0.0):.4f}" if agg.get('wall_iou') is not None else "N/A"
        riou = f"{agg.get('room_iou', 0.0):.4f}" if agg.get('room_iou') is not None else "N/A"
        dmae = f"{agg.get('dimension_mae_mm', 0.0):.4f}" if agg.get('dimension_mae_mm') is not None else "N/A"
        rt = f"{agg.get('inference_time_sec', 0.0):.4f}" if agg.get('inference_time_sec') is not None else "N/A"
        
        print(f"{method_name:<34} {wiou:<9} {riou:<9} {dmae:<9} {rt:<9}")

def main():
    parser = argparse.ArgumentParser(description="Kairo Evaluation CLI")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset to evaluate on")
    parser.add_argument("--method", type=str, required=False, help="Method to evaluate")
    parser.add_argument("--all-methods", action="store_true", help="Run all ablation variants")
    
    args = parser.parse_args()
    results_dir = Path(__file__).parent / "results"
    
    methods_to_run = []
    if args.all_methods:
        methods_to_run = ["baseline", "geometry_reconciled", "metric_calibrated", "topology_validated", "full_mgr", "raster2seq"]
    elif args.method:
        methods_to_run = [args.method]
    else:
        print("Must specify --method or --all-methods")
        return
        
    adapter = get_dataset(args.dataset)
    samples = adapter.load()
    if not samples:
        print(f"No samples found in dataset {args.dataset}.")
        return

    for m_name in methods_to_run:
        method = get_method(m_name)
        runner = EvaluationRunner(method, results_dir)
        try:
            results = runner.run(args.dataset, samples)
        except NotImplementedError as e:
            if str(e) == "METHOD_UNAVAILABLE":
                # Save unavailable state
                out_file = results_dir / f"{method.name}_{args.dataset}_results.json"
                with open(out_file, "w") as f:
                    json.dump({"experiment": method.name, "dataset": args.dataset, "error": "METHOD_UNAVAILABLE"}, f)
                print(f"Method {method.name} is unavailable. Skipped.")
            else:
                raise
                
    # Finally, print aggregate table
    print_research_table(results_dir, args.dataset)

if __name__ == "__main__":
    main()
