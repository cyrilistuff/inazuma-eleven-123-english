#!/usr/bin/env python3
"""Convierte las 21 películas de IE1 DS ES al lote MOFLEX de volumen 1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mods_to_moflex import DEFAULT_FONT, DEFAULT_MOBIPEG, convert, read_subtitles


REPO = Path(__file__).resolve().parents[1]
DS_MOVIE = REPO / "work" / "ie1_es" / "data_iz" / "movie"
DS_TEXT = DS_MOVIE / "txt" / "sp"
TARGET = (REPO / "work" / "volumen_1" / "ie1_media_mod" / "archive_extra" /
          "inazuma1" / "data_iz" / "movie")


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def sources() -> list[Path]:
    result = sorted(DS_MOVIE.glob("*.mods"), key=lambda path: path.name.casefold())
    regional = DS_MOVIE / "sp" / "am0102.mods"
    if not regional.is_file():
        raise FileNotFoundError(regional)
    result.append(regional)
    if len(result) != 21 or len({path.stem.casefold() for path in result}) != 21:
        raise ValueError(f"se esperaban 21 películas únicas y hay {len(result)}")
    return sorted(result, key=lambda path: path.stem.casefold())


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    report = []
    for number, source in enumerate(sources(), 1):
        target = TARGET / f"{source.stem}.moflex"
        subtitle_path = DS_TEXT / f"{source.stem}.dat"
        if not subtitle_path.is_file():
            raise FileNotFoundError(subtitle_path)
        print(f"[{number:02d}/21] {source.stem}", flush=True)
        frames, subtitle_count, descriptors = convert(
            source, target, DEFAULT_MOBIPEG, 28,
            subtitles_path=subtitle_path, font_path=DEFAULT_FONT, rotation=1,
        )
        report.append({
            "name": source.stem,
            "source": str(source.relative_to(REPO)).replace("\\", "/"),
            "source_sha256": sha256(source),
            "subtitles": str(subtitle_path.relative_to(REPO)).replace("\\", "/"),
            "subtitle_records": subtitle_count,
            "frames": frames,
            "rotation_descriptors": descriptors,
            "output": str(target.relative_to(REPO)).replace("\\", "/"),
            "output_size": target.stat().st_size,
            "output_sha256": sha256(target),
        })
    manifest = TARGET.parent.parent.parent.parent / "movies_manifest.json"
    manifest.write_text(json.dumps({"schema": 1, "movies": report}, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"OK: {len(report)} películas -> {TARGET.relative_to(REPO)}", flush=True)


if __name__ == "__main__":
    main()
