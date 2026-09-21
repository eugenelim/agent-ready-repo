# Spec: Intent metadata shape contract and its two enforcement points

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0033; ADR-0098; ADR-0108; ADR-0111; ADR-0121
- **Brief:** docs/product/briefs/intent-identity-and-registration.md
- **Discovery:** docs/product/intents/FEAT-0001-intent-identity-and-registration.md
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

Anyone reading an intent's preamble learns who owns it, what altitude it sits
at, where it stands in its lifecycle, and whether it has been de-risked,
reviewed and decomposed — without opening the body. A preamble that does not
carry those facts is refused when the intent is ratified and named when the
corpus is linted.

## What Changes

- One intent shape, replacing two. `intake-intent` in `packs/core` and
  `frame-intent` in `packs/product-engineering` share exactly one preamble
  field today, `Level:`; both converge on the field set below
- Owner moves from a `## Owner` body section into an `Owner:` preamble field —
  the core renderer and its template
- `Status:` gains the terminal values — an intent that stopped, or that was
  replaced, can say so
- Three shaping-progress fields that do not exist today — `De-risked:`,
  `Shaping-reviewed:`, `Decomposed:` — in both templates
- `## Decomposition` becomes structured when the decomposition terminates in
  direct-light work, so the intent carries each item's requested outcome
- The preamble `Authority:` field becomes `Governed by:`, leaving core's two
  `## Source` usages of that name alone
- A corpus lint over `docs/product/intents/`, shipping in `packs/core` beside
  the ordinal allocator — `packs/core/.apm/skills/work-intake/scripts/`
- The gate that runs it, so a non-zero exit fails something
- The corpus itself — every intent brought onto the contract, so the gate
  guards a directory that passes
- A seventh condition and token in the shaping reviewer's intent mode —
  `packs/core/.apm/agents/shaping-reviewer.md`
- An erratum on ADR-0111 recording that the intent mode's condition count is
  delivery-owned — `docs/adr/`
- The adopter-visible field documentation —
  `guides/product-engineering/reference/intent-fields-and-modes.md`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — four new field names (`Owner:` in preamble position, `De-risked:`, `Shaping-reviewed:`, `Decomposed:`), six retired, and three new `Status` values | `guides/product-engineering/reference/intent-fields-and-modes.md` | eugenelim | The field table restated as required / constrained-when-present / unconstrained / retired, replacing "Only Outcome and Opportunity are load-bearing; the rest are offered, never required" | The page describes every field the lint decides on, and no field the lint decides on is absent from it |
| Maintainer procedure | Applicable — an author hitting `MALFORMED(shape)` or a lint failure needs to know which field and what value | `guides/product-engineering/how-to/` | eugenelim | A how-to naming each refusal and its remedy | The page resolves one real refusal of each kind end to end |
| Release history | Applicable — the lint, the templates and the reviewer condition ship inside `packs/core` and `packs/product-engineering` | each pack's `CHANGELOG.md` | eugenelim | One entry per pack | Entries present under the released versions |
| Current product truth | Applicable — both packs' intent templates seed the old shape | `packs/core/.apm/skills/intake-intent/assets/minimal-intent.md`, its renderer, and `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md` | eugenelim | Both templates emit a preamble the lint accepts | Neither template seeds a shape the lint refuses |
| Reusable learning | Applicable — the field inventory and the three distinct `Authority` usages were measured, and the criteria rest on those counts | `docs/specs/intent-metadata-shape-contract/notes/verification-ledger.md` | eugenelim | The measured per-field counts; the two-writer divergence; and the three `Authority` usages — a bolded preamble governance pointer, a bolded `## Source` owner attribution, and an unbolded `## Source` provenance token | The ledger records the per-field inventory, the two-writer divergence, and all three `Authority` usages distinguished |
| Current architecture | Not applicable — the lint ships inside an existing skill's script directory and adds no module boundary | — | — | — | — |

## Agent Rules

### Always do

- Cite `docs/specs/intent-renumber-and-reissue/spec.md` for the tombstone
  partition rule and the tombstone field contract rather than restating them.
- Name the intent and the field on every refusal, at both enforcement points.
- Keep `Level` value-unchecked. ADR-0033 D2 owns the open set.
- Make a terminal `Status` value a peer of success, never a flavour of it. A
  rollup that counts `Withdrawn` as delivered is the failure this vocabulary
  exists to prevent.

### Ask first

