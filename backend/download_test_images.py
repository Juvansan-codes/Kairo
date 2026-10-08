import urllib.request
import os
from pathlib import Path

def download_test_images():
    output_dir = Path(r"d:\College Files\Kairo\backend\outputs\test_images")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    urls = [
        ("F1_scaled.png", "https://raw.githubusercontent.com/CubiCasa/CubiCasa5k/master/sample_data/F1_scaled.png"),
        ("F2_scaled.png", "https://raw.githubusercontent.com/CubiCasa/CubiCasa5k/master/sample_data/F2_scaled.png"),
        ("F3_scaled.png", "https://raw.githubusercontent.com/CubiCasa/CubiCasa5k/master/sample_data/F3_scaled.png")
    ]
    
    for filename, url in urls:
        path = output_dir / filename
        print(f"Downloading {filename}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(path, 'wb') as out_file:
                data = response.read()
                out_file.write(data)
            print(f"Saved to {path}")
        except Exception as e:
            print(f"Failed to download {filename}: {e}")

if __name__ == "__main__":
    download_test_images()
