#!/usr/bin/env python3
"""Prove `tools/run-pip-audit-gate.py` still speaks before the recipe trusts it.

A live audit against a healthy feed is silent both when the gate works and when
it has been broken into a no-op, so the recipe runs this first — the same order
and the same reason as the two sibling SCA self-tests (ADR-0084, ADR-0083).

Every case drives the wrapper's pure decision seam against synthetic pip-audit
JSON, so none of them touches the network or resolves anything. Each asserts the
exit code AND that the message names the entry, advisory or dependency: an exit
code alone does not tell a contributor what to do.

Run: python3 tools/test-run-pip-audit-gate.py
Exit 0 = every case passed, 1 = at least one failed.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess  # nosec B404  # no process is spawned here; used for its exception types
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_HERE = Path(__file__).resolve().parent


def _load_gate():
    """Import the hyphenated wrapper by path, the way its siblings' tests do."""
    spec = importlib.util.spec_from_file_location(
        "run_pip_audit_gate", _HERE / "run-pip-audit-gate.py"
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise SystemExit("test-run-pip-audit-gate: cannot load run-pip-audit-gate.py")
    module = importlib.util.module_from_spec(spec)
    # Register before executing: @dataclass resolves annotations through
    # sys.modules[cls.__module__], which is None for an unregistered module.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_FAILURES: list[str] = []
_PASSES = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global _PASSES
    if condition:
        _PASSES += 1
    else:
        _FAILURES.append(f"{name}{': ' + detail if detail else ''}")


def entry(**overrides) -> dict:
    """A complete, valid allowlist entry; override one field per case."""
    base = {
        "id": "CVE-2026-102268",
        "package": "pyjwt",
        "fixed_in": "2.14.0",
        "reason": "trigger, and why this invocation cannot reach it",
        "unblocked_when": "Semgrep permits PyJWT>=2.14.0",
    }
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not _OMIT}


_OMIT = object()


def allowlist(entries=None, allowed=("pyjwt",)) -> dict:
    return {
        "allowed_packages": list(allowed),
        "allow": [entry()] if entries is None else entries,
    }


def dep(name="pyjwt", version="2.13.0", vulns=None) -> dict:
    return {"name": name, "version": version, "vulns": vulns or []}


def vuln(vid="CVE-2026-102268", fix=("2.14.0",), aliases=()) -> dict:
    return {
        "id": vid,
        "fix_versions": list(fix),
        "aliases": list(aliases),
        "description": "synthetic",
    }


def report(deps=None) -> dict:
    """A report carrying the three direct requirements plus whatever is passed."""
    floor = [dep("bandit", "1.9.0"), dep("pip-audit", "2.10.1"), dep("semgrep", "1.178.0")]
    return {"dependencies": floor + list(deps or []), "fixes": []}


FLOOR = frozenset({"bandit", "pip-audit", "semgrep"})


def run(gate, rep, alw, floor=FLOOR):
    """Call the decision seam, returning (exit_code, joined message text)."""
    verdict = gate.evaluate(rep, alw, floor)
    return verdict.exit_code, "\n".join(verdict.lines)


