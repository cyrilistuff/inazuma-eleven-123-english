# tools/_archivo — scripts retirados

Esta carpeta guarda scripts **retirados** de `tools/` durante la migración al paquete
`ie123kit` (subfase F1.2, [issue #43](https://github.com/luishidalgoa/inazuma-eleven-123-spanish/issues/43)).

- **No son importables**: la carpeta no tiene `__init__.py` y no está en `sys.path`.
- Se conservan **solo como referencia histórica**. Lo más probable es que no se puedan
  ejecutar tal cual: usan rutas `parents[N]` y estructuras antiguas de `work/` que ya no existen.
- Está excluida de ruff/black, de pytest (`testpaths = tests`) y de `unittest discover`.
- Se han movido con `git mv` sin tocar su contenido, así que el historial sigue con `git log --follow`.

Antes de rescatar cualquier idea de aquí, lee [`docs/FURIGANA_LECCIONES.md`](../../docs/FURIGANA_LECCIONES.md).

## Scripts archivados

| Script | Motivo | Sustituto o dónde vive ahora |
|---|---|---|
| `pkb_scan.py` | Diagnóstico sin importadores. Su premisa (texto en bytecode sin LZ10) es errónea según EVENT_SCRIPT_FORMAT.md. | `ie123kit.nucleo.eventos.packnum` |
| `reinsert_test.py` | Prueba de concepto de la etapa 7. Nadie la referencia. | `ie123kit.nucleo.texto.sjis_portador` / `_legado/reinsert.py` |
| `recompress_test.py` | Diagnóstico v9 con efectos al importar y rutas inexistentes (`work/fa_extract`). | Ninguno |
| `build_translation.py` | **PELIGROSO: no reutilizar.** Sobrescribe `translation/ie*/dialogo.csv` con emparejamiento por orden. | Emparejamiento por ID (`tools/audit_dialogo_ids.py`); ver [#36](https://github.com/luishidalgoa/inazuma-eleven-123-spanish/issues/36) |
| `str_align.py` | Emparejamiento por índice ingenuo (item.STR 300 frente a 603). NDS_FIX superada. | `ie123kit.nucleo.texto.nds_latin` |
| `nds_str_dump.py` | Volcado ASCII trivial de la fase 2 inicial. Sin importadores. | `nds_latin` + `tools/build_glossary.py` |
| `tr_prepare.py` | Flujo de lotes IA de 2026-06-14 ya terminado, con rutas rotas. | Validaciones de `ie123 textos importar` (fase 2): %NF fuera y conteo de `\f` |
| `tr_merge.py` | Mitad de fusión del mismo flujo. | Validación «solo rellenar pendiente o vacío» del importador de textos (fase 2) |
| `align_events.py` | Alineador por orden (Needleman-Wunsch), fallido. | Emparejamiento por ID; ver [#36](https://github.com/luishidalgoa/inazuma-eleven-123-spanish/issues/36). `dialogue_runs`/`is_furigana` siguen en la fachada `_legado` de pkb_unpack |
| `audit_ie1_voiced_text.py` | Sustituido por la auditoría por ID. Sin importadores. | `work/ie1/capas/v51/voces/auditoria.py`; regla documentada en `ie1/media/voces.py` |
| `verify_build.py` | Comprobaciones SAME_SIZE de la era v27. Sin llamadores. | `tools/verify_candidate.py` |
| `verify_v21.py` | Aserciones puntuales contra v21, que ya no existe. | `tools/verify_candidate.py` |
| `fix_ie1_title_logo.py` | Rehecho por capas posteriores; tenía una ruta fija a Downloads. | Capas v60/v62/v63 y `work/ie1/capas/v67/titulo_logo` |
| `compact_typography.py` | Experimentos v4/v8 superados por el bloqueo v20. | Bloqueo tipográfico v20 (`tools/dialogue_lock.py`, `AGENTS.md`) |
| `build_match_content_patch.py` | Produjo mch v23-v27. | `work/ie1/capas/v33/mch_story` y `work/ie1/capas/v55/pachangas`; invariantes a `ie1/texto/mch.py` (fase 2) |
| `build_mch_patch.py` | Variante solo Royal (v21), contenida en la anterior. | `work/ie1/capas/v33/mch_story` y `work/ie1/capas/v55/pachangas` |
| `build_3ds.py` | Constructor in situ de la etapa 8 (parches v1-v9). | `work/ie1/capas/v33/_final/build_rom.py` + `tools/build_ui_revision.py` + `tools/verify_candidate.py` |
| `build_3ds_var.py` | **PELIGROSO: no reutilizar.** Sin SKIP_CRO/NO_CODE_PATCH aplica parches fallidos. | `work/ie1/capas/v33/_final/build_rom.py` + `tools/build_ui_revision.py` + `tools/verify_candidate.py` |
| `build_fontui.py` | **PELIGROSO: no reutilizar.** Diagnóstico v7 con efectos al importar; pasa FONT12T por el editor 4bpp incompatible. | Bloqueo tipográfico v20 (`tools/font_patch.py`, `tools/dialogue_lock.py`) |
| `ui_insert.py` | **PELIGROSO: no reutilizar.** Escribía unitbase +0 en ASCII sin NUL. | Regla +16/NUL: [#16](https://github.com/luishidalgoa/inazuma-eleven-123-spanish/issues/16), `work/ie1/capas/v36/nombres` |
| `probe_ie1_spacing.py` | Experimento v18 retirado; sus fuentes chocan con el bloqueo v20. | Bloqueo tipográfico v20 (`tools/dialogue_lock.py`, `AGENTS.md`) |
| `build_ie1_movies.py` | Sustituido: las 21 películas de v66/v67 son idénticas a su `extra/`. | `work/ie1/capas/v58/cinematicas/build.py` |
| `reorganizar_proyecto.py` | Migración del 2026-09-16 ya aplicada. | Ninguno (la migración a juego_principal será una acción aparte que copia) |
| `tests/test_compact_typography.py` | Prueba un módulo archivado; ya se saltaba por faltar `work/fa_extract`. | Ninguno |
| `tests/test_validate_inputs.py` | Prueba `validate.py`, que queda en cuarentena. | `ie123kit/_legado/validate.py` (F1.4) |

Issues relacionados: [#9](https://github.com/luishidalgoa/inazuma-eleven-123-spanish/issues/9),
[#16](https://github.com/luishidalgoa/inazuma-eleven-123-spanish/issues/16),
[#36](https://github.com/luishidalgoa/inazuma-eleven-123-spanish/issues/36).

## Pendientes de archivo en F1.4

- `tools/patch_code.py`
- `tools/patch_cro.py`

Siguen en `tools/` porque `tools/patch_exefs.py` (activo; se divide en F1.4) hace
`import patch_code` a nivel de módulo, y `patch_code` importa `patch_cro`. Moverlos ahora
rompería `import patch_exefs`. Se archivarán en F1.4 junto con la ruta code.bin/exheader de
`patch_exefs.py`.

Ambos son **obsolete_dangerous** según [`FURIGANA_LECCIONES.md`](../../docs/FURIGANA_LECCIONES.md):

- `patch_code.py`: saltos a cuevas de la CRO imposibles (crash en 0xAD9E38). Regla vigente: `NO_CODE_PATCH=1`.
- `patch_cro.py`: la cueva 0x50E14 es zona de reubicación (crash en 0xAD9E1C). Regla vigente: `SKIP_CRO=1`.

## Nota

No se crean stubs en `tools/` para estos nombres. En la fase 2, `ie123 compat equivalencias`
indicará la orden sustituta de cada script retirado.