- Adding, removing or renaming any field in the contract after the ADR records
  it.
- Widening the shaping reviewer's declared tool surface. Its frontmatter
  declares `Read, Grep, Glob` and the seventh condition is decidable without
  more.
- Changing what `intake-intent` admits, or any control in its admission
  transaction. ADR-0098 D2 owns the minimum contract this builds on.
- Wiring the lint into any gate beyond the one AC-0028 names.

### Never do

- Add a new top-level directory, a new module boundary, or a new dependency.
  The lint ships inside an existing skill's script directory.
- Infer a declared fact from a side channel — git authorship for `Owner:`, a
  body heading for de-risk state, or the presence of a downstream artifact for
  `Decomposed:`. A declared field is the signal.
- Close `Level` to a vocabulary, or derive an eighth reviewer condition from
  this one.
- Let any file in `docs/product/intents/` go unvalidated.

## Testing Strategy

- **The field contract (AC-0001, AC-0002, AC-0003, AC-0009, AC-0022,
  AC-0025):** TDD. Required presence, each closed vocabulary, backtick
  normalization, the retired names and the repeat rule are one compressible
  predicate over a fixture corpus, so conforming and non-conforming fixtures
  decide them.
- **The normalization stage (AC-0004, AC-0034):** TDD. A value that is
  backticked, commented, and both at once is accepted wherever the bare value
  is — the both-at-once case is the corpus's dominant shape and the one an
  order-sensitive implementation gets wrong. A value that is empty once the
  stage has run is absent: that is the `frame-intent` template's comment-only
  `Parent intent:`, which no criterion may refuse.
- **Preamble bounding (AC-0011):** TDD. Two fixtures a whole-file scan gets
  wrong: a second `- **Status:**` line inside a de-risk record body, and a
  bolded `- **Authority:**` line inside a `## Source` block. Both shapes are in
  the real corpus.
- **The progress fields and the direct-light decomposition (AC-0005, AC-0006,
  AC-0007, AC-0008, AC-0023):** TDD. Each is a predicate over a preamble value
  or a section's checkbox items, so fixtures decide them. AC-0023 takes its own
  cases rather than sharing AC-0005's, because absence and the literal `no` are
  the pair it separates and AC-0005 cannot fail on that distinction.
- **Pointer value form (AC-0031, AC-0032):** TDD. Packet-decidable predicates
  over a preamble value, so fixtures alone decide them; they carry no
  filesystem access, which is what keeps them inside the reviewer's reach.
- **Pointer resolution (AC-0010, AC-0021, AC-0024):** TDD. Fixtures whose
  targets exist, are missing, and are tombstones. This is filesystem work
  rather than a fixture-corpus predicate, so it needs its own group.
- **Lint reporting and exit behaviour (AC-0013, AC-0014, AC-0015, AC-0017):**
  TDD. A mixed fixture corpus carrying two faults, a tombstone and one
  unreadable file, asserting the named fields, the exit code, the non-clean
  unreadable path, and that no file is skipped.
- **The two enforcement points' independence (AC-0016):** TDD. One fixture
  passes the lint and fails the review, asserted in one module so a rule that
  drifts between them fails rather than passing twice.
- **The reviewer's seventh condition (AC-0012, AC-0026, AC-0027, AC-0030):**
  goal-based check on the pinned contract, exercised against the pack suite.
  The token tuple is `INTENT_TOKENS` in
  `packs/core/tests/pack/test_shaping_review_contract.py`; the check is that it
  gains `MALFORMED(shape)`, that the other six are unchanged, that the
  suppression exception holds, and that the mode's prose states no condition
  count anywhere.
- **The gate (AC-0028):** goal-based check. The gate fails when the lint exits
  non-zero.
- **Corpus cleanliness (AC-0033):** goal-based check. One lint run over
  `docs/product/intents/` exits zero.
- **Template conformance (AC-0018):** goal-based check. Each template's
  rendered output, with every placeholder resolved, is fed to the lint; a
  refusal fails the check.
- **The operator how-to:** manual QA. A person hits each refusal and follows
  the page out of it; a test cannot tell whether the page is followable.

## Acceptance Criteria

Backtick stripping and trailing-HTML-comment discarding are a **normalization
stage**, stated by AC-0004 and AC-0034. The stage runs once, comment first then
backticks, and every criterion below decides on its output — the corpus's
dominant commented shape is backticked *and* commented, and stripping backticks
first no-ops because the comment trails the closing backtick.

