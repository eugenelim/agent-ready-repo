# Spec: Intent preamble lifecycle records — supersession pointer and dated evidence

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Approved:** 2026-09-23 by eugenelim, on the same confirmation that cut the slice. Three contract decisions were put to the owner explicitly and answered: one slice rather than two, the value rules on the surface the shaping reviewer's condition refers to, and a new slice rather than an amendment to the `Shipped` `intent-metadata-shape-contract`. The independent spec-mode shaping review that `new-spec` requires before approval **did not run before approval**. Independent adversarial reviews of the combined spec and implementation ran after it instead, and every sustained finding was repaired; the plan's `## Changelog` is the record, one entry per round. No total is stated here, because a total goes stale on the next round. Recorded as taken out of order rather than as met.
- **Constrained by:** ADR-0033; ADR-0111
- **Plan:** [`plan.md`](plan.md)
- **Brief:** brief:intent-identity-and-registration
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

Anyone reading an intent's preamble finds one bare lifecycle token in `Status:`
and reads a supersession pointer, a ratification record and a fulfilment record
from fields of their own. A record that is there carries a date and text rather
than a date alone, so it cannot be written without saying something; *whether*
a given state requires one belongs to the lifecycle contract, not here.

## What Changes

- `Status:` loses its one parameterized value and carries six bare tokens —
  `Superseded` joins the five it already had — in
  `packs/core/.apm/skills/work-intake/scripts/intent_shape.py`
- A `Superseded by:` preamble field carries the pointer `Status:` used to
  embed, paired with `Superseded` in both directions — same module
- `Accepted:` and `Fulfilled:` move from unconstrained to constrained when
  present, each carrying a dated evidence value — same module
- One shared dated-evidence value rule, sitting beside the ISO 8601 calendar
  date predicate the contract already has rather than restating it
- The adopter field table gains a row for each of the three fields, and its
  `Status` row drops the embedded pointer —
  `guides/product-engineering/reference/intent-fields-and-modes.md`
- Every surface that offered `Superseded by <slug>` as a `Status` value stops
  — `frame-intent`'s template and three how-tos. `intake-intent`'s template is
  not among them: it seeds `Status: Draft` and never carried the retired form,
  so it is unchanged and serves only as a conformance target
- One intent's `Accepted:` record, whose date token carries a trailing comma —
  `docs/product/intents/architect-design-gate-calibration.md`

**One change in this delivery is outside the contract above**, bundled on
explicit owner instruction given with the slice request and recorded here so the
diff is not larger than the record. `docs/product/briefs/intent-lifecycle-and-closure.md`
§ Scope / Non-goals asserted that A4 — whether `close-work`'s disposition
contract covers a closed product bet — was settled before that brief's slice-cut
confirmation. It was not: the cut was confirmed 2026-09-23 with A4 open. The
deviation was recorded only in `docs/specs/lifecycle-transition-contract/spec.md`
§ Assumptions, which is spec prose nothing re-reads to find a missed brief
precondition, so it was added to the non-goal where the obligation lives. It
touches no criterion of this spec and no code; its verification is that the
sentence is present and names the date, the open assumption and its settler.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — one new field name (`Superseded by:`), two fields moving from unconstrained to constrained when present, and one `Status` value replaced by a bare token | `guides/product-engineering/reference/intent-fields-and-modes.md` | eugenelim | A row for `Superseded by`, `Accepted` and `Fulfilled` in the field table, and a `Status` row naming the bare tokens | The page describes every field the lint decides on, and no field the lint decides on is absent from it. **Read the three new rows against the module before closing:** their tier and the `Status` vocabulary are machine-checked, their prose is not, and a row that negates its own rule passes every gate |
| Maintainer procedure | Applicable — three new refusals an author can hit, and one changed one | `guides/product-engineering/how-to/fix-a-refused-intent.md` | eugenelim | Each new refusal named with its remedy, and the `Superseded by <slug>` remedy rewritten to the split form | The page resolves one real refusal of each new kind end to end |
| Current product truth | Applicable — the intent preamble is inlined verbatim on several surfaces, and a stale copy teaches the retired form | `frame-intent`'s template and the three how-tos that inline the preamble | eugenelim | No surface offers `Superseded by <slug>` as a `Status` value | A repository-wide search for the retired form returns only historical records |
| Decision rationale | Applicable, and **settled 2026-09-24 by eugenelim: no decision record is owed.** The shaping decision is already recorded in `FEAT-0005-lifecycle-and-closure.md` § Legal transitions. `intent-metadata-shape-contract` § Follow-ons asked whether the field vocabularies additionally need one before an adopter depends on them, and publishing the changed `Status` set fired that trigger | this spec § Follow-ons, which carries the reasoning | eugenelim | the reasoned decision that none is owed | Discharged. `close-work` reads the Follow-on entry |

