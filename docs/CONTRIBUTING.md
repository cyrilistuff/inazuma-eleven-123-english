# Guía de contribución

Gracias por querer ayudar con la traducción. Lee esto antes de empezar.

## Reglas de oro

1. **Nunca subas ROMs ni contenido extraído** (ver [`LEGAL.md`](../LEGAL.md)).
   El `.gitignore` los bloquea; no lo desactives.
2. **Respeta el glosario.** Personajes, técnicas y equipos usan los **nombres
   europeos oficiales** en español. Consulta `translation/shared/glossary/` antes de
   inventar una traducción.
3. **Una cosa por commit / PR.** Facilita la revisión.

## Convenciones de estilo

- Español de España (es-ES), coherente con la localización oficial de DS.
- Usa `ñ`, tildes y signos de apertura `¿` `¡` (la fuente se ampliará para
  soportarlos; mientras no esté, marca con `TODO:FONT` las cadenas afectadas).
- Respeta los **códigos de control** y variables del juego (p. ej. `{0}`,
  saltos de línea, etiquetas). No los traduzcas ni borres.
- Cuidado con la **longitud**: muchos cuadros de texto tienen límite de
  caracteres/ancho. Si dudas, déjalo anotado.

## Flujo de trabajo del texto

1. El texto se exporta de la ROM a archivos editables en `translation/gameN/`.
2. Tradúcelo ahí (no edites binarios directamente).
3. Los scripts de `tools/` reinsertan el texto y reconstruyen la ROM.

## Glosario

Los CSV de `translation/shared/glossary/` tienen columnas:
`japones, ingles, espanol_oficial, notas`. Si encuentras un término sin entrada,
añádelo con la fuente (de qué juego/escena lo sacaste).
