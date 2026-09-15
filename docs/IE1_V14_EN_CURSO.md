> Actualización 2026-09-09 (v27): la candidata instalada elimina los tres restos
> visibles de 9210 y deja 18.806 diálogos visibles sin japonés en 982 eventos.
> `eve.pkb` pasa con 19.039 textos y 0 rechazos. Hash candidato/instalado:
> `91f816060775190e994f585fae5e09c8adab4cc1998b059f250372387ab10369`. La prueba
> jugable guiada sigue pendiente.

> Actualización 2026-09-09 (v26): la candidata actual está instalada en Azahar.
> Hash: `394b3ea3f986204a5ed7bb9d8fb2a349333d6b15490736cf16f259ca1dcfa27f`.
> Los 27 rechazos de longitud quedaron resueltos sin tocar caja ni tipografía; 19.036
> textos pasan el reinserto con 0 rechazos. Se mantienen traducidos los diálogos de
> pachangas/cadena, Royal, nombres de equipos y categorías. Falta la prueba guiada.

# V23 candidata: pachangas, cadena y nombres de equipos

2026-09-09. La candidata local v23 está generada como archivo LayeredFS y
instalada en Azahar. Añade los diálogos visibles de las pachangas y la cadena de
partidos de `mch.pkb` (1.422 registros en los eventos `9420xxxx`), mantiene la
traducción del partido de la Royal (`94001500`) y traduce los 158 nombres de
`team.pkb`, los 20 títulos de `teamtitle.dat` y las 32 categorías de
`clubinfo.dat`. La auditoría conserva las
instrucciones, no encuentra japonés visible y no cambia la caja ni la
tipografía bloqueadas de v20. Hash de la candidata y de la instalación:
`bf1e194564170d86cffcf3acfa70409420584ca048b699253611011e35614393`.

La prueba jugable queda pendiente de reiniciar Azahar y recorrer las escenas con
esta candidata; no se considera estable por la auditoría estática. La carpeta de
la v21 se eliminó después de verificar la copia instalada.

# V21 histórica: diálogos del partido de la Royal

2026-09-08. La candidata local v21 se generó como archivo LayeredFS y estuvo
instalada en Azahar. Incluye los 143 diálogos visibles del partido de la Royal
Academy (evento `94001500` de `mch.pkb`). Sigue pendiente la verificación jugable
guiada por el usuario; v16, v15, v14 y v13 quedan preservadas.
Seguimiento: issue #19. Las entradas de v14 se conservaron y las correcciones de
variantes y semántica se guardaron en `work/probe_ie1_v14_inputs/reviewed.json`.
La candidata v21 fue sustituida por v23 y su carpeta se eliminó tras verificar
la instalación.

## Estado de compilación

La orden de no generar la build fue sustituida por la indicación posterior del
usuario. Se generaron `work/probe_ie1_v17/archive.fa` y
`work/probe_ie1_v17/inazuma123_ie1_v17.3ds` con cero rechazos y se conservaron
las candidatas anteriores y la ROM original. La instalación activa de Azahar
coincide con el SHA-256 de v17; la candidata aún requiere la prueba guiada y no
se debe llamar estable hasta completar ese recorrido.

La v17 corrige el ancho de reflujo de los diálogos (208 px), conserva la imagen
original de `FONT12T` y añade un píxel de avance a las letras latinas. El rótulo
rojo de «Objetivo» vuelve a ocupar exactamente su interior, sin sobresalir por
la derecha. También se corrigieron 18 pares desalineados de los eventos 81000010
y 81000011: recorrido del Sr. Veteran, acceso a las zonas del instituto y
mensajes del partidillo. La textura de `field_t.arc` se regeneró y se comprobó
que es el único recurso gráfico nuevo respecto a la v16.

## Alcance de la tanda v14

Completar primero todas las correcciones solicitadas. Después continuar la
traducción del capítulo 2 y de TODAS las zonas del instituto Raimon (incluida
la caseta) y la torre Inazuma. Incluir NPC y variantes por evento, escenas,
misiones y rótulos de ubicación. No generar ni instalar una build al finalizar
la tanda de correcciones: esperar una nueva indicación de compilación.

Nueva captura: rótulo del edificio principal, segunda planta, aula de segundo.
Traducción prevista, sujeta al espacio: «Edificio principal 2F · Aula de 2.º».
Inventario local iniciado en `work/v14_location_audit/`: 41 texturas de minimapas
mr01 extraídas para identificar las zonas. El rótulo se ha localizado en los
eventos 92070100 y 92080100, opcode 4037, junto a sus órdenes de minimapa 3070.
La traducción aplicada a los datos de trabajo es «Edificio principal 2F Aula 2».

