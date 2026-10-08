# Raster2Seq Setup Script for Windows (PowerShell)
# This script automates the Raster2Seq installation process

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Raster2Seq Installation Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$RASTER2SEQ_DIR = "Raster2Seq"

# Check if Raster2Seq directory exists
if (-not (Test-Path $RASTER2SEQ_DIR)) {
    Write-Host "Error: Raster2Seq directory not found!" -ForegroundColor Red
    Write-Host "Please run: git clone https://github.com/Cornell-VAILab/Raster2Seq.git" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/4] Installing Python dependencies..." -ForegroundColor Green
Set-Location $RASTER2SEQ_DIR

# Install requirements
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install requirements" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/4] Compiling deformable attention modules..." -ForegroundColor Green
Set-Location "models\ops"

# Check if Visual Studio Build Tools are available
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vswhere) {
    Write-Host "  Visual Studio Build Tools found" -ForegroundColor Gray
} else {
    Write-Host "  Warning: Visual Studio Build Tools not found" -ForegroundColor Yellow
    Write-Host "  You may need to install them for compilation" -ForegroundColor Yellow
}

# Compile
python setup.py build install
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Warning: Deformable attention compilation had issues" -ForegroundColor Yellow
    Write-Host "  This may be okay if CUDA is not available" -ForegroundColor Yellow
}

# Return to Raster2Seq root
Set-Location ".."
Set-Location ".."

Write-Host ""
Write-Host "[3/4] Compiling differentiable rasterization..." -ForegroundColor Green
Set-Location "diff_ras"

python setup.py build develop
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Warning: Diff rasterization compilation had issues" -ForegroundColor Yellow
}

# Return to backend directory
Set-Location ".."
Set-Location ".."

Write-Host ""
Write-Host "[4/4] Testing installation..." -ForegroundColor Green
python test_raster2seq_integration.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run 'python test_raster2seq_integration.py' to verify" -ForegroundColor White
Write-Host "  2. Update your analysis service to use Raster2Seq" -ForegroundColor White
Write-Host "     Example: PerceptionAnalysisService(use_raster2seq=True)" -ForegroundColor White
Write-Host ""
