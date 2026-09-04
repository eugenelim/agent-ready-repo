# Plan: phase-policy registry and deterministic selector

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - Convention source: root [`AGENTS.md`](../../../AGENTS.md) and
    [`docs/CONVENTIONS.md`](../../../docs/CONVENTIONS.md), whose authored source
    is `packs/core/seeds/docs/CONVENTIONS.md`.
  - Analogous production implementation 1 — a module index an orchestrator
    selects from: `packs/core/.apm/skills/operational-safety/SKILL.md:148`, whose
    modules live in `references/` and are inlined into a subagent brief per its
    line 51. This is the pattern the brief says D1 extends.
  - Analogous production implementation 2 — a fenced structured record carried
    inside a work-loop reference:
    `packs/core/.apm/skills/work-loop/references/review-verdict-record.md:15`,
    read today only by tests
    (`packs/core/tests/pack/test_review_depth_and_verdict_contract.py:15`).
  - Construction path for loading a hyphenated script as a module:
    `packs/core/tests/skills/work-loop/test_loop_guards_parity.py:80-81` and
    `test_loop_cohort_schedule.py:14`.
  - Construction path for a published-tree projection test:
    `packages/agentbundle/tests/build_pipeline/test_sequential_implementer_dispatch_projection.py:26-31`.
  - **Named deviation:** no work-loop script reads `references/` today; the only
    script-read data file is `assets/state.json`
    (`packs/core/.apm/skills/work-loop/scripts/_loop_guards.py:354`). The brief
    mandates `references/`, so this selector is the first reader of that tree.
    T6 records the boundary change in `docs/architecture/pack-layout.md` rather
    than leaving it in this plan, which freezes with the spec.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit
