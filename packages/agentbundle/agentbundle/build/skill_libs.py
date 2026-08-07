"""skill-libs/ build-pipeline primitive class.

Projects a **stdlib-only package module** into a skill's ``scripts/`` directory,
so one authored source serves both the package and the skill without the skill
importing the package at runtime (ADR-0074).

Sibling to ``user_libs``, and deliberately not a generalisation of it. The two
differ in the property that matters:

- ``user-libs`` targets ``~/.agentbundle/lib`` — a ``sys.path`` *floor* appended
  at lowest precedence and guarded on the directory existing. It may legitimately
  be **absent**, and a consumer degrades gracefully when it is.
- ``skill-libs`` targets the skill's own ``scripts/`` dir, so the file ships with
  the skill and is present whenever the skill is. That matters for code whose
  absence cannot be degraded around: an advisory lock that might not be there
  fails *open*, which is the one failure mode the state lock must not have.

Source of truth is the package module; the projected copy is generated. It is
copied **byte-for-byte** — no header is injected, so drift is a plain byte
comparison and the source's own docstring is what tells a reader the copy is
generated. (``user_libs`` makes the same choice for the same reason.)

The pack copy flows onward: ``build/main.py`` copytrees the whole ``.apm/`` tree
into each dist pack, and ``make build-self`` projects skills into ``.claude/`` and
``.agents/``, so one source reaches every consumer.

Both halves of the build-pipeline contract live here:

- ``apply_projection(packs_dir)`` — write the targets. Called by
  ``make build-self``. Default file mode (importable Python, no exec bit).
- ``check_drift(packs_dir)`` — read-only gate for ``make build-check``.
  Resolves the same three outcomes as ``user-libs``/``adapter-root-bins``:
  **modified** / **missing** / **orphaned**.

Like ``user-libs``, this is build-pipeline-only: it has no per-adapter projection
rules, so adding it does **not** bump the adapter-contract version.

**Non-monorepo invocation.** The package source only exists in the development
monorepo. When it is absent (``packs_dir.parent`` is not the repo root — a
fixture packs dir, or a packaged ``agentbundle`` run outside the monorepo) the
projection is a no-op and the gate is silent: there is nothing to compare
against. The *committed* copy is what adopters receive, so a no-op costs them
nothing. Real ``make build-self`` / ``make build-check`` always run with
``packs_dir == <repo>/packs``, so the gate is live in CI.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

# Declared projections: (repo-relative source, packs-relative target).
#
# One row today. When a second stdlib-only module needs projecting into a skill,
# add a row — not a parameter. Every row is a single file: a tree walk would
# invite projecting a package with third-party imports, which the target cannot
# satisfy.
PROJECTIONS: tuple[tuple[Path, Path], ...] = (
    (
        Path("packages") / "agentbundle" / "agentbundle" / "statelock_core.py",
        Path("core") / ".apm" / "skills" / "work-loop" / "scripts" / "_statelock.py",
    ),
)

_LABEL = "skill-libs"
_REGEN = "run: make build-self FORCE=1"


@dataclass(frozen=True)
class SkillLibProjection:
    """One concrete projection: copy ``source`` to ``target``."""

    source: Path
    target: Path


def compute_projections(packs_dir: Path) -> list[SkillLibProjection]:
    """Return the ``(source → target)`` list, in declaration order.

    A row whose source is absent is skipped — that is the documented
    non-monorepo no-op. ``packs_dir.parent`` is the repo root in every real
    ``make build-self`` / ``make build-check`` invocation.
    """
    repo_root = packs_dir.parent
    projections: list[SkillLibProjection] = []
    for source_rel, target_rel in PROJECTIONS:
        source = repo_root / source_rel
        if not source.is_file():
            continue
        projections.append(
            SkillLibProjection(source=source, target=packs_dir / target_rel)
        )
    return projections


def apply_projection(packs_dir: Path) -> None:
    """Write every declared target from its source. Called by build-self.

    Idempotent. Resolves **missing** (written) and **modified** (overwritten).
    There is no orphan sweep: every target is named explicitly, so retiring a
    row means hand-removing its committed target — the same requirement
    ``user_libs`` documents for whole-package retirement.
    """
    for proj in compute_projections(packs_dir):
        proj.target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(proj.source, proj.target)


def check_drift(packs_dir: Path) -> list[str]:
    """Return drift descriptions for build-check; empty list == clean.

    **modified** / **missing** per declared row, plus **orphaned** for a target
    whose source row was retired but whose file is still committed. Each
    description ends with the regeneration command.
    """
    drifts: list[str] = []
    repo_root = packs_dir.parent
    projections = compute_projections(packs_dir)
    declared_targets = {packs_dir / target_rel for _, target_rel in PROJECTIONS}

    for proj in projections:
        target_display = _display(proj.target, repo_root)
        source_display = _display(proj.source, repo_root)
        try:
            source_bytes = proj.source.read_bytes()
        except OSError as exc:  # pragma: no cover — defensive
            drifts.append(f"[{_LABEL}] source unreadable: {exc}")
            continue
        if not proj.target.exists():
            drifts.append(
                f"[{_LABEL}] missing: {target_display} "
                f"(source: {source_display}); {_REGEN}"
            )
            continue
        if proj.target.read_bytes() != source_bytes:
            drifts.append(
                f"[{_LABEL}] modified: {target_display} diverges from "
                f"{source_display} — edit the source, not the projection; "
                f"{_REGEN}"
            )

    # Orphan: the package tree IS here but this specific module is gone, i.e.
    # the row was retired and its committed target left behind.
    #
    # The predicate is the source's *package directory*, not the source file.
    # Keying on the file alone conflates "row retired" with "not in the
    # monorepo" — and the non-monorepo shape is precisely `source absent,
    # target present`, because the target is committed and ships with the pack.
    # That mistake reported a false orphan for every fixture packs dir and broke
    # three build-check integration tests.
    projected_targets = {p.target for p in projections}
    for target in sorted(declared_targets - projected_targets):
        source_rel = next(s for s, t in PROJECTIONS if packs_dir / t == target)
        package_dir = repo_root / source_rel.parent
        if not package_dir.is_dir():
            continue  # not the monorepo — nothing to compare, stay silent
        if (repo_root / source_rel).exists() or not target.exists():
            continue
        drifts.append(
            f"[{_LABEL}] orphaned: {_display(target, repo_root)} present but its "
            f"source {source_rel.as_posix()} is gone; remove the projection or "
            f"restore the source; {_REGEN}"
        )

    return drifts


def _display(path: Path, repo_root: Path) -> str:
    """Render *path* relative to the repo root for a drift message."""
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:  # pragma: no cover — defensive
        return path.as_posix()
