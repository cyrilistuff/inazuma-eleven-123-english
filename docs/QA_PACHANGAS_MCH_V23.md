# QA estática de pachangas y cadena de partidos en v23

La candidata `work/shared/candidatas/probe_ie1_v23/archive.fa` incluye los textos de partido del
paquete `inazuma1/data_iz/script/mch.pkb` y sus índices `mch.pkh`.

- 183 eventos `9420xxxx` modificados, incluidos los ocho eventos de la cadena
  (`94200251`–`94200258`) y las pachangas de los clubes; se conserva además el
  evento `94001500` de la Royal.
- 1.422 registros visibles de partido traducidos; la auditoría no encuentra
  japonés en esos registros.
- El evento `94001500` de la Royal conserva sus 143 registros traducidos y se
  vuelve a incluir en la misma candidata.
- `team.pkb`: 158 nombres fijos traducidos, sin desbordar el campo de 32 bytes.
- `teamtitle.dat`: 20 títulos de equipo traducidos, respetando sus ranuras de
  16 bytes.
- `clubinfo.dat`: 32 categorías del selector de pachangas traducidas, incluidos
  los clubes deportivos y las entradas numeradas.
- Las instrucciones y el número de registros SSD de los eventos modificados
  permanecen intactos. Las fuentes aprobadas y la caja de diálogo de v20 no se
  tocaron.
- Hash SHA-256 de `archive.fa` y de la copia instalada en Azahar:
  `bf1e194564170d86cffcf3acfa70409420584ca048b699253611011e35614393`.

La validación es estática. Para cerrar el QA hay que reiniciar Azahar, cargar un
estado creado con v23 y recorrer una pachanga de club, varios partidos de la
cadena y el partido de la Royal. El registro de esa prueba debe observarse sin
mezclar estados rápidos de builds anteriores.
