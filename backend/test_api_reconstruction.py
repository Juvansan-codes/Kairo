import time
from fastapi.testclient import TestClient
from pathlib import Path
from app.main import app

client = TestClient(app)

def test_full_api_flow():
    test_img = Path(r"d:\College Files\Kairo\evaluation\datasets\custom_real_v1\real_001.png")
    assert test_img.exists()
    
    print("Uploading file...")
    with open(test_img, "rb") as f:
        response = client.post("/api/v1/reconstruct", files={"file": ("real_001.png", f, "image/png")})
    
    assert response.status_code == 200, f"Upload failed: {response.text}"
    job_id = response.json()["job_id"]
    print(f"Job registered: {job_id}")
    
    # Poll for completion
    while True:
        status_res = client.get(f"/api/v1/reconstruct/{job_id}")
        data = status_res.json()
        status = data["status"]
        stage = data.get("stage")
        print(f"Status: {status}, Stage: {stage}")
        
        if status == "completed":
            print("Job completed!")
            break
        elif status == "failed":
            print("Job failed!")
            return False
            
        time.sleep(2)
        
    # Get Metadata
    print("Fetching metadata...")
    meta_res = client.get(f"/api/v1/result/{job_id}/metadata")
    assert meta_res.status_code == 200
    print("Metadata:", meta_res.json()["metadata"])
    
    # Get Model
    print("Fetching model...")
    model_res = client.get(f"/api/v1/result/{job_id}/model")
    assert model_res.status_code == 200
    assert model_res.headers["content-type"] == "model/gltf-binary"
    assert len(model_res.content) > 0
    print(f"Model downloaded! Size: {len(model_res.content)} bytes")
    
    print("API TEST SUCCESSFUL")
    return True

if __name__ == "__main__":
    test_full_api_flow()
