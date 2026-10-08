# Raster2Seq Quick Start Guide

## TL;DR - Automated Setup (Windows)

```powershell
cd backend
.\setup_raster2seq.ps1
```

This script will:
1. Install Python dependencies
2. Compile native extensions
3. Run integration tests

## Manual Setup (3 Steps)

### Step 1: Install Dependencies (5 mins)

```bash
cd backend/Raster2Seq
pip install -r requirements.txt
```

### Step 2: Compile Extensions (10 mins)

**Option A - Windows:**
```powershell
# Deformable attention
cd models/ops
python setup.py build install
cd ../..

# Differentiable rasterization
cd diff_ras
python setup.py build develop
cd ../..
```

**Option B - Linux/Mac:**
```bash
cd models/ops
sh make.sh
cd ../../diff_ras
python setup.py build develop
cd ..
```

### Step 3: Test Integration (1 min)

```bash
cd backend
python test_raster2seq_integration.py
```

## Usage in Code

### Option 1: Automatic Fallback (Recommended)

```python
from app.services.analysis import PerceptionAnalysisService

# Try Raster2Seq first, fall back to ResNet if unavailable
service = PerceptionAnalysisService(use_raster2seq=True)

# Use normally
result = service.analyze(image_path, job)
```

### Option 2: Explicit Model Selection

```python
from app.perception.raster2seq_adapter import get_raster2seq_adapter

# Use Raster2Seq directly
model = get_raster2seq_adapter("cubicasa5k")  # or "s3d-bw", "raster2graph"
result = model.predict(image_path)
```

### Option 3: Compare Both Models

```python
# Test both models
from app.services.analysis import PerceptionAnalysisService

# Raster2Seq
r2s_service = PerceptionAnalysisService(use_raster2seq=True)
r2s_result = r2s_service.analyze(image_path, job)

# ResNet
resnet_service = PerceptionAnalysisService(use_raster2seq=False)
resnet_result = resnet_service.analyze(image_path, job)

print(f"Raster2Seq: {r2s_service.model_name}")
print(f"ResNet: {resnet_service.model_name}")
```

## Available Checkpoints

| Checkpoint | Dataset | RoomF1 | Best For |
|------------|---------|--------|----------|
| `cubicasa5k` | CubiCasa5K | 88.7% | Residential plans |
| `s3d-bw` | Structured3D | 99.6% | Best accuracy |
| `raster2graph` | Raster2Graph | 97.0% | Technical drawings |

## Troubleshooting

### Issue: Import Error

**Error**: `ModuleNotFoundError: No module named 'models'`

**Fix**:
```python
# The adapter automatically adds Raster2Seq to path
# If this fails, manually add:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "Raster2Seq"))
```

### Issue: Compilation Fails

**Error**: Build errors during `setup.py build`

**Fix**:
- **Windows**: Install Visual Studio Build Tools
- **CUDA**: Ensure CUDA version matches PyTorch (11.8 recommended)
- **CPU-only**: Compilation may fail but inference will still work

### Issue: Checkpoint Download Fails

**Error**: HuggingFace download timeout

**Fix**:
```python
# Download manually
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="haopt/Raster2Seq",
    allow_patterns="cubicasa5k/*",
    local_dir="./checkpoints"
)
```

### Issue: Out of Memory

**Error**: CUDA OOM during inference

**Fix**:
```python
# Use CPU
model = get_raster2seq_adapter("cubicasa5k", device="cpu")

# Or use smaller image size
model = get_raster2seq_adapter("cubicasa5k", image_size=256)  # instead of 512
```

## Performance

### ResNet34-U-Net (Current)
- ⚡ Inference: ~0.5s (GPU) / ~2s (CPU)
- 📊 Accuracy: Good for simple-moderate plans
- 💾 Memory: ~2GB GPU / ~500MB CPU
- ⚠️ Issues: Fragmentation on complex plans

### Raster2Seq (New)
- ⚡ Inference: ~2-3s (GPU) / ~8-10s (CPU)
- 📊 Accuracy: State-of-the-art (88-99%)
- 💾 Memory: ~4GB GPU / ~1.5GB CPU
- ✅ Benefits: No fragmentation, semantic labels

## Integration Status

✅ **Implemented**:
- Complete Raster2Seq adapter
- Automatic fallback to ResNet
- Model selection in AnalysisService
- Conversion to KAIRO format
- Full test suite

🚧 **Optional Future Work**:
- API endpoint for model selection
- UI toggle for fast/accurate mode
- Benchmark comparison
- Door/window detection refinement

## Quick Test

```bash
# Test if Raster2Seq works
cd backend
python -c "
from app.perception.raster2seq_adapter import get_raster2seq_adapter
model = get_raster2seq_adapter('cubicasa5k', device='cpu')
print('✓ Raster2Seq loaded successfully!')
"
```

## For Hackathon Demo

**Current Setup** (Works Now):
```python
# Use fast ResNet model
service = PerceptionAnalysisService(use_raster2seq=False)
```

**After Integration** (Better Accuracy):
```python
# Use Raster2Seq for better results
service = PerceptionAnalysisService(use_raster2seq=True)
```

Both work! Choose based on your needs:
- **Speed** → ResNet (already working)
- **Accuracy** → Raster2Seq (needs setup)

## Support

- Full guide: `RASTER2SEQ_INTEGRATION.md`
- Test suite: `test_raster2seq_integration.py`
- Setup script: `setup_raster2seq.ps1`
- Raster2Seq repo: https://github.com/Cornell-VAILab/Raster2Seq
