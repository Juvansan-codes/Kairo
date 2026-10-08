import numpy as np
import cv2
import matplotlib.pyplot as plt
from app.perception.adapter import ResNetUNetPerception
from pathlib import Path

# Load model
run_dir = Path(r"d:\College Files\Kairo\backend\models\floorplan-to-3d-walls-repo")
perception = ResNetUNetPerception(run_dir)

# Analyze
img_path = r"d:\College Files\Kairo\evaluation\datasets\custom_real_v1\real_001.png"
result = perception.predict(Path(img_path))

print("=== RAW PERCEPTION OUTPUT ===")
print(f"Keys: {result.keys()}")
print(f"Raw mask shape: {result['raw_mask'].shape if 'raw_mask' in result else 'N/A'}")
print(f"Raw mask dtype: {result['raw_mask'].dtype if 'raw_mask' in result else 'N/A'}")

# Check mask contents
if 'raw_mask' in result:
    mask = result['raw_mask']
    unique_values = np.unique(mask)
    print(f"Unique mask values: {unique_values}")
    
    print("\nClass distribution:")
    for val in unique_values:
        count = np.sum(mask == val)
        pct = 100 * count / mask.size
        class_name = ['background', 'wall', 'door', 'window'][int(val)] if val < 4 else f'unknown({val})'
        print(f"  Class {val} ({class_name}): {count} pixels ({pct:.2f}%)")
    
    # Visualize each class
    fig, axes = plt.subplots(1, len(unique_values) + 1, figsize=(20, 4))
    
    # Original
    img = cv2.imread(img_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    axes[0].imshow(img_rgb)
    axes[0].set_title('Original')
    axes[0].axis('off')
    
    # Each class
    for idx, val in enumerate(unique_values):
        class_mask = (mask == val).astype(np.uint8) * 255
        axes[idx + 1].imshow(class_mask, cmap='gray')
        class_name = ['Background', 'Wall', 'Door', 'Window'][int(val)] if val < 4 else f'Class {val}'
        count = np.sum(mask == val)
        axes[idx + 1].set_title(f'{class_name}\n{count} px')
        axes[idx + 1].axis('off')
    
    plt.tight_layout()
    plt.savefig('perception_raw_output.png', dpi=150, bbox_inches='tight')
    print("\nSaved perception analysis to perception_raw_output.png")
    
    # Check if wall pixels form continuous regions
    wall_mask = (mask == 1).astype(np.uint8) * 255
    from skimage import morphology, measure
    
    # Skeletonize
    skeleton = morphology.skeletonize(wall_mask > 0)
    print(f"\nWall skeleton pixels: {np.sum(skeleton)}")
    
    # Connected components
    labels = measure.label(wall_mask)
    print(f"Connected wall components: {labels.max()}")
    
    # Component sizes
    for i in range(1, min(10, labels.max() + 1)):
        size = np.sum(labels == i)
        print(f"  Component {i}: {size} pixels")