A criterion is **packet-decidable** when it can be settled from the supplied
artifact alone, without opening any other file. The packet-decidable criteria
are exactly AC-0001 through AC-0009, AC-0011, AC-0022 and AC-0025. AC-0021
resolves a slug against other artifacts; every other criterion below constrains
the lint, the gate, the reviewer or a template rather than an artifact's
content.

The line is "no other file", not "the preamble alone", because AC-0007 and
AC-0008 read the artifact's `## Decomposition` and AC-0011 is about lines below
its preamble. Both facts travel with the artifact.

The split is load-bearing: `shaping-reviewer.md` states that intent mode
retrieves nothing, and that a condition the packet cannot settle emits its
token, so a reviewer asked to resolve a pointer would refuse every intent
carrying one. AC-0012 and AC-0026 are a closed biconditional over this set; no
third criterion enumerates a further silence.

- [ ] **AC-0001.** The corpus lint refuses a live intent whose preamble omits any
      of exactly `Owner:`, `Slug:`, `Level:`, `Status:`.
- [ ] **AC-0002.** A `Status:` value outside `Draft`, `Accepted`, `Fulfilled`,
      `Withdrawn`, `Cancelled`, and `Superseded by ` followed by a non-empty
      slug, is refused.
- [ ] **AC-0021.** The corpus lint refuses a `Superseded by` slug that equals
      no live intent's `Slug:` value, naming both the intent and the unresolved slug.
- [ ] **AC-0022.** A value outside its field's closed vocabulary is refused, at
      each of `Kind:` (`outcome`, `opportunity`), `Scale:` (`app`,
      `business-unit`) and `Maturity:` (`greenfield`, `brownfield`).
- [ ] **AC-0003.** `Level:` is never refused for its value.
- [ ] **AC-0004.** A field value enclosed in backticks is accepted wherever the
      same value bare is accepted.
- [ ] **AC-0034.** A field value carrying a trailing HTML comment is accepted
      wherever the same value without it is accepted, including where the value
      is also enclosed in backticks. A value that is empty once the stage has
      run is absent, not malformed.
- [ ] **AC-0005.** `De-risked:` and `Shaping-reviewed:` each carry an ISO 8601
      date or the literal `no`; any other value is refused.
- [ ] **AC-0023.** The lint's report carries one line per intent stating, for
      each of `De-risked:`, `Shaping-reviewed:` and `Decomposed:`, whether the
      field is absent or carries the literal `no`. Absence alone does not change
      the exit code.
- [ ] **AC-0006.** `Decomposed:` carries the literal `no`, or an ISO 8601 date
      followed by exactly one terminus from `children`, `brief`, `spec`,
      `direct-light`; any other value is refused.
- [ ] **AC-0007.** An intent whose `Decomposed:` terminus is `direct-light` and
      whose `## Decomposition` section carries no checkbox item is refused.
- [ ] **AC-0008.** Every checkbox item under a `direct-light` `## Decomposition`
      carries non-empty text.
- [ ] **AC-0009.** A preamble field named `Type`, `Raised`, `Stage`, `Parent`,
      `Source` or `Authority` is refused, and a preamble field named outside
      both that set and the contract is accepted.
- [ ] **AC-0025.** A preamble field occurring more than once is refused, naming
      the field and the intent.
- [ ] **AC-0011.** A field-shaped line below the preamble block does not satisfy
      or violate any obligation of that field.
- [ ] **AC-0012.** The shaping reviewer's intent mode emits `MALFORMED(shape)`
      for a preamble that fails any packet-decidable criterion, except where
      `MALFORMED(owner)` is emitted, which suppresses it.
- [ ] **AC-0026.** The shaping reviewer's intent mode emits no
      `MALFORMED(shape)` for a preamble that satisfies every packet-decidable
      criterion.
- [ ] **AC-0030.** No sentence anywhere in the shaping reviewer's text states a
      count of intent-mode conditions. An ordinal label naming one condition,
      such as `Condition 4`, is not a count. Its `MALFORMED(owner)` suppression
      sentence suppresses every other condition rather than a fixed set or a
      number.
- [ ] **AC-0027.** The shaping reviewer's six existing intent-mode tokens are
      unchanged.
- [ ] **AC-0013.** The corpus lint names every non-conforming intent together
      with the field at fault.
- [ ] **AC-0014.** The corpus lint exits non-zero when any intent is
      non-conforming.
