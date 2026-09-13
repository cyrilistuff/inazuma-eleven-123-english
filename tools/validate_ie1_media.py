#!/usr/bin/env python3
"""Valida los medios europeos de IE1 preparados e instalados en Azahar."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
STAGE = REPO / "work" / "volumen_1" / "ie1_media_mod"
STAGE_SOUND = STAGE / "romfs" / "inazuma1" / "data_iz" / "sound"
STAGE_MOVIES = STAGE / "archive_extra" / "inazuma1" / "data_iz" / "movie"
MOVIES_MANIFEST = STAGE / "movies_manifest.json"
INSTALLED = Path.home() / "AppData" / "Roaming" / "Azahar" / "load" / "mods" / "00040000000BB800" / "romfs"
INSTALLED_SOUND = INSTALLED / "inazuma1" / "data_iz" / "sound"
VGMSTREAM = REPO / "work" / "media_tools" / "vgmstream-nightly-win64" / "vgmstream-cli.exe"
MOBIPEG = REPO / "work" / "media_tools" / "mobipeg-v2.1-x86" / "ffmpeg.exe"
REPORT = REPO / "work" / "probe_ie1_v35" / "media_validation.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def rotation_layouts(path: Path) -> list[int]:
    data = path.read_bytes()
    values = []
    pos = 0
    while True:
        pos = data.find(b"\x4c\x32", pos)
        if pos < 0:
            return values
        if pos + 29 <= len(data) and data[pos + 14:pos + 16] == b"\x03\x0d":
            values.append(data[pos + 28])
        pos += 2


def main() -> None:
    if not VGMSTREAM.is_file():
        raise FileNotFoundError("Ejecuta antes tools/setup_vgmstream.ps1")
    staged = sorted(STAGE_SOUND.glob("*.SAD"), key=lambda p: p.name.casefold())
    if len(staged) != 70:
        raise ValueError(f"Se esperaban 70 SAD preparados; hay {len(staged)}")

    rows = []
    failures = []
    for source in staged:
        target = INSTALLED_SOUND / source.name
        source_hash = digest(source)
        target_hash = digest(target) if target.is_file() else None
        decoded = subprocess.run(
            [str(VGMSTREAM), "-i", "-O", str(target)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        ) if target.is_file() else None
        ok = target_hash == source_hash and decoded is not None and decoded.returncode == 0
        row = {
            "name": source.name,
            "sha256": source_hash,
            "installed_match": target_hash == source_hash,
            "decoder_exit": decoded.returncode if decoded else None,
        }
        rows.append(row)
        if not ok:
            failures.append({**row, "decoder_stderr": decoded.stderr[-1000:] if decoded else "missing"})

    if not MOBIPEG.is_file():
        raise FileNotFoundError("Ejecuta antes tools/setup_mobipeg.ps1")
    manifest = json.loads(MOVIES_MANIFEST.read_text(encoding="utf-8"))
    expected_movies = {item["name"]: item for item in manifest["movies"]}
    movies = []
    movie_failures = []
    for movie in sorted(STAGE_MOVIES.glob("*.moflex"), key=lambda path: path.name.casefold()):
        layouts = rotation_layouts(movie)
        decoded = subprocess.run(
            [str(MOBIPEG), "-hide_banner", "-loglevel", "error", "-i", str(movie),
             "-map", "0:v:0", "-an", "-f", "null", "-"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace",
        )
        item = expected_movies.get(movie.stem)
        ok = (item is not None and item["output_sha256"] == digest(movie) and
              decoded.returncode == 0 and bool(layouts) and set(layouts) == {0x16})
        row = {
            "name": movie.name,
            "sha256": digest(movie),
            "manifest_match": item is not None and item["output_sha256"] == digest(movie),
            "rotation_descriptors": len(layouts),
            "layouts": sorted(set(layouts)),
            "decoder_exit": decoded.returncode,
        }
        movies.append(row)
        if not ok:
            movie_failures.append({**row, "decoder_stderr": decoded.stderr[-1000:]})
    if set(expected_movies) != {path.stem for path in STAGE_MOVIES.glob("*.moflex")}:
        movie_failures.append({"manifest_names": sorted(expected_movies),
                               "staged_names": sorted(path.stem for path in STAGE_MOVIES.glob("*.moflex"))})

    report = {
        "schema": 1,
        "checked_sad": len(rows),
        "valid_sad": len(rows) - len(failures),
        "failures": failures,
        "checked_movies": len(movies),
        "valid_movies": len(movies) - len(movie_failures),
        "movie_failures": movie_failures,
        "movies": movies,
        "files": rows,
        "runtime_verified": False,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("checked_sad", "valid_sad", "failures",
                                             "checked_movies", "valid_movies", "movie_failures")}, indent=2))
    if failures or movie_failures or len(movies) != 21:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
