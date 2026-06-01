# Plan: lld-aware-spec-plan

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **additive to `core`'s spec/plan templates and two skills**, and
lands as a single PR (RFC-0004 atomicity). Four surfaces, all edited at
**pack-source** (`packs/core/.apm/skills/new-spec/...`) and then projected by
`make build-self` — never the projected `.claude/` copies directly:

1. **`spec.md` template (light):** an optional stack-neutral `Shape:` field +
   AC guidance (UI state/trigger/outcome → AC; NFR with a pass/fail bar → AC) +
   minor `Contract:` / `Testing Strategy` wording. No LLD body in the spec.
2. **`plan.md` template (the LLD home):** a `## Design (LLD)` section before
   `## Tasks` built from the ten stack-neutral categories as optional,
   shape-selected sub-headings, plus an **expanded `## Rollout`** covering infra,
   external-system integration, and deployment sequencing.
3. **`new-spec` SKILL.md:** a shape/stack-derivation step — derive `Shape:`
   (from the brief or by asking) and the stack, reading
   `docs/architecture/reference.md` when present and degrading to repo detection
   + elicitation when absent.
4. **`receive-brief` SKILL.md:** the same derivation step when it scaffolds
   specs (cross-spec — depends on `receive-brief` existing).

The riskiest part is **keeping the templates universal** while making the LLD
useful: the shipped template must carry only category *names*, never a stack —
verified by a grep that returns no framework/library strings (T5). Everything
else is goal-based file authoring; the derivation step's quality is LLM judgment
verified by walking a reference-present and a reference-absent case (manual QA,
T3). Because the spec/plan templates are the widest blast radius in the repo,
**additivity is load-bearing** — T5 and T7 prove all prior specs/plans stay
valid and the projection re-renders cleanly.

This spec can land **before or after** `product-brief-intake` (RFC-0019's
either-order seam), with one exception: T4 (derivation inside `receive-brief`)
depends on `receive-brief` existing, so it carries a cross-spec dependency on
`product-brief-intake`. If `lld-aware-spec-plan` lands first, T4 is deferred to a
follow-up that lands once `receive-brief` exists; the rest ships standalone.

## Constraints

- **RFC-0019** — Decision 8 (LLD locus = enrich `plan.md` + light `spec.md`;
  reuse Rollout / Depends-on; no new tiers) and Decision 9 (stack derived from
  `reference.md` when present, else degrade; template ships categories only).
- **ADR-0009** — plan-owned LLD; derived, never-baked stack; additive-only.
- **RFC-0020** — `docs/architecture/reference.md` is the foundation the LLD
  conforms to when present; the present/absent branch is the either-order seam.
- **Charter Principle 1 (Universal):** no stack in the shipped template.

## Construction tests

Most construction tests live under **Tasks** below. Cross-cutting:

**Integration tests:** `make build-check` green after `make build-self` projects
the enriched templates — the end-to-end proof that additive template edits
re-render cleanly and break no existing gate. A grep across the shipped templates
for concrete framework names (`react|tanstack|kafka|spring|django|rails|...`)
returns nothing — the universality gate.
**Manual verification:** walk the derivation step against (a) a repo with
`docs/architecture/reference.md` present and (b) one without, confirming the LLD
conforms in case (a) and degrades to detection + elicitation in case (b);
recorded in the implementing PR.

## Tasks

### T1: `spec.md` template gains `Shape:` + AC guidance + Contract/Testing wording

**Depends on:** none
**Touches:** packs/core/.apm/skills/new-spec/assets/spec.md

**Tests:**
- Goal-based: the template carries an optional `- **Shape:**` field with the
  `ui | service | data | integration | mixed` vocabulary, documented as selecting
  the plan's `## Design (LLD)` sub-sections. *(verifies AC: Shape: field)*
- Goal-based: the AC-guidance comment instructs that a UI state/trigger/outcome
  and an NFR-with-a-bar each become acceptance criteria. *(verifies AC: AC guidance)*
- Goal-based: no LLD body section is added to the spec template (negative).
  *(verifies AC: no LLD body in spec)*
- Goal-based: a grep of the shipped `spec.md` template confirms its `Testing
  Strategy` comment names integration / E2E and its `Contract:` comment names
  events / BFF. *(verifies AC: Contract / Testing verification surfaces)*
