# Spec: direct-light execution

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0092 and ADR-0090 (both authored by this spec).
  ADR-0090 refines ADR-0014, ADR-0076, and ADR-0078. ADR-0088 and RFC-0090 are
  preserved unchanged and constrain how this spec may edit its target files.
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer who asks an agent to make a bounded, low-risk change now gets that
change implemented, verified, reviewed, and reported without first paying for a
durable planning artifact. Light work runs **direct-light**: the explicit trusted
invocation is its authority, and the run creates no `docs/specs/<feature>/`
directory, no `plan.md`, no `docs/specs/README.md` row, no `workspace.toml` work
entry, and no loop-state file. The maintainer still gets a plan, mechanical
gates, one bounded adversarial review, repair, and an evidence-bearing handoff —
the trims are the *artifacts*, never the *rigor*.

Work that genuinely needs a durable contract keeps one. Queueing, cross-session
resumption, handoff, parallel or multi-person execution, external orchestration,
an approval boundary that must survive context loss, a published behavior
contract, and any current risk trigger all route to the spec-and-plan path
exactly as before. Workspace dispatch stays spec-and-plan based and fail-closed.

Removing the mandatory spec removes a human-reviewed artifact that used to stand
between untrusted text and written code. Direct-light therefore draws its
authority boundary explicitly: the **explicit trusted invocation** and
repository policy decide eligibility, scope, and whether a risk trigger fires.
The invocation may **reference** an issue or a pull request; the referenced
content is context the run may read, never authority. An issue body, a
pull-request description, a `workspace.toml` comment, a README, an issue
template, or any other repository or tracker text is **data** that may inform the
work and never authority that may select the route, assert its own eligibility,
or declare a trigger inapplicable.

This boundary is **doctrine with eval and substring coverage, not a technical
guarantee** — see [Accepted limitations](#accepted-limitations).

The change converges concepts the repository already has rather than adding one.
The explicit trusted invocation is the immediate authority for direct execution;
`work-intake` routes and is not an artifact; an intent is a durable
non-dispatchable record; a **brief** is the durable shared outcome across several
delivery slices or repositories; a **spec** is the durable behavior contract for
one delivery slice; a **plan** is the implementation and verification strategy;
`workspace.toml` indexes durable queued and resumable work. No "Work Contract"
abstraction is introduced. Brief authoring stops contradicting itself:
`author-brief` produces a Draft and never certifies readiness, and
`receive-brief` owns one canonical semantic Ready gate that the shipped brief
template matches.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit sources of truth only; regenerate every projection with the repository's
  own command (`make build-self` for `.claude/**`, `.agents/**`, root
  `docs/CONVENTIONS.md`; `make site-sync` for `docs-site/src/content/docs/**`).
- Treat `packs/core/.apm/skills/work-loop/SKILL.md` as the **sole** documented
  home of the risk-trigger block, per ADR-0088. Other surfaces name the skill.
- Keep the fenced `risk-triggers:start`…`risk-triggers:end` span byte-identical
  across its three live homes — the source and its two projections
  (`tools/lint-agents-md.py` §10g) — by editing the source and regenerating.
- Preserve every existing transactional guarantee on the intent, brief, spec,
  defect, and tracker-refresh routes.
- State each governing-artifact refinement in the new RFC and ADR rather than
  editing accepted RFC or ADR bodies.
- Carry a positive control alongside every completion-proving grep.

### Ask first

- Adding, removing, or renaming a `workspace.toml` collection, kind, or schema
  field.
- Changing the normalized intake envelope's `contract_version` value.
- Registering this spec as a `workspace.toml` work entry.
- Any decomposition into more than one pull request.
- Any change to the risk-trigger block's own wording (as opposed to the stale
  comment inside its opening marker, which AC26 corrects).

### Never do

- Introduce a `work-contract.md` file, a Work Contract schema, directory,
  registry, lifecycle, `workspace.toml` kind, or public workflow term.
