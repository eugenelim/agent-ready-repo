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
import re
import sys
import tempfile
from pathlib import Path
from unittest import mock

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

# Pinned so a shrinking SCA input set is a named failure rather than a quieter
# gate. Raise these in the same commit that adds a manifest.
_EXPECTED_PACK_MANIFESTS = 8
_EXPECTED_TOOLS_MANIFESTS = [
    "requirements-ci-security-locked.txt",
    "requirements-evals-locked.txt",
    "requirements-sast.txt",
    "requirements.txt",
]


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        FAILURES.append(f"{label}{': ' + detail if detail else ''}")
        print(f"  FAIL {label} {detail}")


_MAKE_TARGET = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\- ]*?\s*::?(?!=)")


def sast_unleased_recipe_lines(makefile: str) -> list[str]:
    """Return target recipe lines, retaining Make conditionals but not define bodies."""
    lines = makefile.splitlines()
    try:
        start = lines.index("sast-unleased:")
    except ValueError:
        return []
    recipe: list[str] = []
    for line in lines[start + 1:]:
        if line.startswith(("\t", " ")):
            recipe.append(line)
        elif line.startswith("define ") or _MAKE_TARGET.match(line.split("#", 1)[0]):
            break
    return recipe


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

    # 9. Optional dependencies are extracted from the package contract so the
    #    SCA input cannot drift from the declared lint authoring prerequisite.
    with tempfile.TemporaryDirectory() as tmp:
        pyproject = Path(tmp) / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "demo"\n\n'
            '[project.optional-dependencies]\n'
            'lint = ["pyyaml>=6.0"]\n',
            encoding="utf-8",
        )
        check(
            "optional dependency group is extracted",
            _MOD.optional_dependency_requirements([pyproject], "lint")
            == ["pyyaml>=6.0"],
        )
        try:
            _MOD.optional_dependency_requirements([pyproject], "missing")
        except ValueError:
            missing_extra_refused = True
        else:
            missing_extra_refused = False
        check("missing optional dependency group fails closed", missing_extra_refused)

    # 10. Dependency-bearing option lines count as content, so a manifest whose
    #     only content is an include is audited rather than reported empty.
    for line in ("-r nested.txt", "--requirement=nested.txt", "-c constraints.txt",
                 "-e .", "--editable .", "-f ./wheels", "--find-links ./wheels"):
        check(
            f"dependency-bearing option is content: {line!r}",
            _MOD._is_dependency_bearing(line),
        )
    for line in ("--index-url https://example.invalid/simple",
                 "--extra-index-url https://example.invalid/simple",
                 "--no-binary :all:"):
        check(
            f"resolution-only option is not content: {line!r}",
            not _MOD._is_dependency_bearing(line),
        )
    # Asserted on the CONTENT PREDICATE rather than by calling audit(), which
    # would spawn pip-audit against a nonexistent include — network I/O and a
    # usage error inside a self-test. The predicate is the thing under test; the
    # old bug was that `-r nested.txt` did not count as content.
    include_only = ["# only an include", "", "-r nested.txt"]
    audited_only, _ = _MOD.partition(include_only, first_party)
    has_content = any(
        stripped
        and not stripped.startswith("#")
        and (not stripped.startswith("-") or _MOD._is_dependency_bearing(stripped))
        for stripped in (line.strip() for line in audited_only)
    )
    check(
        "an include-only manifest counts as having content to audit",
        has_content,
        str(audited_only),
    )

    # 11. The environment scrub really removes the variables that can re-aim the
    #     advisory feed or the index, and leaves everything else alone.
    import os as _os
    _os.environ["PIP_AUDIT_VULNERABILITY_SERVICE"] = "osv"
    _os.environ["PIP_INDEX_URL"] = "https://example.invalid/simple"
    _os.environ["AUDIT_SELFTEST_KEEP_ME"] = "kept"
    try:
        scrubbed = _MOD._scrubbed_env()
        check("PIP_AUDIT_* is scrubbed",
              "PIP_AUDIT_VULNERABILITY_SERVICE" not in scrubbed)
        check("PIP_INDEX_URL is scrubbed", "PIP_INDEX_URL" not in scrubbed)
        check("unrelated variables survive",
              scrubbed.get("AUDIT_SELFTEST_KEEP_ME") == "kept")
    finally:
        for key in ("PIP_AUDIT_VULNERABILITY_SERVICE", "PIP_INDEX_URL",
                    "AUDIT_SELFTEST_KEEP_ME"):
            _os.environ.pop(key, None)

    # 12. THE PACKS AUDITED SET HAS A FLOOR.
    #     A renamed, moved or deleted pack manifest must not silently shrink the
    #     SCA input at exit 0. Pin the shape AND the count.
    repo_root = _HERE.parent
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
    makefile_lines = sast_unleased_recipe_lines(makefile)
    check(
        "the packs audit invocation is present",
        any(
            line.lstrip("\t ").startswith(
                "python3 tools/audit-requirements.py "
                "$$(find packs -name requirements.txt | sort)"
            )
            for line in makefile_lines
        ),
    )
    check(
        "the tools-manifests audit invocation is present",
        any(
            line.lstrip("\t ").startswith(
                "python3 tools/audit-requirements.py --tools-manifests"
            )
            for line in makefile_lines
        ),
    )
    check(
        "the direct SAST audit matches the resolver exclusion",
        any(
            line.lstrip("\t ").startswith(
                f"@pip-audit -r tools/{_MOD._DIRECT_SAST_MANIFEST}"
            )
            for line in makefile_lines
        ),
    )
    pack_manifests = sorted(
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "packs").rglob("requirements.txt")
    )
    check(
        f"packs manifest count is {_EXPECTED_PACK_MANIFESTS}",
        len(pack_manifests) == _EXPECTED_PACK_MANIFESTS,
        f"found {len(pack_manifests)}: {pack_manifests}. If a manifest was added, "
        f"raise _EXPECTED_PACK_MANIFESTS in the same commit; if one vanished, the "
        f"SCA input just shrank and that is the failure this case exists for.",
    )
    # 13. THE TOOLS AUDITED SET IS CONSTRUCTED BY THE AUDITOR.
    #     A new matching manifest joins the audit without a Makefile edit. The
    #     direct SAST manifest remains excluded because its accepted-CVE
    #     suppressions belong to its dedicated pip-audit invocation.
    tools_manifests = sorted(
        path.name for path in (repo_root / "tools").glob("requirements*.txt")
    )
    check(
        "the tools/ manifest roster is unchanged",
        tools_manifests == _EXPECTED_TOOLS_MANIFESTS,
        f"found {tools_manifests}, expected {_EXPECTED_TOOLS_MANIFESTS}. A new "
        f"tools/requirements*.txt is selected automatically by the auditor.",
    )
    with tempfile.TemporaryDirectory() as tmp:
        tools_dir = Path(tmp)
        for name in (
            "requirements.txt",
            "requirements-ci-security-locked.txt",
            "requirements-evals-locked.txt",
            "requirements-extra.txt",
            "requirements-linked.txt",
            "requirements-sast.txt",
            "not-a-requirements.txt",
        ):
            (tools_dir / name).write_text("example>=1\n", encoding="utf-8")
        resolved = [
            path.name for path in _MOD.tools_requirements_manifests(tools_dir)
        ]
        with mock.patch.object(
            Path,
            "is_symlink",
            lambda path: path.name == "requirements-linked.txt",
        ):
            resolved_without_symlink = [
                path.name for path in _MOD.tools_requirements_manifests(tools_dir)
            ]
    check(
        "tools resolver includes every matching manifest except direct SAST",
        resolved == [
            "requirements-ci-security-locked.txt",
            "requirements-evals-locked.txt",
            "requirements-extra.txt",
            "requirements-linked.txt",
            "requirements.txt",
        ],
        str(resolved),
    )
    check(
        "tools resolver ignores symlink candidates",
        "requirements-linked.txt" not in resolved_without_symlink,
        str(resolved_without_symlink),
    )

    if FAILURES:
        print(f"\naudit-requirements self-test: {len(FAILURES)} failure(s)")
        return 1
    print("\naudit-requirements self-test: passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
