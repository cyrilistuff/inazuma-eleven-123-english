<#
.SYNOPSIS
  Genera el parche xdelta a partir de la ROM original y la ROM traducida.
.DESCRIPTION
  Requiere xdelta3.exe en tools/bin/. El parche es el ÚNICO entregable que se
  distribuye (no contiene datos originales del juego).
.EXAMPLE
  ./tools/build_patch.ps1 -Original "roms\...123.3ds" -Translated "build\123_es.3ds"
#>
[CmdletBinding()]
param(
  [string]$Original   = "roms\Inazuma Eleven 1-2-3 - Endou Mamoru Densetsu.3ds",
  [Parameter(Mandatory)] [string]$Translated,
  [string]$Patch = "patch\inazuma123-es.xdelta"
)
$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$orig = Join-Path $repo $Original
$new  = Join-Path $repo $Translated
$out  = Join-Path $repo $Patch
$tool = Join-Path $repo "tools\bin\xdelta3.exe"

if (-not (Test-Path $tool)) { throw "Falta tools/bin/xdelta3.exe" }
if (-not (Test-Path $orig)) { throw "No se encuentra la ROM original: $orig" }
if (-not (Test-Path $new))  { throw "No se encuentra la ROM traducida: $new" }
New-Item -ItemType Directory -Force -Path (Split-Path $out -Parent) | Out-Null

Write-Host "==> Generando parche: $out"
& $tool -e -f -s $orig $new $out
Write-Host "OK. Parche listo (este SÍ se sube a GitHub): $out"
