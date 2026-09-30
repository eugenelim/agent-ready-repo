#!/usr/bin/env python3
"""Run pip-audit over one manifest, applying the governed allowlist (ADR-0131).

Why a wrapper rather than `--ignore-vuln` flags. A flag carries its reasoning in
a Makefile comment, and nothing checks that the reasoning is still true or that
the suppression has not already outlived its cause. This reads
`tools/pip-audit-allowlist.toml`, where every acceptance carries a reason and a
retirement condition, and it FAILS when an entry has stopped matching and the
evidence shows the fix arrived. ADR-0102 records the unenforced-retirement
weakness on the sibling Semgrep control; this is the enforced version for the
SCA leg.

Exit contract (this process only; the recipe's own `command -v` guards keep
their own codes):

    0  every advisory allowlisted, every entry live, the tree actually audited
    1  at least one advisory no entry covers -- and nothing else
    2  the gate could not render a trustworthy verdict

Exit 2 beats exit 1, and both sets print. "Do not trust this result" dominates
"there is a vulnerability", and a reader who sees 1 should be looking for a CVE
and nothing else. `main()` wraps its body so an unhandled exception cannot leak
Python's default exit 1 and be read as a finding.

Why `--strict` is NOT passed. It looks like the native way to catch a skipped
dependency, and it is the wrong tool here: pip-audit 2.10.1 calls
`_fatal(f"{spec.name}: {spec.skip_reason}")` inside the audit loop
(`_cli.py:555-558`), exiting before any formatter runs, so under `--strict` the
skipped dependency never reaches stdout at all and the only record of its name
is a stderr log line. Omitting the flag is what makes the skip visible in the
JSON, where this gate can name it.

Why suppression is applied here and not by `--ignore-vuln`. Delegating it would
hide the suppressed advisories from this process, and the retirement detector
needs to see them: an entry is retired precisely when its advisory stops being
reported AND the fix is present.

Run: python3 tools/run-pip-audit-gate.py <requirements-file>
Proven by tools/test-run-pip-audit-gate.py.
"""

from __future__ import annotations

import json
import os
import re
import subprocess  # nosec B404  # list argv, no shell; argv[0] is the literal "pip-audit"
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST = REPO_ROOT / "tools" / "pip-audit-allowlist.toml"

# Matches tools/audit-requirements.py's `_PIP_AUDIT_TIMEOUT_S`: an unbounded
# resolver backtrack once hung the gate rather than failing it.
TIMEOUT_S = 300

# `_NAME` and `_canonical` below are copied from tools/audit-requirements.py
# (search for `_NAME =` and `def _canonical`) rather than imported: that module
# is hyphenated, so importing it needs importlib file-path loading, and
# executing its body reconfigures sys.stdout/sys.stderr as a side effect -- the
# hazard tools/test-all.py documents by name. Two short helpers are not worth
# that coupling. `_RELEASE` is this module's own; it has no sibling.
_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
_RELEASE = re.compile(r"^\d+(\.\d+)*$")

REQUIRED_FIELDS = ("id", "package", "fixed_in", "reason", "unblocked_when")

# Compared case-insensitively against each env key: urllib's proxy lookup
# case-folds, so a mixed-case spelling is honoured just as the canonical one is.
TRANSPORT_NAMES = frozenset({
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
    "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "SSL_CERT_FILE", "SSL_CERT_DIR",
})

# Include-style options pull requirements this gate would not see. Rather than
# silently narrowing the audited floor, refuse: a partial floor still passes the
# non-empty check and would guard fewer packages than the manifest declares.
_INCLUDE_OPTIONS = ("-r", "-c", "-e", "--requirement", "--constraint", "--editable")

# Exactly one branch may tell a maintainer to delete a written risk acceptance.
# Both tokens are asserted by name in tools/test-run-pip-audit-gate.py, so the
# distinction cannot quietly degrade into whichever synonym the prose reached
# for -- an earlier draft said "deleting" on one branch and "delete" on the
# other, which made the negative assertions pass by coincidence.
ACTION_REMOVE = "ACTION: remove this entry"
ACTION_HOLD = "ACTION: change nothing yet"


