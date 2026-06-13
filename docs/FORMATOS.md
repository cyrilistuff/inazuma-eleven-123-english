# Notas técnicas sobre formatos

## ROM 3DS — Inazuma Eleven 1·2·3 (objetivo)

- Contenedor: **NCSD** (`.3ds`, volcado de cartucho), **descifrado**
  (flag NoCrypto activo en la NCCH → no hacen falta claves de consola).
- Partición 0 (CXI/NCCH): offset `0x4000`, ~1825 MB. Producto `CTR-P-AETJ`.
- Dentro de la NCCH:
  - **ExeFS**: código y banner.
  - **RomFS**: árbol de archivos del juego → **aquí está casi todo el texto y los assets**.
- Formatos internos de Level-5 esperados (a confirmar al extraer):
  - `.cfg.bin` — binarios de configuración/datos (incluyen cadenas). Editor: **CfgBinEditor** / **Nyanko**.
  - Archivos de texto/script propios, fuentes y gráficos empaquetados.

## ROMs NDS de referencia (oficiales en ES)

- Inazuma Eleven 1 (`YEES`) y 2 (`BEES`): formato **NDS** clásico.
- Sistema de archivos extraíble con **ndstool** / Tinke / similar.
- Sirven como **fuente de terminología oficial** (no como texto trasplantable
  directo: el motor y la codificación del 3DS son distintos).

## Estrategia de emparejado (matching) — juego 1

El primer juego del collection 3DS es el remaster del Inazuma Eleven 1 de DS.
Plan: generar un **mapa de cadenas** de ambos (NDS ES y 3DS JP), alinear por
orden/escena/ID y producir una tabla `id_3ds ↔ texto_es` para volcar la
traducción oficial con mínimos retoques.

> Si se consigue la versión **3DS PAL (ES)** del juego 1 (mismo motor que el
> collection), el emparejado pasa a ser casi 1:1 a nivel de archivo.

## Formato del contenedor `archive.fa` (magic `B123`) — DECODIFICADO

Es una **variante del formato ARC0/XFSA de Level-5**, pero con las **tablas SIN
comprimir** y entradas de directorio de **24 bytes** (ARC0 usa 20 y comprimidas).
Por eso las herramientas de la comunidad (Pingouin/StudioElevenLib) **no lo abren**:
solo aceptan los magics `ARC0/XFSA/XFSP/XPCK`. → Parser propio: `tools/fa_unpack.py`.

**Cabecera (72 bytes):**
| Offset | Tipo | Campo |
|---|---|---|
| 0x00 | char[4] | Magic = `B123` |
| 0x04 | u32 | DirectoryEntriesOffset (= 0x48) |
| 0x08 | u32 | DirectoryHashOffset |
| 0x0C | u32 | FileEntriesOffset |
| 0x10 | u32 | NameTableOffset |
| 0x14 | u32 | DataOffset |
| 0x18 | u16 | DirectoryEntriesCount |
| 0x1A | u16 | DirectoryHashCount |
| 0x1C | u32 | FileEntriesCount |

**DirectoryEntry (24 bytes):** crc32(4), fileCount(u16), subdirCount(u16),
fileNameBaseOffset(u32), firstFileIndex(u32), firstSubdirIndex(u32),
dirNameOffset(u32). **FileEntry (16 bytes):** crc32(4), nameOffset(u32, relativo a
fileNameBase), dataOffset(u32, relativo a DataOffset), size(u32).

Los archivos internos pueden estar **crudos** o con compresión Level-5
(None/LZ10/Huffman4/Huffman8/RLE/ZLib; cabecera de 4 B: 3 bits método + 29 bits
tamaño). `fa_unpack.py` detecta cuál es por magic/plausibilidad.

## Mapa de contenido (15.547 archivos) y dónde está el TEXTO

- `import/sItx*.itx` → ficheros de **parámetros** (`cImportTxt2Data`: offsets de
  fuente/ventanas), **NO** diálogo. Texto plano con macros `_PARAM_`.
- `message/jp/GameString.bin` (+`.tbl`) → **cadenas de sistema/UI en UTF-8**,
  separadas por NUL (ej.: "ニューゲーム"=Nueva partida). ✅ traducible directo.
- `inazumaN/data_iz/a_field/field_message*.arc` → **mensajes/diálogos**, dentro de
  contenedores **ARCV** (formato clásico de Level-5 de la era DS).
- Miles de `.arc` (XPCK/ARCV) con datos de menús, técnicas, jugadores, etc.

> **Encoding clave:** el 3DS usa **UTF-8** (las NDS usaban Shift-JIS). El uso de
> contenedores **ARCV** sugiere que el remaster reutiliza estructuras de los juegos
> de DS → posible emparejado favorable con el texto español oficial.
>
> **Pendiente (siguiente fase):** parsear ARCV y el formato interno de los
> message-bin para volcar los diálogos a formato editable.

## Herramientas (resumen, detalle en tools/README.md)

| Tarea | Herramienta |
|---|---|
| Extraer/reconstruir NCSD/NCCH/RomFS/ExeFS | 3dstool, ctrtool, GodMode9 |
| Editar `.cfg.bin` / texto Level-5 | CfgBinEditor, Nyanko |
| Toolbox específico de la saga | Inazuma-Eleven-Toolbox, Strikers2013-Tools |
| Extraer NDS | ndstool, Tinke |
| Parche final | xdelta3 |
| Pruebas | Lime3DS / Azahar |
