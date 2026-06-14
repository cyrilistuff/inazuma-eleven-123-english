# Progreso del proyecto

Leyenda: ⬜ pendiente · 🟡 en curso · ✅ hecho

## Fase 0 — Infraestructura
- ✅ Diagnóstico de las ROMs (formato, cifrado, regiones)
- ✅ Estructura del repositorio + git init
- ✅ `.gitignore`, `README.md`, `LEGAL.md`, `CLAUDE.md` (normas de trabajo)
- ✅ Repo en GitHub (privado) + push: `luishidalgoa/inazuma-eleven-123-spanish`
- ✅ Workflow de Issues: #1 objetos, #2 técnicas, #3 diálogo, #4 juego 2, #5 juego 3
  (Project board pendiente: el token necesita scope `project`)
- 🟡 Herramientas (3dstool ✅, extractores propios ✅; xdelta3 pendiente p/ release)

## Fase 1 — Extracción y mapeo
- ✅ Extraer RomFS/ExeFS de la ROM 3DS (1·2·3) → `work/romfs`, `work/exefs`
- ✅ Mapa de primer nivel del RomFS 3DS
- ✅ **`archive.fa` decodificado** (magic `B123` = variante ARC0/XFSA) y
  **extractor propio** `tools/fa_unpack.py` (15.547 archivos, rutas correctas)
- ✅ Verificado que las herramientas de la comunidad NO soportan `B123` (plan B)
- ✅ Localizado el texto: `message/jp/GameString.bin` (UTF-8), `import/*.itx`
  (parámetros), `field_message*.arc` (diálogos, en contenedores ARCV)
