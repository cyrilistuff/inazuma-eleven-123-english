# V10: candidata construida e instalada, pendiente de QA

2026-09-06. La prueba del usuario rechaza la tipografía de v9: hay letras
solapadas y líneas que no aprovechan la parte derecha del cuadro (Tod y Mark).
También persisten logos IE2 demasiado grandes y el logo japonés de carga.

Entradas locales: `work/probe_ie1_v10_inputs/`, copiadas de v9.

- Los cuatro archivos FONT12/FONT8 BCFNT/NFTR son idénticos a v7, comprobados
  byte por byte. Se revierten las métricas nativas introducidas en v8.
- `reviewed.json` es idéntico al de v9: se conservan todas las traducciones.
- Ambos logos IE2 del atlas de selección tienen escala 0.68, centrados en sus
  rectángulos originales. No se alteran coordenadas del diseño.
- El logo de carga se sustituye en `menu/common.arc`, textura
  `ie99_common_loading_mes_t01.tga`, caja 278,110–396,205, por el de la recopilación
  con «La leyenda de Mark Evans».
- Los títulos 1–10 de `stage_title_b.arc` siguen incluidos; falta comprobar su
  representación en juego. El primero dice «¡Llega la Royal!».

Se han regenerado 39 texturas en 14 archivos con comprobación de tamaño,
metadatos y roundtrip. Revisadas las previews de selección y carga.
Pasan 19 pruebas automáticas. No hay validación jugable de estas correcciones.
El ajuste de líneas sigue siendo el de v7 (20 columnas); la recuperación de la
fuente no demuestra por sí misma que el ancho visible sea satisfactorio.

La construcción falló al copiar el archivo base por falta de espacio. Se eliminó
únicamente el archivo parcial recién creado. Quedaban aproximadamente 780 MiB
libres; cada archive.fa ocupa 1.307.772.544 bytes. La v10 NO está construida ni
instalada. Azahar seguía abierto; no se modificó el mod activo v9.

Para retomar: liberar espacio con el usuario (recomendado 4 GB para construcción
y copia de instalación), ejecutar el comando de v9 de REANUDAR_IE1.md sustituyendo
las rutas v9 por v10, verificar el informe y los hashes, y cerrar Azahar antes de
instalar con copia de reversión. Repetir primero las conversaciones de Tod y Mark
aportadas, y después selección, carga y título del capítulo. No usar save states
de otra build. El usuario controla el emulador.

Precisión de alcance: las 21 adiciones de v9 son registros del evento 81000040;
su distribución por zonas y disponibilidad en capítulo 1 no están demostradas.
No equivalen a 21 NPC ni a un capítulo completo.

## Construcción e instalación completadas

Tras liberar espacio, se construye e instala v10 con Azahar cerrado.
SHA256: e711c314625139a1857285463f8a1704b199bb89fff5230cda20e1f25da89f7e.
Archivo: work/probe_ie1_v10/archive.fa. Informe: archive.report.json.
205 traducciones idénticas a v9, sin rechazos ni registros ausentes; 26 archivos
adicionales comprobados contra sus hashes. Copia del mod anterior:
work/probe_ie1_v10/previous-installed.fa (v9). El bloqueo de espacio descrito
arriba corresponde al intento anterior y ya está resuelto.

Mapa y ampliación de NPC quedan para la siguiente build por instrucción del
usuario. También registrar su precisión: los puntos suspensivos de v9 se veían
bien, pero el resto de letras se pegaban. Esta candidata aplica la reversión de
fuentes completa ya preparada; comprobar también los puntos suspensivos al probar.
