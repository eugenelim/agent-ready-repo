"""T4: shared-libs/ build-pipeline primitive class.

Source rule: ``packs/<pack>/.apm/shared-libs/*.py``.
Target rule: for every skill in any pack whose ``SKILL.md`` declares
``metadata.auth: creds``, project each ``shared-libs/*.py`` byte-
identical into that skill's ``scripts/`` directory; create
``scripts/`` if absent.

This module owns both halves of the projection contract:

- ``apply_projection(packs_dir)`` — write the files. Called by
  ``make build-self``.
- ``check_drift(packs_dir)`` — read-only gate. Returns a list of
  drift descriptions (empty list == clean). Each description
  classifies one of the three outcomes RFC-0013 § 4c pins:
    * **modified** — projected file exists but bytes diverge from source
    * **missing** — consumer declares ``auth: creds`` but projected file absent
    * **orphaned** — projected file present but consumer no longer
      declares ``auth: creds`` (or the source has been removed)

Inter-pack collision: two packs both shipping ``shared-libs/<file>``
under the same basename is a hard error (``ValueError``) at
projection time. The v1 catalogue ships one source pack
(``credential-brokers``); the rail exists to refuse a future
second-pack collision before it can silently overwrite.

The detection of ``metadata.auth: creds`` is a regex scan against
``SKILL.md`` text, not a full YAML parse. The strict lint
(``tools/lint-agent-artifacts.py``) does the YAML round-trip;
this module only needs to know *which* skills are consumers, and
the regex is stdlib-only — the build pipeline carries no PyYAML
dependency.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

# Pin the source path so a downstream consumer that wants to
# enumerate shim sources doesn't hardcode the literal repeatedly.
SOURCE_SUBDIR = ".apm/shared-libs"

# Static allow-list of basenames the build pipeline recognises as
# shim files. Used by the orphan-rail when ``collect_sources`` returns
# empty (a future PR removes the shared-libs source) — without this,
# the orphan check would key on an empty source set and silently miss
# stale projected copies under consumer skills.
KNOWN_SHIM_BASENAMES: frozenset[str] = frozenset({
    "credentials_shim.py",
    "_keychain_macos.py",
    "_credman_windows.py",
})

# Regex match against `auth: creds` as an indented mapping value under
# `metadata:`. The shape we look for, anchored to start-of-line:
#     metadata:
#       ...
#       auth: creds
# We don't try to honour YAML's full grammar — quoted form
# (`auth: "creds"`) and inline form (`metadata: { auth: creds }`) are
# refused by the lint, so they cannot reach the build pipeline.
# An unquoted scalar token is what every in-tree credentialed skill
# carries today.
_AUTH_CREDS_RE = re.compile(
    r"^[ \t]+auth:[ \t]+creds[ \t]*(?:#.*)?$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class SharedLibProjection:
    """One concrete projection: copy `source` to `target`."""

    source: Path
    target: Path


def collect_sources(packs_dir: Path) -> dict[str, Path]:
    """Return ``{basename → source_path}`` for every ``.apm/shared-libs/*.py``.

    Raises ``ValueError`` on inter-pack basename collision — two packs
    shipping the same basename produces non-deterministic projection
    order and silent overwrites; refuse hard at enumeration time.
    """
    sources: dict[str, Path] = {}
    for pack in sorted(packs_dir.iterdir()):
        if not pack.is_dir() or not (pack / "pack.toml").exists():
            continue
        shared = pack / SOURCE_SUBDIR
        if not shared.is_dir():
            continue
        for src in sorted(shared.glob("*.py")):
            if src.name in sources:
                raise ValueError(
                    f"shared-libs collision: '{src.name}' shipped by both "
                    f"{sources[src.name]} and {src}"
                )
            sources[src.name] = src
    return sources


def _skill_declares_auth_creds(skill_md: Path) -> bool:
    """Return True if ``SKILL.md``'s frontmatter declares ``auth: creds``.

    Scoped to the frontmatter — text between the first pair of ``---``
    delimiters. A body-only mention (e.g. inside a code fence) is not
    a declaration.
    """
    try:
        text = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return False
    fm = "\n".join(lines[1:end])
    return _AUTH_CREDS_RE.search(fm) is not None


def find_creds_consumers(packs_dir: Path) -> list[Path]:
    """Return every skill-source directory whose ``SKILL.md`` declares
    ``auth: creds``. Sorted for deterministic projection order.
    """
    consumers: list[Path] = []
    for pack in sorted(packs_dir.iterdir()):
        if not pack.is_dir() or not (pack / "pack.toml").exists():
            continue
        skills_dir = pack / ".apm" / "skills"
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue
            if _skill_declares_auth_creds(skill_md):
                consumers.append(skill_dir)
    return consumers


def compute_projections(packs_dir: Path) -> list[SharedLibProjection]:
    """Return the full list of ``(source → target)`` pairs.

    Order: outer loop over consumers (sorted), inner loop over source
    basenames (sorted). Deterministic — drift gates depend on it.
    """
    sources = collect_sources(packs_dir)
    if not sources:
        return []
    consumers = find_creds_consumers(packs_dir)
    out: list[SharedLibProjection] = []
    for skill_dir in consumers:
        scripts = skill_dir / "scripts"
        for basename in sorted(sources):
            out.append(
                SharedLibProjection(
                    source=sources[basename],
                    target=scripts / basename,
                )
            )
    return out


def apply_projection(packs_dir: Path) -> None:
    """Write every projection target and remove orphans. Creates
    ``scripts/`` if absent.

    Called by ``make build-self``. Idempotent — running twice produces
    the same on-disk state.

    Three drift outcomes RFC-0013 § 4c pins are all resolved here:
      * **missing** → file written from source
      * **modified** → file overwritten from source
      * **orphaned** → file removed (consumer no longer declares
        ``auth: creds``, OR the source basename is no longer shipped)
    """
    projections = compute_projections(packs_dir)
    expected_targets = {p.target for p in projections}
    # Write current set first so an orphan removed below cannot be
    # mistaken for a missing write that needs re-running.
    for proj in projections:
        proj.target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(proj.source, proj.target)
    # Orphan removal uses the static basename allow-list so the rail
    # still fires when ``collect_sources`` returns empty (the source
    # pack has been dropped). Without the static list, the orphan
    # set would silently be empty and stale projected copies would
    # survive.
    for existing in _enumerate_existing_projections(packs_dir, set(KNOWN_SHIM_BASENAMES)):
        if existing not in expected_targets:
            try:
                existing.unlink()
            except FileNotFoundError:  # pragma: no cover — race-only
                pass


def _enumerate_existing_projections(
    packs_dir: Path, source_basenames: set[str]
) -> list[Path]:
    """Return every existing projected file in any skill's ``scripts/``
    whose basename matches a shared-libs source.

    Used to detect orphans: a projected file that exists on disk but
    is no longer claimed by any (source × creds-consumer) pairing.
    """
    found: list[Path] = []
    for pack in sorted(packs_dir.iterdir()):
        if not pack.is_dir() or not (pack / "pack.toml").exists():
            continue
        skills_dir = pack / ".apm" / "skills"
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            scripts = skill_dir / "scripts"
            if not scripts.is_dir():
                continue
            for entry in sorted(scripts.iterdir()):
                if entry.is_file() and entry.name in source_basenames:
                    found.append(entry)
    return found


def check_drift(packs_dir: Path) -> list[str]:
    """Return drift descriptions for ``make build-check``.

    Three outcomes per RFC-0013 § 4c:
        * **modified** — projected bytes diverge from source
        * **missing** — consumer declares ``auth: creds`` but file absent
        * **orphaned** — projected file present, no claiming pairing

    Each description ends with the regeneration command so the
    operator can resolve drift in one invocation.
    """
    drifts: list[str] = []
    try:
        sources = collect_sources(packs_dir)
    except ValueError as exc:
        # Collision blocks the projection entirely — report and stop.
        drifts.append(f"[shared-libs] {exc}; run: make build-self")
        return drifts
    if not sources:
        # No source pack carries shared-libs/. The orphan rail still
        # fires: stale projected copies under any consumer skill must
        # surface, otherwise dropping the source pack silently leaves
        # vendored copies behind. Use the static basename allow-list
        # so the rail keys on a known set rather than the (empty)
        # source set.
        for existing in _enumerate_existing_projections(
            packs_dir, set(KNOWN_SHIM_BASENAMES)
        ):
            drifts.append(
                f"[shared-libs] orphaned: "
                f"{existing.relative_to(packs_dir.parent).as_posix()} "
                f"present but no source pack ships shared-libs/ "
                f"(remove the file); "
                f"run: make build-self FORCE=1"
            )
        return drifts

    expected_targets: set[Path] = set()
    for proj in compute_projections(packs_dir):
        expected_targets.add(proj.target)
        source_bytes = proj.source.read_bytes()
        if not proj.target.exists():
            drifts.append(
                f"[shared-libs] missing: "
                f"{proj.target.relative_to(packs_dir.parent).as_posix()} "
                f"(consumer declares 'auth: creds'; source: "
                f"{proj.source.relative_to(packs_dir.parent).as_posix()}); "
                f"run: make build-self FORCE=1"
            )
            continue
        actual_bytes = proj.target.read_bytes()
        if actual_bytes != source_bytes:
            drifts.append(
                f"[shared-libs] modified: "
                f"{proj.target.relative_to(packs_dir.parent).as_posix()} "
                f"diverges from "
                f"{proj.source.relative_to(packs_dir.parent).as_posix()}; "
                f"run: make build-self FORCE=1"
            )

    # Orphan check: any projected file whose basename matches a known
    # source but is NOT in expected_targets is orphaned.
    for existing in _enumerate_existing_projections(packs_dir, set(sources)):
        if existing not in expected_targets:
            drifts.append(
                f"[shared-libs] orphaned: "
                f"{existing.relative_to(packs_dir.parent).as_posix()} "
                f"present but no consumer skill claims it "
                f"(remove the file or restore 'metadata.auth: creds' "
                f"in the surrounding SKILL.md); "
                f"run: make build-self FORCE=1"
            )

    return drifts
