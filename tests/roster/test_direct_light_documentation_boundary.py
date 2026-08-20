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


def test_living_guidance_no_longer_describes_persisted_light_specs() -> None:
    """Pin the swept direct-light terminology on its living documentation homes."""
    living_sources = (
        "packs/core/seeds/docs/CONVENTIONS.md",
        "packs/core/DESIGN.md",
        "guides/_shared/explanation/the-three-loops.md",
        "guides/core/explanation/token-economy.md",
        "guides/core/explanation/why-a-brief-layer.md",
        "packs/core/.apm/skills/new-spec/assets/spec.md",
        "packs/core/.apm/skills/new-spec/assets/plan.md",
    )
    retired_claims = (
        "lean inline spec",
        "the spec stays the *how*",
        "engineering *how* — including any low-level design — stays in the spec",
        "Light-mode lean fill",
    )

    for relative_path in living_sources:
        text = (_REPO_ROOT / relative_path).read_text(encoding="utf-8")
        normalized = _normalized(text).lower()
        for claim in retired_claims:
            assert _normalized(claim).lower() not in normalized, (
                relative_path,
                claim,
            )
