# QA estática v26: pachangas, cadena y diálogos IE1

La candidata `work/probe_ie1_v26/archive.fa` está instalada en Azahar y sustituye a las candidatas intermedias.

- `mch.pkb`: 197 eventos de Royal, pachangas y cadena; 1.422 registros visibles traducidos y sin japonés.
- `team.pkb`: 158 nombres de equipo traducidos, sin desbordar los campos fijos de 32 bytes.
- `teamtitle.dat`: 20 títulos de equipo revisados en sus ranuras de 16 bytes; la ranura de metadatos no textual se conserva.
- `clubinfo.dat`: 32 categorías del selector de pachangas traducidas.
- `eve.pkb`: 19.036 textos insertados en los eventos seleccionados; los nueve bloques 9202–9209 y las zonas 8100 no dejan japonés visible.
- Los 27 registros que excedían el límite en la revisión anterior se redujeron con traducciones equivalentes; el informe v26 queda con **0 rechazos**. Los 106 faltantes son registros vacíos o marcadores sin texto visible.
- Las instrucciones SSD, la caja, el espaciado, las fuentes y el algoritmo de saltos aprobados de v20 permanecen intactos.

Hash SHA-256 de la candidata y de la copia instalada en Azahar:
`394b3ea3f986204a5ed7bb9d8fb2a349333d6b15490736cf16f259ca1dcfa27f`.

La validación es estática. Falta la prueba guiada del usuario desde una partida nueva: recorrer una pachanga de club, varios partidos de la cadena, la Royal y los diálogos de capítulo 2. No se han enviado entradas al emulador.
