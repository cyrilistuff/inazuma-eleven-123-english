# Inazuma Eleven 1·2·3!! — traducción al español, versión 1.0

Primera versión que se aplica con **[IE-repack](https://github.com/Javiju555/IE-repack)**,
de Javiju555, en lugar de DeltaPatcher.

> **Sobre el número de versión:** esta numeración empieza de cero con el sistema de
> parcheo nuevo. Es **posterior** a las antiguas v1 y v1.1, que siguen publicadas para
> quien tenga exactamente el volcado con el que se generaron.

> **Aviso: por ahora solo emulador.** El `.3ds` que genera IE-repack funciona en Azahar y
> Lime3DS, pero falla al verificarlo o instalarlo en una 3DS real (GodMode9: «VERIFICATION
> FAILED» en el contenido 0). Es un fallo de la herramienta al reconstruir la ROM, ya
> comunicado. Se avisará cuando esté corregido.

## Por qué cambia la forma de parchear

El sistema antiguo comparaba la ROM entera byte a byte, así que exigía un volcado
idéntico al nuestro: con cualquier otra revisión fallaba, y no siempre de forma clara.

El pack de esta versión va **archivo por archivo**. La herramienta comprueba el hash de
origen de cada archivo de tu copia, aplica su parche, verifica el resultado y reconstruye
la ROM. Si tu volcado no es el juego esperado, se detiene con un mensaje comprensible en
vez de generar una ROM defectuosa. El parche también es más pequeño.

## Qué incluye

- Inazuma Eleven 1 traducido: historia, menús, objetos, técnicas y jugadores.
- Voces y cinemáticas en español.
- Interfaz de la recopilación traducida.
- Esta versión pule además gráficos de la interfaz que se veían como pegatinas:
  botones de Extras, Supertécnica, Seguir y Salir, Volver y Atrás, placas de partido,
  puntos, uniformes, cuadro del torneo y pantallas de ayuda.
- Inazuma Eleven 2 e Inazuma Eleven 3 siguen en japonés.

## Cómo se aplica

Instrucciones completas en `instrucciones.txt`. En resumen: abres IE-repack, eliges el
modo **Pack (manifiesto)**, tu copia japonesa descifrada, la carpeta `pack` y dónde
guardar. El resultado es un `.3ds` que se abre en Azahar o Lime3DS con
Archivo → Cargar archivo, sin instalar nada.

## Comprobación

Los dos archivos que cambia la traducción, y sus hashes de origen y resultado, están en
`pack/manifiesto.json`. La herramienta los verifica por ti.

## Créditos

- Dirección y traducción: **luishidalgoa**
- Colaboración: **TitoGalan**
- Herramienta de parcheo IE-repack: **Javiju555**

Proyecto de aficionados sin ánimo de lucro, no asociado a LEVEL-5. No se distribuyen
ROMs ni datos del juego: solo los parches, que se aplican sobre tu propia copia.
