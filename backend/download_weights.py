import os
from huggingface_hub import hf_hub_download
from pathlib import Path

def download_model():
    repo_id = "Yytsi/floorplan-to-3d-walls"
    save_dir = Path("d:/College Files/Kairo/backend/models/weights")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    print("Downloading config.yaml...")
    cfg_path = hf_hub_download(repo_id=repo_id, filename="config.yaml", local_dir=str(save_dir))
    print(f"Config saved to {cfg_path}")
    
    print("Downloading best.safetensors...")
    model_path = hf_hub_download(repo_id=repo_id, filename="best.safetensors", local_dir=str(save_dir))
    print(f"Model saved to {model_path}")
    
    print("Download complete.")

if __name__ == "__main__":
    download_model()
