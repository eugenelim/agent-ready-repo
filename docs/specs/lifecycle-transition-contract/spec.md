# Spec: An intent's lifecycle state is a closed contract a lint can decide

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Approved:** 2026-09-23 by eugenelim. Taken on a `Findings` result, not a `Clean` one. Three spec-mode shaping rounds ran, returning 3 then 2 then 2 Blockers; every Blocker was verified against source before repair and all were resolved. Round 3's two were one structural problem — this spec was defining an intent preamble field's shape, which the parent's § Boundary assigns to `FEAT-0001` — and the owner resolved it by moving the value shape and the adopter field-table rows to `intent-identity-and-registration` rather than by rewording. Those repairs were not re-reviewed. The adversarial spec-mode review that `new-spec` step 7 calls for did not run.
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0119; ADR-0121 D1
- **Brief:** brief:intent-lifecycle-and-closure
- **Discovery:** docs/product/intents/FEAT-0005-lifecycle-and-closure.md
- **Contract:** none
- **Shape:** data

## Outcome

Every intent's `Status` names a state the corpus lint can decide from the artifact alone, and a state that asserts something about delivery carries the record that authorises it. An intent claiming `Fulfilled` carries the acceptance that ratified its decomposition and the closure that ended it; the lint refuses one that does not, naming the missing record.

## What Changes

- **The corpus lint gains a state-coherence check, and the shaping reviewer does not.** `intent_shape.py` is the single home both enforcement points read, so a rule added to `validate_live_intent()` reaches the reviewer too — and [`intent-metadata-shape-contract`](../intent-metadata-shape-contract/spec.md) makes the reviewer's packet-decidable set a closed enumeration these rules are not in. `validate_supersession()` is the precedent: a rule the corpus lint calls and `validate_live_intent()` does not. The new rules take that shape, so the shipped reviewer contract stays true and needs no amendment.
- **Two preamble records become required by state.** Whether an intent must carry `Accepted:` or `Fulfilled:` follows from its `Status`. What a valid value looks like is not decided here: an intent preamble field's shape is `FEAT-0001`'s under the parent's § Boundary, so the value shape and the adopter field-table rows are handed to [`intent-identity-and-registration`](../../product/briefs/intent-identity-and-registration.md), whose § Post-Ready decisions carries them. This spec decides presence by state and consumes whatever shape lands.
- **`Draft` narrows to mean open.** It stops carrying shaping progress, which the three shipped shaping-progress fields already record.
- **The corpus is migrated.** Two sets, derived at migration time rather than pinned here: the intents the new rules refuse, and within them the intents that never reached `Accepted` in their history. The first owes a record; the second owes a status judgement, walked back through the parent's `Draft` → `Accepted` gate or reclassified to a state it qualifies for. The second set is the smaller one, and conflating them overstates the judgement work.

**Not changed here.** Whether `Accepted` requires its own `Accepted:` record, and every supersession rule, stay as they are and are not this spec's to settle. The value shape of the two records, and the form supersession takes, were both handed to `intent-identity-and-registration` and have since landed there: a record carries an ISO 8601 date, a space and non-empty text, and supersession is a bare `Status: Superseded` token beside a separate `Superseded by:` field. This spec consumes both and decides presence by state.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Not applicable here — the adopter field-table rows travel with the value shape to `intent-identity-and-registration`, whose Interface-compatibility surface already owns that reference and whose closeout requires no field the lint decides on is absent from it | — | — | — | — |
| Current architecture | Applicable — the rules gain a declared refusal registry, and the module contract is what other checks read | `intent_shape.py` module docstring | eugenelim | The docstring names every refusal class this spec adds | The docstring names every refusal class this spec adds |
| Decision rationale | Applicable — the migration's per-artifact walk-back-or-reclassify call is a decision the parent's § Legal transitions grounds but does not make | `notes/migration-record.md` | eugenelim | One entry per artifact needing a status judgement | Each entry names the branch taken and the review or waiver it rests on |
| Decision rationale | Not applicable — ADR-0119 and FEAT-0005's § Legal transitions already carry the decision and its ground; this spec implements it | — | — | — | — |
| Release history | Applicable — the lint is a gate adopters' CI runs | the repository changelog | eugenelim | One entry naming the new refusal class and the records it requires | The entry names what newly fails, not only what was added |
| Reusable learning | Not applicable — no cross-cutting lesson beyond the decision record | — | — | — | — |
| User promise | Not applicable — no end-user surface changes | — | — | — | — |
| Operations | Not applicable — no runtime or monitored surface | — | — | — | — |

## Agent Rules

### Always do

- Re-run the lint against the real `docs/product/intents/` tree, not only fixtures. The CI job does this deliberately, because "no violations found" and "clean" are different claims about a directory whose files would not open.
- Give every new refusal a message naming the intent and the missing record.

### Ask first

- Before changing any intent's `Status` during the migration. Which of walk-back or reclassification applies is a judgement per artifact and is the owner's.
- Before widening the closed `Status` set.

### Never do