- Let a direct-light run write `docs/specs/**`, `workspace.toml`, or any
  loop-state file.
- Reintroduce a risk-trigger block copy into root `AGENTS.md`,
  `packs/core/seeds/AGENTS.md`, or `docs/CONVENTIONS.md` — ADR-0088 retired those
  homes and `tools/test_lint_agents_md_risk_block.py::test_noncanonical_homes_fail`
  asserts their rejection.
- Let an argless start, a bare `resume`, a workspace comment, a README, an issue
  template, old chat, a branch name, or surrounding prose authorize a
  direct-light run or supply its scope.
- Hand-edit a generated projection.
- Reference a repository-only RFC, ADR, spec, or acceptance-criterion identifier
  from content shipped to adopters.
- Weaken spec quality where a spec is warranted.
- Combine this change with historical spec pruning, workspace sharding, external
  control-plane implementation, or a general context-resolution system.

## Testing Strategy

- **Direct-light non-persistence, intake routing, authority boundary, and brief
  gates: TDD.** These are compressible invariants over deterministic seams
  (`intake_router.py`, `intake_transaction.py`) and over skill-body text
  contracts that `packs/core/tests/**` already asserts by substring and
  structure. Every new guard carries a mutation proof: reverting the guard must
  turn a specific named test red.
- **Decision-seam non-persistence: committed harness (goal-based,
  executable).** `route_intake()` is a pure function, so a harness can prove the
  *code path* writes nothing — it returns the direct `Route`, invokes no
  transaction helper, and leaves a fixture repository's recursive
  path-to-digest map identical. It cannot prove that an agent following prose
  writes nothing, and does not claim to (AC31).
- **End-to-end non-persistence: recorded manual QA.** The actual writer is an
  agent following `SKILL.md`, which no test can drive deterministically. One real
  direct-light run of the shipped skill executes in a throwaway fixture
  repository and the observed evidence is recorded: `workspace.toml` SHA-256
  unchanged, no `docs/specs/**` path, no `state.json`, no `engine-state.json`
  (AC34). This is the `work-loop`'s manual-QA mode, chosen because the mechanism
  for an executable end-to-end check does not exist.
- **Eligibility and durability predicates: TDD as a decision table.** Each
  predicate in AC4 and AC5 gets its own positive and negative case; a group
  assertion that passes when one predicate is wrong is not acceptable.
- **Terminology and stale-claim absence: goal-based check with a positive
  control.** A repository-wide search proves no Work Contract artifact, schema,
  registry, lifecycle, or public term exists and that no living surface claims a
  spec carries the "how"; each search runs alongside a pattern known to match, so
  a silently-empty result cannot read as a pass.
- **Projection and release obligations: goal-based check.** `make build-self`,
  `make build-check`, and the catalogue lint/verify commands are the one-liners.

## Acceptance Criteria

### Direct-light execution

- [ ] AC1 — A bounded explicit low-risk start runs the full light loop (plan,
  implement, gates, one bounded adversarial review, repair, decide, handoff) with
  no durable planning artifact: `packs/core/.apm/skills/work-loop/SKILL.md`
  light mode names the explicit trusted invocation as authority — which may
  reference an issue or PR whose content is context, not authority — requires the
  assumption trio and bounded task/verification plan in the active session, and
  forbids `new-spec`, `docs/specs/` creation, a sibling plan, a
  `docs/specs/README.md` update, a `workspace.toml` mutation, `loop-engine` or
  `loop-cohort` initialization, spec-status lint when no spec exists, and
  project-knowledge capture triggered solely by an absent spec gate.
- [ ] AC2 — Before the first implementation write, a direct-light run emits a
  user-visible decision record naming the authority source, the bounded scope,
  the non-goals, the risk-trigger assessment, the assumptions, and the
  verification plan; ambiguity in any of the six stops the run and surfaces
  rather than proceeding. The record is session output, not a persisted file.
