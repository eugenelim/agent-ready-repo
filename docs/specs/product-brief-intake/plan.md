# Plan: product-brief-intake

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **additive to `core`** and lands as a single PR (RFC-0004
atomicity, matching prior `core`-touching specs). Three surfaces:

1. **A new artifact** — a brief template seed under
   `packs/core/seeds/docs/product/briefs/`, joining `roadmap.md` /
   `changelog.md` in the existing product bucket.
2. **A new skill** — `receive-brief` under `packs/core/.apm/skills/`, the
   elicit → decompose → execute workflow, plus a bundled auto-rollup lint
   script and an `examples/` directory with two worked briefs.
3. **Light template/field edits** — an optional `Brief:` front-matter field on
   the `spec.md` template and in `new-spec`, the `Satisfies:` / `Epic:` markers
   documented, and the `CONVENTIONS.md` seed amendment that records the new
   altitude. All additive; nothing removed or renamed, so prior specs stay valid.

The riskiest part is the **auto-rollup lint**: it must read only existing
`Status:` fields via `Brief:` back-links (no new state), no-op cleanly on a repo
with no brief (this repo), and treat a missing back-link as *untracked*, never an
error. It is built TDD-first. Everything else is goal-based file authoring whose
verification is "the file exists at its conventional path and the existing
linters pass." The `receive-brief` workflow itself is LLM judgment, verified by
walking the two shipped examples (manual QA). Since `receive-brief` only *chains*
`new-spec` (it does not itself implement LLD derivation — that is the sibling
`lld-aware-spec-plan` spec), this spec does **not** depend on `lld-aware-spec-plan`
and can ship standalone.

## Constraints

- **RFC-0019** — Decisions 1 (own-the-slice), 2 (new `brief` artifact), 3 (ship
  in `core`), 4 (elicit, don't mandate a schema), 5 (optional stories +
  `Satisfies:`), 6 (`Brief:` reference linkage), 7 (auto-rollup coverage).
- **ADR-0009** — the brief altitude, own-the-slice boundary, and `Brief:`
  linkage by reference.
- **Open question resolutions (Approver, 2026-06-01):** auto-rollup lint in
  `make build-check` (Q1); skill name `receive-brief` (Q2); `examples/` ships
  both shapes, each labelled an example (Q3).
- **Charter Principle 1 (Universal):** the brief, the skill, and the lint are
  stack-agnostic — no stack baked in.
- **Compose-around-core:** `core` imports no code from another pack.

## Construction tests

Most construction tests live under **Tasks** below. Cross-cutting:

**Integration tests:** the auto-rollup lint runs green inside `make build-check`
on this repo (no brief present → no-op, exit 0) — this is the end-to-end gate
that proves the lint is wired and harmless on a brief-free repo.
**Manual verification:** walk both shipped `examples/` briefs through the
`receive-brief` flow conceptually (elicit → decompose → execute) and confirm the
documented behavior matches — recorded in the implementing PR.

## Tasks

### T1: Brief template seed exists with the documented fields