> (or the adopter repository's equivalent document-lifecycle guidance).

## Approach

Two new files inside the existing `work-loop` skill and nothing else in that
skill: a reference carrying the registry, and a script that reads it. The
registry is prose plus one fenced JSON block, so the same file serves the
maintainer reading a module index and the selector parsing a table — the two
audiences the existing precedents split across `operational-safety/SKILL.md` and
`review-verdict-record.md`.

Order of operations is registry, then record, then resolution, then refusals,
because each step's tests need the prior artifact. Two things drive the design
and are worth stating before the tasks.

**A family's teaching text is named by a logical locator, not a path.** The
registry ships to adopters, where `packs/core/` does not exist and the same rule
lives at `.claude/skills/…` or `.agents/skills/…` instead. A raw catalogue path
would make every authoring phase refuse on a real install. The locator's
namespace (`skill:` or `seed:`) says which search order applies, and resolution
prefers the copy an acting agent would actually read.

**The totality claim is the fragile part, and it needs two independent guards.**
A registry could omit a state, or keep every state and select nothing. The first
is caught by deriving the phase domain from `loop-engine.py`; the second by
pinning the selection map's values as a literal. Either guard alone leaves a
registry that passes while delivering no policy.

Two seams are deliberately not built. Nothing is inlined into a brief and no
digest is computed over assembled text; those are D2 and D3. And
`work-loop/SKILL.md` is not edited, so this slice does not touch the
`Conditional-reference routing` table slice U1 changed.

## Constraints

- **ADR-0093** (Accepted) — its scope is `agentbundle-okf/v1` bundles. The
  registry is authored skill data in its own pack read by a script in the same
  skill, so it is neither an OKF corpus nor the runtime knowledge retrieval that
  is the ADR's named revisit trigger.
- **ADR-0061** (Frozen, Phase 1) — no `dispatch-decision`, `worktree`,
  `auto-parallel`, no `pending_transition`. This slice adds no verb and no state
  field.
- The brief's appetite: one shared registry and one selector.
- `CAT-S004` bounds the skill layout to `scripts`, `references`, `assets`,
  `evals`.

## Construction tests

**Integration tests:** one — the projection landing-path check. It lives under
`packages/agentbundle/tests/build_pipeline/`, a **published** tree: the
`gate-export-boundary` gate builds an sdist and runs it where `packs/` is
absent. It must `return` on a missing corpus rather than `skip`, because
`check-artifact-contents.py` rejects a skip reason naming `packs`.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility / `references/policy-families.md` | T1, T2, T3 | Registry and selector suites green | The reference documents every record field including the unpopulated one |
| Current architecture / `docs/architecture/pack-layout.md` | T6 | The `skill` row names machine-read `references/` data | An architecture reader learns the boundary changed |
| User promise / the adopter guide | T6 | `tools/validate_guides.py` clean; identifier and heading assertions in the registry suite | Guide carries the three required headings and every identifier |
| Release history / changelog and both core manifests | T7 | `make build-check` green | Topmost entry, both versions equal, now-highlights regenerated |
| Product truth / the brief's Spec map and `docs/specs/README.md` | T7 | `lint-brief-coverage.py` exits 0 | Spec map carries the bare identifier and the index carries its row |

## Design (LLD)

Shape is `data`, so only the two sub-sections that shape selects are kept.

### Data & schema

Traces to: AC1, AC2, AC3, AC4 · no `contracts/` file — the record stays inside
the skill, per the spec's Assumptions.

Two load-bearing choices and the alternative each rejected:

- **Fenced JSON inside a Markdown reference, not a bare `.json` under
  `assets/`.** The brief mandates `references/`, and a maintainer needs the prose
  around the table that `operational-safety`'s module index provides. JSON rather
  than TOML because `tomllib` yields typed dates for bare date-shaped scalars,
  which would make a record round-trip lossy.
- **One version token, expressed twice with a stated relation.** The info string
  carries `v1` and the block carries `schema_version: 1`, and the selector
  refuses a pair that disagrees. The nearer precedent
  (`review-verdict-record.md:15`) uses a single string token; that is rejected
  here because the selector needs an integer to compare against a supported
  range, and an unenforced second token is how the two silently diverge.

### Interfaces & contracts

Traces to: AC5, AC6, AC7, AC8 · no `contracts/` file.

The selector is a CLI, not an importable API, because every existing work-loop
script is invoked as a subprocess by the controller and none exposes a package.
Registry path and resolution root are explicit options so the same code serves
the repository, a projection, and a bad-registry fixture without a second entry
point.

Fence extraction needs CommonMark semantics rather than a toggle: a nested fence
inside an example flips a toggle back, the defect `_loop_guards.py:791-800`
already documents here. That logic is inline in `canonical_contract` and exposes
no reusable helper, so the selector carries its own minimal extraction.

## Tasks

### T1: the registry is present, total, and selects something

**Depends on:** none

**Touches:** packs/core/.apm/skills/work-loop/references/policy-families.md, packs/core/tests/skills/work-loop/

**Tests:**
- A new suite under `packs/core/tests/skills/work-loop/` is the sole home for the
  family-table and selection-map assertions. No other suite re-asserts them.
- AC4's domain case loads `loop-engine.py` through
  `importlib.util.spec_from_file_location`, following
  `test_loop_guards_parity.py:80-81`. **The key shape is a two-tuple
  `(source_state, event)`** — sources are `key[0]`, targets are the values. The
  module comment at `loop-engine.py:530` says `(mode, source_state, event)` and
  is wrong; `mode` is the outer `_TRANSITIONS_BY_MODE` mapping. An implementer
  who trusts that comment derives the event set and still gets a plausible green
  suite, so the derivation is named here rather than left to inference.
- **The import is not the same shape as the cited precedent.**
  `test_loop_guards_parity.py:80-81` loads `_loop_guards.py`, which has no
  module-level stream call. `loop-engine.py:47-48` calls
  `sys.stdout.reconfigure(...)` at module scope, which raises under a test that
  captures stdout with an `io.StringIO`. The repository already documents the
  hazard and its fix at `_loop_guards.py:613-621` — swap in a throwaway
  `TextIOWrapper` so the caller's stream is untouched. Reuse that mechanism; the
  spike that proved the ten states ran outside a capturing harness and does not
  cover this.
- No stub is authored here. `new-spec` step 4 is a pointer and self-check only —
  `work-loop` PLAN owns exact stub code, its compile pass, and its recorded red
  (`work-loop/SKILL.md:286`, `references/tdd-stubs.md:2-5`). Each TDD task below
  carries its `Tests:` intent; the stub blocks and the spec's covered /
  uncovered / `no stub (mode)` tally land when the loop enters PLAN.

**Approach:**
- Author the reference: prose framing, then a table describing the *fields* a
  family record carries and what each selection key means, then the fenced block.
  The prose must not restate the five records — a second unpinned copy of the
  data in the same file is how the two drift, and AC2 pins only the block.
  `review-verdict-record.md:15-40` is the precedent: fence plus field schema, not
  fence plus a duplicate of the data.
- Populate families and the selection map from the spec's AC2 and AC3.

**Mutation proof A (the empty-registry defect):** replace
`SPEC-PLAN-DRAFTING`'s list with `[]`. AC3's literal comparison must fail. This
is the mutation the criteria set previously survived, so it is the one that
proves the guard exists.

**Mutation proof B (the omitted-state defect):** delete the `CODE-REVIEW` entry.
AC4's derived-domain case must fail naming that state, while AC3 also fails —
two independent guards reddening is the expected result, not a duplicate.

**Done when:** the suite is green and both mutations redden it as described.
Restore by editing.

### T2: a selection key yields a record in declared order

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/scripts/select-policy-families.py, packs/core/tests/skills/work-loop/

**Tests:**
- Extend T1's suite with the envelope case (AC5) and the ordering case (AC6).
- The ordering case compares against the registry's declared list, not against a
  second run of the selector. A same-code comparison proves only determinism,
  which a reversed-but-deterministic selector also satisfies.

**Approach:**
- Add the script with its two options and one positional key.
- Extract the fenced block under CommonMark rules, validate the version pair,
  then emit the envelope.

**Mutation proof:** make the selector emit `list(reversed(...))` for `families`.
The ordering case must fail. A set-derived list is deliberately *not* the
mutation here: for a two-member selection it frequently round-trips in
declaration order, so it can leave the case green and prove nothing.

**Done when:** the selector prints a record for every registry key and the
reversal reddens the ordering case.

### T3: the record fingerprints the teaching text an agent would read

**Depends on:** T2

**Touches:** packs/core/.apm/skills/work-loop/scripts/select-policy-families.py, packs/core/tests/skills/work-loop/

**Tests:**
- The `seed:` case asserts against root `AGENTS.md`, not the seed copy. The two
  differ in this repository, which is what makes the preference order observable.
- The `skill:` case cannot use the repository tree as its fixture: all three
  candidates there are byte-identical, so the digest is invariant under any
  permutation and the order has no oracle. It builds a tmp root holding two
  deliberately different files at the first and third candidate paths, and
  asserts which one is chosen. Without that fixture an implementer could invert
  the order to prefer the catalogue source — re-entering the defect the locator
  exists to prevent — with every case still green.
- One case asserts the emitted `tier` and `module` against the registry record
  for the same `id`, not merely their presence.

**Approach:**
- Resolve `skill:` and `seed:` locators by first-existing candidate, then digest
  the resolved bytes.

**Mutation proof A (the flattened-tier defect):** emit a constant
`tier: "advisory"` for every family. The tier case must fail. Presence-only
assertions survive this, which is why the case compares against the registry.

**Mutation proof B (the resolution-order defect):** reverse the `seed:`
candidate order so `packs/core/seeds/AGENTS.md` is preferred over root
`AGENTS.md`, and independently reverse the `skill:` order under the tmp fixture.
Each must redden its own case on a differing digest.

**Done when:** all three cases are green and each mutation reddens exactly its
own case.

### T4: a malformed registry or an unknown key is refused

**Depends on:** T3

**Touches:** packs/core/tests/skills/work-loop/, packs/core/.apm/skills/work-loop/scripts/select-policy-families.py

**Tests:**
- One case per member of AC8's set, each driving a purpose-built bad registry
  written to a tmp path rather than mutating the shipped one. A shared fixture
  would let an earlier case destroy the evidence a later case needs.
- The two version cases need specific, different fixtures, because the pair check
  validates before the `== 1` check and each obvious choice is dominated by the
  other member:
  - `schema_version` case — `json policy-registry.v2` with `schema_version: 2`.
    The obvious `v1` with `schema_version: 2` trips the pair check first, so it
    would prove that check and stay green when `== 1` is removed.
  - info-string case — `json policy-registry.v2` with `schema_version: 1`. The
    obvious `v1` with `schema_version: 2` is caught by the `== 1` check once the
    pair check is removed, so it stays green under its own mutation. Only a
    *supported* version with a mismatched info string dies.

  Neither fixture is interchangeable. Getting this wrong makes the pair check
  removable with no red test, which would undo the whole reason two version
  tokens exist.
- Assert the `select-policy-families:` prefix at the start of the stream, not as
  a bare substring: the script name appears in argv echoes, so a substring check
  can pass while the message is missing.

**Approach:**
- Validate in the order a reader hits it: version pair, family-table integrity,
  locator namespaces, selection-map integrity, then the key.

**Mutation proof:** remove the duplicate-`id` check. Its case must fail while
every other case stays green, proving the cases are independent rather than all
riding one validation path. The expectation is "every other", not a number —
AC8's membership has already grown twice during review.

**Done when:** every refusal case is green and removing any single check reddens
exactly its own case.

### T5: the registry reaches both adapters

**Depends on:** T1

**Touches:** packages/agentbundle/tests/build_pipeline/

**Tests:**
- One integration test asserting the two landing paths, projecting each adapter
  into its own output tree — projecting both into one directory cannot
  distinguish a swap from a correct result.
- It returns rather than skips when the corpus is absent, per § Construction
  tests.
- It passes `--registry` the projected copy and `--root` the repository root.
  Those must be different trees: `ADAPTERS[adapter](...)` emits pack artifacts
  only, and seeds reach a consumer through the separate `scaffold` command, so a
  projection tree holds no `seed:` target. `CODE-IMPLEMENTATION` selects two
  `seed:` families, so pointing `--root` at the projection output makes the
  selector refuse under AC8 and AC9 can never be reached.
- It compares each projected copy against AC9's literal sequence, never against
  the other projection; the spec's § "Assumptions" carries why.

**Approach:**
- Follow the sibling projection test's adapter iteration and temporary roots.

**Mutation proof A:** restrict the projection to the `claude-code` adapter. The
test must fail naming the missing `.agents/skills/` path.

**Mutation proof B:** empty `CODE-IMPLEMENTATION`'s list in the projected
registries only. The test must fail on the literal comparison, proving AC9 does
not merely check that two projections agree.

**Done when:** the test passes in the repository and returns cleanly when
`packs/` is absent.

### T6: an adopter can declare, classify, and troubleshoot a family

**Depends on:** T1

**Touches:** guides/core/reference/phase-scoped-policy-delivery.md, docs/architecture/pack-layout.md, packs/core/tests/skills/work-loop/

**Tests:**
- `tools/validate_guides.py` covers the frontmatter half.
- The heading and identifier coverage assertions live in T1's suite, so the
  family list has one assertion home shared by registry and guide.

**Approach:**
- Follow the house shape of `guides/core/reference/spec-shape-and-lld.md`:
  frontmatter, a `:::note` orientation block, then the three task-shaped sections
  the spec's Durable Outputs row names.
- Extend the `skill` row of `pack-layout.md`'s primitive table to record that
  `references/` may carry an authored machine-read block, so the boundary change
  is discoverable outside this frozen plan.

**Done when:** guide validation is clean and the coverage assertions are green.

### T7: the release surface and the brief record this slice

**Depends on:** T1-T6

**Touches:** docs/product/changelog.md, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/briefs/phase-scoped-policy-delivery.md, docs/specs/README.md, web/src/lib/now-highlights.generated.json

**Tests:**
- `lint-brief-coverage.py` and the roster's version-parity assertion cover this
  task; no new test is written.

**Approach:**
- Bump both core manifests together; add the changelog section directly beneath
  `[Unreleased]`.
- Add the bare identifier to the brief's Spec map and a row to
  `docs/specs/README.md`'s Active-specs table; the spec's Product-truth row names
  both destinations.
- Regenerate the now-highlights projection rather than hand-editing it.

**Done when:** every gate in the spec's release closeout condition is green.

## Rollout

Pure-logic and data change inside one already-installed skill. No flag, no
infrastructure, no external system, no sequencing constraint: the registry and
selector are inert until D2 calls them, so shipping them early carries no runtime
risk. Rollback is reverting the PR.

## Risks

- **The state-derivation mechanism could have failed.** `loop-engine.py` is
  hyphenated and so not importable by name. Spiked before this plan was
  finalised: loading it through `importlib.util.spec_from_file_location` executes
  cleanly and yields exactly the ten states the schema documents, and two
  work-loop tests already use that idiom.
- **The locator's resolution order is a guess about adopter layout.** It prefers
  the copy an agent reads over the catalogue source; the spec's
  § "Acceptance Criteria" → "Locator resolution" is its single canonical
  statement and this plan does not restate it. An adopter installing only `codex`
  still resolves, because a later candidate matches. An adopter who installs
  neither has no teaching text to inline, and AC8's resolution refusal is the
  intended outcome rather than a silent empty digest. The order is
  behaviourally inert in this repository, where every `skill:` candidate is
  byte-identical, so T3 builds a tmp fixture whose candidates differ rather than
  leaving a three-member ordering with no oracle.
- **The registry can drift from the rules it points at.** A locator that stops
  resolving is caught by AC8; a rule that moves *within* its file is not caught
  here, and the `module_digest` will change without anyone noticing why. Accepted
  for this slice — detecting a moved section is the arrival validator's problem.
- **`seed:AGENTS.md` degrades silently on an edited adopter root, and that is
  the expected adopter state.** `packs/core/seeds/AGENTS.md` tells the adopter to
  "Replace the marked project and command details", so the root file is designed
  to be rewritten. An adopter who drops § "Cut before adding" leaves `the-razor`
  resolving to a file that exists and digests cleanly while teaching nothing.
  AC8 refuses only a locator that resolves to no file. This slice establishes
  which file carries a rule, never that the file still contains it; the Objective
  is worded to claim only the former, and the content question is V1's.
- **The first `references/` reader sets a precedent.** T6 records it in the
  architecture reference so the next author finds it there rather than in a
  frozen plan.

## Changelog

- 2026-09-03: initial plan. Written after a spike disconfirmed the main
  implementation risk (hyphenated-module import for the state domain).
- 2026-09-03: adversarial verification round. Two approach changes, not
  re-orderings. T5's construction now fixes which tree each option points at:
  `--registry` at the projected copy, `--root` at the repository, because an
  adapter projection emits no seeds and both families `CODE-IMPLEMENTATION`
  selects are `seed:` locators — AC9 as first written could never be reached.
  T4 gained two mandatory and non-interchangeable fixture shapes, because each
  version member is dominated by the other under the obvious fixture.
- 2026-09-03: adversarial spec-mode round. Two more pinned-source/floating-side
  holes closed in the spec (the info-string version pair was unenforced, and the
  record's stream and success exit were unnamed), plus per-selection-list
  duplication and the digest's string form. In this plan: the malformed
  `stub: true` marker removed, since `work-loop` PLAN owns stub authoring and
  `new-spec` is explicitly a pointer only; the `loop-engine.py` import hazard
  named with its shipped fix; T6's `Touches:` corrected so a wave's disjointness
  prediction is honest; and T1's reference shape changed from a second copy of
  the family data to a field-schema table.
- 2026-09-03: second shaping round. The emitted side of the record was
  unpinned in two more places — a selector could flatten every `tier` to
  `advisory`, or echo a constant `selection_key`, and pass all eight criteria.
  Both are now compared against their source. The two locator resolution
  algorithms moved out of the checklist into prose above it, leaving AC7 as one
  predicate over the family record. T3 gained a tmp fixture because the `skill:`
  order has no oracle in a tree where every candidate is byte-identical.
- 2026-09-03: reworked after spec-stage shaping review. Three changes of
  approach, not ordering: family teaching text moved from raw catalogue paths to
  `skill:`/`seed:` logical locators, because the raw paths would have made every
  authoring phase refuse on an adopter install; the selection map's values gained
  a literal pin, because the prior criteria set was satisfied by a registry that
  selected nothing; and per-family `module_digest` entered the record, restoring
  what the brief assigns this slice. Task count went 6 to 7 and the mutation
  proofs for ordering and resolution were replaced with ones that actually kill.
