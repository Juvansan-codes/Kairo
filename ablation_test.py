import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evaluation.baselines.registry import get_method

def main():
    input_img = "evaluation/datasets/custom_synthetic_v1/plan_001.png"
    
    for method_name in ["baseline", "geometry_reconciled", "metric_calibrated", "topology_validated", "ours"]:
        method = get_method(method_name)
        print(f"--- Running {method.name} ---")
        result = method.reconstruct(input_img)
        walls = result.get("walls", [])
        rooms = result.get("rooms", [])
        doors = result.get("doors", [])
        scale = result.get("scale_mm_per_px")
        valid = result.get("confidence", {}).get("topology_valid")
        print(f"Walls: {len(walls)}, Rooms: {len(rooms)}, Doors: {len(doors)}, Scale: {scale}, TopologyValid: {valid}\n")

if __name__ == "__main__":
    main()