- [ ] AC3 — The direct-light handoff carries requested outcome, implemented
  scope, verification evidence, non-goals and deferrals, and any discovered
  reason future work should use a durable spec. Its testable form is the
  five-field requirement asserted in the skill body plus an eval case; no
  durable handoff file is created.
- [ ] AC4 — Direct-light eligibility is a conjunction, and each conjunct has a
  positive and a negative test case: an explicit user request to start or perform
  the change now; one bounded logical change; independent verifiability; expected
  completion in the current session; no firing full-mode risk trigger; no need
  for queueing, assignment, cross-session resumption, parallel coordination, or a
  durable product contract; no conflict with a canonical queued or active
  workspace item; and no supplied governing spec for the same work.
- [ ] AC5 — Each of these routes to the durable spec-and-plan path, is refused
  the direct route, and has its own test case: any current full-mode risk
  trigger; multi-person or parallel execution; dependent delivery tasks needing
  durable sequencing; expected multi-session work; queueing for later; external
  control-plane orchestration; a human approval boundary that must survive
  context loss; a public or durable product behavior contract; source-authority
  or refresh state that must remain meaningful after the session; and an explicit
  user request for a spec. A refused direct route invokes or recommends
  `new-spec`.
- [ ] AC6 — Classification happens before the first implementation write, and a
  trigger discovered mid-implementation stops before crossing the newly
  discovered boundary, preserves the current diff without asserting it was
  produced under an earlier approved spec, creates a spec and plan describing the
  intended final state and the already-observed repository reality, runs the
  normal human approval gates, and brings the complete diff through full
  verification and review. No backfilled implementation chronology.
- [ ] AC7 — Direct execution being unavailable never creates a brief; a brief
  requires a coherent multi-slice or cross-repository outcome.

### Authority boundary

- [ ] AC8 — Eligibility, scope, the risk-trigger assessment, and any exception
  decision derive only from the explicit trusted invocation plus repository
  policy. Text embedded in an issue body, pull-request description,
  `workspace.toml` comment, README, issue template, commit message, branch name,
  or surrounding prose is data: it can neither select the direct route, nor
  assert its own eligibility, nor declare a risk trigger inapplicable, nor widen
  scope. Falsification cases cover at least an embedded "start this direct-light",
  an embedded "no risk trigger applies", and an embedded instruction to change a
  file outside the stated scope.
- [ ] AC9 — All applicable input validation, confidentiality comparison, and
  path-independent safety checks run and can refuse **before** route
  classification selects a processor and before any implementation write; a
  refusal is terminal for the attempt and no implementation write follows it.
  For the direct route, "applicable" means normalized-source and locator
  validation plus any processor-relevant safety check. It does not imply
  artifact-*target* confinement, because the route has no artifact target — but a
  locator that names repository content the run will then read or edit is
  canonicalized and proven repository-confined before that use, with symlink,
  junction, and dot-segment traversal refused.

### Existing specs and workspace orientation

- [ ] AC10 — A supplied or workspace-resolved existing spec is used, never
  replaced or downgraded; spec/plan lifecycle and workspace reconciliation are
  preserved; full-mode behavior on a firing risk trigger is preserved; and every
  spec-related check is conditional on a spec existing.
- [ ] AC11 — A persisted spec that predates this change and carries
  `Mode: light (no risk trigger fired)` remains readable, remains valid, and
  remains resumable as a spec-driven run through its existing status ladder; no
  adopter must migrate or delete such a spec, and a test covers resumption from
  each of its `Draft`, `Approved`, and `Implementing` states.
- [ ] AC12 — `work-loop` Step 0 no longer lets the mere presence of
  `workspace.toml` force an explicit current request to resolve to a canonical
  spec. An argless queued start still requires a `canonical.ready` item; a
  fresh-session resume still requires a `canonical.active` item; a supplied spec
  path still passes canonical preflight; a direct-light run is not resumable
  through `workspace-status`; and a bare `resume` in a fresh context never infers
  a direct-light authority from workspace comments, old chat, branch names, or
  surrounding prose.