def main() -> int:
    gate = _load_gate()
    pyjwt_vulns = [vuln()]

    # 1. The whole contract's happy path.
    code, msg = run(gate, report([dep(vulns=pyjwt_vulns)]), allowlist())
    check("1 clean accepted tree exits 0", code == 0, f"got {code}: {msg}")
    check("1 prints the suppression with its package", "pyjwt" in msg and "CVE-2026-102268" in msg, msg)

    # 2-9. AC2 — an undocumented or out-of-bounds entry is a tool error.
    for case, bad in (
        ("2 missing id", entry(id=_OMIT)),
        ("3 missing package", entry(package=_OMIT)),
        ("4 missing reason", entry(reason=_OMIT)),
        ("5 blank unblocked_when", entry(unblocked_when="   ")),
        ("6 missing fixed_in", entry(fixed_in=_OMIT)),
        ("7 non-string field", entry(reason=42)),
    ):
        code, msg = run(gate, report([dep(vulns=pyjwt_vulns)]), allowlist([bad]))
        check(f"{case} exits 2", code == 2, f"got {code}: {msg}")
        check(f"{case} names the entry", "pyjwt" in msg or "CVE-2026-102268" in msg, msg)

    code, msg = run(gate, report([dep(vulns=pyjwt_vulns)]), {"allowed_packages": ["pyjwt"], "allow": "nope"})
    check("8 allow not an array of tables exits 2", code == 2, f"got {code}: {msg}")
    check("8 names the offending structure", "array of tables" in msg, msg)

    code, msg = run(gate, report([dep(vulns=pyjwt_vulns)]), allowlist([entry(), entry()]))
    check("9a duplicate entry exits 2", code == 2, f"got {code}: {msg}")
    check("9a names it a duplicate, not an absent advisory",
          "duplicates an earlier entry" in msg, msg)

    code, msg = run(
        gate, report([dep(vulns=pyjwt_vulns)]), allowlist([entry(package="cryptography")])
    )
    check("9 package outside allowed_packages exits 2", code == 2, f"got {code}: {msg}")
    check("9 names both package and bound", "cryptography" in msg and "pyjwt" in msg, msg)

    # 10-13. AC3 — matching, and what must not match.
    code, msg = run(
        gate,
        report([dep(vulns=[vuln(), vuln("CVE-2026-999999")])]),
        allowlist(),
    )
    check("10 unallowlisted advisory exits 1", code == 1, f"got {code}: {msg}")
    check("10 names the id", "CVE-2026-999999" in msg, msg)

    code, msg = run(
        gate,
        report([dep("cryptography", "42.0.0", [vuln()])]),
        allowlist(),
    )
    # Exit 2, not 1: the entry matches nothing, which trips the retirement
    # branch, and AC8's precedence puts exit 2 above the blocking advisory.
    check("11 same id on another package is not suppressed", code == 2, f"got {code}: {msg}")
    check("11 the advisory is reported as blocking", "CVE-2026-102268" in msg, msg)

    code, msg = run(gate, report([dep("PyJWT", "2.13.0", pyjwt_vulns)]), allowlist())
    check("12 PEP 503 canonicalisation matches PyJWT to pyjwt", code == 0, f"got {code}: {msg}")

    code, msg = run(
        gate,
        report([dep(vulns=[vuln("PYSEC-2026-1", aliases=("CVE-2026-102268",))])]),
        allowlist(),
    )
    check("13 alias is not a match path", code == 2, f"got {code}: {msg}")
    check("13 the unmatched primary id is reported", "PYSEC-2026-1" in msg, msg)

    # 14-18. AC4 — only a real retirement reads as one.
    absent = report([dep("pyjwt", "2.14.0")])
    code, msg = run(gate, absent, allowlist())
    check("14 advisory gone and fix present exits 2", code == 2, f"got {code}: {msg}")
    check("14 says the retirement condition fired", "retirement condition fired" in msg.lower(), msg)
    check("14 carries the remove action token", gate.ACTION_REMOVE in msg, msg)

    code, msg = run(gate, report([dep("pyjwt", "2.13.0")]), allowlist())
    check("15 advisory gone, fix absent exits 2", code == 2, f"got {code}: {msg}")
    check("15 withholds the remove action", gate.ACTION_REMOVE not in msg and gate.ACTION_HOLD in msg, msg)

    code, msg = run(gate, report([dep("pyjwt", "2.14.0rc1")]), allowlist())
    check("16 unorderable resolved version exits 2", code == 2, f"got {code}: {msg}")
    check("16 says the versions could not be compared", "could not" in msg.lower(), msg)
    check("16 withholds the remove action", gate.ACTION_REMOVE not in msg and gate.ACTION_HOLD in msg, msg)

    code, msg = run(gate, report([dep("pyjwt", "2.14.0")]), allowlist([entry(fixed_in="2.14.0-beta")]))
    check("16a unorderable fixed_in exits 2", code == 2, f"got {code}: {msg}")
    check("16a withholds the remove action", gate.ACTION_REMOVE not in msg and gate.ACTION_HOLD in msg, msg)

    code, msg = run(gate, report(), allowlist())
    check("17 package absent from report exits 2", code == 2, f"got {code}: {msg}")
    check("17 says nothing was audited for it", "audit" in msg.lower(), msg)
    check("17 withholds the remove action", gate.ACTION_REMOVE not in msg and gate.ACTION_HOLD in msg, msg)

    code, msg = run(gate, report([dep("pyjwt", "2.9.0")]), allowlist())
    check("18 2.9.0 is below 2.14.0 (reddens on a string compare)", code == 2, f"got {code}: {msg}")
    check("18 withholds the remove action", gate.ACTION_REMOVE not in msg and gate.ACTION_HOLD in msg, msg)

    # 19. AC5 — fixed_in cannot drift or disable the detector.
    code, msg = run(
        gate, report([dep(vulns=[vuln(fix=("2.14.0",))])]), allowlist([entry(fixed_in="99.0.0")])
    )
    check("19 fixed_in absent from fix_versions exits 2", code == 2, f"got {code}: {msg}")
    check("19 names the disagreement", "99.0.0" in msg, msg)

    code, msg = run(
        gate, report([dep(vulns=[vuln(fix=("2.14.0",))])]), allowlist([entry(fixed_in="2.14")])
    )
    check("19a 2.14 equals published 2.14.0 (reddens without zero-padding)", code == 0, f"got {code}: {msg}")

    # An undecidable comparison must not be reported as a decided mismatch: the
    # obvious remedy for "matches none" is to copy the published string into
    # fixed_in, which parks the entry permanently in AC4's safe branch.
    code, msg = run(
        gate,
        report([dep(vulns=[vuln(fix=("2.14.0rc1",))])]),
        allowlist([entry(fixed_in="2.14.0rc1")]),
    )
    check("19b undecidable fix_versions exits 2", code == 2, f"got {code}: {msg}")
    check("19b says it could not compare, not that they disagree",
          "could not be compared" in msg and "matches none" not in msg, msg)

    code, msg = run(gate, report([dep(vulns=[vuln(fix=())])]), allowlist())
    check("19c empty fix_versions exits 2", code == 2, f"got {code}: {msg}")
    check("19c names it a feed condition, not an entry error", "feed condition" in msg, msg)

    # 20-21. AC6 — an unaudited tree is not a clean one.
    skipped = report([dep(vulns=pyjwt_vulns)])
    skipped["dependencies"].append({"name": "flaky-dep", "skip_reason": "not found on index"})
    code, msg = run(gate, skipped, allowlist())
    check("20 skipped dependency exits 2", code == 2, f"got {code}: {msg}")
    check("20 names the skipped dependency", "flaky-dep" in msg, msg)

    thin = {"dependencies": [dep("bandit", "1.9.0"), dep(vulns=pyjwt_vulns)], "fixes": []}
    code, msg = run(gate, thin, allowlist())
    check("21 missing direct requirement exits 2", code == 2, f"got {code}: {msg}")
    check("21 names what is missing", "semgrep" in msg or "pip-audit" in msg, msg)

    code, msg = run(gate, report([dep(vulns=pyjwt_vulns)]), allowlist(), floor=frozenset())
    check("21a empty derived floor exits 2", code == 2, f"got {code}: {msg}")
    check("21a says the floor is empty", "floor" in msg and "empty" in msg, msg)

    for case, alw in (
        ("21b allowed_packages absent", {"allow": [entry()]}),
        ("21b allowed_packages a bare string", {"allowed_packages": "pyjwt", "allow": [entry()]}),
        ("21b allowed_packages holds a non-string", {"allowed_packages": [1], "allow": [entry()]}),
    ):
        code, msg = run(gate, report([dep(vulns=pyjwt_vulns)]), alw)
        check(f"{case} exits 2", code == 2, f"got {code}: {msg}")
        check(f"{case} names the field", "allowed_packages" in msg, msg)

    # An include line would narrow the audited floor without saying so.
    with tempfile.TemporaryDirectory() as tmp:
        manifest = Path(tmp) / "requirements-with-include.txt"
        manifest.write_text("bandit>=1.9\n-r other.txt\n", encoding="utf-8")
        raised = False
        try:
            gate.direct_requirements(manifest)
        except gate.GateError:
            raised = True
        check("21c an include line is a gate error, not a silent narrowing", raised)

        empty = Path(tmp) / "requirements-empty.txt"
        empty.write_text("# only a comment\n", encoding="utf-8")
        named = ""
        try:
            gate.direct_requirements(empty)
        except gate.GateError as exc:
            named = str(exc)
        check("21d an empty derivation names the manifest it came from",
              "requirements-empty.txt" in named, named or "no GateError raised")

    # 22. AC8 — exit 2 beats exit 1, and both are printed.
    both = report([dep(vulns=[vuln(), vuln("CVE-2026-999999")])])
    both["dependencies"].append({"name": "flaky-dep", "skip_reason": "not found on index"})
    code, msg = run(gate, both, allowlist())
    check("22 exit 2 wins over exit 1", code == 2, f"got {code}: {msg}")
    check("22 prints the blocking advisory too", "CVE-2026-999999" in msg, msg)
    check("22 prints the skipped dependency too", "flaky-dep" in msg, msg)

    # 23. AC7 — the environment is built by rule.
    dirty = {
        "PIP_CONSTRAINT": "evil-constraints.txt",
        "PIP_INDEX_URL": "https://evil.example",
        "PIP_AUDIT_OSV_URL": "https://evil.example",
        "HTTPS_PROXY": "http://evil.example",
        "https_proxy": "http://evil.example",
        "all_proxy": "http://evil.example",
        "REQUESTS_CA_BUNDLE": "evil-bundle.pem",
        "PATH": "/usr/bin",
    }
    built = gate.build_env(dirty)
    for name in ("PIP_CONSTRAINT", "PIP_INDEX_URL", "PIP_AUDIT_OSV_URL", "HTTPS_PROXY",
                 "https_proxy", "all_proxy", "REQUESTS_CA_BUNDLE"):
        check(f"23 {name} is scrubbed", name not in built, f"still present: {built.get(name)!r}")
    check("23 PATH is preserved (stated envelope)", built.get("PATH") == "/usr/bin", repr(built.get("PATH")))

    # urllib case-folds every key before matching *_proxy, so a mixed-case
    # spelling is honoured exactly as the canonical one is.
    built = gate.build_env({"Https_Proxy": "http://evil.example", "Http_Proxy": "http://evil.example"})
    check("23c mixed-case proxy names are scrubbed",
          not [k for k in built if "proxy" in k.lower()],
          f"survived: {[k for k in built if 'proxy' in k.lower()]}")

    built = gate.build_env({"PIP_CONFIG_FILE": "/etc/pip.conf"})
    check(
        "23a PIP_CONFIG_FILE is set to os.devnull, not removed",
        built.get("PIP_CONFIG_FILE") == os.devnull,
        f"got {built.get('PIP_CONFIG_FILE')!r}",
    )

    # 23b-27. AC8 — how pip-audit's own outcome is read.
    class _Completed:
        def __init__(self, returncode, stdout):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = ""

    payload = '{"dependencies": [], "fixes": []}'
    parsed = gate.run_audit(
        "tools/requirements-sast.txt", runner=lambda *a, **k: _Completed(1, payload)
    )
    check("23b returncode 1 with parseable JSON proceeds", parsed == {"dependencies": [], "fixes": []}, repr(parsed))

    def _timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd="pip-audit", timeout=300)

    text = _raises(gate, _timeout)
    check("24 timeout is a GateError", bool(text), "no GateError raised")
    check("24 names the timeout and the manifest",
          "exceeded" in text and "requirements-sast.txt" in text, text)

    def _garbage(*a, **k):
        return _Completed(1, "not json at all")

    text = _raises(gate, _garbage)
    check("25 unparseable stdout is a GateError", bool(text), "no GateError raised")
    check("25 distinguishes unparseable output from a finding",
          "unparseable" in text, text)

    def _missing(*a, **k):
        raise FileNotFoundError("pip-audit")

    text = _raises(gate, _missing)
    check("26 absent binary is a GateError", bool(text), "no GateError raised")
    check("26 names the tool it could not run", "pip-audit" in text, text)

    # 27. An unexpected internal failure must not leak Python's default exit 1.
    #     Uses a manifest the case controls, so it cannot pass via a GateError
    #     from a relative path that does not resolve in the caller's cwd.
    with tempfile.TemporaryDirectory() as tmp:
        owned = Path(tmp) / "requirements.txt"
        owned.write_text("bandit>=1.9\npip-audit>=2.10\nsemgrep>=1.174\n", encoding="utf-8")
        buffer = io.StringIO()
        with contextlib.redirect_stderr(buffer):
            code = gate.main([str(owned)], _audit=_boom, _allowlist=lambda: allowlist())
        text = buffer.getvalue()
    check("27 unexpected exception exits 2, not 1", code == 2, f"got {code}")
    check("27 reports it as an internal error, not a manifest error",
          "internal error" in text and "RuntimeError" in text, text)

    # 28. The `fixed_in = "none"` sentinel: accepting an advisory upstream has
    #     not fixed. The risk it introduces is a permanent mute, so every case
    #     below exists to prove the entry still has a live retirement trigger.
    unfixed = [entry(id="CVE-2026-103001", fixed_in=gate.UNFIXED,
                     unblocked_when="PyJWT publishes any release fixing it")]
    nofix = [vuln(vid="CVE-2026-103001", fix=())]

    code, msg = run(gate, report([dep(vulns=nofix)]), allowlist(unfixed))
    check("28a unfixed entry against an unfixed advisory exits 0", code == 0, f"got {code}: {msg}")
    check("28a reports it as accepted with its retirement condition",
          "CVE-2026-103001" in msg and "retires when" in msg, msg)

    # The mirror of D6. A normal entry is wrong when the feed does not know its
    # fixed_in; this one is wrong as soon as the feed knows ANY fix.
    fixed_now = [vuln(vid="CVE-2026-103001", fix=("2.16.0",))]
    code, msg = run(gate, report([dep(vulns=fixed_now)]), allowlist(unfixed))
    check("28b a fix appearing retires the sentinel, exit 2", code == 2, f"got {code}: {msg}")
    check("28b names the published fix and the entry", "2.16.0" in msg and "CVE-2026-103001" in msg, msg)
    check("28b holds rather than telling anyone to delete the acceptance",
          gate.ACTION_HOLD in msg and gate.ACTION_REMOVE not in msg, msg)

    # The advisory going quiet is a withdrawal or a degraded feed. With no
    # release to compare against it can never be an arriving remediation, so
    # this must not reach the one branch that says "remove this entry".
    code, msg = run(gate, report([dep(vulns=[])]), allowlist(unfixed))
    check("28c an unfixed advisory going absent exits 2", code == 2, f"got {code}: {msg}")
    check("28c refuses to read absence as the fix landing",
          "cannot mean the fix landed" in msg, msg)
    check("28c holds rather than retiring it",
          gate.ACTION_HOLD in msg and gate.ACTION_REMOVE not in msg, msg)

    # A real release string must keep its old meaning: the sentinel is opt-in,
    # never inferred from an empty feed.
    code, msg = run(gate, report([dep(vulns=nofix)]), allowlist([entry(id="CVE-2026-103001")]))
    check("28d a release-valued entry still exits 2 on an empty feed", code == 2, f"got {code}: {msg}")
    check("28d points the maintainer at the sentinel",
          "feed condition" in msg and gate.UNFIXED in msg, msg)

    # Spelling robustness: the TOML is hand-edited, so the sentinel is matched
    # case- and whitespace-insensitively rather than by exact bytes.
    for spelling in ("None", " none "):
        code, _ = run(gate, report([dep(vulns=nofix)]),
                      allowlist([entry(id="CVE-2026-103001", fixed_in=spelling)]))
        check(f"28e sentinel spelled {spelling!r} is honoured", code == 0, f"got {code}")

    print(f"test-run-pip-audit-gate: {_PASSES} passed, {len(_FAILURES)} failed")
    for failure in _FAILURES:
        print(f"  FAIL {failure}", file=sys.stderr)
    return 1 if _FAILURES else 0


def _raises(gate, runner) -> str:
    """The GateError's text, or "" when none was raised.

    Returns the message rather than a bool so each case can assert what a
    contributor is actually told, not merely that something failed.
    """
    try:
        gate.run_audit("tools/requirements-sast.txt", runner=runner)
    except gate.GateError as exc:
        return str(exc) or "<empty message>"
    except Exception:  # noqa: BLE001 - any other escape is itself the failure
        return ""
    return ""


def _boom(*args, **kwargs):
    raise RuntimeError("synthetic internal failure")


if __name__ == "__main__":
    raise SystemExit(main())
