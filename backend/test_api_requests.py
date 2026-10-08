import time
import requests
from pathlib import Path

def test_full_api_flow():
    test_img = Path(r"d:\College Files\Kairo\evaluation\datasets\custom_real_v1\real_001.png")
    
    print("Uploading file to local API...")
    with open(test_img, "rb") as f:
        response = requests.post("http://127.0.0.1:8000/api/reconstruct", files={"file": ("real_001.png", f, "image/png")})
    
    assert response.status_code == 200, f"Upload failed: {response.text}"
    job_id = response.json()["job_id"]
    print(f"Job registered: {job_id}")
    
    while True:
        status_res = requests.get(f"http://127.0.0.1:8000/api/reconstruct/{job_id}")
        data = status_res.json()
        status = data["status"]
        print(f"Status: {status}, Stage: {data.get('stage')}")
        if status == "completed": break
        elif status == "failed": return False
        time.sleep(2)
        
    print("Fetching model...")
    model_res = requests.get(f"http://127.0.0.1:8000/api/result/{job_id}/model")
    assert model_res.status_code == 200
    assert "model/gltf-binary" in model_res.headers["content-type"]
    assert len(model_res.content) > 0
    print(f"Model downloaded! Size: {len(model_res.content)} bytes")
    print("API TEST SUCCESSFUL")
    return True

if __name__ == "__main__":
    # Wait for server to start
    time.sleep(3)
    test_full_api_flow()