- ✅ Primer vistazo a texto real del juego 1 (cadenas de sistema en UTF-8)
- ✅ **Diálogo localizado**: `inazuma1/data_iz/script/eve.pkb` (4,2 MB, historia)
  + `mch.pkb` (combates), paquete "PackNum". Texto en bytecode Shift-JIS (issue #3)
- 🟡 Parser del script de evento (bytecode) para volcar diálogo a CSV/JSON + alinear
  con el español oficial del NDS `evet.pkb` (misma estructura)
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
- ✅ Extraído el filesystem de IE1/IE2 NDS (ES) → `work/ie1_es`, `work/ie2_es`
- ✅ Localizado el texto español oficial en carpetas `data_iz/logic/sp/` y
  `data_iz/script/sp/`: `command.STR` (técnicas), `item.STR` (objetos),
  `unitbase.STR/.dat` (jugadores), `evet.pkb`/`mcht.pkb` (eventos), `team.pkb`
- ✅ Confirmados términos oficiales (Regate, Bloqueo, Vaselina, Testarazo…) con
  `tools/nds_str_dump.py`
- ✅ Mapear la **tabla de codificación** NDS (parcial: á é í ó ú ñ ü ¿ ¡ Í)
- ✅ **Glosario JP↔ES del juego 1** generado (`tools/build_glossary.py`):
  ~1174 jugadores, 20 títulos de equipo, 133 menús = **~1327 parejas exactas**
  (alineadas por índice de registro). Verificado: 円堂守→Mark Evans, 鬼道有人→Jude Sharp
- 🟡 Objetos y técnicas/hissatsu: el `item.dat`/`command.STR` no casan 1:1
  (estructura/recuento distintos) → pendiente parsear su índice real

## Juego 2
- ✅ Extraído + alineado con NDS IE2 (74% con ES oficial, `translation/game2/dialogo.csv`)
- ✅ **Reinsertado en la build** (multi-juego): 2610 eventos / 24843 líneas ES

## UI / menús (AMBOS juegos)
- ✅ **Re-insertor de UI** (`tools/ui_insert.py`): inserta en la ROM (mismo tamaño,
  acentos vía griego→SJIS): menús (`games.STR`), jugadores (`unitbase.dat`),
  equipos (`teamtitle.dat`). `build_glossary` multi-juego.
  - Juego 1: menús 133, jugadores 1170, equipos 20
  - Juego 2: menús 209, jugadores 2032, equipos 20  (verificado: Axel Blaze, etc.)
- ⬜ Objetos/técnicas (#1/#2) · GameString.bin (textos de sistema)

## Builds / parches
- v1–v5 (ver historial) · v6 (4.95M): j1+j2 diálogo + UI completa
- Compresor LZ10 (lazy + cap 256) — recuperada la cobertura del juego 1

### Investigación "pantalla negra / japonés" (v7–v13) — 2026-06
Tras crear partida la build se quedaba en negro o el diálogo seguía en japonés.
Aislado por bisección:
- **Causa del cuelgue (v1–v6):** traducir cadenas **estructurales** del script
  (etiquetas, comentarios `(`, debug en inglés) corrompía el bytecode →
  `looks_like_dialogue()` las excluye. **v10 ARRANCA** y se juega.
- **Furigana:** v10 **salta** los diálogos con furigana (`%NF`) → solo ~30% del
  texto sale en español (el 70% lleva furigana). Quitar los marcadores (v12) o las
  lecturas (v11) **descuadra el consumo de lecturas y cuelga**.
- **v13 (candidata, `FURIGANA_KEEP_MARKERS`):** traduce el furigana pero
  **reinyecta los mismos marcadores** (conteo invariante) → las lecturas se siguen
  consumiendo. Invariantes verificadas offline (tamaño, nº de chunks y de
  marcadores) en muestra de 240 eventos: **OK**. Cobertura ~3× la de v10.
  **Riesgo restante: cosmético** (ruby kana flotante), no de cuelgue. **Falta que
  el usuario lo pruebe visualmente.** Ver `docs/FORMATOS.md` §"Estructura SSD".
- **Recomendación actual:** **v10 = estable** (arranca seguro, ~30% diálogo).
  **v13 = a probar** (≈90% diálogo si el motor tolera el ruby sobrante).
- ⬜ Verificación de arranque/visual de v13 en emulador (**usuario**)

## Fase 3 — Traducción
- ✅ Contenedor **PackNum resuelto** (`tools/pkb_unpack.py`): 1293 eventos
- ✅ **Entradas comprimidas con LZ10** → diálogo extraído **LIMPIO** (no eran
  códigos de control). Etapa 3 resuelta.
- ✅ **Alineado por `event_id`** JP(3DS)↔ES(NDS): 1289 ids comunes; **133 eventos
  con nº de líneas idéntico → ES oficial aplicado** (934 líneas), `tools/align_events.py`
- ✅ **Alineado fino (Needleman-Wunsch)** con señal de longitud + formato (%s/%d/\n):
  `translation/game1/dialogo.csv` (29985 líneas). **Cobertura con ES: 66,2%**
  (oficial 3,1% + revisar 56,4% + auto-dup 6,7%); pendiente 33,8%
  (`tools/align_events.py`, `tools/build_translation.py`)
- 🟡 Traducir a mano lo `pendiente` (33,8%) y revisar lo `revisar`
- ⬜ Juego 2 · ⬜ Juego 3

## Fase 4 — Fuente y gráficos
- ✅ **Fuente BCFNT ampliada** (`tools/bcfnt.py`, `tools/font_patch.py`): añadidos
  ñÑáéíóúüÁÉÍÓÚ¡¿ reusando glifos griegos (swizzle morton + LA4 validados, CWDH
  copiado). Mapeo byte→glifo: ES→griego→SJIS (0x839F+). Parcheadas FONT12T/12/8.
- ⬜ Gráficos con texto incrustado

## Fase 5 — Build y release
- ✅ Re-encoder real del ES (`tools/reinsert.py`): 477 eventos, 6893 líneas ES
  (sin acentos; saltados 531 por tamaño LZ10)
- ✅ Reinsertar + reconstruir la ROM (parche in-place de archive.fa, `tools/build_3ds.py`)
- ✅ **Parche v1** `patch/inazuma123-es.xdelta` (~416 KB, sin acentos, 477 eventos)
- ✅ **LZ10 con lazy matching** → más eventos caben
- ✅ **Parche v2** `patch/inazuma123-es-v2.xdelta` (~1,14 MB): con acentos, 821 eventos
- ✅ **Ajuste parcial por evento** (revierte líneas que no caben en vez de saltar
  el evento) → **Parche v3** `patch/inazuma123-es-v3.xdelta` (~1,53 MB):
  **992/1008 eventos (≈98% de los traducibles), 12343 líneas ES**, roundtrip OK
- ⬜ Pruebas en emulador (Lime3DS / Azahar) — **lo verifica el usuario**
- 🟡 Traducir manualmente el 33,8% pendiente (líneas JP SIN equivalente oficial NDS)
- ⬜ Primera release pública

## Notas de las ROMs (referencia)
| ROM | Plataforma | Región | Código | Tamaño |
|---|---|---|---|---|
| Inazuma Eleven 1·2·3 | 3DS (NCSD, descifrado) | JP | CTR-P-AETJ | 2 GB |
| Inazuma Eleven 1 | NDS | EU (ES) | YEES | 256 MB |
| Inazuma Eleven 2 (Tormenta de Fuego) | NDS | EU (ES) | BEES | 256 MB |
