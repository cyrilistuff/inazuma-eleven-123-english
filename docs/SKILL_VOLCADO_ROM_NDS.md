---
name: volcado-rom-nds
description: Checklist y lecciones para volcar y verificar la localización de Inazuma Eleven 1·2·3 (3DS) desde la ROM NDS española. Usar al traducir o auditar diálogos, nombres, rótulos, texturas de UI, iconos, teclado, eventos, doblaje, cinemáticas o subtítulos, o al preparar una candidata vN.
---

# Volcado y análisis desde la ROM NDS → 3DS

Referencia única: la ROM NDS española extraída en `work/ie1_es` (`data_iz/…`, `bin/strings.txt`).
Original japonés 3DS: `work/v33/base/orig/…`. Nada extraído se sube (Norma 2). Leer antes
`CLAUDE.md`, `AGENTS.md` y `docs/FURIGANA_LECCIONES.md`.

## 0. Antes de tocar nada

- Issue de GitHub para la tanda (Norma 1). Comentar al terminar; no cerrar sin prueba en juego.
- Candidata nueva = capa nueva `work/vN/<linea>/` (apply.py + validate.py + extra/ o events/ + previews/).
  Base = candidata anterior instalada, nunca una más vieja: cada capa acumula sobre la previa.
- Tipografía v20 bloqueada (`tools/dialogue_lock.py`): no cambiar caja, fuentes, codificación ni saltos.
- No acumular builds: borrar las candidatas viejas que el usuario diga.

## 1. Inventario: qué hay que volcar

