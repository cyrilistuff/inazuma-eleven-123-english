# Tanda v36 — diálogos emparejados por ID y nombres cortos oficiales

Base: candidata v35 (`bcee069a…3f17df9e`: v33 + audio europeo + 21 cinemáticas localizadas).
Motivo: reportes de jugadores sobre diálogos incorrectos y el nombre de Max (issues #35 y #36).
Referencia única: la ROM NDS española (`work/ie1/fuentes/nds_es`). Tipografía v20 bloqueada: el bloqueo pasa.

## 1. Diálogos (#36, `work/ie1/capas/v36/dialogo_ids`)

**Causa.** `tools/ds_official.py` alineaba el diálogo NDS con el 3DS por orden de líneas. Cada
frase tiene un identificador de instrucción, y en 621 eventos la NDS lleva instrucciones de más
que desplazan los identificadores: todas las frases posteriores quedaban corridas una posición.
Además, parte del texto de la v33 no venía del oficial y tenía traducciones rotas o nombres sin
localizar («Suele estar en ribera de baños cerca», «profesora Fuyukai» por Wintersea).

**Emparejado.** Se alinea el patrón de saltos entre identificadores consecutivos, que es idéntico
en ambas ROMs, y se valida con anclas ASCII (nombres de archivo, variables): 12.617 idénticas
frente a 72 distintas (99,4 %). Formato en `docs/EVENT_SCRIPT_FORMAT.md`.

**Inventario sobre la v35** (`prepare.py`), 18.031 diálogos con referencia NDS:

| Clase | Registros | Acción |
|---|---|---|
| igual a la NDS | 7.063 | nada |
| editado (parecido ≥ 0,55) | 5.585 | se respeta |
| **desplazado** (es otra frase del mismo evento) | 234 | frase oficial |
| **distinto** (ni la suya ni otra) | 4.904 | frase oficial |
| protegido (crear partida 92010100..92010509, 81000040) | 245 | nada |

**Aplicado** (`apply.py`): **4.823 registros en 761 eventos** (231 desplazados, 4.592 distintos),
maquetados con `dialogue_lock.approved_layout` y codificados a ancho completo.

**No aplicados, pendientes de condensar a mano** (`no_caben.json`, se quedan como estaban):
- 299 frases oficiales superan los 247 bytes del registro de texto
- 15 con apóstrofo o comillas: no tienen glifo en las fuentes NFTR
- 1 con una palabra más ancha que la línea

**Validación** (`validate.py`): PASS. Sección de código byte-idéntica, misma identidad de cada
registro, solo cambian los 4.823 declarados, re-codificación exacta, mismos `%s`/`%d` que el
japonés, sin japonés ni marcas de furigana, ida y vuelta LZ10.

## 2. Nombres (#35, `work/ie1/capas/v36/nombres`)

**Causa.** El 3DS pinta en el recuadro del hablante el campo `+16` de `unitbase.dat`. La NDS guarda
en `+32` el nombre corto oficial (Max, Timmy, King, Styx, Creepy…), que casi nunca es la primera
palabra del nombre completo. Desde la v14, `+16` llevaba esa primera palabra («Maxwell», «Tim»).

**Aplicado:** 1.797 nombres (1.469 completos, 328 recortados a 7 caracteres por decisión del
usuario, p. ej. «Winters», «Tomlins»). 139 ya estaban bien. 20 apellidos «O'…» se escriben sin
apóstrofo («OReilly»): ni `'` ni `’` tienen glifo en las fuentes NFTR. Solo cambia `+16`;
`+0`/`+32` intactos (issue #16). 463 registros sin nombre NDS válido no se tocan.

## Candidata

```
python work/ie1/capas/v36/dialogo_ids/prepare.py
python work/ie1/capas/v36/dialogo_ids/apply.py
python work/ie1/capas/v36/dialogo_ids/validate.py
python work/ie1/capas/v36/nombres/apply.py
python tools/build_ui_revision.py --base work/shared/candidatas/probe_ie1_v35/archive.fa --ui work/ie1/capas/v36/dialogo_ids \
    --output work/shared/candidatas/probe_ie1_v36/archive.fa --extra work/ie1/capas/v36/nombres/extra \
    --cro work/shared/candidatas/probe_ie1_v35/romfs/cro/ina_main1.cro
python tools/verify_candidate.py --base work/shared/candidatas/probe_ie1_v35 --candidate work/shared/candidatas/probe_ie1_v36 \
    --layer work/ie1/capas/v36/nombres/extra --events work/ie1/capas/v36/dialogo_ids/events
```

- `archive.fa`: `ebc1230b5bfc2a448c2f0232dea9a1fddd6ee3c4bca957efd3a885fa4ea4bb00`
- CRO idéntico a v35: `44d4e206…bfe113a4`
- `verify_candidate`: 1 reemplazo (`unitbase.dat`), 22 fuentes idénticas, 761 eventos declarados,
  0 literales del CRO, bloqueo tipográfico PASS
- 2026-09-15: instalada en Azahar (con Azahar cerrado); los 70 SADL europeos se conservan.

## Pendiente

- **Prueba en juego** según `docs/PROTOCOLO_QA_IE1.md`. Riesgo principal: 87 de los desplazados y
  parte de los distintos están en eventos de sistema (≥ 90000000). Comprobar además el recuadro
  del hablante con Max, Timmy y los rivales de la Royal Academy (King, Samford, Drent).
- Condensar las 315 frases de `no_caben.json` respetando el sentido oficial.
- Revisar la clase «editado»: el umbral 0,55 puede dejar pasar algún nombre sin localizar.
