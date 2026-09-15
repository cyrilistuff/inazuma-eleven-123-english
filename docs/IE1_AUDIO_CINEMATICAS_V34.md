# IE1 v34: audio europeo y cinemática localizada

## Alcance

La candidata v34 conserva íntegramente la traducción y la tipografía aprobada de
v33. Solo añade medios europeos de la ROM española de Inazuma Eleven 1 para DS.
No modifica los diálogos, las fuentes ni sus saltos de línea.

## Inventario comprobado

- ROM NDS ES: código `YEES`, SHA-256
  `f3978af50a1697bf756ea6107ab7b9be1007591644365426ab3954d5360f0186`.
- La carpeta regional `data_iz/sound/sp` contiene 72 archivos SADL.
- 70 nombres coinciden exactamente con los 70 SADL de IE1 en la RomFS 3DS.
- `J18.SAD` y `J19.SAD` solo existen en DS y no se instalan porque no tienen una
  entrada equivalente en IE1 3DS.
- La ROM DS contiene 21 vídeos `.mods`; 20 son comunes y solo `movie/sp/am0102.mods`
  es una variante visual española específica.
- La recopilación 3DS contiene los mismos 21 identificadores como `.moflex`.

Los SADL conservan el mismo formato en ambas plataformas. La frecuencia y los
canales se describen en su propia cabecera; por ejemplo, la escena `am0101.SAD`
europea es estéreo a 32728 Hz y la japonesa de 3DS es estéreo a 16364 Hz. Por eso
se sobreponen los archivos europeos completos, sin recodificarlos.

## Preparación reproducible

> Nota (F1.4, #45): `python tools/ie1_media.py --stage` pasó a
> `python -m ie123kit.ie1.media.voces --stage`. El stage legacy de v34 que se describe aquí es histórico.

```powershell
python tools/ie1_media.py --stage
pwsh -File tools/setup_mobipeg.ps1
python tools/mods_to_moflex.py `
  "work/ie1/fuentes/nds_es/data_iz/movie/sp/am0102.mods" `
  "work/ie1/legacy/volumen_1/ie1_media_mod/archive_extra/inazuma1/data_iz/movie/am0102.moflex"
python tools/build_ui_revision.py `
  --base work/shared/candidatas/probe_ie1_v33/archive.fa `
  --ui work/ie1/legacy/volumen_1/ie1_media_mod `
  --extra work/ie1/legacy/volumen_1/ie1_media_mod/archive_extra `
  --cro work/shared/candidatas/probe_ie1_v33/romfs/cro/ina_main1.cro `
  --output work/shared/candidatas/probe_ie1_v34/archive.fa
```

`mods_to_moflex.py` convierte YCgCo de DS a YCbCr y gira 256x192 a 240x320,
que es la orientación almacenada por las cinemáticas de IE1 3DS. La compilación
x64 de mobipeg v2.1 falla en Windows con vídeo complejo; la x86 del mismo
lanzamiento convierte y descodifica correctamente.

## Resultado local

- `archive.fa` v34: SHA-256
  `64d234ffe37bb08f70405f20389a573b4ec18d9ea1a9642b2d2b30124528e476`.
- `am0102.moflex`: 361 fotogramas, 240x320, 24 fps, SHA-256
  `b6377f27f8f0b19bb3f7ed3d92b9353be614029d8f6c52c83b860a5a374edea0`.
- Los 70 SADL instalados coinciden byte por byte con la extracción europea.
- Los 70 SADL instalados se descodifican completos con vgmstream, sin errores.
- La copia de `archive.fa` instalada en Azahar coincide con la candidata v34.
- Azahar arrancó después de la instalación, registró los 70 SADL como reemplazos
  LayeredFS y llegó a la pantalla de partidas sin bloqueo. En una segunda
  observación alcanzó una conversación jugable con Silvia y Mark sin errores
  nuevos de audio, vídeo o sistema de archivos en el registro.
- Validación offline: descodificación secuencial completa del nuevo MOFLEX y ocho
  pruebas de bloqueo tipográfico/UI superadas.

La comprobación auditiva del opening y las voces cortas, junto con la reproducción
completa de `am0102`, queda pendiente con el usuario al mando de Azahar, siguiendo
`docs/PROTOCOLO_QA_IE1.md`. El arranque y el avance normal por una conversación no
demuestran por sí solos que esos tres medios concretos se hayan reproducido.
