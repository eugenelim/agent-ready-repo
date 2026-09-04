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

import contextlib
import importlib.util
import io
import os
import pathlib
import shutil
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

LOW = _report(("trivial", "low", [_advisory("trivial", "low", "GHSA-4444-5555-6666", 4)]))

# What the canary probe sees when the endpoint is answering, and when a mirror
# returns 200 with an empty advisory set. The second is byte-identical in shape
# to a clean audit — including the locally-computed metadata block — which is
# the whole reason the canary exists.
CANARY_LIVE = _report(("lodash", "critical", [_advisory("lodash", "critical", "GHSA-jf85-cpcp-j695", 5)]))

CANARY_SILENT = {
    "auditReportVersion": 2,
    "vulnerabilities": {},
    "metadata": {
        "vulnerabilities": {"info": 0, "low": 0, "moderate": 0, "high": 0,
                            "critical": 0, "total": 0},
        "dependencies": {"prod": 455, "dev": 0, "optional": 119, "peer": 2,
                         "peerOptional": 0, "total": 573},
    },
}

# A high advisory plus a package that is only vulnerable *through* it — the
# string-`via` chain link. Suppressing the root advisory must suppress the chain.
CHAINED = _report(
    ("js-yaml", "high", [_advisory("js-yaml", "high", "GHSA-aaaa-bbbb-cccc", 1)]),
    ("some-consumer", "high", ["js-yaml"]),
)

ERROR_PAYLOAD = {"error": {"code": "ENETUNREACH", "summary": "request to registry failed"}}

NO_VERSION = {"vulnerabilities": {}, "metadata": {}}

# A shape npm does not emit: blocking severity with no advisories to explain it.
# Reading it as "nothing to report" would drop a real finding.
BLOCKING_WITHOUT_VIA = _report(("mystery", "high", []))


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


def _permission_fixtures_supported() -> bool:
    """Whether POSIX mode bits can make the synthetic walk paths inaccessible."""
    return os.name == "posix" and os.geteuid() != 0


def _write_allowlist(root: pathlib.Path) -> None:
    """Give audit-npm's CLI the empty allowlist it requires before discovery."""
    allowlist = root / "tools" / "npm-audit-allowlist.toml"
    allowlist.parent.mkdir()
    allowlist.write_text("", encoding="utf-8")


def _assert_walk_failure(name: str, root: pathlib.Path, diagnostic: str) -> None:
    """Assert the CLI reports a bounded discovery error instead of a traceback."""
    m = _load_subject()
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        exit_code = m.main(["--root", str(root)])
    output = stderr.getvalue()
    check(name, exit_code == 2, f"exit_code={exit_code}; stderr={output}")
    check(f"{name}_names_failure", diagnostic in output, output)
    check(f"{name}_has_no_traceback", "Traceback" not in output, output)