**Depends on:** none
**Touches:** packs/core/seeds/docs/product/briefs/*

**Tests:**
- Goal-based: a brief template file exists under
  `packs/core/seeds/docs/product/briefs/` and contains headings for Outcome,
  Success metrics, Scope / Non-goals, Appetite, optional User stories, optional
  `Epic:`, and the Spec map (coverage table). *(verifies AC: brief template)*
- Goal-based: the template's framing text states the shape is a guide, not a
  schema (elicit posture). *(verifies AC: elicit / never reject)*

**Approach:**
- Author the brief template seed with the RFC-0019 field set; phrase the Spec
  map as an auto-derived coverage table (status column populated by the lint).
- Keep it stack-agnostic; no example content baked in (examples ship in T5).

**Done when:** the seed file exists at the conventional path with every
documented field heading present.

### T2: `spec.md` template + `new-spec` gain an optional `Brief:` field

**Depends on:** none
**Touches:** packs/core/.apm/skills/new-spec/assets/spec.md, packs/core/.apm/skills/new-spec/SKILL.md

**Tests:**
- Goal-based: the `spec.md` template carries an optional `- **Brief:**` header as
  a sibling to `Constrained by:` / `Contract:`. *(verifies AC: Brief: field)*
- Goal-based: `new-spec` SKILL.md documents stamping `Brief:` when a spec is
  derived from a brief, and treats it as optional (specs without it stay valid).
- Goal-based: `lint-spec-status.py` and `lint-skill-spec.py` still pass with the
  added field (additive, no breakage).

**Approach:**
- Edit the `new-spec` pack-source `assets/spec.md` to add the `Brief:` header
  (commented as optional, "from a product brief; see receive-brief").
- Note in `new-spec` SKILL.md where the field is stamped. Do **not** add the
  `Shape:` field here — that belongs to the sibling `lld-aware-spec-plan` spec.

**Done when:** the template carries the optional field, `new-spec` documents it,
and both linters pass.

### T3: `Satisfies: US-n` and `Epic:` markers documented

**Depends on:** T1, T2
**Touches:** packs/core/seeds/docs/product/briefs/*, packs/core/.apm/skills/new-spec/**

**Tests:**
- Goal-based: the brief template documents the optional `Epic:` pointer field.
- Goal-based: the `Satisfies: US-n` acceptance-criterion marker is documented in
  `new-spec` / the spec template's AC guidance as the Shape-B story trace.
  *(verifies AC: Satisfies / Epic documented)*

**Approach:**
- Document `Epic:` in the brief template (optional, "external coordinator id").
- Document `Satisfies: US-n` as an optional inline AC marker for story-granular
  traceability; keep it optional (Shape A omits it).

**Done when:** both markers are documented in their conventional places.

### T4: `receive-brief` skill authored (elicit → decompose → execute)

**Depends on:** T1, T2
**Touches:** packs/core/.apm/skills/receive-brief/**

**Tests:**
- Goal-based: `packs/core/.apm/skills/receive-brief/SKILL.md` exists with
  frontmatter that passes `tools/lint-skill-spec.py`. *(verifies AC: skill ships)*
- Goal-based: SKILL.md documents the three stages — elicit load-bearing fields
  only / decompose by shippability + surface the cut / chain `new-spec` per slice
  and stamp `Brief:` (and `Satisfies:` in Shape B) then hand to `work-loop`.
  *(verifies ACs: elicit, decompose, execute)*
- Manual QA: the documented flow, walked against the T5 examples, produces a
  sensible cut and back-links (recorded in the PR).

**Approach:**
- Write the skill prose modelled on the existing `new-spec` / `bug-fix` shape:
  trigger description in frontmatter, numbered procedure (Elicit / Decompose /
  Execute), anti-patterns (never mandate a schema; never build a hub; never
  hand-maintain coverage).
- Reference (do not duplicate) `new-spec` and `work-loop` for the per-slice loop.

**Done when:** the skill file passes `lint-skill-spec.py` and documents all three
stages and the two shapes (A: no stories; B: story list).

### T5: `examples/` ships two labelled worked briefs

**Depends on:** T1, T4
**Touches:** packs/core/.apm/skills/receive-brief/examples/*

**Tests:**
- Goal-based: `examples/` contains exactly two briefs — a Shape-A (no-stories)
  outcome brief and a Shape-B (story-list) brief. *(verifies AC: two examples)*
- Goal-based: each example's header clearly labels it an **example demonstrating
  the shape, not a schema**. *(verifies AC: labelled as examples — Q3)*
- Manual QA: each example shows a populated Spec map consistent with what the
  auto-rollup lint would produce.

**Approach:**
- Author both worked briefs against the T1 template, each with a populated Spec
  map; Shape B carries `US-n` ids and `Satisfies:` traces.
- Prepend a one-line "This is an example, not a schema" banner to each.

**Done when:** both examples exist, are labelled, and are internally consistent.

### T6: Auto-rollup lint logic (TDD)

**Depends on:** T1, T2
**Touches:** packs/core/.apm/skills/receive-brief/scripts/lint-brief-coverage.py, packs/core/.apm/skills/receive-brief/scripts/test-lint-brief-coverage.py

**Tests:**
- TDD: given a brief whose Spec map lists specs A (`Shipped`) and B
  (`Implementing`), the lint rolls A→shipped, B→implementing, brief→not
  delivered. *(verifies AC: rollup from Status)*
- TDD: given a brief whose every back-linked spec is `Shipped`, the brief reports
  *delivered*. *(verifies AC: delivered when all Shipped)*
- TDD: given a brief whose Spec map has **no mapped child specs**, the brief
  reports **not delivered** (an empty rollup is never vacuously delivered).
  *(verifies AC: empty map → not delivered)*
- TDD: given a repo with no brief, the lint exits 0 with no diagnostic output.
  *(verifies AC: no-op when no brief)*
- TDD: given a spec carrying `Brief: <slug>` not present in that brief's map, the
  spec is reported **untracked** (informational), not a lint error.
  *(verifies AC: missing back-link → untracked, not error)*
- TDD: invoked via its documented file-path form (subprocess), not a synthesised
  import, so the real entry point is exercised.

**Approach:**
- Stdlib-only Python (`scripts/lint-brief-coverage.py`), reads every
  `docs/specs/*/spec.md` `Status:` field and each spec's `Brief:` back-link,
  reconciles against each brief's Spec map, no new state.
- Pure reconciliation function with a thin CLI wrapper; co-locate a
  script-invocable self-test `scripts/test-lint-brief-coverage.py` (matching the
  `test-lint-spec-status.py` precedent) that the gate can run as a standalone
  `$(PYTHON) .../test-lint-brief-coverage.py` line; tests target the function and
  one subprocess smoke test against the CLI.

**Done when:** all six tests pass (red→green) and the script is stdlib-only.

### T7: Wire the lint into `make build-check`; verify no-op on this repo

**Depends on:** T6
**Touches:** Makefile

**Tests:**
- Goal-based: `make build-check` invokes **both** the projected self-test
  (`test-lint-brief-coverage.py`) and the lint (`lint-brief-coverage.py`),
  mirroring the two-line `test-lint-spec-status.py` + `lint-spec-status.py`
  precedent, and exits 0 on this repo (no brief present → no-op).
  *(verifies AC: wired into build-check, fail-closed, green here)*

**Approach:**
- Add two lines to the `build-check` target calling the projected
  `.claude/skills/receive-brief/scripts/test-lint-brief-coverage.py` then
  `.claude/skills/receive-brief/scripts/lint-brief-coverage.py` — the same shape
  as the existing spec-status self-test + lint pair (Makefile:79-80).
- Confirm the no-brief no-op so this repo's gate stays green.

**Done when:** `make build-check` runs the self-test + lint and passes on this repo.

### T8: `CONVENTIONS.md` seed amendment

**Depends on:** T1, T2, T3
**Touches:** packs/core/seeds/docs/CONVENTIONS.md

**Tests:**
- Goal-based: the `CONVENTIONS.md` seed adds `briefs/` under `product/` in the
  document-hierarchy diagram, documents the `Brief:` field on specs, and the
  `roadmap → brief → spec → AC` altitude. *(verifies AC: CONVENTIONS amendment)*

**Approach:**
- Edit the pack-source seed `packs/core/seeds/docs/CONVENTIONS.md` (not the
  projected `docs/CONVENTIONS.md` — `build-self` projects it). Keep the LLD parts
  (`Shape:`, `## Design (LLD)`) out — those land with `lld-aware-spec-plan`.

