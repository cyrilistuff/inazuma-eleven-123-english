> Actualización 2026-09-06: candidata IE1 v6 de interfaz instalada para prueba.
> Ver [detalle y limitaciones](IE1_UI_Y_CAPITULO1.md). Las etiquetas históricas
> de estabilidad que aparecen abajo no sustituyen el protocolo QA vigente.

# Progreso del proyecto

## Retoma 2026-09-05: diagnóstico y prueba pendiente

- Protocolo obligatorio del usuario: [PROTOCOLO_QA_IE1.md](PROTOCOLO_QA_IE1.md).
- CIA convertida localmente a NCSD conservando programa y manual, verificados
  contra SHA-256 del TMD y contra las particiones de salida. Script temporal
  eliminado por petición del usuario. La nueva base NO equivale al cartucho usado
  para los xdelta antiguos.
- Descubierto el tamaño por registro de texto inline SSD, omitido por el motor
  anterior. Ver [SSD_REGISTROS_IE1.md](SSD_REGISTROS_IE1.md). Lectura y roundtrip
  exactos de 1.240 SSD originales; cinco pruebas sintéticas de regresión pasan.
- Corregido el falso éxito del validador cuando faltan PKB/PKH o la selección está
  vacía; tres pruebas de regresión pasan.
- Preparada prueba local de 92010100, 92010200 y 92010250. Verificado que cambia
  solo esos eventos y tres fuentes; 16 textos insertados, uno rechazado por longitud.
  Instalado como mod local de Azahar; el usuario confirmó arranque y diálogo
  español dentro del club con capturas. QA-001 abierto: cortes dentro de palabras
  y fragmento al cambiar de página. Evidencias locales en `work/qa_dialogue_001/`.
  Corregido el reflujo por caracteres en el generador; nueva candidata por avances
  de FONT12 instalada tras cerrar Azahar: `work/probe_ie1_v2/archive.fa`, SHA-256
  `a2cb278c36866fedfad569bed436986de59596f1107aab7d3bc433f7050a1c4c`.
  Cuatro pruebas de reflujo pasan; verificados 16 registros insertados, anchos
  calculados, instrucciones y demás registros intactos. Pendiente repetir toda
  esa conversación en Azahar, incluidos los cambios de página y el cierre.
- Original convertido probado en Azahar 2126.0: llega al recopilatorio; al entrar
  en IE1 se observó pantalla negra prolongada y 0 FPS de aplicación, sin excepción
  CPU en el log. Se detuvo esa prueba. En la repetición con región japonesa y
  control del usuario se observó al personaje jugable frente al club. La
  configuración anterior era europea; no atribuir una causa única sin aislarla.
- `tools/jugar.ps1` usa la instalación de Program Files (o parámetro `-Azahar`),
  conserva el log previo y evita mezclar sesiones simultáneas.

Las conclusiones antiguas siguientes son históricas; no sustituyen las pruebas
actuales ni demuestran estabilidad de la nueva reinserción.

Leyenda: ⬜ pendiente · 🟡 en curso · ✅ hecho

---

## ⏸️ ESTADO FINAL (proyecto pausado, build v27) — 2026-06

**Build v27** = la mejor lograda: **arranca, crea partida, intro + diálogo de historia en
español**. Parche [`patch/inazuma123-es-v27.xdelta`](../patch/). Cómo trabajar:
[`DESARROLLO.md`](DESARROLLO.md).

**Motor nuevo de reinserción** (`tools/ssd_reinsert.py`): el texto SSD se referencia por
**índice** (no por offset) → el bytecode queda intacto, el diálogo de **gameplay crece libre**
(sin truncar), y los eventos de **sistema/intro** van INPLACE a mismo tamaño con **re-paginación**
(reparte el ES en las páginas `\f` del JP) + **fallback global** (reusa traducción del mismo
japonés en otro evento, +~22 % cobertura). Validador `validate.py` consciente del crecimiento.

**Muros DEFINITIVOS** (no reintentar — [`FURIGANA_LECCIONES.md`](FURIGANA_LECCIONES.md)):
- ❌ **Parchear el código es inviable**: la zona de caves del CRO (`0x50E14`) es de
  **relocalización** → el loader la pisa → crash `0xAD9E1C`. Ni ruby (`0xABFCC0`) ni `code.bin`.
- ❌ **Sistema/intro no puede crecer** (ruby cuelga al avanzar, ❌#9) → mismo tamaño → truncado.
  La apertura/crear-partida (`92010100..92010249`) exige eventos intactos (❌#1).
- 📉 **Techo de datos: ~48 %** del diálogo tiene traducción; el resto no existe en los datos.

**Qué queda** para subir cobertura: traducir a mano lo `pendiente`/`revisar` de `dialogo.csv`,
objetos/técnicas (#1/#2), juego 3. El motor ya aguanta; el límite es de datos.

---

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
  marcadores) en muestra de 240 eventos: **OK**. Cobertura real game1: **4923
  líneas de furigana aplicadas (44,8% de las disponibles)** + 1741 sin furigana =
  6664 (vs v10 que aplicaba 0 furigana). El total es parejo a v10 porque al
  competir por el presupuesto de bytes se revierten más líneas, pero el **diálogo
  de historia visible** sube mucho. **Riesgo restante: cosmético** (ruby kana
  flotante), no de cuelgue. **Falta prueba visual.** Ver FORMATOS.md §"SSD".
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
