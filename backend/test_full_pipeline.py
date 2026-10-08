from pathlib import Path
from app.services.analysis import PerceptionAnalysisService
from app.geometry.adapter import adapt_analysis_to_mgr
from app.geometry.pipeline import run_mgr_pipeline
from app.reconstruction.generator import generate_scene

class DummyJob:
    stage = ""

# Analyze
img_path = r"d:\College Files\Kairo\evaluation\datasets\custom_real_v1\real_001.png"
perc = PerceptionAnalysisService().analyze(img_path, DummyJob())
inputs = adapt_analysis_to_mgr(perc)

# Run MGR
mgr_result = run_mgr_pipeline(**inputs)

print("=== MGR RESULT ===")
print(f"Rooms: {len(mgr_result.rooms)}")
print(f"Walls: {len(mgr_result.walls)}")
print(f"Doors: {len(mgr_result.doors)}")
print(f"Windows: {len(mgr_result.windows)}")

# Generate 3D
output_path = "test_output.glb"
stats = generate_scene(mgr_result, output_path)

print(f"\n=== 3D GENERATION STATS ===")
for key, value in stats.items():
    print(f"{key}: {value}")

print(f"\n✓ 3D model saved to: {output_path}")
