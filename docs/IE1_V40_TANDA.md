# Tanda v40 — rótulos del minimapa, barras 1P/2P y mensajes (issue #37)

Base: candidata v39 (`f0aba68f…00fdf870`). Capa: `work/v40/rotulos_1p2p` (apply + validate).

## 1. Rótulo de lugar del minimapa (eve.pkb, 0x4037 argumento 3)

Inventario de los 170 rótulos medidos con los avances de `FONT12.NFTR`. El japonés más ancho mide
117 px, que se toma como hueco disponible. 7 registros lo superaban: la tanda de diálogos v36 los
emparejó con frases NDS largas. Vuelven a un nombre corto coherente con el resto de rótulos:

| Japonés | Antes (px) | Ahora (px) | Eventos |
|---|---|---|---|
| 帝国学園　通路 | Pasillo de la Royal (183) | Pasillo (71) | 92041450 |
| 帝国学園　正面 | Entrada de la Royal (182) | Entrada (70) | 92031395, 92060100 |
| 河川敷グラウンド | Campo de la ribera (172) | Campo río (78) | 92020950 |
| サッカー部室 | Caseta del club (144) | Caseta club (107) | 92030900, 92081300 |
| 鉄塔 | Torre Inazuma (128) | Torre (50) | 92010600 |

Tras el cambio, el rótulo más ancho mide 107 px. Detalle en `work/v40/rotulos_1p2p/rotulos.json`.

## 2. Barras de equipo de la intro (3ddemo_school)

En el original, `ts001l` = 雷門 (azul), `lp1` = 1P (azul), `lp2` = 1P (roja), `rp1` = 2P (azul),
`rp2` = 2P (roja). La traducción anterior puso «Raimon» en las cuatro de 1P/2P y cortaba la barra en
x=22. Se reconstruye la barra desde el original y se pinta Raimon / 1P / 2P; `parts · ghost01` igual
que `ts001l`.

## 3. Mensajes

`field_message_b · win_p01`: borrado el trazo suelto de トピックス junto a «Noticias».
`gmap_b · name01` ya estaba en español (Zona comercial, Ribera…): sin cambios.

## Candidata

- validate PASS (7 texturas en 7 .arc); verify: 7 reemplazos, 7 eventos declarados, 22 fuentes
  idénticas, CRO idéntico, bloqueo PASS.
- `archive.fa`: `e9c2f5a75f2010fe9f1005433917c8feea318e594b5681e42122f38ddc7667ab`
- 2026-09-15: instalada en Azahar; 70 SAD intactos. Pendiente prueba en juego.
