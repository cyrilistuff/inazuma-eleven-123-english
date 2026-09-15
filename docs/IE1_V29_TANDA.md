# Tanda v29 — descripciones de jugadores, pantalla VS y equipos

Issue: #21 (derivado: #22). Base: candidata v28 instalada (`19a23738…a483a`).
Tipografía v20 bloqueada: `tools/dialogue_lock.py` pasa en todos los pasos; no
se modifican caja, fuentes, codificación ni algoritmo de saltos.

## Petición del usuario

Traducir las descripciones de los jugadores, la pantalla VS al empezar un
partido y los nombres de equipos como la Royal Academy. Integrar además lo que
la sesión anterior dejó preparado y sin instalar.

## Contenido

1. **Lote `work/ui_followup` (sesión anterior)**: Continuar al reanudar el
   partido, PT en la animación de supertécnica, pestañas Equipo/Reservas, botón
   Datos, confirmaciones de fichaje y etiquetas NV/PE/PT. 8 texturas en 3 archivos.
2. **Descripciones de perfil** (`logic/unitbase.STR`): las 1.040 descripciones,
   cada una en su hueco original. Puntero `u16@+94 × 32` en `unitbase.dat`
   (ver `FORMATOS.md`). Se respeta la forma original de dos líneas con la métrica
   aprobada (avance 11, 220 px) y la capacidad en bytes del hueco.
3. **Pantalla VS**: 16 placas grandes de escuela (`vs_school_name`), 18 placas
   pequeñas (`pk_school_name`, incluidas las variantes resaltadas) y 13 rótulos de
   campo (`vs_stage_select`). Solo cambian los rectángulos declarados; el panel
   naranja y la banda se restauran con sus colores planos medidos en los 13 banners.
4. **Nombres oficiales de equipo**: `team.pkb` pasa de «Brainwashing», «Alpine»,
   «Inazuma KFC» y «Cloister Divinity» a **Brain, Farm, Inazuma Kids FC y
   Kasamino** (los tres primeros confirmados en el diálogo oficial NDS). El mismo
   cambio se aplica a 9 diálogos ya traducidos que usaban esos nombres
   (81000040, 81000080, 90000000, 92020700, 97000004), a `reviewed.json`,
   a `dialogo.csv` y a `tools/build_match_content_patch.py`.
5. **PE/PT**: 2 diálogos de recuperación (63000380, 63000450) y 6 literales del
   CRO del uso de objetos: recuperación de PE, de PT y de ambos, «No se puede
   usar», «No se puede usar más» y «¿Lo tiras?».

Terminología: イナビカリ = Centella (diálogo oficial), ＯＢ = Veteranos, ウラゼウス =
Zeus oscuro, 秘密の倉庫 = Almacén secreto, 商店街 = Solar del barrio (como v28).

## Fuera de esta tanda

- Objetos (`item.STR`/`item.dat`) y menú de entrenamiento Centella del CRO: #22.
- Menú principal, etiquetas dinámicas de guardado, NPC «Andy y la chica» y
  rótulos de supertécnicas: siguen como en `REVISION_UI_IE1_2026-09-10.md`.

## Reproducción (recursos locales en `work/`, no publicar)

```text
python work/ui_followup/prepare.py
python tools/translate_ui_textures.py work/ui_followup/manifest.json --source work/menu_audit --base work/ui_followup/base --output work/ui_followup/extra --previews work/ui_followup/previews
python work/ui_followup/validate.py
python work/vs_revision/prepare.py
python tools/translate_ui_textures.py work/vs_revision/manifest.json --source work/vs_revision/base --base work/vs_revision/base --output work/vs_revision/extra --previews work/vs_revision/previews
python work/vs_revision/teams.py
python work/vs_revision/validate.py
python work/vs_revision/events.py
python work/vs_revision/literals.py
python work/desc_revision/check_desc.py work/desc_revision/chunk_0*.json
python work/desc_revision/apply.py
python tools/build_ui_revision.py --base work/probe_ie1_v28/archive.fa --ui work/vs_revision --extra work/ui_followup/extra --extra work/vs_revision/extra --extra work/desc_revision/extra --cro work/vs_revision/romfs/cro/ina_main1.cro --output work/probe_ie1_v29/archive.fa
python work/vs_revision/install.py work/probe_ie1_v29
```

## Estado

2026-09-11: candidata `work/probe_ie1_v29/archive.fa` generada e **instalada** en
Azahar (mod `00040000000BB800`), con Azahar cerrado y sin enviar entradas al emulador.

- `archive.fa` candidato e instalado: `cbada7a494f1b392dd7f9260830d208986583fef8c10e3c8a68a49fa89eaf465`
- `ina_main1.cro` candidato e instalado: `4a73fb4930733c07cdda0b678a4baca9e5d8e13ece3654104cfffbee6fda9e19`
- Verificación estática (`work/vs_revision/verify_v29.py`): 52 entradas iguales a
  sus capas; el resto del archivo, incluidas las 22 fuentes, idéntico a v28; solo
  cambian los 7 eventos preparados (1.286 idénticos tras descomprimir); el CRO solo
  difiere en los 6 literales; bloqueo tipográfico PASS.
- Descripciones: 1.040/1.040 validadas, máximo 2 líneas, ningún byte fuera de sus huecos.
- Limpieza: se borró `work/probe_ie1_v27/archive.fa` (conservando sus informes);
  v28 se mantiene porque es la base reproducible de v29.

**No está verificada en juego.** Prueba sugerida para el usuario: ficha de un
jugador (Mark, Axel, un jugador del Brain), inicio de un partido/pachanga para
ver las placas y el campo en la pantalla VS, uso de un objeto de recuperación,
reanudar un partido (Continuar) y la pantalla de fichajes. Si las descripciones
admiten una tercera línea sin cortes, se podrían ampliar en una tanda posterior.
