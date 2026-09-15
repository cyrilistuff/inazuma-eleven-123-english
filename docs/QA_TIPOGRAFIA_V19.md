# Candidata de regresión general v19

V17 presenta cortes dentro de palabras y espaciado irregular. La prueba v18
solo cambió 81000090/287 y no resolvió completamente los solapamientos. La
captura de Steve que parecía correcta provenía de un estado rápido de otra ROM;
no permite atribuir el fallo exclusivamente al capítulo 2.

V19 conserva las traducciones actuales y la textura corregida de Objetivo.
Recupera las cinco fuentes BCFNT/NFTR de v13 y retira el experimento de fuentes
de v18. El reflujo de prueba usa un máximo conservador de 20 caracteres por línea,
cortando entre palabras y con tres líneas por página. No se afirma que ese límite
aproveche todo el contenedor ni que los anchos reales hayan sido resueltos.

Entradas, orden reproducible e informes: `work/shared/candidatas/probe_ie1_v19/`.
La candidata requiere repetición jugable de profesora, Andy, Nelly y puerta
trasera. Arrancar de nuevo y usar guardados internos del juego; no cargar estados
rápidos de otras builds. No declarar corregido el espaciado sin esa regresión.