**Done when:** the seed carries the briefs altitude and `Brief:` field; the
projection re-renders cleanly in T9.

### T9: `make build-self` projection + `make build-check` green

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8
**Touches:** dist/**, .claude/**, AGENTS.md

**Tests:**
- Goal-based: `make build-self` projects the new core skill + seed cleanly;
  `git status` shows no unexpected reverts (guard against projection-only drift).
- Goal-based: `make build-check` is green end to end.
  *(verifies AC: build-self projects cleanly; build-check green)*

**Approach:**
- Run `make build-self`, inspect `git status` for unexpected reverts to projected
  paths, run `make build-check`. Resolve any projection drift in this PR.

**Done when:** both targets succeed and the projection is consistent.

### T10: Adopter guides authored via `new-guide`

**Depends on:** T1, T2, T3, T4, T5
**Touches:** docs/guides/**

**Tests:**
- Goal-based: three guide files exist under `docs/guides/` at their Diátaxis
  paths — a how-to, a reference, and an explanation per the spec's guide ACs.
  *(verifies AC: guide files exist)*
- Manual QA: each reads accurately against the shipped skill + template
  (recorded in the PR). *(verifies AC: guides read accurately)*

**Approach:**
- `new-guide` lives in the non-core `user-guide-diataxis` pack — this task runs
  **in this catalogue repo**, where that pack is installed; it is not a capability
  `core` ships to adopters. Scaffold each quadrant via `new-guide`; write the
  how-to (receive → decompose end to end), the reference (brief fields + `Brief:`
  / `Satisfies:`), and the explanation (why a brief layer; the altitude).

**Done when:** the three guide files exist and read accurately against the
implementation.

## Rollout

Additive, single PR, no runtime behavior change for existing adopters — a brief
is opt-in (you only get one if you run `receive-brief`). The `Brief:` field and
`## Design (LLD)` (sibling spec) are optional, so specs/plans authored before
this change stay valid. Reversible: removing the skill + seed + lint line leaves
prior specs untouched. The auto-rollup lint is fail-closed in `build-check` but
no-ops where no brief exists, so it cannot break a brief-free adopter's gate.

## Risks

- **The lint mis-classifies a half-mapped brief.** Mitigation: it reads only
  existing `Status:` fields and treats a missing/extra back-link as untracked
  (informational), never an error — TDD pins exactly these cases (T6).
- **The skill becomes ceremony.** Mitigation: it earns its place by executing
  (brief → specs → work-loop) and auto-tracking coverage, not by producing a
  document.
- **`Brief:` field addition ripples through the self-host projection.**
  Mitigation: additive-only; T9 runs `build-self` and guards against
  projection-only reverts before the PR opens.
- **Scope bleed into `lld-aware-spec-plan`.** Mitigation: this spec stops at
  *chaining* `new-spec`; the `Shape:` field and LLD derivation are explicitly out
  of scope and owned by the sibling spec.

## Changelog

- 2026-06-01: initial plan (drafted from RFC-0019 + ADR-0009).
- 2026-06-01: T6 refined during EXECUTE — the lint's fail-closed condition is a
  brief's Spec-map Status cell that *contradicts* the spec's actual `Status:`
  (a hand-edited, now-stale cell); an unset cell (`<auto>`/`—`/empty) is
  reported, not failed, and the `_template.md` placeholder is skipped. Added two
  self-test cases (stale-cell drift → exit 1; unset cell → not drift) beyond the
  six in the task. This is what gives "fail-closed in build-check" non-vacuous
  meaning while keeping the no-brief / untracked / empty-map ACs intact.
- 2026-06-01: shipped. All tasks T1–T10 complete; `make build-check` green;
  spec marked Shipped with all ACs checked (spec + code land atomically).
  Self-host projection: build-self does not project `docs/product/briefs/` into
  this repo (consistent with `docs/product/` being adopter-owned), so this repo
  ships no brief and the coverage lint no-ops — no `self_host.py` change needed.
