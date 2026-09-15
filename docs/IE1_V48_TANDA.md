# Tanda v48 — pestaña «Equipo» y nombres de objeto (issues #37, #39)

Base: candidata v46 (`81137775…`; incluye v45 nombres principales y títulos cortos). Capa: `work/ie1/capas/v48/pestanas`.
La prueba v47 (latín de 1 byte en objetos) se descartó y no forma parte de esta candidata.

## 1. Pestaña «◀L Equipo» (formation_b · form_mes_b01)

El juego coloca estas piezas pegadas a la pestaña. «Equipo» (そうび, rect 0–56) iba de x11 a x45 y se salía;
el japonés ocupaba x1–31. Ahora «Equipo» va en x1 con 30 px de ancho; «Intercambiar» y «Formación» también a la
izquierda y sin superar el ancho del japonés.

## 2. Nombres de objeto (item.dat, máx. 9 caracteres)

Criterio (`work/ie1/capas/v47/objetos/propuesta.py`, tabla en `propuesta.md`):
1. Oficial NDS si cabe; si no, sin conectores.
2. Sin la palabra del tipo cuando el icono ya lo indica y el nombre no choca con otro objeto
   («Popular», «Chillona», «Caseta», «PE bronce», «Malditas»).
3. Si choca, inicial del tipo («B.salvaje», «G.juvenil»).
4. Técnicas, tácticas y equipaciones con nombre compuesto se quedan como estaban (quitar palabras
   cambiaba el sentido: «Mega», «Súper»).

82 nombres cambian; 144 se quedan. «Kung-fu» se queda como «Kung fu» (el guion de ancho completo no existe
en Shift-JIS).

- verify: 2 reemplazos (`formation_b.arc`, `item.dat`), 22 fuentes idénticas, bloqueo PASS.
- `archive.fa`: `4403d601…` · 2026-09-15 instalada, 70 SAD intactos. Pendiente prueba en juego.
