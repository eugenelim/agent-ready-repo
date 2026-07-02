#!/usr/bin/env python3
"""Self-test for ``lint-catalogue-curation-guard.py`` (RFC-0059 D6).

Proves the guard's pure logic catches each crafted bad case and passes the good
ones, without needing git or the real tree. Pure-stdlib; exit 0 = all pass,
1 = a case failed. Paired with the lint in ``build-check.yml``, matching the
``test-lint-profiles.py`` convention.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "guard", _HERE / "lint-catalogue-curation-guard.py"
)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

_failures: list[str] = []


def check(name: str, cond: bool) -> None:
    if not cond:
        _failures.append(name)


# --- classify_paths -------------------------------------------------------
check(
    "engine behavioural code is a hit",
    guard.classify_paths(["packages/agentbundle/agentbundle/scope.py"])
    == ["packages/agentbundle/agentbundle/scope.py"],
)
check(
    "credential-brokers is a hit",
    guard.classify_paths(["packs/credential-brokers/pack.toml"])
    == ["packs/credential-brokers/pack.toml"],
)
check(
    "build/recipes carve-out is NOT a hit",
    guard.classify_paths(
        ["packages/agentbundle/agentbundle/build/recipes/self-host.toml"]
    )
    == [],
)
check(
    "engine tests carve-out is NOT a hit (additive coverage, not behaviour)",
    guard.classify_paths(["packages/agentbundle/tests/unit/test_catalogue_curation_deps.py"])
    == [],
)
check(
    "credential-brokers is fully protected — even a test path is a hit",
    guard.classify_paths(["packs/credential-brokers/tests/test_x.py"])
    == ["packs/credential-brokers/tests/test_x.py"],
)
check(
    "unrelated pack path is NOT a hit",
    guard.classify_paths(["packs/catalogue-curation/pack.toml"]) == [],
)
check(
    "windows-separator path still classified",
    guard.classify_paths(["packages\\agentbundle\\agentbundle\\install.py"])
    == ["packages/agentbundle/agentbundle/install.py"],
)

# --- has_exemption --------------------------------------------------------
check("exemption present", guard.has_exemption("feat: x\n\nEngine-Change-RFC: 0061"))
check("exemption absent", not guard.has_exemption("feat: ordinary change"))

# --- check_presence -------------------------------------------------------
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    sk = root / guard.PACK_SKILLS_DIR
    good = sk / "good-skill"
    good.mkdir(parents=True)
    (good / "SKILL.md").write_text(
        "---\nname: good-skill\ndescription: d\n---\n\n"
        "Never write packages/agentbundle/ or packs/credential-brokers/ in this repo.\n",
        encoding="utf-8",
    )
    bad = sk / "bad-skill"
    bad.mkdir(parents=True)
    (bad / "SKILL.md").write_text(
        "---\nname: bad-skill\ndescription: d\n---\n\nNo refusal clause here.\n",
        encoding="utf-8",
    )
    viols = guard.check_presence(root)
    check("presence flags the skill missing the clause", any("bad-skill" in v for v in viols))
    check("presence passes the skill with the clause", not any("good-skill" in v for v in viols))

# absent pack ⇒ no presence violations (nothing to check)
with tempfile.TemporaryDirectory() as td:
    check("absent pack lints clean", guard.check_presence(Path(td)) == [])

# --- check_dup_sync -------------------------------------------------------
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    base = root / guard.PACK_SKILLS_DIR
    # write byte-identical ssrf_check.py to both skills, and a DRIFTED write_jail.py
    for skill in ("assimilate-primitive", "assimilate-repo"):
        d = base / skill / "scripts"
        d.mkdir(parents=True)
        (d / "ssrf_check.py").write_text("SAME\n", encoding="utf-8")
    (base / "export-catalogue" / "scripts").mkdir(parents=True)
    (base / "assimilate-primitive" / "scripts" / "write_jail.py").write_text("A\n", encoding="utf-8")
    (base / "assimilate-repo" / "scripts" / "write_jail.py").write_text("A\n", encoding="utf-8")
    (base / "export-catalogue" / "scripts" / "write_jail.py").write_text("DRIFTED\n", encoding="utf-8")
    viols = guard.check_dup_sync(root)
    check("dup-sync passes identical ssrf_check copies", not any("ssrf_check.py" in v for v in viols))
    check("dup-sync flags drifted write_jail copy", any("write_jail.py" in v and "drifted" in v for v in viols))

if _failures:
    for f in _failures:
        print(f"FAIL: {f}", file=sys.stderr)
    print(f"{len(_failures)} case(s) failed.", file=sys.stderr)
    raise SystemExit(1)
print("test-lint-catalogue-curation-guard: all cases passed.")