### Inicio de la ampliación de NPC

- 81000180: preparados sus 24 diálogos principales de la caseta, incluidos
  búsqueda de miembros, reunión con Wintersea y pregunta por Axel.
- 81000140: preparados 14 diálogos de aula de tercero. La ubicación se infiere
  del contenido; falta enlazarla con el mapa exacto, no confundirla con el aula
  de segundo de la captura.
- Total revisado actualizado: 19.039 registros, todos con hash y reinserción
  comprobados; instrucciones conservadas. La candidata v17 ya está compilada e
  instalada en Azahar para la prueba guiada.
- La limpieza semántica posterior corrigió 267 textos heredados de otra variante
  o con marcadores antiguos pegados (`i...j`, `i!j`, `h…h` y envoltorios equivalentes),
  incluidos diálogos de Axel, Jack, Bobby, Jude, Celia y NPC de Raimon. Las
  elipsis que formaban parte del texto se conservaron.
- Se completaron además ocho diálogos visibles de transición de 9201 que aún no
  estaban enlazados en la revisión por evento: caseta, búsqueda de Nathan, escena
  de Jack, narración del partido y cierre de la Royal.
- Se añadieron la conversación compartida de 92040300 sobre el miembro que dejó
  el equipo y 29 diálogos compartidos de las escenas 9210. No quedan diálogos
  compartidos no revisados en 9202–9210 ni en las zonas 8100.
- También se retiraron 30 envoltorios `h…h` que seguían visibles en NPC y
  escenas de Raimon, la torre y la historia de 9210, además de separadores y prefijos
  heredados que aparecían pegados a algunos mensajes.
- Inventario local por evento en `work/probe_ie1_v14_inputs/npc_inventory.json`,
  actualizado con los índices principales y las variantes compartidas auditadas.
  Las cadenas cortas restantes son lecturas kana; no se tratan como diálogos.

### Cobertura real comprobada

- El inventario 81xxxx contiene 1.953 diálogos principales y están revisados.
  Las variantes compartidas, los rótulos y los nombres de lugar ya están
  auditados de forma estática; queda comprobarlos en el recorrido jugable.
- El capítulo 2 queda completo en sus diálogos principales. La auditoría actual de
  referencias visibles de argumento 1 da 9201: 413/416; 9202: 399/399;
  9203: 728/728; 9204: 480/487; 9205: 492/492; 9206: 611/612;
  9207: 629/629; 9208: 618/618 y 9209: 394/394. Los tres registros restantes
  de 9201, los siete de 9204 y el de 9206 son espacios técnicos; no contienen
  texto visible.
- La auditoría directa de `opcode 0x301d`, argumento 1, confirma 382/382 en
  9202 y cero pendientes visibles en todos los bloques 9202–9209 y 8100.
  Se incorporaron 121 diálogos que pertenecían a eventos con la cabecera `SSD`
  omitida en la extracción; 79 son del bloque 9202–9209 y 42 pertenecen a
  variantes de 9000, 9201, 9210 y 9340. Los siete de 9204 y uno de 9206 quedan clasificados
  como espacios de ancho completo, no como diálogos pendientes. En 9210 quedan
  diez respuestas de pausa o puntos suspensivos, conservadas sin alterar.
- Se han añadido los rótulos de edificio de 2.º y 3.º, las órdenes de minimapa y
  las indicaciones de reclutamiento de Handa, Shourinji y el pasillo de la
  segunda planta. Los demás nombres de ubicación localizados en estos eventos
  también están cubiertos; queda comprobar su aparición por evento.
- Se localizaron 3.096 mensajes repetidos de ojeo que indicaban en japonés dónde
  estaba cada NPC. Ahora usan plantillas españolas con lugares concretos de la
  ribera, la caseta, la torre, los campos, los edificios de Raimon y la zona
  comercial. La tanda suma 3.114 registros de esta familia al contar las
  variantes con nombre que ya estaban revisadas.
- Se promovieron además 5.363 líneas unívocas del CSV español existente a la
  revisión con hash. Las 208 coincidencias ambiguas y las líneas que no pasan el
  límite se mantienen separadas para revisarlas por evento y no mezclar diálogos.
- Se añadieron también 988 mensajes repetidos de ojeo, selección y recompensa:
  nombres de jugadores, criterios de búsqueda, puntos de amistad, premios y
  confirmaciones de la caseta.
- Se hizo una revisión semántica adicional de los diálogos largos del capítulo
  2: se corrigieron 25 coincidencias que habían recibido por error un mensaje
  de incorporación de jugador, además de 24 variantes repetidas de indicación
  de ubicación y un grito alargado que no podía ajustarse a una línea.
