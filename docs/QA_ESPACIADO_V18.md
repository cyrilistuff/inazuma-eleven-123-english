# Regresión tipográfica de v17: prueba acotada v18

El usuario confirma cortes automáticos dentro de palabras en el aula: una letra
sola ocupa la segunda línea y el salto insertado desplaza el resto a la tercera.
También confirma separaciones y solapamientos. V17 no supera la regresión.

Registro localizado: evento 81000090, índice 287. Las métricas ASCII BCFNT usadas
para envolver el texto no corresponden a las métricas NFTR presentes: esta última
solo contiene el espacio en el rango ASCII. Las correspondencias de varios
portadores griegos también faltan. Esto es una hipótesis de causa, pendiente de
confirmación jugable.

`tools/probe_ie1_spacing.py` prepara una candidata local desde v17. Cambia solo
ese registro de diálogo a transporte latino de ancho completo, con dibujo y
métricas coordinados en FONT12 BCFNT/NFTR. Añade las correspondencias ausentes,
conservando los demás registros e instrucciones. Usa un límite de prueba de
184 unidades BCFNT; no se afirma que sea el ancho máximo del contenedor.

Candidata: `work/probe_ie1_spacing_v18/archive.fa`. Datos e informe permanecen
locales. La ROM v17 sirve de base con el mod de prueba; no hay una ROM v18 nueva.
La v17 original se conserva para revertir. No extender esta solución a la
traducción completa sin repetir el diálogo de la profesora, todas sus páginas,
su cierre y la devolución del control. El usuario controla Azahar.