class GateError(Exception):
    """The gate could not render a trustworthy verdict. Always exit 2."""


def _canonical(name: str) -> str:
    """PEP 503 normalisation, so `PyJWT` and `pyjwt` match."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _release(version: str) -> tuple[int, ...] | None:
    """The comparable release tuple, or None when this version is not orderable.

    Deliberately narrower than PEP 440. The only question asked is "did the fix
    arrive", and the cost of a wrong answer is telling a maintainer to delete a
    written risk acceptance -- so a pre-release, a local version, an epoch or any
    non-numeric segment is refused rather than guessed at.
    """
    if not isinstance(version, str) or not _RELEASE.match(version.strip()):
        return None
    return tuple(int(part) for part in version.strip().split("."))


def _pad(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[tuple, tuple]:
    """Zero-pad the shorter release to the longer before comparing.

    Load-bearing: a bare tuple comparison makes (2, 14) and (2, 14, 0) unequal,
    which would fail a published version against the same version written with
    fewer segments.
    """
    width = max(len(left), len(right))
    return left + (0,) * (width - len(left)), right + (0,) * (width - len(right))


def versions_equal(left: str, right: str) -> bool | None:
    """True/False, or None when either side is not orderable."""
    a, b = _release(left), _release(right)
    if a is None or b is None:
        return None
    a, b = _pad(a, b)
    return a == b


def version_at_least(candidate: str, floor: str) -> bool | None:
    """True/False, or None when either side is not orderable."""
    a, b = _release(candidate), _release(floor)
    if a is None or b is None:
        return None
    a, b = _pad(a, b)
    return a >= b


def build_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """The child environment, built by rule rather than by a list of names.

    Every `PIP_*` name goes, which covers pip's option mapping (`PIP_INDEX_URL`,
    `PIP_CONSTRAINT`, `PIP_FIND_LINKS`, ...) and pip-audit's own feed and service
    knobs (`PIP_AUDIT_VULNERABILITY_SERVICE`, `PIP_AUDIT_OSV_URL`, ...).

    `PIP_CONFIG_FILE` is the one exception, and it is SET rather than removed.
    Removing it would re-enable `/etc/pip.conf` and `~/.config/pip/pip.conf`,
    whose `index-url` or `constraint` lines no environment scrub can reach;
    pointing it at os.devnull is what suppresses them. pip-audit resolves a
    ranged manifest by building a venv and running a real `pip install`
    (`_virtual_env.py`), and `_subprocess.run` calls Popen with no `env=`, so
    this environment reaches that innermost pip.

    Proxy and CA names are matched CASE-INSENSITIVELY, not in two fixed
    spellings. urllib.request.getproxies_environment lowercases every key before
    matching `*_proxy`, so `Https_Proxy` is honoured exactly as `HTTPS_PROXY` is;
    removing only the upper and lower spellings would leave it in place.

    Stated envelope -- these remain and are deliberately not scrubbed: PATH,
    PYTHONPATH, and pip's cache directory.
    """
    env = dict(os.environ if base is None else base)
    for name in [k for k in env if k.upper().startswith("PIP_")]:
        del env[name]
    for name in [k for k in env if k.upper() in TRANSPORT_NAMES]:
        del env[name]
    env["PIP_CONFIG_FILE"] = os.devnull
    return env


def direct_requirements(manifest: Path | str) -> frozenset[str]:
    """The canonical names the manifest names directly -- AC6's audited floor."""
    try:
        text = Path(manifest).read_text(encoding="utf-8")
    except OSError as exc:
        raise GateError(f"cannot read the manifest {manifest}: {exc}") from exc
    names = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(_INCLUDE_OPTIONS):
            raise GateError(
                f"{manifest} line {line!r} pulls requirements this gate cannot see; "
                f"the audited floor would silently narrow. Resolve the include or "
                f"audit that manifest on its own invocation."
            )
        if stripped.startswith("-"):
            continue
        found = _NAME.match(stripped)
        if found:
            names.add(_canonical(found.group(1)))
    if not names:
        # Named here because evaluate() never receives the path and so could not
        # say which manifest emptied. A partial or empty floor passes every
        # later check while guarding fewer packages than the manifest declares.
        raise GateError(
            f"no direct requirements could be derived from {manifest}; the "
            f"audited floor would be empty, so nothing would detect a resolve "
            f"that fell below the manifest"
        )
    return frozenset(names)