- Goal-based: `lint-spec-status.py` still passes on the existing specs.

**Approach:**
- Add the `Shape:` header (commented optional) below `Contract:`; extend the
  Acceptance Criteria comment with the UI-state and NFR-bar guidance; touch the
  `Contract:` / `Testing Strategy` comments to name events/BFF and integration/E2E.
- Do not add the `Brief:` field here — that is `product-brief-intake`'s; this PR
  coordinates so both additive fields coexist.

**Done when:** the template carries `Shape:` + extended AC guidance, no LLD body,
and the spec linter passes.

### T2: `plan.md` template gains `## Design (LLD)` + expanded `## Rollout`

**Depends on:** none
**Touches:** packs/core/.apm/skills/new-spec/assets/plan.md

**Tests:**
- Goal-based: the template carries a `## Design (LLD)` section **before
  `## Tasks`** with **nine** category names as optional, shape-selected `###`
  sub-headings (the tenth, rollout & deployment, realized by the expanded
  `## Rollout`). *(verifies AC: Design (LLD) section + nine sub-headings)*
- Goal-based: each sub-section's guidance says it traces to the AC(s) it
  satisfies and the `contracts/` it implements. *(verifies AC: tracing guidance)*
- Goal-based: `## Rollout` is expanded to name infra, external-system
  integration, and deployment sequencing. *(verifies AC: expanded Rollout)*
- Goal-based: no new dependency tier or testing tier appears — `Depends on:` /
  `Touches:` and `Construction tests` are reused (negative). *(verifies AC: no new tiers)*

**Approach:**
- Insert the `## Design (LLD)` section between `## Construction tests` and
  `## Tasks`; list the nine design categories as `###` sub-headings (the tenth,
  rollout & deployment, is realized by the expanded `## Rollout`), each marked
  optional + shape-selected with a one-line "trace to AC(s) + contracts/" note.
- Expand the existing `## Rollout` comment to cover the three deployment
  dimensions; leave its existing meaning intact (expand, don't redefine).

**Done when:** the plan template carries the new section and expanded Rollout,
adds no new tiers, and prior plans remain valid.

### T3: `new-spec` gains the shape/stack-derivation step

**Depends on:** T1, T2
**Touches:** packs/core/.apm/skills/new-spec/SKILL.md

**Tests:**
- Goal-based: `new-spec` SKILL.md documents a step that derives `Shape:` (from
  the brief or by asking) and the stack. *(verifies AC: new-spec derivation step)*
- Goal-based: the step documents reading `docs/architecture/reference.md` when
  present (conform, reference components by name) and degrading to repo detection
  (lockfiles / build files / imports) + elicitation when absent.
  *(verifies AC: reference.md present/absent branch)*
- Goal-based: `new-spec`'s SKILL.md still passes `tools/lint-skill-spec.py` after
  the edit (matching the sibling spec's `lint-skill-spec` check on `receive-brief`).
- Manual QA: walked against a reference-present and a reference-absent repo, the
  step produces a conforming LLD vs a detected/elicited one (recorded in PR).

**Approach:**
- Add the derivation step to `new-spec`'s procedure (between spec body and plan
  authoring); state the present/absent branch and the "elicit, don't invent"
  rule for ambiguous detection.

**Done when:** the step is documented with both branches and the manual walk is
recorded.

### T4: `receive-brief` gains the same derivation step (cross-spec)

**Depends on:** spec:product-brief-intake/T4, T3
**Touches:** packs/core/.apm/skills/receive-brief/SKILL.md

**Tests:**
- Goal-based: `receive-brief` SKILL.md's execute spine documents invoking the
  shape/stack-derivation step when it scaffolds each spec. *(verifies AC: receive-brief derivation)*

**Approach:**
- Add a one-line reference in `receive-brief`'s Execute stage pointing at
  `new-spec`'s derivation step (reference, don't duplicate). If
  `product-brief-intake` has not shipped, defer this task to a follow-up PR that
  lands once `receive-brief` exists (per the cross-spec dependency).

**Done when:** `receive-brief` documents the derivation step, or the task is
explicitly deferred pending `receive-brief`.

### T5: Universality + additivity gates (grep + backward compat)

**Depends on:** T1, T2
**Touches:** (verification only)