- La auditoría de variantes de incorporación corrigió otros 186 nombres
  desplazados en transiciones, reclutamientos, escenas 9210 y eventos 9100/9700.
  También se normalizaron 211 referencias de glosario que mezclaban nombres
  japoneses con los nombres españoles del proyecto (Celia, Silvia, Nelly,
  Julia, Arthur, Jude, Axel, Bobby, Seymour, Ray Dark y Kirkwood). Se conservó
  la elipsis de una escena que había recibido una frase ajena. La validación
  vuelve a pasar los 19.039 registros sin japonés visible, sin cambios en las
  instrucciones y con todas las cadenas dentro del límite.
- La auditoría de 82 eventos 8100 confirma 1.953/1.953 diálogos de dueño y cero
  candidatos compartidos largos pendientes. Las 41 texturas de minimapa de
  `mr01` son tiles de mapa sin texto incrustado; los nombres visibles proceden
  del atlas de mapa general y de los rótulos dinámicos opcode 4037.
- El atlas de mapa general contiene ya las siete etiquetas españolas: Estación,
  Zona comercial, Royal Academy, Torre Inazuma, Raimon, Ribera y Residencial.
- La cifra histórica de «97 rechazados por longitud» no aparece como lista
  separada en los informes conservados. La auditoría actual reconstruye 241
  candidatos de 9202–9209 que excedían el límite o fallaban la codificación;
  los 241 tienen ahora una traducción revisada dentro del límite de 247 bytes (máximo 244) y quedan
  0 rechazados. El detalle está en
  `work/probe_ie1_v14_inputs/length_recovery_audit.json`.
- Se repitió la auditoría directa de referencias visibles tras la última limpieza: 9201 413/416, 9202 399/399, 9203 728/728, 9204 480/487, 9205 492/492, 9206 611/612, 9207 629/629, 9208 618/618, 9209 394/394 y 8100 2.014/2.014. Los diez registros no textuales de 9210 son pausas o puntos suspensivos intencionados; no se han alterado.

### Último avance del capítulo 2

- 9207 queda cerrado en sus diálogos principales (609/609), incluidas las escenas de los veteranos, el entrenamiento del Ciclón de Fuego, Igajima y el seguimiento de Kageyama.
- 9208 queda cerrado en 574/574 y 9209 en 369/369.
- En los eventos 8100 de Raimon se han cubierto 1.953/1.953 diálogos principales de NPC y escenas,
  además de 21 variantes compartidas compactadas. No quedan candidatos largos
  pendientes en este bloque.

- 92010100: entrenamiento del club y comentarios de sus miembros (10).
- 92010200: monólogo de Mark al buscar un campo libre (1).
- 92010250: tutorial de movimiento, guardado y descanso (6).
- 92010300: NPC de Nathan, atletismo y el conflicto por el balón (22).
- Los nuevos registros pasan la validación de tamaños y mantienen intacto el
  código de instrucciones. La candidata v16 está compilada e instalada; queda
  la comprobación jugable.
- Se añadieron 1.142 coincidencias del glosario oficial en 9202–9209, 88
  diálogos manuales de historia y NPC en 9202, 28 variantes compartidas
  localizadas en 9205–9209, 21 variantes de NPC de Raimon compactadas y 23
  variantes compartidas de las escenas de Otaku y Royal, 16 del bloque de
  Shuriken, veteranos y campo, 32 de Zeus y Farm, y 15 de las escenas finales.
  Se añadieron también 15 rótulos dinámicos de ubicación (caseta, entrada,
  Royal, ribera y aulas) y se revisaron los argumentos
  compartidos largos de 9202; no quedan diálogos relevantes pendientes en ese
  bloque. Se añadieron además 121 diálogos de eventos con cabecera SSD ausente,
  3.096 indicaciones de localización de NPC, 5.363 traducciones unívocas del
  CSV existente y 988 mensajes repetidos. Se cubrieron también 447 coincidencias
  adicionales del CSV con prefijos binarios y 41 líneas manuales del bloque 9210.
  Se tradujeron además 60 textos visibles del visor de eventos/debug de 9000,
  incluidos los selectores de capítulos, partidos, clubes y guardado de
  90000000 y 90000005. La validación global pasa para 19.039 registros en 982
  eventos con entrada (965 contienen sustituciones); esto es una tanda
  de trabajo y no equivale a capítulo terminado.
- En la revisión de variantes compartidas se añadieron 14 líneas que faltaban en
  eventos 1009 y se corrigieron seis respuestas desfasadas de pachangas y
  reclutamiento en 1008–1009. La traducción de esas variantes se comprobó contra
  el mismo texto fuente y sus hashes.
