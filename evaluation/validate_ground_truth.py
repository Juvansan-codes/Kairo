import json
import argparse
from pathlib import Path
from shapely.geometry import Polygon, LineString

def validate_json(filepath):
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Invalid JSON: {e}"
        
    if "id" not in data:
        return False, "Missing 'id' field"
        
    # Check rooms
    if "rooms" in data:
        for i, room in enumerate(data["rooms"]):
            if "polygon" not in room:
                return False, f"Room {i} missing 'polygon'"
            poly = Polygon(room["polygon"])
            if not poly.is_valid:
                return False, f"Room {i} polygon is invalid (e.g. self-intersecting)"
            if poly.area == 0:
                return False, f"Room {i} has zero area"
                
    # Check walls
    if "walls" in data:
        for i, wall in enumerate(data["walls"]):
            if "geometry" not in wall:
                return False, f"Wall {i} missing 'geometry'"
            if len(wall["geometry"]) < 2:
                return False, f"Wall {i} geometry has < 2 points"
            line = LineString(wall["geometry"])
            if line.length == 0:
                return False, f"Wall {i} has zero length"

    # Check scale
    if "scale_mm_per_px" in data and data["scale_mm_per_px"] is not None:
        if data["scale_mm_per_px"] <= 0:
            return False, "Scale must be > 0"
            
    # Check dimensions
    if "dimensions" in data:
        for i, dim in enumerate(data["dimensions"]):
            if "value_mm" not in dim:
                return False, f"Dimension {i} missing 'value_mm'"
            if dim["value_mm"] < 0:
                return False, f"Dimension {i} cannot be negative"
                
    return True, "Valid"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Dataset name, e.g. custom_v1")
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent
    dataset_dir = base_dir / "datasets" / args.dataset
    
    if not dataset_dir.exists():
        print(f"Dataset directory not found: {dataset_dir}")
        return
        
    manifest_path = dataset_dir / "manifest.json"
    if not manifest_path.exists():
        print("Manifest not found.")
        return
        
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    print(f"Validating {args.dataset}...")
    all_valid = True
    
    for s in manifest.get("samples", []):
        sample_id = s.get("id")
        if s.get("status") == "pending":
            print(f"  [PENDING] {sample_id} - Skipping validation")
            continue
            
        gt_path = base_dir.parent / s.get("ground_truth", "")
        if not gt_path.exists():
            print(f"  [FAIL] {sample_id}: Ground truth file missing at {gt_path}")
            all_valid = False
            continue
            
        valid, msg = validate_json(gt_path)
        if valid:
            print(f"  [OK] {sample_id}")
        else:
            print(f"  [FAIL] {sample_id}: {msg}")
            all_valid = False
            
    if all_valid:
        print("\nAll ground truth annotations passed validation.")
    else:
        print("\nSome ground truth annotations failed validation.")
        exit(1)

if __name__ == "__main__":
    main()
