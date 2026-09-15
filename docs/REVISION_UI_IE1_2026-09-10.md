# Revisión de interfaz — 10 de septiembre de 2026

Estado: **recursos preparados; no instalados ni comprobados en juego**.
La ROM/mod v27 instalada permanece sin cambios. Se mantiene la instrucción
local de `work/scope_no_build.md`: preparar las correcciones sin generar ROM.

## Cambios preparados

- 27 texturas en 16 archivos: posiciones POR/DEF/MED/DEL y botones de plantilla,
  iconos de afinidad, salida de partida, narraciones del Royal, badges de
  búsqueda/fichaje/objetivo, experiencia/pasión/amistad, nombres de equipos y
  escenarios de la presentación, opciones y confirmación del escudo/nombre.
- PE (resistencia) y PT (técnica) en barras de resultados, indicadores de duelo
  y etiquetas de estadísticas. Se conserva la variante reflejada del duelo.
- 23 nombres de formaciones en `item.dat`, dentro del campo de 19 bytes.
  Los nombres largos se abrevian explícitamente; no hay truncado automático.
- 8 cadenas del CRO: obtenido/cofre vacío/amistad, sin datos, nivel, horas,
  minutos y selección de partida. Solo se sustituyen literales identificados;
  no se alteran instrucciones, punteros ni longitud del archivo.
- 13 objetivos en cuatro eventos de reclutamiento: faltan 4/3/2 jugadores,
  hablar con Willy (último jugador) y volver a la caseta. Son textos visibles
  del opcode 0x402f, argumento 3; la clasificación previa como «ruby invisible»
  era incorrecta. Se conserva el argumento 2, que contiene la clave del aviso.
- «Reservas» en el sprite heredado `MSDN_BG03.PAC_` de `formation.SPL/SPD`.
  Compresión original: 4348 bytes; nueva: 4349; hueco existente: 4352.
  No crece ningún archivo ni cambia ningún otro sprite, color de paleta o
  píxel exterior al rótulo.
- 95 sustituciones de rótulos correspondientes a 45 mapas y sus variantes:
  zonas del Raimon, plantas, aulas, caseta, torre y entrada del Royal. Máximo
  de 10 caracteres, una sola línea, sin tocar la caja. La desaparición del
  rótulo de primera planta aún requiere comprobarse en juego.

## Corrección del trabajo anterior

Los recursos se basan en la candidata v27, conservando las traducciones ajenas
a cada recorte. No se reconstruye un archivo entero a partir de la versión
japonesa perdiendo sus otras traducciones.

El borrado por interpolación de colores no se utiliza en este lote. Los marcos
se conservan y se comprueba que la pintura no salga de los rectángulos. En ETC,
la validación distingue los píxeles vecinos del mismo bloque de compresión 4×4.
La geometría QNA y los demás recursos del archivo permanecen idénticos.

Se encontró una regresión en las entradas de preparación `extra_ascii`: faltaba
FONT12T.bcfnt y FONT12.bcfnt/FONT8.bcfnt no coincidían con el bloqueo. Las cinco
fuentes de la v27 sí coincidían. Se restauraron esas tres entradas desde v27,
sin cambiar los hashes del bloqueo ni ninguna fuente aprobada.

## Reproducción y evidencias locales

Todo recurso recuperado permanece en `work/ui_revision/` (no publicar).

1. `python work/ui_revision/extend_points.py`
2. `python work/ui_revision/extract_base.py`
3. `python tools/translate_ui_textures.py work/ui_revision/manifest.json --source work/menu_audit --base work/ui_revision/base --output work/ui_revision/extra --previews work/ui_revision/previews`
4. `python work/ui_revision/formation_names.py`
5. `python work/ui_revision/literals.py`
6. `python work/ui_revision/validate.py`
7. `python work/ui_revision/extract_events.py` y `python work/ui_revision/objectives.py`
8. `python work/ui_revision/reserves.py`
9. `python work/ui_revision/extract_locations.py` y `python work/ui_revision/locations.py`

Estos pasos preparan recursos pequeños, no una ROM. La futura integración debe
superponer `extra/` a las entradas de v27 y `romfs/` al CRO actual; no sustituir
las demás traducciones. No instalar hasta que el usuario autorice la build.

Manifiestos: `manifest.json`, `formations.json`, `literals.json`.
Evidencias: `validation.json`, `font_restoration.json`, `previews/report.json`.
Pruebas: `test_ui_formats.py`, `test_dialogue_lock.py` y `test_legacy_sprite.py`.
Los SSD de `events/` deben integrarse por ID en el paquete de eventos durante
la futura build; no son archivos sueltos que el juego lea directamente.

## Pendiente del encargo original

- Menú principal completo, miembros/título del equipo y resto de etiquetas de
  guardado: hay cadenas incrustadas cuyo espacio no admite la traducción completa.
  No solucionar cambiando las fuentes ni con recortes silenciosos.
- Resto de pantallas de creación/desbloqueo del equipo.
- Andy y la chica. La escena de fichaje de Willy (93911004) ya tiene traducidos
  todos los argumentos de diálogo visibles en v27; queda reproducir el caso
  señalado para determinar si corresponde a otra variante o a una ROM anterior.
- Verificación jugable de los rótulos y revisión de NPC de las zonas del Raimon,
  caseta y torre, incluidas sus variantes del capítulo 2. Los seis objetivos
  de los eventos 9202 revisados ya estaban traducidos en la candidata.
- Ampliar la comprobación PE/PT a los otros indicadores y ayudas del juego.
- Reproducción en el emulador de las capturas del usuario tras la futura
  instalación; ningún resultado está declarado estable en juego.

No cerrar la incidencia #20 ni declarar terminado el objetivo con este lote.

El usuario pidió cerrar este lote el 11 de septiembre para limitar el consumo.
Se detiene la ampliación del alcance y se conservan estos pendientes explícitos.
