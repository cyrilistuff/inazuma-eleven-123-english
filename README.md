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

🟡 **Fase inicial** — montaje de herramientas y mapeo de textos. Ver
[`docs/PROGRESO.md`](docs/PROGRESO.md).

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

> _(Pendiente de la primera release.)_

1. Consigue tu propia ROM legal de *Inazuma Eleven 1·2·3!! Endō Mamoru Densetsu* (3DS), descifrada.
2. Descarga el parche `patch/inazuma123-es.xdelta` de la sección *Releases*.
3. Aplícalo con [xdelta UI](https://www.romhacking.net/utilities/598/) o
   `xdelta3 -d -s tu_rom.3ds inazuma123-es.xdelta inazuma123_es.3ds`.
4. Juega en una consola con tu propia copia o en un emulador (Lime3DS / Azahar).

## Cómo contribuir

Lee [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) y el glosario antes de traducir.

## Créditos

- Traducción: comunidad (ver contribuyentes de GitHub).
- Herramientas de terceros usadas: ver [`tools/README.md`](tools/README.md).

## Aviso legal

Fan-project sin relación con Level-5 ni Nintendo. Inazuma Eleven © Level-5.
Ver [`LEGAL.md`](LEGAL.md).
