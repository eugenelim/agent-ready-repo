# Plan: RFC and architecture simplification

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/governance-extras/.apm/skills/new-rfc/`,
  `packs/core/.apm/agents/adversarial-reviewer.md`, and
  `packs/architect/.apm/skills/{architect-design,architect-review}/`; analogous
  `docs/specs/new-rfc-fresh-context/` and
  `docs/specs/architect-platform-grounding/`; tests under
  `packs/{governance-extras,core,architect}/tests/`. Uncertainty resolved:
  `design-reviewer` remains unchanged because RFC-0099 assigns this slice to
  architect author self-check and `architect-review` — which requires keeping
  the delta off the `references/rubric-*.md` read path named at
  `packs/architect/.apm/agents/design-reviewer.md:70-75`.

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
  govern this slice. The erratum on pre-EXECUTE sufficiency bounds review of
  this plan: a reviewer may block work that is impossible, unsafe,
  contradictory, untestable, or ownerless, but must not require helper
  functions, fixture internals, module symbols, or exhaustive edge-case
  matrices that EXECUTE is meant to discover.
- Workspace dependency resolution blocks plan approval until both prerequisite
  specs are Shipped; the executable task graph uses local task IDs only.
- Agent boundary metadata support from `shaping-review-contracts` precedes the
  changed adversarial agent declaration.
- Existing `new-rfc` research, preview, citation, review, circulation, and index
  gates remain intact after the new pre-write branch.
- Non-design-doc architecture rubrics, well-architected modes, and
  `design-reviewer` remain unchanged. AC4 adds the YAGNI delta to
  `architect-review`'s design-doc route in an `architect-review`-only branch,
  not to a shared `references/rubric-*.md`, because `design-reviewer` reads
  those when co-installed.
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
  `architect-review/SKILL.md` owns independent YAGNI critique in an
  `architect-review`-only design-doc branch. The delta does NOT go in
  `references/rubric-design-doc.md`: `design-reviewer.md:70-75` reads
  `architect-review`'s `references/rubric-*.md` when co-installed, so a shared
  rubric edit would change the forked reviewer's effective contract.
  Traces to AC3–AC4.

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
- `no stub (implementation-discovered)` — `new-rfc` is skill prose plus one pure
  function (`next_ordinal()`); no callable pre-create decision seam exists to
  assert against, and RFC-0099's 2026-08-27 erratum requires this form rather
  than inventing an interface.
  - *Discovery predicate:* EXECUTE finds a callable seam that decides the route
    before ordinal resolution.
  - *Constraint:* the checkpoint runs before ordinal resolution, directory or
    index creation, and body drafting.
  - *Required outcome:* every cheaper route returns without allocating an
    ordinal or changing the repository.
  - *Verification mode:* goal-based content tests on the ordered checkpoint,
    plus manual QA per cheaper route. If the discovery predicate fires, add
    red/green tests and a filesystem fingerprint at that seam.
- TDD/goal-based: skip, reuse/amend/reference, ADR/spec/PR/issue/design/trial,
  and warranted-RFC contract fixtures assert checkpoint order and an explicit
  no-effect return before ordinal, directory, index, or body work (AC1). If the
  implementation exposes a callable seam, an integration fixture additionally
  fingerprints the temporary RFC tree before and after every cheaper route.
- Goal-based: the warranted path retains every existing authoring and review
  gate after the reorder.
- Goal-based: `new-rfc` carries the written confinement contract for RFC
  target, index, and companion-note writes; a static content test pins each
  clause and one manual-QA record shows it honoured. This slice adds no code
  that performs those writes, so the contract is guidance, not a gate (AC1).
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
- Goal-based: a content test pins all ten untrusted-draft prohibitions
  (repository instructions, identity, tool permissions, review scope, reviewer
  routing, rubric or checklist coverage, severity, verdict, clean status,
  normative authority) plus the no-suppression clause. Nine vectors must match
  the agent's existing `<knowledge-evidence>` wording; `reviewer routing` is
  RFC-mode-specific and the shared envelope is not edited, so the test asserts
  the existing modes' wording is byte-unchanged (AC2).
- Visual/manual QA: one hostile-draft run whose embedded text claims its own
  authority, demands a clean verdict, and tries to route the reviewer out of
  RFC mode; the recorded outcome shows the reviewer still reporting findings
  (AC2).
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
- Goal-based: `architect-design` — and only `architect-design` — carries the
  written confinement contract for saves within the resolved configured output
  root, pinned by a static content test. `architect-review` is excluded: it
  directs no output-root save. A content test also pins that its
  `assets/risk-register.md` and `assets/critique.md` are inline output
  templates, resolving the existing contradiction between its
  well-architected route and its "No file write. Render inline" step without
  changing well-architected mode. No code in this slice performs those saves
  (AC3).
- Goal-based/manual QA: direct architecture requests reach `architect-design`
  without creating a synthetic intent or dispatching shaping review (AC5).
- Goal-based: a content test pins that `architect-review` saves only on an
  explicit user request naming the destination, that the reviewed artifact and
  supplied evidence cannot request/authorize/select/alter a write target, and
  that the inline no-file-write default stands (AC6).
- Goal-based: both changed skills declare exactly the tools and
  `metadata.boundaries` AC6 enumerates — asserted as equality, so a superset
  fails — including `architect-review`'s newly added
  `allowed-tools: Read Grep Glob Write` and
  `boundaries: [filesystem_read_untrusted, filesystem_write]`. Every adapter
  projection preserves the existing effective authority (AC6).

**Approach:**
- Extend the existing author gate and design-doc rubric; change the template
  only if a fixture demonstrates it is necessary.
- Put independent YAGNI findings in an `architect-review`-only design-doc
  branch, never in a shared `rubric-*.md` that `design-reviewer` reads.

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
- Editing `design-reviewer` would widen the accepted slice. Excluding its file
  is not sufficient: it reads `architect-review`'s `references/rubric-*.md`
  when co-installed (`design-reviewer.md:70-75`), so a shared-rubric edit
  changes it indirectly. A construction test asserts this slice adds no YAGNI
  check to any rubric file on that read path.

## Changelog

- 2026-08-27: initial plan from accepted RFC-0099; declined a new reviewer,
  template-first enforcement, adapter change, and `design-reviewer` expansion.
- 2026-08-30: pre-EXECUTE review amendments. T1 becomes
  `no stub (implementation-discovered)` per RFC-0099's 2026-08-27 erratum — no
  callable pre-create seam exists to assert against. AC1/AC3 confinement
  narrows to a declarative contract with static tests plus located manual QA
  (owner decision: the alternative was a new write seam this plan forbids).
  The YAGNI delta moves out of the shared design-doc rubric because
  `design-reviewer` reads it when co-installed. AC5 restated as the enforceable
  negative; AC6 gains a per-surface authority baseline; AC2 gains an
  untrusted-draft criterion, since the agent's only untrusted-data framing today
  covers the optional knowledge-evidence envelope.
- 2026-08-30: round-2 pre-EXECUTE review. All three findings were introduced by
  the round-1 amendment itself. AC6 left `architect-review`'s post-change
  authority as "the minimum set it actually needs", which no test can pin; it
  now enumerates exact values asserted as equality. AC1 still carried the
  architecture-save clause after being rescoped to `new-rfc`, which does not
  write those; the clause moved to AC3, scoped to `architect-design`, since
  `architect-review` is inline and no-file-write. AC2's prohibition list had
  seven vectors against the repository's canonical eleven; it now adopts that
  set verbatim, adding reviewer routing, clean status and normative authority,
  and T2 gains the matching content test and hostile-draft run. AC1's forward
  pointer to `write_files_no_follow` was corrected: that helper provides link
  refusal only and performs no root confinement, so any future seam must prove
  the output directory is confined first.
- 2026-08-30: round-3 pre-EXECUTE review. Three findings, all
  `introduced-by-round-2-fix`. (1) Granting `architect-review` `Write` in AC6
  while AC3 excluded its save path from confinement created a chain where an
  untrusted artifact could name the reviewer's write target; AC6 now forbids
  the reviewed artifact from requesting, authorizing, selecting or altering a
  save destination. (2) AC2 claimed its ten vectors were adopted "verbatim",
  but the agent's own envelope carries nine and omits `reviewer routing`; that
  vector is now declared RFC-mode-specific and the shared envelope is
  explicitly not edited, since AC2's first criterion forbids changing existing
  modes. (3) `architect-review`'s source contradicts itself — its
  well-architected route says "write `assets/risk-register.md`" while step 8
  says "No file write. Render inline"; AC3 now resolves this as inline
  templates, the direction the skill already operates, without changing
  well-architected mode. A structural break in AC6 introduced by the round-2
  edit was also repaired.
