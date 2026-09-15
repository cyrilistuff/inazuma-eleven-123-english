# Tanda v31 — técnicas, objetos y equipos con nombres oficiales

Base: candidata v30 instalada (`447f2bd8…a430f31af`). Issues #22 y #23.
El usuario aportó la ROM NDS española de Inazuma Eleven (código `YEES`) en `Roms/`;
se extrajo localmente a `work/ie1_es/` (ignorado por Git) con `tools/nds_unpack.py`.
Tipografía v20 bloqueada: el bloqueo pasa en todos los pasos.

## Fuente oficial y emparejado

- **Técnicas**: `command.dat` comparte el orden de ID en ambas versiones
  (3DS: registros de 24 B con punteros nombre/descripción en +16; NDS: 28 B, +20).
- **Objetos**: mismo índice (3DS 32 B, nombre de 19 B y descripción en +30;
  NDS 48 B, nombre de 32 B y descripción en +46).
- **Equipos**: `team.pkb` de 320 B; iguales hasta el registro 31 y desplazados uno
  a partir del 32 (la NDS inserta un equipo). Glosario versionado:
  `translation/glossary/equipos.csv` (solo nombres cortos).
- Decodificador NDS ampliado (`tools/build_glossary.py`): Á, Í, comillas Shift-JIS y
  «~» usado como ordinal.

## Contenido

1. **Supertécnicas** (`command.STR`): 131 nombres oficiales (30 abreviados para caber
   en 15 caracteres, p. ej. «Trampol. relám.», «Escudo total») y 114 descripciones
   condensadas del texto oficial a dos líneas.
2. **Rótulos de supertécnica en partido** (`command_technique` bc/bg, 261 texturas):
   nombre oficial con el aspecto original (letras en bloque, contorno blanco, sombra
   gris; rojo, azul o gris desactivado), comprimido en horizontal si hace falta para
   no salir de la zona visible. Sustituye también los 18 rótulos de la tanda anterior
   que no usaban los nombres oficiales (Finta → Regate, etc.).
3. **Objetos** (`item.dat`/`item.STR`): 307 nombres (límite de 9 caracteres: nombre
   oficial o abreviatura reconocible, p. ej. «Agua min.», «M.PE br.») y 300
   descripciones condensadas del oficial. Las descripciones vuelven a sus huecos
   originales; las que una tanda anterior añadió al final dejan de usarse.
4. **Equipos oficiales**: 130 nombres de `team.pkb` corregidos (Umbrella, Sallys,
   Ultra Zeus, Sumokas, Centella…), placas VS y del Fichero, y 5 diálogos que decían
   Kasamino o Zeus oscuro.

## Reproducción (recursos locales en `work/`, no publicar)

```text
python tools/nds_unpack.py "Roms/Inazuma Eleven (2011).nds" work/ie1_es
python work/tech_revision/build_worklist.py
python work/item_revision/build_worklist.py
python work/tech_revision/check.py work/tech_revision/worklist.json work/tech_revision/chunk_*.json
python work/tech_revision/check.py work/item_revision/worklist.json work/item_revision/chunk_*.json
python work/tech_revision/apply.py
python work/item_revision/apply.py
python work/team_revision/prepare.py
python tools/translate_ui_textures.py work/team_revision/manifest.json --source work/team_revision/base --base work/team_revision/base --output work/team_revision/extra --previews work/team_revision/previews
python work/menu_revision/validate.py work/team_revision
python work/team_revision/events.py
python work/banner_revision/prepare.py
python tools/translate_ui_textures.py work/banner_revision/manifest.json --source work/banner_revision/base --base work/banner_revision/base --output work/banner_revision/extra --previews work/banner_revision/previews
python work/menu_revision/validate.py work/banner_revision
python tools/build_ui_revision.py --base work/probe_ie1_v30/archive.fa --ui work/team_revision --extra work/team_revision/extra --extra work/tech_revision/extra --extra work/item_revision/extra --extra work/banner_revision/extra --cro work/probe_ie1_v30/romfs/cro/ina_main1.cro --output work/probe_ie1_v31/archive.fa
python tools/verify_candidate.py --base work/probe_ie1_v30 --candidate work/probe_ie1_v31 --layer work/team_revision/extra --layer work/tech_revision/extra --layer work/item_revision/extra --layer work/banner_revision/extra --events work/team_revision/events
python work/vs_revision/install.py work/probe_ie1_v31
```

## Pendiente

- Títulos RPG (`rpgtitle.STR`): el orden NDS no coincide; requiere su tabla `.dat`.
- Descripciones oficiales de jugadores (NDS): su tabla de punteros es distinta y el
  texto no cabe en dos líneas; se mantienen las condensadas de v29.
- Menú de entrenamiento Centella (CRO) y demás pantallas sin tocar (blog, uniforme,
  conexión, resultados de partido).

## Estado

2026-09-11: candidata `work/probe_ie1_v31/archive.fa` generada e **instalada** en
Azahar con Azahar cerrado y sin enviar entradas al emulador.

- `archive.fa` candidato e instalado: `e19252b1e6cc2ddf4a0b8b46c7baddea1182d7f7b87bcfae51bd8003eb00f746`
- `ina_main1.cro`: el de v30, sin cambios (`4a73fb49…6fda9e19`).
- `tools/verify_candidate.py`: 272 entradas iguales a sus capas; el resto del archivo
  y las 22 fuentes idénticos a v30; solo cambian los eventos 90000000 y 92030600;
  CRO sin cambios; bloqueo tipográfico PASS.
- Validación de textos: 245 de técnicas y 607 de objetos sin problemas; rótulos
  y texturas sin píxeles fuera de sus rectángulos (los 9 rótulos ETC1A4 borran con
  blanco transparente para que el color clave magenta no manche las letras).
- Limpieza: se borró `work/probe_ie1_v29/archive.fa`; v30 se conserva como base.

**No está verificada en juego.** Prueba sugerida: menú de la bolsa → Objetos y
Equipamiento (nombres y descripciones), Supertécnicas (nombres y descripciones),
un partido con supertécnicas para ver los rótulos, la tienda y el selector de
pachangas o torneo para los nombres de equipo (Umbrella, Sallys…).
