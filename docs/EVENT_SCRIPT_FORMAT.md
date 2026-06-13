# Formato de los scripts de evento (eve.pkb / evet.pkb) — notas de RE

Estado: **RESUELTO** (extracción limpia). El contenedor es PackNum y **cada entrada
está comprimida con LZ10 de Nintendo**. Tras descomprimir, el texto son cadenas
Shift-JIS separadas por NUL. (Lo que parecían "códigos de control" eran flags y
back-references de LZ10.) Reinserción: pendiente recomprimir + fixup de offsets.

## Contenedor PackNum (RESUELTO — `tools/pkb_unpack.py`)

- `.pkh`: `"PackNum YYYYMMDD"` (16 B) · `+0x10 u32` tamaño · `+0x30` tabla de
  entradas de **12 B**: `{event_id u32, offset u32, size u32}`.
- `event_id` = id de mapa/evento (p.ej. `10010001`). Offsets cubren el `.pkb`.
- Juego 1: 3DS `eve.pkb` = **1293 eventos**; NDS `evet.pkb` = **1737**;
  **1289 `event_id` comunes** → alineables (etapa 4).

## Compresión LZ10 (RESUELTO)

Cada entrada del `.pkb` empieza por `10 XX XX 00` = **LZ10 de Nintendo**
(`0x10` + tamaño descomprimido de 24 bits LE). `tools/pkb_unpack.py:lz10_decompress`.
Hallado vía comunidad ([Kuriimu #249](https://github.com/IcySon55/Kuriimu/issues/249),
GBAtemp). Tras descomprimir → cadenas Shift-JIS separadas por NUL.

## Texto descomprimido

- **Sustitución**: `%s` (nombre), `%d` (número).
- **Furigana/ruby**: `%1F`/`%2F`/`%3F` marcan kanji; la **lectura** va como cadena
  aparte (solo hiragana) → se filtra con `is_furigana()`.
- `\n` literal (backslash+n) = salto de línea.
- Encoding: **Shift-JIS** (3DS) / Latin propia (NDS, ver `build_glossary.NDS_DEC`).

## Estado de extracción y alineado

- `tools/pkb_unpack.py --text` → diálogo LIMPIO (descomprime + NUL-split + filtro).
  JP ~57k cadenas; ES ~22k.
- `tools/align_events.py` → empareja por `event_id` (1289 comunes), quita furigana,
  dedup. **133 eventos con nº de líneas JP=ES idéntico → emparejado posicional
  perfecto** (reúso directo del ES oficial). El resto necesita matching más fino.

## Pendiente (reinserción, etapa 7)

Recomprimir/almacenar el texto ES, **fixup de offsets** (cambian los tamaños):
pkb-entry → tabla `.pkh` → `archive.fa` (B123) → NCSD `.3ds`. Y la fuente (ñ, tildes,
¿¡) debe existir en el 3DS (Shift-JIS no los tiene → asignar códigos + glifos).
