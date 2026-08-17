#!/usr/bin/env python3
"""Self-test for tools/audit-requirements.py.

The risk this guards is not "does it skip credbroker" — that is the easy half.
It is that a filter written to skip first-party pins quietly drops a
*third-party* one and the SCA gate goes green over an unaudited dependency.
Every case below asserts on what survives into the audited set, not only on what
was removed.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "audit_requirements", _HERE / "audit-requirements.py"
)
assert _SPEC and _SPEC.loader
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        FAILURES.append(f"{label}{': ' + detail if detail else ''}")
        print(f"  FAIL {label} {detail}")


def main() -> int:
    print("audit-requirements self-test")

    first_party = {"credbroker", "agentbundle"}

    # 1. A first-party pin is skipped; the third-party pins beside it are not.
    audited, skipped = _MOD.partition(
        ["httpx>=0.27", "credbroker>=0.5.0", "lxml>=5.2"], first_party
    )
    check("third-party pins survive", audited == ["httpx>=0.27", "lxml>=5.2"], str(audited))
    check("first-party pin is skipped", skipped == ["credbroker>=0.5.0"], str(skipped))

    # 2. Extras and markers on a first-party pin are still recognised, and a
    #    third-party name that merely *starts with* one is not.
    audited, skipped = _MOD.partition(
        ['credbroker[crypto]>=0.5.0; python_version >= "3.11"', "credbroker-extras>=1"],
        first_party,
    )
    check("extras/marker form is skipped", len(skipped) == 1, str(skipped))
    check(
        "a longer name that shares the prefix is audited",
        audited == ["credbroker-extras>=1"],
        str(audited),
    )

    # 3. PEP 503 normalisation. Case folds, and runs of `-_.` collapse to `-` —
    #    so `python_slugify` is `python-slugify`, while `cred_broker` is a
    #    *different* project from `credbroker` and must still be audited.
    _, skipped = _MOD.partition(["CredBroker>=1"], first_party)
    check("case folds", skipped == ["CredBroker>=1"], str(skipped))
    _, skipped = _MOD.partition(["python_slugify>=8"], {"python-slugify"})
    check("separators collapse", skipped == ["python_slugify>=8"], str(skipped))
    audited, _ = _MOD.partition(["cred_broker>=1"], first_party)
    check(
        "a separator-bearing lookalike is not treated as first-party",
        audited == ["cred_broker>=1"],
        str(audited),
    )

    # 4. Comments and pip options travel with the audited half, unaltered.
    audited, _ = _MOD.partition(["# a note", "", "-r other.txt", "httpx>=0.27"], first_party)
    check(
        "comments and options are preserved",
        audited == ["# a note", "", "-r other.txt", "httpx>=0.27"],
        str(audited),
    )

    # 5. Discovery really reads this repository's own package names.
    discovered = _MOD.first_party_names(_HERE.parent)
    check("credbroker is discovered", "credbroker" in discovered, str(discovered))
    check("agentbundle is discovered", "agentbundle" in discovered, str(discovered))

    # 6. Broken discovery fails closed rather than auditing everything as-is.
    with tempfile.TemporaryDirectory() as empty:
        check(
            "no packages/ discovers nothing",
            _MOD.first_party_names(Path(empty)) == set(),
        )
    # 7. A file of only first-party pins audits nothing and still exits 0.
    with tempfile.TemporaryDirectory() as tmp:
        only = Path(tmp) / "requirements.txt"
        only.write_text("credbroker>=0.1.0\n", encoding="utf-8")
        check("first-party-only file exits 0", _MOD.audit(only, first_party) == 0)

    # 8. Build backends are extracted from the PEP 517 contract rather than
    #    being copied into a second, drift-prone requirements file.
    with tempfile.TemporaryDirectory() as tmp:
        pyproject = Path(tmp) / "pyproject.toml"
        pyproject.write_text(
            '[build-system]\nrequires = ["setuptools>=77", "wheel>=0.45"]\n',
            encoding="utf-8",
        )
        check(
            "build-system requirements are extracted",
            _MOD.build_system_requirements([pyproject])
            == ["setuptools>=77", "wheel>=0.45"],
        )
        pyproject.write_text("[project]\nname = \"missing\"\n", encoding="utf-8")
        try:
            _MOD.build_system_requirements([pyproject])
        except ValueError:
            missing_refused = True
        else:
            missing_refused = False
        check("missing build-system requirements fail closed", missing_refused)

    batching_stubs(first_party)

    if FAILURES:
        print(f"\naudit-requirements self-test: {len(FAILURES)} failure(s)")
        return 1
    print("\naudit-requirements self-test: passed.")
    return 0


def _missing(*names: str) -> str | None:
    """Return a message naming the first absent attribute, else None.

    Keeps a red stub legible: an unimplemented contract surface reports as a
    named failure through `check()` rather than aborting the whole self-test
    with an AttributeError, so every stub's red state is visible in one run.
    """
    absent = [name for name in names if not hasattr(_MOD, name)]
    return f"not implemented yet: {', '.join(absent)}" if absent else None


def batching_stubs(first_party: set[str]) -> None:
    """Red stubs for docs/specs/pip-audit-batching.

    Materialised at PLAN per docs/CONVENTIONS.md § "Stub → EXECUTE handoff".
    These are red until T1-T4 land; EXECUTE's red step starts from here rather
    than re-deriving the assertions. Each carries the AC it verifies.
    """
    print("\npip-audit-batching (red stubs — docs/specs/pip-audit-batching)")

    # STUB: AC1 — lower-bound-only files merge; anything that could narrow the
    # resolution is audited alone.
    gap = _missing("is_merge_safe")
    if gap:
        check("AC1 merge-safety predicate", False, gap)
    else:
        check(
            "AC1 lower-bound-only file is merge-safe",
            _MOD.is_merge_safe(["httpx>=0.27", "pyyaml>=6.0", "# a note", ""]) is True,
        )
        check(
            "AC1 an inline comment does not hide an == pin",
            _MOD.is_merge_safe(["tomlkit==0.15.1  # workspace-status repair-apply"])
            is False,
        )
        for pin in ("foo<2", "foo<=2", "foo~=1.4", "foo!=1.5", "foo==1.0"):
            check(
                f"AC1 {pin} forces a solo invocation",
                _MOD.is_merge_safe([pin]) is False,
            )
        check(
            "AC1 an environment marker does not hide the specifier",
            _MOD.is_merge_safe(['foo<2; python_version >= "3.11"']) is False,
        )
        for option in ("--extra-index-url https://example.invalid/simple",
                       "-c constraints.txt",
                       "--hash=sha256:0000"):
            check(
                f"AC1 pip option {option.split()[0]} forces a solo invocation",
                _MOD.is_merge_safe(["httpx>=0.27", option]) is False,
            )
        check(
            "AC1 an unpinned third-party name is merge-safe",
            _MOD.is_merge_safe(["httpx"]) is True,
        )

    # STUB: AC8 — every non-empty file lands in exactly one group.
    gap = _missing("group_files", "has_third_party")
    if gap:
        check("AC8 coverage conservation", False, gap)
    else:
        entries = [
            ("a.txt", ["httpx>=0.27"]),
            ("b.txt", ["pyyaml>=6.0"]),
            ("c.txt", ["tomlkit==0.15.1"]),
            ("d.txt", ["lxml>=5.2", "-c constraints.txt"]),
            ("a.txt", ["httpx>=0.27"]),  # duplicated path must stay two members
        ]
        groups = _MOD.group_files(entries)
        flat = [index for group in groups for index in group]
        check(
            "AC8 every entry appears exactly once",
            sorted(flat) == list(range(len(entries))),
            str(groups),
        )
        check("AC8 no empty group", all(groups), str(groups))
        check(
            "AC8 the merge-safe entries share one group",
            any(sorted(g) == [0, 1, 4] for g in groups),
            str(groups),
        )
        check(
            "AC8 each unsafe entry is alone",
            [len(g) for g in groups].count(1) == 2,
            str(groups),
        )
        check(
            "AC8 membership uses the reporting predicate",
            _MOD.has_third_party(["# only a comment", ""]) is False
            and _MOD.has_third_party(["httpx>=0.27"]) is True,
        )

    # STUB: AC7, AC9, AC10 — a batch failure is final; the diagnostic re-run
    # can add a failure but never clear one.
    gap = _missing("run_groups")
    if gap:
        check("AC7/AC9/AC10 exit-code precedence", False, gap)
        return
    calls: list[list[str]] = []

    def runner_factory(codes: list[int]):
        def runner(argv, **kwargs):  # noqa: ARG001 - signature mirrors subprocess.run
            calls.append(list(argv))
            index = min(len(calls) - 1, len(codes) - 1)

            class _Result:
                returncode = codes[index]

            return _Result()

        return runner

    entries = [("a.txt", ["httpx>=0.27"]), ("b.txt", ["pyyaml>=6.0"])]

    calls.clear()
    check(
        "AC7 a clean batch aggregates to 0",
        _MOD.run_groups(entries, [[0, 1]], first_party, runner=runner_factory([0])) == 0,
    )

    calls.clear()
    check(
        "AC9 a failed batch is not cleared by clean per-file re-runs",
        _MOD.run_groups(
            entries, [[0, 1]], first_party, runner=runner_factory([1, 0, 0])
        )
        != 0,
    )
    check(
        "AC9 the diagnostic re-run is one level deep, one call per member",
        len(calls) == 3,
        f"{len(calls)} runner calls",
    )

    calls.clear()
    _MOD.run_groups(entries, [[0], [1]], first_party, runner=runner_factory([1, 0]))
    check(
        "AC9 a single-member group does not re-run",
        len(calls) == 2,
        f"{len(calls)} runner calls",
    )

    # STUB: AC11 — every audit of the nine-file set is strict.
    calls.clear()
    _MOD.run_groups(entries, [[0, 1]], first_party, runner=runner_factory([0]))
    check("AC11 the batched argv is strict", any("-S" in argv for argv in calls),
          str(calls))

    # STUB: AC12 — no suppression ever reaches a batched invocation.
    check(
        "AC12 no --ignore-vuln in any batched argv",
        all("--ignore-vuln" not in argv for argv in calls),
        str(calls),
    )
    check(
        "AC12 one -r per group member",
        calls and calls[0].count("-r") == 2,
        str(calls),
    )

    # STUB: AC12 — the Makefile leak path an argv assertion cannot see.
    makefile = (_HERE.parent / "Makefile").read_text(encoding="utf-8")
    stray = [
        line.strip()
        for line in makefile.splitlines()
        if "--ignore-vuln" in line and "requirements-sast" not in line
    ]
    # The four suppressions sit on a continued recipe whose --ignore-vuln lines
    # do not themselves name the file, so walk back to the invocation they
    # belong to rather than matching line-locally.
    check(
        "AC12 every --ignore-vuln belongs to the requirements-sast invocation",
        _MOD.ignore_vuln_is_contained(makefile) is True
        if hasattr(_MOD, "ignore_vuln_is_contained")
        else False,
        f"not implemented yet: ignore_vuln_is_contained (stray lines: {stray})",
    )


if __name__ == "__main__":
    raise SystemExit(main())
