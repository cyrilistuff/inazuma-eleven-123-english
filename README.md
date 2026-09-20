# Inazuma Eleven 1·2·3!! Endō Mamoru Densetsu — English patch project

This is an **early English localization fork** of
[luishidalgoa/inazuma-eleven-123-spanish](https://github.com/luishidalgoa/inazuma-eleven-123-spanish)
for the Japanese Nintendo 3DS compilation. The upstream project's tools,
research, and Spanish patch are credited to its original contributors.

**There is no English patch to download yet.** The inherited `.xdelta` files,
release packages, and most translation data are Spanish. Do not apply or
redistribute them as an English release. The current work begins with an English
translation workspace for Inazuma Eleven 1.

## Status and plan

1. Build an English text corpus using official English terminology where
   available. Keep Japanese identifiers and control codes intact.
2. Connect the English corpus to a separate build path. Remove Spanish text,
   textures, voice, and video from any candidate that claims to be English.
3. Verify text layout and play from a new save through the first practice match,
   then expand coverage and test further chapters.
4. Publish only a tested patch, never a ROM or extracted game assets.

See [the English work guide](docs/ENGLISH_PATCH.md) for the first translation
steps and current blockers. The upstream [development guide](docs/DESARROLLO.md)
and [format notes](docs/FORMATOS.md) describe the inherited tools and game data.

## Credits and legal note

Original Spanish project: **luishidalgoa** and **TitoGalan**. IE-repack:
**Javiju555**. This fan project is unaffiliated with LEVEL-5 or Nintendo.
You must provide your own lawful copy of the Japanese game to build or use a
future patch. No ROMs or extracted game assets belong in this repository.
