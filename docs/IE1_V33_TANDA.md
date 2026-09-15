# Tanda v33 — partidos de historia, rótulos, CRO, datos y texturas pendientes

Base: candidata v32 (`4043c5c9…8a7498a`). Programa de la auditoría de pendientes
(issues #25–#30). Cada línea se preparó en `work/v33/<línea>/` a partir de copias de
los archivos base (`work/v33/base/{orig,v32}`), con un implementador, una revisión
adversarial y hasta dos rondas de corrección. El mapa de propiedad
`work/v33/ownership.json` impide que dos líneas toquen el mismo archivo (403 archivos,
0 solapes). Tipografía v20 bloqueada: el bloqueo pasa en todas las líneas.

## Contenido

1. **Partidos de historia** (#25, `mch.pkh/pkb`, `work/v33/mch_story`): 4.628 registros
   de los eventos 9400xxxx (todos salvo 94001500, ya aprobado). Se alinearon con
   `script/sp/mcht.pkb` de la NDS española; con oficial de confianza alta se usa el
   oficial, y el resto se traduce del japonés con el estilo de `match_94001500.json`.
   Japonés visible restante en 9400xxxx: 0. Crecimiento máximo de un evento: ×1,14.
2. **Rótulos y objetivos** (#26, `eve.pkb`, `work/v33/eve_labels`): 336 registros en
   168 eventos: 61 rótulos de lugar (0x4037), 126 objetivos y 139 cabeceras de
   objetivo (0x402f) y 10 diálogos con argumento distinto de 1.
3. **Literales del CRO** (#27, `ina_main1.cro`, `work/v33/cro`): 155 textos visibles
   con referencia verificada en el código y 3 cambios especiales. G06: «%2F熱血ポイント»
   pasa a «Pasión» como texto base y el formato compartido añade un espacio
   («Pasión 30»). 131 literales no se tocan (claves de comparación, listas de longitud
   fija, lecturas de furigana, huérfanos); cada uno con su motivo en `literals.json`.
4. **Datos** (#28, `work/v33/data`): 36 títulos (`rpgtitle.STR`), 89 textos de
   Contactos (`JinmyakuData.dat` reconstruido), 44 nombres de campo (`fieldinf.dat`),
   17 nombres de `unitbase.dat` y corrección de acentos heredados de la tabla NDS
   antigua (0xD9 = É: «Épsilon») en `item.dat`, `item.STR`, `command.STR`, chunks y
   glosarios `objetos.csv`/`tecnicas.csv`.
5. **Mensajes del sistema** (#30, `message/jp/GameString.bin/.tbl`): 51 de 52 cadenas
   (arranque, guardado, errores, comunicación); la tabla del teclado se conserva.
6. **Menú común de la recopilación** (#30, `menu/*.arc`, `passing.arc`): 46 texturas y
   124 textos (errores de carga, Museo y Galería, conexión SD, StreetPass, Sí/No,
   Volver). `ina_menu.cro` se auditó (129 cadenas: títulos de galería y canciones) pero
   no se modifica: no caben traducciones seguras en sus bytes.
7. **Texturas** (#29):
   - Rótulos 3D de supertécnica: 126 (nombres oficiales, `condense` cuando no caben).
   - Placas de instituto: 54. Pantallas de partido: 62 textos en 31 texturas.
   - Menús: 48 textos (A) y 93 operaciones en 30 texturas (B), con «Tú/Rival».
   - Varias (campo, título, `pic2d`, minimapa, ending): 82 textos en 22 texturas y las
     4 texturas fantasma (G03), idénticas a su textura 001, con las mismas operaciones.
   - Fondos de historia: 221 textos en 30 texturas (resultados, tutoriales, cuadros de
     torneo, periódico). Se omiten 2 cartas/documentos ilegibles también en NDS.
   - Ayuda y tutoriales: 87 páginas (83 + 147 + 126 + 85 operaciones).
   - Créditos: 378 líneas en 30 texturas.
8. **Título del icono** (G13, `work/v33/smdh`): SMDH con título español preparado
   (variantes `es` y `es_en`); no forma parte de `archive.fa` y no se instala por
   defecto (ver `work/v33/smdh/report.json`).

Correcciones finales del coordinador (`work/v33/_final/patch_residual.py`): restos de
«らい» junto a «Kim» en la ayuda `ie01_tt52` y final de «画像をスライド» en
`ie99_content_mtl_bg_b02` (pie de la Galería). Por eso `validate.py` de `tex_help_3`
marca píxeles fuera de sus cajas en tt52: es el parche declarado.

## Pendiente

- **Auditoría de texturas ya cambiadas** (`work/v33/tex_residual/report.json`): 98
  elementos en 52 texturas (40 de japonés visible de prioridad alta). Próxima tanda.
- `ina_menu.cro`: títulos de galería y canciones (requiere reubicar cadenas).
- Vídeos con subtítulos incrustados (#31, bloqueado).
- Decisiones abiertas: logotipo «INAZUMA ELEVEN» rotulado (tex_menus_a); «Duelos»
  frente a «Pachangas» en la ayuda tt40; coherencia de 106 grupos de frases japonesas
  iguales con distinto español oficial entre partidos; abreviaturas de `fieldinf`
  (P., Ens./Ent., Est.); lectura «Hiroshi» de 弘 en los créditos.
- Comprobar en consola: ancho de Contactos y títulos RPG, paneles translúcidos
  repintados de la ayuda (tt81–tt84) y si `GameString` usa FONT12T (sus portadores de
  acentos no están parcheados en v32).

## Estado

2026-09-11: candidata `work/probe_ie1_v33/archive.fa` generada e **instalada** en
Azahar con Azahar cerrado y sin enviar entradas al emulador.

- `archive.fa` candidato e instalado: `b65cd7eacc170580b9b24c1da1921fe488b33ab44cd769679d28dc0b48285314`
- `ina_main1.cro` candidato e instalado: `44d4e206dffb4bd66841cf28a7ccc2b14c60c94e2772954464f63535bfe113a4`
- `tools/verify_candidate.py`: 400 entradas iguales a sus 16 capas; el resto del archivo
  y las 22 fuentes idénticos a v32; solo cambian los 168 eventos declarados; el CRO
  solo difiere en los 158 literales declarados; bloqueo tipográfico PASS.
- `build_ui_revision.py`: 168 eventos, 400 reemplazos, ninguna capa pisa a otra.
- Validación por línea (`work/v33/_final/validate.log`): PASS en todas. `tex_help_3`
  falla solo en tt52 por el parche declarado del coordinador (su validación previa
  al parche pasó con los mismos archivos).
- Limpieza: se borró `work/probe_ie1_v31/archive.fa`; v32 se conserva como base.

**No está verificada en juego.** Prueba sugerida: un partido de historia (p. ej. la
pachanga de la Occult o la Wild) con comentarista y diálogos, rótulos de lugar y
objetivos al entrar en zonas, pantalla de recompensas («Pasión 30»), Contactos,
títulos, menú de ayuda/tutorial, cinemáticas de supertécnica, menú principal de la
recopilación (Museo, Galería, conexión SD) y créditos finales si hay partida
avanzada.

## Reproducción

```text
python work/v33/mch_story/apply.py && python work/v33/mch_story/validate.py
python work/v33/eve_labels/validate.py
python work/v33/cro/validate.py
python work/v33/data/validate.py
python work/v33/gamestring/validate.py
python work/v33/ie99_menu/validate.py
python work/v33/<tex_*>/validate.py
python work/v33/_final/patch_residual.py
python tools/build_ui_revision.py --base work/probe_ie1_v32/archive.fa --ui work/v33/eve_labels --output work/probe_ie1_v33/archive.fa --extra work/v33/mch_story/extra --extra work/v33/data/extra --extra work/v33/gamestring/extra --extra work/v33/ie99_menu/extra --extra work/v33/tex_banners3d/extra --extra work/v33/tex_demo_bg/extra --extra work/v33/tex_game/extra --extra work/v33/tex_help_1/extra --extra work/v33/tex_help_2/extra --extra work/v33/tex_help_3/extra --extra work/v33/tex_help_4/extra --extra work/v33/tex_menus_a/extra --extra work/v33/tex_menus_b/extra --extra work/v33/tex_misc/extra --extra work/v33/tex_schools/extra --extra work/v33/tex_staffroll/extra --cro work/v33/cro/romfs/cro/ina_main1.cro
python tools/verify_candidate.py --base work/probe_ie1_v32 --candidate work/probe_ie1_v33 --events work/v33/eve_labels/events --literals work/v33/_final/cro_literals_v33.json --layer (las mismas 16 capas)
python work/vs_revision/install.py work/probe_ie1_v33
```
