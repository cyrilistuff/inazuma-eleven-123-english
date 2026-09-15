# Tanda v39 — nombres de escuela y pictogramas del mando (issue #37)

Base: candidata v38 (`bac2944c…c287b962`). Capa: `work/v39/escudos_pictogramas` (apply + validate).

| Pantalla · textura | Antes | Ahora | Origen |
|---|---|---|---|
| Intro de partido · 3ddemo_school ts001r–ts015r, ts020r, ts042r (17) | barra roja con 帝国, 尾刈斗, 野生… (ts001r: «Raimon» sobre un resto de 帝) | barra limpia con el nombre europeo oficial (Royal Academy, Occult, Wild, Brain, Otaku, Shuriken, Farm, Kirkwood, Zeus, Inazuma Kids FC, Umbrella, Sallys, Veteranos, Centella, Raimon, Ultra Zeus) | `translation/glossary/equipos.csv` |
| Mando de técnicas · top_plt_b01/b02 | pictogramas 風 林 山 火 | iconos de afinidad aire, bosque, montaña, fuego | NDS `menu_special_comand/HWD_I03` |
| Mando de técnicas · tec_button_b01 | botón 戻 (rojo y gris) y rayas rojas bajo el icono | flecha de volver (de `command_return_b01`); rayas borradas | 3DS |

Se quedan: `ts001l`, `ghost01` (artefactos de prioridad baja), `ts001lp1/lp2/rp1/rp2` (1P/2P,
contenido dudoso), técnicas `bc023/bc043`, `field_message_b`, `gmap_b` y los píxeles de
`common`/`result`.

- validate PASS (20 texturas en 18 .arc); verify: 18 reemplazos, 22 fuentes idénticas, 0 eventos,
  CRO idéntico, bloqueo PASS.
- `archive.fa`: `f0aba68f76b88bb9c6871388b5786c04ba3640db22ddbee69f91036d00fdf870`
- 2026-09-15: instalada en Azahar; 70 SAD intactos. Pendiente prueba en juego.
