---
title: Annotate the frozen documents that actually relied on a superseded decision
slug: frozen-doc-supersession-annotations
---

# Spec: frozen-doc supersession annotations, decided per document

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** none — see § Named deviation
- **Mode:** full (governance surface — it applies `docs/CONVENTIONS.md`
  § *Superseding a frozen document* to eight frozen documents, and the rule it
  applies is convention-enforced, not machine-enforced. A reviewer is the only
  thing standing between a supersession and a wrong one.)
- **Constrained by:**
  [`frozen-spec-supersession`](../frozen-spec-supersession/spec.md)
  (the mechanism and the survey this closes);
  [ADR-0040](../../adr/0040-route-cohort-skills-to-shared-agents-skills-home.md)
  (the supersession being recorded);
  [ADR-0042](../../adr/0042-agent-additions-keyed-to-loop-and-work-type.md) and
  [ADR-0084](../../adr/0084-nosec-reason-delimiter-and-stderr-as-a-gate.md)
  (the two supersessions found **not** to warrant an annotation)
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Named deviation from full mode

The `loop-engine` / `loop-cohort` state machine was not run, and there is no
`plan.md`. The two human approval gates it sequences — **spec-approved** and
**plan-approved** — were **granted up front by the requester**, as a standing
instruction to carry this through to merge. The merge decision itself was
explicitly retained. `adversarial-reviewer` was run. Same deviation shape as
`frozen-spec-supersession`, the spec this closes.

## Objective

`frozen-spec-supersession` wrote down how a frozen document records that a later
decision reversed part of it, applied it to one spec directory, and surveyed the
rest without touching them — because the rest are **not** a mechanical rewrite.
Its § Survey says so plainly: *"citing ADR-0017 does not mean a spec teaches the
reversed spelling."*

This spec is the judgment pass that survey deferred, plus one adjacent
application of the same mechanism (`bandit-nosec-comment-hygiene`'s § Known
skip, whose register pointer was closed out from under it).

The deliverable is mostly a decision, and mostly a decision **not** to annotate.
Of eighteen frozen specs citing a superseded ADR, three get a pointer.

## Decision 1 — the test is "does the body teach the superseded sub-decision", not "does it cite the ADR"

`Constrained by:` is a weak signal. A spec cites the ADR that governed it, which
is usually the ADR's *standing* half. The question the convention actually asks
is whether *"a reader who starts there [is] left following a rule we no longer
keep"* — so the test is applied to the body:

> **Annotate when the document's body states the superseded sub-decision as an
> operative rule.** Leave it alone when the citation is a bare `Constrained by:`
> reference, or when the body states the part that still stands.

Applied below to all three supersession chains. Each verdict is measured against
the tree, not read off a docstring — the method is in § Testing Strategy.

## Decision 2 — ADR-0017 → ADR-0084: annotate none

ADR-0084 supersedes the **reason-delimiter spelling** in ADR-0017's
suppression-policy sub-decision, and nothing else.

A scan of `docs/`, `packs/`, `guides/`, `tools/` and `.github/` for the reversed
form — matching the placeholder spelling as well as a literal `Bnnn`, which a
`Bnnn`-only pattern misses — finds it in exactly six files, in three kinds:

| File | Kind |
| --- | --- |
| `docs/adr/0017-*.md`, `docs/adr/0084-*.md` | Quoted while recording the amendment / the reversal |
| `docs/specs/bandit-nosec-comment-hygiene/spec.md` | Quoted while recording the reversal it implements |
| `docs/specs/bandit-nosec-form-lint/spec.md` AC2 | Quoted to assert the form *fails* the new lint |
| `tools/test-lint-nosec-form.py` | Two test fixtures asserting the same |
| `docs/specs/sast-sca-tooling/spec.md` + `plan.md` | **Taught as the rule — and already annotated** by `frozen-spec-supersession` |

