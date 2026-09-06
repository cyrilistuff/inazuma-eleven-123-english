# Incidencias de la prueba IE1 — 2026-09-05

## QA-001: diálogo del club, cortes dentro de palabras

Capturas del usuario muestran palabras partidas y una página que empieza con
un fragmento de palabra. Candidata inicial `work/probe_ie1/archive.fa`.
Evidencia en `work/qa_dialogue_001/`. El generador recomponía por caracteres los
saltos calculados por ancho de fuente. La candidata v2 usa avances de FONT12 y
132 píxeles por línea; instalada con Azahar cerrado. Regresión visual pendiente.

## QA-002: congelación comunicada y posteriormente retirada

El usuario aclara que no ocurrió la congelación: fue un error suyo y ahora
percibe mayor fluidez. Se retira como fallo confirmado; no investigar un bloqueo
basándose en ese aviso. Logs conservados en `work/qa_cinematic_002/`.
QA-001 sigue abierto: nuevas capturas muestran espaciado irregular/solapamientos
y poco aprovechamiento del ancho. No aceptar v2 como corrección visual completa.

Nueva candidata v3 instalada para QA-001: véase [TIPOGRAFIA_IE1.md](TIPOGRAFIA_IE1.md).
Compara repertorio latino de ancho completo frente al ASCII con avances
incompatibles. Pendiente confirmación visual del usuario antes de seguir.

Actualización: capturas v3 muestran mejoría confirmada por el usuario, pero letras
demasiado separadas. V4 preparada con ajuste conservador, nombres, mapa y NPC.
Probar primero cajas y después el NPC tutorial completo, incluido modal tt36.

## QA-003: cinemática inicial negra, el juego después avanza

Nuevo aviso explícito del usuario en v3, distinto del bloqueo retirado QA-002.
Tenía el audio silenciado, así que su reproducción no está confirmada. El juego
avanza tras un rato. Causa no aislada; comparar con original y audio activado.
Los recursos de vídeo no están modificados. Esto no descarta un problema indirecto
ni demuestra por sí solo un fallo de Azahar.

## Resultado comunicado por el usuario en v4

El usuario confirma que los diálogos ahora están bien y los NPC probados
funcionan. Se conserva esa tipografía. Las capturas muestran rótulos de lugar y
objetivo cortados, el nombre William demasiado largo y la conversación opcional
de Willy todavía japonesa. El resto de la historia aún tiene huecos.

V5 instalada: `work/probe_ie1_v5/archive.fa`, SHA-256
`15ba60d4d600a510724dbcd57c312f446e1f51578e57ba394e8036ca666ca679`.
44 registros verificados, sin rechazos por tamaño. Nombres cortos Caseta/Clubes,
objetivo Ve al campo, nombre Willy y ambas conversaciones tutoriales revisadas.
83000040 era el evento de entrada que reponía el nombre japonés del área.
Se conserva bytecode, decisiones y referencias; las etiquetas gráficas de Sí/No
siguen pendientes. Los 21 textos sin correspondencia de 92010300 siguen pendientes.

QA-003: el usuario confirma audio durante el opening negro. Se encontró el aviso
oficial https://github.com/azahar-emu/azahar/issues/2495 (otro juego de la serie).
Un mantenedor recomienda desactivar skip present duplicate frames. Se aplicó
`use_skip_duplicate_frames=false` solo al título 00040000000BB800, con Azahar
cerrado y copia de la configuración en work/probe_ie1_v5. Pendiente prueba visual;
no dar por demostrado que sea la misma causa ni por solucionado el vídeo.

Pendiente localizar recursos de Extras, pantallas de avisos, nombre/teclado y
opciones Sí/No. Una captura no demuestra si son texturas o texto renderizado.
Un teclado latino necesita verificar también qué carácter introduce y guarda
cada tecla, no solo traducir su apariencia.
