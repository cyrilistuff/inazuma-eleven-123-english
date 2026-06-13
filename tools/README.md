# Herramientas

> Los **binarios de terceros no se suben** a este repositorio (ver `.gitignore`,
> carpeta `tools/bin/`). Aquí solo viven nuestros **scripts** y este índice de
> enlaces. Descarga/compila cada herramienta desde su fuente oficial.

## Cadena 3DS (contenedor)

| Herramienta | Para qué | Fuente |
|---|---|---|
| **3dstool** | Extraer/reconstruir NCSD, NCCH, ExeFS, RomFS | https://github.com/dnasdw/3dstool |
| **ctrtool** | Inspeccionar/extraer CIA/NCCH | https://github.com/3DSGuy/Project_CTR |
| **GodMode9** | Volcar/descifrar en consola real | https://github.com/d0k3/GodMode9 |

## Formatos internos de Level-5

| Herramienta | Para qué | Fuente |
|---|---|---|
| **Pingouin** | **Abrir/extraer/reempaquetar archivos `.fa` (XFSA) de Level-5** — es la clave para `archive.fa` | https://github.com/Tiniifan/Pingouin |
| **Nyanko** | Editor de **texto** Level-5 | https://github.com/Tiniifan/Nyanko |
| **CfgBinEditor** | Editar `.cfg.bin` de Level-5 | https://github.com/Tiniifan/CfgBinEditor |
| **Level5ResourceEditor** | Editar `RES.bin` (recursos) | https://github.com/Tiniifan/Level5ResourceEditor |
| **Strikers2013-Tools** | Extraer/importar texto, gráficos, fuentes (referencia) | https://github.com/obluda3/Strikers2013-Tools |

> **Nota:** *Inazuma-Eleven-Toolbox* (SwareJonge) es un **editor de partidas/estadísticas**,
> NO sirve para extraer `.fa` ni traducir. Las herramientas de traducción son las de Tiniifan
> (Pingouin, Nyanko, CfgBinEditor), las mismas que usan las traducciones de la comunidad.
>
> Las apps de Tiniifan son GUI de .NET Framework (4.6.1+). En `tools/bin/` quedan descargadas
> (ignoradas por git): `Pingouin/`, `Nyanko/`. El `archive.fa` de este juego usa el magic
> `B123H` (variante de XFSA): comprobar que Pingouin lo abre.

## Cadena NDS (referencia ES)

| Herramienta | Para qué | Fuente |
|---|---|---|
| **ndstool** | Extraer/reconstruir sistema de archivos NDS | https://github.com/devkitPro/ndstool |
| **Tinke** | Explorar/editar assets NDS (GUI) | https://github.com/pleonex/tinke |

## Parche y pruebas

| Herramienta | Para qué | Fuente |
|---|---|---|
| **xdelta3** | Generar/aplicar el parche `.xdelta` | https://github.com/jmacd/xdelta |
| **Lime3DS / Azahar** | Emulador 3DS para pruebas | https://azahar-emu.org/ |

## Scripts de este repo

- `extract_romfs.ps1` — extrae ExeFS/RomFS de la ROM 3DS a `work/`.
- `extract_nds.ps1` — extrae el sistema de archivos de una ROM NDS a `work/`.
- `build_patch.ps1` — genera `patch/inazuma123-es.xdelta` a partir de la ROM
  original y la traducida.

> Coloca los ejecutables descargados en `tools/bin/` (ignorado por git).
