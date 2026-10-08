"""
Test script for Raster2Seq integration.

This script tests:
1. Raster2Seq model loading
2. Inference on a test floor plan
3. Comparison with ResNet34-U-Net
4. Full MGR pipeline integration
"""

import sys
from pathlib import Path
import numpy as np

def test_raster2seq_availability():
    """Test if Raster2Seq is available and can be imported."""
    print("=" * 60)
    print("TEST 1: Raster2Seq Availability")
    print("=" * 60)
    
    try:
        from app.perception.raster2seq_adapter import get_raster2seq_adapter, RASTER2SEQ_AVAILABLE
        
        if not RASTER2SEQ_AVAILABLE:
            print("✗ Raster2Seq dependencies not fully installed")
            print("  See backend/RASTER2SEQ_INTEGRATION.md for setup instructions")
            return False
        
        print("✓ Raster2Seq dependencies available")
        return True
    except ImportError as e:
        print(f"✗ Failed to import Raster2Seq adapter: {e}")
        return False


def test_model_loading():
    """Test Raster2Seq model loading."""
    print("\n" + "=" * 60)
    print("TEST 2: Model Loading")
    print("=" * 60)
    
    try:
        from app.perception.raster2seq_adapter import get_raster2seq_adapter
        
        print("Loading Raster2Seq model (cubicasa5k checkpoint)...")
        model = get_raster2seq_adapter("cubicasa5k", device="cpu")
        
        print(f"✓ Model loaded successfully")
        print(f"  Device: {model.device}")
        print(f"  Image size: {model.image_size}")
        print(f"  Checkpoint: {model.checkpoint_key}")
        
        return True, model
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_inference(model):
    """Test inference on a real floor plan."""
    print("\n" + "=" * 60)
    print("TEST 3: Raster2Seq Inference")
    print("=" * 60)
    
    # Use test floor plan
    test_image = Path("d:/College Files/Kairo/evaluation/datasets/custom_real_v1/real_001.png")
    
    if not test_image.exists():
        print(f"✗ Test image not found: {test_image}")
        return False, None
    
    try:
        print(f"Running inference on: {test_image.name}")
        result = model.predict(test_image)
        
        print("\n✓ Inference successful!")
        print(f"  Inference time: {result['inference_time']:.3f}s")
        print(f"  Rooms detected: {len(result['semantic_regions'])}")
        print(f"  Walls extracted: {len(result['walls'])}")
        print(f"  Doors detected: {len(result['doors'])}")
        print(f"  Windows detected: {len(result['windows'])}")
        
        if result['semantic_regions']:
            print(f"\n  Room details:")
            for i, room in enumerate(result['semantic_regions'][:3]):  # First 3 rooms
                print(f"    Room {i}: {len(room.get('polygon', []))} corners, "
                      f"area={room.get('area', 0):.1f}px², "
                      f"conf={room.get('confidence', 0):.2f}")
        
        return True, result
    except Exception as e:
        print(f"✗ Inference failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_comparison():
    """Compare Raster2Seq with ResNet34-U-Net."""
    print("\n" + "=" * 60)
    print("TEST 4: Model Comparison")
    print("=" * 60)
    
    test_image = Path("d:/College Files/Kairo/evaluation/datasets/custom_real_v1/real_001.png")
    
    if not test_image.exists():
        print(f"✗ Test image not found")
        return False
    
    try:
        # Test Raster2Seq
        from app.perception.raster2seq_adapter import get_raster2seq_adapter
        r2s_model = get_raster2seq_adapter("cubicasa5k", device="cpu")
        r2s_result = r2s_model.predict(test_image)
        
        # Test ResNet
        from app.perception.adapter import ResNetUNetPerception
        resnet_run_dir = Path("d:/College Files/Kairo/backend/models/floorplan-to-3d-walls-repo")
        resnet_model = ResNetUNetPerception(resnet_run_dir, improve_walls=True, device="cpu")
        resnet_result = resnet_model.predict(test_image)
        
        print("\nComparison Results:")
        print("-" * 60)
        print(f"{'Metric':<25} {'Raster2Seq':>15} {'ResNet34-U-Net':>15}")
        print("-" * 60)
        print(f"{'Inference time (s)':<25} {r2s_result['inference_time']:>15.3f} {resnet_result['inference_time']:>15.3f}")
        print(f"{'Rooms detected':<25} {len(r2s_result['semantic_regions']):>15} {0:>15}")
        print(f"{'Walls extracted':<25} {len(r2s_result['walls']):>15} {resnet_result['class_counts']['wall']:>15}")
        print(f"{'Doors detected':<25} {len(r2s_result['doors']):>15} {resnet_result['class_counts']['door']:>15}")
        print(f"{'Windows detected':<25} {len(r2s_result['windows']):>15} {resnet_result['class_counts']['window']:>15}")
        print("-" * 60)
        
        print("\n✓ Comparison complete")
        return True
        
    except Exception as e:
        print(f"✗ Comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mgr_pipeline():
    """Test full MGR pipeline with Raster2Seq."""
    print("\n" + "=" * 60)
    print("TEST 5: Full MGR Pipeline Integration")
    print("=" * 60)
    
    try:
        from app.services.analysis import PerceptionAnalysisService
        from app.geometry.adapter import adapt_analysis_to_mgr
        from app.geometry.pipeline import run_mgr_pipeline
        
        class DummyJob:
            stage = ""
        
        # Test with Raster2Seq
        print("Testing with Raster2Seq...")
        perc = PerceptionAnalysisService(use_raster2seq=True)
        
        test_image = "d:/College Files/Kairo/evaluation/datasets/custom_real_v1/real_001.png"
        result = perc.analyze(test_image, DummyJob())
        
        # Adapt to MGR format
        inputs = adapt_analysis_to_mgr(result)
        
        # Run MGR pipeline
        mgr_result = run_mgr_pipeline(**inputs)
        
        print("\n✓ Full pipeline successful!")
        print(f"  Perception model: {perc.model_name}")
        print(f"  MGR Rooms detected: {len(mgr_result.rooms)}")
        print(f"  MGR Walls: {len(mgr_result.walls)}")
        print(f"  MGR Doors: {len(mgr_result.doors)}")
        print(f"  MGR Windows: {len(mgr_result.windows)}")
        print(f"  Topology valid: {mgr_result.confidence.get('topology_valid', False)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("RASTER2SEQ INTEGRATION TEST SUITE")
    print("=" * 60)
    
    results = {
        'availability': False,
        'loading': False,
        'inference': False,
        'comparison': False,
        'pipeline': False
    }
    
    # Test 1: Availability
    results['availability'] = test_raster2seq_availability()
    
    if not results['availability']:
        print("\n" + "=" * 60)
        print("SETUP REQUIRED")
        print("=" * 60)
        print("\nRaster2Seq is not fully set up. To install:")
        print("1. cd backend/Raster2Seq")
        print("2. pip install -r requirements.txt")
        print("3. Compile native extensions (see RASTER2SEQ_INTEGRATION.md)")
        print("\nFor now, the system will use ResNet34-U-Net fallback.")
        return
    
    # Test 2: Model loading
    success, model = test_model_loading()
    results['loading'] = success
    
    if not success:
        print("\n⚠ Skipping remaining tests due to model loading failure")
        return
    
    # Test 3: Inference
    success, inference_result = test_inference(model)
    results['inference'] = success
    
    # Test 4: Comparison
    results['comparison'] = test_comparison()
    
    # Test 5: Full pipeline
    results['pipeline'] = test_mgr_pipeline()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"{test_name.title():<20} {status}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Raster2Seq is fully integrated.")
    elif passed > 0:
        print(f"\n⚠ {total - passed} test(s) failed. Check errors above.")
    else:
        print("\n✗ Integration incomplete. See RASTER2SEQ_INTEGRATION.md")


if __name__ == "__main__":
    main()
