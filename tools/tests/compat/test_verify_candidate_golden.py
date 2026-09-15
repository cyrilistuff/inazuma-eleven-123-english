"""verify_candidate (shim → ie123kit._legado.verify_candidate) reproduce el informe del commit 0af2abd."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ie123kit.nucleo.config.raiz import find_root

pytestmark = pytest.mark.requiere_rom

RAIZ = find_root()
GOLDEN = Path(__file__).resolve().parent / "golden" / "verify_v66_v67.json"
CANDIDATAS = RAIZ / "work" / "shared" / "candidatas"


@pytest.mark.skipif(not all((CANDIDATAS / f"probe_ie1_v{n}" / "archive.fa").is_file() for n in (66, 67)),
                    reason="faltan las candidatas probe_ie1_v66/v67")
def test_verify_candidate_igual_al_golden():
    g = json.loads(GOLDEN.read_text(encoding="utf-8"))
    env = dict(os.environ)
    env.pop("IE123_ROOT", None)
    r = subprocess.run([sys.executable, "-X", "utf8", "tools/verify_candidate.py", *g["orden"]], cwd=RAIZ, env=env,
                       capture_output=True, text=True, encoding="utf-8", check=False)
    verify = CANDIDATAS / "probe_ie1_v67" / "verify.json"
    assert r.returncode == g["returncode"]
    assert r.stdout == g["stdout"]
    assert r.stderr == g["stderr"]
    obtenido = json.loads(verify.read_text(encoding="utf-8")) if verify.is_file() else None
    assert obtenido == g["verify_json"]