## Agent Rules

### Always do

- Keep the field table in `intent_shape.py`. Both enforcement points read it
  from that one home, and a second copy drifts from it.
- Keep the ISO 8601 calendar date rule in one predicate. The dated-evidence
  rule consumes it; it does not restate the pattern or re-parse the date.
- Re-run the inherited `intent-metadata-shape-contract` suite unamended
  alongside the new cases, so a change to a shared rule is visible where it
  lands.

### Ask first

- Any edit to `docs/specs/intent-metadata-shape-contract/spec.md`. This slice
  exists because that spec is `Shipped` and its criteria are historical.
- Any change to an intent's `Accepted:` or `Fulfilled:` evidence *text*.
  Correcting a date token's shape is migration; rewriting what the record
  claims is not.

### Never do

- Add a `MALFORMED` token, add an intent-mode condition, or state a count of
  either in the shaping reviewer's text. It is byte-unchanged by this delivery;
  counting what it already has is how a count gets asserted by accident.
- Enumerate a vocabulary member in the shaping reviewer's text. Condition 7
  names the obligation and defers the member lists, and that is what lets it
  reach a new field rule with no edit.
- Delete a superseded intent's body when its pointer moves out of `Status:`.

## Testing Strategy

- **The value and coherence rules: TDD.** Each is a pure predicate over one
  preamble with a compressible invariant, unit-tested in
  `packs/core/tests/skills/work-intake/test_intent_shape.py`.
- **Pointer resolution against the live corpus: TDD**, at the corpus-lint
  surface in `test_intent_corpus_lint.py`, because it reads more than one
  artifact and cannot be settled from a single preamble.
- **The reviewer's decided set: goal-based**, exercised by the existing
  `packs/core/tests/pack/test_shaping_review_contract.py` re-run unamended.
  The claim under test is that the reviewer's text needs no edit, so a passing
  unamended suite is the evidence and a new assertion there would not be.
- **The projected preamble surfaces: goal-based**, a repository-wide search
  for the retired form over a closed, named file set.
- **The real corpus: goal-based**, the corpus lint exiting zero over
  `docs/product/intents/`.

## Acceptance Criteria

The normalization stage that `intent-metadata-shape-contract` states — trailing
HTML comment discarded, then surrounding backticks stripped, once per value —
is inherited unchanged, and every criterion below decides on its output. A
value emptied by the stage is absent, not malformed, so an empty
`Superseded by:` is judged by AC-0002 rather than by a value rule.

Where each rule sits is a contract, and this spec states it rather than
asserting what a reviewer will do with it.

**Two surfaces.** `validate_live_intent()` decides a rule from one artifact and
is the surface the shaping reviewer's preamble condition refers to.
`validate_supersession()` is called by the corpus lint alone. AC-0001 and
AC-0004 are rules about one field's *value* and sit on the first. AC-0002,
AC-0003 and AC-0005 sit on the second: the first two say which field another
field's *value* requires, which no clause of that condition reaches, and the
third resolves against other artifacts, which the reviewer cannot do because it
retrieves nothing.

**What this spec does not claim.** It does not assert that a shaping reviewer
emits `MALFORMED(shape)` for a value AC-0001 or AC-0004 refuses. That depends on
whether a given reviewer packet carries the field contract, which
`intent-metadata-shape-contract` owns and this delivery neither strengthens nor
weakens — the reviewer's text is byte-unchanged, which AC-0008 states and an
empty diff proves. Placing a value rule on the shared surface is what keeps that
inherited mechanism true for these two rules as it is for the rest; asserting the
outcome would be asserting a behaviour nothing here can check.

- [x] **AC-0001.** A `Status:` value outside exactly `Draft`, `Accepted`,
      `Fulfilled`, `Withdrawn`, `Cancelled` and `Superseded` is refused,
      including any value beginning `Superseded by `.
- [x] **AC-0002.** The corpus lint refuses an intent whose `Status:` is
      `Superseded` and whose preamble carries no `Superseded by:` value, naming
      the intent and the absent field. The shared surface accepts it, so the
      shaping reviewer is not obliged to decide it.