- También se unificaron 11 respuestas repetidas dentro de 92051400 y 92081200,
  donde una misma línea japonesa aparecía con traducciones diferentes según la
  rama del evento.
- Diez variantes de incorporación de Willy que aún decían «el chico de las
  gafas» ahora usan su nombre oficial, manteniendo el texto de cada tipo de
  evento (unión al equipo, acompañamiento o llegada con el grupo).
- El bloque de la caseta 92041050 tenía 42 respuestas de ojeo y entrenamiento
  desplazadas; se corrigieron según cada frase fuente. Sus 223 variantes 9713
  se sincronizaron con ese mismo glosario para que nombres, filtros, afinidades,
  puntos de amistad y confirmaciones no muestren mensajes de otra opción.
- La revisión cruzada de historia y NPC corrigió otras 28 respuestas
  desalineadas en la torre, las escenas de Bobby, Axel y Mark y los eventos 8100
  del edificio y el bedel. Se conservaron las elipsis de las escenas donde eran
  parte del texto correcto.
- En 9203 se añadieron diálogos manuales de las escenas de Bobby, Nathan, Wild,
  la llegada a la caseta y los amistosos. Su cobertura actual es 708/708;
  9203 queda cerrado en sus diálogos principales; los mensajes compartidos que quedan son técnicos o lecturas kana. En 9204 están cubiertas las escenas de Natsumi, Mikage Seino, Yuka, el aparato, la torre Inazuma y el legado de David Evans; los siete registros restantes son vacíos técnicos. Se añadieron también las escenas del campo de Kasamino, el seguimiento de Axel, el manual de Rayo Caído, el conflicto de la puerta trasera y la preparación del partido contra Wild.

### Siguiente bloque de traducción

- El capítulo 2, incluidas las escenas 9210, sus variantes de historia, las zonas
  de Raimon y la Torre Inazuma quedan cubiertos de forma estática en la tanda
  actual.
- El visor de eventos/debug 9000 ya está revisado: sus 60 textos visibles han
  quedado en español, incluidos los selectores de capítulos, partidos,
  amistosos, clubes y guardado. La candidata v16 ya está instalada para la
  prueba guiada en Azahar.
- Las variantes 93xxxx de NPC quedan prácticamente cerradas: se han localizado
  cinco eventos de reclutamiento (99 diálogos, incluidos los puntos suspensivos sin cambios) y solo quedan nueve líneas de
  puntos suspensivos que se mantienen intactas. Queda la prueba visual guiada
  por el usuario.
- Se han corregido también los 14 mensajes visibles de recuperación de puntos
  de pasión y de la variante de reclutamiento de la caseta.
- La revisión semántica posterior ha dejado en 0 los nombres desplazados en los
  mensajes de incorporación y en los diálogos largos de 9202–9209; queda
  pendiente ver estas escenas en Azahar para confirmar que cada variante aparece
  en su evento.
- La última validación vuelve a pasar los 19.039 registros tras 267 correcciones
  semánticas y de formato, incluidos los envoltorios antiguos, separadores y
  prefijos residuales. Quedan 0 cadenas con japonés visible, 0 rechazos de longitud y el
  máximo codificado es 245 bytes. Las 18 entradas fuera de la tanda siguen siendo
  solo puntuación, espacios técnicos o variantes de puntos suspensivos, que se
  mantienen intactas por indicación del usuario.
- La auditoría global deja 18 registros no revisados: son signos de puntuación,
  espacios técnicos o variantes aisladas en 8600, 9102, 9210 y 9700. Las escenas 9210 del capítulo 2 ya no dejan texto japonés
  visible pendiente; las tres líneas de puntos suspensivos se conservan intactas.
- La auditoría global de 18.806 referencias `0x301d/arg1` en todos los eventos
  extraídos no encuentra NPC ni escenas de historia sin revisar: solo quedan tres
  pausas de 9210 (`ウ…。`, `う…。` y `…。\f…ん…。`), conservadas deliberadamente.
- El CSV de traducción solo conserva una fila `pendiente` dentro de estos bloques (`92102300`); es una lectura kana (`ようじん`), no un diálogo visible.
- La auditoría directa de los registros visibles `0x301d/arg1` en 9202–9210 y
  8100 no encuentra japonés pendiente en NPC ni historia. Solo permanecen tres
  pausas intencionadas de 9210 (`ウ…。`, `う…。` y `…。…ん…。`), registradas en
  `work/probe_ie1_v15/visible_jp_audit.txt`.

## Limpieza local

