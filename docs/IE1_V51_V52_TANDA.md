# Tandas v51–v52 — frases con voz, capítulo, estrategias y resultados (issues #36, #37)

## v51 (`work/ie1/capas/v51/voces`, base v50)

- **Frases con voz**: auditoría `work/ie1/capas/v51/voces/auditoria.py`. En IE1 hay 31 frases con voz europea
  (`NN_N.SAD`). 27 no coincidían con el audio: estaban en los eventos protegidos de crear partida
  92010100 (01_1..01_10) y 92010340 (02_*), que la v36 no tocó. Se sustituyen por la línea oficial NDS
  (primera frase tras cada llamada de voz), con el método de v36 (`approved_layout` + `encode_fullwidth`
  + `ssd_records.replace`). También 03_5 (92011300), que solo cambiaba el salto de línea.
  **Riesgo**: eventos del inicio de partida; probar partida nueva hasta la escena de Axel y la caseta.
- **Equipos Centella** sin «C.»: Lanzas, Bombas, Jets, Chicos, Bravos.

## v52 (`work/ie1/capas/v52`, base v51)

- **Capítulo**: los romanos Ⅰ…Ⅹ no existen en `FONT12.NFTR` (la fuente que pinta la caja de partida) y
  salían en blanco. Ahora dígitos de ancho completo １…９ y «Ｘ» para el 10.
- **Estrategias** (CRO 0x1b1cdb/0x1b1ce4/0x1b1ceb): estaban en ASCII de 1 byte y más largas que el japonés
  («Nomal», «Norma»). Ahora ancho completo dentro de los bytes del japonés: «Norm», «Def», «Ata».
- **Resultados** (`game_result_t · result_exp_t01`, rectángulo de 92 px): «Experiencia total» → «Experiencia».
- `archive.fa` `dc262288…`, CRO `b9b358da…`. Instalada 2026-09-15.

## Subtítulos de cinemáticas con retraso

Los `.dat` de `movie/txt/sp` cuentan en **ticks de 30 Hz**, no en fotogramas: `op00.mods` tiene 1.763
fotogramas a 20 fps y su último subtítulo termina en 2.675 (= 1.763 × 30/20). `tools/mods_to_moflex.py`
comparaba el tick con el número de fotograma, así que cada subtítulo salía 1,5× (20 fps) o 1,25× (24 fps)
más tarde y los finales no llegaban a verse. Corregido con `SUBTITLE_TICK_RATE = 30`; se regeneran las 21
películas (`tools/build_ie1_movies.py`).

## Pendiente

- «ナイス!» y otros sprites de DS en el campo: 95 paquetes `pic3d/*` tienen versión española en la NDS
  (`pic3d/sp`). Probar sustitución en una candidata aparte.
