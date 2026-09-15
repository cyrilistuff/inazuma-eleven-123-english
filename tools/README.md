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
  motivos y sustitutos en [`_archivo/README.md`](_archivo/README.md). `patch_code.py` y `patch_cro.py` se archivarán en F1.4.

## Audio y cinemáticas europeas de IE1

- `ie1_media.py --stage`: inventaría los SADL de IE1 DS/3DS y prepara los 70
  reemplazos europeos en el mod local de volumen 1.
- `setup_mobipeg.ps1`: descarga y verifica la versión portátil x86 de mobipeg 2.1.
- `mods_to_moflex.py`: convierte una película `.mods` de DS, incrusta su pista
  española `.dat` y restaura la orientación MOFLEX `0x16` de la recopilación.
- `work/ie1/capas/v58/cinematicas/build.py`: genera las 21 cinemáticas europeas de IE1
  (sustituye a `build_ie1_movies.py`, archivado en `_archivo/`; ver [`_archivo/README.md`](_archivo/README.md)).
- `work/ie1/capas/v67/titulo_logo` (sustituye a `fix_ie1_title_logo.py`, archivado en `_archivo/`): aísla el wordmark europeo y sustituye el rótulo
  rectangular anterior conservando el balón y el rayo animados del juego.
- `setup_vgmstream.ps1` + `validate_ie1_media.py`: preparan el decodificador
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
