"""Migración única a la arquitectura por juego (docs/ARQUITECTURA.md).

Mueve work/, Roms/ y translation/ a carpetas ie1/ ie2/ ie3/ shared/, reescribe las rutas escritas en
scripts y documentos, y corrige `parents[N]` en los .py movidos para que sigan apuntando a la raíz.
Uso: python tools/reorganizar_proyecto.py          (simulación: lista movimientos y ficheros a reescribir)
     python tools/reorganizar_proyecto.py --aplicar
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work'

SHARED = {'romfs': 'shared/base_3ds/romfs', 'exefs': 'shared/base_3ds/exefs', 'media_tools': 'shared/herramientas/media_tools',
          'trailer': 'shared/trailer', 'release_v35': 'shared/releases/release_v35'}
IE1_FUENTES = {'ie1_es': 'ie1/fuentes/nds_es', 'ie1_eu3ds': 'ie1/fuentes/3ds_eu'}
BORRAR = ['volumen_2', 'volumen_1/comparison', 'volumen_1/diagnostic_orientation', 'volumen_1/diagnostic_title_installed']
ROMS = {'Inazuma Eleven 1-2-3 - Endou Mamoru Densetsu.3ds': 'shared', 'Inazuma Eleven 1-2-3 - Endou Mamoru Densetsu (2012).cia': 'shared',
        'Inazuma Eleven (2011).nds': 'ie1', '000400000010DD00 INAZUMA ELEVEN (2011).cia': 'ie1',
        'Inazuma Eleven 2 - Tormenta de Fuego (2012).nds': 'ie2/tormenta_de_fuego',
        'Inazuma Eleven 2 - Ventisca Eterna (2012).nds': 'ie2/ventisca_eterna',
        'Inazuma Eleven 3 - Bomb Blast (2013).cia': 'ie3/fuego_explosivo'}
TRANSLATION = {'game1': 'ie1', 'game2': 'ie2', 'game3': 'ie3', 'glossary': 'shared/glossary'}
VACIAS = ['ie2/tormenta_de_fuego', 'ie2/ventisca_eterna', 'ie2/shared', 'ie3/rayo_celeste', 'ie3/fuego_explosivo',
          'ie3/amenaza_del_ogro', 'ie3/shared']
TEXTO = {'.py', '.ps1', '.json', '.md', '.bat', '.yml', '.yaml', '.txt', '.toml', '.cfg', '.gitignore'}
NUEVAS = {'shared', 'ie1', 'ie2', 'ie3'}


def mapa_work():
    m = {}
    for d in sorted(p.name for p in WORK.iterdir() if p.is_dir()):
        if d in NUEVAS:
            continue
        if d in SHARED:
            m[d] = SHARED[d]
        elif d in IE1_FUENTES:
            m[d] = IE1_FUENTES[d]
        elif re.fullmatch(r'probe_ie1_v\d+', d):
            m[d] = 'shared/candidatas/' + d
        elif re.fullmatch(r'v\d+', d) or d.startswith(('v7_', 'v14_')):
            m[d] = 'ie1/capas/' + d
        elif d.startswith('qa_'):
            m[d] = 'ie1/qa/' + d
        elif d in BORRAR:
            continue
        else:
            m[d] = 'ie1/legacy/' + d
    return m


def reglas(m):
    out = []
    for viejo, nuevo in sorted(m.items(), key=lambda x: -len(x[0])):
        out.append((re.compile(r'(?<![A-Za-z0-9_])work([/\\]+)' + re.escape(viejo) + r'(?![A-Za-z0-9_])'),
                    lambda mo, n=nuevo: 'work' + mo.group(1) + n.replace('/', mo.group(1))))
    out.append((re.compile(r'(?<![A-Za-z0-9_])work([/\\]+)probe_ie1_v(\d+)(?![A-Za-z0-9_])'),
                lambda mo: 'work' + mo.group(1) + 'shared' + mo.group(1) + 'candidatas' + mo.group(1) + 'probe_ie1_v' + mo.group(2)))
    out.append((re.compile(r'(?<![A-Za-z0-9_])work([/\\]+)v(\d+)(?=[/\\\'"`\s)\],]|$)'),
                lambda mo: 'work' + mo.group(1) + 'ie1' + mo.group(1) + 'capas' + mo.group(1) + 'v' + mo.group(2)))
    for viejo, nuevo in TRANSLATION.items():
        out.append((re.compile(r'translation([/\\]+)' + viejo + r'(?![A-Za-z0-9_])'),
                    lambda mo, n=nuevo: 'translation' + mo.group(1) + n.replace('/', mo.group(1))))
    for nombre, carpeta in ROMS.items():
        out.append((re.compile(r'([Rr]oms)([/\\]+)' + re.escape(nombre)),
                    lambda mo, c=carpeta, n=nombre: mo.group(1) + mo.group(2) + c.replace('/', mo.group(2)) + mo.group(2) + n))
    return out


def ficheros_texto():
    bases = [ROOT / 'tools', ROOT / 'docs', ROOT / '.claude', ROOT / '.github', WORK, ROOT / 'translation']
    sueltos = [ROOT / n for n in ('AGENTS.md', 'CLAUDE.md', 'README.md', 'LEGAL.md', '.gitignore')]
    for b in bases:
        for p in b.rglob('*'):
            if p.is_file() and (p.suffix.lower() in TEXTO) and p.stat().st_size < 3 * 2**20 and p.name != Path(__file__).name:
                yield p
    yield from (p for p in sueltos if p.exists())


PARENTS = re.compile(r'(Path\(__file__\)(?:\.resolve\(\))?(?P<parent>\.parent)?|HERE)\.parents\[(?P<k>\d+)\]')


def corregir_parents(texto, viejo, nuevo):
    def sub(mo):
        k = int(mo.group('k'))
        base_v, base_n = (viejo.parent, nuevo.parent) if (mo.group(1) == 'HERE' or mo.group('parent')) else (viejo, nuevo)
        cadena_v = [base_v, *base_v.parents]
        if k + 1 < len(cadena_v) and base_v.parents[k] == ROOT:
            nk = list(base_n.parents).index(ROOT)
            return mo.group(0)[:mo.start('k') - mo.start()] + str(nk) + ']'
        return mo.group(0)
    return PARENTS.sub(sub, texto)


def main():
    aplicar = '--aplicar' in sys.argv
    m = mapa_work()
    movs = [(WORK / a, WORK / b) for a, b in m.items()]
    movs += [(ROOT / 'Roms' / n, ROOT / 'Roms' / c / n) for n, c in ROMS.items() if (ROOT / 'Roms' / n).exists()]
    rg = reglas(m)

    # 1) reescritura de rutas en texto y parents[] de los .py (antes de mover, con rutas viejas)
    destino_de = {}
    for a, b in movs:
        if a.is_dir():
            for p in a.rglob('*.py'):
                destino_de[p] = b / p.relative_to(a)
    cambiados = 0
    for p in ficheros_texto():
        try:
            t = p.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        n = t
        for rx, fn in rg:
            n = rx.sub(fn, n)
        if p in destino_de:
            n = corregir_parents(n, p, destino_de[p])
        if n != t:
            cambiados += 1
            if aplicar:
                p.write_text(n, encoding='utf-8')
            else:
                print('reescribir', p.relative_to(ROOT))
    print('ficheros con rutas reescritas:', cambiados)

    # 2) borrados de restos y movimientos
    for rel in BORRAR:
        if (WORK / rel).exists():
            print('borrar', rel)
            if aplicar:
                shutil.rmtree(WORK / rel)
    for a, b in movs:
        print('mover', a.relative_to(ROOT), '->', b.relative_to(ROOT))
        if aplicar:
            b.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(a), str(b))
    for rel in VACIAS:
        if aplicar:
            (WORK / rel).mkdir(parents=True, exist_ok=True)
    for viejo, nuevo in TRANSLATION.items():
        a, b = ROOT / 'translation' / viejo, ROOT / 'translation' / nuevo
        if a.exists():
            print('git mv', a.relative_to(ROOT), '->', b.relative_to(ROOT))
            if aplicar:
                b.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(['git', 'mv', str(a), str(b)], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()

