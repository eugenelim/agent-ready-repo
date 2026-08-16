#!/usr/bin/env python3
"""Self-test for tools/audit-npm.py — the npm SCA leg of `make sast`.

Runs in `make sast` immediately *before* the live audit, and in
`tools/test-all.py`. The reason it exists is the same one stated in the `sast`
recipe for `tools/test-audit-requirements.py` and
`tools/test-semgrep-argv-boundary.py`: **a live audit against a healthy registry
is silent both when the gate works and when it has been broken into a no-op, so
it cannot tell the two apart.** Only fixtures can.

Two cases here are load-bearing beyond ordinary coverage — `error_payload_is_tool_error`
and `missing_report_version_is_tool_error`. They pin spec AC1a: a registry
outage, a proxy returning an HTML error page, or a corporate MITM must never be
indistinguishable from "no vulnerabilities found". `npm audit` exits non-zero
for *both* "found advisories" and "could not run", so the verdict has to come
from the payload, and the failing-closed path is exactly the one a healthy CI
run never exercises.

Pure stdlib. No network, no `npm` binary, no filesystem outside a tmpdir.
Exit 0 = every case passed; 1 = at least one failed.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SUBJECT = REPO_ROOT / "tools" / "audit-npm.py"


def _load_subject():
    """Import audit-npm.py by path — its filename is not a legal module name.

    The module is registered in `sys.modules` *before* `exec_module`: the
    subject defines `@dataclass` types, and `dataclasses` resolves each field's
    annotations through `sys.modules[cls.__module__]`. Loading by spec without
    registering first leaves that lookup returning None.
    """
    cached = sys.modules.get("audit_npm")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("audit_npm", SUBJECT)
    if spec is None or spec.loader is None:  # pragma: no cover - import plumbing
        raise RuntimeError(f"cannot load {SUBJECT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_npm"] = module
    spec.loader.exec_module(module)
    return module


# ── Fixtures ────────────────────────────────────────────────────────────────
# Shaped from real `npm audit --json --package-lock-only` output (npm 11):
# `via` entries are either an advisory dict carrying its own `severity` and a
# GitHub advisory `url`, or a bare string naming another vulnerable package.


def _advisory(name: str, severity: str, ghsa: str, source: int) -> dict:
    return {
        "source": source,
        "name": name,
        "dependency": name,
        "title": f"{name}: synthetic advisory for tests",
        "url": f"https://github.com/advisories/{ghsa}",
        "severity": severity,
        "cwe": ["CWE-000"],
        "range": "<1.0.0",
    }


def _report(*packages: tuple[str, str, list]) -> dict:
    return {
        "auditReportVersion": 2,
        "vulnerabilities": {
            name: {"name": name, "severity": severity, "isDirect": False, "via": via}
            for name, severity, via in packages
        },
        "metadata": {"vulnerabilities": {"total": len(packages)}},
    }


CLEAN = {"auditReportVersion": 2, "vulnerabilities": {}, "metadata": {}}

HIGH = _report(("js-yaml", "high", [_advisory("js-yaml", "high", "GHSA-aaaa-bbbb-cccc", 1)]))

CRITICAL = _report(("evil", "critical", [_advisory("evil", "critical", "GHSA-dddd-eeee-ffff", 2)]))

MODERATE = _report(("postcss", "moderate", [_advisory("postcss", "moderate", "GHSA-1111-2222-3333", 3)]))

# A high advisory plus a package that is only vulnerable *through* it — the
# string-`via` chain link. Suppressing the root advisory must suppress the chain.
CHAINED = _report(
    ("js-yaml", "high", [_advisory("js-yaml", "high", "GHSA-aaaa-bbbb-cccc", 1)]),
    ("some-consumer", "high", ["js-yaml"]),
)

ERROR_PAYLOAD = {"error": {"code": "ENETUNREACH", "summary": "request to registry failed"}}

NO_VERSION = {"vulnerabilities": {}, "metadata": {}}


# ── Harness ─────────────────────────────────────────────────────────────────

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ✓ {name}")
    else:
        FAILURES.append(name)
        print(f"  ✖ {name}{': ' + detail if detail else ''}", file=sys.stderr)


def expect_error(name: str, fn) -> None:
    """The subject raised AuditError — i.e. the caller will exit 2."""
    m = _load_subject()
    try:
        fn()
    except m.AuditError:
        print(f"  ✓ {name}")
    except Exception as exc:  # noqa: BLE001 - any other type is the failure
        FAILURES.append(name)
        print(f"  ✖ {name}: raised {type(exc).__name__}, expected AuditError", file=sys.stderr)
    else:
        FAILURES.append(name)
        print(f"  ✖ {name}: returned normally, expected AuditError", file=sys.stderr)


def main() -> int:
    if not SUBJECT.is_file():
        print(f"✖ subject not found: {SUBJECT}", file=sys.stderr)
        return 1
    m = _load_subject()

    print("evaluate() — severity threshold")
    check("clean_report_passes", m.evaluate(CLEAN, {}).blocking == [])
    check("high_finding_blocks", [f.advisory_id for f in m.evaluate(HIGH, {}).blocking]
          == ["GHSA-aaaa-bbbb-cccc"])
    check("critical_finding_blocks", [f.advisory_id for f in m.evaluate(CRITICAL, {}).blocking]
          == ["GHSA-dddd-eeee-ffff"])
    check("moderate_finding_does_not_block", m.evaluate(MODERATE, {}).blocking == [])

    print("evaluate() — allowlist")
    allow = {"GHSA-aaaa-bbbb-cccc": {"reason": "r", "unblocked_when": "u"}}
    verdict = m.evaluate(HIGH, allow)
    check("allowlisted_high_passes", verdict.blocking == [])
    check("allowlisted_high_is_reported",
          [f.advisory_id for f in verdict.suppressed] == ["GHSA-aaaa-bbbb-cccc"],
          f"suppressed={verdict.suppressed}")
    chained = m.evaluate(CHAINED, allow)
    check("suppressing_root_advisory_suppresses_chain", chained.blocking == [],
          f"blocking={[f.advisory_id for f in chained.blocking]}")
    check("unrelated_allowlist_entry_does_not_suppress",
          [f.advisory_id for f in m.evaluate(HIGH, {"GHSA-zzzz-zzzz-zzzz":
                                                    {"reason": "r", "unblocked_when": "u"}}).blocking]
          == ["GHSA-aaaa-bbbb-cccc"])

    print("evaluate() — fail-closed (spec AC1a)")
    expect_error("error_payload_is_tool_error", lambda: m.evaluate(ERROR_PAYLOAD, {}))
    expect_error("missing_report_version_is_tool_error", lambda: m.evaluate(NO_VERSION, {}))
    expect_error("non_dict_payload_is_tool_error", lambda: m.evaluate([], {}))

    print("load_allowlist() — incomplete entries are a tool error, not a pass")
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)

        empty = d / "empty.toml"
        empty.write_text("", encoding="utf-8")
        check("empty_allowlist_loads_as_empty", m.load_allowlist(empty) == {})

        good = d / "good.toml"
        good.write_text(
            '[[allow]]\nid = "GHSA-aaaa-bbbb-cccc"\nreason = "r"\nunblocked_when = "u"\n',
            encoding="utf-8",
        )
        check("complete_entry_loads",
              m.load_allowlist(good) == {"GHSA-aaaa-bbbb-cccc":
                                         {"reason": "r", "unblocked_when": "u"}})

        for field in ("reason", "unblocked_when"):
            bad = d / f"missing_{field}.toml"
            lines = ['[[allow]]', 'id = "GHSA-aaaa-bbbb-cccc"',
                     'reason = "r"', 'unblocked_when = "u"']
            lines = [ln for ln in lines if not ln.startswith(field)]
            bad.write_text("\n".join(lines) + "\n", encoding="utf-8")
            expect_error(f"allowlist_missing_{field}_is_tool_error",
                         lambda p=bad: m.load_allowlist(p))

        blank = d / "blank_reason.toml"
        blank.write_text(
            '[[allow]]\nid = "GHSA-aaaa-bbbb-cccc"\nreason = "  "\nunblocked_when = "u"\n',
            encoding="utf-8",
        )
        expect_error("allowlist_whitespace_reason_is_tool_error",
                     lambda: m.load_allowlist(blank))

        noid = d / "no_id.toml"
        noid.write_text('[[allow]]\nreason = "r"\nunblocked_when = "u"\n', encoding="utf-8")
        expect_error("allowlist_missing_id_is_tool_error", lambda: m.load_allowlist(noid))

    print("discover_lockfiles()")
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / "docs-site").mkdir()
        (root / "docs-site" / "package-lock.json").write_text("{}", encoding="utf-8")
        (root / "web").mkdir()
        (root / "web" / "package-lock.json").write_text("{}", encoding="utf-8")
        nested = root / "web" / "node_modules" / "dep"
        nested.mkdir(parents=True)
        (nested / "package-lock.json").write_text("{}", encoding="utf-8")
        hidden = root / ".cache" / "x"
        hidden.mkdir(parents=True)
        (hidden / "package-lock.json").write_text("{}", encoding="utf-8")

        found = [p.relative_to(root).as_posix() for p in m.discover_lockfiles(root)]
        check("discovers_project_lockfiles",
              found == ["docs-site/package-lock.json", "web/package-lock.json"],
              f"found={found}")
        check("skips_node_modules", not any("node_modules" in f for f in found))
        check("skips_dot_directories", not any(f.startswith(".") for f in found))

    print("advisory_id() — GHSA/CVE from url, else npm source id")
    check("id_from_ghsa_url",
          m.advisory_id({"url": "https://github.com/advisories/GHSA-aaaa-bbbb-cccc",
                         "source": 7}) == "GHSA-aaaa-bbbb-cccc")
    check("id_from_cve_url",
          m.advisory_id({"url": "https://github.com/advisories/CVE-2026-59870",
                         "source": 7}) == "CVE-2026-59870")
    check("id_falls_back_to_source",
          m.advisory_id({"source": 7}) == "npm:7")

    print()
    if FAILURES:
        print(f"✖ audit-npm self-test: {len(FAILURES)} case(s) failed: "
              f"{', '.join(FAILURES)}", file=sys.stderr)
        return 1
    print("✓ audit-npm self-test: severity threshold, allowlist, fail-closed payload "
          "handling, lockfile discovery and advisory-id extraction all behave as specified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
