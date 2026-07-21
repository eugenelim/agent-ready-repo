# Plan: author-brief-docs

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Four files change; all are docs under `docs/guides/core/`. T1 writes the new how-to guide (the bulk of the work). T2 patches three existing files — the `product-brief-fields.md` reference (fixes stale attribution + adds `Rabbit holes`/`Status` rows to the table + adds DoR gate section), the `receive-brief` how-to (adds `author-brief` row to its decision table), and the README. Both tasks conform to `author-brief` SKILL.md as the source of truth; they can land in one PR.

All verification is goal-based grep + a final manual read-through of the how-to to confirm it is followable without consulting SKILL.md.

## Constraints

- RFC-0064 P3 phase-slice doctrine: tooling already shipped; docs ride with the capability.
- Diátaxis conventions per `docs/CONVENTIONS.md § 5c`: how-to is task-oriented (recipes for a problem you already have); reference is information-oriented (dry, complete field definitions). Mixing kinds is the failure mode; don't let the how-to become a reference or vice versa.
- `author-brief` SKILL.md is the source of truth. If the guide disagrees with the skill, the skill wins — this spec does not change the skill.

## Construction tests

**Integration tests:** none
**Manual verification:** (1) read `how-to/intake-an-external-brief.md` from top to bottom without consulting SKILL.md; assert: (1.1) decision table names all three skills with distinct triggers, (1.2) all six flow steps are present, (1.3) all three `workspace.toml` branch outcomes are named, (1.4) the boundary sentence contains both "stops at draft" and "decompose" (or equivalent), (1.5) Next-step link is present. (2) read `reference/product-brief-fields.md`; assert: (2.1) opening paragraph and callout no longer attribute brief creation solely to `receive-brief` and name both skills correctly, (2.2) body-sections table has `Rabbit holes` and `Status` rows, (2.3) DoR gate section names all four eligibility fields (Outcome, Appetite, Rabbit holes ≥1, Spec map skeleton ≥1 placeholder row), (2.4) DoR gate section states `author-brief` sets `Status: Draft` and `receive-brief` sets `Status: Ready`.

## Tasks

### T1: Write `how-to/intake-an-external-brief.md`

**Depends on:** none

**Tests:**
- `ls docs/guides/core/how-to/intake-an-external-brief.md` exits 0 (AC1)
- `grep -i "author-brief\|receive-brief\|new-spec" docs/guides/core/how-to/intake-an-external-brief.md` returns hits — backstop only; full decision-table assertion in manual (1.1) (AC2)
- `grep -i "rabbit holes" docs/guides/core/how-to/intake-an-external-brief.md` returns hits; `grep -i "appetite" ...` returns hits; `grep -i "outcome" ...` returns hits — three independent greps, each individually required; full six-step flow asserted in manual (1.2) (AC3)
- `grep -i "workspace\.toml" docs/guides/core/how-to/intake-an-external-brief.md` returns hits; `grep -i "diagnostic" docs/guides/core/how-to/intake-an-external-brief.md` returns hits; `grep -i "multiple.*initiative\|select" docs/guides/core/how-to/intake-an-external-brief.md` returns hits — covering all three branch outcomes (AC3 — workspace.toml branches)
- `grep -i "stops at draft" docs/guides/core/how-to/intake-an-external-brief.md` returns hits (first half); `grep -i "decompose" docs/guides/core/how-to/intake-an-external-brief.md` returns hits (second half) — two independent greps, both required (AC4)
- `grep -i "receive-a-product-brief" docs/guides/core/how-to/intake-an-external-brief.md` returns the Next-step link (AC5)

