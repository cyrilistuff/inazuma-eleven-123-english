# Tanda v32 — blog, textos de partido y pantallas restantes

Base: candidata v31 instalada (`e19252b1…eb00f746`). Fuente oficial: ROM NDS española
extraída en `work/ie1_es/` (datos) y, para los textos del ejecutable, ARM9 descomprimido
con `tools/blz.py` en `work/ie1_es/bin/` (1.483 cadenas, solo local).
Tipografía v20 bloqueada: el bloqueo pasa en todos los pasos.

## Contenido

1. **Textos cortos de datos** (`work/misc_revision/apply.py`):
   - `livetalk.dat`: 24 gritos de partido oficiales (huecos de 7 caracteres; se
     acortan «¡Arriba!» → «¡Sube!», «¡Cachis!» → «¡Jolín!», etc.).
   - `games.STR`: los 9 objetivos que seguían en japonés (15 caracteres).
   - `gamerule.dat`: 9 objetivos, con la misma redacción aprobada en `games.STR`.
   - `schinfo.dat`: 14 nombres oficiales de escuela (9 caracteres).
2. **Futblog** (`blogpost.dat`, `blogres.dat`; `work/blog_revision`): 108 títulos,
   108 entradas y 94 comentarios. Mismo orden de registros en NDS y 3DS; 126 textos
   oficiales caben tal cual y 184 se condensan del oficial a las líneas del 3DS
   (17 caracteres por línea; título 1 línea, entrada 5, comentario 2; `%s` se
   conserva).
3. **Pantallas restantes** (`work/screens2_revision`, 30 texturas): fin de partido
   (Resultado/Tiros/Técnicas/Posesión/Goles, Seguir/Salir), «¡Sube nivel!» de
   resultados, blog (Futblog, cabecera, Anterior/Siguiente/Cerrar), uniformes
   (Selección de uniforme, avisos), capitán (Pasión/Calma/Apoyo, Capitán,
   Estrategia), carpeta superior, botón Volver compartido con guardado y conexión,
   centro Centella (cursos, descripciones y botones), entrenamiento especial (Tiro,
   Físico, Control, Defensa, Rapidez, Aguante, Valor), transferir técnicas
   (Recibir/Dar), barra PE/PT superior y avisos de penaltis.

## Pendiente

- Literales del menú de entrenamiento y otros mensajes del CRO: hay equivalentes
  oficiales en el ARM9 NDS, pero la capacidad es mínima y algunos literales pueden
  ser claves internas.
- `JinmyakuData.dat` (contactos) y `rpgtitle` (títulos): estructuras distintas en NDS.
- Etiquetas «自分/相手» de uniformes, `fieldinf.dat` (nombres internos de campo).

## Estado

2026-09-11: candidata `work/probe_ie1_v32/archive.fa` generada e **instalada** en
Azahar con Azahar cerrado y sin enviar entradas al emulador.

- `archive.fa` candidato e instalado: `4043c5c979d4d5f272567edecfba6db96355ab06764d7c1f737567e9a8a7498a`
- `ina_main1.cro`: el de v31, sin cambios.
- `tools/verify_candidate.py`: 22 entradas iguales a sus capas; el resto del archivo,
  las 22 fuentes, los eventos y el CRO idénticos a v31; bloqueo tipográfico PASS.
- Validación: 310 textos del blog y todas las ranuras cortas dentro de su capacidad;
  30 texturas sin píxeles fuera de sus rectángulos QNA.
- El registro 5 del blog NDS repite por error el texto del registro 7; allí se sigue
  el japonés («%s ha abandonado el equipo»).
- Limpieza: se borró `work/probe_ie1_v30/archive.fa`; v31 se conserva como base.

**No está verificada en juego.** Prueba sugerida: menú de la bolsa → Blog (título,
entradas y comentarios), un partido completo (gritos, penaltis, pantalla final y
subida de nivel), elegir capitán y uniforme, centro Centella y entrenamiento especial.

## Reproducción

```text
python work/misc_revision/apply.py
python work/blog_revision/build_worklist.py
python work/blog_revision/check.py work/blog_revision/chunk_0*.json
python work/blog_revision/apply.py
python work/screens2_revision/prepare.py
python tools/translate_ui_textures.py work/screens2_revision/manifest.json --source work/screens2_revision/base --base work/screens2_revision/base --output work/screens2_revision/extra --previews work/screens2_revision/previews
python work/menu_revision/validate.py work/screens2_revision
python tools/build_ui_revision.py --base work/probe_ie1_v31/archive.fa --ui work/misc_revision --extra work/misc_revision/extra --extra work/blog_revision/extra --extra work/screens2_revision/extra --cro work/probe_ie1_v31/romfs/cro/ina_main1.cro --output work/probe_ie1_v32/archive.fa
python tools/verify_candidate.py --base work/probe_ie1_v31 --candidate work/probe_ie1_v32 --layer work/misc_revision/extra --layer work/blog_revision/extra --layer work/screens2_revision/extra
python work/vs_revision/install.py work/probe_ie1_v32
```
