# Prueba jugable obligatoria de Inazuma Eleven 1

Instrucción explícita del usuario, 2026-09-05. Este protocolo forma parte de los
criterios de aceptación y debe retomarse en sesiones posteriores.

Flujo acordado después de probar el control remoto: **el usuario controla y testea;
el agente observa las pantallas y logs**, diagnostica y prepara las correcciones.
No enviar entradas al emulador mientras el usuario realiza el recorrido.

## Recorrido y calidad exigida

- Probar la historia desde una partida nueva hasta la primera pachanga.
- Las cajas de diálogo no deben presentar bugs gráficos: texto cortado o fuera de
  la caja, glifos incorrectos, superposiciones, lecturas furigana residuales que
  estropeen el texto, páginas vacías inesperadas o controles de formato visibles.
- Hablar con varios NPC durante el recorrido, priorizando los que tengan fallos
  conocidos y aquellos cuyo comportamiento resulte sospechoso.
- Revisar especialmente las conversaciones de apertura, la zona del club y el NPC
  tutorial protegido por el evento 81000040 cuando estén accesibles. No asumir que
  un evento concreto se alcanza antes de la primera pachanga sin comprobarlo.

## Ciclo de fallo, corrección y regresión

1. Identificar la build y la ROM base con hashes; registrar la configuración y la
   versión del emulador. Distinguir original, reconstrucción sin cambios y traducción.
2. Ante el primer bug gráfico, de diálogo, interacción con NPC, bloqueo o crash,
   DETENER el avance de esa prueba. No seguir jugando para acumular otros fallos.
3. Registrar la escena, NPC, últimas acciones, resultado esperado/observado, build,
   captura disponible y log de la sesión; añadir event_id y PC si se pueden obtener.
4. Diagnosticar y corregir la causa. No declarar solucionado un fallo solo porque
   desaparezca un PC, aparezca otro fallo antes o pase un validador estático.
5. Repetir las acciones que provocaron el fallo con la build corregida. Verificar
   toda la conversación, avance de páginas, cierre del cuadro y vuelta al control.
6. Solo continuar el recorrido tras superar esa regresión. Repetir el ciclo ante
   cualquier nuevo fallo. Si no se logra corregirlo, informar del bloqueo exacto.

Nunca cargar save states de otra build. Usar partida nueva para los cambios del
intro; cualquier guardado normal de apoyo debe estar identificado y no sustituye
la prueba desde el comienzo. Conservar los logs antes de reiniciar Azahar.

## Informe de resultado

Separar comprobaciones estáticas de pruebas observadas en el emulador. Documentar
hasta dónde se ha llegado, NPC comprobados, fallos detectados y regresiones
superadas. No llamar estable ni aprobada a una build que no complete este recorrido.

La conversión CIA a cartucho es preparación local. El usuario pide eliminar el
script temporal de conversión una vez verificado el resultado y conservar la ROM
original. No subir ROMs ni archivos extraídos.