**Tests:**
- Goal-based: a grep across the shipped templates for concrete framework/library
  names returns nothing. *(verifies AC: templates carry only category names)*
- Goal-based: the existing specs/plans parse/lint unchanged after the template
  edits (additive). *(verifies AC: additive; prior specs stay valid)*

**Approach:**
- Run the grep and the existing linters across `docs/specs/*`; confirm no
  regressions.

**Done when:** the grep is empty and all existing specs/plans stay valid.

### T6: `CONVENTIONS.md` seed amendment (LLD enrichment, §4)

**Depends on:** T1, T2, T3
**Touches:** packs/core/seeds/docs/CONVENTIONS.md

**Tests:**
- Goal-based: the `CONVENTIONS.md` seed §4 documents the `Shape:` field, the
  `## Design (LLD)` categories, and stack-derivation. *(verifies AC: CONVENTIONS amendment)*

**Approach:**
- Edit the pack-source seed `packs/core/seeds/docs/CONVENTIONS.md` §4. Coordinate
  with `product-brief-intake`'s CONVENTIONS edit if both land near each other
  (briefs altitude vs LLD enrichment are different parts of the file).

**Done when:** §4 of the seed documents the LLD enrichment; projection re-renders
in T7.

### T7: `make build-self` projection + `make build-check` green

**Depends on:** T1, T2, T3, T4, T5, T6
**Touches:** dist/**, .claude/**

**Tests:**
- Goal-based: `make build-self` projects the enriched templates + skills cleanly;
  `git status` shows no unexpected reverts to projected paths.
- Goal-based: `make build-check` is green end to end. *(verifies AC: build-check green)*

**Approach:**
- Run `make build-self`, inspect `git status`, run `make build-check`; resolve
  any projection drift in this PR.

**Done when:** both targets succeed and the projection is consistent.

### T8: Adopter reference/explanation guides for the LLD additions

**Depends on:** T1, T2, T3
**Touches:** docs/guides/**

**Tests:**
- Goal-based: a reference guide file and an explanation guide file exist under
  `docs/guides/` at their Diátaxis paths. *(verifies AC: guide files exist)*
- Manual QA: the reference guide documents `Shape:`, the `## Design (LLD)`
  categories, and stack-derivation; the explanation guide covers why the design
  lives in the plan — both reviewed for accuracy. *(verifies AC: guides accurate)*

**Approach:**
- `new-guide` lives in the non-core `user-guide-diataxis` pack — this task runs
  **in this catalogue repo**, where that pack is installed; it is not a capability
  `core` ships to adopters. Coordination with `product-brief-intake`'s guide work
  (so the reference guide can carry both the `Brief:` and the LLD additions in one
  place) is **advisory, not a hard sequencing dependency** — hence no
  `spec:product-brief-intake/T10` (the sibling's guide task) in `Depends on:`;
  whichever lands second appends
  its section to the existing reference guide.

**Done when:** the guide files exist and read accurately against the templates.

## Rollout

Additive, single PR, no runtime behavior change. The `Shape:` field and
`## Design (LLD)` section are optional and shape-pruned, so a trivial change
keeps a thin plan and specs/plans authored before this change stay valid.
Reversible: the additions can be removed without invalidating prior specs.
Because the spec/plan templates feed the self-host projection and every adopter,
the additive-only rule is the safety property — T5/T7 enforce it before the PR
opens.

## Risks

- **A stack leaks into the shipped template.** Mitigation: the T5 grep gate is
  fail-loud; the template carries only category names.
- **The `## Design (LLD)` section bloats trivial plans.** Mitigation: optional +
  shape-pruned; the small-change path scaffolds nothing.
- **The derivation step invents a stack on an ambiguous repo.** Mitigation:
  "elicit, don't invent" is a Boundary; detection degrades to a question.
- **Same-file additive collision with `product-brief-intake`** (both add a
  front-matter field to `spec.md`; both touch `CONVENTIONS.md`). Mitigation:
  coordinate the two PRs — different fields, different file regions; whichever
  lands second rebases the additive hunk.
- **Editing the widest-blast-radius templates.** Mitigation: additive-only;
  `make build-self` + the existing linters + the prior-spec backward-compat check
  run before the PR opens.

## Changelog

- 2026-06-01: initial plan (drafted from RFC-0019 Decisions 8–9 + ADR-0009).
