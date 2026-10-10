# Plan: Architect output reaches shaping and specs

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/AGENTS.md` (version bump, self-host, eval
  harness, no internal citations); `packs/product-engineering/.apm/skills/frame-domain/SKILL.md`
  § Detect-and-degrade (the roster-check primitive reused here);
  `packs/product-engineering/.apm/skills/discovery-loop/SKILL.md` (the
  "if installed" tech lens); `guides/_shared/reference/catalogue-authoring-standards.md`
  § 11 (`[[pack.integrations]]`); `packs/product-engineering/tests/pack/test_frame_intent_experience_handoff.py`
  (the prose-contract test shape). Non-structural: prose, manifest, eval, and
  test edits only.

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

Work pack by pack, test first: write each pack's contract test, see it red,
then edit the skill prose until it is green. Architect first (gaps 1, 2, 5's
producer side), then product-engineering (gaps 3, 4, the gap 2 wiring, and the
silence proof), then Core (gap 5). Releases and projections last. The riskiest
part is the silence rule: every offer must carry the same clause, and the
mutation proves the test catches a missing one.

## Constraints

- `core` must not depend on or name `architect`; its new step uses only the
  semantic roles it already owns.
- `tools/lint-pack-test-boundary.py`: each pack's tests read only that pack, so
  changelog checks are goal-based commands.
- `tools/lint-knowledge-surface-parity.py` pins area names and questions in
  `frame-intent/references/knowledge-surfaces.md`; edit only the lens paragraph.
- Shipped pack content carries no internal-governance citations.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none; prose has no runtime. AC-0015 proves projection parity.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current architecture — `packs/architect/DESIGN.md` | T1 | AC-0002, AC-0004 tests | Sections read whole |
| Decision rationale — spec § Decisions; `packs/architect/DESIGN.md` § Downstream: core | T1 | Section present; AC-0004 test | spec-status lint clean |
| User promise — three pack READMEs | T1, T2, T3 | README assertions | Each README names its behaviour |
| Release history — `docs/product/changelog.md` | T4 | Versions match; entries placed | Three entries with Highlights |

## Design (LLD)

### Design decisions

Traces to: AC-0001 – AC-0012.

Owned by: T1, T2, T3.

- Detection is the available-skills roster check. No filesystem probe, no
  install hint, no dependency.
- One silent clause, verbatim at every product-engineering offer, so one test
  pins them all: "If it is not in the roster, continue with this skill's own
  behaviour and say nothing about it: no mention, no note, and no error."
- Reading an existing current-architecture artifact is not an architect offer.
  Any pack can produce one, so `explore-options` and the artifact-reuse halves
  of the other skills need no roster check.
- `[[pack.integrations]]` records each optional seam declaratively; `catalogue
  verify` checks the provider refs exist in the target pack.

### Behavior & rules

Owned by: T1, T2, T3.

**architect-design step 2** — a new paragraph after "Cite only the sources
relevant to the design.":

> **Check the reference architecture.** Look for the repository's reference
> architecture — its golden path of stack, chosen patterns, and constraints,
> often a `reference.md` at the resolved `current-architecture` destination or
> a source mapped from `AGENTS.md`. State what you found in the concept,
> including "none found". When none is reachable, ground the design against the
> stack you can observe, lower the confidence of stack assumptions, and offer to
> establish one: check your available-skills roster for `adapt-to-project` (an
> existing codebase) or `init-project` (a new project) and offer to hand off to
> the one that fits, since it owns harvesting, destination resolution, and
> confirmation. When neither is available, state the absence in the concept and
> continue. Never draft or write a reference architecture inside this skill.

**architect-design step 8** — appended after the role sentence: "A saved
design is future-state. After the change ships, reconcile it into
`current-architecture` — a closeout workflow may offer this — rather than
treating it as a description of the running system."

**DESIGN.md** — § Reference architecture's second paragraph is replaced to say
it routes to `adapt-to-project` or `init-project` when available and otherwise
states the absence. § Downstream: core is replaced with exactly two routes:
delivery-contract design context from `decompose-intent` (which `new-spec`
reads as attributed context), and reconciliation into `current-architecture`,
which `work-loop` and `new-spec` read when an `AGENTS.md` maps that source. It
says a `workspace.toml` `needs` entry only orders work and carries no content,
and that Core reads only mapped architecture sources so a future-state design
never becomes a second architecture authority.

**frame-domain** — the section heading becomes "The brownfield half —
`decision-archaeology` + current-system extraction", the schema comment and
producer step 3 say "current-system extraction", and the brownfield bullet
"Architecture extraction" becomes:

> **Current-system extraction.** First reuse a reachable current-architecture
> artifact (a resolved `current-architecture` source, or one mapped from
> `AGENTS.md`) as the starting model, attributed and checked against the code.
> When none exists, check your available-skills roster for `architect-assess`
> and offer it to produce the current-state model; use its result as the
> extraction. If it is not in the roster, continue with this skill's own
> behaviour and say nothing about it: no mention, no note, and no error.
> Without either, extract the domain model, events, and binding seams from code
> and docs yourself.

Detect-and-degrade gains a final paragraph of its own, with no "roster" in it:
"`architect-assess` is an offer, not a grounding dependency: its absence is
never named in *Residual assumptions*."

**frame-intent** — a new `## System-shape questions` section after
§ Situational product-to-experience handoff:

