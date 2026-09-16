"""Limpieza de work/ según docs/ARQUITECTURA.md.

Borra lo que se puede regenerar o está superado: candidatas probe_ie1_vN que no sean las dos últimas,
imágenes de ROM reconstruidas de releases publicadas, volcados de texturas de auditorías antiguas,
descargas duplicadas de herramientas, cachés y temporales (.partial, .yuv, __pycache__, *_x2.png).
Nunca toca: shared/base_3ds, ieN/fuentes, Roms, capas vN con scripts, docs ni tools.
Uso: python tools/limpiar_work.py            (solo lista)
     python tools/limpiar_work.py --borrar   (borra)
"""
import re

from ie123kit.nucleo.config.raiz import find_root

ROOT = find_root()
WORK = ROOT / 'work'

FIJOS = [
    'shared/releases/release_v35/base_rebuilt.3ds', 'shared/releases/release_v35/roundtrip_v35.3ds',
    'ie1/capas/v58/cinematicas/fuentes', 'ie1/legacy/pending/renders', 'ie1/legacy/pending/audit',
]
CANDIDATAS_A_CONSERVAR = 2


def objetivos():
    out = [WORK / p for p in FIJOS]
    probes = sorted((p for p in (WORK / 'shared/candidatas').glob('probe_ie1_v*') if re.fullmatch(r'probe_ie1_v\d+', p.name)),
                    key=lambda p: int(p.name.rsplit('v', 1)[1]))
    out += [p for p in probes[:-CANDIDATAS_A_CONSERVAR] if not (p / '.conservar').exists()]  # golden de #41
    out += list(WORK.rglob('__pycache__'))
    out += [p for pat in ('*.partial', '*.yuv', '*_x2.png', 'tmp_*.dat') for p in WORK.rglob(pat)]
    out += [p for p in (WORK / 'shared/trailer').glob('check*.*') if re.fullmatch(r'check\d*\.(err|json)', p.name)]
    out += [ROOT / 'sideloadlydaemon.log']
    return [p for p in dict.fromkeys(out) if p.exists()]


def tam(p):
    return p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
