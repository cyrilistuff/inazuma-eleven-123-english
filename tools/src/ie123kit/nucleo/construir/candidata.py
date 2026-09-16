"""Construcción de una candidata por capas sobre un contenedor B123 base.

Traslado de ``tools/build_ui_revision.py`` (que queda CONGELADO en tools/ y no se toca: v55 hace
exec de su texto). ``digest``, ``archive_payload``, ``replace_entry`` y ``rebuild_events`` son copia
literal. ``construir`` reproduce su ``main()`` sin argparse ni print.

``construir`` está generalizada a las cuatro CRO de la recopilación (ina_menu, ina_main1,
ina_main2, ina_main3ogre), al reempaquetado de ``mch`` además de ``eve`` y a aportaciones por
objetivo, con la regla «la última capa gana».
"""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
from pathlib import Path

from ie123kit.nucleo.compresion.lz10 import compress, decompress
from ie123kit.nucleo.contenedores.fa import FaArchive, fe_offset_of
from ie123kit.nucleo.errores import ValidacionError
from ie123kit.nucleo.eventos import ssd as S
from ie123kit.nucleo.eventos.packnum import parse_index, rebuild

__all__ = ["CRO_CONOCIDAS", "archive_payload", "construir", "digest", "rebuild_events", "replace_entry"]


