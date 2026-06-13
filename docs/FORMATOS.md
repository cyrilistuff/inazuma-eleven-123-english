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

## Herramientas (resumen, detalle en tools/README.md)

| Tarea | Herramienta |
|---|---|
| Extraer/reconstruir NCSD/NCCH/RomFS/ExeFS | 3dstool, ctrtool, GodMode9 |
| Editar `.cfg.bin` / texto Level-5 | CfgBinEditor, Nyanko |
| Toolbox específico de la saga | Inazuma-Eleven-Toolbox, Strikers2013-Tools |
| Extraer NDS | ndstool, Tinke |
| Parche final | xdelta3 |
| Pruebas | Lime3DS / Azahar |
