#!/usr/bin/env python3
"""Inventaría y prepara el audio europeo de IE1 DS para LayeredFS de 3DS.

Los recursos extraídos y el mod generado permanecen en ``work/``. La herramienta
no toca la ROM original ni ``archive.fa``: los ``.SAD`` de IE1 están fuera del
contenedor y se pueden sobreponer directamente con LayeredFS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
from dataclasses import asdict, dataclass
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DS_SOUND = REPO / "work" / "ie1" / "fuentes" / "nds_es" / "data_iz" / "sound" / "sp"
CTR_SOUND = REPO / "work" / "shared" / "base_3ds" / "romfs" / "inazuma1" / "data_iz" / "sound"
DS_MOVIE = REPO / "work" / "ie1" / "fuentes" / "nds_es" / "data_iz" / "movie"
STAGE = REPO / "work" / "ie1" / "legacy" / "volumen_1" / "ie1_media_mod"
STAGE_SOUND = STAGE / "romfs" / "inazuma1" / "data_iz" / "sound"
STAGE_MOVIE = STAGE / "archive_extra" / "inazuma1" / "data_iz" / "movie" / "am0102.moflex"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class SadInfo:
    size: int
    channels: int
    sample_rate: int
    codec_flag: str
    loop: bool
    data_size: int
    start_offset: int
    sha256: str


def inspect_sad(path: Path) -> SadInfo:
    data = path.read_bytes()
    if len(data) < 0x58 or data[:4] != b"sadl":
        raise ValueError(f"{path}: no es un SADL válido")
    flags = data[0x33]
    rate_bits = flags & 0x06
    if rate_bits == 0x04:
        sample_rate = 32728
    elif rate_bits in (0x00, 0x02):
        sample_rate = 16364
    else:
        raise ValueError(f"{path}: frecuencia SADL desconocida (flags=0x{flags:02x})")
    return SadInfo(
        size=len(data),
        channels=data[0x32],
        sample_rate=sample_rate,
        codec_flag=f"0x{flags:02x}",
        loop=bool(data[0x31]),
        data_size=struct.unpack_from("<I", data, 0x40)[0],
        start_offset=struct.unpack_from("<I", data, 0x48)[0],
        sha256=sha256(path),
    )


def inventory() -> dict:
    if not DS_SOUND.is_dir():
        raise FileNotFoundError(f"Falta la extracción de IE1 DS: {DS_SOUND}")
    if not CTR_SOUND.is_dir():
        raise FileNotFoundError(f"Falta la extracción RomFS de 3DS: {CTR_SOUND}")

    ds_files = {p.name: p for p in DS_SOUND.glob("*.SAD")}
    ctr_files = {p.name: p for p in CTR_SOUND.glob("*.SAD")}
    common = sorted(ds_files.keys() & ctr_files.keys(), key=str.casefold)
    ds_only = sorted(ds_files.keys() - ctr_files.keys(), key=str.casefold)
    ctr_only = sorted(ctr_files.keys() - ds_files.keys(), key=str.casefold)

    pairs = []
    for name in common:
        pairs.append(
            {
                "name": name,
                "ds": asdict(inspect_sad(ds_files[name])),
                "ctr": asdict(inspect_sad(ctr_files[name])),
            }
        )

    ds_movies = {p.stem.casefold(): p.name for p in DS_MOVIE.glob("*.mods")}
    ds_movies.update({p.stem.casefold(): p.name for p in (DS_MOVIE / "sp").glob("*.mods")})
    return {
        "schema": 1,
        "source": {
            "nds_sound": str(DS_SOUND.relative_to(REPO)),
            "ctr_sound": str(CTR_SOUND.relative_to(REPO)),
            "nds_movie": str(DS_MOVIE.relative_to(REPO)),
        },
        "summary": {
            "nds_sad": len(ds_files),
            "ctr_sad": len(ctr_files),
            "matched_sad": len(common),
            "nds_only_sad": ds_only,
            "ctr_only_sad": ctr_only,
            "nds_movies": len(ds_movies),
        },
        "sad_pairs": pairs,
        "nds_movies": [ds_movies[key] for key in sorted(ds_movies)],
    }


def stage_audio(report: dict) -> None:
    STAGE_SOUND.mkdir(parents=True, exist_ok=True)
    wanted = {pair["name"] for pair in report["sad_pairs"]}

    for old in STAGE_SOUND.glob("*.SAD"):
        if old.name not in wanted:
            old.unlink()

    for name in sorted(wanted, key=str.casefold):
        source = DS_SOUND / name
        target = STAGE_SOUND / name
        shutil.copy2(source, target)
        if sha256(target) != sha256(source):
            raise RuntimeError(f"La copia no coincide: {target}")

    report["staged"] = {
        "layeredfs_sad": len(wanted),
        "layeredfs_sad_bytes": sum((STAGE_SOUND / name).stat().st_size for name in wanted),
    }
    if STAGE_MOVIE.is_file():
        report["staged"]["localized_movie"] = {
            "path": str(STAGE_MOVIE.relative_to(REPO)),
            "size": STAGE_MOVIE.stat().st_size,
            "sha256": sha256(STAGE_MOVIE),
            "source": "work/ie1/fuentes/nds_es/data_iz/movie/sp/am0102.mods",
            "note": "única variante visual dentro de movie/sp; convertida MODS a MOFLEX",
        }

    STAGE.mkdir(parents=True, exist_ok=True)
    manifest = STAGE / "manifest.json"
    manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Reserva la separación acordada sin extraer todavía IE2.
    (REPO / "work" / "ie3" / "fuego_explosivo").mkdir(parents=True, exist_ok=True)
    (REPO / "work" / "ie2" / "ventisca_eterna").mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", action="store_true", help="copia los 70 SAD europeos al mod local")
    args = parser.parse_args()

    report = inventory()
    if args.stage:
        stage_audio(report)

    summary = report["summary"]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.stage:
        print(f"Mod preparado en: {STAGE.relative_to(REPO)}")


if __name__ == "__main__":
    main()