Only the last row teaches it, and it is already done. Ten specs cite ADR-0017 in
`Constrained by:` without a pointer; **none of them teaches the spelling.** They
cite it for the gate itself — the tool choices, the severity floor, the
real-fix-first ladder — every one of which ADR-0084 explicitly leaves standing.
Stamping ten specs with "superseded in part" over a sub-decision none of them
states is precisely the false positive `frozen-spec-supersession` § Boundaries
names as *worse than silence*.

(`frozen-spec-supersession` § Survey put this at "four locations". Counting by
file rather than by directory, and including `bandit-nosec-form-lint` and the
test fixtures — both of which post-date or were omitted from that scan — gives
six. Same conclusion.)

## Decision 3 — ADR-0023 → ADR-0042: annotate none

This one looks like the strongest candidate and is the weakest, because
ADR-0023's Status reads `Superseded by ADR-0042` without an "in part" — so a
mechanical reading would annotate all three citing specs.

ADR-0042 says what it kept: *"keeps this ADR's core holding (the ceiling binds
the core code-review gate) and generalizes the rest."* All three citing specs
rely on that core holding and only on it:

| Spec | What it says | Verdict |
| --- | --- | --- |
| `architect-design-reviewer` | `Constrained by: RFC-0032, ADR-0023`; the body never restates the ceiling | Bare citation → no annotation |
| `infra-grounding` | § Never do: *"Add a fourth reviewer or a dedicated `infra-contract-reviewer` (three-reviewer ceiling; ADR-0023)"* | A **core** work-loop reviewer, which ADR-0042 still binds → no annotation |
| `operational-safety-checklists` | *"depth … without a fourth reviewer (ADR-0023)"*; *"`quality-engineer` remains the consumer; no new reviewer is added"* | Same → no annotation |

Under ADR-0042 the answer to all three is unchanged: the ceiling still binds the
core work-loop code-review gate, so none of these specs would decide differently
today. What ADR-0042 generalized is the treatment of *non-core* agents, which is
not what any of them relied on.

`frontend-engineering-skill` also cites ADR-0023 and already carries a
`Superseded in part` annotation — for an unrelated reason (ADR-0057 deleting a
file). No second annotation is added.

## Decision 4 — ADR-0013 / 0015 / 0016 → ADR-0040: annotate three

ADR-0040 supersedes the **skill-home sub-decision** of those three ADRs, and
nothing else. Unlike the other two chains, the implementing specs state the
superseded sub-decision as an *acceptance criterion*:

- `cursor-full-parity` **AC7** — *"`skill` projects via `direct-directory` to
  `.cursor/skills/<name>/`"*
- `gemini-full-parity` **AC2** — *"projects `skill` → `direct-directory`
  `.gemini/skills/<name>/`"*
- `copilot-skills-and-web` — *"copilot `skill` mode is `direct-directory` →
  `.github/skills/`"*, with `.copilot/skills/` at user scope

`contracts/adapter.toml` today routes `skill` to `.agents/skills/` for all three
adapters. Each spec is a document whose ACs assert a filesystem shape the repo
no longer produces. That is exactly the reader the convention protects.

Their `plan.md` files teach the same homes and are `Done`, so both halves of
each directory get the annotation, per `CONVENTIONS.md` § *A spec directory
freezes as a unit*.

**`copilot-full-parity` is deliberately excluded.** Its skill decision — an
`instruction-file` to `.github/instructions/` — is *already* marked reversed by
a body banner at the top of the file that forwards the reader to
`copilot-skills-and-web`, which is where this change's ADR-0040 pointer lands.
The chain works: a reader is not left following a rule we no longer keep. A
second pointer on a decision already flagged as reversed is noise, and would
require deciding which of two supersessions the Status line names.

## Decision 5 — the Known-skip pointer uses the same carrier, but is not a supersession

