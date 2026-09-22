# Plan: Intent metadata shape contract and its two enforcement points

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py`
  (the sibling corpus-walking script this one sits beside, and the source of the
  refuse-rather-than-guess posture); `packs/core/tests/skills/work-intake/test_intent_ordinal.py`
  (its construction-test shape); `packs/core/.apm/agents/shaping-reviewer.md` with
  `packs/core/tests/pack/test_shaping_review_contract.py` (the pinned prose and
  the `INTENT_TOKENS` tuple the seventh condition edits).

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> execution observations belong in `notes/verification-ledger.md`.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material an implementer corrects in place before
> approval.

## Approach

One validator decides the contract, and both enforcement points read the same
rules from it — the corpus lint by walking a directory, the shaping reviewer by
reading one supplied preamble against prose that delegates the field list here
rather than restating it. Building the validator first means the vocabularies
have exactly one home before anything consumes them.

The order is forced in three places. The validator precedes both enforcement
points because they are its callers. The template work precedes the gate,
because a template that seeds a refused shape re-dirties the corpus at the next
admission. The gate lands last, because wiring a failing check into a route
before the corpus can pass it blocks everyone.

The riskiest part is not the validator — it is the reviewer edit. The intent
mode's tokens are pinned and its text says "Do not create a fourth mode"; a
seventh condition has to read as bounded and mechanical or it converts a
well-formedness reviewer into a schema gate, which is the failure the brief
names.

## Constraints

- **ADR-0033 D2** keeps `Level` an open string field and states that lint
  cannot enforce a closed set. The validator carries no `Level` vocabulary.
- **ADR-0098 D2** fixes `intake-intent`'s minimum contract. What it establishes
  here: owner and status are already required by decision, so this work changes
  where owner is written, not whether it is required.
- **ADR-0108 D3** and `docs/specs/intent-renumber-and-reissue/spec.md` own the
  partition rule and the tombstone field contract. This plan implements them and
  states neither.
- **`close-work/SKILL.md`** already distinguishes `Withdrawn` from `Cancelled`
  by execution evidence, and its evals pin that distinction. The `Status`
  vocabulary adopts those two names rather than inventing synonyms.
- **`docs/product/AGENTS.md`** gives status exactly one home. The lint reports a
  field's state; it writes no status anywhere.
- The shaping reviewer's frontmatter declares `tools: Read, Grep, Glob`. The
  seventh condition is decidable by reading, and nothing here widens that.

## Construction tests

**Integration tests:** one fixture corpus exercised through both enforcement
points in the same test module, so a rule that drifts between them fails rather
than passing twice against two copies.

**Manual verification:** the how-to walked end to end against one refusal of
each kind.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current product truth — both intent templates | T7 | Both renderers' output fed to the validator in test | Neither template seeds a refused shape |
| Interface compatibility — `intent-fields-and-modes.md` | T9 | The field table rewritten in the four tiers | Every field the validator decides on appears; no orphan rows |
| Maintainer procedure — `guides/product-engineering/how-to/` | T9 | A how-to per refusal kind | One real refusal of each kind resolved by following it |
| Release history — `docs/product/changelog.md` | T9 | One free-standing `## [<pack>][<version>]` entry per pack beneath `[Unreleased]` | Both entries under the versions this change sets |
| Reusable learning — `notes/verification-ledger.md` | T1, T3 | The measured field inventory and the three distinct `Authority` usages | The counts the Follow-ons rest on are recorded, all three `Authority` usages distinguished |

## Design (LLD)

### Data & schema

