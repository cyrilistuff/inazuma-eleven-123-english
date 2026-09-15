<#
.SYNOPSIS
  Extrae el sistema de archivos de una ROM NDS a work/<nombre>/.
.DESCRIPTION
  Requiere ndstool.exe en tools/bin/. Usalo con las ROMs de referencia ES.
.EXAMPLE
  pwsh ./tools/extract_nds.ps1 -Rom "Roms\ie1\Inazuma Eleven (2011).nds" -Name ie1\fuentes\nds_es
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string]$Rom,
  [Parameter(Mandatory)] [string]$Name
)
$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$rom  = Join-Path $repo $Rom
$tool = Join-Path $repo "tools\bin\ndstool.exe"
$out  = Join-Path $repo (Join-Path "work" $Name)

if (-not (Test-Path $tool)) { throw "Falta tools/bin/ndstool.exe - devkitPro/ndstool" }
if (-not (Test-Path $rom))  { throw "No se encuentra la ROM: $rom" }
New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host "==> Extrayendo $Rom -> $out"
& $tool -x $rom `
  -9 (Join-Path $out "arm9.bin") -7 (Join-Path $out "arm7.bin") `
  -y9 (Join-Path $out "overlay9.bin") -y7 (Join-Path $out "overlay7.bin") `
  -d (Join-Path $out "data") -y (Join-Path $out "overlay") `
  -t (Join-Path $out "banner.bin") -h (Join-Path $out "header.bin")

Write-Host "OK. Sistema de archivos en: $out\data"
