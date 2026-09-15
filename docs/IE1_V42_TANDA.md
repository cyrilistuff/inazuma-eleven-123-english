# Tanda v42 — maquetación contra rectángulos QNA y literales de equipo (issue #37)

Base: candidata v41 (`47f36ea8…`). Capa: `work/ie1/capas/v42/maquetacion` (apply, cro, validate).
Auditoría nueva: `work/ie1/capas/v42/auditoria/celdas.py` (contenido traducido frente al original por rectángulo QNA).

## Causa de los recortes

Los gráficos se colocaban centrados en celdas de 16/32/64 px, pero el juego dibuja cada pieza con su
**rectángulo QNA**, que a menudo es más estrecho o está desplazado (Control 0–80, Valor 80–128;
en el entrenamiento Tiro 34 px, Defensa 36 px…). El japonés iba pegado a la izquierda (x+1) y el
número se pinta a continuación del ancho original.

## Cambios

| Textura | Antes | Ahora |
|---|---|---|
| status_t · st_mes01 | rótulos centrados, «Valor» cortado | a la izquierda de su rectángulo real |
| tokkun_b · res_b_mes01 | rótulos de 45–47 px en rectángulos de 34–46 px | a la izquierda y ajustados al ancho |
| status_t · mes01 | «Niv.», PE, PT centrados (hasta 28 px) | a la izquierda, máx. 21 px como «LV»; DL/MD/DF/PR a la izquierda |
| status_t · mes01 (0,52) | «TP» japonés | «PT» |
| binder_t · mes01 | «Raimon» cruzando dos celdas → «Rair non» | «Rai» y «mon», uno por celda, misma línea base |

## Literales del CRO (dentro del hueco alineado, relleno sin referencias)

| Offset | Hueco | Japonés | Español | Pantalla |
|---|---|---|---|---|
| 0x1447cc | 24 | チームレベル | Niv. Equipo | ventana de equipo (término NDS) |
| 0x144620 | 12 | なかま | Jug | ventana de equipo (3 caracteres, como el original) |
| 0x144630 | 8 | 人 | espacio | ventana de equipo (vacío pinta basura) |
| 0x14463c | 12 | 称号 | Rango | ventana de equipo («Título» no cabe en 5 letras) |
| 0x71df4 | 12 | なかま | Jug | caja de partida (3 caracteres, como el original) |
| 0x71e04 | 12 | 人 | espacio | caja de partida (vacío pinta basura) |

## Pendiente

- Capítulo de la caja de partida: 第 (4 B = 1 letra) + número de una tabla de kanji (一…十, 3 B) + 章 (8 B).
  «Capítulo 1» no cabe tal cual: decisión del usuario.
- Tablas del archivador/buscador (あ行…, 雷門 y equipos): punteros con relocación; se pueden
  reapuntar, pero requiere espacio libre en el CRO.
- «◀L Equipo» desbordado: pantalla sin identificar.
- Resto de avisos CORTE de `celdas.json` en texturas de tandas anteriores (gmap, entrenamiento
  Centella, conexión, uniforme, avisos de partido).

- validate PASS; verify: 3 reemplazos, 6 literales CRO declarados, 22 fuentes idénticas, bloqueo PASS.
- `archive.fa`: `c002ef54…` · CRO: `befb3961…` · 2026-09-15 instalados en Azahar (archive.fa y
  cro/ina_main1.cro), 70 SAD intactos. Pendiente prueba en juego.

## Corrección tras prueba (2026-09-15)

En la caja de partida «Jug.» se montaba con el número y el sufijo vacío pintaba «*&». El número se
pinta en una **posición fija** calculada para el japonés y un literal vacío no es válido. Ahora
«Jug» (3 caracteres, como なかま) y un espacio de ancho completo en lugar de 人. CRO `9b550e80…`.
