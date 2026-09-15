# Tanda v50 — equipos a 9 caracteres, capítulo y tienda (issue #37)

Base: candidata v49 (`38cee6a3…`). Capa: `work/ie1/capas/v50` (`apply.py`, `equipos9.json`, `cro_literals.json`).

1. **Equipos (`team.pkb`)**: el cuadro de pachanga sale pegado al borde de la pantalla y los nombres de
   11 caracteres se cortaban («Béisb. torp»). 118 nombres pasan a 9 caracteres o menos.
2. **Capítulo de la caja de partida (CRO)**: 第 y 章 pasan a espacio; la tabla de números del capítulo
   (punteros `0x2017a8..0x2017cc`: 十, 一…九) pasa a números romanos Ⅰ…Ⅹ, presentes en las fuentes.
   Se ve «Ⅲ» (opción 3 elegida por el usuario).
3. **Tienda (CRO)**: «かう»/«うる» → «C.»/«V.»; nombres de tienda de la tabla `0x1A336C` sin furigana:
   Tienda Raimon, Macro dep., Maqueta, Quiosco. Todos ≤ bytes del japonés.

- verify: 1 reemplazo (`team.pkb`), 18 literales CRO declarados, bloqueo PASS.
- Pendiente de instalar (Azahar abierto): copiar `archive.fa` y `cro/ina_main1.cro`.
- Sin localizar: lista «Normal / Atacar / Cubrir» con letras montadas.
