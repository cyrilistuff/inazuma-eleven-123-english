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

> ⚠️ **Build PARCIAL (v27).** Traduce el **juego 1 y el juego 2** (el 3 sigue en
> japonés): intro y diálogo de historia, menús, nombres de jugadores y equipos, todo
> **con acentos** (ñ, tildes, ¿¡). El intro va algo **truncado** y ~la mitad de las
> líneas sin traducción oficial se quedan en japonés (límite de datos, ver estado arriba).

**Requisitos:** tu **propia ROM legal**, **descifrada**, de *Inazuma Eleven 1·2·3!!
Endō Mamoru Densetsu* (3DS) — el parche está hecho contra la versión descifrada.
Y [`xdelta3`](https://github.com/jmacd/xdelta-gpl/releases).

**Aplicar el parche (v27, el último):**

La forma recomendada para usuarios es abrir DeltaPatcher y seleccionar la ROM
original en **Original file**, `patch/inazuma123-es-v27.xdelta` en **XDelta
patch** y un nombre nuevo para **Patched file**. La operación se explica paso a
paso en [`docs/DISTRIBUCION_DELTAPATCHER.md`](docs/DISTRIBUCION_DELTAPATCHER.md).

También se puede usar `xdelta3` directamente:

```
xdelta3 -d -f -s "tu_rom.3ds" patch/inazuma123-es-v27.xdelta "inazuma123_es.3ds"
```
Obtendrás `inazuma123_es.3ds` sin modificar la ROM original.

**Jugar:** abre `inazuma123_es.3ds` en **Lime3DS** o **Azahar** (File → Load File).

### Si no arranca (hashes IVFC/NCCH)
El parche sobrescribe datos sin recalcular los hashes internos del cartucho.
Lime3DS/Azahar **suelen ignorarlos** y arranca igual. Si tu emulador lo rechaza,
reconstruye la ROM recalculando hashes con [3dstool](https://github.com/dnasdw/3dstool):
```
3dstool -xtf 3ds "tu_rom.3ds" -0 part0.cxi --header ncsd.bin
3dstool -xtf cxi part0.cxi --romfs romfs.bin --exefs exefs.bin --header ncch.bin \
        --exh exh.bin --logo logo.bin --plain plain.bin
3dstool -xtf romfs romfs.bin --romfs-dir romfs            # extraer
#  -> aplica el parche a romfs/archive.fa (o usa el archive.fa parcheado)
3dstool -ctf romfs romfs_new.bin --romfs-dir romfs        # reconstruir (recalcula IVFC)
3dstool -ctf cxi part0.cxi --romfs romfs_new.bin --exefs exefs.bin --header ncch.bin \
        --exh exh.bin --logo logo.bin --plain plain.bin   # recalcula hash NCCH
3dstool -ctf 3ds salida.3ds -0 part0.cxi --header ncsd.bin
```
**Alternativa (LayeredFS):** en Lime3DS/Citra puedes cargar solo el `archive.fa`
parcheado como mod de RomFS sin tocar la ROM (carpeta `load/mods/<TitleID>/romfs/`).

## Cómo contribuir / retomar

- **Desarrollo (clonar, build, pipeline, flags):** [`docs/DESARROLLO.md`](docs/DESARROLLO.md)
- **Traducir texto (estilo, glosario):** [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)
- **Qué NO funciona (no repetir):** [`docs/FURIGANA_LECCIONES.md`](docs/FURIGANA_LECCIONES.md)
- **Formatos técnicos:** [`docs/FORMATOS.md`](docs/FORMATOS.md) · [`docs/EVENT_SCRIPT_FORMAT.md`](docs/EVENT_SCRIPT_FORMAT.md)
- **Avance:** [`docs/PROGRESO.md`](docs/PROGRESO.md)

## Créditos

- Traducción: comunidad (ver contribuyentes de GitHub).
- Herramientas de terceros usadas: ver [`tools/README.md`](tools/README.md).

## Aviso legal

Fan-project sin relación con Level-5 ni Nintendo. Inazuma Eleven © Level-5.
Ver [`LEGAL.md`](LEGAL.md).
