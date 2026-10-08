import sys
import os
import time
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

client = TestClient(app)

def test_real_floorplans():
    test_dir = Path(r"d:\College Files\Kairo\backend\outputs\test_images")
    if not test_dir.exists():
        print(f"Test directory not found: {test_dir}")
        return
        
    test_images = list(test_dir.glob("*.png"))
    if not test_images:
        print("No test images found.")
        return
        
    print(f"--- TESTING {len(test_images)} REAL FLOORPLANS ---")
    
    for img_path in test_images:
        print(f"\nProcessing {img_path.name}...")
        
        # 1. Upload
        start_time = time.time()
        with open(img_path, "rb") as f:
            upload_resp = client.post(
                "/api/reconstruct",
                files={"file": (img_path.name, f, "image/png")}
            )
        
        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        job_id = upload_resp.json()["job_id"]
        print(f"  Job created: {job_id}")
        
        # 2. Poll for completion
        # For TestClient, background tasks run after the request returns, synchronously if awaited?
        # Actually TestClient in FastAPI runs background tasks synchronously after returning the response!
        # So by the time `client.post` returns, the background task HAS ALREADY FINISHED in TestClient.
        # This means the job status should immediately be "completed" or "failed".
        
        status_resp = client.get(f"/api/reconstruct/{job_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        status = status_data["status"]
        
        end_time = time.time()
        print(f"  Final Status: {status} (Took {end_time - start_time:.2f}s)")
        
        if status == "failed":
            # Let's see what went wrong (in our hacky job state we stored it in metadata)
            meta_resp = client.get(f"/api/result/{job_id}/metadata")
            # Usually we'd check error endpoint, but let's peek the job directly
            from app.services.job_manager import JobManager
            job = JobManager.get_job(job_id)
            print(f"  FAILED STAGE: {job.metadata.get('failed_stage')}")
            print(f"  ERROR: {job.metadata.get('error')}")
            continue
            
        assert status == "completed", "Job did not complete successfully"
        
        # 3. Metadata
        meta_resp = client.get(f"/api/result/{job_id}/metadata")
        assert meta_resp.status_code == 200
        meta = meta_resp.json()["metadata"]
        
        # 4. Verify Member 1 real results are in metadata
        print("  --- METADATA ---")
        print(f"  Geometry Status: {meta.get('geometry_status')}")
        
        analysis = meta.get("analysis", {})
        print(f"  Rooms: {analysis.get('rooms')}")
        print(f"  Walls: {analysis.get('walls')}")
        
        scale = meta.get("scale", {})
        print(f"  Scale: {scale.get('scale_mm_per_px')} mm/px")
        print(f"  Scale Source: {scale.get('scale_source')}")
        
        prov = meta.get("provenance", {})
        print(f"  Associations: {prov.get('scale_associations_count')}")
        
        # 5. Model
        model_resp = client.get(f"/api/result/{job_id}/model")
        assert model_resp.status_code == 200
        assert model_resp.content.startswith(b"mock glb content")

if __name__ == "__main__":
    test_real_floorplans()
    print("\nINTEGRATION TESTS FINISHED.")
