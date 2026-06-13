# Progreso del proyecto

Leyenda: ⬜ pendiente · 🟡 en curso · ✅ hecho

## Fase 0 — Infraestructura
- ✅ Diagnóstico de las ROMs (formato, cifrado, regiones)
- ✅ Estructura del repositorio + git init
- ✅ `.gitignore`, `README.md`, `LEGAL.md`
- 🟡 Conseguir/compilar herramientas (3dstool, ndstool, CfgBinEditor, Nyanko, xdelta3)

## Fase 1 — Extracción y mapeo
- ⬜ Extraer RomFS/ExeFS de la ROM 3DS (1·2·3)
- ⬜ Extraer sistema de archivos del Inazuma Eleven 1 (NDS, ES)
- ⬜ Extraer sistema de archivos del Inazuma Eleven 2 (NDS, ES)
- ⬜ **Mapa de textos** del juego 1 (NDS ES): dónde está cada cadena
- ⬜ **Mapa de textos** del juego 1 dentro de la ROM 3DS
- ⬜ **Emparejado (match)** entre cadenas NDS ES ↔ 3DS JP del juego 1

## Fase 2 — Glosario y terminología
- ⬜ Volcar terminología oficial ES de las NDS (personajes, técnicas, equipos)
- ⬜ Construir glosario maestro en `translation/glossary/`

## Fase 3 — Traducción
- ⬜ Juego 1
- ⬜ Juego 2
- ⬜ Juego 3
- ⬜ Interfaz / menús / sistema

## Fase 4 — Fuente y gráficos
- ⬜ Ampliar fuente (ñ, ¿ ¡, tildes) y tabla de anchos
- ⬜ Gráficos con texto incrustado

## Fase 5 — Build y release
- ⬜ Reinsertar y reconstruir la ROM
- ⬜ Pruebas en emulador (Lime3DS / Azahar)
- ⬜ Generar parche `.xdelta`
- ⬜ Primera release pública

## Notas de las ROMs (referencia)
| ROM | Plataforma | Región | Código | Tamaño |
|---|---|---|---|---|
| Inazuma Eleven 1·2·3 | 3DS (NCSD, descifrado) | JP | CTR-P-AETJ | 2 GB |
| Inazuma Eleven 1 | NDS | EU (ES) | YEES | 256 MB |
| Inazuma Eleven 2 (Tormenta de Fuego) | NDS | EU (ES) | BEES | 256 MB |
