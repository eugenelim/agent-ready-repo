"""T8 output write path — atomic, collision-detecting, --overwrite-aware.

The only place the skill writes to disk. T7's :func:`render.render_markdown`
and :func:`render.render_json` produce the wire strings; this module takes
``(path, contents)`` pairs and lands them on disk atomically.

Two contracts pin the design:

1. **Pre-flight collision check.** Every target path is checked for
   existence up front. If any target exists and ``overwrite=False``, the
   function raises :class:`ValidationError` listing **all** colliding
   paths (not just the first), and **no write is performed**. This
   guarantees that ``--format=both`` never half-writes when one of the
   two targets pre-exists — the user always sees either both old files
   intact or both new files in place.

2. **Atomic write per target via** ``tempfile.NamedTemporaryFile`` +
   ``os.replace``. The temp file is created in the same parent directory
   as its target so ``os.replace`` is atomic on POSIX (cross-filesystem
   rename is not atomic). On failure the temp file is unlinked; the
   target file is never opened directly. Mirror of
   :mod:`flow_metrics.output`'s pattern.

Partial-write window: between the first ``os.replace`` and the second,
a crash leaves the first target replaced and the second not. The
pre-flight catches the common case (collision); a mid-write I/O error
during the second file is rare enough that we do not attempt to roll
the first one back. Documented for future readers.

Sidecar path derivation: ``<x>.md`` → ``<x>.json``; ``<x>`` (no
extension) → ``<x>.json``; ``<x>.<other>`` → ``<x>.<other>.json``
(preserves unusual extensions); ``<x>.json`` is rejected with exit 2 so
the Markdown and sidecar cannot collide on the same filename.

Env var: :data:`GENERATED_AT_ENV_VAR` (``AI_ADOPTION_REPORT_GENERATED_AT``)
is read by the CLI dispatch in :mod:`ai_adoption_report` to pin
``generated_at`` for deterministic-build tests. T7 stays pure; T8 owns
the clock.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import List, Sequence, Tuple

from . import ValidationError


# Pinned for the CLI dispatch + T9's SKILL.md to reference.
GENERATED_AT_ENV_VAR = "AI_ADOPTION_REPORT_GENERATED_AT"


def derive_sidecar_path(markdown_path: Path) -> Path:
    """Return the JSON sidecar path for a Markdown output path.

    Rules:

    - ``<name>.md`` → ``<name>.json``
    - ``<name>`` (no extension) → ``<name>.json``
    - ``<name>.json`` → :class:`ValidationError` (would collide with the
      Markdown file)
    - ``<name>.<other>`` → ``<name>.<other>.json`` (preserves unusual
      extensions so a deliberate ``report.txt`` doesn't lose its suffix)
    """
    suffix = markdown_path.suffix.lower()
    if suffix == ".json":
        raise ValidationError(
            "--output is treated as the Markdown-shaped path; the JSON "
            "sidecar is derived from it by replacing .md with .json. A "
            "path ending in .json would collide with itself (got {}). "
            "Rename --output to use .md (or no extension) — under "
            "--format=json the Markdown file is not written, but the "
            "sidecar still derives from the Markdown-shaped path.".format(
                markdown_path
            )
        )
    if suffix == ".md":
        return markdown_path.with_suffix(".json")
    # No extension OR unusual extension: append ``.json``.
    # ``with_name`` is the safe way to append — ``with_suffix`` would
    # replace ``.txt`` instead of preserving it.
    return markdown_path.with_name(markdown_path.name + ".json")


def write_outputs(
    targets: Sequence[Tuple[Path, str]],
    *,
    overwrite: bool,
) -> None:
    """Atomic-write each ``(path, contents)`` pair after a collision check.

    Pre-flight: every existing target raises :class:`ValidationError`
    (exit 2) when ``overwrite=False``. The error message lists every
    colliding path so the user fixes them in one shot rather than running
    the command repeatedly.

    Atomic write: per target, write to a sibling temp file in
    ``target.parent``, ``flush``, ``fsync``, ``os.replace``. On any
    exception the temp file is unlinked and the exception propagates.

    Empty ``targets`` is a no-op.
    """
    if not targets:
        return

    if not overwrite:
        colliding: List[str] = [str(p) for p, _ in targets if p.exists()]
        if colliding:
            raise ValidationError(
                "output file(s) already exist (use --overwrite): {}".format(
                    ", ".join(colliding)
                )
            )

    for path, contents in targets:
        _atomic_write(path, contents)


def _atomic_write(target: Path, contents: str) -> None:
    """Write ``contents`` to ``target`` atomically.

    The temp file lives in ``target.parent`` so ``os.replace`` stays
    within one filesystem (POSIX-atomic rename). ``delete=False`` keeps
    the file around after ``close()`` so ``os.replace`` can move it; on
    any error we unlink it manually.

    File mode: :func:`tempfile.NamedTemporaryFile` creates the temp
    file with mode 0600 (security default), and ``os.replace`` carries
    that mode through to the final target. That's wrong for a report
    meant to be read by other users / committed to a repo — every
    other tool the user runs (vim, cp, touch) produces ``0o666 & ~umask``
    files. We re-chmod the tempfile to the umask-derived mode **before**
    the replace so atomicity is preserved (the rename is the visible
    transition; the file's mode is already correct at that point).
    """
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(target.parent),
        delete=False,
        prefix=".{}.".format(target.name),
        suffix=".tmp",
    )
    try:
        tmp.write(contents)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()
        os.chmod(tmp.name, _umask_mode())
        os.replace(tmp.name, target)
    except Exception:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        raise


def _umask_mode() -> int:
    """Return ``0o666 & ~umask`` — the mode a freshly-touched file would
    receive in the current process.

    Reading ``umask`` requires *setting* it (the stdlib has no read-only
    getter), so we briefly set it to ``0`` and immediately restore. The
    skill is single-threaded so the window where another thread could
    observe ``umask=0`` does not exist. (Documented for future readers
    who add concurrency: this helper is not thread-safe; lock around it
    or cache the value at import time.)
    """
    current = os.umask(0)
    os.umask(current)
    return 0o666 & ~current


__all__ = [
    "GENERATED_AT_ENV_VAR",
    "derive_sidecar_path",
    "write_outputs",
]
