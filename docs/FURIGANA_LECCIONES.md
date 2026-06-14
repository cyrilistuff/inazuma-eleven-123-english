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

## ✅ Lo que SÍ funciona (enfoque actual = `FURIGANA_INPLACE`, build v23)

- Conservar los marcadores `%NF`, repartidos **por página** igual que el original.
- Cada marcador seguido de **N espacios de ancho completo** (`　` U+3000, 2 bytes).
- **Solo** traducir chunks donde el nº de páginas `\f` coincide ES/JP (resto → japonés).
- Quitar cualquier `%NF` huérfano del texto español.
- Nunca truncar los marcadores: si no caben enteros, dejar la línea en japonés.

**Estado:** arranca, crea partida, **muestra el diálogo en español**. Validador
(`work/validate_furigana.py`) = 0 anomalías sobre 895 eventos.

## ⚠️ Problemas ABIERTOS del enfoque que funciona (v23/v25)

### 1. Texto cortado (truncado)
El presupuesto **mismo-tamaño** + el coste de los rellenos de ancho completo dejan
poco espacio → frases recortadas ("Vaya, entr" en vez de "Vaya, a entrenar"). 
**Solución real: longitud variable** (`tools/reinsert_var.py` + `fa_repack.py` +
`build_3ds_var.py`) → reconstruye el contenedor con eventos más grandes. En marcha.

### 2. BUG: cuelgue al hablar con NPC en `サークル棟エリア` (y quizá otras zonas)
- **Síntoma:** en una build con furigana (INPLACE: v21/v23/v25), al hablar con un NPC
  de esa zona el juego se cuelga (negro, no llega a abrir el cuadro de diálogo).
- **NO ocurre** en la build sin furigana (v22) → es **específico del furigana**.
- **Causa: AÚN SIN AISLAR.** NO es `%NF` huérfano ni mismatch de páginas; el
  validador (`work/validate_furigana.py`) da 0 anomalías. Hipótesis: puede estar
  ligado al **truncado** (mismo-tamaño corta algo a media) → la build de **longitud
  variable** (sin truncado) podría arreglarlo; PENDIENTE confirmar.
- **Cómo aislar:** crear build **sin furigana** (estable) para confirmar; localizar el
  evento del NPC buscando su japonés en `eve.pkb`; comparar chunk original vs
  transformado. No re-probar marcadores (ver tabla ❌).

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
