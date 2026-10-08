import os
import json
from PIL import Image, ImageDraw
from pathlib import Path

def create_dataset():
    ds_dir = Path(__file__).parent / "datasets" / "custom_synthetic_v1"
    gt_dir = Path(__file__).parent / "ground_truth" / "custom_synthetic_v1"
    
    ds_dir.mkdir(parents=True, exist_ok=True)
    gt_dir.mkdir(parents=True, exist_ok=True)
    
    samples = []
    
    # Generate 5 simple plans
    for i in range(1, 6):
        name = f"plan_{i:03d}"
        img_path = ds_dir / f"{name}.png"
        gt_path = gt_dir / f"{name}.json"
        
        # 1. Create a simple white image
        img = Image.new("RGB", (512, 512), "white")
        draw = ImageDraw.Draw(img)
        
        # We'll draw a square room with black walls
        # Let's vary the size slightly per plan
        margin = 50 + i*10
        left, top, right, bottom = margin, margin, 512-margin, 512-margin
        
        # Draw floor (grayish)
        draw.rectangle([left, top, right, bottom], fill=(240, 240, 235))
        # Draw walls (thick black lines)
        thickness = 10
        draw.line([(left, top), (right, top)], fill="black", width=thickness)
        draw.line([(right, top), (right, bottom)], fill="black", width=thickness)
        draw.line([(right, bottom), (left, bottom)], fill="black", width=thickness)
        draw.line([(left, bottom), (left, top)], fill="black", width=thickness)
        
        img.save(img_path)
        
        # 2. Create the exact ground truth
        gt = {
            "id": name,
            "walls": [
                {"id": "W1", "geometry": [[left, top], [right, top]]},
                {"id": "W2", "geometry": [[right, top], [right, bottom]]},
                {"id": "W3", "geometry": [[right, bottom], [left, bottom]]},
                {"id": "W4", "geometry": [[left, bottom], [left, top]]}
            ],
            "rooms": [
                {"id": "R1", "polygon": [[left, top], [right, top], [right, bottom], [left, bottom]], "label": "Room"}
            ],
            "doors": [],
            "windows": [],
            "dimensions": [
                {"id": "D1", "value_mm": (right - left) * 20.0}
            ],
            "scale_mm_per_px": 20.0
        }
        
        with open(gt_path, "w") as f:
            json.dump(gt, f, indent=2)
            
        samples.append({
            "id": name,
            "image": f"evaluation/datasets/custom_synthetic_v1/{name}.png",
            "ground_truth": f"evaluation/ground_truth/custom_synthetic_v1/{name}.json",
            "status": "annotated"
        })
        
    # Write manifest
    manifest = {
        "dataset_version": "1.0",
        "samples": samples
    }
    
    with open(ds_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    print("Created 5 synthetic annotated plans.")

if __name__ == "__main__":
    create_dataset()
