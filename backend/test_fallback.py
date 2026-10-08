import torch
import torchvision
from torchvision.models.segmentation import fcn_resnet50
from PIL import Image
import numpy as np

def test_inference():
    print(f"PyTorch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")

    print("\nInitializing Fallback Model (ResNet/FCN style)...")
    try:
        # Load a pre-trained FCN with ResNet backbone to simulate the ResNet34-U-Net fallback
        model = fcn_resnet50(pretrained=False, num_classes=5) # 5 classes as per context
        model.eval()
        print("Model initialized successfully.")

        # Create dummy input
        print("\nCreating dummy input tensor (1, 3, 512, 512)...")
        dummy_input = torch.randn(1, 3, 512, 512)

        # Run inference
        print("Running inference...")
        with torch.no_grad():
            output = model(dummy_input)['out']
        
        print(f"Inference successful! Output shape: {output.shape}")
        return True

    except Exception as e:
        print(f"Error during fallback test: {e}")
        return False

if __name__ == "__main__":
    test_inference()
