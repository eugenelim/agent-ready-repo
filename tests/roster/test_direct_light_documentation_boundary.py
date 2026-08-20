#!/usr/bin/env python3
"""Repository-level coverage for the direct-light documentation boundary.

Lives here, not under `packs/core/tests/`, because both properties read files
above the pack root — `docs/architecture/` and several `guides/` pages. The
`pack-tests-stay-in-pack` boundary check rejects a pack test that reaches above
its owning pack, and it is right to: a pack's tests ship with the pack, so a
test that depends on repository layout would fail in an adopter's checkout.

Two properties:

  1. The architecture page states the *narrowed* dispatch invariant and carries
     all three classification branches.
  2. No living documentation home still describes light mode as persisting a
     lean spec, or a spec as carrying the implementation "how".

Frozen records are deliberately out of scope: accepted RFC and ADR bodies and
Shipped or Archived spec directories keep their original wording as history.

Prose is matched on whitespace-normalized text so a pure re-wrap is not a
failure, while deleting a pinned claim still is.
"""

import pathlib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _normalized(text: str) -> str:
    """Collapse whitespace so a contract pin survives re-wrapping."""

    return " ".join(text.split())


def test_workspace_dispatch_and_direct_light_have_distinct_durability() -> None:
    """Pin the architecture boundary without coupling it to line wrapping."""
    architecture = _normalized(
        (_REPO_ROOT / "docs/architecture/work-intake-and-artifact-routing.md").read_text(
            encoding="utf-8"
        )
    )

    for required in (
        "Every workspace-dispatchable, queued, or resumable build item resolves "
        "to an existing durable `spec.md` and sibling `plan.md`",
        "An explicit direct-light request is session-local, creates no workspace "
        "entry, and is ineligible for argless dispatch or fresh-session resumption.",
        "+-- direct light --> work-loop from current request",
        "+-- durable single slice --> spec + plan --> workspace --> work-loop",
        "+-- multi-slice outcome --> brief --> confirmed specs + plans",
    ):
        assert _normalized(required) in architecture, required


# Frozen or self-referential paths, each exempt for a stated reason.
_EXEMPT_PREFIXES = (
    "docs/rfc/",        # accepted proposals are immutable history
    "docs/adr/",        # accepted decisions are immutable history
    ".claude/",         # generated projection
    ".agents/",         # generated projection
    "dist/",            # generated build output
    "docs-site/src/content/docs/guides/",  # generated from guides/
    "tests/roster/",    # this file holds the patterns as assertion strings
    "packs/core/tests/",  # pack tests hold them as negative assertions
)

# Unambiguous retired phrasings only. A looser pattern such as "spec carries the
# implementation" false-positives on unrelated prose — the Mermaid parser notes in
# docs/architecture/binder-publishing/ use that wording about a *web standard*
# mandating behavior, which has nothing to do with docs/specs.
_RETIRED_CLAIMS = (
    "lean inline spec",
    "Light-mode lean fill",
    "the spec stays the *how*",
    "carries the *what/why*; the spec stays",
    "If the change touches more than one file, the spec is cheap insurance",
)


# The active spec quotes the retired claims in order to prohibit them.
_QUOTES_CLAIMS_TO_FORBID_THEM = "docs/specs/direct-light-execution/"

_FROZEN_SPEC_STATUSES = ("Shipped", "Archived")


def _is_frozen_spec(path: pathlib.Path, relative: str) -> bool:
    """True only for a Shipped or Archived spec directory.

    The contract exempts *frozen* records, not every spec. Exempting all of
    `docs/specs/**` would let a future Draft, Approved, or Implementing spec
    reintroduce a retired claim and stay green — the exemption has to read the
    status rather than the path.
    """

    if not relative.startswith("docs/specs/"):
        return False
    spec = path.parent / "spec.md"
    if path.name != "spec.md":
        # A sibling file in a spec directory inherits that spec's status.
        if not spec.is_file():
            return False
    else:
        spec = path
    for line in spec.read_text(encoding="utf-8").splitlines():
        if line.startswith("- **Status:**"):
            return any(s in line for s in _FROZEN_SPEC_STATUSES)
    return False


def _living_markdown() -> list[pathlib.Path]:
    living = []
    for path in sorted(_REPO_ROOT.rglob("*.md")):
        if "node_modules" in path.parts:
            continue
        relative = path.relative_to(_REPO_ROOT).as_posix()
        if relative.startswith(_EXEMPT_PREFIXES):
            continue
        if relative.startswith(_QUOTES_CLAIMS_TO_FORBID_THEM):
            continue
        if _is_frozen_spec(path, relative):
            continue
        living.append(path)
    return living


def test_living_guidance_no_longer_describes_persisted_light_specs() -> None:
    """Scan every living markdown file, rather than a list someone must remember.

    This began as a hard-coded list of known offenders and therefore could not
    catch a surface nobody had thought to list — two real ones slipped through
    exactly that way. An enumeration of files to check leaks; a scan with a
    justified exemption list does not.
    """

    offenders = []
    for path in _living_markdown():
        normalized = _normalized(path.read_text(encoding="utf-8")).lower()
        for claim in _RETIRED_CLAIMS:
            if _normalized(claim).lower() in normalized:
                offenders.append((path.relative_to(_REPO_ROOT).as_posix(), claim))

    assert not offenders, f"retired claims survive on living surfaces: {offenders}"


def test_the_sweep_actually_scans_something() -> None:
    """Positive control: an empty corpus would make the sweep vacuously green."""

    files = _living_markdown()
    # No arbitrary corpus size: ordinary documentation pruning would fail that for
    # an unrelated reason. What matters is that the exemptions did not swallow the
    # surfaces this sweep exists to police, and that a non-frozen spec is in scope.
    names = {p.relative_to(_REPO_ROOT).as_posix() for p in files}
    for required in (
        "packs/core/seeds/docs/CONVENTIONS.md",
        "guides/_shared/explanation/the-three-loops.md",
        "guides/core/how-to/plan-and-execute-non-trivial-work.md",
        "docs/architecture/work-intake-and-artifact-routing.md",
    ):
        assert required in names, required
