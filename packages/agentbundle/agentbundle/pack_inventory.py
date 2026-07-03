"""Live pack-inventory walk over a pack's ``.apm/`` source tree.

A pack's authoritative contents live under ``<pack>/.apm/``:

  - skills at ``.apm/skills/<name>/SKILL.md``  → ``<name>``
  - agents at ``.apm/agents/<name>.md``        → ``<name>``

This module is the single enumeration path for that tree (ADR-0049 /
RFC-0060 AC9): both ``agentbundle show`` and ``build/lint_packs`` walk it
through :func:`apm_entries`, so the directory traversal lives in one place.
The primitive returns **raw sorted entries** — each caller applies its own
filter (``show`` counts only ``SKILL.md``-bearing skill dirs and ``.md``
agent files; ``lint_packs`` lints every entry, ``SKILL.md`` or not).

Pure stdlib ``pathlib`` — no I/O beyond reading the directory tree, and
nothing is persisted (ADR-0049: derive live, persist nothing).
"""

from __future__ import annotations

from pathlib import Path


def apm_entries(pack_dir: Path, subdir: str) -> list[Path]:
    """Return the sorted direct children of ``<pack_dir>/.apm/<subdir>``.

    Returns ``[]`` when the directory is absent (AC4) — a pack that ships no
    skills, or no agents, is not an error. Sorted ascending by path so every
    consumer sees a deterministic order. This is the shared raw walk (AC9);
    callers filter the entries themselves.
    """
    d = pack_dir / ".apm" / subdir
    if not d.is_dir():
        return []
    return sorted(d.iterdir())


def skill_names(pack_dir: Path) -> list[str]:
    """Sorted names of ``.apm/skills/<name>/`` dirs that contain a ``SKILL.md``.

    A skills subdirectory without a ``SKILL.md`` is not a skill (AC2); a
    missing ``.apm/skills/`` yields ``[]`` (AC4).
    """
    return [
        entry.name
        for entry in apm_entries(pack_dir, "skills")
        if entry.is_dir() and (entry / "SKILL.md").is_file()
    ]


def agent_names(pack_dir: Path) -> list[str]:
    """Sorted stems of ``.apm/agents/*.md`` files.

    Non-``.md`` entries and subdirectories are ignored (AC2); a missing
    ``.apm/agents/`` yields ``[]`` (AC4).
    """
    return [
        entry.stem
        for entry in apm_entries(pack_dir, "agents")
        if entry.is_file() and entry.suffix == ".md"
    ]