- [ ] **AC-0015.** The corpus lint exits non-zero, rather than clean, when it
      could not fully read the corpus.
- [ ] **AC-0028.** The gate that runs the corpus lint over
      `docs/product/intents/` fails when the lint exits non-zero.
- [ ] **AC-0016.** An intent the corpus lint accepts is still refused by the
      shaping review when it fails any of that review's other conditions.
- [ ] **AC-0017.** The corpus lint validates every file in
      `docs/product/intents/`, routing each to the live-intent contract or to
      the tombstone contract by the partition rule in
      `docs/specs/intent-renumber-and-reissue/spec.md`, and validating the
      tombstone branch against that spec's tombstone field contract. Both are
      cited by name and by path rather than by criterion number, because a bare
      number resolves inside this directory, where those numbers name unrelated
      criteria.
- [ ] **AC-0033.** The corpus lint exits zero over the real
      `docs/product/intents/`.
- [ ] **AC-0018.** A rendered intent produced by `intake-intent`'s renderer, and
      `frame-intent`'s template with every placeholder resolved to a
      representative value, each satisfy the contract. The template asset itself
      is not corpus input to the lint.

## Retired identifiers

- AC-0010
- AC-0019
- AC-0020
- AC-0024
- AC-0029
- AC-0031
- AC-0032

## Follow-ons

- eugenelim: this spec fixes closed vocabularies for `Status:`, `Kind:`,
  `Scale:` and `Maturity:`, a required-present tier, and a retired-name set,
  and records them in no decision record. ADR-0111 governs the reviewer's
  mandate, not the field contract, so there is no ADR to amend when one of
  these sets changes. Decide whether that needs a decision record before an
  adopter depends on the vocabularies.
- eugenelim: `intent-reference-grammar-migration` owns pointer *form* and
  *resolution* for `Governed by:` and `Parent intent:`. The brief names it the
  owner of the canonical `<kind>:<slug>` grammar, so this spec states neither,
  and the criteria that did are retired above.
- eugenelim: `guides/product-engineering/how-to/frame-the-intent.md` and
  `hand-it-to-build.md` each inline a copy of the intent preamble. AC-0018
  reaches the renderer and the template only, so those copies are out of
  contract; bring them under one owning template or replace them with a
  pointer to it.
- Settled 2026-09-21 by eugenelim, with
  `docs/specs/intent-renumber-and-reissue/spec.md`: that spec states the
  partition rule, and this spec's AC-0017 and AC-0028 own routing every file
  and failing the gate. Neither slice blocks the other and no dependency edge
  is recorded, because an edge either way would assert a false block and both
  would cycle.
- eugenelim: `docs/specs/intent-review-mandate-split/spec.md` is `Shipped`, and
  two of its ticked criteria assert the condition count AC-0030 removes. No
  amendment: a shipped spec's criteria record what was true at delivery, not a
  standing assertion, so that record stays historical and is not reopened.
- eugenelim: the contract carries no field for a non-parent edge. Children are
  derived by inverting `Parent intent:`, which is deliberate, but a "related"
  relationship has nowhere to live — `work-loop-delivery-efficiency` describes
  `spec-review-validation-guidance` as thematically part of its effort and
  records that no pointer links them. A `Related:` field is a contract
  amendment, not a migration item.
- eugenelim: most intents remain `Draft`.
  `FEAT-0005-lifecycle-and-closure` owns the transition rule, including whether
  an intent may reach a terminal status without first passing `Accepted`. This
  spec fixes the member set only.

## Assumptions

- Process: whether reversing the reference page's "Only Outcome and Opportunity
  are load-bearing; the rest are offered, never required" needs an RFC rather
  than the ADR this spec plans — it changes a published adopter-facing rule
  across two packs (settled by: eugenelim).
- Product: whether `Superseded by <slug>` belongs on `Status:` at all, given the
  sibling tombstone contract's `Reissued as:` already carries a supersession
  pointer for a retired filename. The two answer different questions — one
  retires an ordinal, one retires a bet — but nothing yet states that boundary
  (settled by: eugenelim, with FEAT-0005 as the lifecycle owner).
- Technical: whether `Milestone:` stays unconstrained permanently. The intents
  carrying it all name a position in RFC-0071's implementation sequence, and
  AC-0009 accepts it by accepting any unrecognized name outside the retired set
  — so a later decision to constrain it is additive rather than a reversal.
