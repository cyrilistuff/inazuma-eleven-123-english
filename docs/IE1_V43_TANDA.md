# Tanda v43 — nombres de equipo cortos y botones del partido (issue #37)

Base: candidata v42 (`c002ef54…`, CRO `039fcf3b…`). Capas: `work/v43/equipos`, `work/v43/botones`. Candidata construida como `work/probe_ie1_v44` (`725bd025…`).

## 1. Nombres de equipo (`logic/team.pkb`)

El cuadro de equipo pinta el nombre con paso fijo. El japonés más largo mide 11 caracteres;
122 nombres oficiales NDS pasaban de ahí («Miserias del rugby», 18) y se salían del gráfico.
Se sustituyen por formas cortas de 11 caracteres o menos, derivadas del oficial
(`work/v43/equipos/cortos.json`, p. ej. «Miserias R.», «Sumo gordos», «Flechas C.», «Royal Acad.»).

## 2. Gráficos

| Textura | Antes | Ahora |
|---|---|---|
| game_command_select_b · tec_button_b01 | rayo con ruido sobre el kanji 必 y trazos rojos | cuadro limpio con rayo de pixel art (rojo / gris) |
| game_command_select_b · tec_plt_b01 | «TP» | «PT» |
| battle_member(_b) · point_plt_b01 | «Experiencia obtenida» tapado («Experiencia t») | «Experiencia», a la izquierda |
| status_t · mes01 | «Niv.» NDS pequeño, se veía mal | «NV» con la construcción y colores del «LV» original |
| binder_t · mes01 | «Rai» y «mon» centrados, muy separados | pegados hacia el centro |

- validate PASS; verify: 6 reemplazos, 22 fuentes idénticas, 0 eventos, CRO igual a v42, bloqueo PASS.
- Pendiente de instalar (Azahar abierto) y de prueba en juego.
- Sin localizar: botón de retroceder con imagen japonesa y «Puntos de técnica» recortado (piden captura).

## Ajustes tras la segunda prueba

- «NV» pegado arriba de su celda (el juego recorta la parte baja).
- «Fichero» (grande y pequeño) pegado al fondo de su celda, como el japonés.
- Archivador: el juego coloca las celdas 雷 y 門 a −40/+40 px (48 px de hueco). En el layout QNA de
  `binder_t` se acercan a −16/+16 las partes 6–9 y 111–114 (solo los campos X): «Raimon» queda unido.
  `validate.py` admite ese QNA declarado con el mismo tamaño.
- «Jugadores» no cabe: el búfer de なかま es de 3 caracteres.
