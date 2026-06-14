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

🟢 **Build jugable v10** (estable, arranca y se juega) — **menús, nombres de
jugadores y equipos** (ambos juegos) + parte del **diálogo** (líneas sin furigana,
~30%), con acentos. Parche: [`patch/inazuma123-es-v10.xdelta`](patch/).

🧪 **v13 (experimental, a probar)** — intenta también el diálogo **con furigana**
preservando los marcadores `%NF` para no colgar el juego (causa raíz documentada en
[`docs/FORMATOS.md`](docs/FORMATOS.md) §"Estructura SSD"). Estructura verificada
offline; **pendiente de prueba visual**. Posible efecto cosmético (ruby kana
flotante) y muchas líneas largas se revierten al japonés por el límite de tamaño.
Parche: [`patch/inazuma123-es-v13.xdelta`](patch/). Si falla, usa v10.
Ver [`docs/PROGRESO.md`](docs/PROGRESO.md).

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
  [`translation/glossary/`](translation/glossary/).

## Cómo aplicar el parche (para jugadores)

> ⚠️ **Build de prueba PARCIAL (v5).** Traduce el **juego 1 y el juego 2**
> (el 3 sigue en japonés): diálogo de eventos (reúso del español oficial del NDS),
> **menús, nombres de jugadores y equipos**, todo **con acentos** (ñ, tildes, ¿¡).
> Quedan líneas sin equivalente oficial (en japonés) y objetos/técnicas pendientes.
> Mejora en cada versión.

**Requisitos:** tu **propia ROM legal**, **descifrada**, de *Inazuma Eleven 1·2·3!!
Endō Mamoru Densetsu* (3DS) — el parche está hecho contra la versión descifrada.
Y [`xdelta3`](https://github.com/jmacd/xdelta-gpl/releases).

**Aplicar el parche (recomendado: v10):**
```
xdelta3 -d -f -s "tu_rom.3ds" patch/inazuma123-es-v10.xdelta "inazuma123_es.3ds"
```
(las versiones anteriores v1-v5 siguen en `patch/` por si alguna diera problemas)
(o con una GUI tipo *xdelta UI*). Obtendrás `inazuma123_es.3ds`.

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

## Cómo contribuir

Lee [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) y el glosario antes de traducir.

## Créditos

- Traducción: comunidad (ver contribuyentes de GitHub).
- Herramientas de terceros usadas: ver [`tools/README.md`](tools/README.md).

## Aviso legal

Fan-project sin relación con Level-5 ni Nintendo. Inazuma Eleven © Level-5.
Ver [`LEGAL.md`](LEGAL.md).
