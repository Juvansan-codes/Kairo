import traceback
from .job_manager import JobManager
from .analysis import PerceptionAnalysisService
from .geometry import MockGeometryService
from .scene import MockSceneGenerationService

class ReconstructionService:
    # Initialize services (lazy loading or at startup)
    _analysis_service = None
    _geometry_service = MockGeometryService()
    _scene_service = MockSceneGenerationService()

    @classmethod
    def get_analysis_service(cls):
        if cls._analysis_service is None:
            # Load models on first use
            cls._analysis_service = PerceptionAnalysisService()
        return cls._analysis_service

    @staticmethod
    async def reconstruct(job_id: str):
        job = JobManager.get_job(job_id)
        if not job:
            return
            
        job.status = "processing"
        
        try:
            # 1. Perception/OCR/Dimensions/Scale (Member 1)
            analysis_service = ReconstructionService.get_analysis_service()
            analysis_result = analysis_service.analyze(job.file_path, job)
            
            # 2. Geometry (Member 2 Real MGR)
            job.stage = "GEOMETRY"
            from .geometry import MockGeometryService
            from app.geometry.adapter import adapt_analysis_to_mgr
            from app.geometry.pipeline import run_mgr_pipeline
            
            # Adapt Member 1 output to Member 2 inputs
            geometry_inputs = adapt_analysis_to_mgr(analysis_result)
            
            # Execute real MGR pipeline
            mgr_result = run_mgr_pipeline(**geometry_inputs)
            
            # Serialize for downstream (and metadata)
            serialized_metadata = {
                "rooms": len(mgr_result.rooms),
                "walls": len(mgr_result.walls),
                "doors": len(mgr_result.doors),
                "windows": len(mgr_result.windows),
                "scale_mm_per_px": mgr_result.scale_mm_per_px,
                "confidence": mgr_result.confidence,
                "topology_valid": mgr_result.confidence.get("topology_valid", False),
                "geometry_status": "completed",
                "scene_generation_status": "pending"
            }
            
            # Store the structured geometry result in job metadata
            analysis_result["metadata"]["geometry_status"] = "completed"
            
            geometry_result = {
                "metadata": serialized_metadata,
                "mgr_result": mgr_result  # Keep raw dataclasses for GLB generator
            }
            
            # 3. Scene Generation (Real Trimesh generation)
            job.stage = "3D_GENERATION"
            from app.reconstruction.generator import generate_scene
            import os
            
            # Setup output path
            RESULT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "results")
            os.makedirs(RESULT_DIR, exist_ok=True)
            glb_path = os.path.join(RESULT_DIR, f"{job_id}.glb")
            
            # Generate valid GLB
            gen_stats = generate_scene(mgr_result, glb_path)
            
            # Update metadata with generator stats
            serialized_metadata.update(gen_stats)
            serialized_metadata["scene_generation_status"] = "completed"
            
            # Save final structured metadata and model
            JobManager.save_result(job_id, serialized_metadata, glb_path)
            
        except Exception as e:
            job.status = "failed"
            # Propagate the stage where it failed as part of error message
            job.metadata = {
                "error": str(e),
                "failed_stage": job.stage,
                "traceback": traceback.format_exc()
            }
