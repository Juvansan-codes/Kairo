import numpy as np
from app.geometry.pipeline import run_mgr_pipeline
from app.services.analysis import PerceptionAnalysisService
from app.geometry.adapter import adapt_analysis_to_mgr
import matplotlib.pyplot as plt
import cv2

class DummyJob:
    stage = ""

# Test with real floor plan
img_path = r"d:\College Files\Kairo\evaluation\datasets\custom_real_v1\real_001.png"
perc = PerceptionAnalysisService().analyze(img_path, DummyJob())
inputs = adapt_analysis_to_mgr(perc)

print("=== ANALYSIS OUTPUT ===")
print(f"Wall mask shape: {inputs['wall_mask'].shape if inputs['wall_mask'] is not None else 'None'}")
print(f"Doors: {len(inputs['doors'])}")
print(f"Windows: {len(inputs['windows'])}")
print(f"Scale: {inputs['scale_mm_per_px']}")

# Test with DEFAULT parameters (25.0 node tolerance)
print("\n=== TEST 1: Default parameters (node_tolerance_px=25.0) ===")
res_default = run_mgr_pipeline(**inputs)
print(f"Walls: {len(res_default.walls)}, Rooms: {len(res_default.rooms)}")

# Test with CONSISTENT parameters (15.0 node tolerance)
print("\n=== TEST 2: Consistent parameters (node_tolerance_px=15.0) ===")
res_consistent = run_mgr_pipeline(**inputs, node_tolerance_px=15.0)
print(f"Walls: {len(res_consistent.walls)}, Rooms: {len(res_consistent.rooms)}")

# Test with TIGHT parameters (3.0 node tolerance)
print("\n=== TEST 3: Tight parameters (node_tolerance_px=3.0) ===")
res_tight = run_mgr_pipeline(**inputs, node_tolerance_px=3.0)
print(f"Walls: {len(res_tight.walls)}, Rooms: {len(res_tight.rooms)}")

# Visualize the wall mask
if inputs['wall_mask'] is not None:
    plt.figure(figsize=(12, 4))
    
    plt.subplot(131)
    plt.imshow(inputs['wall_mask'], cmap='gray')
    plt.title('Wall Mask')
    plt.axis('off')
    
    # Read original image
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.subplot(132)
    plt.imshow(img)
    plt.title('Original')
    plt.axis('off')
    
    # Overlay walls
    plt.subplot(133)
    plt.imshow(img)
    for wall in res_consistent.walls:
        plt.plot([wall.start[0], wall.end[0]], [wall.start[1], wall.end[1]], 'r-', linewidth=2)
    plt.title(f'Walls (n={len(res_consistent.walls)})')
    plt.axis('off')
    
    plt.tight_layout()
    plt.savefig('debug_real_floor_plan.png', dpi=150, bbox_inches='tight')
    print("\nSaved visualization to debug_real_floor_plan.png")
