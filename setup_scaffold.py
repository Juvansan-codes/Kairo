import os
from pathlib import Path

root = Path(r"d:\College Files\Kairo")

# Directories
dirs = [
    "backend/app/api",
    "backend/app/core",
    "backend/app/perception",
    "backend/app/ocr",
    "backend/app/geometry",
    "backend/app/reconstruction",
    "backend/app/services",
    "backend/app/models",
    "backend/app/utils",
    "backend/data/raw",
    "backend/data/processed",
    "backend/data/evaluation",
    "backend/tests",
    "models",
    "outputs",
    "evaluation/metrics",
    "evaluation/ground_truth",
    "evaluation/results",
    "docs",
]

for d in dirs:
    (root / d).mkdir(parents=True, exist_ok=True)
    if "data" in d or "outputs" in d or "models" in d or "evaluation" in d:
        (root / d / ".gitkeep").write_text("")

# Init files for python packages
init_dirs = [
    "backend/app",
    "backend/app/api",
    "backend/app/core",
    "backend/app/perception",
    "backend/app/ocr",
    "backend/app/geometry",
    "backend/app/reconstruction",
    "backend/app/services",
    "backend/app/models",
    "backend/app/utils",
]

for d in init_dirs:
    (root / d / "__init__.py").write_text("")

# Module placeholders
(root / "backend/app/perception/adapter.py").write_text('''\
class PerceptionModel:
    def predict(self, image_path: str):
        """Mock prediction for floorplan segmentation/vectorization."""
        pass
''')

(root / "backend/app/ocr/engine.py").write_text('''\
def extract_text(image_path: str):
    pass

def extract_dimensions(image_path: str):
    pass
''')

(root / "backend/app/geometry/solver.py").write_text('''\
def skeletonization(mask):
    pass

def generate_wall_graph(skeleton):
    pass

def polygonize_rooms(wall_graph):
    pass
''')

(root / "backend/app/reconstruction/generator.py").write_text('''\
def generate_scene(room_graph):
    pass

def export_glb(scene, output_path: str):
    pass
''')

(root / "backend/reconstruct.py").write_text('''\
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input floorplan image")
    parser.add_argument("--output", required=True, help="Output scene GLB")
    args = parser.parse_args()
    print(f"Mock CLI reconstruction: {args.input} -> {args.output}")

if __name__ == "__main__":
    main()
''')

(root / "backend/.env.example").write_text('''\
API_HOST=0.0.0.0
API_PORT=8000
# MODEL_CHECKPOINT_PATH=
''')

(root / "evaluation/README.md").write_text('''\
# Evaluation

This directory contains evaluation datasets, metrics, and results.
- `CubiCasa5K` evaluation
- Custom 10-15 plan evaluation
- Wall IoU
- Room IoU
- Dimension Error
- Opening Completeness
- Chamfer distance
- Ablation results
''')

print("Directories and backend placeholders created.")
