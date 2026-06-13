# Formato de los scripts de evento (eve.pkb / evet.pkb) — notas de RE

Estado: **parcialmente resuelto**. El contenedor (PackNum) está resuelto; el
formato de mensaje in-band está caracterizado pero **falta la tabla exacta de
códigos de control** para extracción/reinserción 100% limpia (issue #3).

## Contenedor PackNum (RESUELTO — `tools/pkb_unpack.py`)

- `.pkh`: `"PackNum YYYYMMDD"` (16 B) · `+0x10 u32` tamaño · `+0x30` tabla de
  entradas de **12 B**: `{event_id u32, offset u32, size u32}`.
- `event_id` = id de mapa/evento (p.ej. `10010001`). Offsets cubren el `.pkb`.
- Juego 1: 3DS `eve.pkb` = **1293 eventos**; NDS `evet.pkb` = **1737**;
  **1289 `event_id` comunes** → alineables (etapa 4).

## Mensaje in-band (caracterizado, tabla PENDIENTE)

Dentro de cada evento el texto va mezclado con el script. Codificación:
**Shift-JIS** (3DS) / Latin propia (NDS). Elementos identificados:

- **Sustitución printf**: `%s` (nombre, 724×), `%d` (número, 225×).
- **Furigana/ruby**: `%1F` (669×), `%2F` (678×), `%3F` (399×), `%4F` — delimitan
  kanji/lectura. (Semántica exacta por confirmar.)
- **Otros escapes**: `%kw`, `%g/%G`, `%O/%o`, `%c`, `%0..%9`…
- **Códigos de control de 1 byte** recurrentes cerca del texto: `0x1C`, `0x1F`,
  y separadores `0x00`/`0x09`/`0x0A`. Tras `！`(0x8149) abundan `40 1F`, `\n`.
- El resto de bytes `<0x20` (0x0F, 0x01, 0x03, 0x10…) son **opcodes del script**.

**Lo que falta:** determinar, para cada código de control, su **longitud y
semántica** (cuántos bytes de parámetro consume) y los **marcadores de inicio/fin
de mensaje**. Sin eso, la extracción tiene ruido en los bordes y la **reinserción
exacta no es fiable**. Es el objetivo del issue #3.

## Extracción best-effort disponible

- `tools/pkb_unpack.py --text` → vuelca líneas (tokeniza `%XX` como `{..}`, filtra
  por hiragana). Cobertura: diálogo en **962/1293** eventos (~3939 líneas JP).
- `tools/align_events.py` → agrupa por `event_id` el JP (3DS) y el ES oficial (NDS)
  lado a lado (1035 eventos con texto). Material de trabajo, **no** listo para
  reinsertar. Salida en `work/` (no se sube: contiene texto extraído).
