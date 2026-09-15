#!/usr/bin/env python3
"""[Longitud VARIABLE] Reconstruye el .3ds con 3dstool (recalcula IVFC/NCCH) usando
archive_var.fa (pkb de longitud variable). A diferencia del parche in-place, aqui el
contenedor cambia de tamano, asi que hay que rehacer romfs -> cxi -> 3ds.

Pasos:
  1. fa_repack: archive_es.fa (fuentes/UI) + eve_var/*.pkb -> archive_var.fa
  2. extraer partes CXI del .3ds original (exefs/exh/logo/plain) si faltan
  3. poner archive_var.fa en work/shared/base_3ds/romfs/, 3dstool -ctf romfs (recalcula IVFC)
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
    # 0) VALIDACION offline (red de seguridad): aborta ANTES de compilar si hay regresiones
    #    -> nunca se produce una ROM con un crash conocido (operandos corruptos, furigana
    #    que crece ❌#9, dialogo vacio...). SKIP_VALIDATE=1 para forzar (builds de prueba).
    if not os.environ.get("SKIP_VALIDATE"):
        sys.path.insert(0, os.path.join(REPO, "tools"))
        import validate
        print("== validate (red de seguridad pre-build) ==")
        if not validate.run():
            print("\n❌ VALIDACION FALLIDA -> NO se compila la ROM. (SKIP_VALIDATE=1 para forzar.)")
            sys.exit(1)

    cxi = os.path.join(W, "part0.cxi")
    exefs = os.path.join(W, "exefs.bin"); exh = os.path.join(W, "exh.bin")
    exefs_dir = os.path.join(W, "exefs_out")
    exh_exefs = os.path.join(W, "exh_exefs.bin")
    exefs_patched = os.path.join(W, "exefs_patched.bin")
    exh_patched = os.path.join(W, "exh_patched.bin")
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

    # 2b) extraer los FICHEROS del exefs (.code/banner/icon/logo) para parchear el .code
    if not os.path.exists(os.path.join(exefs_dir, "code.bin")):
        print("== extraer ficheros del exefs ==")
        run(TOOL, "-xtf", "exefs", exefs, "--exefs-dir", exefs_dir, "--header", exh_exefs)

    # secciones opcionales (esta NCCH puede no tener logo): incluir solo las que existen
    opt = []
    if os.path.exists(logo) and os.path.getsize(logo) > 0:
        opt += ["--logo", logo]
    if os.path.exists(plain) and os.path.getsize(plain) > 0:
        opt += ["--plain", plain]

    # 3a) PARCHE del CRO de ruby (idempotente): bounds-check que evita el crash del furigana
    #     al traducir (ver tools/patch_cro.py — ingenieria inversa de ina_main1.cro). Sin esto
    #     el texto completo (FULLTEXT) crashea (el muro ❌#1/#9 era del codigo, no de los datos).
    sys.path.insert(0, os.path.join(REPO, "tools"))
    # SKIP_CRO=1: NO parchear el CRO. La zona del cave (0x50E14/0xAD9E14) es de RELOCACION:
    # el loader la pisa al cargar -> el parche se corrompe -> crash 0xAD9E1C (confirmado por
    # log). Con NO_BLANK (lectura original) la ruby no se dispara y el parche sobra: restaurar
    # el CRO original.
    cro_path = os.path.join(ROMFS_DIR, "cro", "ina_main1.cro")
    if os.environ.get("SKIP_CRO"):
        _orig = cro_path + ".orig"
        if os.path.exists(_orig):
            open(cro_path, "wb").write(open(_orig, "rb").read())
        print("== CRO SIN parchear (SKIP_CRO; original restaurado) ==")
    else:
        import patch_cro
        _cb = bytearray(open(cro_path, "rb").read())
        if patch_cro.patch(_cb):
            open(cro_path, "wb").write(_cb); print("== CRO ruby PARCHEADO (bounds-check 0xABFCC0) ==")
        else:
            print("== CRO ruby ya parcheado ==")

    # 3b) PARCHE de code.bin (bounds-checks de las funciones de texto strcpy/getc/strcmp que
    #     crashean con el texto traducido) -> exefs reconstruido con el .code PLANO + flag
    #     compress-code a 0. Ver tools/patch_code.py + patch_exefs.py (ingenieria inversa).
    import patch_exefs, patch_code
    npatch, plain_sz = patch_exefs.build_exefs(exefs_dir, exefs_patched)
    ts = patch_code.NEW_TEXT_SIZE if npatch else None
    patch_exefs.patch_exheader(exh, exh_patched, text_size=ts)
    print(f"== code.bin PARCHEADO: {npatch} bounds-checks, plano {plain_sz}B; compress-flag->0; text_size->{ts} ==")

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
    run(TOOL, "-ctf", "cxi", cxi, "--romfs", romfs_bin, "--exefs", exefs_patched,
        "--header", ncch, "--exh", exh_patched, "--not-encrypt", *opt)
    run(TOOL, "-ctf", "3ds", out, "-0", cxi, "--header", ncsd)
    print(f"\n-> {out}  ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    main()