# Avoid a test_ prefix: these stdlib self-tests run through main(), while pytest would pass this because check() accumulates failures.
def case_discovery_iterdir_permission_failure() -> None:
    """An unreadable directory makes the audit CLI exit 2 without a traceback."""
    if not _permission_fixtures_supported():
        print(
            "  - discovery_iterdir_permission_failure skipped (root or non-POSIX)"
        )
        return
    root = pathlib.Path(tempfile.mkdtemp(prefix="audit-npm-unreadable-"))
    unreadable = root / "unreadable"
    try:
        _write_allowlist(root)
        unreadable.mkdir()
        unreadable.chmod(0o000)
        try:
            _assert_walk_failure(
                "discovery_iterdir_permission_failure_exits_2",
                root,
                "cannot read",
            )
        finally:
            unreadable.chmod(0o700)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def case_discovery_child_classification_permission_failure() -> None:
    """A listable but untraversable directory fails per-child classification."""
    if not _permission_fixtures_supported():
        print(
            "  - discovery_child_classification_permission_failure skipped "
            "(root or non-POSIX)"
        )
        return
    root = pathlib.Path(tempfile.mkdtemp(prefix="audit-npm-listable-"))
    listable = root / "listable"
    try:
        _write_allowlist(root)
        (listable / "child").mkdir(parents=True)
        listable.chmod(0o400)
        try:
            _assert_walk_failure(
                "discovery_child_classification_permission_failure_exits_2",
                root,
                "cannot classify",
            )
        finally:
            listable.chmod(0o700)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main() -> int:
    if not SUBJECT.is_file():
        print(f"✖ subject not found: {SUBJECT}", file=sys.stderr)
        return 1
    m = _load_subject()

    print("evaluate() — severity threshold (moderate and above)")
    check("clean_report_passes", m.evaluate(CLEAN, {}).blocking == [])
    check("high_finding_blocks", [f.advisory_id for f in m.evaluate(HIGH, {}).blocking]
          == ["GHSA-aaaa-bbbb-cccc"])
    check("critical_finding_blocks", [f.advisory_id for f in m.evaluate(CRITICAL, {}).blocking]
          == ["GHSA-dddd-eeee-ffff"])
    check("moderate_finding_blocks", [f.advisory_id for f in m.evaluate(MODERATE, {}).blocking]
          == ["GHSA-1111-2222-3333"])
    check("low_finding_does_not_block", m.evaluate(LOW, {}).blocking == [])
    # The npm flag and our own blocking set are two separate decisions about the
    # same threshold; if they drift, npm's exit code and our verdict disagree.
    check("threshold_flag_matches_blocking_set",
          m.AUDIT_LEVEL == "moderate"
          and sorted(m.BLOCKING_SEVERITIES) == ["critical", "high", "moderate"],
          f"AUDIT_LEVEL={m.AUDIT_LEVEL} BLOCKING={sorted(m.BLOCKING_SEVERITIES)}")

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

    print("run_audit_with_retry() — re-ask a detail-free error, never launder one")
    EMPTY = {"error": {"summary": "", "detail": ""}}
    check("retryable_for_the_measured_empty_error", m.is_detail_free_error(EMPTY))
    check("not_retryable_for_a_populated_code",
          not m.is_detail_free_error({"error": {"code": "EAI_AGAIN"}}))
    check("not_retryable_for_a_populated_summary",
          not m.is_detail_free_error({"error": {"summary": "rate limited"}}))
    check("not_retryable_for_a_clean_report", not m.is_detail_free_error(CLEAN))
    check("not_retryable_for_a_non_dict_payload", not m.is_detail_free_error(["nope"]))

    @contextlib.contextmanager
    def _quiet():
        """Swallow the retry notice so fixtures do not litter the gate's log."""
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            yield

    def _sequence(*payloads):
        """An audit stub that answers each payload in turn, counting calls."""
        calls = []

        def audit(_project_dir):
            calls.append(1)
            return payloads[min(len(calls) - 1, len(payloads) - 1)]

        return audit, calls

    audit, calls = _sequence(EMPTY, CLEAN)
    with _quiet():
        got = m.run_audit_with_retry(
            pathlib.Path(), attempts=3, audit=audit, sleep=lambda _s: None
        )
    check("retry_returns_the_clean_report_after_a_transient", got == CLEAN, repr(got))
    check("retry_stopped_asking_once_clean", len(calls) == 2, f"calls={len(calls)}")

    audit, calls = _sequence({"error": {"code": "EAI_AGAIN"}})
    with _quiet():
        m.run_audit_with_retry(pathlib.Path(), attempts=3, audit=audit, sleep=lambda _s: None)
    check("a_populated_error_is_asked_once", len(calls) == 1, f"calls={len(calls)}")

    audit, calls = _sequence(CLEAN)
    with _quiet():
        m.run_audit_with_retry(pathlib.Path(), attempts=3, audit=audit, sleep=lambda _s: None)
    check("a_clean_report_is_asked_once", len(calls) == 1, f"calls={len(calls)}")

    # The load-bearing one. Exhausting the retries must leave the gate exactly as
    # a single failed attempt did: an error payload that `evaluate` refuses. If
    # this ever passes a verdict instead of raising, the retry has turned a
    # registry outage into "no vulnerabilities found" — the AC1a failure the two
    # cases above exist to prevent.
    audit, calls = _sequence(EMPTY)
    with _quiet():
        exhausted = m.run_audit_with_retry(
            pathlib.Path(), attempts=3, audit=audit, sleep=lambda _s: None
        )
    check("retry_exhausted_asked_every_attempt", len(calls) == 3, f"calls={len(calls)}")
    check("retry_exhausted_returns_the_error_payload", exhausted == EMPTY, repr(exhausted))
    expect_error(
        "retry_exhausted_still_fails_closed", lambda: m.evaluate(exhausted, {})
    )

    # The canary probe is the site a registry limit actually reds, because it runs
    # before the lockfile audit. Pin both of its failure modes: a detail-free
    # error is re-asked, and silence — a valid report that simply omits the
    # advisory — is not, because re-asking cannot cure a mirror that answers 200
    # with no advisories.
    canary_ok = _report((m.CANARY_PACKAGE, m.CANARY_VERSION,
                         [_advisory(m.CANARY_PACKAGE, "high", "GHSA-canary", 1)]))
    audit, calls = _sequence(EMPTY, canary_ok)
    with _quiet():
        m.run_canary_probe(audit=lambda d: m.run_audit_with_retry(
            d, attempts=3, audit=audit, sleep=lambda _s: None))
    check("canary_re_asks_a_detail_free_error", len(calls) == 2, f"calls={len(calls)}")

    # Injecting the asker proves the probe uses what it is given — it says nothing
    # about which asker it reaches for when given none, and that default is the
    # thing a registry limit actually hits. Pin it by swapping the module's
    # retrying asker for a stub and calling the probe with no argument: if the
    # default reverts to the single-ask `run_audit`, the stub is never reached.
    # Both askers are stubbed, so the case records *which* the default reaches
    # and fails fast either way. Stubbing only the retrying one would let a
    # reverted call site fall through to the real `run_audit`, sending the
    # self-test to the registry for ten minutes to discover a one-word change.
    reached = []

    def _stub_retry(project_dir, **_kw):
        reached.append("retry")
        return canary_ok

    def _stub_plain(project_dir, **_kw):
        reached.append("plain")
        return canary_ok

    original_retry, original_plain = m.run_audit_with_retry, m.run_audit
    try:
        m.run_audit_with_retry, m.run_audit = _stub_retry, _stub_plain
        with _quiet():
            m.run_canary_probe()
    finally:
        m.run_audit_with_retry, m.run_audit = original_retry, original_plain
    check("canary_default_asker_is_the_retrying_one", reached == ["retry"], f"reached={reached}")

    silent = {"auditReportVersion": 2, "vulnerabilities": {}}
    audit, calls = _sequence(silent)
    expect_error("canary_silence_is_not_re_asked", lambda: m.run_canary_probe(
        audit=lambda d: m.run_audit_with_retry(
            d, attempts=3, audit=audit, sleep=lambda _s: None)))
    check("canary_silence_asked_once", len(calls) == 1, f"calls={len(calls)}")

    slept = []
    audit, _ = _sequence(EMPTY)
    with _quiet():
        m.run_audit_with_retry(
            pathlib.Path(), attempts=3, audit=audit, sleep=slept.append
        )
    check("retry_backs_off_between_attempts", slept == [5, 10], f"slept={slept}")
    expect_error("non_dict_payload_is_tool_error", lambda: m.evaluate([], {}))
    expect_error("blocking_severity_without_via_is_tool_error",
                 lambda: m.evaluate(BLOCKING_WITHOUT_VIA, {}))
    # The same shape at a non-blocking severity is ordinary and must still pass —
    # the guard above must not turn every via-less entry into a hard error.
    check("nonblocking_without_via_passes",
          m.evaluate(_report(("quiet", "low", [])), {}).blocking == [])

    print("canary_is_live() — the check no payload inspection can make")
    check("canary_live_when_endpoint_answers", m.canary_is_live(CANARY_LIVE) is True)
    check("canary_silent_when_mirror_returns_empty", m.canary_is_live(CANARY_SILENT) is False,
          "a 200-with-no-advisories mirror must NOT read as live")
    # The point of the canary, stated as an assertion: the silent-mirror payload
    # is a perfectly valid report that evaluate() passes. Only the canary
    # separates it from a genuinely clean tree.
    check("silent_mirror_payload_passes_evaluate_by_design",
          m.evaluate(CANARY_SILENT, {}).blocking == [])
    expect_error("canary_probe_rejects_error_payload", lambda: m.canary_is_live(ERROR_PAYLOAD))
    expect_error("canary_probe_rejects_versionless_payload", lambda: m.canary_is_live(NO_VERSION))
    check("canary_pin_is_declared",
          bool(m.CANARY_PACKAGE) and bool(m.CANARY_VERSION) and m.CANARY_ADVISORY.startswith("GHSA-"))

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

        # A symlinked *directory* is a loop risk and is pruned; a symlinked
        # *lockfile* is a real project's lockfile and must still be found.
        (root / "loop").symlink_to(root, target_is_directory=True)
        linked = root / "third"
        linked.mkdir()
        (linked / "package-lock.json").symlink_to(root / "docs-site" / "package-lock.json")
        found = [p.relative_to(root).as_posix() for p in m.discover_lockfiles(root)]
        check("prunes_symlinked_directories", not any(f.startswith("loop/") for f in found),
              f"found={found}")
        check("still_finds_symlinked_lockfile", "third/package-lock.json" in found,
              f"found={found}")

    print("discover_lockfiles() — permission failures")
    case_discovery_iterdir_permission_failure()
    case_discovery_child_classification_permission_failure()

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
