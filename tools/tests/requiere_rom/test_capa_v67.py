"""Gate 3: la capa work/ie1/capas/v67/titulo_logo se regenera byte a byte igual que su golden.

Requiere work/ local (ROM extraída); en CI se deselecciona con -m "not requiere_rom".
"""
import pytest

pytestmark = pytest.mark.requiere_rom

CAPA = 'work/ie1/capas/v67/titulo_logo'
BASE_V66 = 'work/shared/candidatas/probe_ie1_v66/archive.fa'
GOLDEN = 'tools/tests/compat/golden/capas_v67.sha256'


def test_regenerar_capa_v67_coincide_con_golden():
    from ie123kit.nucleo.compat.golden import regenerar_capa, sha
    from ie123kit.nucleo.config.raiz import find_root

    raiz = find_root()
    for rel in (f'{CAPA}/apply.py', BASE_V66):
        if not (raiz / rel).is_file():
            pytest.skip(f'falta recurso local: {rel}')

    total, malos = regenerar_capa(raiz)
    assert total >= 1
    assert malos == []

    # Comprobación independiente de comprobar_grupo: recalcular cada sha tras la regeneración.
    for linea in (raiz / GOLDEN).read_text(encoding='utf-8').splitlines():
        esperado, rel = linea.split('  ', 1)
        assert (raiz / rel).is_file(), f'ausente {rel}'
        assert sha(raiz / rel) == esperado, f'distinto {rel}'
