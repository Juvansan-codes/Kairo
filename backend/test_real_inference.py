import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app.perception.adapter import ResNetUNetPerception

def main():
    print("Loading ResNetUNetPerception model...")
    run_dir = Path(r"d:\College Files\Kairo\backend\models\floorplan-to-3d-walls-repo")
    try:
        model = ResNetUNetPerception(run_dir)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    images_dir = Path(r"d:\College Files\Kairo\backend\outputs\test_images")
    output_dir = Path(r"d:\College Files\Kairo\backend\outputs\debug")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    test_files = list(images_dir.glob("*.png"))
    if not test_files:
        print("No test images found.")
        return
        
    for img_path in test_files:
        print(f"\nProcessing {img_path.name}...")
        out_file = output_dir / f"debug_{img_path.name}"
        try:
            result = model.create_debug_visualization(img_path, out_file)
            print(f"Inference Time: {result['inference_time']:.4f}s")
            print("Detected Classes:", result["class_counts"])
            print(f"Debug image saved to {out_file}")
        except Exception as e:
            print(f"Inference failed for {img_path.name}: {e}")

if __name__ == "__main__":
    main()
