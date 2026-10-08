import urllib.request
import shutil
import time
from pathlib import Path

def download_with_retry(url, path, max_retries=3):
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(max_retries):
        try:
            print(f"Downloading {path.name} (Attempt {attempt+1}/{max_retries})...")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response, open(path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            print(f"Success: {path.name} downloaded. Size: {path.stat().st_size} bytes")
            return True
        except Exception as e:
            print(f"Failed: {e}")
            time.sleep(2)
    return False

def main():
    weights_path = Path(r"d:\College Files\Kairo\backend\models\weights\best.safetensors")
    weights_url = "https://huggingface.co/Yytsi/floorplan-to-3d-walls/resolve/main/best.safetensors"
    download_with_retry(weights_url, weights_path)

    images_dir = Path(r"d:\College Files\Kairo\backend\outputs\test_images")
    urls = [
        ("F1.png", "https://upload.wikimedia.org/wikipedia/commons/e/ec/Floor_plan_of_a_house.png"),
        ("F2.png", "https://upload.wikimedia.org/wikipedia/commons/c/c5/Floor_plan.png"),
    ]
    for name, url in urls:
        download_with_retry(url, images_dir / name)

if __name__ == "__main__":
    main()
