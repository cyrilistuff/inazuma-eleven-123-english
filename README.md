# Inazuma Eleven 1·2·3!! Endō Mamoru Densetsu — Traducción al español (fan-project)

Proyecto **no oficial, sin ánimo de lucro**, hecho por y para la comunidad, para
traducir al **español** la recopilación de Nintendo 3DS
*Inazuma Eleven 1·2·3!! Endō Mamoru Densetsu* (solo lanzada en Japón).

Inspirado en otros trabajos de la comunidad como las traducciones de
*Inazuma Eleven GO: Big Bang / Supernova*.

> ⚠️ **Aquí NO encontrarás la ROM del juego.** Este repositorio solo contiene el
> **parche** y las **herramientas/scripts** de la traducción. Necesitas aportar
> tu **propia copia legal** del juego. Lee [`LEGAL.md`](LEGAL.md).

## Estado del proyecto

🟡 **Desarrollo activo local** — la traducción IE1 se está retomando mediante
candidatas LayeredFS probadas en Azahar. La guía para continuar el trabajo está en
[`docs/REANUDAR_IE1.md`](docs/REANUDAR_IE1.md).

🟡 **Candidata v27 local**: incluye los diálogos visibles de los diez capítulos
de IE1, las zonas de Raimon y las variantes de NPC, además de pachangas, cadena
de partidos y Royal. La auditoría estática deja 0 japonés visible; sigue
pendiente el recorrido jugable completo desde una partida nueva. El parche
portable es [`patch/inazuma123-es-v27.xdelta`](patch/) y el detalle de cobertura
está en [`docs/PROGRESO.md`](docs/PROGRESO.md).

**Muros técnicos definitivos** (documentados en [`docs/FURIGANA_LECCIONES.md`](docs/FURIGANA_LECCIONES.md)):
parchear el código del juego es inviable (zona de relocalización del CRO); los eventos
de sistema/intro no pueden crecer (se truncan); y ~la mitad del diálogo no tiene datos
de traducción. No es un fallo del motor — es el techo real con lo que hay.

> 🛠️ **¿Quieres retomarlo o trabajar en él?** Empieza por
> **[`docs/DESARROLLO.md`](docs/DESARROLLO.md)**: clonar, requisitos, regenerar los datos
> que no están en git, el pipeline de build paso a paso y la tabla de flags.

## La ROM objetivo

| Campo | Valor |
|---|---|
| Plataforma | Nintendo 3DS |
| Código de producto | `CTR-P-AETJ` (edición japonesa) |
| Formato | NCSD (cartucho), **descifrado** |
| Contenido | Remaster de los juegos 1, 2 y 3 de la saga (DS) en un solo cartucho |

## Decisiones del proyecto

- **Convención de nombres:** se usan los **nombres europeos oficiales** en español
  (Mark Evans, Axel Blaze, Raimon, etc.), tomados de las versiones oficiales en
  castellano de Inazuma Eleven 1 y 2 (DS). Ver
  [`translation/shared/glossary/`](translation/shared/glossary/).

## Cómo aplicar el parche (para jugadores)

> **Versión 1.0.** Traduce **Inazuma Eleven 1** (historia, menús, objetos, técnicas y
> jugadores), con voces y cinemáticas en español, más la interfaz de la recopilación.
> Los juegos 2 y 3 siguen en japonés.

**Necesitas:** tu **propia copia legal** de *Inazuma Eleven 1·2·3!! Endō Mamoru Densetsu*
(3DS, CTR-P-AETJ), volcada y **descifrada**, en `.3ds` o `.cia`; el paquete
`inazuma123-es-v1.0-pack.zip` de [Releases](../../releases); la herramienta
**[IE-repack](https://github.com/Javiju555/IE-repack)** de Javiju555 para tu sistema; y
unos 12 GB libres.

**Pasos:**

1. Descomprime IE-repack entero (el ejecutable necesita su carpeta `sidecars` al lado) y
   descomprime este paquete en otra carpeta.
2. Abre IE-repack y elige el modo **Pack (manifiesto)**.
3. Como base, tu copia japonesa descifrada. Como pack, la carpeta `pack` del paquete
   (la que contiene `manifiesto.json`). Elige dónde guardar y pulsa el botón.
4. Abre el `.3ds` resultante en **Azahar** o **Lime3DS** con Archivo → Cargar archivo.

La herramienta comprueba el hash de cada archivo de tu copia antes y después de
parchear. Si tu volcado es de otra revisión, se detiene con un mensaje claro en vez de
generar una ROM defectuosa. Si dice **«ningún origen cuadra con el manifiesto»**, la copia
elegida no es la ROM japonesa original: no vale una ya traducida, ni una `.cia` cifrada,
ni otra región.

**Si usas la carpeta de mods de Azahar** (`load/mods/<TitleID>/romfs/`), recuerda que sus
archivos tienen prioridad sobre cualquier ROM que cargues: desactívala para probar el
`.3ds` parcheado.

**Método antiguo (DeltaPatcher).** Las releases v1 y v1.1 siguen publicadas y se aplican
con DeltaPatcher sobre la ROM entera, pero exigen un volcado byte a byte idéntico al
nuestro; con cualquier otra revisión fallan. Se documentan en
[`docs/DISTRIBUCION_DELTAPATCHER.md`](docs/DISTRIBUCION_DELTAPATCHER.md).

## Cómo contribuir / retomar

- **Desarrollo (clonar, build, pipeline, flags):** [`docs/DESARROLLO.md`](docs/DESARROLLO.md)
- **Traducir texto (estilo, glosario):** [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)
- **Qué NO funciona (no repetir):** [`docs/FURIGANA_LECCIONES.md`](docs/FURIGANA_LECCIONES.md)
- **Formatos técnicos:** [`docs/FORMATOS.md`](docs/FORMATOS.md) · [`docs/EVENT_SCRIPT_FORMAT.md`](docs/EVENT_SCRIPT_FORMAT.md)
- **Avance:** [`docs/PROGRESO.md`](docs/PROGRESO.md)

## Créditos

- Dirección y traducción: **luishidalgoa**.
- Colaboración: **TitoGalan**.
- Herramienta de parcheo [IE-repack](https://github.com/Javiju555/IE-repack): **Javiju555**.
- Herramientas de terceros usadas: ver [`tools/README.md`](tools/README.md).

## Aviso legal

Fan-project sin relación con Level-5 ni Nintendo. Inazuma Eleven © Level-5.
Ver [`LEGAL.md`](LEGAL.md).
