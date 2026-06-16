# build.ps1 — genera ticketera.exe listo para distribuir
#
# Uso (desde la raíz del repo en PowerShell):
#   .\build.ps1
#
# El ejecutable final queda en:  dist\ticketera.exe
#
# Requisitos previos:
#   - Python 3.11+ instalado y en el PATH
#   - Se crea un entorno virtual .venv automáticamente si no existe

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = $PSScriptRoot

# ── 1. Crear / activar entorno virtual ─────────────────────────────────────
$VenvDir = Join-Path $RepoRoot ".venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creando entorno virtual en $VenvDir ..." -ForegroundColor Cyan
    python -m venv $VenvDir
}

$Activate = Join-Path $VenvDir "Scripts\Activate.ps1"
& $Activate

# ── 2. Instalar dependencias de la app + PyInstaller ───────────────────────
Write-Host "Instalando dependencias ..." -ForegroundColor Cyan
pip install --quiet --upgrade pip
pip install --quiet -r (Join-Path $RepoRoot "requirements.txt")
pip install --quiet pyinstaller

# ── 3. Limpiar builds anteriores ───────────────────────────────────────────
$BuildDir = Join-Path $RepoRoot "build"
$DistDir  = Join-Path $RepoRoot "dist"
if (Test-Path $BuildDir) { Remove-Item $BuildDir -Recurse -Force }
if (Test-Path $DistDir)  { Remove-Item $DistDir  -Recurse -Force }

# ── 4. Compilar con PyInstaller ────────────────────────────────────────────
Write-Host "Compilando ticketera.exe ..." -ForegroundColor Cyan
Set-Location $RepoRoot
pyinstaller ticketera.spec

# ── 5. Resultado ───────────────────────────────────────────────────────────
$Exe = Join-Path $DistDir "ticketera.exe"
if (Test-Path $Exe) {
    $Size = [math]::Round((Get-Item $Exe).Length / 1MB, 1)
    Write-Host ""
    Write-Host "✓ Ejecutable generado: $Exe  ($Size MB)" -ForegroundColor Green
    Write-Host "  Copia ticketera.exe a cualquier carpeta y ejecuta con doble clic." -ForegroundColor Green
} else {
    Write-Host "✗ La compilación falló. Revisa los mensajes anteriores." -ForegroundColor Red
    exit 1
}
