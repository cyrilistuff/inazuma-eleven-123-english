# IE1 v35: cinemáticas europeas completas y logo integrado

## Fallos reproducidos en v34

- El opening conservaba el vídeo japonés aunque su audio ya era español.
- Las demás cinemáticas seguían usando imagen y subtítulos japoneses.
- am0102 aparecía girada porque el MOFLEX generado declaraba layout 0x06;
  los archivos retail de IE1 declaran 0x16.
- El título latino eran dos rótulos rectos sobre el balón y el rayo originales,
  por lo que parecía una pegatina.

## Corrección aplicada

- Se convirtieron las 21 películas .mods de la ROM española de IE1 DS.
- Las 21 pistas movie/txt/sp/*.dat se interpretan como intervalos de
  fotogramas y se incrustan en blanco sobre la banda inferior de cada vídeo.
- Todos los descriptores de sincronía se corrigen a layout 0x16
  (Simple2D, ImageRotation 1).
- El wordmark europeo se aisló del recurso de referencia y se integró como una
  única capa transparente con el balón y el rayo animados existentes.
- No se modificaron diálogos, fuentes, caja, espaciado ni saltos.

## Evidencia local

- Candidata: work/shared/candidatas/probe_ie1_v35/archive.fa.
- SHA-256: bcee069a2263148617de7ace13f5c93e49f3a023e94058e8d437e6531f17df9e.
- 22 entradas del archivo verificadas byte por byte: 21 MOFLEX y title_t.arc.
- Las 21 películas se descodifican completas y todos sus descriptores usan
  0x16.
- Los 70 SADL europeos instalados continúan coincidiendo y descodificando.
- Ocho pruebas de bloqueo tipográfico/UI superadas.
- La copia instalada en Azahar coincide con la candidata v35.

## Prueba jugable pendiente

El usuario debe comprobar el opening y al menos una cinemática narrativa:
orientación horizontal, subtítulos españoles, sincronía y ausencia de cortes.
También debe revisar el logo final del título. El agente observa pantallas y
registro sin enviar controles, conforme a docs/PROTOCOLO_QA_IE1.md.
