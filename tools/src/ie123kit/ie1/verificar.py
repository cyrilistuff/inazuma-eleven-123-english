"""Verificación estática de candidatas IE1 y de sus medios europeos.

Invariantes:
- toda entrada aportada por una capa coincide con esa capa (las posteriores ganan); el resto del
  contenedor, fuentes incluidas, es idéntico a la base; solo cambian los eventos SSD preparados y la
  CRO únicamente en los literales declarados;
- el audio instalado en Azahar es idéntico byte a byte a la fuente preparada y decodificable;
- los MOFLEX solo usan la disposición de rotación 0x16 y son decodificables;
- ``runtime_verified`` es siempre False: nada de esto sustituye la prueba en emulador.

Ni escribe informes por su cuenta (salvo ``escribir_informe_media``) ni imprime.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from ie123kit.nucleo.contenedores.fa import FaArchive
from ie123kit.nucleo.errores import ValidacionError
from ie123kit.nucleo.validar import candidata as V

__all__ = [
    "CRO",
    "EVE",
    "escribir_informe_media",
    "media_valida",
    "verificar_candidata",
    "verificar_media",
]

EVE = ('inazuma1/data_iz/script/eve.pkh', 'inazuma1/data_iz/script/eve.pkb')
CRO = 'romfs/cro/ina_main1.cro'


def verificar_candidata(base, candidata, capas=(), eventos=None, literales=None) -> dict:
    """Reproduce las comprobaciones de verify_candidate; lanza ValidacionError al primer fallo."""
    base = Path(base)
    candidata = Path(candidata)
    arc_base = FaArchive(str(base / 'archive.fa'))
    arc_cand = FaArchive(str(candidata / 'archive.fa'))
    if list(V.indice(arc_base)) != list(V.indice(arc_cand)):
        raise ValidacionError('lista_entradas', None, 'entry list changed')
    expected = V.cargar_capas([Path(c) for c in capas])
    replaced, fonts = V.comprobar_entradas(arc_base, arc_cand, expected, ignoradas=EVE)

    staged = {int(f.stem): f.read_bytes() for f in Path(eventos).glob('*.ssd')} if eventos else {}
    changed_events = V.comprobar_eventos_packnum(arc_base, arc_cand, EVE[0], EVE[1], staged)

    cro_a = (base / CRO).read_bytes()
    cro_b = (candidata / CRO).read_bytes()
    lits = json.loads(Path(literales).read_text(encoding='utf-8'))['entries'] if literales else []
    V.comprobar_literales_cro(cro_a, cro_b, lits)

    return {'candidate': str(candidata), 'archive_sha256': V.sha256_fichero(candidata / 'archive.fa'),
            'cro_sha256': hashlib.sha256(cro_b).hexdigest(), 'base_sha256': V.sha256_fichero(base / 'archive.fa'),
            'replaced_entries': replaced, 'fonts_identical_to_base': fonts,
            'events_changed': sorted(changed_events),
            'cro_literals_changed': len(lits) if cro_a != cro_b else 0, 'dialogue_lock': 'PASS',
            'runtime_verified': False}


# ----------------------------------------------------------------------------- medios


def verificar_media(raiz=None, instalado=None) -> dict:
    """Valida los medios europeos preparados e instalados; devuelve el report (sin escribirlo)."""
    if raiz is None:
        from ie123kit.nucleo.config.raiz import find_root
        raiz = find_root()
    REPO = Path(raiz)
    STAGE = REPO / "work" / "ie1" / "legacy" / "volumen_1" / "ie1_media_mod"
    STAGE_SOUND = STAGE / "romfs" / "inazuma1" / "data_iz" / "sound"
    STAGE_MOVIES = STAGE / "archive_extra" / "inazuma1" / "data_iz" / "movie"
    MOVIES_MANIFEST = STAGE / "movies_manifest.json"
    INSTALLED = (Path(instalado) if instalado is not None else
                 Path.home() / "AppData" / "Roaming" / "Azahar" / "load" / "mods" / "00040000000BB800" / "romfs")
    INSTALLED_SOUND = INSTALLED / "inazuma1" / "data_iz" / "sound"
    VGMSTREAM = REPO / "work" / "shared" / "herramientas" / "media_tools" / "vgmstream-nightly-win64" / "vgmstream-cli.exe"
    MOBIPEG = REPO / "work" / "shared" / "herramientas" / "media_tools" / "mobipeg-v2.1-x86" / "ffmpeg.exe"
    digest = V.sha256_fichero

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
            check=False,
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
    from ie123kit.nucleo.media.moflex import disposicion_rotacion as rotation_layouts
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
            encoding="utf-8", errors="replace", check=False,
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

    return {
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


def media_valida(report: dict) -> bool:
    """Sin fallos de audio ni de vídeo y con las 21 películas."""
    return not report["failures"] and not report["movie_failures"] and len(report["movies"]) == 21


def escribir_informe_media(report: dict, destino) -> Path:
    """Escribe el report como JSON UTF-8 (formato del validador original)."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destino