Traces to: AC-0001 – AC-0009, AC-0011, AC-0021 – AC-0023, AC-0025, AC-0034 ·
no
`contracts/` file (the
spec's `Contract:` is `none`).

Owned by: T1, T2, T3.

The contract is one table keyed by field name, carrying a tier and an optional
value rule. Four tiers: required, constrained-when-present, unconstrained,
retired. A field name absent from the table is accepted — that is what keeps
`Milestone:` and any future organic field passing while the six retired names
fail, and it is why AC-0009 needs both halves.

Value rules are of four kinds: membership in a closed set (`Kind`, `Scale`,
`Maturity`); membership-or-parameterized-form (`Status`, where `Superseded by
<slug>` carries a payload the bare values do not); a date-or-literal
shape (`De-risked`, `Shaping-reviewed`); and a date-plus-terminus shape
(`Decomposed`). `Level` has a tier and no value rule.

`Status` is a membership-or-parameterized-form rule: five bare values plus
`Superseded by ` with a slug payload. Its terminal values are peers of
`Fulfilled` rather than flavours of it.

Normalization runs once before every value rule, **comment first, then
backticks**. The order is load-bearing: the corpus's dominant commented shape
is backticked *and* commented on one line, and stripping backticks first
no-ops because the comment trails the closing backtick, leaving them attached.
A value empty after the stage is absent rather than malformed — that is the
`frame-intent` template's comment-only `Parent intent:`. Both templates seed their
placeholders backticked *and* commented — the comment is how an author learns
what a field means at the point of use — so a rule applied to the raw line
would refuse the shape the templates themselves produce. Every commented value
in the corpus is trailing, closed on its own line, with nothing after the
close, so the rule is exact rather than a best effort.

**The preamble is a bounded region, not a pattern.** It is the run of lines
before the first `## ` heading. The real corpus breaks a whole-file pattern
match in two distinct ways. A `- **Status:**` line can sit inside a de-risk
record body, where the value is a probe's narrative. A bolded
`- **Authority:**` line can sit inside a `## Source` block, where it is an
owner attribution rather than the governance pointer the preamble field holds;
unbolded in the same block it is a provenance token. The region boundary is the whole defence, and AC-0011 holds it.

`## Decomposition` is read only when `Decomposed:` resolves to the
`direct-light` terminus. Its items are checkbox lines; the text after the box is
the requested outcome, which is the unit `work-loop/SKILL.md:592` says a
direct-light run owes and which otherwise exists only in a session.

### Interfaces & contracts

Traces to: AC-0012 – AC-0018, AC-0026, AC-0027, AC-0028, AC-0030.

Owned by: T4, T5, T6, T7, T8.

Two consumers and one gate, over one rule table.

The **corpus lint** is a script beside `intent_ordinal.py`, taking a
repository-relative directory. It partitions each file to the live-intent or
tombstone contract before validating, so no file is skipped. Exit codes follow
the sibling allocator's posture: non-zero for any violation, and non-zero rather
than clean for a corpus it could not fully read. Boundary crossing is confined
by `agentbundle.catalogue_tooling.file_safety`, the blessed helper.

The **shaping reviewer** gains condition 7 and the token `MALFORMED(shape)`. The
condition names this spec as the field list's owner and enumerates nothing, so
the reviewer's text does not become a second copy of the table that can drift
from it. The existing suppression rule is load-bearing rather than incidental: a
preamble with no owner cannot settle condition 6, so `MALFORMED(owner)` is
emitted alone and condition 7 stays silent. That is why AC-0012 carries the
exception.

The **gate** is what makes a non-zero exit mean something. Without it AC-0014
fixes an exit code nobody invokes.

Owner moves from `## Owner` to an `Owner:` preamble field. ADR-0098 D2 requires
an owner and does not fix its position, so the renderer and template change and
the ADR does not.

## Tasks

### T1: The contract table and preamble reader decide every field rule

**Depends on:** none

**Tests:**
- A fixture whose preamble omits each of `Owner:`, `Slug:`, `Level:`,
  `Status:` in turn is refused, one case per field — AC-0001.
- Each bare `Status` value and the `Superseded by ` form is accepted, and an
  unlisted value refused,
  read from the same table the implementation uses rather than a second literal
  list — AC-0002.
- A fixture carrying an out-of-set value at each of `Kind:`, `Scale:`,
  `Maturity:` is refused, one case per field — AC-0022.
- A fixture whose `Level:` carries an unrecognized altitude is accepted —
  AC-0003.
- Each accepted value is re-asserted backticked — AC-0004.
- Each accepted value is re-asserted commented, and re-asserted backticked
  *and* commented on one line — the composed case, which an order-sensitive
  implementation fails and which dominates the real corpus — AC-0034.
- A value that is a comment and nothing else is absent, not malformed: the
  `frame-intent` template's `Parent intent:` line is that shape — AC-0034.
- Each of the six retired names is refused; `Milestone:` and one invented name
  are accepted — AC-0009, both halves.
- A preamble carrying two `Governed by:` lines is refused — AC-0025.
- Two body-level fixtures neither satisfy nor violate their field: a
  `- **Status:** Run 2026-09-09; killed on …` line below the first `## `
  heading, and a bolded `- **Authority:** eugenelim, lifecycle owner` inside a
  `## Source` block — AC-0011.

**Approach:**
- The fixture corpus is authored here and every later task reuses it, so a rule
  change has one place to break rather than five.

**Done when:** the tests above are green.

### T2: The progress fields and the direct-light decomposition are decided

**Depends on:** T1

**Tests:**
- `De-risked:` and `Shaping-reviewed:` accept an ISO 8601 date and the literal
  `no`, and refuse any other value — AC-0005.
- For each of the three progress fields, the report distinguishes absence from
  `no`, and a corpus whose only irregularity is absence exits zero — AC-0023.
- `Decomposed:` accepts `no` and a date with each of the four termini, and
  refuses a date with no terminus, two termini, and an unlisted terminus —
  AC-0006.
- A `direct-light` intent with an empty `## Decomposition`, and one with the
  section absent, are both refused — AC-0007.
- A checkbox item whose text is empty or whitespace is refused; the other three
  termini leave `## Decomposition` unread — AC-0008.

**Done when:** the tests above are green.

### T3: A superseding slug resolves or the intent is refused

**Depends on:** T1

**Tests:**
- The lint refuses a `Superseded by` slug equalling no live intent's `Slug:`
  value, naming both — AC-0021.
- The comparand is the normalized `Slug:` value: a fixture whose target slug is
  written backticked and commented still matches, which is the corpus's
  dominant `Slug:` shape and the case an unnormalized comparison fails.

**Approach:**
- Pointer *form* and *resolution* for `Governed by:` and `Parent intent:` are
  `intent-reference-grammar-migration`'s, per the brief's canonical grammar
  decision. Nothing here reads a pointer's target.

**Done when:** the tests above are green.

### T4: The corpus lint reports and exits

**Depends on:** T1, T2, T3

**Tests:**
- Every non-conforming intent in a mixed fixture corpus is named together with
  its offending field; a corpus with two faults reports both rather than the
  first — AC-0013.
- Exit is non-zero for any violation, and zero for a clean corpus — AC-0014.
- A corpus containing an unreadable file exits non-zero and does not report
  clean — AC-0015.
- Every file in the fixture directory is routed to exactly one contract, and a
  tombstone fixture is validated against the sibling spec's three-field
  contract rather than skipped — AC-0017.

**Approach:**
- Confinement goes through `agentbundle.catalogue_tooling.file_safety`; an
  `UnsafeContentError` is an unreadable corpus, which is AC-0015's path, not a
  crash.

**Touches:** packs/core/.apm/skills/work-intake/scripts/, packs/core/tests/skills/work-intake/

**Done when:** the tests above are green and the lint runs against a fixture
directory from the repository root.

### T5: The shaping reviewer emits the seventh token

**Depends on:** T1

**Tests:**
- `INTENT_TOKENS` in `packs/core/tests/pack/test_shaping_review_contract.py`
  gains `MALFORMED(shape)` — AC-0012.
- The six existing tokens are unchanged in that tuple — AC-0027.
- A preamble failing a packet-decidable criterion emits `MALFORMED(shape)`; a
  preamble missing `Owner:` emits `MALFORMED(owner)` alone — AC-0012.
- A preamble satisfying every packet-decidable criterion emits no
  `MALFORMED(shape)` — AC-0026.
- No site in the text states a condition count, and the suppression sentence
  suppresses every other condition rather than a fixed set — AC-0030. The
  sentences carrying a count are intent mode's "six conditions, each decidable
  by reading" opener, the `MALFORMED(owner)` suppression sentence, and the
  "six conditions are the whole of its rubric" sentence under `## Known
  failure modes in delivery-brief and spec mode`; each is rewritten.
- The pinning suite moves with the prose: `test_shaping_review_contract.py`
  asserts the literal `"suppresses the other five"` and names a test for the
  condition count.

**Approach:**
- A renamed test can trip the repository's test-name-set hash, so check that
  guard before renaming rather than after.
- Condition 7 states its rule directly rather than citing this spec, because
  `packs/AGENTS.md` forbids shipped pack content from citing a repository-only
  path. It names the required fields and asserts vocabulary membership without
  enumerating the vocabularies, which keeps the member lists in one home. A reviewer carrying its own copy
  of the field table is a second home that drifts from T1's, and the brief's
  tension is precisely about the reviewer's scope growing.

**Touches:** packs/core/.apm/agents/shaping-reviewer.md, packs/core/tests/pack/test_shaping_review_contract.py

**Done when:** the pack suite covering the reviewer contract is green.

### T6: Neither enforcement point substitutes for the other

**Depends on:** T4, T5

**Tests:**
- One fixture passes the corpus lint and fails the shaping review on one of the
  review's other six conditions, asserted in one module against one fixture
  corpus — AC-0016.

**Approach:**
- Co-locating the assertion with T1's corpus is the point: separate modules let
  one rule drift and both suites stay green, which is the failure AC-0016 exists
  to catch.

**Done when:** the assertion is green.

### T7: Both packs' templates emit a conforming preamble

**Depends on:** T1, T2

**Tests:**
- `intake-intent`'s renderer output is fed to the validator and accepted,
  including the authority modes that change the rendered body — AC-0018.
- `frame-intent`'s template with every placeholder resolved to a representative
  value is accepted, and the unresolved asset is not corpus input — AC-0018.
- The existing `intake-intent` admission suite stays green, with its
  confinement, provenance and authority-transfer assertions unedited — that is
  how the ADR-0098 D2 controls are evidenced as preserved rather than
  re-specified. Two of its assertions move with the contract and only those
  two: the pin on `level`'s optional default, which ADR-0121 D3 removes, and
  the `## Owner` heading, which becomes a preamble field. Editing any other
  assertion in that suite is out of contract.

**Approach:**
- Owner moves into the preamble here, so the renderer's `## Owner` section and
  the template token change together with the validator already able to judge
  the result.

**Touches:** packs/core/.apm/skills/intake-intent/assets/minimal-intent.md, packs/core/.apm/skills/intake-intent/scripts/intent_renderer.py, packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md

**Done when:** both renderers' output validates and the admission suite is green.

### T8: The lint runs somewhere that fails

**Depends on:** T4, T7, T10

**Tests:**
- The gate fails when the lint exits non-zero over `docs/product/intents/` —
  AC-0028.

**Approach:**
- The gate lands after the templates so the first thing it guards is a shape
  both packs can already produce. Which gate it is, is a repository-local
  placement decision recorded here at execution; the criterion fixes that one
  exists and that it fails, not which file it lives in.

**Done when:** the gate fails on a seeded violation in the real directory and
passes once it is removed.

### T9: The adopter-visible surfaces describe the contract

**Depends on:** T1, T2, T3

**Tests:**
- Goal-based: every field the validator decides on appears in
  `intent-fields-and-modes.md`, and every field row there is one the validator
  knows — a two-way check, so neither a new field nor a deleted one leaves the
  page stale.
- Manual QA: the how-to is followed out of one refusal of each kind.

**Approach:**
- One new ADR, and only one. ADR-0121 supersedes ADR-0098 D3 in part: D3 fixes
  `level` as optional enrichment while AC-0001 requires it on every live
  intent, and `intake-intent` writes into the directory AC-0028's gate guards,
  so admission would otherwise produce an intent the gate rejects. RFC-0102
  fixes the instrument — an accepted record's body is frozen and "anything else
  is a *new* ADR that supersedes", and an erratum records an error rather than
  a changed decision. ADR-0111 still takes its erratum, and the field
  contract's own decision record stays deferred — see the spec's `Follow-ons`.

**Touches:** guides/product-engineering/reference/intent-fields-and-modes.md, guides/product-engineering/how-to/, docs/product/changelog.md

**Done when:** the parity check is green and the how-to resolves one refusal of
each kind.

### T10: The corpus satisfies the contract

**Depends on:** T1, T2, T3

**Tests:**
- Every packet-decidable criterion, and AC-0021, refuse
  nothing across every file in `docs/product/intents/` — AC-0033.
- Every `Status:` and `Authority:` line below the first `## ` heading is
  byte-identical before and after — the constraint a whole-file pattern match
  breaks.

**Approach:**
- Four script-driven passes, each verified by re-running the criteria rather
  than by review: required fields and retired names; the `Authority:` rename,
  merging any file carrying the field more than once; evidence-backed
  `Parent intent:` edges; and terminal `Status:` values. No pass infers a value it cannot evidence.

**Touches:** docs/product/intents/

**Done when:** the criteria refuse nothing over the real directory and the
ledger records the before and after counts.

## Rollout

- **Delivery:** reversible. The lint is a new script and the gate is one
  invocation, so backing both out is a revert.
- **Deployment sequencing:** templates (T7) before the gate (T8), because a
  template seeding a refused shape re-dirties the corpus at the next admission.
  T10 brings the corpus onto the contract before T8 points a gate at it.
- **Infrastructure and external systems:** none.

## Risks

- **The reviewer edit is the one that can go wrong quietly.** Condition 7 reads
  as bounded in review and grows in use, because "the preamble satisfies the
  contract" invites a reviewer to reason about field *quality*. The mitigation
  is that the condition enumerates nothing and names an owner; the residual is
  that prose cannot force that reading.
- **T10 rewrites the whole corpus, and a mistake below a `## ` heading is
  invisible.** Body-level `Status:` and `Authority:` lines share their names
  with preamble fields, so a whole-file pattern match corrupts them. Every pass is script-driven and verified by re-running
  the criteria over the corpus, not by reading diffs.
- **Moving owner into the preamble touches the admission transaction's
  neighbourhood.** The renderer change is small, but `intake-intent`'s
  confinement, provenance and authority-transfer controls are in the same
  module. T7 re-runs their suite unamended rather than editing it.

## Changelog

- 2026-09-21: spec approved by eugenelim
- 2026-09-21: plan approved by eugenelim
- 2026-09-21: contract amended by eugenelim — ADR-0121 supersedes ADR-0098 D3
  in part so `Level` is required, lifting this plan's "No new ADR"; AC-0017
  drops its cross-spec criterion numbers; the routing Follow-on is recorded as
  settled
- 2026-09-21: spec approved by eugenelim (post-amendment)
- 2026-09-21: plan approved by eugenelim (post-amendment)
- 2026-09-21: contract amended by eugenelim — T7's Tests restated because
  ADR-0121 D3 makes an unamended admission suite impossible, naming the two
  assertions that may move and forbidding any other; T9's Touches rehomed to
  `docs/product/changelog.md`
- 2026-09-21: plan approved by eugenelim (second amendment)
