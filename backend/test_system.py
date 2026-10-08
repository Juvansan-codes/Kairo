"""
Quick system test to verify all components are working
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from app.services.analysis import PerceptionAnalysisService
        print("✅ PerceptionAnalysisService imported")
        
        from app.perception.adapter import ResNetUNetPerception
        print("✅ ResNetUNetPerception imported")
        
        from app.geometry.fragment_connection import improve_wall_mask
        print("✅ Wall fragment connection imported")
        
        from app.ocr.engine import PaddleOCREngine
        print("✅ PaddleOCR imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_perception_service():
    """Test perception service initialization"""
    print("\nTesting perception service...")
    try:
        from app.services.analysis import PerceptionAnalysisService
        
        # Test with ResNet (current working model)
        service = PerceptionAnalysisService(use_raster2seq=False)
        print(f"✅ Service initialized with model: {service.model_name}")
        
        # Test with Raster2Seq (should fallback to ResNet)
        service_r2s = PerceptionAnalysisService(use_raster2seq=True)
        print(f"✅ Service with Raster2Seq flag initialized (model: {service_r2s.model_name})")
        
        return True
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cuda():
    """Test CUDA availability"""
    print("\nTesting CUDA...")
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"✅ CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✅ CUDA version: {torch.version.cuda}")
            print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        return True
    except Exception as e:
        print(f"❌ CUDA test failed: {e}")
        return False

def test_fragment_connection():
    """Test wall fragment connection module"""
    print("\nTesting wall fragment connection...")
    try:
        import numpy as np
        from app.geometry.fragment_connection import improve_wall_mask
        
        # Create a simple fragmented mask
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[10:15, 10:90] = 255  # Horizontal line
        mask[20:25, 10:15] = 255  # Small fragment (should be removed)
        
        improved = improve_wall_mask(mask)
        print(f"✅ Fragment connection working (input shape: {mask.shape}, output shape: {improved.shape})")
        
        return True
    except Exception as e:
        print(f"❌ Fragment connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("KAIRO System Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("CUDA", test_cuda()))
    results.append(("Fragment Connection", test_fragment_connection()))
    results.append(("Perception Service", test_perception_service()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - System is ready for demo!")
    else:
        print("⚠️  Some tests failed - check errors above")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