def digest(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def archive_payload(arc: FaArchive, path: str) -> bytes:
    for p, off, size in arc.entries:
        if p == path:
            return bytes(arc.d[off:off + size])
    raise ValueError(f"missing archive entry: {path}")


def replace_entry(handle, arc: FaArchive, path: str, payload: bytes) -> None:
    field = fe_offset_of(arc, path)
    if field is None:
        raise ValueError(f"missing archive entry: {path}")
    handle.seek(0, 2)
    handle.write(bytes((-handle.tell()) % 16))
    offset = handle.tell()
    handle.write(payload)
    handle.seek(field + 8)
    handle.write(struct.pack("<II", offset - arc.data_off, len(payload)))


def rebuild_events(arc: FaArchive, events_dir: Path):
    pkh_path = "inazuma1/data_iz/script/eve.pkh"
    pkb_path = "inazuma1/data_iz/script/eve.pkb"
    pkh = archive_payload(arc, pkh_path)
    pkb = archive_payload(arc, pkb_path)
    index = parse_index(pkh)
    by_id = {eid: (off, size) for eid, off, size in index}
    staged = {int(p.stem): p for p in events_dir.glob("*.ssd")}
    unknown = sorted(set(staged) - set(by_id))
    if unknown:
        raise ValueError(f"unknown staged event ids: {unknown}")

    output = bytearray()
    new_index = []
    report = []
    for eid, off, size in index:
        original_compressed = pkb[off:off + size]
        original = decompress(original_compressed)
        payload = original
        changed = 0
        if eid in staged:
            payload = staged[eid].read_bytes()
            # Copia literal de tools/build_ui_revision.py (fichero bloqueado v20); la
            # igualdad por AST la vigila test_construir_candidata.test_literalidad, así
            # que no se renombra old_end aunque no se use.
            old_end, old_instructions, old_records = S.parse(original)  # noqa: RUF059
            new_end, new_instructions, new_records = S.parse(payload)
            if old_instructions != new_instructions:
                raise ValueError(f"event {eid}: instruction table changed")
            if len(old_records) != len(new_records):
                raise ValueError(f"event {eid}: record count changed")
            for i, (old, new) in enumerate(zip(old_records, new_records)):
                if (old.instruction, old.argument) != (new.instruction, new.argument):
                    raise ValueError(f"event {eid}: record identity changed at {i}")
                if old.body != new.body:
                    changed += 1
            if new_end != 32 + struct.unpack_from("<I", payload, 16)[0]:
                raise ValueError(f"event {eid}: malformed SSD payload")
        compressed = compress(payload)
        if decompress(compressed) != payload:
            raise ValueError(f"event {eid}: LZ10 round-trip failed")
        new_index.append((eid, len(output), len(compressed)))
        output.extend(compressed)
        output.extend(bytes((-len(output)) % 4))
        if eid in staged:
            report.append({"event": eid, "records_changed": changed,
                           "old_compressed": len(original_compressed),
                           "new_compressed": len(compressed),
                           "source_sha256": digest(staged[eid])})

    new_pkh = bytearray(pkh[:0x30])
    for record in new_index:
        new_pkh.extend(struct.pack("<III", *record))
    struct.pack_into("<I", new_pkh, 0x10, len(new_pkh))
    return bytes(new_pkh), bytes(output), report


RUTA_EVE = ("inazuma1/data_iz/script/eve.pkh", "inazuma1/data_iz/script/eve.pkb")
RUTA_MCH = ("inazuma1/data_iz/script/mch.pkh", "inazuma1/data_iz/script/mch.pkb")

#: CRO de la recopilación (una por juego, más la del menú).
CRO_CONOCIDAS = ("ina_menu.cro", "ina_main1.cro", "ina_main2.cro", "ina_main3ogre.cro")


def _normalizar_aportaciones(aportaciones) -> list[dict]:
    """Admite una lista de aportaciones o un dict ``{objetivo: aportacion}``."""
    if aportaciones is None:
        return []
    if isinstance(aportaciones, dict):
        crudas = [{**v, "objetivo": v.get("objetivo", k)} for k, v in aportaciones.items()]
    else:
        crudas = list(aportaciones)
    normalizadas = []
    for cruda in crudas:
        if not isinstance(cruda, dict):
            raise TypeError(f"aportación no válida (se esperaba un dict): {cruda!r}")
        extra = cruda.get("extra")
        eventos = cruda.get("eventos") or {}
        cro = cruda.get("cro") or []
        if isinstance(cro, (str, Path)):
            cro = [cro]
        normalizadas.append({
            "objetivo": str(cruda.get("objetivo") or ""),
            "extra": Path(extra).resolve() if extra is not None else None,
            "eventos": {k: Path(v).resolve() for k, v in eventos.items() if v is not None},
            "cro": [Path(c).resolve() for c in cro],
        })
    return normalizadas


def _hay_ssd(directorio) -> bool:
    return directorio is not None and Path(directorio).is_dir() and any(Path(directorio).glob("*.ssd"))


#: Alineado de las entradas del .pkb reempaquetado; el mismo que usa ``rebuild_events`` para eve.
ALINEADO_PACKNUM = 4


def _ssd_preparados(directorio: Path) -> dict[int, Path]:
    """Mapa ``id de evento -> fichero`` de los ``.ssd`` de ``directorio`` (el nombre es el id).

    Equivale al ``{int(p.stem): p for p in events_dir.glob('*.ssd')}`` de ``rebuild_events``,
    pero un nombre que no sea un id numérico da un error con la ruta en vez de un ``ValueError``
    pelado de ``int()``.
    """
    preparados: dict[int, Path] = {}
    for ruta in sorted(Path(directorio).glob("*.ssd")):
        if not ruta.stem.isdigit():
            raise ValidacionError(
                "PACKNUM_SSD_SIN_ID",
                ruta=ruta,
                detalle="el nombre de un .ssd preparado debe ser el id numérico del evento",
            )
        preparados[int(ruta.stem)] = ruta
    return preparados


def _comprobar_ssd(eid: int, original: bytes, payload: bytes) -> int:
    """Valida un ``.ssd`` preparado contra el original y devuelve cuántos textos cambian.

    Mismas comprobaciones que ``rebuild_events`` (copia literal del congelado, que solo sabe de
    ``eve``): tabla de instrucciones intacta, mismo número de registros, misma identidad
    (instrucción/argumento) registro a registro y cabecera coherente. No se reutiliza
    ``rebuild_events`` porque su cuerpo está vigilado por ``test_literalidad``.
    """
    _, instrucciones_viejas, registros_viejos = S.parse(original)
    fin_nuevo, instrucciones_nuevas, registros_nuevos = S.parse(payload)
    if instrucciones_viejas != instrucciones_nuevas:
        raise ValueError(f"event {eid}: instruction table changed")
    if len(registros_viejos) != len(registros_nuevos):
        raise ValueError(f"event {eid}: record count changed")
    cambiados = 0
    for i, (viejo, nuevo) in enumerate(zip(registros_viejos, registros_nuevos)):
        if (viejo.instruction, viejo.argument) != (nuevo.instruction, nuevo.argument):
            raise ValueError(f"event {eid}: record identity changed at {i}")
        if viejo.body != nuevo.body:
            cambiados += 1
    if fin_nuevo != 32 + struct.unpack_from("<I", payload, 16)[0]:
        raise ValueError(f"event {eid}: malformed SSD payload")
    return cambiados


def _reempaquetar(arc: FaArchive, directorio: Path, rutas: tuple[str, str]):
    """Reempaqueta un PackNum (hoy ``mch``) desde una carpeta de ``.ssd`` preparados.

    ``rebuild_events`` (copia literal del congelado) solo sabe de ``eve`` y además lee el disco;
    ``packnum.rebuild`` es la primitiva parametrizada y NO toca el disco: recibe
    ``{id: bytes}``. Aquí se hace el paso que falta —leer los ``.ssd``, mapear nombre→id y
    validar tabla de instrucciones y registros contra el payload original— y después se llama a
    ``rebuild``. Devuelve ``(pkh, pkb, informe)`` con el informe en el mismo formato que
    ``rebuild_events``, para que ``events`` y ``events_mch`` se lean igual en el build.json.
    """
    pkh = archive_payload(arc, rutas[0])
    pkb = archive_payload(arc, rutas[1])
    indice = parse_index(pkh)
    por_id = {eid: (off, size) for eid, off, size in indice}
    preparados = _ssd_preparados(directorio)
    desconocidos = sorted(set(preparados) - set(por_id))
    if desconocidos:
        raise ValueError(f"unknown staged event ids: {desconocidos}")

    reemplazos: dict[int, bytes] = {}
    anotaciones: dict[int, dict] = {}
    for eid, ruta in sorted(preparados.items()):
        off, size = por_id[eid]
        original = decompress(bytes(pkb[off:off + size]))
        payload = ruta.read_bytes()
        reemplazos[eid] = payload
        anotaciones[eid] = {"records_changed": _comprobar_ssd(eid, original, payload),
                            "source_sha256": digest(ruta)}
    nuevo_pkh, nuevo_pkb, informe = rebuild(pkh, pkb, reemplazos, align=ALINEADO_PACKNUM)
    report = [
        {
            "event": entrada["evento"],
            "records_changed": anotaciones[entrada["evento"]]["records_changed"],
            "old_compressed": entrada["bytes_antes"],
            "new_compressed": entrada["bytes_despues"],
            "source_sha256": anotaciones[entrada["evento"]]["source_sha256"],
        }
        for entrada in informe
    ]
    return nuevo_pkh, nuevo_pkb, report


def _recoger_cro(ui, cro, aportaciones: list[dict]) -> list[tuple[Path, str]]:
    """Fuentes de CRO en orden de aplicación (la última capa gana)."""
    fuentes: list[tuple[Path, str]] = []
    if cro is not None:
        entradas = [cro] if isinstance(cro, (str, Path)) else list(cro)
        fuentes += [(Path(c).resolve(), "") for c in entradas]
    elif ui is not None:
        carpeta = Path(ui) / "romfs/cro"
        descubiertas = sorted(carpeta.glob("*.cro")) if carpeta.is_dir() else []
        if not descubiertas:
            descubiertas = [carpeta / "ina_main1.cro"]
        fuentes += [(p.resolve(), "") for p in descubiertas]
    for aportacion in aportaciones:
        fuentes += [(c, aportacion["objetivo"]) for c in aportacion["cro"]]
    return fuentes


def construir(base, salida, *, ui=None, capas=None, cro=None, aportaciones=None,
              rehusar_sobrescribir: bool = True) -> dict:
    """Construye la candidata ``salida`` (archive.fa) sobre ``base``; devuelve el report.

    ``capas`` son carpetas de ficheros relativos al archive (la última gana). ``aportaciones`` es
    la forma generalizada: una lista (o un dict por objetivo) de
    ``{objetivo, extra, eventos: {'eve': dir, 'mch': dir}, cro: [...]}``; se aplican después de
    ``capas``, también con la regla «la última gana», y quedan anotadas en el build.json.
    """
    base = Path(base).resolve()
    ui = Path(ui).resolve() if ui is not None else None
    output = Path(salida).resolve()
    if not base.is_file():
        raise FileNotFoundError(base)
    if output.exists() and rehusar_sobrescribir:
        raise FileExistsError(f"refusing to overwrite candidate: {output}")
    aportes = _normalizar_aportaciones(aportaciones)
    arc = FaArchive(str(base))

    # -- eventos (eve por el camino literal del congelado, mch por packnum.rebuild) --
    events_dir = ui / "events" if ui is not None else None
    for aporte in aportes:
        if _hay_ssd(aporte["eventos"].get("eve")):
            events_dir = aporte["eventos"]["eve"]
    staged_events = _hay_ssd(events_dir)
    event_report = []
    if staged_events:
        new_pkh, new_pkb, event_report = rebuild_events(arc, events_dir)
    mch_dir = None
    for aporte in aportes:
        if _hay_ssd(aporte["eventos"].get("mch")):
            mch_dir = aporte["eventos"]["mch"]
    mch_report = []
    if mch_dir is not None:
        mch_pkh, mch_pkb, mch_report = _reempaquetar(arc, mch_dir, RUTA_MCH)

    # -- capas de ficheros del archive --
    known = {p for p, _, _ in arc.entries}
    if capas:
        overlays = [(Path(p).resolve(), "") for p in capas]
    elif ui is not None:
        overlays = [(ui / "extra", "")]
    else:
        overlays = []
    overlays += [(a["extra"], a["objetivo"]) for a in aportes if a["extra"] is not None]
    extra_files = {}
    overridden = []
    for extra, objetivo in overlays:
        for src in sorted(extra.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(extra).as_posix()
            if rel not in known:
                raise ValueError(f"extra file is not an archive entry: {rel}")
            if rel in extra_files:
                anotacion = {"entry": rel, "overlay": str(extra)}
                if objetivo:
                    anotacion["objetivo"] = objetivo
                overridden.append(anotacion)
            extra_files[rel] = src.read_bytes()

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(base, output)
    with output.open("r+b") as handle:
        if staged_events:
            replace_entry(handle, arc, RUTA_EVE[0], new_pkh)
            replace_entry(handle, arc, RUTA_EVE[1], new_pkb)
        if mch_dir is not None:
            replace_entry(handle, arc, RUTA_MCH[0], mch_pkh)
            replace_entry(handle, arc, RUTA_MCH[1], mch_pkb)
        for rel, payload in sorted(extra_files.items()):
            replace_entry(handle, arc, rel, payload)

    # -- CRO: las cuatro de la recopilación, la última capa gana --
    destino_cro = output.parent / "romfs/cro"
    cros: dict[str, dict] = {}
    for fuente, objetivo in _recoger_cro(ui, cro, aportes):
        if not fuente.is_file():
            continue
        destino = destino_cro / fuente.name
        if fuente.name in cros:
            anotacion = {"entry": f"romfs/cro/{fuente.name}", "overlay": str(fuente.parent)}
            if objetivo:
                anotacion["objetivo"] = objetivo
            overridden.append(anotacion)
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fuente, destino)
        cros[fuente.name] = {
            "nombre": fuente.name,
            "origen": str(fuente),
            "destino": str(destino),
            "sha256": digest(destino),
            "objetivo": objetivo or None,
            "conocida": fuente.name in CRO_CONOCIDAS,
        }
    cro_principal = destino_cro / "ina_main1.cro"
    report = {
        "base": str(base),
        "base_sha256": digest(base),
        "archive": str(output),
        "archive_sha256": digest(output),
        "events": event_report,
        "events_staged": len(event_report),
        "archive_replacements": len(extra_files),
        "overridden_by_later_overlay": overridden,
        "cro": str(cro_principal) if cro_principal.is_file() else None,
        "typography": "v20 lock preserved",
        "runtime_verified": False,
        # Claves nuevas de F2.2 (las anteriores se conservan tal cual).
        "cros": [cros[n] for n in sorted(cros)],
        "events_mch": mch_report,
        "events_mch_staged": len(mch_report),
        "aportaciones": [
            {
                "objetivo": a["objetivo"],
                "extra": str(a["extra"]) if a["extra"] is not None else None,
                "eventos": {k: str(v) for k, v in a["eventos"].items()},
                "cro": [str(c) for c in a["cro"]],
            }
            for a in aportes
        ],
    }
    output.with_suffix(".build.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Construye una candidata por capas sobre un archive.fa base.")
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--ui", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extra", type=Path, action="append",
                        help="Overlay directory of archive-relative files (repeatable, "
                             "later overlays win); defaults to <ui>/extra")
    parser.add_argument("--cro", type=Path, action="append",
                        help="CRO to ship with the candidate (repeatable); defaults to every "
                             "<ui>/romfs/cro/*.cro")
    args = parser.parse_args()
    print(json.dumps(construir(args.base, args.output, ui=args.ui, capas=args.extra, cro=args.cro), indent=2))