> Framing sometimes hits a question about system shape: how to integrate, what
> stack is mandated, which reference architecture applies, or why a past design
> went the way it did. Do not answer it in the intent. Record it in
> `Assumptions` as an open design question and keep Outcome and Opportunity
> solution-independent. Then check your available-skills roster for
> `architect-design` and offer it at the scope the question needs:
> `application/system` for a whole system, `subsystem` for one part, or
> `architecture change` for a change to what already runs. If it is not in the
> roster, continue with this skill's own behaviour and say nothing about it: no
> mention, no note, and no error.

`knowledge-surfaces.md`: "hand it to the architect lens." becomes "park it as
an open design question, as the skill's § System-shape questions describes."

**de-risk-intent** — appended to step 2:

> When the riskiest assumption is feasibility — can this be built on what
> exists — ground it against a reachable current-architecture artifact and cite
> it in the test target. When no such artifact exists, check your
> available-skills roster for `architect-assess` and offer it as the cheap
> probe. If it is not in the roster, continue with this skill's own behaviour
> and say nothing about it: no mention, no note, and no error.

**explore-options** — a candidate slot gains `feasibility: <optional — fit
against a reachable current-architecture artifact, cited; omit when none>`,
and step 1 gains one bullet saying so.

**diverge-solutions** — step 3's per-option list gains: "and, when a
current-architecture artifact is reachable, an optional feasibility note citing
it". Step 5's Options entry fields gain the same optional Feasibility
note after Trade-offs.

**decompose-intent** — a new paragraph at the end of step 1, so no step is
renumbered:

> When a reachable current-architecture or architecture-design artifact names
> subsystem boundaries, check each child against them: a child that crosses a
> boundary names the contract it depends on. Boundaries inform dependencies;
> the cut stays by shippability, never by component. When a capability-level
> intent needs a structural decomposition before its children can be cut,
> check your available-skills roster for `architect-design` and offer it at
> `subsystem` or `application/system` scope; its decomposition rubric decides
> how many design documents result. If it is not in the roster, continue with
> this skill's own behaviour and say nothing about it: no mention, no note, and
> no error.

Step 3, "Project the confirmed delivery unit", gains: "When a resolved `architecture-design` artifact covers this
feature, carry its locator in the delivery contract's design context, or in a
delivery brief's design artifacts, so the spec stage reads it as attributed
context."

**map-capabilities** — appended to step 4:

> When the build sequence is set, check your available-skills roster for
> `architect-design` and offer it at `application/system` scope for the Build
> capabilities. If it is not in the roster, continue with this skill's own
> behaviour and say nothing about it: no mention, no note, and no error.

**close-work** — appended to step 4:

> When the closed work's spec, plan, or delivery contract names a future-state
> `architecture-design` artifact that this work implemented, offer to reconcile
> it into the resolved `current-architecture` surface: record what was built in
> the current-architecture source and mark the design implemented or
> superseded. Apply it only under step 7's confirmation, and never overwrite a
> current-architecture source without per-file acceptance. When no
> `current-architecture` destination resolves, report that and leave the design
> unchanged.

**Integrations.** `product-engineering/pack.toml` gains:

- `architect-design-offer` — `kind = "handoff"`, consumers `frame-intent`,
  `decompose-intent`, `map-capabilities`; providers `skill:architect-design`.
- `architect-current-state` — `kind = "handoff"`, consumers `frame-domain`,
  `de-risk-intent`; providers `skill:architect-assess`.

Both fallbacks: "If the skill is not installed, the consuming skill continues
with its own behaviour and says nothing about it: no mention, no note, and no
error."

`architect/pack.toml` gains `core-reference-architecture-handoff` per AC-0003,
fallback: "If neither skill is available, architect-design states the absence
of a reference architecture in the concept and continues."

## Tasks

### T1: Architect — reference architecture, future-state note, DESIGN.md

**Depends on:** none

