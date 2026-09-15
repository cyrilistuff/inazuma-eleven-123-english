# Tanda v30 — menú de la bolsa y sus pantallas

Base: candidata v29 instalada (`cbada7a4…9eaf465`). Issues #21 (seguimiento) y #22.
Petición del usuario (2026-09-11): continuar con lo que quedó fuera, empezando por
el menú que se abre con la bolsa («Objetos, Equipo…»), que seguía en japonés.
Tipografía v20 bloqueada: solo se editan texturas; ningún diálogo ni fuente cambia.

## Contenido

1. **Menú de la bolsa** (`a_menu/bag_b`, textura `menu_bag_mes_b01`): los 28 rótulos
   visibles en sus rectángulos QNA de 128×16, alineados a la izquierda como el
   original: Plantilla, Objetos, Tácticas, Información, Sistema, Guardar, Cambios,
   Equipamiento, Supertécnicas, Partido, Duelo, Blog, Fichero, Fichar, Fichajes,
   Uniforme, Historial, Torneo, Móvil, Abandonar y las versiones pequeñas (Órdenes,
   Pasión, Amistad…). Los literales japoneses del CRO con esas palabras están junto
   a tablas de código y no se tocan: el menú visible es la textura.
2. **Guía del sistema** (`system_b`): corrige traducciones erróneas de la tanda
   anterior (用語 «Puerta» → Glosario, 練習試合 «Entrenamiento» → Amistosos,
   イナビカリ → Centella, 技アタッチ → Asignar técnicas, ナイスボーナス →
   Bonificación) y traduce Altavoz/Auriculares (texto girado) y «Online».
3. **Pantallas que abre la bolsa** (`work/ie1/legacy/submenu_revision`):
   - Cambios (`select_player_b`): etiquetas, botones Sí/No/Cancelar/Aceptar en sus
     tres estados, títulos y pestañas Equipo/Reservas en sus cuatro estados.
   - Tácticas (`formation_b`): Banquillo, frase de pareja de supertécnica, botones
     Mover/Equipar/Volver y etiquetas de `nmes_b01` (renderizado sin suavizado por
     su alfa de 1 bit).
   - Fichar (`scout_b`): Sí/No/Elegir/Salir, Condiciones (Club, Posición,
     Habilidad, Afinidad), Amistad P, Nv. equipo, Maestro y Nombre.
   - Fichero (`binder_b`): nombres de los 13 equipos, Equipos rivales y Raimon.
     El índice por kana (あかさたな…) se conserva: ordena por la lectura japonesa.
   - Tienda (`shop_b`/`shop_t`): Comprar/Vender/Salir, Aceptar/Salir (también
     girados), Sí/No, pestañas Equipo/Reservas, No se vende, En posesión/Pasión.
   - Subida de nivel (`battle_member_b`): «¡Sube nivel!».

Método: el texto incrustado en caras planas se borra con el color de la cara
medido dentro del rango de filas y columnas donde ese color supera el 30 %, de
modo que marcos, biseles e iconos A/B/L/R no se pintan. Cada lote pasa
`work/ie1/legacy/menu_revision/validate.py`: fuera de los rectángulos declarados no cambia
ningún píxel, ni metadatos ni la geometría QNA; bloqueo tipográfico PASS.

## Pendiente que requiere decisión

- **Nombres de supertécnicas** (`command.STR`: 132 nombres y 114 descripciones) y
  **objetos** (`item.dat`: 253 nombres de 9 caracteres como máximo; `item.STR`:
  273 descripciones, muchas de manuales que citan técnicas). El diálogo oficial
  NDS solo confirma Mano celestial, Muralla infinita, Triángulo Z y Ruptura
  relámpago. Los nombres oficiales completos están en la ROM NDS española
  (`tools/extract_nds.ps1` + `tools/build_glossary.py`), que no está en el equipo.

## Reproducción

```text
python work/ie1/legacy/menu_revision/prepare.py
python tools/translate_ui_textures.py work/ie1/legacy/menu_revision/manifest.json --source work/ie1/legacy/menu_revision/base --base work/ie1/legacy/menu_revision/base --output work/ie1/legacy/menu_revision/extra --previews work/ie1/legacy/menu_revision/previews
python work/ie1/legacy/menu_revision/validate.py
python work/ie1/legacy/submenu_revision/prepare.py
python tools/translate_ui_textures.py work/ie1/legacy/submenu_revision/manifest.json --source work/ie1/legacy/submenu_revision/base --base work/ie1/legacy/submenu_revision/base --output work/ie1/legacy/submenu_revision/extra --previews work/ie1/legacy/submenu_revision/previews
python work/ie1/legacy/menu_revision/validate.py work/ie1/legacy/submenu_revision
python tools/build_ui_revision.py --base work/shared/candidatas/probe_ie1_v29/archive.fa --ui work/ie1/legacy/menu_revision --extra work/ie1/legacy/menu_revision/extra --extra work/ie1/legacy/submenu_revision/extra --cro work/shared/candidatas/probe_ie1_v29/romfs/cro/ina_main1.cro --output work/shared/candidatas/probe_ie1_v30/archive.fa
python tools/verify_candidate.py --base work/shared/candidatas/probe_ie1_v29 --candidate work/shared/candidatas/probe_ie1_v30 --layer work/ie1/legacy/menu_revision/extra --layer work/ie1/legacy/submenu_revision/extra
python work/ie1/legacy/vs_revision/install.py work/shared/candidatas/probe_ie1_v30
```

## Estado

2026-09-11: candidata `work/shared/candidatas/probe_ie1_v30/archive.fa` generada e **instalada** en
Azahar con Azahar cerrado y sin enviar entradas al emulador. Issue #23.

- `archive.fa` candidato e instalado: `447f2bd8b44081f5b039c62ce2f20f2fc315713c1106496d847a1eea430f31af`
- `ina_main1.cro`: el de v29, sin cambios (`4a73fb49…6fda9e19`).
- `tools/verify_candidate.py`: 9 entradas iguales a sus capas; el resto del archivo,
  las 22 fuentes, los eventos y el CRO idénticos a v29; bloqueo tipográfico PASS.
- Limpieza: se borró `work/shared/candidatas/probe_ie1_v28/archive.fa`; v29 se conserva como base de v30.

**No está verificada en juego.** Prueba sugerida: abrir la bolsa y entrar en
Plantilla/Cambios, Tácticas, Fichar, Fichero y una tienda; comprobar los botones
Sí/No/Aceptar/Cancelar en sus estados (normal, seleccionado, pulsado), las
pestañas Equipo/Reservas con L/R y la guía del sistema (Glosario, Amistosos).
