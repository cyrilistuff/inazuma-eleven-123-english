[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$root = Join-Path $repo "work\media_tools"
$archive = Join-Path $root "vgmstream-win64.zip"
$target = Join-Path $root "vgmstream-nightly-win64"

if (Test-Path (Join-Path $target "vgmstream-cli.exe")) {
    Write-Host "vgmstream portátil ya está preparado en $target"
    exit 0
}
if (Test-Path $target) {
    throw "Existe una instalación incompleta: $target"
}

New-Item -ItemType Directory -Force -Path $root | Out-Null
try {
    gh release download nightly --repo vgmstream/vgmstream-releases `
        --pattern "vgmstream-win64.zip" --dir $root --clobber
    Expand-Archive -LiteralPath $archive -DestinationPath $target
    if (-not (Test-Path (Join-Path $target "vgmstream-cli.exe"))) {
        throw "El paquete no contiene vgmstream-cli.exe"
    }
    Write-Host "vgmstream portátil preparado en $target"
}
finally {
    Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
}
