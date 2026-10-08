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
            
            # 2. Geometry (Member 2 stub)
            job.stage = "GEOMETRY"
            geometry_result = ReconstructionService._geometry_service.reconstruct(analysis_result)
            
            # 3. Scene Generation (Member 2/4 stub)
            job.stage = "3D_GENERATION"
            glb_path = ReconstructionService._scene_service.generate(job_id, geometry_result)
            
            # Save final structured metadata and model
            JobManager.save_result(job_id, geometry_result.get("metadata", {}), glb_path)
            
        except Exception as e:
            job.status = "failed"
            # Propagate the stage where it failed as part of error message
            job.metadata = {
                "error": str(e),
                "failed_stage": job.stage,
                "traceback": traceback.format_exc()
            }
