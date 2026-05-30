"""T4 (issue #190 minor): `_collect_unresolved_markers` ignores code-span markers.

A `<adapt:NAME>` token inside Markdown inline-code or a fenced block is
documentation *about* the marker syntax, not a live substitution point, and must
not leak into the install-marker's `unresolved-markers` list (AC9). A live
(non-code) marker is still collected.
"""

from __future__ import annotations

from agentbundle.commands.install import _collect_unresolved_markers


def test_inline_code_marker_not_collected() -> None:
    proj = {"skill.md": b"For each `<adapt:name>` marker the packs declare, do X."}
    assert _collect_unresolved_markers(proj) == []


def test_fenced_code_marker_not_collected() -> None:
    proj = {"doc.md": b"Example:\n\n```\n<adapt:project-name>\n```\n\nend."}
    assert _collect_unresolved_markers(proj) == []


def test_tilde_fenced_code_marker_not_collected() -> None:
    proj = {"doc.md": b"~~~\n<adapt:foo>\n~~~\n"}
    assert _collect_unresolved_markers(proj) == []


def test_live_marker_still_collected() -> None:
    proj = {"AGENTS.md": b"This project is <adapt:project-name>, built with care."}
    assert _collect_unresolved_markers(proj) == ["project-name"]


def test_live_marker_collected_even_when_a_doc_example_is_present() -> None:
    proj = {
        "AGENTS.md": b"Name: <adapt:project-name>\n",
        "skill.md": b"Resolve each `<adapt:name>` marker.\n",
    }
    # The live marker is collected; the inline-code example is not.
    assert _collect_unresolved_markers(proj) == ["project-name"]
