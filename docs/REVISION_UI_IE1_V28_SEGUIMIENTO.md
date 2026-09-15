# Seguimiento tras la prueba de v28

El usuario confirma que v28 muestra parte de las correcciones, pero sigue
encontrando elementos pendientes. Esto no constituye aprobación de toda la ROM.

Preparación local en `work/ui_followup/`, con v28 como base:

- Botón de reanudar el partido: «Técnicas» sustituido por «Continuar».
- Indicador de la animación de supertécnica: TP sustituido por PT.
- Pantalla de fichajes: botones de aceptar/volver y sí/no, confirmaciones de
  despedir o renunciar al fichaje, y etiquetas NV/PE/PT.

También se han preparado las pestañas Equipo/Reservas en sus cuatro estados y
el botón Datos; la confirmación precisa que el jugador sustituido dejará el
equipo. Se conservan las flechas y botones L/R originales.

Se han generado ocho texturas en tres archivos, comprobando tamaño, metadatos,
codificación gráfica reversible y límites de cada región. Vistas previas de
Continuar, PT y confirmaciones inspeccionadas. No se ha instalado este lote;
Azahar sigue usando v28.

Petición para más adelante: traducir los rótulos de las supertécnicas.
Siguen pendientes los otros elementos enumerados en
`REVISION_UI_IE1_2026-09-10.md`, especialmente etiquetas dinámicas de guardado,
menú principal y nombres de NPC. No ampliar ni alterar la tipografía para
resolver campos cortos.

Reproducción:

```text
python work/ui_followup/prepare.py
python tools/translate_ui_textures.py work/ui_followup/manifest.json --source work/menu_audit --base work/ui_followup/base --output work/ui_followup/extra --previews work/ui_followup/previews
python work/ui_followup/validate.py
```
