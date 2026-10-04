# Plan: Silent taxonomy domain is an upstream gap

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0130 D2/D3 and ADR-0139; the gap rows in
  `references/visual-observation.md` and their pack test
  `test_visual_authority_upstream_gap.py`; the roster walk in
  `tests/roster/test_visual_handoff_golden_path.py`, which already evaluates
  the two existing gap sources. Non-structural.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

Change the rule table first, then bring every restatement into line with it,
then teach the roster walk and the evals the new source. The walk reads the
installed table, so the walk test reds until the table names the source — the
table is the single owner and the rest follow.

## Constraints

- ADR-0139 D1–D3; ADR-0130 D3 (no lower rung fills the axis).
- The `SKILL.md` body budget AC-0003 names.
- `packs/AGENTS.md` — portable wording, no internal-governance citations in
  shipped content; the pack change bumps its patch version.

## Construction tests

**Integration tests:** the roster golden-path module, which installs both
packs and walks every fixture.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale — ADR-0139 | T4 | ADR status line | ADR shape lint green |
| User-facing promise — the how-to guide | T1 | roster adopter-prose test | test green |
| Release history — changelog | T4 | the changelog heading at the version AC-0010 names | `catalogue verify` exits zero |

## Design (LLD)

### Design decisions

- **One operation kind.** A silent domain is completed by the same operation as
  an unresolved one, so it reuses `domain-completion-required`. Traces to
  AC-0002.
- **"Needed" is fixture data in the walk.** Whether a surface needs a domain is
  agent judgement, so every fixture whose taxonomy resolves declares
  `needed_domains` in its `scenario.toml`; there is no default. The walk tests
  silence per section: a needed domain is silent unless the taxonomy has a
  `### <Domain>` commitments section for it or records it `unresolved` — a
  coarser stand-in for ADR-0139's per-value test, which the fixtures satisfy
  because each section they carry holds every value their implementation
  sets. The existing checkout fixtures — `confirmed`, `unconfirmed`,
  `unresolved-domain` and `refusal` — need Typography, Color, Spacing and
  rhythm, Shape and containment, and Spatial structure, so their taxonomies
  gain a Shape and containment section carrying the divider stroke and a
  Spatial structure section carrying the column split and breakpoint the
  golden implementation already uses. The walk reads the third source from the installed `gap-sources` cell
  and raises if the cell stops naming it. Traces to AC-0005, AC-0006, AC-0011.

<!-- Owned by: T1, T2. -->

## Tasks

### T1: The rule names three gap sources everywhere it is stated

**Depends on:** none
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md, packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md, guides/frontend-engineering/how-to/read-the-design-handoff.md, packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_upstream_gap.py, tests/roster/test_frontend_visual_authority_adopter_prose.py
**Tests:**
- AC-0001, AC-0002: new assertions in `test_visual_authority_upstream_gap.py` over the three cells; its exact `gap-outcome` assertion moves with the cell.
- AC-0003: a step-2 assertion in the same module; the existing body-budget test stays green.
- AC-0004: the adopter-prose roster test asserts the third source in the guide.
- AC-0012: pack-test assertions over the `SKILL.md` gap paragraph and adopter-prose assertions over the guide's routing sentence.
- `stub: true`

```python
def test_the_gap_names_its_silent_domain_source() -> None:
    """AC-0001: a domain a resolved taxonomy leaves silent is a gap source."""
    sources = rule("Upstream gaps", "gap-sources").lower()
    assert "silent" in sources
```

**Done when:** `python3 -m pytest packs/frontend-engineering/tests tests/roster/test_frontend_visual_authority_adopter_prose.py -q` passes.

### T2: The walk holds a silent domain

**Depends on:** T1
**Touches:** tests/roster/test_visual_handoff_golden_path.py, tests/roster/fixtures/visual-handoff-golden-path/**
**Tests:**
- AC-0005, AC-0011: walk tests over the `silent-domain` fixture.
- AC-0006: the existing walk tests stay green with explicit `needed_domains`, plus an in-test mutation removing the `confirmed` Typography section.
- no stub (implementation-discovered) — discovery predicate: the T1 cell wording; proof obligation: the silent-domain test reds when the cell's third source is removed.

**Done when:** `python3 -m pytest tests/roster/test_visual_handoff_golden_path.py tests/roster/test_visual_target_exclusive_property.py -q` passes.

### T3: The evals cover the hold and stop leaving type silent

**Depends on:** T1, T2
**Touches:** packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json, tests/roster/test_visual_handoff_golden_path.py
**Tests:**
- AC-0007, AC-0008: roster assertions over the installed `evals.json`.
- no stub (implementation-discovered) — discovery predicate: the existing eval-case fixture in the roster module; proof obligation: each assertion reds on the current `evals.json`.

**Done when:** `python3 -m pytest tests/roster/test_visual_handoff_golden_path.py packs/frontend-engineering/tests -q` passes.

### T4: Decision accepted and release cut

**Depends on:** T1, T2, T3
**Touches:** docs/adr/0139-a-taxonomy-silent-domain-is-an-upstream-gap.md, docs/adr/README.md, packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_release.py, docs/product/changelog.md
**Tests:**
- AC-0009: goal-based — `python3 -m pytest tests/roster/test_lint_adr_shape_corpus.py -q` and the ADR index regenerated with no diff on re-run; no stub (goal-based).
- AC-0010: goal-based — `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .`; no stub (goal-based).

**Done when:** both commands and the frontend pack suite pass.

Review shape: one review unit — one rule, its restatements, and their tests.

## Rollout

Pack content and tests only; rollback is a revert.

## Changelog

- 2026-10-04: spec approved by eugenelim
- 2026-10-04: plan approved by eugenelim