def load_allowlist(path: Path | str = ALLOWLIST) -> dict:
    try:
        with Path(path).open("rb") as handle:
            return tomllib.load(handle)
    except OSError as exc:
        raise GateError(f"cannot read the allowlist {path}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise GateError(f"allowlist {path} is not valid TOML: {exc}") from exc


def run_audit(manifest: Path | str, *, runner=subprocess.run) -> dict:
    """Spawn pip-audit and return its parsed report.

    pip-audit exits 1 on a normal run of this gate, because no `--ignore-vuln`
    is passed and advisories are found -- so 0 and 1 with parseable JSON both
    proceed. Any other code, or unparseable stdout at any code, is a GateError.
    """
    argv = ["pip-audit", "-f", "json", "-s", "pypi", "-r", str(manifest)]
    try:
        # Deliberately carries no B603 suppression comment. The call goes
        # through the injected `runner` seam rather than a literal
        # subprocess.run, so bandit raises nothing here, and run-bandit-gate.py
        # fails the gate on a suppression that matched nothing (ADR-0084).
        # argv is a literal list, no shell, and argv[0] is the constant
        # "pip-audit".
        proc = runner(
            argv,
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_S,
            env=build_env(),
        )
    except subprocess.TimeoutExpired as exc:
        raise GateError(f"pip-audit exceeded {TIMEOUT_S}s on {manifest}") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise GateError(f"could not run pip-audit: {exc}") from exc

    if proc.returncode not in (0, 1):
        raise GateError(
            f"pip-audit exited {proc.returncode} (not an advisory result): "
            f"{(proc.stderr or '').strip()[:400]}"
        )
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise GateError(
            f"pip-audit exited {proc.returncode} with unparseable stdout: {exc}"
        ) from exc
    if not isinstance(report, dict) or not isinstance(report.get("dependencies"), list):
        raise GateError("pip-audit report has an unrecognised shape")
    return report


@dataclass
class Verdict:
    exit_code: int
    lines: list[str] = field(default_factory=list)


def _validate(allowlist: dict) -> tuple[list[dict], list[str]]:
    """Return (entries, problems). A malformed allowlist yields no entries."""
    problems: list[str] = []
    allowed = allowlist.get("allowed_packages")
    if not isinstance(allowed, list) or not allowed or not all(
        isinstance(name, str) and name.strip() for name in allowed
    ):
        # A bare string would make the membership test a substring match, which
        # is the widening this field exists to prevent.
        problems.append(
            "allowlist: `allowed_packages` must be a non-empty array of strings"
        )
        allowed_set: frozenset[str] = frozenset()
    else:
        allowed_set = frozenset(_canonical(name) for name in allowed)

    raw = allowlist.get("allow", [])
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        problems.append("allowlist: `allow` must be an array of tables")
        return [], problems

    entries: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(raw):
        label = item.get("id") if isinstance(item.get("id"), str) else f"entry #{index + 1}"
        bad = [
            name
            for name in REQUIRED_FIELDS
            if not isinstance(item.get(name), str) or not item[name].strip()
        ]
        if bad:
            problems.append(
                f"allowlist entry {label} ({item.get('package', 'unknown package')}): "
                f"missing or blank {', '.join(bad)} -- every field is required, "
                f"because an allowlist that decays into an undocumented mute list "
                f"is worse than no allowlist"
            )
            continue
        key = (item["id"], _canonical(item["package"]))
        if key in seen:
            problems.append(
                f"allowlist entry {label}: duplicates an earlier entry for the same "
                f"advisory and package. Only the first can ever match, and the second "
                f"would otherwise be reported as an advisory that stopped being seen."
            )
            continue
        seen.add(key)
        if _canonical(item["package"]) not in allowed_set:
            problems.append(
                f"allowlist entry {label}: package {item['package']!r} is outside "
                f"`allowed_packages` ({sorted(allowed_set) or 'unset or malformed'}) "
                f"-- widening the vehicle must be its own visible edit"
            )
            continue
        entries.append(item)
    return entries, problems


def evaluate(report: dict, allowlist: dict, floor: frozenset[str]) -> Verdict:
    """The whole decision, as a pure function over parsed data."""
    lines: list[str] = []
    problems: list[str] = []
    blocking: list[str] = []

    entries, validation_problems = _validate(allowlist)
    problems.extend(validation_problems)

    resolved: dict[str, dict] = {}
    skipped: list[str] = []
    for dependency in report.get("dependencies", []):
        if not isinstance(dependency, dict) or "name" not in dependency:
            problems.append("report: a dependency entry has no name")
            continue
        name = _canonical(dependency["name"])
        if "skip_reason" in dependency or "vulns" not in dependency:
            reason = dependency.get("skip_reason", "no vulns key")
            skipped.append(f"{dependency['name']}: {reason}")
        else:
            resolved[name] = dependency

    for skip in skipped:
        problems.append(
            f"pip-audit skipped {skip} -- that dependency was NOT audited, and an "
            f"unaudited dependency is not a clean one"
        )

    if not floor:
        problems.append(
            "the audited floor derived from the manifest is empty -- an unreadable "
            "or reshaped manifest would otherwise let every report pass"
        )
    else:
        for missing in sorted(floor - resolved.keys()):
            problems.append(
                f"direct requirement {missing!r} is absent from the audited "
                f"dependencies -- the resolve fell below the manifest itself"
            )

    matched: set[int] = set()
    for name, dependency in sorted(resolved.items()):
        for advisory in dependency.get("vulns", []):
            if not isinstance(advisory, dict) or not isinstance(advisory.get("id"), str):
                problems.append(f"report: {dependency['name']} carries a malformed advisory")
                continue
            hit = None
            for index, item in enumerate(entries):
                if item["id"] == advisory["id"] and _canonical(item["package"]) == name:
                    hit = (index, item)
                    break
            if hit is None:
                fixes = ", ".join(advisory.get("fix_versions") or []) or "none"
                blocking.append(
                    f"  BLOCKING {dependency['name']} {dependency.get('version', '?')} "
                    f"{advisory['id']} (fix: {fixes})"
                )
                continue
            index, item = hit
            matched.add(index)
            published = advisory.get("fix_versions") or []
            decisions = [versions_equal(item["fixed_in"], each) for each in published]
            listed = ", ".join(published) or "none"
            if not published:
                problems.append(
                    f"allowlist entry {item['id']}: the advisory publishes no fix "
                    f"versions, so fixed_in {item['fixed_in']!r} cannot be checked "
                    f"against the feed. This is a feed condition, not an entry error."
                )
            elif any(decision is True for decision in decisions):
                pass
            elif any(decision is None for decision in decisions):
                # Not a mismatch -- a comparison that was never performed. Saying
                # "matches none" here would assert a property the check did not
                # compare, and the obvious remedy (copy the published string into
                # fixed_in) would park the entry permanently in AC4's
                # could-not-compare branch, disabling the very detector AC5 adds.
                problems.append(
                    f"allowlist entry {item['id']}: fixed_in {item['fixed_in']!r} could not "
                    f"be compared with the fix versions the advisory publishes ({listed}) "
                    f"-- at least one is not a dotted all-numeric release. Whether they "
                    f"agree is unknown; this is not evidence that they disagree."
                )
            else:
                problems.append(
                    f"allowlist entry {item['id']}: fixed_in {item['fixed_in']!r} matches "
                    f"none of the fix versions the advisory publishes ({listed}) -- an "
                    f"entry whose fixed_in the feed does not recognise can never retire"
                )
            lines.append(
                f"  accepted {dependency['name']} {dependency.get('version', '?')} "
                f"{advisory['id']} -- retires when: {item['unblocked_when']}"
            )

    for index, item in enumerate(entries):
        if index in matched:
            continue
        package = _canonical(item["package"])
        dependency = resolved.get(package)
        if dependency is None:
            problems.append(
                f"allowlist entry {item['id']}: {item['package']} is absent from the report "
                f"entirely, so nothing was audited for it. This is NOT evidence the fix "
                f"arrived. {ACTION_HOLD} -- check why the package left the resolve, "
                f"or why the audit returned nothing for it."
            )
            continue
        resolved_version = str(dependency.get("version", ""))
        reached = version_at_least(resolved_version, item["fixed_in"])
        if reached is None:
            problems.append(
                f"allowlist entry {item['id']}: the advisory is no longer reported, but "
                f"{item['package']} {resolved_version!r} and fixed_in {item['fixed_in']!r} "
                f"could not be compared, so whether the fix arrived is unknown. "
                f"{ACTION_HOLD}."
            )
        elif reached:
            problems.append(
                f"allowlist entry {item['id']}: RETIREMENT CONDITION FIRED -- the advisory "
                f"is no longer reported and {item['package']} resolves to {resolved_version} "
                f">= {item['fixed_in']}. {ACTION_REMOVE} from tools/pip-audit-allowlist.toml. "
                f"({item['unblocked_when']})"
            )
        else:
            problems.append(
                f"allowlist entry {item['id']}: the advisory is absent but the fix is not -- "
                f"{item['package']} resolves to {resolved_version}, below {item['fixed_in']}. "
                f"A withdrawn advisory or a degraded feed looks exactly like this. "
                f"{ACTION_HOLD} -- confirm against the feed first; if the advisory was "
                f"withdrawn, removing the entry is a maintainer decision recorded in ADR-0131."
            )

    if lines:
        lines.insert(0, f"run-pip-audit-gate: {len(lines)} accepted advisory(ies) "
                        f"from tools/pip-audit-allowlist.toml")
    if blocking:
        lines.append(f"run-pip-audit-gate: {len(blocking)} advisory(ies) no entry covers:")
        lines.extend(blocking)
    if problems:
        lines.append("run-pip-audit-gate: the gate could not render a trustworthy verdict:")
        lines.extend(f"  {problem}" for problem in problems)

    if problems:
        return Verdict(2, lines)
    if blocking:
        return Verdict(1, lines)
    if not lines:
        lines.append("run-pip-audit-gate: no known vulnerabilities, no suppressions in force")
    return Verdict(0, lines)


def _utf8_streams() -> None:
    """Windows cp1252 guard, called from main rather than at import.

    Deliberately not at module scope: this module's own provenance comment cites
    a sibling's import-time stream reconfiguration as the reason not to import
    it, and doing the same thing here would earn the same objection. The
    self-test imports this module by path and would inherit it.
    """
    for stream, errors in ((sys.stdout, "strict"), (sys.stderr, "backslashreplace")):
        # A redirected stream (StringIO under test, a pipe wrapper) has no
        # reconfigure; the guard exists so this cannot turn a caller's capture
        # into a crash that masquerades as the failure under test.
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors=errors)


def main(argv: list[str], *, _audit=None, _allowlist=None) -> int:
    _utf8_streams()
    if len(argv) != 1:
        print("usage: python3 tools/run-pip-audit-gate.py <requirements-file>", file=sys.stderr)
        return 2
    manifest = argv[0]
    try:
        allowlist = (_allowlist or load_allowlist)()
        floor = direct_requirements(manifest)
        report = (_audit or run_audit)(manifest)
        verdict = evaluate(report, allowlist, floor)
    except GateError as exc:
        print(f"run-pip-audit-gate: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - see the module docstring's exit contract
        # Never let an internal failure leak Python's default exit 1, which this
        # gate reserves for "there is a vulnerability".
        print(f"run-pip-audit-gate: internal error ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 2
    stream = sys.stdout if verdict.exit_code == 0 else sys.stderr
    for line in verdict.lines:
        print(line, file=stream)
    return verdict.exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
