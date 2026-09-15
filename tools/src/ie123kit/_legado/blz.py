"""BLZ (backward-LZSS de Nintendo) — descompresor/compresor del `.code` (ejecutable
ARM11) del 3DS. El `.code` va comprimido (flag bit0 del exheader) y se procesa HACIA
ATRAS: los flags y los datos se leen desde el final, y la salida se escribe desde el
final. Necesario para parchear las funciones de texto que crashean (PC en code.bin).

Para reinsertar SIN recomprimir: descomprimir -> parchear -> dejar el .code PLANO y
poner el flag compress-code del exheader a 0 (el loader lo carga tal cual)."""
from ie123kit.nucleo.compresion.blz import *  # noqa: F401,F403


def main():
    import sys
    d = open(sys.argv[1], "rb").read()
    out = decompress(d)
    open(sys.argv[2], "wb").write(out)
    print(f"{len(d)} -> {len(out)} bytes")


if __name__ == "__main__":
    main()
