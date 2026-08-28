# Plan: RFC and architecture simplification

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/governance-extras/.apm/skills/new-rfc/`,
  `packs/core/.apm/agents/adversarial-reviewer.md`, and
  `packs/architect/.apm/skills/{architect-design,architect-review}/`; analogous
  `docs/specs/new-rfc-fresh-context/` and
  `docs/specs/architect-platform-grounding/`; tests under
  `packs/{governance-extras,core,architect}/tests/`. Uncertainty resolved:
  `design-reviewer` remains unchanged because RFC-0099 assigns this slice to
  architect author self-check and `architect-review`.

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; the approved baseline is immutable after sealing.

## Approach

Reorder `new-rfc` so the existing artifact-choice logic becomes a real
pre-write checkpoint. Add one explicit RFC context/rubric branch to the existing
adversarial agent. Tighten the two architecture skills at their current
author/reviewer owners, reusing their existing real-choice, Stage-0, grounding,
and rubric structure. Prove behavior with seeded fixtures and update only the
existing how-tos and pack releases.

No new helper, reviewer, artifact, template, adapter feature, or orchestration
state is introduced. Template changes are made only when behavior tests show the
skill/rubric alone cannot express a required output.

## Constraints

- RFC-0099, including all 2026-08-27 Errata, and the canonical Core ladder
  govern this slice.
- Workspace dependency resolution blocks plan approval until both prerequisite
  specs are Shipped; the executable task graph uses local task IDs only.
- Agent boundary metadata support from `shaping-review-contracts` precedes the
  changed adversarial agent declaration.
- Existing `new-rfc` research, preview, citation, review, circulation, and index
  gates remain intact after the new pre-write branch.
- Non-design-doc architecture rubrics, well-architected modes, and
  `design-reviewer` remain unchanged; AC4 explicitly adds the YAGNI delta to
  `architect-review`'s existing design-doc route and rubric.
- Shipped pack content carries no internal governance citations.
- No dependency, independent retrieval/network capability, or new public
  primitive is added.

## Construction tests

**Integration tests:** build the changed packs and exercise seeded RFC and
architecture prompts through the real installed skills/agent. Assert zero RFC
filesystem writes for cheaper routes, exact RFC-mode findings, Stage-0 stop,
and architecture-review YAGNI findings while legacy modes remain selectable.

**Manual verification:** run one warranted RFC from checkpoint through Draft,
one skipped/reused RFC request, one Stage-0-final architecture choice, and one
overbuilt design review; record route, files touched, verdict, and retained
gates.

## Design (LLD)

### Component / module decomposition

- `new-rfc/SKILL.md` owns artifact choice before ordinal/write. Traces to AC1.
- `adversarial-reviewer.md` owns RFC-specific cold critique while preserving
  its existing modes. Traces to AC2 and AC5.
- `architect-design/SKILL.md` plus `design-doc-rubric.md` own author reuse/stop;
  `architect-review/SKILL.md` plus `rubric-design-doc.md` own independent YAGNI
  critique. Traces to AC3–AC4.

### State & control flow

`request → pre-write artifact checkpoint → skip/reuse/route OR existing RFC
authoring lifecycle`. Architecture follows `real choice → reuse/Stage 0 → full
design only if needed → architect-review`. Neither path enters shaping review
unless it materially changes a shaped artifact through that artifact's owner.
Traces to AC1 and AC5.

### Failure, edge cases & resilience

An ambiguous consequential direction remains at the existing research/human
checkpoint; an adequate existing artifact prevents a new file. Review never
removes safeguards for brevity and reports ignored capability or unsupported
complexity as findings rather than silently rewriting the artifact. Traces to
AC1–AC4.

### Dependencies & integration

Core supplies canonical guidance and the adversarial agent. Governance Extras
and Architect remain independently installable; their skills consume their own
local delta and do not reach into another pack's source. Traces to AC5–AC7.

## Tasks

### T1: `new-rfc` chooses the cheapest valid artifact before ordinal or filesystem work

**Depends on:** none

**Touches:** `packs/governance-extras/.apm/skills/new-rfc/**, packs/governance-extras/tests/skills/new-rfc/**`

**Tests:**
- `stub: true` —
  `packs/governance-extras/tests/skills/new-rfc/test_prewrite_artifact_choice.py`
  (`STUB: AC1`).
- The PLAN stub pins one representative no-effect contract seam; the complete
  cheaper-route matrix and any callable filesystem fingerprint are EXECUTE
  construction obligations.
- TDD/goal-based: skip, reuse/amend/reference, ADR/spec/PR/issue/design/trial,
  and warranted-RFC contract fixtures assert checkpoint order and an explicit
  no-effect return before ordinal, directory, index, or body work (AC1). If the
  implementation exposes a callable seam, an integration fixture additionally
  fingerprints the temporary RFC tree before and after every cheaper route.
- Goal-based: the warranted path retains every existing authoring and review
  gate after the reorder.
- TDD/goal-based: RFC target, index, and companion-note writes stay within the
  resolved RFC owner root and refuse unsafe, link-like, identity-changing, or
  out-of-root targets before mutation (AC1).
- Goal-based: claim fixtures delete an unnecessary RFC assertion, ground a
  necessary cross-document fact with one bounded target check, and mark an
  ungrounded necessary claim as an assumption/discovery predicate (AC1).
- Goal-based/manual QA: direct RFC requests reach `new-rfc` without creating a
  synthetic intent or second owner hop (AC5).
- Goal-based: `new-rfc` frontmatter, tools, `metadata.boundaries`, and adapter
  projection retain the minimum static authority needed by the eventual
  warranted-RFC path (AC6); AC1 fixtures separately govern when effects occur.

**Approach:**
- Move artifact-choice questions ahead of ordinal resolution and target setup.
- Reuse the current checkpoint prose and ordinal script; add no second router.

**Done when:** no cheaper-route fixture allocates an ordinal or changes the
repository, and a warranted RFC still completes the existing Draft flow.

### T2: `adversarial-reviewer` has an isolated RFC context and YAGNI rubric

**Depends on:** none

**Touches:** `packs/core/.apm/agents/adversarial-reviewer.md, packs/core/tests/pack/test_review_depth_and_verdict_contract.py`

**Tests:**
- `no stub (goal-based/manual QA)` —
  `packs/core/tests/pack/test_review_depth_and_verdict_contract.py` and one
  recorded fresh RFC-review fixture.
- Goal-based construction tests pin RFC mode/context/checks, exact tools and
  boundary metadata, findings-only output, and preservation of existing modes
  (AC2, AC5, AC6).
- Goal-based: reviewer fixtures remove unnecessary claims without requesting
  supporting prose and flag only unsupported claims necessary to the RFC
  decision (AC2).
- Visual/manual QA: a fresh reviewer finds every seeded RFC YAGNI defect and
  does not demand a code diff or work-loop state.

**Approach:**
- Add one explicit context-loading and rubric branch; share only the existing
  report contract and universal ladder reference.

**Done when:** RFC fixtures converge clean after defects are removed and all
  prior review-mode construction tests remain green.

### T3: Architecture author and reviewer stop at justified surface

**Depends on:** none

**Touches:** `packs/architect/.apm/skills/architect-design/**, packs/architect/.apm/skills/architect-review/**, packs/architect/tests/skills/{architect-design,architect-review}/**`

**Tests:**
- `no stub (goal-based/manual QA)` —
  `packs/architect/tests/skills/architect-design/test_yagni_contract.py`,
  `packs/architect/tests/skills/architect-review/test_yagni_contract.py`, and
  recorded author/reviewer fixtures.
- Goal-based/eval: author fixtures prove prior-design/capability reuse, Stage-0
  finality, and full-document component justification (AC3).
- Goal-based/eval: reviewer fixtures seed every AC4 defect and prove other
  artifact rubrics and well-architected modes remain unchanged.
- Goal-based/eval: author/reviewer fixtures minimize architecture claim surface,
  perform one bounded check for a necessary named-target assertion, and use an
  assumption/discovery predicate when it remains ungrounded (AC3–AC4).
- Goal-based/eval: architecture saves stay within the resolved configured
  output root and refuse unsafe, link-like, identity-changing, or out-of-root
  targets before mutation (AC1, AC3).
- Goal-based/manual QA: direct architecture requests reach `architect-design`
  without creating a synthetic intent or dispatching shaping review (AC5).
- Goal-based: both changed skills declare the minimum tools and
  `metadata.boundaries`, and every adapter projection preserves the existing
  effective authority (AC6).

**Approach:**
- Extend the existing author gate and design-doc rubric; change the template
  only if a fixture demonstrates it is necessary.
- Put independent YAGNI findings in the existing design-doc review route.

**Done when:** adequate concept/reuse cases stop without a full design and every
unjustified design case receives the expected finding.

### T4: Existing guides, evals, versions, and projections close the technical-shaping slice

**Depends on:** T1, T2, T3

**Touches:** `guides/governance-extras/how-to/new-rfc.md, guides/architect/how-to/{shape-an-architecture-concept,review-an-architecture-artifact}.md, packs/{core,governance-extras,architect}/{pack.toml,.claude-plugin/plugin.json}, docs/product/changelog.md`

**Tests:**
- `no stub (goal-based/manual QA)` — aggregate guide, eval, pack, catalogue,
  version, projection, and installed-profile evidence.
- Goal-based: behavior evals, pack tests, guide lint/index/link/site checks,
  catalogue lint/verify, version parity, marketplace, and projection/build
  checks cover AC6–AC7.
- Visual/manual QA: built skill and agent runs record the four representative
  stop/review outcomes.
- Goal-based/manual QA: when RFC or architecture work materially revises an
  intent, delivery brief, or spec, only that artifact's lifecycle owner invokes
  its shaping-review mode; unchanged and directly started technical artifacts
  do not create a shaping-review hop (AC5).

**Approach:**
- Reconcile stale contradictory statements in an edited guide rather than add
  caveats around them.
- Patch-bump only packs whose shipped content changes and regenerate owned
  projections.

**Done when:** AC1–AC7 pass and no changed guide or eval teaches artifact
creation before reuse/necessity.

## Rollout

The three pack changes are independently reversible but ship only after their
cross-pack tests pass. The pre-write reorder can roll back without migrating
artifacts; reviewer/architecture prose can roll back with its pack version.
Existing RFCs, designs, and adapter contracts require no migration.

## Risks

- A checkpoint placed after ordinal resolution would satisfy prose but not the
  zero-write behavior; fixtures pin the order.
- An RFC mode can accidentally inherit code/spec assumptions; context-specific
  negative fixtures prohibit them.
- Duplicating YAGNI prose across author/reviewer/template creates drift; keep
  one local author delta and one local review rubric.
- Editing `design-reviewer` would widen the accepted slice; construction tests
  and task touches exclude it.

## Changelog

- 2026-08-27: initial plan from accepted RFC-0099; declined a new reviewer,
  template-first enforcement, adapter change, and `design-reviewer` expansion.
