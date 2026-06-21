# Build Photo Enhancer Pro Windows executable and installer

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Installing dependencies..."
pip install -r requirements.txt -q

Write-Host "Running tests..."
pytest tests/ -q --tb=short -m "not performance"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Building executable with PyInstaller..."
pyinstaller --noconfirm PhotoEnhancerPro.spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$exePath = Join-Path $Root "dist\Photo Enhancer Pro.exe"
if (-not (Test-Path $exePath)) {
    Write-Error "Executable not found: $exePath"
}

Write-Host "Built: $exePath"

$iscc = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($iscc) {
    Write-Host "Building installer with Inno Setup..."
    & $iscc (Join-Path $Root "installer\PhotoEnhancerPro.iss")
    Write-Host "Installer: installer\output\Photo Enhancer Pro Setup.exe"
} else {
    Write-Warning "Inno Setup not found. Install from https://jrsoftware.org/isinfo.php"
    Write-Host "Executable ready at: $exePath"
}
