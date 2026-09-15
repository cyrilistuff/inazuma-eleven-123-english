[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$root = Join-Path $repo "work\shared\herramientas\media_tools"
$archive = Join-Path $root "mobipeg-windows-x86.zip"
$target = Join-Path $root "mobipeg-v2.1-x86"
$expected = "0558027C103C64366C3AE84CAAE3D21D5220778AAC119C58FB02A9CADED2D770"

if (Test-Path (Join-Path $target "ffmpeg.exe")) {
    Write-Host "mobipeg v2.1 x86 ya está preparado en $target"
    exit 0
}
if (Test-Path $target) {
    throw "Existe una instalación incompleta: $target"
}

New-Item -ItemType Directory -Force -Path $root | Out-Null
try {
    gh release download v2.1 --repo quatric/mobipeg `
        --pattern "mobipeg-windows-x86.zip" --dir $root --clobber
    $actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash
    if ($actual -ne $expected) {
        throw "Hash inesperado para mobipeg: $actual"
    }
    Expand-Archive -LiteralPath $archive -DestinationPath $target
    if (-not (Test-Path (Join-Path $target "ffmpeg.exe")) -or
        -not (Test-Path (Join-Path $target "ffprobe.exe"))) {
        throw "El paquete no contiene ffmpeg.exe y ffprobe.exe"
    }
    Write-Host "mobipeg v2.1 x86 preparado en $target"
}
finally {
    Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
}
