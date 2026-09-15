# Tanda v37 — gráficos de la NDS en la interfaz

Base: candidata v36 (`ebc1230b…a4bb00`). Issue #37. Fuente única: ROM NDS española (`work/ie1_es`).
Línea: `work/v37/graficos_nds` (`piezas_nds.py`, `apply.py`, `validate.py`, `previews/`).

## Dónde están los gráficos en la NDS

- `pic3d/sp/*.SPL|SPD`: pares SFP con sprites PAC de 4 bpp **con nombre** (`tools/legacy_sprite.py`).
- `pic2d/**/*.pac_`: PAC del motor 2D = paleta + mapa de teselas u16 + teselas 8x8 de 4 bpp.
  El ancho del mapa no va en el archivo (fondos: 32 teselas).
- `pic2d/**/*.SPF_`: maquetaciones de escena (colocan PAC por nombre), no contienen imágenes.
- «PE» naranja y «Niv.» azul **no existen** como sprites sueltos en la NDS (buscado en SFP, PAC 2D,
  PAC 3D sueltos y binarios).

## Cambios (11 texturas, 5 archivos)

| Textura 3DS | Antes | Ahora (pieza NDS) |
|---|---|---|
| `select_player_b`, `select_captain_b` · `pos_icon` | M / F / D / G | MD / DL / DF / PR en vertical (letras de `menu_member/NID_I00`, ancho nativo por ranura) |
| `status_t` · `st_mes01` | Tiro … Experiencia (letra lisa) | rótulos cian de `msup_bg02` (… «EXP.») con sombra de 1 px |
| `status_t` · `mes01` | LV, PE, PT · DEL, MED, DEF, POR | «Niv.» (`wc_result`, nativo), «PE» (compuesto con el alfabeto del «PT»), «PT» (`HWD_N01`) a x2 · distintivos DL/MD/DF/PR |
| `status_t` · `mes02`, `formation_b` · `frkz` | A / B / F / M | iconos de aire, bosque, fuego y montaña (`HWD_I03`) |
| `formation_b`, `teach_sp_move_b` · `mes_cmd` | Regate, Bloq., Tiro, Atajo | distintivos `HWD_I02` (Reg., Bloq., Tiro, Atajo) |
| `select_player_b`, `select_captain_b`, `teach_sp_move_b` · `mes_b01` | «Despedir», **«せってい»** | «Echar», «Opciones» |

Hallazgos: «せってい» seguía en japonés; las abreviaturas de posición de la ficha eran DEL/MED/DEF/POR
en vez de las oficiales DL/MD/DF/PR.

## Candidata

```
python work/v37/graficos_nds/apply.py
python work/v37/graficos_nds/validate.py
python tools/build_ui_revision.py --base work/probe_ie1_v36/archive.fa --ui work/v37/graficos_nds \
    --output work/probe_ie1_v37/archive.fa --extra work/v37/graficos_nds/extra \
    --cro work/probe_ie1_v36/romfs/cro/ina_main1.cro
python tools/verify_candidate.py --base work/probe_ie1_v36 --candidate work/probe_ie1_v37 \
    --layer work/v37/graficos_nds/extra
```

- `archive.fa`: `e1a2e93607a4d3d9348f3d64238acbbcd652e2414a508022c464b753a552376e`
- `validate.py` PASS (11/11, resto de cada .arc idéntico) · `verify_candidate` PASS (5 reemplazos,
  22 fuentes idénticas, 0 eventos, CRO idéntico, bloqueo tipográfico PASS)
- 2026-09-15: instalada en Azahar; 70 SADL conservados.

## Pendiente

- Prueba en juego (issues #35, #36, #37).
- «Niv.» a tamaño nativo NDS se ve pequeño junto a PE/PT (a x2 no cabe en la celda de 32 px).
- Otras pantallas aún con gráficos 3DS (revisión general del #37).
