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

    if FAILURES:
        print(f"\naudit-requirements self-test: {len(FAILURES)} failure(s)")
        return 1
    print("\naudit-requirements self-test: passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
