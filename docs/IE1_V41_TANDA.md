# Tanda v41 — teclado de nombre alineado con la rejilla (38)

Base: candidata v40 (`e9c2f5a7…dc7667ab`). Capa: `work/ie1/capas/v41/teclado`.

**Síntoma:** en el teclado de nombre y al crear partida, el cursor no cae sobre la letra o queda entre dos,
y en las filas bajas se escribe otra letra.

**Causa:** `tools/ie1_keyboard.texture_operations` pintaba las 6 filas cada 16 px (y 0..96). La rejilla de
selección del juego es la del teclado japonés original: celdas de 20×20 px (fila k en y 20k, columna c en
x 20c, controles en x 200..224). Medido en `font_hira01/kana01` originales: filas en y 3–17, 23–37,
44–57, 63–77, 84–97 y 104–117.

**Arreglo:** se parte de la textura original y cada letra de `ROWS` se pinta centrada en su celda de
20 px. «abc/ABC» va en la celda de «カナ» y la flecha de borrar se añade también en minúsculas (la tecla
existe en `fcode1`). `fcode0/1/2` no cambian.

- validate PASS; verify: 1 reemplazo (`name_b.arc`), 22 fuentes idénticas, 0 eventos, CRO idéntico, bloqueo PASS.
- `archive.fa`: `47f36ea8…` · 2026-09-15 instalada en Azahar, 70 SAD intactos. Pendiente prueba en juego.
- `tools/ie1_keyboard.texture_operations` corregida al paso de 20 px.
