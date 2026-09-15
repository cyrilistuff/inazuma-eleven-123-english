# Herramientas

## Paquete ie123kit (migración en curso, #40)

- El código nuevo vive en `tools/src/ie123kit` y se instala con `pip install -e tools[dev]`.
- Tests: `python -X utf8 -m pytest tools/tests -m "not requiere_rom" -q`.
- Los 5 ficheros bloqueados (`dialogue_typography.py`, `font_patch.py`, `dialogue_lock.py`,
  `build_ie1_probe.py`, `build_ui_revision.py`) siguen intactos en `tools/` y excluidos de ruff/black.
- Los tests heredados de la raíz (`tools/test_*.py`) también quedan fuera de ruff (`./test_*.py` en
  `extend-exclude`, anclado a `tools/`): no se retocan durante la migración. Los tests nuevos de
  `tools/tests/` sí pasan por ruff.
- Los scripts vigentes de `tools/` siguen funcionando igual.
- Los 25 scripts y tests retirados en F1.2 (#43) viven en `tools/_archivo/` (sin stubs, no importables);
  motivos y sustitutos en [`_archivo/README.md`](_archivo/README.md). `patch_code.py`, `patch_cro.py` y otros 4 scripts se archivaron en F1.4 (#45).

### F1.3 (#44): módulos de motor trasladados

El código de estos 16 módulos se copió tal cual a `ie123kit.nucleo`. En `tools/<nombre>.py` queda
un shim sin lógica que sustituye su entrada de `sys.modules` por el módulo del paquete, así que
`import fa_unpack` o `from lz10 import compress` siguen devolviendo los mismos objetos y las
mutaciones de globales (p. ej. `lz10.MAX_CAND`) llegan al módulo real. Como `nucleo` no imprime ni
termina el proceso, los módulos con un CLI que escribe en pantalla, o cuyo bloque `__main__` no llama
a `main()`, pasan por una **fachada `_legado`**: la lógica va a `nucleo`, y el `main()` o el bloque CLI
originales van a `ie123kit/_legado/<nombre>.py`, que además reexporta todos los nombres de antes,
privados incluidos.

| Módulo antiguo (`tools/`) | Módulo real | Tipo de shim |
|---|---|---|
| `lz10.py` | `ie123kit.nucleo.compresion.lz10` | alias directo |
| `blz.py` | `ie123kit.nucleo.compresion.blz` | fachada `_legado.blz` |
| `sszl.py` | `ie123kit.nucleo.compresion.sszl` | alias directo |
| `ui_archive.py` | `ie123kit.nucleo.contenedores.arcv` + `nucleo.compresion.sszl` | fachada `_legado.ui_archive` |
| `nds_unpack.py` | `ie123kit.nucleo.contenedores.nds_rom` | fachada `_legado.nds_unpack` |
| `qna_regions.py` | `ie123kit.nucleo.graficos.qna` | alias directo |
| `legacy_sprite.py` | `ie123kit.nucleo.graficos.pac_sprite` | alias directo |
| `nftr_metrics.py` | `ie123kit.nucleo.fuentes.nftr` | fachada `_legado.nftr_metrics` |
| `bcfnt.py` | `ie123kit.nucleo.fuentes.bcfnt` | fachada `_legado.bcfnt` (permanente) |
| `ctpk_ui.py` | `ie123kit.nucleo.graficos.ctpk` | alias directo |
| `ssd_records.py` | `ie123kit.nucleo.eventos.ssd` | alias directo |
| `fa_unpack.py` | `ie123kit.nucleo.contenedores.fa` | fachada `_legado.fa_unpack` |
| `fa_repack.py` | `ie123kit.nucleo.contenedores.fa` (`fe_offset_of`) | fachada `_legado.fa_repack` |
| `patch_smdh_title.py` | `ie123kit.nucleo.ejecutable.smdh` | fachada `_legado.patch_smdh_title` |
| `harvest_log.py` | `ie123kit.nucleo.construir.registro_azahar` | fachada `_legado.harvest_log` |
| `limpiar_work.py` | `ie123kit.nucleo.construir.limpieza` | fachada `_legado.limpiar_work` |

- Los shims se generan con `python -m ie123kit.nucleo.compat.shims generar <nombre>` (el destino sale
  de `MAPA`; `lz10` va con `--cli ninguno`) y se verifican con
  `python -m ie123kit.nucleo.compat.shims comprobar`. No se editan a mano.
- Las invocaciones documentadas siguen funcionando igual: `python tools/fa_unpack.py`,
  `python tools/nds_unpack.py`, `python tools/harvest_log.py`, `python tools/limpiar_work.py --borrar`,
  `python tools/blz.py in out` y `python tools/patch_smdh_title.py`.
- `python tools/lz10.py` ya no ejecuta el autotest de ida y vuelta (su shim no tiene CLI, para no romper
  la mutación de `MAX_CAND`). Ahora se lanza con `python -m ie123kit.nucleo.compresion.lz10`.
- `bcfnt.py` es un shim **permanente**: `font_patch.py` está bloqueado (v20) y hace `from bcfnt import BCFNT`.
- Las rutas `REPO`/`ROOT` de `fa_repack`, `harvest_log` y `limpiar_work` salen ahora de `find_root`
  (`mods_to_moflex` queda para F1.4).
- Puerta del bloqueo v20 sobre una candidata construida:
  `python -m ie123kit.nucleo.validar.bloqueo --candidata <archive.fa>` (acepta también la carpeta de la
  candidata). Extrae en crudo las 5 fuentes de `dialogue_lock.FONT_HASHES` a un temporal que borra al
  terminar y llama a `dialogue_lock.validate`; devuelve 0 si todo cuadra y 1 si no.
- `tools/tests/compat/test_traslados.py` comprueba el mapa, que cada shim no tenga lógica, la identidad
  de módulos y la superficie de `superficie_v0.json`.

### F1.4 (#45): divisiones, fachadas de legado y reparto por juego

Los 13 módulos restantes pasan a `ie123kit` con el mismo patrón de shims que en F1.3 (29 shims en
total en `tools/`). Seis scripts sin importadores se archivan con `git mv` en `tools/_archivo`, sin shim.

| Módulo antiguo (`tools/`) | Módulo(s) real(es) | Tipo |
|---|---|---|
| `pkb_unpack.py` | `ie123kit.nucleo.eventos.packnum` + `nucleo.texto.nds_latin` | fachada `_legado.pkb_unpack` |
| `build_glossary.py` | `ie123kit.nucleo.texto.nds_latin` | fachada `_legado.build_glossary` |
| `ds_official.py` | `ie123kit.nucleo.texto.nds_latin` + `nucleo.eventos.alineado_ids` | fachada `_legado.ds_official` (`main`/`align` con `--legado-lo-se`) |
| `audit_dialogo_ids.py` | `ie123kit.nucleo.eventos.alineado_ids` (auditoría IE1 en la fachada) | fachada `_legado.audit_dialogo_ids` |
| `reinsert.py` | `ie123kit.nucleo.texto.sjis_portador` + `nucleo.texto.tipografia_v20` | fachada `_legado.reinsert` |
| `translate_ui_textures.py` | `ie123kit.nucleo.graficos.pintado` | fachada `_legado.translate_ui_textures` |
| `mods_to_moflex.py` | `ie123kit.nucleo.media.moflex` + `nucleo.media.subtitulos_dat` | fachada `_legado.mods_to_moflex` |
| `verify_candidate.py` | `ie123kit.nucleo.validar.candidata` + `ie1.verificar` | fachada `_legado.verify_candidate` |
| `ie1_keyboard.py` | `ie123kit.ie1.graficos.teclado` | alias directo |
| `ds_roster.py` | `ie123kit._legado.ds_roster` | cuarentena |
| `reinsert_var.py` | `ie123kit._legado.reinsert_var` | cuarentena |
| `ssd_reinsert.py` | `ie123kit._legado.ssd_reinsert` | cuarentena |
| `validate.py` | `ie123kit._legado.validate` | cuarentena |
| `ie1_tables.py` | `ie123kit.nucleo.registros.tabla_fija` + `ie1.texto.tablas` | archivado |
| `ie1_media.py` | `ie123kit.nucleo.media.audio` + `ie1.media.voces` | archivado |
| `validate_ie1_media.py` | `ie123kit.ie1.verificar` + `nucleo.media.moflex.disposicion_rotacion` | archivado |
| `patch_exefs.py` | `ie123kit.nucleo.contenedores.exefs` (experimental) | archivado |
| `patch_code.py`, `patch_cro.py` | ninguno (**peligrosos**) | archivado |

- **Re-exports perezosos de los bloqueados** (no copian código; devuelven los mismos objetos que
  `tools/`): `ie123kit.nucleo.texto.ancho_completo` (de `dialogue_typography`, más `decode_fullwidth`
  nuevo), `ie123kit.nucleo.texto.tipografia_v20` (de `build_ie1_probe`) e
  `ie123kit.nucleo.fuentes.glifos` (de `font_patch`). Todos cargan los congelados con
  `ie123kit.nucleo.config.congelados.cargar`.
- `ie123kit.nucleo.construir.candidata` contiene la construcción de candidatas;
  `tools/build_ui_revision.py` **sigue congelado** en `tools/` y se usa igual.
- **Cuarentena**: `ds_roster`, `reinsert_var`, `ssd_reinsert` y `validate` solo ejecutan su CLI con
  `--legado-lo-se`; `ds_official` exige la misma bandera para `main`/`align` (o `IE123_LEGADO_LO_SE=1`
  cuando `align` se llama desde código).
- Órdenes nuevas:
  - `python -m ie123kit.ie1.media.voces [--stage]` (sustituye a `python tools/ie1_media.py --stage`);
  - `python -m ie123kit.nucleo.construir.candidata --base … --ui … --output …`.
- Cada objetivo declara sus activos en `activos.toml` (esquema 1: prefijos de `archive.fa`, CRO y rutas
  de solo lectura) en `juego_principal/`, `ie1/`, `ie2/<versión>/` e `ie3/<versión>/`. El registro de
  activos del servicio los leerá en F2.1.
- La invocación documentada `python tools/verify_candidate.py` sigue igual.
- `tools/tests/compat/test_traslados_f14.py` comprueba el mapa, los shims, los archivados, la raíz final
  de `tools/`, los congelados y las identidades de texto.

## Audio y cinemáticas europeas de IE1

- `python -m ie123kit.ie1.media.voces --stage` (antes `ie1_media.py --stage`): inventaría los SADL de IE1 DS/3DS y prepara los 70
  reemplazos europeos en el mod local de volumen 1.
- `setup_mobipeg.ps1`: descarga y verifica la versión portátil x86 de mobipeg 2.1.
- `mods_to_moflex.py`: convierte una película `.mods` de DS, incrusta su pista
  española `.dat` y restaura la orientación MOFLEX `0x16` de la recopilación.
- `work/ie1/capas/v58/cinematicas/build.py`: genera las 21 cinemáticas europeas de IE1
  (sustituye a `build_ie1_movies.py`, archivado en `_archivo/`; ver [`_archivo/README.md`](_archivo/README.md)).
- `work/ie1/capas/v67/titulo_logo` (sustituye a `fix_ie1_title_logo.py`, archivado en `_archivo/`): aísla el wordmark europeo y sustituye el rótulo
  rectangular anterior conservando el balón y el rayo animados del juego.
- `setup_vgmstream.ps1` + `validate_ie1_media.py` (archivado en F1.4; sus reglas viven en
  `ie123kit.ie1.verificar`): preparan el decodificador
  portátil y comprueban los 70 SADL instalados y las 21 películas sin generar
  WAV ni vídeos temporales. Véase `docs/IE1_AUDIO_CINEMATICAS_V35.md`.

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

### Candidatas IE1 por capas (v28 en adelante)
- `dialogue_lock.py` — bloqueo de la tipografía v20 aprobada por el usuario
  (fuentes, codificación fullwidth, métrica 11 px / 220 px). Todo script que
  toque texto lo valida; no desactivarlo.
- `translate_ui_textures.py` — aplica un manifiesto JSON de rectángulos de texto a
  texturas CTPK sin cambiar tamaños ni metadatos. Borrado: relleno plano,
  `row_sample`, `bright` o `none` (cuando operaciones previas ya restauraron el fondo).
- `build_ui_revision.py` — genera una candidata `archive.fa` sobre la anterior:
  eventos SSD con identidad de registros comprobada (`<ui>/events`), capas de
  archivos repetibles (`--extra`, la última gana) y CRO (`--cro`). Nunca
  sobrescribe una candidata existente.
- `verify_candidate.py` — verificación estática de una candidata frente a su base:
  entradas de las capas, resto del archivo y fuentes idénticos, eventos SSD y
  literales del CRO permitidos, bloqueo tipográfico.
- `work/ie1/capas/v33/mch_story` y `work/ie1/capas/v55/pachangas` (sustituyen a
  `build_match_content_patch.py`, archivado en `_archivo/`) — pachangas, cadena de partidos y nombres de
  `team.pkb`/`teamtitle.dat`/`clubinfo.dat`.
- Detalle de la tanda actual y orden completa: `docs/IE1_V29_TANDA.md`.

### Compilar la build
> **Guía completa (requisitos, regeneración de datos, tabla de flags):**
> [`../docs/DESARROLLO.md`](../docs/DESARROLLO.md).

> **Pipeline HISTÓRICO v27.** `build_3ds_var.py` está archivado en `_archivo/` (ver [`_archivo/README.md`](_archivo/README.md)).
> Cadena vigente: `work/ie1/capas/v33/_final/build_rom.py` (ROM IE1), `build_ui_revision.py`
> (candidatas `work/shared/candidatas/probe_ie1_vNN`) y `verify_candidate.py`.

Secuencia histórica (CSV → ROM jugable), con los **flags de la build v27**:
```
python tools/reinsert.py                                  # fuentes (acentos) + roster + UI -> work/archive_es.fa
python tools/reinsert_var.py game1                        # dialogo (long. variable) -> work/eve_var/
SKIP_CRO=1 NO_CODE_PATCH=1 python tools/_archivo/build_3ds_var.py game1   # (archivado) VALIDA y compila -> work/build/*.3ds
pwsh -File tools/build_patch.ps1 -Translated "work\build\inazuma123_es_var.3ds" -Patch "patch\inazuma123-es-vNN.xdelta"
```
`_archivo/build_3ds_var.py` corría `validate.py` ANTES de compilar y **aborta** si hay una
regresion conocida (operandos corruptos, furigana que crece ❌#9, dialogo vacio,
desbalance marcador↔lectura). `SKIP_VALIDATE=1` lo fuerza (solo builds de prueba).
La build v27 = `SKIP_CRO=1` + `NO_CODE_PATCH=1` (el resto de flags por defecto):
gameplay crece a texto completo, sistema/intro INPLACE, fallback global, CRO sin parchear.

### Detección de errores en runtime (cosecha de logs)
La idea: **cada partida deja su rastro de errores en NUESTRO registro**, para ir
detectando qué mejorar en la siguiente versión sin mirar el log en vivo.

- `harvest_log.py` — lee el log de Azahar, agrupa cada error por su **PC** (firma
  estable del bug; la dirección leída varía y se descarta), separa **crashes**
  (bugs nuestros) del **ruido benigno del emulador**, y lo funde en
  `logs/runtime_errors.json` (persistente) + `logs/INFORME_ERRORES.md`. Los PCs ya
  diagnosticados se anotan en `KNOWN_PCS` (dentro del script).
  ```
  python tools/harvest_log.py            # cosecha el log actual + .old
  python tools/harvest_log.py --report   # solo reimprime el informe
  ```
- `jugar.ps1` — lanza la build en Azahar y, **al cerrar el emulador, cosecha
  automáticamente** la sesión. Así el registro se alimenta solo en cada arranque.
  ```
  pwsh -File tools/jugar.ps1 [ruta\build.3ds]   # sin arg: la build más reciente
  ```

> `logs/` está en `.gitignore` (datos locales de la máquina). A GitHub solo van las
> herramientas, no la cosecha.

> Coloca los ejecutables descargados en `tools/bin/` (ignorado por git).
