# QA estática v27: diálogos IE1, pachangas y NPC

La candidata `work/probe_ie1_v27/archive.fa` está instalada en Azahar.

- `eve.pkb`: 19.039 textos insertados en 982 eventos; 0 rechazos de longitud.
- Auditoría directa de `0x301d`, argumento 1: 18.806 diálogos visibles y 0 caracteres japoneses, incluidos 9202–9209, 9210 y las 82 zonas 8100 de Raimon.
- `mch.pkb`: 197 eventos de Royal, pachangas y cadena; 1.422 registros visibles sin japonés.
- `team.pkb`: 158 nombres de equipo traducidos sin desbordar los campos fijos.
- `teamtitle.dat`: 20 títulos revisados; la ranura de metadatos no textual se conserva.
- `clubinfo.dat`: 32 categorías de clubes traducidas.
- Caja, fuentes, espaciado, fullwidth y algoritmo de saltos aprobados de v20 intactos.

Hash SHA-256 de candidata e instalación:
`91f816060775190e994f585fae5e09c8adab4cc1998b059f250372387ab10369`.

La validación sigue siendo estática. Falta el recorrido jugable del usuario desde una partida nueva para comprobar escenas, NPC, una pachanga, la cadena y la Royal sin mezclar estados de builds anteriores.
