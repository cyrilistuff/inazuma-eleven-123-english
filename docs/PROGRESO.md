# Progreso del proyecto

Leyenda: ⬜ pendiente · 🟡 en curso · ✅ hecho

## Fase 0 — Infraestructura
- ✅ Diagnóstico de las ROMs (formato, cifrado, regiones)
- ✅ Estructura del repositorio + git init
- ✅ `.gitignore`, `README.md`, `LEGAL.md`
- 🟡 Conseguir/compilar herramientas (3dstool, ndstool, CfgBinEditor, Nyanko, xdelta3)

## Fase 1 — Extracción y mapeo
- ✅ Extraer RomFS/ExeFS de la ROM 3DS (1·2·3) → `work/romfs`, `work/exefs`
- ✅ Mapa de primer nivel del RomFS 3DS
- ✅ **`archive.fa` decodificado** (magic `B123` = variante ARC0/XFSA) y
  **extractor propio** `tools/fa_unpack.py` (15.547 archivos, rutas correctas)
- ✅ Verificado que las herramientas de la comunidad NO soportan `B123` (plan B)
- ✅ Localizado el texto: `message/jp/GameString.bin` (UTF-8), `import/*.itx`
  (parámetros), `field_message*.arc` (diálogos, en contenedores ARCV)
- ✅ Primer vistazo a texto real del juego 1 (cadenas de sistema en UTF-8)
- 🟡 Parsear **ARCV / message-bin** para volcar diálogos a formato editable
- ⬜ Extraer sistema de archivos completo del IE1 / IE2 (NDS, ES) con `nds_unpack.py`
- ⬜ **Mapa de textos** del juego 1 (NDS ES) y del 3DS, y **emparejado (match)**

### Hallazgos de la extracción 3DS (RomFS)
- Estructura por juego: `inazuma1/`, `inazuma2/`, `inazuma3/`, `inazuma3_ogre/`
  → contienen sobre todo **sonido/voces** (`.SAD/.SWD/.SED/.SMD`).
- `sound/` → audio global.
- **`archive.fa` (1,2 GB, magic `B123H`)** → contenedor Level-5 con TOC propia.
  Aquí viven texto, scripts, tablas y gráficos de los 3 juegos. **Es el objetivo
  principal a desempaquetar.**
- `cro/`, `.crr` → módulos de código 3DS (CRO). `icon/`, `import/` auxiliares.
- Herramienta candidata para `.fa`: **Inazuma-Eleven-Toolbox v0.6.1**
  (SwareJonge) — tiene binario en releases.

## Fase 2 — Glosario y terminología
- ⬜ Volcar terminología oficial ES de las NDS (personajes, técnicas, equipos)
- ⬜ Construir glosario maestro en `translation/glossary/`

## Fase 3 — Traducción
- ⬜ Juego 1
- ⬜ Juego 2
- ⬜ Juego 3
- ⬜ Interfaz / menús / sistema

## Fase 4 — Fuente y gráficos
- ⬜ Ampliar fuente (ñ, ¿ ¡, tildes) y tabla de anchos
- ⬜ Gráficos con texto incrustado

## Fase 5 — Build y release
- ⬜ Reinsertar y reconstruir la ROM
- ⬜ Pruebas en emulador (Lime3DS / Azahar)
- ⬜ Generar parche `.xdelta`
- ⬜ Primera release pública

## Notas de las ROMs (referencia)
| ROM | Plataforma | Región | Código | Tamaño |
|---|---|---|---|---|
| Inazuma Eleven 1·2·3 | 3DS (NCSD, descifrado) | JP | CTR-P-AETJ | 2 GB |
| Inazuma Eleven 1 | NDS | EU (ES) | YEES | 256 MB |
| Inazuma Eleven 2 (Tormenta de Fuego) | NDS | EU (ES) | BEES | 256 MB |