**Touches:** packs/architect/.apm/skills/architect-design/SKILL.md, packs/architect/DESIGN.md, packs/architect/pack.toml, packs/architect/README.md, packs/architect/.apm/skills/architect-design/evals/evals.json, packs/architect/tests/skills/architect-design/test_shaping_reach.py

**Tests:**
- `test_shaping_reach.py` asserts AC-0001's phrases in step 2, AC-0005's step 8 sentence, AC-0002 and AC-0004 on `DESIGN.md` sections, AC-0003's integration via `tomllib`, the AC-0014 architect README phrase, and eval id `no-reference-architecture`.
- Red first: the test fails before the prose exists.

**Done when:** `python3 -m pytest packs/architect/tests -q` passes.

### T2: Product-engineering — offers, silence, design context

**Depends on:** none

**Touches:** packs/product-engineering/.apm/skills/frame-domain/SKILL.md, packs/product-engineering/.apm/skills/frame-intent/SKILL.md, packs/product-engineering/.apm/skills/frame-intent/references/knowledge-surfaces.md, packs/product-engineering/.apm/skills/de-risk-intent/SKILL.md, packs/product-engineering/.apm/skills/explore-options/SKILL.md, packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md, packs/product-engineering/.apm/skills/decompose-intent/SKILL.md, packs/product-engineering/.apm/skills/map-capabilities/SKILL.md, packs/product-engineering/pack.toml, packs/product-engineering/README.md, packs/product-engineering/.apm/skills/frame-domain/evals/evals.json, packs/product-engineering/.apm/skills/frame-intent/evals/evals.json, packs/product-engineering/.apm/skills/de-risk-intent/evals/evals.json, packs/product-engineering/.apm/skills/decompose-intent/evals/evals.json, packs/product-engineering/tests/pack/test_architect_optional_offers.py

**Tests:**
- `test_architect_optional_offers.py` asserts AC-0006 – AC-0010 phrases per skill, and AC-0011: every paragraph that names `architect-design` or `architect-assess` with "roster" also carries the silent clause; the forbidden phrases are absent under `.apm/`; the manifest has no architect dependency and two architect integrations with "say nothing about it".
- Mutation: a helper-level test removes the clause from one flattened paragraph and asserts the checker reports it (AC-0011).
- The same file asserts the AC-0013 eval ids and "Does not mention" assertions, and the AC-0014 product-engineering README phrases.
- `python3 tools/lint-knowledge-surface-parity.py` exits 0.

**Done when:** `python3 -m pytest packs/product-engineering/tests -q` passes and the parity lint exits 0.

### T3: Core — reconcile an implemented design in close-work

**Depends on:** none

**Touches:** packs/core/.apm/skills/close-work/SKILL.md, packs/core/.apm/skills/close-work/evals/evals.json, packs/core/README.md, packs/core/tests/skills/close-work/test_design_reconciliation.py

**Tests:**
- `test_design_reconciliation.py` asserts AC-0012's step 4 phrases, the regex absence over every line of `close-work/SKILL.md`, `close-work/evals/evals.json`, and `packs/core/README.md`, eval id `reconcile-implemented-design`, and the AC-0014 Core README phrase.

**Done when:** `python3 -m pytest packs/core/tests/skills/close-work -q` passes.

### T4: Releases and projections

**Depends on:** T1, T2, T3

**Touches:** packs/core/pack.toml, packs/architect/pack.toml, packs/product-engineering/pack.toml, packs/core/.claude-plugin/plugin.json, packs/architect/.claude-plugin/plugin.json, packs/product-engineering/.claude-plugin/plugin.json, docs/product/changelog.md, self-host projection paths (`.claude/`, `.agents/`, and other generated adapter copies)

**Tests:**
- `grep` each `pack.toml` and `plugin.json` for the AC-0014 version.
- `grep -n '^## \[' docs/product/changelog.md | head -5` lists the three new entries above older releases, each followed by `### Highlights`.
- `make lint-ruff lint-mypy` passes; `agentbundle catalogue lint --root . --deep` passes.
- After commit: `agentbundle catalogue verify --root .` passes and `make build-self` leaves `git status --porcelain` empty (AC-0015).

**Done when:** every command above prints its expected result.

## Rollout

Guidance-only patch releases of three packs. Rollback is a revert of the PR.

## Risks

- A host that omits an installed skill from its roster silently skips the
  offer; that is the safe direction.
- `close-work` and `frame-intent` are pinned by existing phrase tests; their
  suites run in GATES.

## Changelog
- 2026-10-10: spec approved by eugenelim
- 2026-10-10: plan approved by eugenelim
