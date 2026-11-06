"""Pins for the seeded governance starter, issue template and rfc.py copies."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parents[3]
SEEDS = PACK / "seeds"
SCRIPTS = PACK / ".apm/skills/new-rfc/scripts"
STARTER = SEEDS / "docs/GOVERNANCE.md"
ISSUE = SEEDS / ".github/ISSUE_TEMPLATE/proposal-idea.md"
TEMPLATE = SEEDS / "docs/rfc/template.md.tmpl"
CATALOGUE_HELPER = (
    PACK.parents[1] / "packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py"
)
SEEDED = [
    STARTER,
    ISSUE,
    TEMPLATE,
    SEEDS / "docs/rfc/README.md",
    SEEDS / "docs/rfc/rfc.py",
    SEEDS / "docs/rfc/file_safety.py",
]


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_seeded_files_exist() -> None:
    """AC-0050 (delivery side): every named seed is present."""
    assert all(path.is_file() for path in SEEDED)


def test_scripts_are_byte_identical_copies() -> None:
    """AC-0052, AC-0053."""
    for name in ("rfc.py", "file_safety.py"):
        assert (SEEDS / "docs/rfc" / name).read_bytes() == (SCRIPTS / name).read_bytes()
    seeded = (SEEDS / "docs/rfc/file_safety.py").read_bytes()
    assert seeded == CATALOGUE_HELPER.read_bytes()


def test_maintainer_owned_files_and_close_review() -> None:
    """AC-0035."""
    text = _flat(STARTER)
    for name in ("rfc.py", "file_safety.py", "template.md.tmpl", "this file"):
        assert name in text
    assert "maintainer-owned" in text and "close review" in text


def test_trusted_copy_and_ci_guidance() -> None:
    """AC-0036, AC-0037."""
    text = _flat(STARTER)
    assert (
        "run your own copy of `rfc.py` from the default branch, never the one in their branch"
        in text
    )
    assert "`pull_request` trigger with read-only permissions and no secrets" in text
    assert "never on `pull_request_target`" in text
    assert (
        "The CI job must run the default-branch copy of `rfc.py` and read the pull request "
        "only through `--dir`; a copy taken from the pull request is the contributor's code."
    ) in text


def test_decider_is_a_suggestion() -> None:
    """AC-0038."""
    assert "A decider named inside an RFC is only a suggestion" in _flat(STARTER)
    template = _flat(TEMPLATE).lower()
    assert "suggestion" in template and "merge" in template


def test_maintainers_list_and_no_silence_rule() -> None:
    """AC-0039 and the removed prototype sections."""
    raw = STARTER.read_text(encoding="utf-8")
    section = raw.split("## Maintainers", 1)[1].split("\n## ", 1)[0]
    assert re.findall(r"^- (.+)$", section, flags=re.M) == ["<maintainer-handle>"]
    lowered = raw.lower()
    for banned in (
        "codeowners",
        "seven",
        "7 day",
        "silence",
        "timeout",
        "escalation",
        "through an rfc",
        "decision model",
    ):
        assert banned not in lowered, banned


def test_issue_template() -> None:
    """AC-0040."""
    text = ISSUE.read_text(encoding="utf-8")
    front = text.split("---", 2)[1]
    assert "assignees" not in front
    assert "A reply here is not an acceptance." in front
    lowered = text.lower()
    for banned in ("email", "phone", "address", "real name"):
        assert banned not in lowered


def test_starter_headings_ladder_and_rfc_rule() -> None:
    """AC-0041, AC-0042, AC-0043, AC-0044."""
    raw = STARTER.read_text(encoding="utf-8")
    headings = re.findall(r"^## (.+)$", raw, flags=re.M)
    assert headings[:5] == [
        "Maintainers",
        "How decisions are made",
        "Suggesting a change",
        "When to write an RFC",
        "How an RFC is decided",
    ] or all(
        h in headings
        for h in (
            "Maintainers",
            "How decisions are made",
            "Suggesting a change",
            "When to write an RFC",
            "How an RFC is decided",
        )
    )
    ladder = _flat(STARTER).split("Suggesting a change", 1)[1].split("When to write an RFC", 1)[0]
    positions = [
        ladder.find(k) for k in ("issue or start a discussion", "pull request", "ADR", "RFC")
    ]
    assert positions == sorted(positions) and -1 not in positions
    assert "This step is optional." in ladder
    text = _flat(STARTER)
    assert "One RFC proposes one change." in text
    assert "python3 -I docs/rfc/rfc.py new" in text
    assert "Rules meant to bind AI agents belong in your project instructions" in text
    assert "unresolved" in text and "more than one owner must agree" in text
    for category in (
        "mission, scope or foundational principles",
        "maintainer authority, approval or the governance model",
        "a security trust model",
        "withdrawal or breaking change of a stable, published compatibility promise",
    ):
        assert category in text


def test_no_internal_identifiers_in_shipped_text() -> None:
    """AC-0045: no RFC- or ADR- followed by digits."""
    pattern = re.compile(r"\b(?:RFC|ADR)-\d+")
    for path in [*SEEDED, SCRIPTS / "rfc.py", PACK / ".apm/skills/new-rfc/assets/rfc.md"]:
        assert not pattern.search(path.read_text(encoding="utf-8")), path


def test_rfc_py_command_lines_use_isolated_mode() -> None:
    """AC-0046 over the seeded files, the script's help and the template header."""
    pattern = re.compile(r"(?<!-I )(?:python3?\s+(?!-I)\S*rfc\.py)")
    for path in SEEDED:
        assert not pattern.search(path.read_text(encoding="utf-8")), path
    for line in (
        STARTER.read_text(encoding="utf-8").splitlines()
        + TEMPLATE.read_text(encoding="utf-8").splitlines()
    ):
        if "rfc.py" in line and "python" in line:
            assert "python3 -I" in line, line
    help_text = subprocess.run(
        [sys.executable, "-I", str(SEEDS / "docs/rfc/rfc.py"), "--help"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    for line in help_text.splitlines():
        if "rfc.py" in line and "python" in line:
            assert "python3 -I" in line, line
