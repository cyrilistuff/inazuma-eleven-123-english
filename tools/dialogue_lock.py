"""User-approved dialogue appearance: v20 box/layout + v73 glyph spacing (authorized 2026-09-16, #66). No opt-out build switch."""
import hashlib
import inspect
from pathlib import Path

FONT_HASHES = {
    'font/FONT12.bcfnt': '9069b9e346574d98fca442832d0759846b942170d494f38096d5edc80abd2d0a',
    'font/FONT12T.bcfnt': 'f7100c2d97e2fd07285acbc83a03aed6a2975775060d36af939b4dd1f4dced65',
    'font/FONT8.bcfnt': 'b05e64c84cb564a98bea87cbdc94454f14f3df17e78252edf5a32be43ce454dd',
    'inazuma1/data_iz/font/FONT12.NFTR': 'e9a25928b2e66fd45a9879fe620e103e0553a91158b753517ba6a83b328fcdf2',
    'inazuma1/data_iz/font/FONT8.NFTR': '4e79520bc16f5583d07322e0eb66accd43d4a53084e6149179dde1e95b7d0c74',
}
SOURCE_HASHES = {
    'tools/dialogue_typography.py': '8e983419465a36460da722df4fccdb18b18b56836dc47fbc618974c18c4f42fa',
    'tools/font_patch.py': '04cf7ff5ed019f78f05b8b4912d483fbbd6c33268e1c21e85d7d1dbbe75655dc',
}
LAYOUT_HASH = '9af32753aa26c1a6738c8e76ec0816d82ed901b6b46dab5e26f51f1ed1d102b2'


def validate(fullwidth, extra_files, layout):
    """Fail before compilation if approved typography has drifted."""
    def fail(detail):
        raise ValueError('Tipografia v20 bloqueada por el usuario: ' + detail)
    if not fullwidth:
        fail('se requiere --fullwidth; ASCII no esta autorizado')
    if extra_files is None:
        fail('faltan las fuentes aprobadas en --extra-files')
    root = Path(__file__).resolve().parents[1]
    for base, manifest in ((root, SOURCE_HASHES), (Path(extra_files), FONT_HASHES)):
        for rel, expected in manifest.items():
            path = base / rel
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                fail('archivo cambiado o ausente: ' + rel)
    source = inspect.getsource(layout).replace('\r\n', '\n')
    if hashlib.sha256(source.encode()).hexdigest() != LAYOUT_HASH:
        fail('se ha cambiado el ajuste de lineas')


def approved_layout(text, layout):
    return layout(text, advance=lambda ch: 11, width=220)