| Qué | 3DS | NDS (fuente oficial) | Clave de emparejado |
|---|---|---|---|
| Diálogo de eventos | `script/eve.pkb` (SSD) | `script/sp/evet.pkb` | **ID de instrucción** alineado por patrón de saltos + anclas ASCII |
| Nombre del hablante | `unitbase.dat +16` | `unitbase.dat +32` (nombre corto) | índice de registro |
| Nombre completo | `unitbase.dat +0/+32` | — | **no tocar** (issue #16) |
| Rótulo de lugar del minimapa | `eve.pkb` op `0x4037` arg 3 | `bin/strings.txt` | texto japonés original |
| Objetivos | `eve.pkb` op `0x402f` arg 2/3 | última línea imperativa del evento NDS | evento |
| Campos de partido | `fieldinf.dat +144` (20 B) | `fieldinf.dat` | índice |
| Títulos / Contactos | `rpgtitle.STR`, `JinmyakuData.dat` | equivalentes NDS | índice |
| Literales del ejecutable | `cro/ina_main1.cro` | `bin/` | referencia verificada en código |
| Equipos | texturas | `translation/glossary/equipos.csv` | — |
| Teclado | `fcode0/1/2.txt` + `name_b` font_hira01/kana01 | — | rejilla de 20×20 px |
| Texturas de UI | `.arc` ARCV (SSZL) con CTPK | sprites SFP `pic3d/sp/*.SPL/SPD`, `pic2d/**/*.pac_` | celda del atlas |

## 2. Diálogos: método que funciona

- **Nunca emparejar por orden de líneas** (`tools/ds_official.py` lo hacía: 621 eventos desplazados).
  Usar `tools/audit_dialogo_ids.py`: IDs de instrucción, alineando la secuencia de *saltos* entre IDs con
  difflib y validando con anclas ASCII (12.617 iguales / 72 distintas).
- Clasificar: igual / editado (parecido ≥ 0,55, se respeta) / desplazado / distinto / protegido.
  Protegidos: crear partida `92010100..92010509` y `81000040`.
- Límite de registro de texto 247 B; `%s`/`%d` deben coincidir con el japonés; sin furigana.
- Apóstrofo y comillas **no tienen glifo** en NFTR: «O'Reilly» → «OReilly». Lo que no quepa va a
  `no_caben.json` para condensar a mano, no se trunca.
- **Los registros de rótulo/objetivo comparten eventos con el diálogo**: una tanda de diálogo puede
  meter frases largas en rótulos (`0x4037`). Excluir esos opcodes o medirlos después (sección 4).

## 3. Nombres

- Hablante = `unitbase.dat +16`, máx. 7 caracteres de ancho completo + NUL. El nombre NDS está en
  `+32`, casi nunca es la primera palabra del completo (Max, Timmy, King…). Recortar a 7 si el usuario lo pide.

## 4. Medir en píxeles, no en caracteres

- Avances de `font/FONT12.NFTR` con `tools/nftr_metrics.read_metrics` (claves Shift-JIS).
- Hueco disponible = ancho del japonés original más ancho del mismo tipo de texto
  (rótulo del minimapa: 117 px). Todo lo que lo supere se desborda en juego.
- Script de referencia: `work/v39/estado/medir_rotulos.py`. Validar la candidata con él.

- **Nombres de equipo, supertécnicas y objetos**: se vuelcan por ID desde la NDS (`team.pkb`,
  `command.STR`, `item.dat`), pero después hay que **medir cada nombre contra el hueco de su pantalla**.
  El cuadro de equipo pinta con paso fijo: máximo 11 caracteres (el japonés más largo).

## 4b. Literales del CRO

- Hueco = del inicio al siguiente dato **y** sin referencias dentro (`work/v33/cro/analysis/crorefs.py`).
- Solo ancho completo (las métricas ASCII de las fuentes solo tienen el espacio).
- **No superar el número de caracteres del japonés** si a continuación va un número u otro texto: el
  juego lo pinta en posición fija («Jug.» se montaba con «10»).
- **El juego copia el literal a un búfer del tamaño del japonés**: más bytes que el original salen como
  basura («Niv. Equ?7&», «Ran»). Límite real = longitud en bytes del japonés.
- **Nunca dejar un literal vacío**: pinta basura («*&»). Usar un espacio de ancho completo.

## 5. Texturas de UI: checklist por pantalla

0. Colocar cada pieza en su **rectángulo QNA** (`tools/qna_regions.py`), no en la celda de 16/32/64 px,
   con la alineación y el ancho del japonés; auditar con `work/v42/auditoria/celdas.py`.
1. Volcar **todas** las texturas del `.arc` (no solo las ya pintadas) de la candidata actual y del
   original japonés; hoja ampliada con rejilla de 16 px (`work/v38/estado/`).
2. Por cada texto: ¿japonés visible, resto de trazo, artefacto, término no oficial, texto cambiado?
   El informe `work/v33/tex_residual/report.json` está desfasado: comprobar sobre la candidata.
3. **Buscar primero la pieza NDS** (`work/v37/graficos_nds/piezas_nds.py`):
   - posiciones DL/MD/DF/PR: `menu_member/NID_I00`
   - afinidad aire/bosque/fuego/montaña: `menu_special_comand/HWD_I03` (sustituye 風林火山)
   - tipos de técnica: `HWD_I02`; «PT»: `HWD_N01`
   - rótulos cian Tiro…Valor/EXP.: `pic2d/menu/sp/msup_bg02.pac_` (mapa de 32 teselas)
   - capitán Pasión/Calma/Seguir y «Táctica»: `captainselect/CSDN_B01`, `CSDN_W02`
   - `.SPF_` son layouts, no imágenes; pac de equipos/jugadores no son UI.
4. Si no hay pieza NDS: pintar en español con el estilo de la textura (`translate_ui_textures.paint`,
   `arialbd`, `crisp` para alfa de 1 bit) y comprobar que no se sale de la celda.
5. Comparar con el **original japonés** cuando algo parezca raro: así se vio que `ts001lp/rp` eran
   1P/2P (no «Raimon») y que las barras estaban cortadas.
6. Grep global de nombres de textura parecidos (`top_plt`, `attribute`…) para no dejar copias en otras pantallas.

### Trampas de texturas (ya pasaron)

- `paint()` **rellena su caja con `background`**: si hay fondo debajo, pintar en una capa transparente y
  componer, o pasar el color real del fondo.
- Color dominante: **ignorar píxeles con alfa 0** (el transparente es `(255,32,230,0)`).
- No mover coordenadas de atlas ni tamaños; `metadata(CTPK)` idéntica y códec ida y vuelta.
- Al recortar piezas NDS, dejar fuera los bordes del botón origen (aparecen barras laterales).
- Extraer glifos de otra textura: limitar la región y quitar píxeles aislados.
- Heredoc de bash convierte `\0`/`\x01` en bytes reales dentro de `.py`: escribir con la herramienta Write.

## 6. Teclado de nombre

- `fcodeN.txt`: 26 celdas × 6 filas + CRLF; cada letra ocupa 2 celdas, hueco tras la 5.ª, `AAAA` cambia
  modo, `DDDD` borra.
- La **rejilla de selección es de 20×20 px** (fila k en y = 20k, controles en x 200–224). Pintar filas de
  16 px descuadra el cursor y hace pulsar la fila vecina (issue #38). La flecha de borrar debe estar en
  mayúsculas y minúsculas.

## 7. Doblaje, cinemáticas y subtítulos

Docs: `docs/IE1_AUDIO_CINEMATICAS_V34.md`, `docs/IE1_AUDIO_CINEMATICAS_V35.md`.
Herramientas: `tools/ie1_media.py`, `tools/mods_to_moflex.py`, `tools/build_ie1_movies.py`,
`tools/validate_ie1_media.py`, `tools/audit_ie1_voiced_text.py`.

### Inventario

| Qué | NDS ES (`data_iz/`) | 3DS | Instalación |
|---|---|---|---|
| Voces / música de escena | `sound/sp/*.SAD` (72) | 70 SADL con el mismo nombre | **LayeredFS** en `romfs/` del mod (fuera de `archive.fa`) |
| Cinemáticas | `movie/*.mods`, variante ES `movie/sp/am0102.mods` (21) | `movie/*.moflex` (21) | dentro de `archive.fa` |
| Subtítulos de cinemática | `movie/txt/sp/*.dat` (intervalos de fotogramas) | no existen: se incrustan en el vídeo | — |
| Texto de eventos con voz | `evet.pkb` | `eve.pkb` | auditar con `audit_ie1_voiced_text.py` |

- `J18.SAD`/`J19.SAD` solo existen en DS: no se instalan.
- SADL: copiar el archivo europeo **entero, sin recodificar**; la frecuencia va en su cabecera
  (ES 32728 Hz, JP 16364 Hz). Comprobar byte a byte y descodificar con vgmstream.
- Cada build nueva debe **conservar los 70 SAD** en la carpeta del mod (contar tras instalar).

### Vídeo

- `mods_to_moflex.py`: YCgCo DS → YCbCr y giro 256×192 → 240×320.
- Descriptor de sincronía **layout 0x16** (Simple2D, ImageRotation 1). Con 0x06 el vídeo sale girado.
- Usar **mobipeg x86**; la x64 falla con vídeo complejo en Windows.
- Descodificar cada MOFLEX completo después de generarlo.

### Subtítulos sin retraso (checklist)

1. **Unidad de los `.dat`**: confirmar si los intervalos son fotogramas del vídeo o ticks de 60 Hz.
   El incrustado actual compara con el índice de fotograma (`item.start <= frame <= item.end`). Si son
   ticks, hay que escalar por `fps_vídeo / 60` o el subtítulo llega tarde y se alarga.
2. **fps**: el MOFLEX debe declarar el mismo `r_frame_rate` que el `.mods` de origen. Nunca forzar
   24 fps sobre un origen distinto: el vídeo, y con él el subtítulo, deriva respecto a la voz.
3. **No perder ni duplicar fotogramas** en la conversión: el número de fotogramas MOFLEX debe ser igual
   al del `.mods` (p. ej. am0102 = 361).
4. **Voz frente a vídeo**: la voz es un SAD que el juego lanza aparte. Comparar la duración del SAD
   con la del vídeo, y el primer subtítulo con el primer tramo con voz del SAD (energía > umbral).
   Una diferencia sistemática indica unidad o fps mal interpretados, no un fallo de texto.
5. Generar una **tira de control** por cinemática (fotograma de inicio y fin de cada subtítulo con su
   marca de tiempo) y revisarla antes de construir.
6. Prueba en juego: opening, `am0102` y al menos una narrativa. Comprobar orientación horizontal,
   subtítulos españoles, sincronía con la voz y ausencia de cortes.

## 8. Construir, verificar, instalar

```
python work/vN/<linea>/apply.py
python work/vN/<linea>/validate.py          # solo cambian las texturas/registros declarados
python tools/build_ui_revision.py --base work/probe_ie1_v(N-1)/archive.fa --ui work/vN/<linea> \
    --extra work/vN/<linea>/extra --cro work/probe_ie1_v(N-1)/romfs/cro/ina_main1.cro \
    --output work/probe_ie1_vN/archive.fa
python tools/verify_candidate.py --base work/probe_ie1_v(N-1) --candidate work/probe_ie1_vN \
    --layer work/vN/<linea>/extra [--events work/vN/<linea>/events]
```

- PASS esperado: reemplazos = los declarados, 22 fuentes idénticas, CRO idéntico, bloqueo PASS.
- Instalar solo con Azahar cerrado: copiar `archive.fa` a
  `%APPDATA%/Azahar/load/mods/00040000000BB800/romfs`; comprobar que siguen los 70 `.SAD` de audio.
- Revisar **visualmente cada preview** antes de construir; corregir y repetir.
- Documentar en `docs/IE1_VN_TANDA.md`: tabla antes/ahora/origen, lo que «se queda» con motivo, sha,
  comandos. Comentar el issue.

## 9. Cierre

- `runtime_verified=false` hasta que el usuario pruebe (`docs/PROTOCOLO_QA_IE1.md`).
- Dar al usuario una lista corta de qué probar y dónde.
- Fallo nuevo o enfoque que no funciona → añadirlo a `docs/FURIGANA_LECCIONES.md` y a esta skill.
