# Guía de continuidad del proyecto IE1

Este documento describe el flujo que ha seguido Astra para que otro modelo pueda
retomar el trabajo sin confundir una candidata local con una build verificada.
La fuente de verdad son los scripts, los manifiestos de `work/` y el protocolo
de QA; las capturas del chat sirven como evidencia visual, pero no sustituyen la
prueba en Azahar.

## Objetivo y límites

El objetivo actual es traducir al español de España **Inazuma Eleven 1** de la
recopilación 3DS japonesa. Se usan los nombres oficiales europeos del glosario
(`Mark Evans`, `Axel Blaze`, `Raimon`, etc.). No se distribuyen ROMs, extracciones,
logs ni recursos oficiales recuperados: todo lo que procede de una ROM permanece
local en `work/`, que está ignorado por Git.

La candidata v7 es experimental. Amplía la traducción de historia y NPC hasta
el tramo previo al partido contra la Royal, pero **no demuestra que todo el
capítulo 1 esté terminado**. La validación offline del archivo no equivale a una
prueba jugable.

## Estructura de trabajo local

- `tools/`: scripts de extracción, análisis, edición y construcción.
- `translation/glossary/`: nombres y términos oficiales.
- `docs/`: formatos, decisiones, incidencias y protocolo de pruebas.
- `work/`: ROM extraída, cachés, manifiestos, previews y builds locales; no se
  versiona.
- `work/archive_entries.json`: índice cacheado del `archive.fa`; permite buscar
  sin cargar repetidamente el archivo completo.
- `work/probe_ie1_v7_inputs/`: entradas de la candidata v7: `reviewed.json`,
  `ui.json`, `items.json`, `keyboard.json`, `extra/` y vistas previas.
- `work/probe_ie1_v7/archive.fa`: candidata v7 construida.

Antes de modificar texto hay que leer `CLAUDE.md`,
`docs/PROTOCOLO_QA_IE1.md` y `docs/SSD_REGISTROS_IE1.md`. También hay que revisar
`docs/FURIGANA_LECCIONES.md` para no repetir enfoques ya rechazados.

## Flujo que se debe seguir

1. Trabajar siempre sobre una copia o un directorio de candidata, conservando el
   original y anotando sus hashes. No editar directamente la ROM original.
2. Localizar el recurso mediante el índice de `archive.fa` y extraer solo el
   fragmento necesario. Para SSD usar `tools/ssd_records.py`; no tratar el texto
   como cadenas separadas por NUL: cada registro lleva un tamaño inline.
3. Preparar traducciones revisadas con hash del texto original. Una sustitución
   debe comprobar que sigue editando exactamente la cadena esperada, conservar
   instrucciones, índices, controles y argumentos, y rechazar el texto si no cabe.
4. Para gráficos CTPK/ARCV/SSZL usar `tools/ui_archive.py`, `tools/ctpk_ui.py` y
   `tools/translate_ui_textures.py`. Mantener dimensiones, formato, metadatos y
   tamaño de entradas. Crear una preview y revisarla antes de empaquetar.
5. Para tablas binarias usar los scripts de `tools/ie1_tables.py`: modificar solo
   campos conocidos y comprobar que estadísticas, punteros y bytes no relacionados
   permanecen iguales. Los nombres largos que no caben se dejan pendientes.
6. Ejecutar los fixtures y validaciones, construir una candidata nueva y guardar
   su informe de hashes. No llamar “estable” a una build que solo pasó validadores.
7. Con Azahar cerrado, conservar la candidata instalada anterior y activar la
   nueva como mod LayeredFS. Registrar archivo, hash, emulador y configuración.
8. El usuario juega y controla el emulador; el modelo observa capturas y logs y
   no envía entradas durante la prueba. Seguir exactamente el protocolo hasta la
   primera pachanga: ante el primer fallo, detenerse, corregir y repetir la misma
   reproducción antes de continuar.

## Construcción de la candidata v7

La orden reproducible usada fue:

```text
python tools/build_ie1_probe.py --events 92010100 92010200 92010250 92010300 92010340 92010400 92010500 81000040 91010000 92010510 92104100 92104200 83000040 --fullwidth --reviewed-json work/probe_ie1_v7_inputs/reviewed.json --extra-files work/probe_ie1_v7_inputs/extra --output work/probe_ie1_v7/archive.fa
```

La v7 instalada tiene SHA-256
`9d1a80d9cada5c39179356042b5a4f84268617591157373629b8d1776f78e26c`. La copia
anterior está en `work/probe_ie1_v7/previous-installed.fa`. La build incluye
menús, guardado, teclado latino, botones de partido, logos, pantallas iniciales,
lugares, objetivos, 1.132 nombres cortos, 28 objetos y los eventos indicados en
la orden. Los vídeos no se modifican.

Para comprobar una instalación local:

```text
Get-Process -Name azahar -ErrorAction SilentlyContinue
Get-FileHash work/probe_ie1_v7/archive.fa -Algorithm SHA256
```

No sustituir una build instalada mientras Azahar esté abierto. El enlace de mods
actual está en `...\\Azahar\\load\\mods\\00040000000BB800\\romfs\\archive.fa`;
la ruta exacta puede variar según la instalación del usuario.

## Qué queda pendiente

- Probar v7 desde partida nueva hasta la primera pachanga y registrar cada NPC.
- Completar eventos y NPC restantes del capítulo 1 después de superar esa prueba.
- Localizar y traducir cadenas dinámicas que todavía puedan aparecer en ranuras,
  nombres, equipamiento o pantallas no cubiertas por las texturas sustituidas.
- Revisar nombres largos omitidos, más descripciones de objetos y cualquier crash
  de NPC de evento con modal. Los eventos protegidos por modales no se traducen a
  ciegas: primero se reproduce y se entiende su cierre.
- No cambiar el ejecutable/CRO ni los vídeos sin evidencia y una prueba específica.

## Diagnóstico y documentación

Los fallos nuevos se anotan en `docs/QA_IE1_INCIDENCIAS.md` con build, escena,
evento, acciones, resultado esperado, captura y log. Las limitaciones de formato
van en `docs/SSD_REGISTROS_IE1.md` o `docs/FORMATOS.md`; no se esconden en el chat.
Antes de publicar cualquier parche, verificar que `git ls-files` no incluye ROMs,
`work/`, logs, archivos extraídos ni logos oficiales locales.
