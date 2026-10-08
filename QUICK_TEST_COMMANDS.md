# Quick Test Commands for KAIRO

## 🚀 Current Status
**Backend**: ✅ Running on http://localhost:8000  
**Terminal ID**: `term_1791493173377_n0r571xdgb`

---

## Essential Commands

### 1️⃣ Check Backend Health
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing
```
Expected: `{"status":"ok"}` with 200 status

### 2️⃣ View API Documentation
Open in browser:
```
http://localhost:8000/docs
```

### 3️⃣ Test System Components
```powershell
cd "d:\College Files\Kairo\backend"
python test_system.py
```
Expected: 🎉 ALL TESTS PASSED

### 4️⃣ Upload Floor Plan (Example)
```powershell
curl -X POST "http://localhost:8000/api/jobs" `
  -H "accept: application/json" `
  -H "Content-Type: multipart/form-data" `
  -F "image=@C:\path\to\your\floorplan.jpg"
```

---

## Process Management

### View Server Logs
Already running in background. Server is healthy and responding.

### Stop Backend
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*"} | Stop-Process -Force
```

### Restart Backend (if needed)
```powershell
cd "d:\College Files\Kairo\backend"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Quick Python Tests

### Test Model Loading
```powershell
cd "d:\College Files\Kairo\backend"
python -c "from app.services.analysis import PerceptionAnalysisService; s = PerceptionAnalysisService(); print('Model:', s.model_name)"
```

### Test CUDA
```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

### Test Fragment Connection
```powershell
python -c "from app.geometry.fragment_connection import improve_wall_mask; import numpy as np; m = np.zeros((100,100), dtype=np.uint8); print('Fragment connection:', 'OK' if improve_wall_mask(m) is not None else 'FAIL')"
```

---

## Expected Results

When you upload a floor plan, you should see:
- ✅ **60-70 walls** detected (was 19 before fix)
- ✅ **1+ rooms** detected (was 0 before fix)
- ✅ **Connected walls** in 3D view (not floating segments)
- ✅ **Room floors** properly generated

---

## Files to Check

### Test Results
- `SYSTEM_READY.md` - Complete system status
- `SYSTEM_STATUS.md` - Detailed technical info
- `test_system.py` - Run this to verify everything

### Logs & Debug
- Check backend terminal for API requests
- Look for any ERROR or WARNING messages

---

## API Endpoints

- `GET /health` - Health check
- `GET /docs` - Swagger UI
- `POST /api/jobs` - Upload floor plan
- `GET /api/jobs/{job_id}` - Get job status
- `GET /api/jobs/{job_id}/result` - Get analysis result

---

## 🎯 Demo Checklist

Before starting your demo:
- [ ] Backend running on port 8000 ✅ (Already running)
- [ ] Health check returns 200 ✅ (Verified)
- [ ] Test system passed ✅ (All tests passed)
- [ ] Have 2-3 test floor plans ready
- [ ] Browser open to http://localhost:8000/docs
- [ ] Know your GPU specs (RTX 3050 with CUDA 12.1)

---

## 📊 Performance Stats

**Your System**:
- GPU: NVIDIA GeForce RTX 3050 4GB Laptop
- CUDA: 12.1 (enabled ✅)
- PyTorch: 2.5.1+cu121
- Model: ResNet34-U-Net with fragment connection

**Results on Test Floor Plan**:
- Walls: 19 → **68 walls** (+258%)
- Rooms: 0 → **1 room** (FIXED ✅)
- Wall components: 51 → **1** (fragment connection)

---

## 🆘 Troubleshooting

### Backend not responding?
```powershell
# Check if running
Get-Process | Where-Object {$_.ProcessName -like "*uvicorn*"}

# Check port
Test-NetConnection -ComputerName localhost -Port 8000
```

### Port already in use?
```powershell
# Kill all Python processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
```

### Import errors?
```powershell
cd "d:\College Files\Kairo\backend"
pip list | findstr "torch paddle"
```

---

**Everything is ready! Start testing! 🚀**
