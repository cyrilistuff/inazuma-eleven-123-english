# Arquitectura del proyecto

La recopilación *Inazuma Eleven 1·2·3!! Endō Mamoru Densetsu* es **un único juego de 3DS**
(`archive.fa` + `ina_main1.cro`) que contiene tres juegos: IE1, IE2 (Fuego / Ventisca) e IE3
(Rayo Celeste / Fuego Explosivo / La amenaza del Ogro). Por eso cada carpeta se divide en:

- `shared/`: lo que pertenece a la recopilación entera (la base 3DS, las candidatas `archive.fa`, las releases, las herramientas externas, el glosario común).
- `ie1/`, `ie2/`, `ie3/`: lo propio de cada juego (sus fuentes oficiales, capas de traducción, QA).
- Dentro de `ie2/` e `ie3/`, una subcarpeta por versión (`tormenta_de_fuego`, `ventisca_eterna`, `rayo_celeste`, `fuego_explosivo`, `amenaza_del_ogro`) para lo que difiere entre versiones, y `shared/` para lo común a las versiones de ese juego.

## Árbol

```
Roms/                         (git lo ignora; nunca se sube)
  shared/                     recopilación 3DS japonesa (.3ds, .cia)
  ie1/                        Inazuma Eleven NDS ES, IE1 3DS europeo (CTR-N-JEUP)
  ie2/tormenta_de_fuego/      NDS ES
  ie2/ventisca_eterna/        NDS ES
  ie3/fuego_explosivo/        IE3 3DS europeo (Bomb Blast)

translation/                  (en git: solo glosarios y CSV de términos)
  shared/glossary/            equipos, jugadores, técnicas, objetos, menús comunes
  ie1/  ie2/  ie3/            diálogo alineado y términos propios de cada juego

tools/                        herramientas (compartidas: formatos, compresión, CRO, texturas, vídeo)

work/                         (git lo ignora)
  shared/
    base_3ds/romfs, exefs     RomFS/ExeFS japoneses originales: base de todo parche. No se borra.
    candidatas/probe_ie1_vNN  archive.fa + CRO construidos (solo las dos últimas)
    releases/                 paquetes de releases publicadas
    herramientas/media_tools  mobipeg x86, vgmstream
    trailer/                  proyecto del tráiler
  ie1/
    fuentes/nds_es            ROM NDS española extraída. No se borra.
    fuentes/3ds_eu            IE1 3DS europeo extraído (es/, voces, cinemáticas, code_dec.bin). No se borra.
    capas/vNN/<linea>/        capa de cada tanda: apply.py, validate.py, extra/, events/, previews/, informes
    qa/                       capturas y registros de pruebas en juego
    legacy/                   carpetas de trabajo anteriores a esta organización (siguen leídas por algún script)
  ie2/{tormenta_de_fuego,ventisca_eterna,shared}/
  ie3/{rayo_celeste,fuego_explosivo,amenaza_del_ogro,shared}/
```

Al empezar IE2/IE3 se repite el patrón de `ie1/`: `fuentes/`, `capas/vNN/`, `qa/`, dentro de la versión
cuando el recurso es propio de ella o en `ieN/shared/` cuando es común a las versiones.

## Reglas

1. **Nada nuevo en la raíz de `work/`**. Lo nuevo va en `work/ieN/capas/vNN/<linea>/` o, si es de la
   recopilación entera, en `work/shared/`. Pruebas e imágenes sueltas: scratchpad de la sesión.
2. Las candidatas se llaman `probe_ie1_vNN` y viven en `work/shared/candidatas/`, porque un `archive.fa`
   contiene los tres juegos.
3. Una capa lee su base de `work/shared/candidatas/probe_ie1_v(NN-1)` y escribe solo dentro de su carpeta.
4. En los scripts, la raíz del repo se calcula con `Path(__file__).resolve().parents[N]`; al mover una capa
   hay que ajustar `N` (lo hizo `tools/_archivo/reorganizar_proyecto.py` en la migración del 2026-09-16).
5. **Antes de construir**: ≥ 4 GB libres. **Al instalar**: comprobar el hash del `archive.fa` copiado.
   **Después**: `python tools/limpiar_work.py --borrar`.

## Limpieza

`python tools/limpiar_work.py` lista lo que sobra y con `--borrar` lo elimina: candidatas salvo las dos
últimas, `.3ds` reconstruidas de releases publicadas, `fuentes/` intermedias de cinemáticas, `__pycache__`,
`*.partial`, `*.yuv`, `*_x2.png` y logs de comprobación. No toca `Roms/`, `shared/base_3ds`, `ieN/fuentes`,
capas con scripts, `docs/` ni `tools/`.
