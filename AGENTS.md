# Retoma del proyecto

- Objetivo actual: traducir y depurar Inazuma Eleven 1 de la recopilación 3DS.
- Leer `CLAUDE.md` y `docs/PROTOCOLO_QA_IE1.md`. El protocolo es una instrucción
  explícita del usuario: cajas de diálogo sin bugs gráficos; recorrido hasta la
  primera pachanga con varios NPC; detenerse ante cada fallo, corregirlo y repetir
  exactamente su reproducción antes de continuar.
- Consultar `docs/SSD_REGISTROS_IE1.md` antes de tocar el texto. El reinsertor
  antiguo omite el tamaño de cada registro inline. Las conclusiones históricas de
  imposibilidad no son evidencia de que el formato correcto falle.
- Flujo acordado con el usuario el 2026-09-05: el usuario juega y prueba; el agente
  observa el emulador y sus logs sin enviar entradas de teclado/ratón durante la
  prueba. Preparar correcciones y volver al punto del fallo con el usuario.
- No subir ROMs, extracciones, logs ni datos oficiales recuperados. Mantener los
  originales y distinguir una candidata de una build verificada en juego.