- [x] **AC-0003.** The corpus lint refuses an intent whose preamble carries a
      `Superseded by:` value and whose `Status:` is not `Superseded`, naming the
      intent and both fields. The shared surface accepts it, on the same
      grounds as AC-0002.
- [x] **AC-0004.** `Accepted:` and `Fulfilled:` each carry an ISO 8601 calendar
      date written `YYYY-MM-DD`, a space, then non-empty text; any other value
      is refused, including a bare date, the literal `no`, a date token carrying
      an adjacent punctuation mark, and the basic form `20260920`. The date is
      the run of characters before the first space, so a separator that is a tab
      rather than a space is refused and further spaces before the text are not.
- [x] **AC-0005.** Where an intent's `Status:` and `Superseded by:` satisfy
      AC-0002 and AC-0003, the corpus lint refuses a `Superseded by:` value that
      equals the `Slug:` of no intent it may resolve to, naming both the intent
      and the unresolved slug. Resolution is one hop: a live intent that is
      itself `Superseded` is not a target, so a chain is refused rather than
      followed. A `Superseded by:` naming a live, non-superseded intent resolves.
      The precondition is the contract, not an implementation detail: a pair
      that is already malformed is reported once, for the fault the author fixes
      first, rather than twice.
- [x] **AC-0006.** `Status:` and the two dated-evidence records are decided by
      `validate_live_intent()`; the supersession pairing and resolution rules are
      decided only by `validate_supersession()`, which `validate_live_intent()`
      does not call. A malformed pair is therefore accepted by the first surface
      and refused by the corpus lint.
- [x] **AC-0008.** `packs/core/.apm/agents/shaping-reviewer.md` is byte-unchanged
      by this delivery, so its intent-mode conditions, its `MALFORMED` tokens and
      its deferral of every vocabulary member all stand exactly as
      `intent-metadata-shape-contract` delivered them. Byte identity is the whole
      criterion: it asserts no count and names no member.
- [x] **AC-0009.** `guides/product-engineering/reference/intent-fields-and-modes.md`
      carries exactly one field-table row for each of `Superseded by`, `Accepted`
      and `Fulfilled`, each at the tier the validator holds, and its `Status`
      row's value cell names exactly the members of `STATUS_VALUES` and no
      embedded pointer. Whether each row's prose *describes its rule correctly*
      is a closeout condition rather than a criterion: a keyword check cannot
      tell "one hop" from "not one hop", so asserting it would read green while
      the page said the opposite. The test file states this boundary where a
      later author will find it.
- [x] **AC-0010.** No file in
      `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`,
      `packs/core/.apm/skills/intake-intent/`,
      `guides/product-engineering/how-to/frame-the-intent.md`,
      `guides/product-engineering/how-to/hand-it-to-build.md` or
      `guides/product-engineering/how-to/fix-a-refused-intent.md` offers
      `Superseded by <slug>` as a `Status:` value.
- [x] **AC-0011.** `guides/product-engineering/how-to/fix-a-refused-intent.md`
      names the refusal message of each of AC-0002, AC-0003 and AC-0004 with its
      remedy.
- [x] **AC-0012.** The corpus lint exits zero over the real
      `docs/product/intents/`.
- [x] **AC-0013.** A rendered intent produced by `intake-intent`'s renderer, and
      `frame-intent`'s template with every placeholder resolved to a
      representative value, each satisfy **both** surfaces — the per-artifact
      rules and the corpus-scoped supersession rules. Naming both is the point:
      a template carrying a populated `Superseded by:` beside `Status: Draft`
      passes the first surface by design, and would seed a corpus the lint
      refuses.

## Retired identifiers

- AC-0007 — asserted that the shaping reviewer emits no `MALFORMED(shape)` for a
  conforming preamble. Withdrawn at review round 3: the reviewer retrieves
  nothing and enumerates no vocabulary, so whether it decides a field rule turns
  on what a caller puts in its packet. Nothing in this delivery establishes that,
  and the evidence offered — an unamended contract suite — passes equally against
  a reviewer that applies no new rule at all. The surface placement it was
  standing in for is now stated directly, above.
- AC-0014 — required a `Superseded by:` value to carry no whitespace. Withdrawn
  at review round 2: `Slug:` is never judged on its value, so the rule refused a
  pointer at a target the contract itself accepts. It existed to satisfy a tier
  parity check, which is not a reason for a rule.

