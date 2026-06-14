#!/usr/bin/env python3
"""[Longitud VARIABLE] Reconstruye el .3ds con 3dstool (recalcula IVFC/NCCH) usando
archive_var.fa (pkb de longitud variable). A diferencia del parche in-place, aqui el
contenedor cambia de tamano, asi que hay que rehacer romfs -> cxi -> 3ds.

Pasos:
  1. fa_repack: archive_es.fa (fuentes/UI) + eve_var/*.pkb -> archive_var.fa
  2. extraer partes CXI del .3ds original (exefs/exh/logo/plain) si faltan
  3. poner archive_var.fa en work/romfs/, 3dstool -ctf romfs (recalcula IVFC)
  4. 3dstool -ctf cxi (recalcula hash NCCH) y -ctf 3ds
Salida: work/build/inazuma123_es_var.3ds
"""
import os, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "bin", "3dstool.exe")
ROM = os.path.join(REPO, "roms", "Inazuma Eleven 1-2-3 - Endou Mamoru Densetsu.3ds")
W = os.path.join(REPO, "work")
ROMFS_DIR = os.path.join(W, "romfs")


def run(*args):
    print(">", " ".join(os.path.basename(a) if a == TOOL else a for a in args))
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:]); print(r.stderr[-2000:])
        raise SystemExit(f"3dstool fallo ({r.returncode})")
    return r


def main():
    cxi = os.path.join(W, "part0.cxi")
    exefs = os.path.join(W, "exefs.bin"); exh = os.path.join(W, "exh.bin")
    logo = os.path.join(W, "logo.bin"); plain = os.path.join(W, "plain.bin")
    ncsd = os.path.join(W, "ncsd_header.bin"); ncch = os.path.join(W, "ncch_header.bin")
    romfs_bin = os.path.join(W, "romfs_new.bin")
    out = os.path.join(W, "build", "inazuma123_es_var.3ds")
    os.makedirs(os.path.join(W, "build"), exist_ok=True)

    # 1) fa_repack
    base = os.path.join(W, "archive_es.fa")
    varfa = os.path.join(W, "archive_var.fa")
    print("== fa_repack ==")
    run(sys.executable, os.path.join(REPO, "tools", "fa_repack.py"), base, varfa)

    # 2) extraer partes CXI si faltan
    if not (os.path.exists(exefs) and os.path.exists(exh)):
        print("== extraer CXI del .3ds original ==")
        run(TOOL, "-xtf", "3ds", ROM, "-0", cxi, "--header", ncsd)
        run(TOOL, "-xtf", "cxi", cxi, "--exefs", exefs, "--header", ncch,
            "--exh", exh, "--logo", logo, "--plain", plain)
    else:
        print("partes CXI ya extraidas")

    # secciones opcionales (esta NCCH puede no tener logo): incluir solo las que existen
    opt = []
    if os.path.exists(logo) and os.path.getsize(logo) > 0:
        opt += ["--logo", logo]
    if os.path.exists(plain) and os.path.getsize(plain) > 0:
        opt += ["--plain", plain]

    # 3) poner archive_var.fa en el romfs y reconstruir romfs.
    #    OJO: no perder el archive.fa ORIGINAL (lo necesita reinsert). Backup+restore.
    print("== copiar archive_var.fa al romfs y reconstruir romfs ==")
    import shutil
    romfs_fa = os.path.join(ROMFS_DIR, "archive.fa")
    orig_backup = os.path.join(W, "_archive_orig.fa")
    if not os.path.exists(orig_backup):
        print("  backup del archive.fa original ->", orig_backup)
        shutil.copyfile(romfs_fa, orig_backup)
    shutil.copyfile(varfa, romfs_fa)
    try:
        run(TOOL, "-ctf", "romfs", romfs_bin, "--romfs-dir", ROMFS_DIR)
    finally:
        shutil.copyfile(orig_backup, romfs_fa)         # restaurar original siempre
        print("  archive.fa original restaurado en el romfs")

    # 4) reconstruir cxi y 3ds
    print("== reconstruir cxi y 3ds ==")
    # --not-encrypt: conservar el flag NoCrypto (el ROM es descifrado); si no,
    # 3dstool limpia el bit 0x04 y Azahar lo da por "encriptado / region no valida".
    run(TOOL, "-ctf", "cxi", cxi, "--romfs", romfs_bin, "--exefs", exefs,
        "--header", ncch, "--exh", exh, "--not-encrypt", *opt)
    run(TOOL, "-ctf", "3ds", out, "-0", cxi, "--header", ncsd)
    print(f"\n-> {out}  ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    main()
