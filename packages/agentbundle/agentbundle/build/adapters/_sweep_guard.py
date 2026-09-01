"""The shared refusal every adapter orphan sweep uses when state is unreadable.

An orphan sweep deletes projected skills that no pack claims.  It decides what
to keep from the installed-state file, so a sweep that cannot read that file
knows nothing about ownership — and an empty protected set does not mean "keep
nothing to be safe", it means "delete everything installed".

State 0.5 makes this reachable rather than theoretical: a reader pinned to 0.4
raises on a 0.5 file, so every sweep in an older binary would degrade to an
empty set and remove the user's direct skills.  Refusing is the only safe
reading of an unreadable state file.
"""

from __future__ import annotations

from pathlib import Path


class OrphanSweepRefused(RuntimeError):
    """A sweep could not establish which projected skills are protected."""


def refuse_unreadable_state(
    exc: Exception, output_root: Path, *, adapter: str
) -> OrphanSweepRefused:
    """Build the refusal for a sweep whose state file cannot be read.

    Returned rather than raised so each call site keeps its own `raise ... from
    exc`, which preserves the underlying `ConfigError` for the reader.
    """

    return OrphanSweepRefused(
        f"{adapter}: refusing to sweep orphaned skills because "
        f"{output_root / '.agentbundle-state.toml'} could not be read ({exc}). "
        f"Proceeding would treat every installed skill as unowned and delete "
        f"it. Re-run with a build that understands this state file, or remove "
        f"the file only if you intend to lose the record of what is installed."
    )


def installed_skill_names(
    output_root: Path, target_dir: Path, *, adapter: str
) -> set[str]:
    """Return the repo-scope skill directory names recorded beneath *target_dir*.

    One implementation for all seven sweeps. Four adapters previously carried a
    copy of this with a "keep in sync" comment, which is the arrangement that
    let three of them drift into having no protected set at all.

    An absent state file yields an empty set, which is correct: nothing is
    installed, so nothing is protected. A state file that *exists* but cannot be
    read refuses, because that is the case where an empty set silently means
    "delete everything".
    """

    from agentbundle.config import ConfigError, load_state

    try:
        state = load_state(output_root / ".agentbundle-state.toml")
    except ConfigError as exc:
        raise refuse_unreadable_state(exc, output_root, adapter=adapter) from exc

    skill_dir_rel = target_dir.relative_to(output_root)
    names: set[str] = set()
    for row in state.packs.values():
        if row.scope != "repo":
            continue
        for relpath in row.files:
            try:
                remainder = Path(relpath).relative_to(skill_dir_rel)
            except ValueError:
                continue
            if remainder.parts:
                names.add(remainder.parts[0])
    return names
