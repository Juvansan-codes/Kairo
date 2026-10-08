import os

RESULT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "results")

class MockSceneGenerationService:
    """
    Temporary stub for Member 2's 3D Generation logic.
    """
    def generate(self, job_id: str, geometry_result: dict) -> str:
        # Generate a placeholder GLB
        model_path = os.path.join(RESULT_DIR, f"{job_id}.glb")
        with open(model_path, "w") as f:
            f.write("mock glb content (scene generation stub)")
        return model_path
