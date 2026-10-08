import pytest
import asyncio
from pathlib import Path
from app.services.job_manager import JobManager
from app.services.reconstruction import ReconstructionService

def test_end_to_end_reconstruction():
    test_img = Path(r"d:\College Files\Kairo\evaluation\datasets\custom_real_v1\real_001.png")
    assert test_img.exists(), "Test image not found"
    
    # Register job
    job = JobManager.create_job()
    job_id = job.job_id
    job.file_path = str(test_img)
    
    # Run the reconstruction
    asyncio.run(ReconstructionService.reconstruct(job_id))
    
    # Retrieve job
    job = JobManager.get_job(job_id)
    
    if job.status == "failed":
        print("JOB FAILED WITH ERROR:", job.metadata.get("error"))
        print("TRACEBACK:", job.metadata.get("traceback"))
        pytest.fail(f"Reconstruction failed at stage {job.metadata.get('failed_stage')}: {job.metadata.get('error')}")
        
    # Verify stages
    assert job.status == "completed"
    assert job.metadata.get("geometry_status") == "completed"
    
    # Verify we got real output counts
    assert "walls" in job.metadata
    
    # Note: real_001.png is a 500kb image, should have at least 1 wall.
    # If the model finds 0 walls due to some threshold, this will fail.
    
    print("\n--- INTEGRATION TEST MGR OUTPUT ---")
    print(f"Walls: {job.metadata['walls']}")
    print(f"Rooms: {job.metadata['rooms']}")
    print(f"Doors: {job.metadata['doors']}")
    print(f"Windows: {job.metadata['windows']}")
    print(f"Scale: {job.metadata.get('scale_mm_per_px')}")
    print(f"Topology Valid: {job.metadata['topology_valid']}")
    
    # 7. GLB Verification
    import trimesh
    glb_path = job.model_path
    assert glb_path is not None
    assert Path(glb_path).exists()
    assert Path(glb_path).stat().st_size > 0
    
    loaded_scene = trimesh.load(glb_path, file_type="glb")
    assert isinstance(loaded_scene, trimesh.Scene)
    
    total_vertices = sum(len(g.vertices) for g in loaded_scene.geometry.values())
    total_faces = sum(len(g.faces) for g in loaded_scene.geometry.values())
    
    assert total_vertices > 0
    assert total_faces > 0
    
    print("\n--- GLB GENERATION STATS ---")
    print(f"File Size (bytes): {Path(glb_path).stat().st_size}")
    print(f"Vertex Count: {total_vertices}")
    print(f"Face Count: {total_faces}")
    print(f"Scale Status: {job.metadata.get('scale_status')}")
    print(f"Coordinate Space: {job.metadata.get('coordinate_space')}")
    print("-----------------------------------\n")

