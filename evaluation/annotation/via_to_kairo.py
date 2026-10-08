import json
import argparse
from pathlib import Path

def convert_via_to_kairo(via_json_path, output_json_path, sample_id, scale_mm_per_px=None):
    with open(via_json_path, 'r') as f:
        via_data = json.load(f)

    kairo_data = {
        "id": sample_id,
        "walls": [],
        "rooms": [],
        "doors": [],
        "windows": [],
        "dimensions": [],
        "scale_mm_per_px": scale_mm_per_px
    }

    wall_idx = 1
    room_idx = 1
    door_idx = 1
    window_idx = 1

    # VIA JSON format is a dict of metadata objects, one per image
    # Extract regions from all images (assuming one image's worth of data was exported for this sample)
    for img_key, img_data in via_data.items():
        if "regions" not in img_data:
            continue
        
        # VIA 2.x regions can be a list or dict
        regions = img_data["regions"]
        if isinstance(regions, dict):
            regions = regions.values()

        for region in regions:
            shape = region.get("shape_attributes", {})
            region_attr = region.get("region_attributes", {})
            label = region_attr.get("label", "").lower()

            if not label:
                continue

            if label == "wall" and shape.get("name") in ["polyline", "polygon", "line"]:
                # Convert VIA points to [[x,y], [x,y]]
                xs = shape.get("all_points_x", [])
                ys = shape.get("all_points_y", [])
                if not xs and shape.get("name") == "line":
                    # Some VIA versions for line: x1, y1, x2, y2
                    xs = [shape.get("x1"), shape.get("x2")]
                    ys = [shape.get("y1"), shape.get("y2")]
                
                if len(xs) >= 2:
                    pts = [[x, y] for x, y in zip(xs, ys)]
                    kairo_data["walls"].append({
                        "id": f"W{wall_idx}",
                        "geometry": pts
                    })
                    wall_idx += 1

            elif label == "room" and shape.get("name") == "polygon":
                xs = shape.get("all_points_x", [])
                ys = shape.get("all_points_y", [])
                if len(xs) >= 3:
                    pts = [[x, y] for x, y in zip(xs, ys)]
                    kairo_data["rooms"].append({
                        "id": f"R{room_idx}",
                        "polygon": pts
                    })
                    room_idx += 1

            elif label in ["door", "window"]:
                pts = []
                if shape.get("name") == "rect":
                    x = shape.get("x")
                    y = shape.get("y")
                    w = shape.get("width")
                    h = shape.get("height")
                    pts = [[x, y], [x+w, y], [x+w, y+h], [x, y+h]]
                elif shape.get("name") == "polygon":
                    xs = shape.get("all_points_x", [])
                    ys = shape.get("all_points_y", [])
                    pts = [[x, y] for x, y in zip(xs, ys)]
                
                if pts:
                    if label == "door":
                        kairo_data["doors"].append({"id": f"D{door_idx}", "polygon": pts})
                        door_idx += 1
                    else:
                        kairo_data["windows"].append({"id": f"Win{window_idx}", "polygon": pts})
                        window_idx += 1

    with open(output_json_path, 'w') as f:
        json.dump(kairo_data, f, indent=2)
    
    print(f"Converted {via_json_path} -> {output_json_path}")
    print(f"Found {len(kairo_data['walls'])} walls, {len(kairo_data['rooms'])} rooms, {len(kairo_data['doors'])} doors, {len(kairo_data['windows'])} windows.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert VIA JSON to Kairo GroundTruth format")
    parser.add_argument("--via", required=True, help="Path to VIA JSON file")
    parser.add_argument("--out", required=True, help="Path to output Kairo JSON file")
    parser.add_argument("--id", required=True, help="Sample ID (e.g. real_001)")
    parser.add_argument("--scale", type=float, default=None, help="Scale mm per px (optional)")
    args = parser.parse_args()
    
    convert_via_to_kairo(args.via, args.out, args.id, args.scale)