**Approach:**
- Create `docs/guides/core/how-to/intake-an-external-brief.md`.
- Open with a "Is `author-brief` the right entry point?" decision table: `author-brief` (unstructured external input → draft brief), `receive-brief` (already-formed multi-feature brief → decompose into specs), `new-spec` (single feature, authoring from scratch). Each row names a distinct trigger so a reader picks the right skill without reading both SKILL.md files.
- Walk the six steps drawn directly from `author-brief` SKILL.md as the source of truth: (1) ingest whatever you have, (2) identify which DoR fields are present/missing, (3) elicit — Outcome is required; Appetite defaults offered; Rabbit holes gap surfaced (≥1 required for DoR), (4) confirm the slug, (5) brief file created and queued in `workspace.toml` — name all three branch outcomes: happy path appends to `brief_queue.draft`; no/unparseable `workspace.toml` → file-only + named diagnostic; multiple active initiatives → user is prompted to select, (6) handoff to `receive-brief`.
- Include a concrete "Before you start" block (the `core` pack installed; any unstructured input; no form needed).
- Name the `author-brief` / `receive-brief` boundary explicitly: "`author-brief` stops at draft — it creates the file and elicits the DoR fields but does not decompose the brief into specs. Use `receive-brief` for that."
- End with a "Next step" sentence: "When you're ready to decompose the brief into specs, run `receive-brief` — see [Receive a product brief and decompose it into specs](receive-a-product-brief-and-decompose-it-into-specs.md)."

**Done when:** AC1–AC5 pass and the manual read-through asserts (1.1)–(1.5) from the Construction tests section above.

### T2: Patch existing docs — attribution fix + DoR gate section + decision table + README

**Depends on:** none (both tasks conform to SKILL.md as source of truth; T1 is ordered first for readability but T2 touches different files)

**Tests:**
- `! grep -q "created by the.*receive-brief.*skill" docs/guides/core/reference/product-brief-fields.md` exits 0 after the attribution fix (negative check — the stale phrase is gone) (AC7)
- `grep -i "rabbit holes" docs/guides/core/reference/product-brief-fields.md` returns hits — currently absent in the file, so a true discriminating check (AC6 — table row)
- `grep -i "DoR gate\|required to reach" docs/guides/core/reference/product-brief-fields.md` returns hits for the new section (AC6 — gate section); `grep -i "spec map" docs/guides/core/reference/product-brief-fields.md` returns hits confirming all four eligibility fields named; `grep -i "status.*draft\|status.*ready" docs/guides/core/reference/product-brief-fields.md` returns hits for Draft/Ready split statement; full DoR gate section assertions in manual (2.3) and (2.4) (AC6)
- `grep -i "author-brief" docs/guides/core/how-to/receive-a-product-brief-and-decompose-it-into-specs.md` returns a row in the decision table (AC8)
- `grep -i "intake-an-external-brief" docs/guides/core/README.md` returns the listing entry (AC9)

**Approach:**
- `docs/guides/core/reference/product-brief-fields.md`:
  1. Fix the opening paragraph (line 3) and callout (line 5): replace "A brief ... is created by the `receive-brief` skill" with language reflecting the two-skill split — `author-brief` creates the draft brief and elicits DoR fields; `receive-brief` decomposes it into specs and marks it Ready. Fix the callout: "`receive-brief` elicits what's missing" → "`author-brief` elicits missing DoR fields when authoring from unstructured input; `receive-brief` elicits what's missing when receiving a formed brief."
  2. Add `Rabbit holes` and `Status` rows to the body-sections table. `Rabbit holes`: optional in general use, but required-for-Ready per DoR gate. `Status`: the lifecycle field set by the skill (`Draft` by `author-brief`; `Ready` by `receive-brief`).
  3. Add a "DoR gate" section after the body-sections table defining the four eligibility fields (Outcome, Appetite, Rabbit holes ≥1, Spec map skeleton ≥1 placeholder row), framing them as "required to reach `Ready`" (not simply "required"), and stating that `author-brief` elicits these but sets `Status: Draft` only; only `receive-brief` sets `Status: Ready`.
- `docs/guides/core/how-to/receive-a-product-brief-and-decompose-it-into-specs.md`: in the entry-point decision table, add row: `author-brief` | "You have unstructured external input (email, stakeholder message, Linear issue) and need to author a brief from scratch first".
- `docs/guides/core/README.md`: add `[Intake an external brief into a product brief](how-to/intake-an-external-brief.md)` under the How-to section.

**Done when:** AC6–AC9 pass.

## Rollout

Pure documentation change; no code, no infra, no migration. Ships as a normal PR.

## Risks

None material — docs-only, no backwards-incompatible change.

## Changelog

- 2026-07-21: initial plan