- [ ] AC13 — An explicit current request may enter direct light mode without
  workspace registration when no matching active, ready, or blocked canonical
  item exists; a matching or conflicting item makes the run surface the conflict
  instead of starting an untracked parallel implementation.
- [ ] AC14 — A direct-light run that cannot finish in-session fails safe: on
  discovering it needs a further session, that a second worktree is already
  changing the same files, or that gates cannot be repaired in-session, it stops,
  surfaces the situation, and escalates to the durable spec-and-plan path rather
  than leaving changes stranded with no durable record.

### Intake routing

- [ ] AC15 — `packs/core/.apm/skills/work-intake/SKILL.md` and
  `scripts/intake_router.py` carry a direct route whose observable result is no
  artifact path, no workspace membership, no transaction or rollback, and
  `work-loop` as processor, and whose repository state is unchanged until
  implementation begins; the route still validates and normalizes input and runs
  the confidentiality and path-independent safety checks of AC9.
- [ ] AC16 — The direct route is fail-closed on the combinations the router can
  observe. Workspace membership is *computed* in `Route`, not supplied, so the
  discriminant is over inputs: a direct-light signal is rejected terminally,
  before any write, unless its `action` is `start`, its `artifact` is empty, its
  `artifact_kind` is empty, and neither `named_gaps` nor `ready_brief` is set. A
  negative test matrix forces each durable artifact kind (intent, brief, spec,
  defect) through attempted direct classification by supplying that kind alongside
  the direct signal, and expects that rejection. This bounds misrouting; it does
  not make the declared signal itself trustworthy — see
  [Accepted limitations](#accepted-limitations).
- [ ] AC17 — "Materialize before register" applies only to routes that create
  durable artifacts, and transactionality is unweakened for intents, briefs,
  specs, defects, and tracker-origin refresh. Artifact routes continue to resolve
  their target through `resolve_confined_target()`.
- [ ] AC18 — `artifact: none` and `workspace membership: none` render as a valid
  direct-route result, not an error. The internal representation is fixed once and
  documented: the router carries the empty string for an absent artifact and the
  literal `none` for absent membership; `none` in output is a *rendering* literal,
  and no fixture encodes a conflicting meaning.
- [ ] AC19 — The rule that one actor plus one bounded capability always enters
  `new-spec` is replaced by the direct-light-versus-durable-work decision, and
  the intake routing table carries the six routes (direct-light, durable single
  slice, multi-slice brief, remember, cited defect, incomplete or ambiguous).

### Brief convergence

- [ ] AC20 — `author-brief` creates a Draft from incomplete multi-slice input
  when the intended multi-slice outcome is identifiable or the missing outcome is
  named as a blocking gap, provenance is recorded, and missing Ready fields are
  named; it requires neither Appetite nor a Rabbit hole to create a Draft,
  invents no missing field, never sets Ready, and never creates a brief for a
  single direct-light change.
- [ ] AC21 — `author-brief` Draft creation still proceeds only from the validated
  normalized envelope after the existing terminal confidentiality and redaction
  refusal, and still copies no raw external payload into the brief; removing the
  Appetite and Rabbit-hole preconditions weakens no containment control.
- [ ] AC22 — `receive-brief` is the single owner of one canonical Ready gate
  whose semantic fields are exactly Outcome, In scope, Non-goals, Constraints or
  appetite, Named assumptions or risks, and Durable source provenance; the Spec
  map may be mechanically present with zero slices; Success metrics,
  instrumentation, stories, and design artifacts are optional absent another
  installed workflow or explicit policy; a Ready brief with zero specs is valid
  and non-dispatchable; and only confirmed delivery slices create specs and
  plans.
- [ ] AC23 — `packs/core/seeds/docs/product/briefs/_template.md` carries an
  explicit safe source/provenance field, Outcome, Scope and Non-goals,
  Constraints/Appetite, Assumptions/Risks, and an empty-capable Spec map; marks
  Success signals, Instrumentation, User stories, and Design artifacts optional;
  claims no field mandatory that the canonical Ready gate does not require;
  duplicates no explanation `receive-brief` owns; and remains a prompt sheet
  rather than a schema or a generic wrapper for every request.
- [ ] AC24 — `new-spec` remains the explicit durable-contract authoring workflow,
  invoked for an explicit spec request, full mode or durable coordination, a
  confirmed brief slice, work needing queueing, resumption, approval persistence,
  or external orchestration, and a warranted durable published behavior contract;
  its universal claim that every one-day feature benefits from or must receive a
  persisted spec is gone, and spec quality where warranted is unchanged.

### Documentation, terminology, and stale claims

- [ ] AC25 — `docs/architecture/work-intake-and-artifact-routing.md` states the
  narrowed invariant — every workspace-dispatchable, queued, or resumable build
  item resolves to an existing durable spec and plan, while an explicit
  direct-light request is session-local, creates no workspace entry, and is
  ineligible for argless dispatch or fresh-session resumption — and carries the
  three-branch classification flow (direct light; durable single slice;
  multi-slice outcome). `workspace.toml`'s schema is unchanged.
- [ ] AC26 — No **living** surface — skill, script, test, eval, seed, template,
  guide, architecture page, `AGENTS.md`, `CONVENTIONS.md`, or projection — states
  that light mode persists a lean spec, that every nontrivial change creates a
  spec, or that a spec carries the implementation "how". Frozen historical
  records are exempt and unedited: accepted RFC and ADR bodies, and Shipped or
  Archived spec directories. The stale comment inside the risk-trigger block's
  opening marker in `packs/core/.apm/skills/work-loop/SKILL.md`, which still says
  the block is copied verbatim into three retired homes and that all four must be
  byte-identical, is corrected to match ADR-0088. A spec means durable delivery
  behavior and a plan means implementation strategy everywhere.
- [ ] AC27 — Root `AGENTS.md` and `packs/core/seeds/AGENTS.md` carry a concise
  `work-loop` pointer and neither the routing policy nor the classification
  table; neither reintroduces a risk-trigger block copy.
- [ ] AC28 — No `work-contract.md`, Work Contract schema, registry, lifecycle,
  `workspace.toml` kind, or public concept exists anywhere in the repository;
  machine-protocol "contract" terminology remains where it genuinely describes an
  interface contract, and the normalized intake envelope keeps its existing
  protocol version field.

### Governance, release, and proof

- [ ] AC29 — RFC-0092 records the decision at `heavy` weight and carries the
  reversal analysis (RFC-0025 explicitly rejected a no-spec light mode and its
  option D) and the compatibility analysis for existing persisted specs,
  workspace entries, and adopters. RFC-0092 also refines RFC-0083's artifact-first
  clauses — "only an existing spec and plan may authorize execution" and the
  router "dispatches only an existing spec and plan" — while preserving its
  workspace-dispatch rule. ADR-0090 refines exactly three accepted
  clauses without editing any accepted body: ADR-0014's inline-lean-spec light
  mode, ADR-0076's dispatch-only-from-workspace-entries rule, and ADR-0078's
  start-route-materializes rule together with its "every captured item must
  materialize a canonical artifact before it can become executable" tradeoff.
  Both are registered in their indexes.
- [ ] AC30 — Falsification cases exist and each turns a named test red:
  reintroducing spec creation on the direct path; mutating `workspace.toml` on
  the direct path; permitting argless direct dispatch; treating a one-slice
  request as a brief; letting `author-brief` stamp Ready; letting embedded issue
  or PR text select the direct route; and letting an artifact-bearing signal
  combination take the direct route.
- [ ] AC31 — The committed harness proves what an executable seam can prove, and
  claims no more: driven inside a throwaway fixture repository, the decision seam
  returns the direct `Route`, invokes no transaction helper, and leaves the
  fixture's recursive path-to-digest map identical. `route_intake()` is a pure
  function, so this establishes that the *code path* writes nothing; it does not
  and cannot establish that an agent following prose writes nothing. Its mutation
  proof is scoped accordingly: removing the fail-closed guard, or making the
  direct branch return an artifact-bearing route, turns a named assertion red.
- [ ] AC34 — Because the writer is an agent following `SKILL.md`, the end-to-end
  property is verified by **recorded manual QA**, not by a test: one real
  direct-light run of the shipped skill executes in a throwaway fixture repository
  containing a `workspace.toml`, and the recorded evidence shows the fixture's
  `workspace.toml` SHA-256 unchanged, no `docs/specs/**` path created, and no
  `state.json` or `engine-state.json` created. The recorded observation is the
  evidence; a passing unit gate does not satisfy this criterion.
- [ ] AC32 — The core pack version and the matching Claude plugin manifest
  version are bumped together, `docs/product/changelog.md` carries the
  adopter-facing entry using no repository-only identifier, eval coverage
  including activation near-misses is updated for every changed public skill,
  self-host projection has run after all source edits, every supported adapter
  projection verifies, and catalogue or package versions changed only where the
  changed source requires it.
- [ ] AC33 — `make build-check` passes; the catalogue deep lint and verify
  commands pass; the focused `work-intake`, `work-loop`, `author-brief`,
  `receive-brief`, workspace-reconciliation, pack-surface, template, link, and
  documentation suites pass; core skill evals including activation near-misses
  pass; and adversarial review reaches Clean under full mode.

## Accepted limitations

These are consequences of the design, named here so no reader mistakes doctrine
for a technical guarantee. Each was raised by an independent secure-design review
and consciously accepted rather than silently carried.

- **The direct-light signal is caller-declared.** Eligibility is a semantic
  judgement the agent makes and declares; `route_intake()` is deterministic over
  declared signals and cannot see where a signal came from. AC8's authority
  boundary is therefore doctrine with eval and substring coverage, and AC16 bounds
  only the combinations the router can observe. The worst surviving outcome is a
  prompt-influenced caller marking a change direct-light when a trigger should
  have fired, bypassing the durable path's heavier review.

  A runtime provenance token was considered and rejected as unimplementable here:
  the caller is an LLM whose context is one undifferentiated prompt stream, so any
  token it mints is exactly as injectable as the boolean it would replace. Every
  existing route (`artifact_kind`, `named_gaps`, `ready_brief`) already rests on
  the same caller-declared basis, and building a trusted-invocation primitive
  would be the general context-resolution system this change explicitly excludes.
  If a future runtime can distinguish turn provenance, that is a separate
  RFC-worthy change.

- **Light mode has no human approval gate, and this change does not remove one.**
  The two approval gates are full-mode only (`work-loop` § PLAN step 12), so the
  lean spec direct-light replaces was never itself human-approved. The remaining
  human control is pull-request review, exactly as before. This change removes an
  *artifact*, not a *control*; a landing handshake would be a new control and is
  out of scope.

- **The end-to-end no-write property is evidenced, not enforced.** AC34's recorded
  run is a one-time observation of the shipped skill, not a standing gate. A
  regression in the prose could pass every executable gate; the standing
  protection is the substring and eval coverage in AC1 and AC30.

## Assumptions

- Process: RFC-0091 is the current RFC gate; a governance-model change to a
  shipped adopter-facing workflow is RFC-qualified and carries `heavy` weight
  (source: `docs/rfc/0091-right-size-rfc-governance.md:60-67,77-81`, read
  2026-08-19).
- Process: the next free ordinals are RFC-0092 and ADR-0090 (source:
  `python3 .claude/skills/new-rfc/scripts/next-ordinal.py docs/rfc` → `0092`;
  `python3 .claude/skills/new-adr/scripts/next-ordinal.py docs/adr` → `0090`,
  run 2026-08-19).
- Process: ADR-0014 explicitly defers the mode-selection mechanism (auto-classify
  versus explicit user flag) "to the implementation spec", so this spec may fix it
  as an explicit request to start (source:
  `docs/adr/0014-rigor-scales-with-risk-work-loop-modes.md:82-84`).
- Process: three accepted clauses become false and are refined by ADR-0090 rather
  than edited — ADR-0014's "A lean spec written inline"
  (`docs/adr/0014-…md:37-43`), ADR-0076's "agents may dispatch work only from
  structured workspace entries that reference those files"
  (`docs/adr/0076-…md:16-18`), and ADR-0078's "**Start or do this:** classify
  normalized content, materialize the canonical …" start route with its
  "every captured item must materialize a canonical artifact before it can become
  executable" tradeoff (`docs/adr/0078-…md:22,66`). ADR-0078's
  *dispatchability* rule at `:121-127` is preserved: it already scopes itself to
  workspace entries, which a direct-light run never creates.
- Technical: ADR-0088 (Accepted 2026-08-19) retired the four-copy risk-trigger
  model and made the `work-loop` skill source its sole documented home; the live
  lint's marker set is the source plus its two projections, it reports drift for
  any other `.md` carrying the marker, and
  `tools/test_lint_agents_md_risk_block.py::test_noncanonical_homes_fail` asserts
  that root `AGENTS.md`, `packs/core/seeds/AGENTS.md`, and `docs/CONVENTIONS.md`
  carrying the block must fail (source: `docs/adr/0088-…md:17-21`;
  `tools/lint-agents-md.py:517-586`;
  `tools/test_lint_agents_md_risk_block.py:58-68`;
  `git grep -ln "risk-triggers:start"` shows no live non-`work-loop` home).
- Technical: root `docs/CONVENTIONS.md` is a projection of
  `packs/core/seeds/docs/CONVENTIONS.md`; source↔projection equality is
  `make build-self`'s drift gate, which is a separate rule from the
  risk-trigger-home rule above (source: `tools/lint-agents-md.py:520-521`;
  `diff -q` of the two files reports identical, 2026-08-19). Root `AGENTS.md` is
  a hand-maintained source that is deliberately not byte-identical to its seed
  (source: `AGENTS.local.md`).
- Technical: `resolve_confined_target()` exists and is the confinement helper for
  artifact routes (source:
  `packs/core/.apm/skills/work-intake/scripts/intake_transaction.py:96`).
- Technical: the core pack and its Claude plugin manifest are both at `2.9.5`
  and move together (source: `packs/core/pack.toml:3`,
  `packs/core/.claude-plugin/plugin.json:3`).
- Technical: no canonical ready, active, or blocked workspace item matches this
  work, so it starts as new durable work without a dispatch conflict (source:
  `workspace_status.py --root .` reconciliation output, 2026-08-19).
- Technical: `guides/core/explanation/why-a-brief-layer.md:36` ("the spec stays
  the *how*") is a living surface carrying the claim AC26 removes; the complete
  living-surface inventory is enumerated in `plan.md` T5 (source:
  `git grep -ln "lean inline spec\|lean spec"` and the `the *how*` search,
  2026-08-19).
- Product: the maintainer authorizes reversing RFC-0025's explicit rejection of a
  no-spec light path ("we keep a lean spec"), via the smallest new RFC plus a
  refining ADR, without rewriting accepted historical artifacts (source: user
  request 2026-08-19; the rejected option is
  `docs/rfc/0025-work-loop-light-mode-and-risk-based-escalation.md:37,77`).
