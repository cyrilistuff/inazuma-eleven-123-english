"""Planes de textura sobre ARCV/CTPK sintéticos (F2.2, #48).

Norma 2: aquí no entra ni un byte de la ROM. El .arc, su tabla ARCV y los CTPK se generan en
el propio test con el formato que documenta docs/FORMATOS.md (CTPK de una sola textura, formato
0 = RGBA8888, que es sin pérdida y por tanto hace ida y vuelta con ctpk.encode/decode).
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import pytest
from PIL import Image

from ie123kit.nucleo.compresion import sszl
from ie123kit.nucleo.contenedores import arcv
from ie123kit.nucleo.contenedores.fa import FaArchive
from ie123kit.nucleo.errores import ValidacionError
from ie123kit.nucleo.graficos import ctpk, texturas

CONTRATO = Path(__file__).resolve().parent.parent.parent / "contrato"
if str(CONTRATO) not in sys.path:
    sys.path.insert(0, str(CONTRATO))

from fa_sintetico import escribir_fa

RUTA_A = "inazuma1/data_iz/a_menu/status_t.arc"
RUTA_B = "inazuma1/data_iz/a_title/title_t.arc"
CABECERA = 64


def hacer_ctpk(nombre: str, imagen: Image.Image) -> bytes:
    """CTPK mínimo de una textura, formato 0 (RGBA8888), con el nombre tras la cabecera."""
    w, h = imagen.size
    crudo = nombre.encode("utf-8") + b"\0"
    texoff = CABECERA + len(crudo)
    texoff += (-texoff) % 4
    tamano = w * h * 4
    datos = bytearray(texoff + tamano)
    datos[0:4] = b"CTPK"
    struct.pack_into("<HH", datos, 4, 1, 1)          # versión, número de texturas
    struct.pack_into("<I", datos, 8, texoff)
    struct.pack_into("<IIII", datos, 32, CABECERA, tamano, 0, 0)
    struct.pack_into("<HH", datos, 48, w, h)
    datos[CABECERA:CABECERA + len(crudo)] = crudo
    return ctpk.encode(bytes(datos), imagen)


def hacer_arcv(blobs: list[bytes]) -> bytes:
    """Contenedor ARCV con la tabla de 12 bytes por entrada que espera arcv.entries."""
    inicio = 12 + 12 * len(blobs)
    cuerpo, tabla, desplazamiento = bytearray(), bytearray(), inicio
    for blob in blobs:
        tabla += struct.pack("<III", desplazamiento, len(blob), 0)
        cuerpo += blob
        desplazamiento += len(blob)
    return b"ARCV" + struct.pack("<II", len(blobs), inicio + len(cuerpo)) + bytes(tabla) + bytes(cuerpo)


def degradado(w: int = 8, h: int = 8, sesgo: int = 0) -> Image.Image:
    im = Image.new("RGBA", (w, h))
    for y in range(h):
        for x in range(w):
            im.putpixel((x, y), ((x * 8 + sesgo) % 256, (y * 8) % 256, 64, 255))
    return im


def en_rojo(im: Image.Image) -> Image.Image:
    return Image.new("RGBA", im.size, (255, 0, 0, 255))


def en_azul(im: Image.Image) -> Image.Image:
    return Image.new("RGBA", im.size, (0, 0, 255, 255))


@pytest.fixture
def base(tmp_path: Path) -> Path:
    arc_a = hacer_arcv([
        hacer_ctpk("uno.tga", degradado()),
        b"QNA0" + b"\x00" * 28,                       # entrada que no es CTPK: debe ignorarse
        hacer_ctpk("dos.tga", degradado(sesgo=3)),
    ])
    arc_b = sszl.compress(hacer_arcv([hacer_ctpk("logo.tga", degradado(16, 8))]))
    return escribir_fa(tmp_path / "archive.fa", {RUTA_A: arc_a, RUTA_B: arc_b})


# ───────────────────────── lectura ─────────────────────────

def test_iter_ctpk_salta_lo_que_no_es_ctpk(base: Path) -> None:
    datos = FaArchive(str(base)).read(RUTA_A)
    encontradas = list(texturas.iter_ctpk(datos))
    assert [t.nombre for t in encontradas] == ["uno.tga", "dos.tga"]
    assert all(t.ancho == 8 and t.alto == 8 and t.formato == 0 for t in encontradas)
    assert all(t.blob[:4] == b"CTPK" and len(t.blob) == t.tamano for t in encontradas)


def test_iter_ctpk_desenvuelve_sszl(base: Path) -> None:
    datos = FaArchive(str(base)).read(RUTA_B)
    assert datos[:4] == b"SSZL"
    assert [t.nombre for t in texturas.iter_ctpk(datos)] == ["logo.tga"]


def test_texture_map(base: Path) -> None:
    datos = FaArchive(str(base)).read(RUTA_A)
    mapa = texturas.texture_map(datos)
    assert set(mapa) == {"uno.tga", "dos.tga"}
    crudo = sszl.unwrap(datos)
    for nombre, (off, tam) in mapa.items():
        assert ctpk.metadata(crudo[off:off + tam])[0] == nombre


def test_find_texture_y_su_error(base: Path) -> None:
    datos = FaArchive(str(base)).read(RUTA_A)
    assert texturas.find_texture(datos, "dos.tga").nombre == "dos.tga"
    with pytest.raises(KeyError) as exc:
        texturas.find_texture(datos, "tres.tga")
    assert "uno.tga" in str(exc.value) and "dos.tga" in str(exc.value)


def test_load_texture(base: Path) -> None:
    arc = FaArchive(str(base))
    im = texturas.load_texture(arc, RUTA_B, "logo.tga")
    assert im.mode == "RGBA"
    assert im.size == (16, 8)


# ───────────────────────── apply_plan ─────────────────────────

def test_apply_plan_escribe_arc_y_registro(base: Path, tmp_path: Path) -> None:
    salida = tmp_path / "extra"
    registro = texturas.apply_plan(base, {RUTA_A: {"uno.tga": en_rojo}}, salida)
    assert registro == [{"archivo": RUTA_A, "textura": "uno.tga", "cambio": "en_rojo"}]

    escrito = (salida / RUTA_A).read_bytes()
    assert escrito[:4] == b"ARCV"                      # rewrap='raw' por defecto, como V37
    original = sszl.unwrap(FaArchive(str(base)).read(RUTA_A))
    assert arcv.entries(escrito) == arcv.entries(original)
    assert texturas.load_texture(FaArchive(str(base)), RUTA_A, "uno.tga") != Image.new("RGBA", (8, 8))
    nueva = ctpk.decode(texturas.find_texture(escrito, "uno.tga").blob)
    assert nueva.getpixel((0, 0)) == (255, 0, 0, 255)
    assert ctpk.decode(texturas.find_texture(escrito, "dos.tga").blob) == \
        ctpk.decode(texturas.find_texture(original, "dos.tga").blob)


def test_apply_plan_varias_texturas_y_archivos(base: Path, tmp_path: Path) -> None:
    salida = tmp_path / "extra"
    plan = {RUTA_A: {"uno.tga": en_rojo, "dos.tga": en_azul}, RUTA_B: {"logo.tga": en_rojo}}
    registro = texturas.apply_plan(base, plan, salida, rewrap="keep")
    assert len(registro) == 3
    assert (salida / RUTA_A).read_bytes()[:4] == b"ARCV"     # la base no venía envuelta
    assert (salida / RUTA_B).read_bytes()[:4] == b"SSZL"     # la base sí


def test_apply_plan_rewrap_sszl(base: Path, tmp_path: Path) -> None:
    salida = tmp_path / "extra"
    texturas.apply_plan(base, {RUTA_A: {"uno.tga": en_rojo}}, salida, rewrap="sszl")
    escrito = (salida / RUTA_A).read_bytes()
    assert escrito[:4] == b"SSZL"
    assert sszl.unwrap(escrito)[:4] == b"ARCV"


def test_apply_plan_previews_y_report(base: Path, tmp_path: Path) -> None:
    salida, vistas, informe = tmp_path / "extra", tmp_path / "previews", tmp_path / "report.json"
    texturas.apply_plan(base, {RUTA_A: {"uno.tga": en_rojo}}, salida,
                        previews=vistas, report=informe)
    assert (vistas / "uno.png").is_file()
    import json
    datos = json.loads(informe.read_text(encoding="utf-8"))
    assert datos["runtime_verified"] is False
    assert datos["base_sha256"] and Path(datos["base"]).name == "archive.fa"
    assert datos["texturas"][0]["textura"] == "uno.tga"


def test_apply_plan_acepta_un_faarchive_abierto(base: Path, tmp_path: Path) -> None:
    arc = FaArchive(str(base))
    registro = texturas.apply_plan(arc, {RUTA_A: {"dos.tga": en_azul}}, tmp_path / "extra")
    assert registro[0]["textura"] == "dos.tga"


def test_apply_plan_falla_si_la_textura_declarada_no_existe(base: Path, tmp_path: Path) -> None:
    with pytest.raises(ValidacionError) as exc:
        texturas.apply_plan(base, {RUTA_A: {"fantasma.tga": en_rojo}}, tmp_path / "extra")
    assert exc.value.codigo == "texturas_no_encontradas"
    assert "fantasma.tga" in str(exc.value)


def test_apply_plan_falla_si_la_edicion_cambia_el_tamano(base: Path, tmp_path: Path) -> None:
    def encoge(im: Image.Image) -> Image.Image:
        return im.resize((im.width // 2, im.height // 2))

    with pytest.raises(ValueError):  # ctpk.encode rechaza el cambio de dimensiones
        texturas.apply_plan(base, {RUTA_A: {"uno.tga": encoge}}, tmp_path / "extra")


def test_apply_plan_falla_si_la_tabla_arcv_queda_alterada(base: Path, tmp_path: Path,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    autentico = arcv.entries
    llamadas = {"n": 0}

    def espia(data):
        llamadas["n"] += 1
        resultado = autentico(data)
        # la tercera llamada es la comprobación final sobre el .arc ya editado
        return resultado[:-1] if llamadas["n"] == 3 else resultado

    monkeypatch.setattr(texturas.arcv, "entries", espia)
    with pytest.raises(ValidacionError) as exc:
        texturas.apply_plan(base, {RUTA_A: {"uno.tga": en_rojo}}, tmp_path / "extra")
    assert exc.value.codigo == "tabla_arcv_alterada"


def test_apply_plan_ruta_inexistente(base: Path, tmp_path: Path) -> None:
    with pytest.raises(KeyError):
        texturas.apply_plan(base, {"no/existe.arc": {"uno.tga": en_rojo}}, tmp_path / "extra")


# ───────────────────────── validate_plan ─────────────────────────

def test_validate_plan_acepta_lo_que_produce_apply_plan(base: Path, tmp_path: Path) -> None:
    salida = tmp_path / "extra"
    plan = {RUTA_A: {"uno.tga": en_rojo}, RUTA_B: {"logo.tga": en_azul}}
    texturas.apply_plan(base, plan, salida, rewrap="keep")
    informe = texturas.validate_plan(base, plan, salida)
    assert informe.ok, informe.problemas
    assert sorted(informe.cambiadas) == sorted(informe.declaradas)


def test_validate_plan_detecta_el_arc_ausente(base: Path, tmp_path: Path) -> None:
    informe = texturas.validate_plan(base, {RUTA_A: {"uno.tga": en_rojo}}, tmp_path / "vacio")
    assert not informe.ok
    assert "falta el .arc" in informe.problemas[0]


def test_validate_plan_detecta_textura_declarada_sin_cambios(base: Path, tmp_path: Path) -> None:
    salida = tmp_path / "extra"
    texturas.apply_plan(base, {RUTA_A: {"uno.tga": en_rojo}}, salida)
    informe = texturas.validate_plan(base, {RUTA_A: {"uno.tga": en_rojo, "dos.tga": en_azul}}, salida)
    assert not informe.ok
    assert any("dos.tga" in p for p in informe.problemas)


def test_validate_plan_detecta_cambio_no_declarado(base: Path, tmp_path: Path) -> None:
    salida = tmp_path / "extra"
    texturas.apply_plan(base, {RUTA_A: {"uno.tga": en_rojo, "dos.tga": en_azul}}, salida)
    informe = texturas.validate_plan(base, {RUTA_A: {"uno.tga": en_rojo}}, salida)
    assert not informe.ok
    assert any("no declarada" in p and "dos.tga" in p for p in informe.problemas)


def test_validate_plan_allow_admite_la_excepcion(base: Path, tmp_path: Path) -> None:
    salida = tmp_path / "extra"
    texturas.apply_plan(base, {RUTA_A: {"uno.tga": en_rojo, "dos.tga": en_azul}}, salida)
    informe = texturas.validate_plan(base, {RUTA_A: {"uno.tga": en_rojo}}, salida,
                                     allow=lambda nombre, _viejo, _nuevo: nombre == "dos.tga")
    assert informe.ok, informe.problemas
    assert "inazuma1/data_iz/a_menu/status_t.arc::dos.tga" in informe.cambiadas


def test_validate_plan_detecta_tabla_arcv_alterada(base: Path, tmp_path: Path) -> None:
    salida = tmp_path / "extra"
    texturas.apply_plan(base, {RUTA_A: {"uno.tga": en_rojo}}, salida)
    destino = salida / RUTA_A
    datos = bytearray(destino.read_bytes())
    entradas = arcv.entries(bytes(datos))
    struct.pack_into("<I", datos, 12 + 4, entradas[0][1] - 4)   # encoge la primera entrada
    destino.write_bytes(bytes(datos))
    informe = texturas.validate_plan(base, {RUTA_A: {"uno.tga": en_rojo}}, salida)
    assert not informe.ok
    assert any("ARCV" in p for p in informe.problemas)
