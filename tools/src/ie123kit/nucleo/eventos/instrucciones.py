"""Lectura de instrucciones de los scripts de evento y preparación de SSD para reinsertar.

Consolida el patrón ``event_ssd_staging`` del catálogo de auditoría (18 copias en
work/): FaArchive -> eve/mch .pkh+.pkb -> índice PackNum -> LZ10 -> ssd.parse ->
elegir registros por opcode y argumento -> ssd.replace -> ``events/<eid>.ssd``.

Las comprobaciones de ``comparar`` son las MISMAS que aplica ``rebuild_events`` del
bloqueado tools/build_ui_revision.py: tabla de instrucciones idéntica, mismo número
de registros, identidad ``(instruction, argument)`` por registro y cierre
``new_end == 32 + u32@16``.

Límite de texto: un registro SSD codifica su tamaño en un solo byte y debe estar
alineado a 4, de modo que el máximo es 252 bytes de registro, esto es 247 bytes de
cuerpo (4 de cabecera + 1 de terminador). ``ssd.replace`` lo rechaza y aquí se valida
antes de tocar nada.
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Literal

from ie123kit.nucleo.compresion.lz10 import decompress
from ie123kit.nucleo.errores import ValidacionError
from ie123kit.nucleo.eventos import ssd
from ie123kit.nucleo.eventos.packnum import parse_index
from ie123kit.nucleo.eventos.ssd import TextRecord

__all__ = ["DIR_SCRIPT", "LIMITE_TEXTO", "EventPack", "comparar", "instrucciones", "stage"]

DIR_SCRIPT = "inazuma1/data_iz/script"
LIMITE_TEXTO = 247
Pack = Literal["eve", "mch"]


def _rutas(pack: str) -> tuple[str, str]:
    if pack not in ("eve", "mch"):
        raise ValidacionError("evento_pack_desconocido", detalle=str(pack))
    return f"{DIR_SCRIPT}/{pack}.pkh", f"{DIR_SCRIPT}/{pack}.pkb"


def instrucciones(data: bytes) -> dict[int, tuple[int, list[tuple[int, int]]]]:
    """``ident -> (opcode, [(tipo_arg, valor), ...])`` con la disposición de ``ssd``."""
    cabecera = b"SSD\0" + data[4:32]
    _, _, _, count, _, _code_size, _, _, _ = struct.unpack_from("<4sIIHHIIII", cabecera)
    pos, salida = 32, {}
    for _ in range(count):
        ident, length, opcode, argc, _unk = struct.unpack_from("<HHHBB", data, pos)
        tipos = 4 * ((argc + 7) // 8)
        args = []
        for a in range(argc):
            tipo = (data[pos + 8 + a // 2] >> (4 * (a % 2))) & 15
            args.append((tipo, struct.unpack_from("<I", data, pos + 8 + tipos + 4 * a)[0]))
        salida[ident] = (opcode, args)
        pos += length
    return salida


def comparar(original: bytes, nuevo: bytes, evento: int | None = None) -> int:
    """Devuelve cuántos registros de texto cambian; rechaza cualquier otra diferencia."""
    detalle = "" if evento is None else f"evento {evento}"
    try:
        _viejo_fin, viejas, viejos = ssd.parse(original)
        nuevo_fin, nuevas, nuevos = ssd.parse(nuevo)
    except ValueError as exc:
        raise ValidacionError("ssd_invalido", detalle=", ".join(p for p in (detalle, str(exc)) if p)) from exc
    if viejas != nuevas:
        raise ValidacionError("ssd_tabla_instrucciones_cambiada", detalle=detalle)
    if len(viejos) != len(nuevos):
        raise ValidacionError("ssd_numero_de_registros", detalle=detalle)
    cambiados = 0
    for i, (viejo, nueva) in enumerate(zip(viejos, nuevos)):
        if (viejo.instruction, viejo.argument) != (nueva.instruction, nueva.argument):
            raise ValidacionError("ssd_identidad_de_registro", detalle=f"{detalle} registro {i}".strip())
        if len(nueva.body) > LIMITE_TEXTO:
            raise ValidacionError("ssd_texto_demasiado_largo", detalle=f"{detalle} registro {i}".strip())
        if viejo.body != nueva.body:
            cambiados += 1
    if nuevo_fin != 32 + struct.unpack_from("<I", nuevo, 16)[0]:
        raise ValidacionError("ssd_payload_malformado", detalle=detalle)
    return cambiados


class EventPack:
    """Paquete de eventos (eve o mch) ya leído en memoria."""

    def __init__(self, pkh: bytes, pkb: bytes, pack: str = "eve") -> None:
        self.pack = pack
        self.pkh = bytes(pkh)
        self.pkb = bytes(pkb)
        self.index = parse_index(self.pkh)

    @classmethod
    def from_archive(cls, arc, pack: Pack = "eve") -> EventPack:
        """Lee <DIR_SCRIPT>/<pack>.pkh|.pkb de un ``contenedores.fa.FaArchive``."""
        ruta_pkh, ruta_pkb = _rutas(pack)
        por_ruta = {p: (o, s) for p, o, s in arc.entries}
        datos = []
        for ruta in (ruta_pkh, ruta_pkb):
            if ruta not in por_ruta:
                raise ValidacionError("evento_pack_ausente", ruta=ruta)
            datos.append(bytes(arc.file_bytes(*por_ruta[ruta])))
        return cls(datos[0], datos[1], pack)

    @classmethod
    def from_dir(cls, dir_base, pack: Pack = "eve") -> EventPack:
        """Lee <dir_base>/<DIR_SCRIPT>/<pack>.pkh|.pkb de un volcado en disco."""
        base = Path(dir_base)
        ruta_pkh, ruta_pkb = _rutas(pack)
        for ruta in (base / ruta_pkh, base / ruta_pkb):
            if not ruta.is_file():
                raise ValidacionError("evento_pack_ausente", ruta=ruta)
        return cls((base / ruta_pkh).read_bytes(), (base / ruta_pkb).read_bytes(), pack)

    def events(self) -> dict[int, bytes]:
        """``event_id -> script descomprimido`` (LZ10 automático)."""
        return {eid: decompress(self.pkb[off:off + size]) for eid, off, size in self.index}

    def instructions(self, eid: int) -> dict[int, tuple[int, list[tuple[int, int]]]]:
        return instrucciones(self._evento(eid))

    def records(self, eid: int) -> list[TextRecord]:
        return ssd.parse(self._evento(eid))[2]

    def find(self, eid: int, opcode: int | None = None, argumento: int | None = None) -> list[tuple[int, TextRecord]]:
        """Registros de texto del evento filtrados por opcode de su instrucción y argumento."""
        tabla = self.instructions(eid)
        salida = []
        for i, registro in enumerate(self.records(eid)):
            if opcode is not None and tabla.get(registro.instruction, (None, []))[0] != opcode:
                continue
            if argumento is not None and registro.argument != argumento:
                continue
            salida.append((i, registro))
        return salida

    def stage(self, cambios: dict[int, dict[int, bytes]], dir_salida, *, verify: bool = True) -> dict:
        """Escribe ``<dir_salida>/<eid>.ssd`` con los cuerpos sustituidos por índice.

        Con ``verify`` se comprueba cada resultado contra el original con las mismas
        reglas que ``build_ui_revision.rebuild_events`` (véase ``comparar``).
        """
        destino = Path(dir_salida)
        destino.mkdir(parents=True, exist_ok=True)
        eventos = self.events()
        desconocidos = sorted(set(cambios) - set(eventos))
        if desconocidos:
            raise ValidacionError("evento_desconocido", detalle=", ".join(str(e) for e in desconocidos))
        informe: list[dict] = []
        for eid in sorted(cambios):
            reemplazos = {int(i): bytes(b) for i, b in cambios[eid].items()}
            largos = sorted(i for i, b in reemplazos.items() if len(b) > LIMITE_TEXTO)
            if largos:
                raise ValidacionError(
                    "ssd_texto_demasiado_largo",
                    detalle=f"evento {eid} registros {', '.join(str(i) for i in largos)}",
                )
            original = eventos[eid]
            try:
                nuevo = ssd.replace(original, reemplazos)
            except ValueError as exc:
                raise ValidacionError("ssd_reemplazo_invalido", detalle=f"evento {eid}: {exc}") from exc
            cambiados = comparar(original, nuevo, eid) if verify else len(reemplazos)
            ruta = destino / f"{eid}.ssd"
            ruta.write_bytes(nuevo)
            informe.append({
                "evento": eid,
                "ruta": str(ruta),
                "registros_cambiados": cambiados,
                "bytes_antes": len(original),
                "bytes_despues": len(nuevo),
            })
        return {"pack": self.pack, "dir_salida": str(destino), "eventos": informe}

    def _evento(self, eid: int) -> bytes:
        for e, off, size in self.index:
            if e == eid:
                return decompress(self.pkb[off:off + size])
        raise ValidacionError("evento_desconocido", detalle=str(eid))


def stage(pack: EventPack, cambios: dict[int, dict[int, bytes]], dir_salida, *, verify: bool = True) -> dict:
    """Forma de función del método ``EventPack.stage`` (la del catálogo de auditoría)."""
    return pack.stage(cambios, dir_salida, verify=verify)
