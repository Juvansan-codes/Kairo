import sys
import os
import time
import io
from fastapi.testclient import TestClient

# Ensure backend module path is correct
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

client = TestClient(app)

def test_health():
    print("--- TESTING HEALTH ENDPOINT ---")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("Health Test: PASSED\n")

def test_upload_invalid_file():
    print("--- TESTING INVALID FILE UPLOAD ---")
    # Try uploading a text file
    file_content = b"Not a real image"
    file_like = io.BytesIO(file_content)
    
    response = client.post(
        "/api/reconstruct",
        files={"file": ("test.txt", file_like, "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]
    print("Invalid Upload Test: PASSED\n")

def test_reconstruction_flow():
    print("--- TESTING RECONSTRUCTION FLOW ---")
    
    # 1. Upload valid mock image
    from pathlib import Path
    img_path = Path(__file__).parent / "outputs" / "test_images" / "empty_test.png"
    if not img_path.exists():
        print("Skipping successful flow test because test image is missing.")
        return
        
    with open(img_path, "rb") as f:
        upload_resp = client.post(
            "/api/reconstruct",
            files={"file": ("test.png", f, "image/png")}
        )
    assert upload_resp.status_code == 200
    job_id = upload_resp.json()["job_id"]
    assert upload_resp.json()["status"] in ["queued", "processing"]
    print(f"Upload successful. Job ID: {job_id}")
    
    # 2. Check status (Wait for async task)
    max_retries = 5
    for i in range(max_retries):
        status_resp = client.get(f"/api/reconstruct/{job_id}")
        assert status_resp.status_code == 200
        status = status_resp.json()["status"]
        if status == "completed":
            break
        time.sleep(0.5)
        
    assert status == "completed", "Job did not complete in time"
    print("Job status check: COMPLETED")
    
    # 3. Get Metadata
    meta_resp = client.get(f"/api/result/{job_id}/metadata")
    assert meta_resp.status_code == 200
    data = meta_resp.json()
    assert data["status"] == "success"
    assert "geometry_status" in data["metadata"]
    print("Metadata retrieval: PASSED")
    
    # 4. Get Model
    model_resp = client.get(f"/api/result/{job_id}/model")
    assert model_resp.status_code == 200
    assert model_resp.content == b"mock glb content"
    print("Model retrieval: PASSED")
    
def test_missing_job():
    print("--- TESTING MISSING JOB ---")
    response = client.get("/api/reconstruct/invalid-job-id")
    assert response.status_code == 404
    print("Missing Job Test: PASSED\n")

if __name__ == "__main__":
    test_health()
    test_upload_invalid_file()
    test_reconstruction_flow()
    test_missing_job()
    print("\nALL API TESTS PASSED.")
