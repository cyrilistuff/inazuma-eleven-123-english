"""Tablas de registros de tamaño fijo (.dat) y pools de cadenas (.STR y ranuras de 32 B).

Las primitivas de escritura NUNCA truncan: si el texto codificado no cabe con su
terminador, lanzan ValueError. El codificador se inyecta; aquí no se elige tipografía.

:class:`TableSpec` y :class:`RecordTable` recogen el patrón ``fixed_width_table_fields`` de las
capas de ``work/`` (calcular offsets a mano, codificar, comprobar capacidad, rellenar con ceros y
volver a verificar que los campos intactos siguen igual). Cada edición queda registrada para la
comprobación enmascarada de :mod:`ie123kit.nucleo.registros.rangos`.
"""
from dataclasses import dataclass, field

from ie123kit.nucleo.errores import ValidacionError
from ie123kit.nucleo.registros.rangos import fusionar


def names_from_dat(path, stride, dec, width=16):
    with open(path, "rb") as fh:
        d = fh.read()
    return [dec(d[i * stride:i * stride + width]) for i in range(len(d) // stride)]


def strings_from_str(path, dec):
    with open(path, "rb") as fh:
        d = fh.read()
    return [dec(p) for p in d.split(b"\x00") if len(p) >= 1]


def escribir_campo(data, offset, size, codificado, texto):
    """Escribe ``codificado`` en un campo fijo de ``size`` bytes y rellena con ceros.

    Exige sitio para el terminador; nunca trunca.
    """
    if len(codificado) >= size:
        raise ValueError('name exceeds field including terminator: ' + texto)
    data[offset:offset + size] = codificado + bytes(size - len(codificado))


def parchear_pool_32(source, translations, codificar):
    """Sustituye cadenas Shift-JIS alojadas en ranuras de 32 B; ``codificar(texto) -> bytes``.

    Devuelve ``(bytes_resultado, posiciones_cambiadas)``.
    """
    result = bytearray(source); pos = 0; changed = []
    for part in source.split(b'\0'):
        if part:
            text = part.decode('shift_jis').strip()
            if text in translations:
                capacity = ((len(part) + 1 + 31) // 32) * 32
                if pos % 32 or any(source[pos + len(part):pos + capacity]):
                    raise ValueError('not a padded 32-byte string slot')
                nuevo = translations[text]
                escribir_campo(result, pos, capacity, codificar(nuevo), nuevo)
                changed.append(pos)
        pos += len(part) + 1
    return bytes(result), changed



def _codificador_por_defecto():
    """Transporte latino de ancho completo v20 (importación perezosa: nunca se copia aquí)."""
    from ie123kit.nucleo.texto.ancho_completo import encode_fullwidth

    return encode_fullwidth


@dataclass(frozen=True)
class TableSpec:
    """Geometría de una tabla de registros de tamaño fijo.

    ``size`` es el paso entre registros, ``header`` los bytes iniciales que no son registros y
    ``fields`` un mapa ``nombre -> (offset_relativo, tamaño)``. ``game_buffer``, si se indica,
    es el búfer real que el juego reserva al leer el campo: manda sobre el tamaño del campo.
    """

    size: int
    fields: dict[str, tuple[int, int]] = field(default_factory=dict)
    header: int = 0
    game_buffer: int | None = None

    def campo(self, nombre: str) -> tuple[int, int]:
        if nombre not in self.fields:
            raise ValidacionError("campo_desconocido", detalle=nombre)
        return self.fields[nombre]

    def capacidad(self, nombre: str) -> int:
        """Bytes utilizables del campo, contando el búfer del juego."""
        tam = self.campo(nombre)[1]
        return min(tam, self.game_buffer) if self.game_buffer else tam


# Presets auditados en work/ie1 (issue #16 y capas v36/v43/v46/v54).
UNITBASE = TableSpec(header=96, size=96, fields={"name": (0, 16), "short": (16, 16), "reading": (32, 32)})
TEAM = TableSpec(size=320, fields={"name": (0, 32)})
ITEM = TableSpec(size=32, fields={"name": (0, 19)})
RPGTITLE = TableSpec(size=32, fields={"title": (0, 32)}, game_buffer=18)


class RecordTable:
    """Vista editable de una tabla de registros de tamaño fijo."""

    def __init__(self, data, spec: TableSpec) -> None:
        if spec.size <= 0:
            raise ValidacionError("paso_invalido", detalle=str(spec.size))
        self.spec = spec
        self._datos = bytearray(data)
        self._rangos: list[tuple[int, int]] = []

    @property
    def count(self) -> int:
        return max(0, (len(self._datos) - self.spec.header)) // self.spec.size

    def _offset(self, i: int, campo: str) -> tuple[int, int]:
        if not 0 <= i < self.count:
            raise ValidacionError("registro_fuera_de_rango", detalle=f"{i} de {self.count}")
        rel, tam = self.spec.campo(campo)
        return self.spec.header + i * self.spec.size + rel, tam

    def get(self, i: int, campo: str) -> bytes:
        off, tam = self._offset(i, campo)
        return bytes(self._datos[off:off + tam])

    def text(self, i: int, campo: str, encoding: str = "cp932") -> str:
        return self.get(i, campo).split(b"\0")[0].decode(encoding)

    def set_text(self, i, campo, texto, encoder=None, max_chars=None, max_bytes=None, nul=True) -> None:
        """Escribe ``texto`` en el campo. LANZA ValidacionError si no cabe; nunca trunca."""
        off, tam = self._offset(i, campo)
        if max_chars is not None and len(texto) > max_chars:
            raise ValidacionError("texto_largo", detalle=f"{texto!r}: {len(texto)} > {max_chars} caracteres")
        codificado = (encoder or _codificador_por_defecto())(texto)
        tope = self.spec.capacidad(campo)
        if max_bytes is not None:
            tope = min(tope, max_bytes)
        disponible = tope - 1 if nul else tope
        if len(codificado) > disponible:
            raise ValidacionError(
                "texto_no_cabe",
                detalle=f"{texto!r}: {len(codificado)} B > {disponible} B en {campo}[{i}]",
            )
        self._datos[off:off + tam] = codificado + bytes(tam - len(codificado))
        self._rangos.append((off, off + tam))

    def rangos_cambiados(self) -> list[tuple[int, int]]:
        """Rangos semiabiertos de todos los campos editados (fusionados)."""
        return fusionar(self._rangos)

    def to_bytes(self) -> bytes:
        return bytes(self._datos)
