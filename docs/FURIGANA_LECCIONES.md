# Furigana / reinserción de diálogo — LO QUE NO FUNCIONA (y por qué)

> **LÉEME ANTES de tocar `tools/reinsert.py` o cambiar el manejo de furigana.**
> Cada enfoque de esta lista ya se probó **en emulador** y FALLÓ. No repetir.
> Cada línea está pagada con una build de ~15 min + una prueba del usuario.

## Resumen en una frase

El diálogo va en `eve.pkb` como **bytecode con texto inline**. Las palabras con
kanji llevan **furigana**: un marcador `%NF` en el texto + una **lectura** (kana) en
un chunk aparte (numerado `0x02..0x1f`). El motor consume **1 lectura por marcador y
por página (`\f`)**. La reinserción es **mismo-tamaño-en-bytes** (no se puede crecer
sin un desensamblador que recalcule offsets). Todo lo que rompa esa mecánica → cuelga.

## ❌ Enfoques que CUELGAN (no reintentar)

| # | Enfoque | Resultado | Por qué |
|---|---|---|---|
| 1 | **Quitar los marcadores `%NF`** del diálogo (texto español limpio) | **CUELGA al crear partida** (v12, v24/STRIP) | El motor EXIGE los marcadores. Sin ellos, la apertura (ev 92010200) descuadra el consumo de lecturas y cuelga. **Los marcadores son obligatorios.** |
| 2 | Marcadores al **final** de la línea (trailing) | CUELGA (v13) | `%NF` intenta dibujar ruby sobre el carácter *siguiente*, que no existe → fuera de límites. |
| 3 | Marcador seguido de **espacios de 1 byte** (half-width) | CUELGA (v14/v15/v16) | `%NF` espera **N caracteres de ANCHO COMPLETO** (2 bytes, como los kanji). Con 1 byte el motor se desalinea. |
| 4 | Rellenar páginas ES vacías para casar el conteo (`%NF` sin texto detrás en una página) | CUELGA al crear partida (v20) | Una página solo-marcadores/vacía descuadra el motor. |
| 5 | Traducir chunks donde el **nº de páginas `\f` ES ≠ JP** | CUELGA (v16/v19/v20) | El reparto de marcadores por página deja de casar 1:1. **Solución: solo traducir si `es.count(\f)==jp.count(\f)`; si no, dejar en japonés.** |
| 6 | Dejar un **`%NF` huérfano** dentro del texto español (venía de algunas líneas `auto-ia`/`revisar`) | CUELGA en zonas concretas (v18/v21/v23) | El marcador suelto, sin N chars de ancho completo detrás, descuadra. **Solución: `reinsert` quita cualquier `%NF` del ES antes de codificar.** |
| 7 | Cargar un **save state del emulador** hecho con OTRA build | "Cuelga" siempre | NO es bug nuestro: los save states guardan memoria de una build concreta. **Probar siempre con partida NUEVA.** |
| 8 | **[Longitud variable]** offset-fixup que actualiza **cualquier u32** que coincida con un inicio de chunk | **Error Fatal al avanzar el 1er diálogo** (build var inicial) | Muchos **operandos numéricos** del bytecode (p.ej. `1000`, coordenadas, IDs) coinciden por casualidad con una posición de inicio de chunk → el fixup los "recoloca" (`1000→972`) y **corrompe el evento**. Esos valores apuntan a **chunks vacíos** (NUL consecutivos) o a **diálogo** (que se consume secuencialmente, nunca por offset). **Solución: solo actualizar offsets cuyo destino sea un chunk TIPADO (`part[0]` 0x01–0x1f: lectura furigana / debug / control) o un BYTE-ID (1 byte ≥0x80).** Ver `_is_ref_target()` en `reinsert_var.py`. Pasó de corromper decenas de u32/evento a ~7 referencias reales/evento. |
| 9 | **Hacer CRECER una línea con furigana** (reinyectar marcadores + texto ES más largo) | **Error Fatal al AVANZAR** (no al mostrar: la línea se ve completa) | El evento queda perfecto a nivel de datos (1 sola ref de texto, recolocada; sin campos de longitud) pero el **runtime del motor de ruby se descuadra** con el diálogo más largo. NO editable desde el evento. **RE-CONFIRMADO (2026-06) con el offset-fixup PRECISO nuevo** (`GROW_INTRO`/`grow_fg`): el dato valida 100% pero **sigue crasheando al avanzar** → es del runtime, no de los datos. **Solución: NO hacer crecer líneas con furigana.** En español el furigana no aporta → en HISTORIA se hace **STRIP** (quitar marcador + vaciar lectura + texto completo); en SISTEMA/INTRO se deja a **mismo tamaño** (=v25). **`tools/validate.py` ahora lo CAZA** (chunks con %NF que crecen) y el build aborta → no se compila una ROM con este crash. |
| 10 | **REUBICAR** una línea de furigana (aunque NO crezca) por hacer crecer **otra** línea del mismo evento | **Texto vacío + no cierra el diálogo + se congela** (NPC de サークル棟エリア / 92010510) | Si un evento de sistema/intro conserva furigana pero crece una línea PLANA suya, todo lo que va detrás (incluidas las líneas de furigana) **se desplaza**. Reubicar una línea de furigana rompe el ruby igual que hacerla crecer (mismo runtime de ❌#9), aunque su contenido no cambie. **Solución: los eventos que conservan furigana (sistema/intro, eid≥90000000) deben quedar a MISMO TAMAÑO en TODAS sus líneas** (planas incluidas) → byte-idénticos, no se reubica nada. Ver rama `not strip` en `reencode_var`. |
| 11 | **[Longitud variable]** offset-fixup que reubica un u32 según el **TIPO del chunk** al que apunta (`_is_ref_target`: tipo 0x01–0x1f o byte-id) | **Error Fatal `unmapped Read32 @ … PC 0x001C8D68`** a los ~20 min (al hablar con cierto NPC) | El tipo del chunk NO distingue una referencia de un operando numérico: el diálogo (tipo 0x01) **nunca se referencia** y muchísimos **contadores/índices** del bytecode coinciden por azar con una posición de diálogo (839/901 eventos game1). El fixup los convertía en offsets grandes → un handler los usa como **contador** y lee un array de u32 hasta salirse de la RAM (`Read32` secuencial). **Solución (la que funciona): identificar los slots de string por ESTADÍSTICA, no por tipo.** El bytecode es un stream `<u16 idx><u16 len><u32 opcode><operandos>` (ver FORMATOS.md); un `(opcode,slot)` es offset-de-string si sus valores caen SIEMPRE en inicio de chunk o 0 y **casi nunca a media cadena**. Reubicar SOLO esos. Validado offline: **0 operandos numéricos alterados**. Ver `build_string_slots()`/`_instr_operands()` en `reinsert_var.py` (sustituye a `_is_ref_target`). |

## ✅ Enfoque ACTUAL (build var STRIP-historia): texto completo + furigana solo en intro

Tras confirmar que **hacer crecer una línea con furigana CUELGA al avanzar** (❌#8,
límite del runtime de ruby — el evento queda perfecto pero el motor se descuadra con
el diálogo más largo) y que **quitar furigana CUELGA al crear partida** (❌#1, solo en
los eventos de apertura), la estrategia que combina ambas restricciones:

- **HISTORIA** (`eid < 90000000`): **STRIP** — quitar marcadores `%NF`, **crecer el
  texto a longitud COMPLETA** (sin cortes) y **vaciar las N lecturas siguientes**
  (espacios, mismo tamaño; conservan su byte de tipo 0x02+ → el motor las ignora).
  En español el furigana no aporta nada. → **texto ES completo y limpio.**
- **SISTEMA/INTRO** (`eid >= 90000000`, incl. club 92010100): **FURIGANA_INPLACE a
  MISMO tamaño** (= v25): marcadores por página + N espacios ancho completo, solo
  páginas `\f` que casan, sin `%NF` huérfano, sin truncar marcadores. NO crecer (❌#8).
  Conservar el furigana aquí evita el cuelgue del crear-partida (❌#1).

`reinsert_var.py` `reencode_var(strip=eid<90000000)`. Reparto game1: **706 ev /
10613 líneas completas** (88%) + 315 ev / 1419 líneas furigana (intro/sistema).

**Estado:** PENDIENTE confirmar en emulador (build var STRIP-historia). Lo anterior
(`FURIGANA_INPLACE` mismo-tamaño en TODO, v23/v25) arranca, crea partida y muestra
diálogo en español, pero **trunca** (este es justo el problema que STRIP-historia
resuelve para el grueso del juego).

### Hechos confirmados del bytecode (offline, evento 92010100)
- La sección de texto tiene **una sola** referencia a la zona que se mueve (`code+2960`
  = byte-id `0xbc` antes de la lectura れんしゅう); el offset-fixup ya la recoloca bien.
- **No hay campos de longitud/offset-de-final** del diálogo en el bytecode (no existe
  `len`/`end` que actualizar al crecer). Los u32 que caen en `[first_change,tlen)` y
  coinciden con un inicio de chunk son **constantes de opcode** (273/819/305/529…),
  NO punteros: reubicarlos corrompe el evento. Por eso `_is_ref_target` solo toca
  cadenas tipadas/byte-id. ⇒ a nivel de DATOS el evento queda correcto al crecer; el
  cuelgue de ❌#8 es del **runtime** del motor, no editable desde el evento.

## ⚠️ Problemas ABIERTOS del enfoque que funciona (v23/v25)

### 1. Texto cortado (truncado)
El presupuesto **mismo-tamaño** + el coste de los rellenos de ancho completo dejan
poco espacio → frases recortadas ("Vaya, entr" en vez de "Vaya, a entrenar"). 
**Solución real: longitud variable** (`tools/reinsert_var.py` + `fa_repack.py` +
`build_3ds_var.py`) → reconstruye el contenedor con eventos más grandes.

**Modelo de referencias del evento SSD (clave para el redimensionado).** La sección
de texto (`d[s10:]`) es una secuencia de records separados por NUL:
`<byte-id><NUL><cadena tipada><NUL>...`. Hay tres clases:
- **Diálogo** (`part[0]`=0x01, estilo): se **consume SECUENCIALMENTE** (el motor lo
  recorre NUL→NUL). **Nunca se referencia por offset** → se puede agrandar libremente.
- **Lecturas furigana / strings de debug / control** (`part[0]` 0x02–0x1f, p.ej.
  `01_3.SAD`, `れんしゅう`) y sus **byte-id** (1 byte ≥0x80 que las precede): **SÍ se
  referencian por offset** (u32 rel a `s10`) desde el bytecode `d[:s10]`.
- **Chunks vacíos** (NUL consecutivos): nunca son destino de referencia.

Al agrandar el diálogo, todo lo que va detrás se desplaza; hay que **sumar el delta a
cada offset del bytecode que apunte a una lectura/debug/byte-id movido** (offset-fixup).
**Solo a esos** (ver ❌ #8): tocar operandos numéricos coincidentes cuelga el juego.

### 2. BUG (CAUSA REAL HALLADA): controles bloqueados al hablar con NPC en `サークル棟エリア`
- **Síntoma:** al hablar con un NPC de la zona, el diálogo **no muestra texto y no se
  cierra**; el juego NO crashea (sonido + sprites siguen vivos) pero **los controles se
  bloquean**. Afecta a TODA la zona, no a un NPC suelto.
- **Causa REAL (verificada offline):** **desincronización marcador `%NF` ↔ lectura
  furigana**. El motor consume **1 lectura por cada marcador**. El STRIP quitaba los
  marcadores de las líneas traducidas pero **VACIABA las lecturas dejándolas como chunks**
  (tipo 0x02 + espacios). Resultado en ev **92010510**: **0 marcadores pero 29 chunks de
  lectura** huérfanos en el stream → el motor los lee como líneas vacías / se descuadra
  y nunca cierra el diálogo. (El STRIP "vaciar" NO arreglaba el bug, solo lo disfrazaba.)
- **SOLUCIÓN (la que funciona):** **ELIMINAR** (no vaciar) las lecturas de cada línea
  traducida, hasta la siguiente línea de diálogo (flag `drop_readings` en `reencode_var`).
  Así marcadores y lecturas quedan **balanceados** como en el original (zona club: de 28
  chunks huérfanos → 0). Es viable gracias al **offset-fixup preciso por slot** (ver ❌#11):
  al borrar chunks, las referencias string se reubican; si alguna apunta a un chunk
  borrado, el evento revierte a japonés (seguro). Validado offline: 0 operandos numéricos
  alterados, 0 referencias nuevas rotas. **PENDIENTE confirmar en emulador.**
- Nota: `STRIP_ZONA` y el rango `92010510..92011000` siguen marcando qué zonas se STRIPean
  (post-intro, seguras); el fix de arriba corrige CÓMO se hace el strip de las lecturas.

### 3. BUG ya resuelto (NO reintentar la causa): cuelgue al CREAR PARTIDA
- **Síntoma (v24/STRIP, v12):** al crear partida nueva se congela en el título/carga,
  no llega a crear la partida.
- **Causa:** se **quitaron los marcadores `%NF`** del diálogo (modo STRIP) → el evento
  de apertura (92010200) descuadra el consumo de lecturas y cuelga.
- **Cómo evitarlo:** **NUNCA quitar los marcadores.** Usar `FURIGANA_INPLACE`
  (conservarlos, ancho completo, por página). Los marcadores son OBLIGATORIOS.

## Herramientas de comunidad (qué cubren y qué no)

- **Tiniifan/CfgBinEditor**, **Tiniifan/Nyanko**, **StudioElevenLib/Pingouin**:
  manejan `.cfg.bin` (menús, objetos, técnicas, stats) — **útiles para los MENÚS**.
- **NINGUNA** maneja el script de evento `.pkb` (formato SSD) con furigana del 3DS →
  ese pipeline es custom (nuestro). No buscar ahí una solución al diálogo.

## Método para depurar un cuelgue nuevo (rápido)

1. Build **sin furigana** (sin flags) = estable → confirma si el cuelgue es del furigana.
2. `work/validate_furigana.py` → busca anomalías (marcador sin ancho completo, etc.).
3. Localizar el evento del NPC/zona (`work/dump_intro2.py`, buscar texto en `eve.pkb`).
4. Comparar el chunk original vs el transformado byte a byte.
5. Probar con **partida NUEVA** (nunca save states entre builds).