- Never add a module, a dependency, or a new script. This work extends one existing lint and edits artifacts.
- Never let a new rule reach a line below the preamble block. The preamble-bounding rule is [`intent-metadata-shape-contract`](../intent-metadata-shape-contract/spec.md)'s and is pinned by its tests; this spec owns only not regressing it.
- Never collapse the lint's exit 1 and exit 2. "No violations found" and "clean" are different claims about a directory whose files would not open, and that distinction is the sibling spec's to own.
- Never infer a transition from history. The lint sees one snapshot; anything it decides is decided from the artifact in front of it.

## Testing Strategy

- **The delivered-terminal rules (AC-0001, AC-0002, AC-0003, AC-0004):** TDD. Each is a pure presence predicate over a parsed preamble, so a fixture pair per rule decides it. AC-0003 takes its own case because the `Withdrawn` exemption is what the other three would swallow.
- **The positive paths (AC-0005, AC-0006):** TDD, with their own fixtures. Without them an implementation that refuses every `Fulfilled` intent satisfies every refusal criterion, and the real-tree run cannot catch it because the migration may leave no `Fulfilled` intent standing.
- **The state exclusions (AC-0007, AC-0008, AC-0009):** TDD. Each is observable only as a refusal when a record sits beside a state that did not earn it.
- **The enforcement-point boundary (AC-0010):** TDD. A forbidden-substring control over the shaping reviewer's intent-mode rubric for both record names. This is the assertion that reds: `test_shaping_review_contract.py` asserts its condition list by positive substring and its token set with `in` per token, so neither observes a condition being added — a criterion resting on those would hold on empty state.
- **The refusal surface (AC-0011, AC-0012, AC-0013):** TDD. AC-0012's registry is what makes AC-0013 a set comparison rather than a read; without it the docstring obligation is a sentence-exists check.
- **The migration (AC-0014):** goal-based check. The real-tree run is the oracle, and no fixture stands in for it.

## Acceptance Criteria

- [ ] **AC-0001.** An intent whose `Status` is `Fulfilled` and which carries no `Accepted:` record is refused.
- [ ] **AC-0002.** An intent whose `Status` is `Cancelled` and which carries no `Accepted:` record is refused.
- [ ] **AC-0003.** An intent whose `Status` is `Withdrawn` is accepted with no `Accepted:` record, because abandoning an unratified bet needs no ratification.
- [ ] **AC-0004.** An intent whose `Status` is `Fulfilled` and which carries no `Fulfilled:` record is refused.
- [ ] **AC-0005.** An intent whose `Status` is `Fulfilled` and which carries both records is accepted.
- [ ] **AC-0006.** An intent whose `Status` is `Cancelled` and which carries an `Accepted:` record is accepted.
- [ ] **AC-0007.** An intent whose `Status` is `Draft` and which carries an `Accepted:` or `Fulfilled:` record is refused, because `Draft` means open.
- [ ] **AC-0008.** An intent whose `Status` is `Accepted` and which carries a `Fulfilled:` record is refused.
- [ ] **AC-0009.** An intent whose `Status` is `Cancelled` or `Withdrawn` and which carries a `Fulfilled:` record is refused, because neither state delivered.
- [ ] **AC-0010.** Neither record's name appears anywhere in the shaping reviewer's intent-mode rubric, so no rule this spec adds joins the set that mode decides and [`intent-metadata-shape-contract`](../intent-metadata-shape-contract/spec.md)'s packet-decidable enumeration is unamended.
- [ ] **AC-0011.** Every refusal this spec adds names the offending file by the same corpus-relative name the lint reports today, and names the record at fault.
- [ ] **AC-0012.** The module defining the rules declares its refusal classes in one enumerable place, and every refusal this spec adds is constructed from a member of it.
- [ ] **AC-0013.** Every refusal class this spec adds is named in the docstring of the module that defines it. Pre-existing classes are out of scope.
- [ ] **AC-0014.** At delivery, `python3 packs/core/.apm/skills/work-intake/scripts/intent_corpus_lint.py --dir docs/product/intents --root .` exits 0 against the real tree. The standing gate is [`intent-metadata-shape-contract`](../intent-metadata-shape-contract/spec.md)'s own real-tree exit-zero criterion; this one is the migration's delivery-time condition.

## Follow-ons

- **The two records' value shape and their adopter field-table rows.** Handed to [`intent-identity-and-registration`](../../product/briefs/intent-identity-and-registration.md) § Post-Ready decisions on 2026-09-23, because an intent preamble field's shape is `FEAT-0001`'s under the parent's § Boundary. Owner: eugenelim.
- **Write-time transition enforcement.** This spec enforces resting states from a snapshot. Preventing an illegal move at the moment it is written needs a writer that knows both the current and proposed status, which is `close-work`'s path and slice 2's surface. Owner: eugenelim, under `brief:intent-lifecycle-and-closure`.

## Assumptions

- Process: the delivery brief states that A4 — whether `close-work`'s disposition contract covers a closed product bet — is settled before the slice-cut confirmation. It was not: the cut was confirmed on 2026-09-23 with A4 open, and the parent's § Validation hook still carries settling it as the zeroth owed activity. Recorded here because the precondition was missed rather than met, and it changes no criterion in this spec. Settles by: eugenelim, in the brief where it is owed.
