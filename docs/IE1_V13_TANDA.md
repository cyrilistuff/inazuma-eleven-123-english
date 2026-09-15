# V13: tanda reunida, pendiente de prueba jugable

2026-09-07. Entradas congeladas en work/probe_ie1_v13_inputs; salida en
work/shared/candidatas/probe_ie1_v13/archive.fa. No usar las entradas de v12 para reproducir la
antigua candidata v12: se ampliaron durante esta tanda y se congelaron como v13.

## Contenido y comprobaciones

- 556 registros traducidos en el informe, 543 de ellos revisados explícitamente.
  Sin rechazos ni registros ausentes en el ámbito seleccionado.
- 81000040, 81000080 y 81000350: todas las entradas normales de diálogo del
  argumento 1 cubiertas, además de las frases compartidas identificadas en otros
  argumentos. Cubren conversaciones del instituto y torre con variantes de
  historia. No equivale a todos los NPC de todos los mapas ni a capítulos completos.
- Objetivos y rótulo Objetivo de capítulos 1–2: opcode 0x402f, argumentos 2/3.
- Recuperación exacta de la captura: eventos 63000050, 63000180, 63000350,
  63000370, 63000390, 63000400, 63000561 y 63000590. El precio se inserta mediante
  %d: se conserva el parámetro y se traducen confirmación, insuficiencia y resultado.
  El filtro histórico de eventos >= 80000000 era la causa de no encontrarlos.
- Menús de formación, estrategias, objetos/equipo, atributos, instrucciones de
  colocación, Empezar/Menú, acciones básicas tanto en command.STR como en sus
  imágenes de sustitución, objetivo y límite rojo de pachanga, indicadores de
  tiempo y potencia total. 93 texturas generadas; 80 archivos adicionales en FA.
- Nombres del mapa, tres formaciones, nombres visibles de 18 jugadores del
  grupo inicial/capturas, perfil de Mark y campos del equipo/club de rugby.
- Letras de v10 conservadas. Solo cambia un byte de métricas en FONT12 BCFNT,
  uno en FONT12 NFTR y uno en FONT8 NFTR para recuperar el punto de v9.
  FONT8 BCFNT queda idéntico. No se ajustan nuevamente las letras.
- Logos: Fuego 0.82, Ventisca 0.68; ambos desplazados 12 píxeles a la izquierda.
  Se mantienen títulos de capítulos y logo occidental de carga anteriores.

SHA256 archive.fa:
1fadc236f24e66d7df03886799aaa7151a473bb750d72eda5ea27b169e688f9b

El informe y todos los hashes de extra/ se verificaron. Pasan 19 pruebas.
Las texturas se recodifican con dimensiones/metadatos intactos y roundtrip.
Se revisaron previews de formación, botones, mapa, logos y rótulos de acciones.

## Literal externo al archivo FA

El texto fijo del equipo Raimon en ina_main1.cro se reemplaza en 0x12d074,
dentro de sus 14 bytes originales. No hay desplazamiento de datos ni cambios
fuera de ese literal. No se aplican los antiguos parches de instrucciones/caves.
Original SHA256: b68bfa2d21f659eff1f9392f8ef19cfda5205a2a73673590d6e676bea032f7be.
Resultado SHA256: 092758d9c0fe46c57d173c37ae5b8ef53896a44a0c17fc72798be97231d1f709.
La carga de este módulo modificado también requiere QA en Azahar.

## Instalación y regresión

Consultar work/shared/candidatas/probe_ie1_v13/installation.json para hashes instalados y presencia
previa del CRO. Copia del archivo antes instalado en previous-installed.fa.
Si previousCroExisted es false, revertir exige retirar únicamente el CRO añadido
al directorio del mod; no tocar el CRO de la ROM base. Si es true, restaurar
previous-ina_main1.cro. Siempre con Azahar cerrado.

El usuario controla el emulador. Comprobar primero arranque y carga de IE1;
después puntos suspensivos y diálogos conocidos, recuperación con coste variable,
mapa/objetivos, formación/objetos y primera pachanga. Detenerse ante el primer
fallo y repetir su reproducción después de corregirlo. No cargar estados rápidos
de otra candidata. La tanda está implementada, no declarada estable ni aprobada
en juego. La cobertura de otras zonas y la calidad de cada variante siguen
requiriendo revisión; no presentar un porcentaje inventado de capítulo traducido.

## Lectura de recortes QNA

tools/qna_regions.py lee QNA 051: tabla de nombres indicada en +36, tabla de
partes en +44, partes de 128 bytes, rectángulo en sus primeros cuatro floats y
índice de textura en +88. Sirve para comprobar recortes sin editar el diseño.
Algunos recursos usan coordenadas mayores que su textura; no asumir una relación
1:1 para todos los QNA. Los recortes de formación y mensajes usados se verificaron.
