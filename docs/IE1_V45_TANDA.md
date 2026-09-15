# Tanda v45 — nombre principal de jugador (unitbase +0) (issue #35)

Base: candidata v44 (`725bd025…`). Capa: `work/ie1/capas/v45/nombre_ficha`.

**Síntoma:** en la ficha de Formación el nombre grande seguía como «Maxwell» o en japonés, mientras la
lista de la plantilla ya decía «Max».

**Causa:** `unitbase.dat` tiene tres nombres por registro: `+0` principal (ficha, formación), `+16` corto
(lista y recuadro del hablante) y `+32`/`+48` completo (línea pequeña de la ficha). La v36 solo corrigió
`+16`. `+0` seguía en japonés en unos 2.000 registros; solo el Raimon estaba en latino.

**Cambio:** `+0` = nombre corto oficial de `+16` en 1.933 registros cuyo `+16` ya es latino de ancho
completo. `+32`/`+48` no se tocan.

**Riesgo (issue #16):** el motor separa `+0` por el espacio de ancho completo 0x8140. El crash antiguo venía
de escribir ASCII sin terminar. Aquí va ancho completo con NUL, igual que los nombres del Raimon, que ya
eran estables. Probar hablando con varios NPC y abriendo fichas de rivales y fichajes.

- verify: 1 reemplazo (`unitbase.dat`), 22 fuentes idénticas, bloqueo PASS. `archive.fa` en `probe_ie1_v45`.
- Pendiente de instalar (Azahar abierto) y de prueba en juego.