## Follow-ons

- eugenelim: **the review class, recorded so the next delivery does not repeat
  it.** Every review round found one class and little else: a claim asserted
  beyond what the delivery establishes. Round 1 — the guides promised one-hop
  resolution the lint did not enforce. Round 2 — AC-0014 rested on "no `Slug:`
  carries whitespace", which is false. Round 3 — AC-0007 asserted what a shaping
  reviewer emits, which nothing here can check. Rounds 4 and 5 — that same
  withdrawn claim was still shipping on four, then two more surfaces, because
  each repair cut it where the finding pointed and nowhere else. Later rounds
  — seams and published rows carrying no control that could fail, counts of a
  reviewer this delivery does not touch, and controls naming one of the two
  fields a single rule governs.

  Three lessons, each priced in review rounds. **Write each criterion from the
  run, not from the intent**: every withdrawn criterion here read plausibly and none
  survived being checked against what the code does. **Repair the class, not the
  instance**: a withdrawn claim is not a code change, so no gate catches it on
  the surfaces a finding did not name — the spec, the plan, the brief, the
  changelog, the `workspace.toml` summary, `.apm/` docstrings and the commit
  message each hid one. Grep the phrase across the tree before re-reviewing.
  **State no running total of anything a later round changes**: three surfaces
  carried a review-round count, and each went stale the moment another round
  ran — which is how a record *of* this class ends up committing it.

- **Settled 2026-09-24 by eugenelim: the intent field vocabularies owe no
  decision record.** `intent-metadata-shape-contract` § Follow-ons raised this
  and named its trigger — an adopter depending on the vocabularies — which
  publishing the changed `Status` set to the adopter field table fired. Three
  grounds, and the third is the one that decides it.

  ADR-0111 governs the shaping reviewer's *mandate*, not the field set, so no
  existing record is being contradicted or left stale. The field set is
  delivery-owned by construction: it is fixed by a spec, projected into the
  adopter reference page, and held to the module by
  `tests/roster/test_intent_field_reference_parity.py`, so it already has a
  single enforced home and a gate that fails when the two drift. And an ADR
  would record no *decision* that is not already recorded — `FEAT-0005`
  § Legal transitions carries the supersession split and its `checkable-adr-metadata`
  precedent, and the value shape was settled in this brief's § Post-Ready
  decisions. A record whose whole content is a pointer at two other records is
  a third home for the same fact, which is what the repository's own guidance
  against duplicated rules exists to prevent.

  What this does **not** settle: whether the *tier taxonomy itself* — required,
  constrained-when-present, unconstrained, retired — should be governed, which
  is a larger question than this slice's two fields and belongs to whoever next
  changes the taxonomy rather than a member of it. Because no ADR is authored,
  the frozen-document rule in
  `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`
  § *Superseding a frozen document* does not engage: it points a superseded
  record at an ADR, and there is none to point at.
- **Closed 2026-09-24 by eugenelim.**
  `docs/specs/lifecycle-transition-contract/plan.md` carried two lines stale
  against the shape this slice shipped: § *Data & schema* called the evidence
  text optional, and its behaviour table named the retired `Superseded by
  <slug>` status form. That plan is `Approved` and pinned in substance, so this
  delivery left it alone until the owner instructed the amendment directly. Both
  lines are now corrected, wording only, with `Status: Approved` untouched and
  the amendment recorded in that plan's own `## Changelog`. Its spec was never
  wrong — it defers value shape here, and that deferral holds.

- eugenelim: `docs/specs/lifecycle-transition-contract/spec.md` decides
  `Accepted:` and `Fulfilled:` *presence by state* on a corpus-lint-only seam,
  and this spec decides their *value shape* on the shared seam. The two seams
  meet at those two fields and nothing states that boundary in one place.
  Decide whether the split is stable before a third rule is added to either.
- eugenelim: `guides/product-engineering/how-to/frame-the-intent.md` and
  `hand-it-to-build.md` each inline a copy of the intent preamble, and this
  delivery edits both by hand for the second time. The owning
  `intent-metadata-shape-contract` follow-on already names bringing them under
  one template or replacing them with a pointer; this delivery is the evidence
  that the copies drift on every preamble change.

## Assumptions

- Process: whether the changed field contract needs a decision record, and
  therefore whether `intent-metadata-shape-contract` owes a partial-supersession
  `Status` pointer at it — what the Durable Outputs blocker and the first
  Follow-on carry (settled by: eugenelim).
