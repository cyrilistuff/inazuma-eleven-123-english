# tools/jugar.ps1 — lanza la build en Azahar y, al cerrar el emulador, COSECHA
# automaticamente los errores de la sesion en nuestro registro persistente
# (logs/runtime_errors.json) + informe. Asi cada partida queda auto-analizada sin
# mirar el log en vivo. (Peticion: registro automatico en CADA arranque, mas
# eficiente que escuchar en directo.)
#
# Uso:  pwsh -File tools\jugar.ps1 [ruta\build.3ds]
#       Sin argumento usa la build mas reciente (work\build o roms\*ES*).
param(
    [string]$Build,
    [string]$Azahar = (Join-Path $env:ProgramFiles "Azahar\azahar.exe")
)

$ErrorActionPreference = "Stop"
$REPO   = Split-Path -Parent $PSScriptRoot
$LOG    = Join-Path $env:APPDATA "Azahar\log\azahar_log.txt"

if (-not (Test-Path $AZAHAR)) { Write-Error "No encuentro azahar.exe en $AZAHAR"; exit 1 }

# 1) elegir build (la mas reciente si no se pasa)
if (-not $Build) {
    $Build = Get-ChildItem "$REPO\work\build\*.3ds", "$REPO\roms\*ES*.3ds", "$REPO\roms\JUGAR*.3ds" `
                 -ErrorAction SilentlyContinue |
             Sort-Object LastWriteTime -Descending |
             Select-Object -First 1 -ExpandProperty FullName
}
if (-not $Build -or -not (Test-Path $Build)) {
    Write-Error "No hay build. Pasa la ruta: tools\jugar.ps1 <build.3ds>"; exit 1
}
Write-Host "[jugar] Build: $Build" -ForegroundColor Cyan

# 2) conservar el registro anterior. Azahar rota el log al iniciar otra sesion.
if (Get-Process azahar -ErrorAction SilentlyContinue) {
    throw "Azahar ya esta abierto. Cierra la sesion anterior antes de iniciar otra."
}
if (Test-Path $LOG) {
    $history = Join-Path $REPO "logs\sessions"
    New-Item -ItemType Directory -Force -Path $history | Out-Null
    Copy-Item -LiteralPath $LOG -Destination (Join-Path $history ("before-" + (Get-Date -Format "yyyyMMdd-HHmmss-fff") + ".log"))
}

# 3) lanzar y ESPERAR a que se cierre Azahar
Write-Host "[jugar] Lanzando Azahar... (cierra el emulador al terminar de jugar)" -ForegroundColor Cyan
Start-Process -FilePath $AZAHAR -ArgumentList "`"$Build`"" -Wait
while (Get-Process azahar -ErrorAction SilentlyContinue) { Start-Sleep -Seconds 1 }

# 4) cosechar la sesion en el registro
Write-Host "[jugar] Cosechando errores de la sesion..." -ForegroundColor Cyan
$name = [IO.Path]::GetFileNameWithoutExtension($Build)
& python "$REPO\tools\harvest_log.py" --session $name
