import os
import time
import urllib.request
import urllib.error
from pathlib import Path

def resume_download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    
    while True:
        headers = {'User-Agent': 'Mozilla/5.0'}
        file_size = 0
        if path.exists():
            file_size = path.stat().st_size
            headers['Range'] = f'bytes={file_size}-'
            print(f"Resuming from {file_size} bytes...")
            
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(path, 'ab') as out_file:
                    while True:
                        chunk = response.read(65536)
                        if not chunk:
                            break
                        out_file.write(chunk)
            print(f"Download complete: {path.name}")
            break
        except urllib.error.HTTPError as e:
            if e.code == 416: # Range Not Satisfiable
                print("Download already complete.")
                break
            print(f"HTTP Error: {e}")
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}. Retrying...")
            time.sleep(2)

if __name__ == "__main__":
    weights_path = Path(r"d:\College Files\Kairo\backend\models\weights\best.safetensors")
    weights_url = "https://huggingface.co/Yytsi/floorplan-to-3d-walls/resolve/main/best.safetensors"
    resume_download(weights_url, weights_path)
