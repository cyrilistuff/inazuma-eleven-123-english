"""Limpieza de work/ según docs/ARQUITECTURA.md.

Borra lo que se puede regenerar o está superado: candidatas probe_ie1_vN que no sean las dos últimas,
imágenes de ROM reconstruidas de releases publicadas, volcados de texturas de auditorías antiguas,
descargas duplicadas de herramientas, cachés y temporales (.partial, .yuv, __pycache__, *_x2.png).
Nunca toca: shared/base_3ds, ieN/fuentes, Roms, capas vN con scripts, docs ni tools.
Uso: python tools/limpiar_work.py            (solo lista)
     python tools/limpiar_work.py --borrar   (borra)
"""
import shutil
import sys

from ie123kit.nucleo.construir.limpieza import *  # noqa: F401,F403


def main():
    borrar = '--borrar' in sys.argv
    total = 0
    for p in objetivos():
        s = tam(p)
        total += s
        print(f'{s / 2**20:9.1f} MB  {p.relative_to(ROOT)}')
        if borrar and p.exists():
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    print(f'{"borrados" if borrar else "a borrar"}: {total / 2**30:.2f} GB')


if __name__ == '__main__':
    main()