`bandit-nosec-comment-hygiene/spec.md` § Known skip records a `make ci` failure
and anchors it to `pre-existing-guides-readme-outcome-label-drift` in
`workspace.toml [backlog].open`. That entry was closed by
[`guides-readme-outcome-label-drift`](../guides-readme-outcome-label-drift/spec.md);
the prose pointer now names nothing. `lint-spec-status.py` invariant (iv) checks
only `(deferred: <slug>)` markers, so nothing catches it.

The mechanism is the same — the **Status field is the carrier, the body is not
touched** — but two of the convention's four rules do not apply and saying so is
part of applying it:

- **Rule 1 ("say in part") does not fit.** Nothing about this spec was
  superseded. The annotation says what actually happened: a register anchor
  closed.
- **Rule 2 ("point at the ADR") has no ADR to point at.** No decision was
  reversed; a backlog entry was worked. The pointer therefore names the spec
  that closed it, which is the only record there is.

Rules 3 and 4 hold unchanged: the pointer is one-way (spec → the closing spec,
which does not point back), and no body line moves.

## Acceptance Criteria

- [x] **AC1 — three spec/plan pairs carry an ADR-0040 pointer.**
      `cursor-full-parity`, `gemini-full-parity` and `copilot-skills-and-web`
      each have `spec.md`'s `Shipped` and `plan.md`'s `Done` annotated
      `(superseded in part by [ADR-0040](…) — <the skill home this document
      pins> now routes to the shared `.agents/skills/`; every other projection
      decision stands)`, linking the ADR.

- [x] **AC2 — no body line changes in any annotated document.**
      `git diff` on the six files touches only the `- **Status:**` line of each.
      Verified by asserting the diff's changed-line set is exactly six lines,
      not by reading it.

- [x] **AC3 — the twelve declined cases are recorded, not silently skipped.**
      § Decision 2 and § Decision 3 name every spec examined and the reason each
      was left alone. `frozen-spec-supersession`'s § Survey listed twelve rows;
      the true figure and the reason for the difference are stated in
      § Survey correction.

- [x] **AC4 — the ADR-0017 verdict is measured, not assumed.** A repository-wide
      scan for the reversed suppression form — a pattern admitting the `<ID>`
      placeholder, not only a literal `Bnnn` — reports exactly the six files
      named in § Decision 2, and the only one that *teaches* the form is
      `sast-sca-tooling`, already annotated.

- [x] **AC5 — the ADR-0040 verdict is measured, not assumed.**
      `contracts/adapter.toml` is parsed with `tomllib` and each of the
      `cursor`, `gemini`, `copilot` adapters' `skill` projection is confirmed to
      target `.agents/skills/` — i.e. the ACs those three specs pin are
      genuinely stale.

- [x] **AC6 — the Known-skip pointer is annotated.**
      `bandit-nosec-comment-hygiene/spec.md`'s Status records that
      `pre-existing-guides-readme-outcome-label-drift` was closed and names the
      spec that closed it. No body line changes. (It has no `plan.md`.)

- [x] **AC7 — every annotated status still parses.** `parse_status` from
      `lint-spec-status.py`, imported and run against each of the four **edited
      `spec.md` files**, returns exactly `Shipped` — confirmed by construction,
      not inferred from the docstring — and
      `lint-spec-status.py --root . --base-ref origin/main` exits 0.

- [x] **AC8 — gates pass.** `python3 tools/lint-ruff.py`, `make lint-mypy`,
      `SKIP_SAST=1 make build-check`, and `make sast` all exit 0.

- [x] **AC9 — both register entries are closed.**
      `frozen-spec-supersession-survey` and
      `bandit-hygiene-known-skip-dangling-pointer` are removed from
      `workspace.toml [backlog].open`, verified with `tomllib`.

## Survey correction

`frozen-spec-supersession` § Survey's table lists **twelve rows over eleven
distinct specs** (`operational-safety-checklists` appears twice, under two
different ADRs). Re-running the same `Constrained by:`-scoped scan today finds
**eighteen** specs citing a superseded ADR, **sixteen** of them without a
pointer. The five it does not list:

| Spec | Cites | First commit | Why the survey missed it |
| --- | --- | --- | --- |
| `bandit-nosec-comment-hygiene` | ADR-0017 | 2026-08-16 | Shipped in the same batch |
| `build-check-single-verify` | ADR-0017 | 2026-08-16 | Shipped in the same batch |
| `compare-bandit-suppressions` | ADR-0017 | 2026-08-16 | Shipped in the same batch |
| `core-path-confinement` | ADR-0017 | 2026-08-11 | Predates the survey — missed |
| `pack-script-root-boundary-validation` | ADR-0017 | 2026-08-07 | Predates the survey — missed |

All five cite ADR-0017 and none teaches the reversed spelling, so § Decision 2
disposes of them and **the outcome is unchanged**. The count is corrected here
rather than quietly carried, because a survey that under-reports is worth
knowing about even when its conclusion holds.

`bandit-nosec-comment-hygiene` deserves one further note: its `Constrained by:`
already names ADR-0084 inline as the record of the reversal, so it carries a
forward pointer already — just not on the Status line. It is also the
implementing spec *for* ADR-0084. Annotating it "superseded in part by ADR-0084"
would be nonsense. (Its Status *is* annotated by this change, for the unrelated
Known-skip reason in § Decision 5.)

## Boundaries

### Always do

- Always decide per document whether the body states the superseded
  sub-decision, and record the verdict for the ones left alone.
- Always keep the annotation on the `Status` line and nowhere else.

### Ask first

- Ask before annotating a document whose superseded sub-decision it may not
  actually rely on. A false "superseded in part" is worse than silence
  (`frozen-spec-supersession` § Boundaries).

### Never do

- Never edit the body of a frozen document, including an "additive" append.
- Never introduce a `Superseded` status token; the vocabulary is closed.
- Never treat a `Constrained by:` citation as evidence of reliance on its own.

## Testing Strategy

Goal-based; every verdict is measured.

| AC | How |
| --- | --- |
| AC1, AC6 | Read the six + one edited Status lines. |
| AC2 | `git diff --unified=0 main...HEAD -- <the seven files>`; assert every changed line begins `- **Status:**`. |
| AC3 | Present in this document. |
| AC4 | `grep -rnE 'nosec +(<ID>\|B[0-9]+)([, ]+B[0-9]+)* *[-–—] ' docs/ packs/ guides/ tools/ .github/`; compare the hit set with § Decision 2's table. A `B[0-9]+`-only pattern silently misses both ADRs, which write the placeholder — that near-miss is why the pattern is pinned here. |
| AC5 | `tomllib.load('contracts/adapter.toml')`; assert the `skill` projection target for `cursor`, `gemini`, `copilot`. |
| AC7 | Import `lint-spec-status.py` by path; call `parse_status` on each edited `spec.md`; assert `== "Shipped"`. Then the linter, exit 0. |
| AC8 | The four gate commands. |
| AC9 | `tomllib.load('workspace.toml')`; assert neither slug is present. |

No new test file. These are one-off document edits against a
convention-enforced rule; a test asserting that a particular spec carries a
particular Status string would pin prose and break on the next legitimate
rewording. `lint-spec-status.py` invariant (i) is the standing machine check and
already covers the thing a machine can check — that the token still parses.

## Honest scope

- **Thirteen frozen specs cited a superseded ADR and are left untouched.** That
  is the deliverable, not an omission — but it rests on a judgment a reviewer
  should re-derive rather than accept. § Decision 2 and § Decision 3 are
  written to be re-attacked.
- **The residual the convention already accepts still stands.** Someone who
  greps mid-file in an annotated spec lands on the stale AC with no pointer in
  view. `CONVENTIONS.md` rule 4 states this and accepts it; the mitigation is
  that the operative rule lives in a Living file (`contracts/adapter.toml`),
  not that the frozen record gets patched.
- **Nothing here is machine-enforced.** `lint-spec-status.py` checks the status
  token's vocabulary and nothing else. A wrong annotation would pass every gate.
