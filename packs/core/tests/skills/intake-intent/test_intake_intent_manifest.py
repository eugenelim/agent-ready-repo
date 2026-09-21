"""The admission owner's declared capabilities did not widen.

`test_intake_intent.py` exercises the renderer and never opens `SKILL.md`, so
it cannot see a capability change. This file carries that half: the claim is
about the manifest, so it reads the manifest.
"""

import pathlib
import re
import sys

sys.dont_write_bytecode = True

_SKILL = (
    pathlib.Path(__file__).resolve().parents[3]
    / ".apm/skills/intake-intent/SKILL.md"
)
_TEXT = _SKILL.read_text(encoding="utf-8")
_FRONTMATTER = _TEXT.split("---", 2)[1]


def test_the_frontmatter_declares_exactly_the_four_admitted_tools() -> None:
    """AC-0008: no shell, no network, and nothing new — in particular no move."""
    declared = re.search(r"^allowed-tools:\s*(.+)$", _FRONTMATTER, re.M)
    assert declared is not None, "intake-intent must declare allowed-tools"
    assert declared.group(1).split() == ["Read", "Write", "Edit", "Agent"]


def test_the_boundaries_block_still_refuses_shell_and_network() -> None:
    """AC-0008: the prose control that keeps admission off a shell."""
    # Whitespace-normalized: a reflow of the prose must not red this gate,
    # because the claim is about what the sentence says, not how it wraps.
    boundaries = " ".join(_TEXT.split("## Boundaries", 1)[1].split())
    assert (
        "No network, shell, tracker, credential, or external-locator"
        " filesystem access is permitted." in boundaries
    )
    for forbidden in ("Bash", "shutil.move", "os.rename"):
        assert forbidden not in boundaries, forbidden


def test_the_ordinal_marker_vocabulary_is_closed_and_stated() -> None:
    """AC-0024: the skill names the tokens, so nothing is composed from input."""
    procedure = _TEXT.split("## Procedure", 1)[1].split("## Shaping-review gate", 1)[0]
    for token in (
        "unparsed-name",
        "incomplete-scan",
        "remote-unavailable",
        "bound-exceeded",
        "no-allocating-path",
        "supplied-prefix-disregarded",
    ):
        assert f"`{token}`" in procedure, token
    assert "do not reproduce its text" in procedure


def test_the_identity_rule_still_forbids_a_rename() -> None:
    """AC-0001: nothing in this slice renames an artifact already on disk."""
    normalized = " ".join(_TEXT.split())
    assert "do not create a renamed copy" in normalized
    assert "do not rename one to add or change a typed ordinal prefix" in normalized
