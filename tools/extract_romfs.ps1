<#
.SYNOPSIS
  Extrae ExeFS y RomFS de la ROM 3DS (descifrada) a la carpeta work/.
.DESCRIPTION
  Requiere 3dstool.exe en tools/bin/. La ROM debe estar descifrada (NoCrypto).
  Salida (ignorada por git): work/shared/base_3ds/exefs, work/shared/base_3ds/romfs.
.EXAMPLE
  pwsh ./tools/extract_romfs.ps1
#>
[CmdletBinding()]
param(
  [string]$Rom = "roms\shared\Inazuma Eleven 1-2-3 - Endou Mamoru Densetsu.3ds",
  [string]$Out = "work\shared\base_3ds"
)
$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$rom  = Join-Path $repo $Rom
$out  = Join-Path $repo $Out
$tool = Join-Path $repo "tools\bin\3dstool.exe"

if (-not (Test-Path $tool)) { throw "Falta tools/bin/3dstool.exe - ver https://github.com/dnasdw/3dstool" }
if (-not (Test-Path $rom))  { throw "No se encuentra la ROM: $rom" }
New-Item -ItemType Directory -Force -Path $out | Out-Null

$cxi    = Join-Path $out "partition0.cxi"
$romfs  = Join-Path $out "romfs.bin"
$exefs  = Join-Path $out "exefs.bin"

Write-Host "==> 1/3 Extrayendo particion 0 (CXI/NCCH) del NCSD..."
& $tool -xtf 3ds $rom --header (Join-Path $out "ncsd_header.bin") -0 $cxi
if ($LASTEXITCODE -ne 0) { throw "3dstool fallo extrayendo la particion 0" }

Write-Host "==> 2/3 Extrayendo ExeFS y RomFS de la NCCH..."
& $tool -xtf cxi $cxi --header (Join-Path $out "ncch_header.bin") --exefs $exefs --romfs $romfs
if ($LASTEXITCODE -ne 0) { throw "3dstool fallo extrayendo exefs/romfs" }

Write-Host "==> 3/3 Desempaquetando RomFS y ExeFS a carpetas..."
& $tool -xtf romfs $romfs --romfs-dir (Join-Path $out "romfs")
if ($LASTEXITCODE -ne 0) { throw "3dstool fallo desempaquetando romfs" }
& $tool -xtf exefs $exefs --exefs-dir (Join-Path $out "exefs")

Write-Host "OK. Archivos en: $out\romfs  y  $out\exefs"
