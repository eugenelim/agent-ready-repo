"""Compatibility contract for the author-brief alias."""

from pathlib import Path

SKILLS = Path(__file__).resolve().parents[3] / ".apm" / "skills"
ALIAS = SKILLS / "author-brief" / "SKILL.md"
TARGET = SKILLS / "author-delivery-brief" / "SKILL.md"


def test_author_alias_delegates_once_and_writes_canonical_receipt() -> None:
    text = ALIAS.read_text(encoding="utf-8")

    assert "`author-delivery-brief create`" in text
    assert text.count("> `author-brief` is deprecated") == 1
    assert "return the canonical owner's result unchanged" in text
    assert "invoked_alias: author-brief" in text
    assert "Do not author content" in text


def test_author_alias_is_strictly_less_privileged_than_target() -> None:
    alias = ALIAS.read_text(encoding="utf-8").split("---\n", 2)[1]
    target = TARGET.read_text(encoding="utf-8").split("---\n", 2)[1]

    assert "allowed-tools: Read\n" in alias
    assert "boundaries: []" in alias
    assert "allowed-tools: Read Write Edit" in target
    assert "filesystem_write" in target
    assert "filesystem_read_untrusted" in target


def test_author_alias_pins_the_removal_gate_without_removing_it() -> None:
    text = ALIAS.read_text(encoding="utf-8")

    assert "at least two minor Core releases and 90 days" in text
    assert "whichever is later" in text
    assert "Announce removal in advance" in text
    assert "first eligible release" in text
    assert "named Approver decision" in text
    assert "last alias-bearing Core pack release" in text
