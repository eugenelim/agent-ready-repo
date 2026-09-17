"""Every registry surface names only folders a skill declares.

Three surfaces claim to say where this pack's artifacts live: ``DESIGN.md``'s
"Where artifacts live" registry, the subdirectory comment above
``[pack.layout.repo]`` in ``pack.toml``, and ``experience-status``'s three
folder-naming surfaces — its scan table, its readiness-gate row, and its report
template. A folder named by any of them that no skill writes sends an adopter
looking for a directory that never appears.

The declared set is derived from the skills, with ``experience-status`` excluded:
it is one of the surfaces under test, so counting its own mentions as
declarations would let it certify itself.

``experience-status`` is read whole rather than surface by surface. Its three
surfaces write folders three ways — a ``<output_dir>/...`` glob in the scan
table, a bare backticked folder in the gate row and in the report — and a
whole-file scan reaches all three plus any fourth surface added later.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = ROOT / "packs" / "experience-design"
SKILLS = PACK_ROOT / ".apm" / "skills"
DESIGN_MD = PACK_ROOT / "DESIGN.md"
PACK_TOML = PACK_ROOT / "pack.toml"
STATUS_SKILL = SKILLS / "experience-status" / "SKILL.md"

# The registry surface under test is itself a folder-naming surface, so it is
# not a source of declarations.
NOT_A_DECLARER = frozenset({"experience-status"})

INLINE_CODE = re.compile(r"`([^`\n]+)`")
LEADING_FOLDER = re.compile(r"^([a-z][a-z0-9-]*)/")
LAYOUT_SECTION = "[pack.layout.repo]"


def _output_dir_base() -> str:
    """The adopter-facing base path, which is not itself a subdirectory."""
    data = tomllib.loads(PACK_TOML.read_text(encoding="utf-8"))
    return str(data["pack"]["layout"]["repo"]["output_dir"])


BASE = _output_dir_base()


def _folder_mentions(text: str) -> set[str]:
    """Every folder under ``output_dir`` that inline code in *text* names.

    Two spellings count, and nothing else does. A span prefixed with the
    templated ``<output_dir>/`` or with the configured base names the folder in
    its next segment. A span carrying no such prefix counts only when it is a
    bare folder — a lowercase segment followed by a slash and nothing more —
    which keeps ``references/containment.md`` and ``./agentbundle-layout.toml``
    out. The base itself is a base, not a subdirectory, so it never counts.
    """
    found: set[str] = set()
    for span in INLINE_CODE.findall(text):
        rest, prefixed = span, False
        for prefix in (f"{BASE}/", "<output_dir>/"):
            if span.startswith(prefix):
                rest, prefixed = span[len(prefix):], True
                break
        if not prefixed and not rest.endswith("/"):
            continue
        match = LEADING_FOLDER.match(rest)
        if match:
            found.add(match.group(1))
    return found


def _declared_folders() -> set[str]:
    """Every folder some skill declares a target under."""
    declared: set[str] = set()
    for directory in sorted(SKILLS.iterdir()):
        skill = directory / "SKILL.md"
        if not skill.is_file() or directory.name in NOT_A_DECLARER:
            continue
        declared |= _folder_mentions(skill.read_text(encoding="utf-8"))
    return declared


DECLARED = _declared_folders()


def _subdirectory_comment() -> str:
    """The contiguous comment block introducing ``[pack.layout.repo]``."""
    lines = PACK_TOML.read_text(encoding="utf-8").splitlines()
    index = lines.index(LAYOUT_SECTION)
    start = index
    while start > 0 and lines[start - 1].startswith("#"):
        start -= 1
    return "\n".join(lines[start:index])


def test_the_declared_set_is_not_empty() -> None:
    """The skills declare folders, so every comparison below has a subject."""
    assert len(DECLARED) >= 2, f"declared folders: {sorted(DECLARED)}"


def test_the_design_registry_matches_the_declared_set() -> None:
    """``DESIGN.md`` is the registry the other surfaces defer to, so it is exact.

    A stale row names a folder nothing writes; a missing row leaves a written
    folder off the registry the pack points its readers at.
    """
    named = _folder_mentions(DESIGN_MD.read_text(encoding="utf-8"))
    assert named == DECLARED, (
        f"DESIGN.md names undeclared: {sorted(named - DECLARED)}; "
        f"omits declared: {sorted(DECLARED - named)}"
    )


def test_the_pack_toml_subdirectory_comment_names_only_declared_folders() -> None:
    """The comment may defer to the registry, but may not name a dead folder."""
    comment = _subdirectory_comment()
    assert comment, f"no comment block precedes {LAYOUT_SECTION} in pack.toml"
    named = _folder_mentions(comment)
    assert named <= DECLARED, f"pack.toml comment names undeclared: {sorted(named - DECLARED)}"


def test_experience_status_names_only_declared_folders() -> None:
    """All three of the reader skill's folder-naming surfaces agree with the skills.

    Equality, not containment: the scan table states it covers every folder the
    pack writes to, so a folder missing from it is a written artifact the status
    report cannot see.
    """
    text = STATUS_SKILL.read_text(encoding="utf-8")
    named = _folder_mentions(text)
    assert named == DECLARED, (
        f"experience-status names undeclared: {sorted(named - DECLARED)}; "
        f"omits declared: {sorted(DECLARED - named)}"
    )