Se eliminaron 18,46 GB de candidatas antiguas v2–v9, v11–v12 y la carpeta de
trabajo v10. Se conservaron la ROM original extraída, la candidata v13, sus
entradas v13/v14 y los datos necesarios para continuar.

## Preparado y comprobado de forma estática

- Escenas 92010510, 92010520 y 92010700: Mark/Silvia, NPC de evento y
  Arnold/Donovan; se incluyen los diálogos largos cuyo dueño usa argumento 2.
- Evento 81000030: 73 diálogos de argumento 1 y dos diálogos compartidos de
  argumento 2 de la zona deportiva, incluidas variantes de la historia.
- 19.039 registros revisados en total pasan hash de origen, codificación, longitud,
  reinserción y lectura. Se mantienen los bytes de instrucciones. La última tanda
  suma 267 limpiezas semánticas y de marcadores antiguos, más ocho transiciones
  visibles de 9201, 50 correcciones de alineación en variantes 9700 y 18 pares
  de NPC/partidillo de 8100. Informe local: `work/probe_ie1_v17/validation.json`.
- La orden ejecutada para v17 usa el codificador ASCII de BCFNT. El modo
  experimental de ancho completo duplicaría los bytes de las frases largas y
  rechazaría 33 registros; con ASCII el máximo actual es 245 bytes y no queda
  ningún rechazo de longitud. La copia tipográfica coherente está en
  `work/probe_ie1_v14_inputs/extra_ascii/` y el archivo generado es
  `work/probe_ie1_v17/archive.fa`.
- Estrategias: las opciones vistas en japonés son literales del CRO, además de
  las texturas. Sustituciones acotadas: Normal, Cubrir y Atacar, con ASCII para
  respetar la capacidad original. Su apariencia exige regresión en juego.
- Caja de recuperación: literal corto cambiado a Pasión, usando padding nulo
  comprobado. No se han desplazado instrucciones ni datos posteriores.
- Objetivo: restaurado desde el atlas original y ajustado al interior del rótulo,
  sin la caja pequeña desplazada que cubría el borde.
- Victoria/derrota y parte superior de recompensas: seis texturas preparadas.
  El borrado por muestra de fila conserva las bandas horizontales del fondo.
- Afinidades y botón de técnicas: siete texturas usan recortes de las referencias
  aportadas por el usuario. Son referencias de captura, no una extracción nueva
  de gráficos NDS sin compresión. Se conservan los marcos y estados numerados.
- Manifiesto completo regenerado: 106 texturas en 67 archivos. Tras ajustar el
  borrado del fondo se regeneró game_result_t con todas sus operaciones.
- Auditoría estática de interfaz: 456 operaciones en el manifiesto y ninguna
  cadena japonesa. Victoria, experiencia, puntos de victoria, bonificación,
  pasión, amistad, objetos, objetivo, mapa, técnica y mensajes de partido ya
  tienen texto español. Los símbolos de afinidad y el botón de técnicas usan
  las referencias gráficas preparadas.
- El nombre de la aplicación vive en `work/exefs/icon.icn` (SMDH). Se conserva
  el título japonés original y el slot español contiene «Inazuma Eleven 1-2-3!!»
  en la build v17; queda comprobar su presentación en el menú.

## Pendiente antes de presentar una build completa

- Las etiquetas inferiores de experiencia, pasión, amistad y objetos ya están
  incluidas en el manifiesto de resultados. Falta la regresión visual en juego.
- La auditoría de NPC, variantes, misiones dinámicas y rótulos de capítulo 2 ya
  está completada de forma estática. Falta comprobar en el recorrido jugable que
  cada evento se muestra en el momento correcto.
- Queda revisar visualmente iconos, estados inactivos y el botón táctico
  independiente de la segunda fila del atlas de técnicas.
- El título de ventana está confirmado en SMDH, `work/exefs/icon.icn`, no en FA.
  El slot español está integrado en la build v17 y pendiente de comprobación en
  el menú.
- La candidata v17 está instalada con Azahar cerrado y tiene copia de reversión
  registrada en `work/probe_ie1_v17/installation.json`. La regresión jugable la
  conduce el usuario; no se declara estabilidad a partir de validaciones offline.

No publicar entradas, capturas, gráficos, literales ni archivos del juego.

## Instalación v17 — 2026-09-08
Instalada en el mod de Azahar 00040000000BB800 con `archive.fa` y el CRO actual.
Los hashes coinciden con la candidata. La copia de reversión está en
`work/probe_ie1_v17/installation.json`. La v16 queda respaldada en su carpeta.
Prueba jugable pendiente; el usuario
controla el emulador.
