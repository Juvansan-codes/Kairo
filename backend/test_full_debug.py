import numpy as np
import cv2
import matplotlib.pyplot as plt
from app.services.analysis import PerceptionAnalysisService
from app.geometry.adapter import adapt_analysis_to_mgr
from app.geometry.pipeline import run_mgr_pipeline

class DummyJob:
    stage = ""

# Load and analyze
img_path = r"d:\College Files\Kairo\evaluation\datasets\custom_real_v1\real_001.png"
img = cv2.imread(img_path)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

perc = PerceptionAnalysisService().analyze(img_path, DummyJob())
inputs = adapt_analysis_to_mgr(perc)
res = run_mgr_pipeline(**inputs, node_tolerance_px=15.0)

# Create comprehensive visualization
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Original image
axes[0, 0].imshow(img_rgb)
axes[0, 0].set_title('Original Floor Plan', fontsize=14, fontweight='bold')
axes[0, 0].axis('off')

# Wall mask
if inputs['wall_mask'] is not None:
    axes[0, 1].imshow(inputs['wall_mask'], cmap='gray')
    axes[0, 1].set_title(f'Wall Mask from Perception', fontsize=14, fontweight='bold')
    axes[0, 1].axis('off')

# Extracted walls overlay
axes[0, 2].imshow(img_rgb, alpha=0.3)
for i, wall in enumerate(res.walls):
    axes[0, 2].plot([wall.start[0], wall.end[0]], 
                    [wall.start[1], wall.end[1]], 
                    'r-', linewidth=3, alpha=0.8)
    # Mark endpoints
    axes[0, 2].plot(wall.start[0], wall.start[1], 'go', markersize=6)
    axes[0, 2].plot(wall.end[0], wall.end[1], 'bo', markersize=6)
axes[0, 2].set_title(f'Extracted Walls (n={len(res.walls)})', fontsize=14, fontweight='bold')
axes[0, 2].axis('off')

# Just walls (no background)
axes[1, 0].set_xlim(0, img_rgb.shape[1])
axes[1, 0].set_ylim(img_rgb.shape[0], 0)
axes[1, 0].set_aspect('equal')
for wall in res.walls:
    axes[1, 0].plot([wall.start[0], wall.end[0]], 
                    [wall.start[1], wall.end[1]], 
                    'r-', linewidth=2)
axes[1, 0].set_title('Wall Graph (isolated)', fontsize=14, fontweight='bold')
axes[1, 0].grid(True, alpha=0.3)

# Doors and windows
axes[1, 1].imshow(img_rgb, alpha=0.3)
for door in inputs['doors']:
    axes[1, 1].plot([door.start[0], door.end[0]], 
                    [door.start[1], door.end[1]], 
                    'orange', linewidth=4, label='Door')
for window in inputs['windows']:
    axes[1, 1].plot([window.start[0], window.end[0]], 
                    [window.start[1], window.end[1]], 
                    'cyan', linewidth=4, label='Window')
axes[1, 1].set_title(f'Openings: {len(inputs["doors"])} doors, {len(inputs["windows"])} windows', 
                     fontsize=14, fontweight='bold')
axes[1, 1].axis('off')

# Summary stats
axes[1, 2].axis('off')
summary_text = f"""
DETECTION SUMMARY
{'='*40}

Perception Output:
  • Walls detected: {len(res.walls)}
  • Doors detected: {len(inputs['doors'])}
  • Windows detected: {len(inputs['windows'])}
  • Scale: {inputs['scale_mm_per_px'] or 'None'}

Geometric Reconciliation (MGR):
  • Final walls: {len(res.walls)}
  • Rooms detected: {len(res.rooms)} ⚠️
  • Doors reconciled: {len(res.doors)}
  • Windows reconciled: {len(res.windows)}

{'='*40}
⚠️ PROBLEM IDENTIFIED ⚠️
{'='*40}

Rooms detected: {len(res.rooms)}

The walls do NOT form closed regions!

Possible causes:
• Perception model is incomplete
• Walls are fragmented
• Missing wall segments
• Walls don't connect properly

The tolerance mismatch hypothesis
was INCORRECT - changing tolerance
from 25.0 to 15.0 to 3.0 made no
difference.

The real issue: Incomplete wall
detection from the perception stage.
"""
axes[1, 2].text(0.05, 0.95, summary_text, transform=axes[1, 2].transAxes,
                fontsize=11, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('full_debug_analysis.png', dpi=150, bbox_inches='tight')
print("Saved comprehensive visualization to full_debug_analysis.png")
print(f"\n⚠️ ROOT CAUSE: Perception model only detecting {len(res.walls)} walls that don't form closed regions")
print(f"   Rooms detected: {len(res.rooms)}")
print(f"   The walls are incomplete or fragmented!")
