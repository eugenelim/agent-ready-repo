# Plan: Frame-intent experience handoff

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/product-engineering/.apm/skills/frame-intent/SKILL.md` (current authoring flow and absence behavior); `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md` (single intent prompt sheet); `packs/product-engineering/.apm/skills/frame-intent/references/intent-model.md` and `references/digital-experience-contract.md` (existing product-field owners); `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py` (pack prose-contract test pattern); `packs/experience-design/.apm/skills/creative-direction/SKILL.md` (existing `target surface` term and the downstream design boundary). Named deviation: no cross-pack integration is registered because the handoff is portable prose and must work without Experience Design.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline.

## Approach

Add one level- and impact-gated step to `frame-intent`, then expose the selected product facts through one optional section in the existing intent template. Tests pin the activation matrix, the five fact groups, the prohibited decision set, and the absence of Experience Design wiring before the source prose changes. The pack ships as a patch release with updated evals, one user guide passage, and an outcome-led changelog entry.

## Constraints

- The intent model remains the single product artifact at every altitude.
- The Digital Experience Contract remains the cross-discipline owner map; Product Engineering facts stay in its Product Engineering section.
- The optional handoff is a projection for discovery, not a new canonical schema or document.
- The change touches no Experience Design skill, Frontend Engineering skill, design-review surface, or reviewer agent.
- Product Engineering `.apm/` changes require matching patch versions in `pack.toml` and `.claude-plugin/plugin.json`, an eval-harness update, self-host regeneration, and an outcome-led release entry.

## Construction tests

**Integration tests:** run the targeted Product Engineering pack tests for the new handoff, existing frame-intent review wiring, and intent-triad wiring. Run the frame-intent eval JSON validation through the repository's existing pack-eval test route.

**Manual verification:** after self-host regeneration, invoke the published frame-intent skill on one qualifying feature request and record that it offers or emits the Product-to-experience handoff without choosing a design direction or invoking another skill.

## Work-loop decision record

- **Files:** the frame-intent skill, intent template, evals, one Product Engineering test module, one Product Engineering guide, pack/plugin versions, release history, generated self-host projections, and this spec directory.
- **Done:** the new contract test earns red then passes; nearby frame-intent, intent-template, and pack-wiring suites pass; catalogue verification and `make lint-ruff lint-mypy` pass; one published-skill invocation is recorded.
- **Not changing:** Product Experience or Frontend Engineering skills, creative-direction behavior, design-review or reviewer agents, the intent model, Digital Experience Contract ownership, or any runtime interface.
- **Declined — cross-pack integration declaration:** cut-before-adding rung 1; ordinary Markdown is sufficient and a declared dependency would violate graceful absence.
- **Declined — separate handoff document or schema:** cut-before-adding rung 2; the intent template and Digital Experience Contract already own every required fact.
- **Declined — automatic creative-direction handoff:** explicitly prohibited by the accepted outcome; product framing exposes facts and leaves design choices downstream.
- **Tail size:** under 2,000 reviewable behavior and test lines; no WIDE, MIXED, or DEEP tail split is required.
- **Domain grounding:** no extra domain claim is needed; the accepted request, intent model, and Digital Experience Contract establish the product-to-experience boundary.
- **Resolve-vs-surface record:** shaping round 1 Major (release version and eval duties were non-binding) — required, draft-origin, repaired in `Agent Rules` and AC-0010. Shaping round 1 Medium (no-RFC boundary was not mechanically explicit) — required, draft-origin, repaired in `Never do` and AC-0009. Adversarial round 1 Blocker (manual QA had no declared artifact) — required, draft-origin, repaired in T3 with an explicit visual/manual mode, qualifying request, observed-result fields, and verification-ledger destination. Adversarial round 1 release-history Concern — refuted by independent adjudication because the Durable Outputs map may own closeout evidence. No finding remains open.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Published behavior / `frame-intent/SKILL.md` | T1, T2 | New handoff contract tests | Manual consumer invocation and targeted pytest |
| Intent prompt / `intent-template.md` | T1, T2 | Template-shape tests | Targeted pytest and catalogue verification |
| Evaluation contract / eval JSON and pack tests | T1, T2 | Red-green test record and JSON validation | Targeted pytest and pack eval gate |
| User guidance / feature-intent guide | T3 | Content-pin and link checks | Repository documentation gates reached by catalogue verification |
| Release identity and history | T3 | Matching-version assertions and generated projection diff | Catalogue lint/verify and clean regeneration check |

## Design (LLD)

### Design decisions

The handoff is an optional section of the existing intent, not a sibling artifact. That keeps the intent and Digital Experience Contract authoritative while giving downstream work one discoverable projection. The activation decision is made from `Level` plus material surface effect; pack installation state does not decide whether product facts exist. Traces to: AC-0001 through AC-0008.

**Owned by:** T2

### Interfaces & contracts

The published prompt contract has five fields: affected journey or surface; user outcome and first-success behavior; product mechanism or proof; claim evidence; constraints, prohibited claims, and material unknowns. Each field points back to or derives from the current intent and Digital Experience Contract rather than establishing another owner. Traces to: AC-0004 and AC-0007.

**Owned by:** T2

### Failure, edge cases & resilience

No Experience Design pack is required or probed. Non-surface work and product-level altitudes omit the optional block, while missing evidence stays an explicit unknown inside a qualifying handoff rather than becoming a guessed claim. Traces to: AC-0002, AC-0003, and AC-0006.

**Owned by:** T2

### Dependencies & integration

The implementation adds no dependency or automatic invocation. An installed downstream pack consumes ordinary Markdown and respects the Digital Experience Contract owner map; an absent pack leaves the same intent artifact valid. Traces to: AC-0006 through AC-0008.

**Owned by:** T2, T3

## Tasks

### T1: The situational handoff contract fails against the current skill

**Depends on:** none

**Mode:** TDD

**Touches:** `packs/product-engineering/tests/pack/test_frame_intent_experience_handoff.py`

**Tests:**

- Add the exact red stub below. It reads only the handoff section for behavioral assertions, reads the optional template block for shape assertions, and parses `pack.toml` for absence wiring (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008).

```python
"""Contract checks for frame-intent's situational experience handoff."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = PACK_ROOT / ".apm/skills/frame-intent/SKILL.md"
TEMPLATE_PATH = PACK_ROOT / ".apm/skills/frame-intent/assets/intent-template.md"


def _section(path: Path, title: str) -> str:
    """Return one level-two Markdown section from a shipped artifact."""
    text = path.read_text(encoding="utf-8")
    match = re.search(
        rf"^## {re.escape(title)}\n(?P<body>.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"{path}: missing section {title!r}"
    return " ".join(match.group("body").split())


def test_handoff_activates_only_for_material_surface_effects() -> None:
    section = _section(SKILL_PATH, "Situational product-to-experience handoff")
    assert "`capability` or `feature`" in section
    for trigger in (
        "creates a human-facing digital surface",
        "materially changes a user journey, interaction, content hierarchy, or visible state",
        "changes what a surface must prove, explain, or allow a person to do",
    ):
        assert trigger in section
    for excluded in (
        "backend-only",
        "infrastructure",
        "internal refactors",
        "dependency changes",
        "build work",
    ):
        assert excluded in section


def test_product_altitudes_never_receive_the_handoff() -> None:
    section = _section(SKILL_PATH, "Situational product-to-experience handoff")
    assert "`product-vision`" in section
    assert "`product-strategy`" in section
    assert "do not offer or emit" in section.lower()


def test_optional_block_contains_only_product_facts() -> None:
    block = _section(TEMPLATE_PATH, "Product-to-experience handoff")
    for label in (
        "Affected journey or surface",
        "User outcome and first-success behavior",
        "Product mechanism or proof",
        "Evidence for user-visible claims",
        "Constraints, prohibited claims, and material unknowns",
    ):
        assert f"**{label}:**" in block
    assert "optional" in block.lower()
    assert "capability" in block and "feature" in block


def test_handoff_leaves_experience_decisions_downstream() -> None:
    section = _section(SKILL_PATH, "Situational product-to-experience handoff")
    for decision in (
        "engagement mode",
        "visual direction",
        "typography",
        "color",
        "layout",
        "motion",
        "first-viewport composition",
        "signature interaction",
        "implementation approach",
    ):
        assert decision in section
    assert "must not select" in section.lower()


def test_experience_design_is_optional_and_has_no_pack_wiring() -> None:
    section = _section(SKILL_PATH, "Situational product-to-experience handoff")
    assert "Experience Design is not installed" in section
    assert "must not invoke" in section
    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    assert all(
        integration["pack"] != "experience-design"
        for integration in manifest["pack"].get("integrations", [])
    )
```

**Grounding:** The exact stub was compiled from this plan and run read-only against the current source on 2026-09-27. It failed at the first assertion because `SKILL.md` has no `## Situational product-to-experience handoff` section, establishing the intended red without creating a repository test file.

**Done when:** the stub compiles and fails against the unmodified source because the handoff section does not yet exist.

### T2: Qualifying capability and feature intents expose product facts

**Depends on:** T1

**Mode:** TDD

**Touches:** `packs/product-engineering/.apm/skills/frame-intent/SKILL.md`, `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`, `packs/product-engineering/.apm/skills/frame-intent/evals/evals.json`

**Tests:**

- Make T1 green without weakening its section bounds or pack-wiring assertion.
- Add eval cases for a qualifying feature, a backend-only feature, a product-strategy surface mention, and an installation without Experience Design (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008).
- Run the existing frame-intent shaping-review and intent-triad suites unchanged to catch nearby contract drift.

**Approach:** Insert one `## Situational product-to-experience handoff` procedure section after the opportunity step, and add one level- and impact-conditional template section after `## Opportunity`. Keep the handoff readable as ordinary Markdown so no downstream pack or parser is required.

**Done when:** T1 and the existing targeted Product Engineering suites pass, and the eval JSON remains valid.

### T3: The patch release publishes the new behavior

**Depends on:** T2

**Mode:** Goal-based check + Visual / manual QA

**Touches:** `guides/product-engineering/how-to/shape-a-feature-intent.md`, `packs/product-engineering/pack.toml`, `packs/product-engineering/.claude-plugin/plugin.json`, `docs/product/changelog.md`, generated self-host projections

**Tests:**

- Assert `pack.toml` and `.claude-plugin/plugin.json` carry the same patch version.
- Run Product Engineering pack wiring tests and catalogue lint/verify after self-host regeneration.
- Confirm the guide describes the optional, situational handoff without promising visual-direction behavior.
- Confirm the release entry includes an outcome-led Highlights block because consumers gain a new capability.
- Confirm the final diff contains no path under `docs/rfc/` (AC-0009).
- Confirm matching patch versions and all four new eval cases are present (AC-0010).
- **No stub (visual / manual QA):** invoke the self-hosted `frame-intent` skill with a capability- or feature-level request that materially changes a human-facing surface. Record the exact request, whether the Product-to-experience handoff was offered or emitted, the five product-fact groups observed, confirmation that no downstream skill was invoked, and any unexercised scope in `docs/specs/frame-intent-experience-handoff/notes/verification-ledger.md` (AC-0008).

**Done when:** matching versions, the guide, release history, generated projections, targeted tests, catalogue verification, repository lint/type gates, and the recorded published-skill invocation are complete.

## Rollout

The Product Engineering pack ships as a patch release. Existing intents remain valid because the new block is optional, and adopters without Experience Design receive the same Product Engineering artifact. Rollback restores the prior pack content and version metadata; no persisted schema or migration exists.

## Risks

- A broad surface keyword test could activate on backend work that merely mentions users. The activation rule therefore requires a material change to a human-facing surface, journey, interaction, hierarchy, visible state, or claim/action obligation.
- Copying Product Engineering facts into a second schema would create competing owners. The optional block instead derives or points to existing intent and Digital Experience Contract fields.
- Naming downstream design choices in the handoff would turn framing into premature design. The test pins the prohibited decision set inside the bounded skill section.
- A new pack integration could make graceful absence false. The pack-wiring assertion rejects any Experience Design integration entry.

## Changelog

- 2026-09-27: spec approved by owner
- 2026-09-27: plan approved by owner
