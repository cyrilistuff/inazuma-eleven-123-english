"""User-approved v20 dialogue appearance. No opt-out build switch."""
import hashlib
import inspect
from pathlib import Path

FONT_HASHES = {
    'font/FONT12.bcfnt': 'db74945637301e74d8d36248626b4cc3e88c794a33e3d439dbb7ab813e9ff2e3',
    'font/FONT12T.bcfnt': '71c37509f0eec6c092ea75f373667b0bf1f19389c45b1741a89a8f53270164ab',
    'font/FONT8.bcfnt': 'b05e64c84cb564a98bea87cbdc94454f14f3df17e78252edf5a32be43ce454dd',
    'inazuma1/data_iz/font/FONT12.NFTR': 'b43cfc73407c928272a001f04b85380976348e30da528b5938a3e45b87ea85c7',
    'inazuma1/data_iz/font/FONT8.NFTR': '6f683a8cef209d6e9eb9b31be5cadaad5eb90bf5ccd5e5c01c40afdf89984865',
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
