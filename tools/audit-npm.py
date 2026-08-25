#!/usr/bin/env python3
"""Run `npm audit` over every committed npm lockfile — the npm SCA leg of
`make sast` (ADR-0017, extended to the npm ecosystem by ADR-0083).

ADR-0017 named the repo's gate "SAST/SCA" and built its SCA half with
`pip-audit`. That audits every Python dependency in the tree. It audits no
JavaScript at all, and the repo has two npm projects — `docs-site/` and `web/` —
whose committed lockfiles ship into built output. This closes that half.

**Why a wrapper rather than two `npm audit` lines in the Makefile.** `npm audit`
has no per-advisory ignore. Its only lever is `--audit-level`, which is
repo-wide: the escape hatch for one unfixable transitive advisory is to stop
gating an entire severity band. The sibling `pip-audit` leg in `make sast` ran
for months with four live `--ignore-vuln` suppressions, each carrying a written
diagnosis and an unblock condition, and they were removed only once that
condition was met — so suppressions are the observed steady state of this
control in this repo, not a hypothetical, and the written-expiry discipline is
what retires them. So the escape hatch is built now, as an ID-keyed allowlist
that forces a reason and an unblock condition into a reviewed diff, and it ships
empty.

**Why the verdict comes from the payload, never the exit code.** `npm audit`
exits non-zero for *both* "found advisories" and "could not reach the registry".
Reading its exit code alone would make a network outage, a proxy returning an
HTML error page, or a corporate MITM indistinguishable from a clean tree — a
gate that fails open exactly when the environment is degraded. So a verdict of
"clean" is reachable only from a parsed payload carrying `auditReportVersion`;
everything else is a tool error. `tools/test-audit-npm.py` pins that path,
because a live run against a healthy registry never reaches it.

**And why reading the payload is still not enough.** One failure survives every
payload check: a registry or mirror that answers the bulk-advisory endpoint with
HTTP 200 and an empty body. Measured against a local stub, that yields
`auditReportVersion: 2`, `vulnerabilities: {}`, no `error` key, and a full
`metadata.dependencies` block — the last because npm computes it from the
lockfile locally and never receives it from the registry. The result is
byte-identical to a genuinely clean audit. No amount of payload inspection
distinguishes them, so the gate first audits a **canary**: a pin with a
permanent published advisory. If the endpoint does not report that, it is not
reporting anything, and the run is a tool error rather than a pass.

Lockfiles are **discovered**, not listed, so a third npm project cannot be added
without the gate noticing. `node_modules/` and dot-directories are pruned:
lockfiles inside an installed tree are dependency artifacts, not projects, and
whether they exist at all depends on who last ran `npm ci`.

Usage:
    audit-npm.py [--root .]

Exit codes — three outcomes, deliberately distinguishable (same reasoning as
`tools/test-all.py`: "found advisories" and "never actually ran" are different
facts, and reporting the second as the first is how a gate sits green for weeks):

  0  every discovered lockfile audited clean, or its only findings were
     allowlisted (each printed).
  1  at least one non-allowlisted advisory at or above the blocking threshold.
  2  the gate could not run: npm absent, unreadable or unparseable audit output,
     an error payload, an unrecognised report schema, a malformed allowlist,
     no lockfile discovered at all, or a canary probe that came back silent.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404  # invokes `npm` with a list argv, no shell
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_REPO_ROOT = Path(__file__).resolve().parents[1]

LOCKFILE_NAME = "package-lock.json"
DEFAULT_ALLOWLIST = "tools/npm-audit-allowlist.toml"

# Matches the `--audit-level` passed to npm. npm's own flag decides its exit
# code; this set decides ours, and ours is the one that gates. Keeping both
# means a future npm that changes its threshold semantics cannot quietly widen
# the gate.
#
# `moderate`, not `high`: both lockfiles were clean at moderate the day this
# threshold was set, so raising the bar cost nothing. The cheapest moment to
# raise a bar is while you are already above it — deferring means tightening on
# a day when there *is* a moderate finding, which turns a one-word diff into an
# argument.
BLOCKING_SEVERITIES = frozenset({"moderate", "high", "critical"})
AUDIT_LEVEL = "moderate"

# Directories that never contain a *project* lockfile.
_PRUNED_DIR_NAMES = frozenset({"node_modules"})

# ── The canary ──────────────────────────────────────────────────────────────
# A pin with a permanent, long-published advisory, audited in a throwaway
# lockfile before the real projects are.
#
# The failure this exists to catch is measured, not imagined. An npm registry
# or mirror that answers the bulk-advisory endpoint with HTTP 200 and an empty
# body produces a report that is *byte-identical to a clean one*:
# `auditReportVersion: 2`, `vulnerabilities: {}`, no `error` key, and a full,
# plausible `metadata.dependencies` block — because that block is computed
# locally from the lockfile and never comes from the registry at all. Every
# other guard in this module reads the payload, and the payload looks perfect.
#
# So the payload cannot answer "did anything actually get checked?". Only a
# known-positive can. If the endpoint does not report this pin, it is not
# reporting anything, and a green run over the real lockfiles means nothing.
#
# Same reasoning the `sast` recipe already applies to
# `tools/test-semgrep-argv-boundary.py`: a scan that is silent when it works and
# silent when it has been broken into a no-op cannot tell you which it did.
CANARY_PACKAGE = "lodash"
CANARY_VERSION = "4.17.11"
CANARY_ADVISORY = "GHSA-jf85-cpcp-j695"  # prototype pollution; critical


class AuditError(Exception):
    """The gate could not run. Always exit 2 — never a pass, never a finding."""


@dataclass(frozen=True)
class Finding:
    advisory_id: str
    package: str
    severity: str
    title: str
    url: str


@dataclass(frozen=True)
class Verdict:
    blocking: list[Finding]
    suppressed: list[Finding]


def discover_lockfiles(root: Path) -> list[Path]:
    """Every project `package-lock.json` under *root*, sorted for stable output.

    Prunes `node_modules/` and dot-directories. Pruning happens on the walk, not
    as a post-filter, so an installed `node_modules` tree costs nothing to skip.
    """
    found: list[Path] = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError as exc:
            # Not silent: an unreadable directory is almost always a permissions
            # artifact, but a walk that quietly skipped the one directory holding
            # a lockfile would under-cover and still print green. The
            # no-lockfile-found guard in main() only catches total failure, so
            # partial failure has to announce itself.
            print(f"audit-npm: warning: cannot read {current}: {exc}", file=sys.stderr)
            continue
        for entry in entries:
            if entry.is_dir():
                # Symlinked directories are skipped for loop safety; symlinked
                # *files* are not, so a lockfile linked into place is still
                # audited rather than silently dropped.
                if (
                    entry.is_symlink()
                    or entry.name in _PRUNED_DIR_NAMES
                    or entry.name.startswith(".")
                ):
                    continue
                stack.append(entry)
            elif entry.name == LOCKFILE_NAME:
                found.append(entry)
    return sorted(found)


def load_allowlist(path: Path) -> dict[str, dict[str, str]]:
    """Parse the advisory allowlist. A malformed entry is an error, not a skip.

    Every entry must carry `id`, a non-blank `reason`, and a non-blank
    `unblocked_when`. Enforcing that here — rather than treating a bare `id` as
    "suppress it" — is what keeps the allowlist from decaying into an
    undocumented mute list, which is the failure mode that makes a suppression
    mechanism worse than none.
    """
    if not path.is_file():
        raise AuditError(f"allowlist not found: {path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise AuditError(f"allowlist {path} is unreadable: {exc}") from exc

    entries = data.get("allow", [])
    if not isinstance(entries, list):
        raise AuditError(f"allowlist {path}: `allow` must be an array of tables")

    result: dict[str, dict[str, str]] = {}
    for index, entry in enumerate(entries):
        where = f"allowlist {path} entry #{index + 1}"
        if not isinstance(entry, dict):
            raise AuditError(f"{where}: must be a table")
        advisory = entry.get("id")
        if not isinstance(advisory, str) or not advisory.strip():
            raise AuditError(f"{where}: missing a non-blank `id`")
        for field in ("reason", "unblocked_when"):
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                raise AuditError(
                    f"{where} ({advisory}): missing a non-blank `{field}` — a "
                    f"suppression without one is an undocumented mute"
                )
        result[advisory.strip()] = {
            "reason": entry["reason"].strip(),
            "unblocked_when": entry["unblocked_when"].strip(),
        }
    return result


def advisory_id(via: dict) -> str:
    """The advisory's stable public ID: GHSA-… or CVE-… from its URL.

    Falls back to `npm:<source>` so an advisory without a GitHub URL is still
    addressable by the allowlist rather than being unsuppressable.
    """
    url = via.get("url")
    if isinstance(url, str) and url:
        tail = url.rstrip("/").rsplit("/", 1)[-1]
        if tail.startswith(("GHSA-", "CVE-")):
            return tail
    source = via.get("source")
    if source is not None:
        return f"npm:{source}"
    raise AuditError(f"advisory entry has neither a usable `url` nor a `source`: {via!r}")


def _require_report(report: object) -> dict:
    """Return the payload's `vulnerabilities` map, or raise AuditError.

    The single place the AC1a fail-closed rule is enforced: anything that is not
    a recognisable `npm audit` report raises rather than reading as clean. Shared
    by `evaluate` and the canary probe so the two cannot drift apart.
    """
    if not isinstance(report, dict):
        raise AuditError(f"audit output is not a JSON object (got {type(report).__name__})")
    if "error" in report:
        detail = report["error"]
        if isinstance(detail, dict):
            detail = detail.get("summary") or detail.get("code") or detail
        raise AuditError(
            f"npm audit reported an error instead of a report: "
            f"{detail or report.get('message') or '(no detail)'}"
        )
    if "auditReportVersion" not in report:
        raise AuditError(
            "audit output carries no `auditReportVersion` — refusing to read an "
            "unrecognised payload as a clean result"
        )
    vulnerabilities = report.get("vulnerabilities", {})
    if not isinstance(vulnerabilities, dict):
        raise AuditError("audit output's `vulnerabilities` is not an object")
    return vulnerabilities


def canary_is_live(report: object) -> bool:
    """Did this audit of the canary lockfile actually report the canary advisory?

    False means the advisory endpoint answered without reporting a pin that has
    carried a published advisory for years — so it is not reporting anything,
    and a clean result over the real lockfiles proves nothing.
    """
    return CANARY_PACKAGE in _require_report(report)


def evaluate(report: object, allowlist: dict[str, dict[str, str]]) -> Verdict:
    """Classify a parsed `npm audit --json` payload.

    Raises AuditError for anything that is not a recognisable audit report —
    see the module docstring on why a degraded environment must not read as
    clean (spec AC1a).

    Only advisory dicts in `via` are considered; a bare-string `via` entry is a
    chain link naming another vulnerable package, whose own advisory appears as
    a dict elsewhere in the same report. Judging the roots therefore covers the
    chains, and suppressing a root correctly suppresses everything downstream of
    it.
    """
    vulnerabilities = _require_report(report)

    blocking: dict[str, Finding] = {}
    suppressed: dict[str, Finding] = {}
    for package, detail in vulnerabilities.items():
        if not isinstance(detail, dict):
            raise AuditError(f"audit entry for {package!r} is not an object")
        via_entries = detail.get("via", [])
        if detail.get("severity") in BLOCKING_SEVERITIES and not via_entries:
            # A blocking package with no `via` at all is a shape npm does not
            # emit. Reading it as "nothing to report" would drop a real finding,
            # so it joins the AC1a fail-closed set rather than passing quietly.
            raise AuditError(
                f"audit entry for {package!r} is {detail.get('severity')} but "
                f"carries no `via` advisories — unrecognised report shape"
            )
        for via in via_entries:
            if not isinstance(via, dict):
                continue  # chain link; its root advisory is judged on its own entry
            severity = via.get("severity")
            if severity not in BLOCKING_SEVERITIES:
                continue
            identifier = advisory_id(via)
            finding = Finding(
                advisory_id=identifier,
                package=str(via.get("name") or package),
                severity=str(severity),
                title=str(via.get("title") or ""),
                url=str(via.get("url") or ""),
            )
            target = suppressed if identifier in allowlist else blocking
            target.setdefault(identifier, finding)

    return Verdict(
        blocking=[blocking[k] for k in sorted(blocking)],
        suppressed=[suppressed[k] for k in sorted(suppressed)],
    )


def run_audit(project_dir: Path) -> object:
    """Invoke `npm audit --json` for one project and return the parsed payload.

    The only impure part of this module, and deliberately the only part the
    self-test does not exercise. Read-only by construction: `npm audit` without
    `fix` mutates nothing, and `--package-lock-only` keeps it off the network
    install path and reads the committed lockfile — the artifact under audit —
    rather than whatever `node_modules` happens to hold.
    """
    argv = [
        "npm", "audit",
        "--json",
        "--package-lock-only",
        f"--audit-level={AUDIT_LEVEL}",
    ]
    try:
        completed = subprocess.run(  # nosec B603  # list argv of constants, no shell
            argv,
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise AuditError(
            "npm not found on PATH — install Node.js (>=24, per package.json "
            "`engines`) so the npm SCA leg can run, or set SKIP_SAST=1 to skip "
            "the whole SAST/SCA gate deliberately"
        ) from exc
    except OSError as exc:
        raise AuditError(f"could not invoke npm in {project_dir}: {exc}") from exc

    # The exit code is deliberately not consulted: npm audit returns non-zero
    # for both "found advisories" and "could not run". The payload decides.
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        stderr = (completed.stderr or "").strip().splitlines()
        hint = stderr[-1] if stderr else "(no stderr)"
        raise AuditError(
            f"npm audit in {project_dir} produced no parseable JSON "
            f"(exit {completed.returncode}): {exc}. Last stderr line: {hint}"
        ) from exc


def run_canary_probe() -> None:
    """Prove the advisory endpoint answers, before trusting a clean result.

    Writes a throwaway lockfile pinning the canary and audits it. Nothing is
    installed and nothing outside the tmpdir is touched.
    """
    manifest = {
        "name": "npm-sca-gate-canary",
        "version": "1.0.0",
        "dependencies": {CANARY_PACKAGE: CANARY_VERSION},
    }
    lock = {
        "name": "npm-sca-gate-canary",
        "version": "1.0.0",
        "lockfileVersion": 3,
        "requires": True,
        "packages": {
            "": manifest,
            f"node_modules/{CANARY_PACKAGE}": {
                "version": CANARY_VERSION,
                "resolved": (
                    f"https://registry.npmjs.org/{CANARY_PACKAGE}/-/"
                    f"{CANARY_PACKAGE}-{CANARY_VERSION}.tgz"
                ),
            },
        },
    }
    with tempfile.TemporaryDirectory(prefix="npm-sca-canary-") as tmp:
        probe_dir = Path(tmp)
        (probe_dir / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
        (probe_dir / "package-lock.json").write_text(json.dumps(lock), encoding="utf-8")
        if not canary_is_live(run_audit(probe_dir)):
            raise AuditError(
                f"the advisory endpoint reported nothing for {CANARY_PACKAGE}@"
                f"{CANARY_VERSION} ({CANARY_ADVISORY}), which has carried a published "
                f"advisory for years. The endpoint is not answering with real data, so "
                f"a clean result over this repo's lockfiles would be meaningless. Check "
                f"the configured registry (`npm config get registry`) — a mirror that "
                f"returns 200 with no advisories produces a report indistinguishable "
                f"from a clean one. If the advisory itself was withdrawn, repin the "
                f"canary in tools/audit-npm.py."
            )
    print(
        f"audit-npm: advisory endpoint confirmed live "
        f"({CANARY_PACKAGE}@{CANARY_VERSION} reported as expected)."
    )


def _describe(finding: Finding) -> str:
    """`<package>: <title>`, without repeating the package when the advisory
    title already leads with it (npm's own titles usually do)."""
    if finding.title.startswith(f"{finding.package}:"):
        return finding.title
    return f"{finding.package}: {finding.title}"


def _report(project: Path, verdict: Verdict, root: Path) -> None:
    label = project.relative_to(root).as_posix()
    for finding in verdict.suppressed:
        print(f"  allowlisted: {finding.advisory_id} ({finding.severity}) {_describe(finding)}")
    if verdict.blocking:
        print(f"✖ {label}: {len(verdict.blocking)} blocking advisory(ies)", file=sys.stderr)
        for finding in verdict.blocking:
            print(
                f"    {finding.advisory_id} ({finding.severity}) {_describe(finding)}"
                f"\n      {finding.url}",
                file=sys.stderr,
            )
    else:
        suffix = f" ({len(verdict.suppressed)} allowlisted)" if verdict.suppressed else ""
        print(f"✓ {label}: no blocking advisories{suffix}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(_REPO_ROOT))
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    allowlist_path = root / DEFAULT_ALLOWLIST

    try:
        allowlist = load_allowlist(allowlist_path)
    except AuditError as exc:
        print(f"audit-npm: {exc}", file=sys.stderr)
        return 2

    lockfiles = discover_lockfiles(root)
    if not lockfiles:
        # Fail closed. Zero lockfiles means discovery broke or the tree moved —
        # both of which would otherwise present as a green gate over nothing.
        print(
            f"audit-npm: found no {LOCKFILE_NAME} under {root} — refusing to "
            f"report a clean result from broken discovery",
            file=sys.stderr,
        )
        return 2

    if allowlist:
        print(f"audit-npm: {len(allowlist)} allowlisted advisory(ies) in {allowlist_path.name}")

    # Before trusting any clean result, prove the endpoint answers at all.
    try:
        run_canary_probe()
    except AuditError as exc:
        print(f"audit-npm: {exc}", file=sys.stderr)
        return 2

    blocked = False
    for lockfile in lockfiles:
        try:
            verdict = evaluate(run_audit(lockfile.parent), allowlist)
        except AuditError as exc:
            print(f"audit-npm: {exc}", file=sys.stderr)
            return 2
        _report(lockfile.parent, verdict, root)
        blocked = blocked or bool(verdict.blocking)

    if blocked:
        print(
            "\naudit-npm: fix with `npm audit fix --package-lock-only` in the "
            "affected project, or — only for an advisory with no available fix — "
            f"add a reasoned entry to {DEFAULT_ALLOWLIST}.",
            file=sys.stderr,
        )
        return 1
    print(f"audit-npm: {len(lockfiles)} lockfile(s) audited at --audit-level={AUDIT_LEVEL}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
