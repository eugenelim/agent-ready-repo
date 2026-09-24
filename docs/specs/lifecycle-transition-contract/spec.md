# Spec: An intent's lifecycle state is a closed contract a lint can decide

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Approved:** 2026-09-23 by eugenelim. Taken on a `Findings` result, not a `Clean` one. Three spec-mode shaping rounds ran, returning 3 then 2 then 2 Blockers; every Blocker was verified against source before repair and all were resolved. Round 3's two were one structural problem — this spec was defining an intent preamble field's shape, which the parent's § Boundary assigns to `FEAT-0001` — and the owner resolved it by moving the value shape and the adopter field-table rows to `intent-identity-and-registration` rather than by rewording. Those repairs were not re-reviewed. The adversarial spec-mode review that `new-spec` step 7 calls for did not run.
- **Re-approved:** 2026-09-24 by eugenelim, after the material amendment restating AC-0010. Taken on a `Clean` result this time: seven adversarial spec-mode rounds ran, returning 6, 4, 3, 3, 5 and 2 findings and then `Clean`. Every Blocker was verified against source before repair, and five were defects in the amendment's own reasoning rather than in the spec it amended. The criterion it replaced was already false on the tree — `shaping-reviewer.md:81` carries `Accepted` inside § intent mode — so this amendment repaired a red criterion rather than tightening a green one.
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0119; ADR-0121 D1
- **Brief:** brief:intent-lifecycle-and-closure
- **Discovery:** docs/product/intents/FEAT-0005-lifecycle-and-closure.md
- **Contract:** none
- **Shape:** data

## Outcome

Every intent's `Status` names a state the corpus lint can decide from the artifact alone, and a state that asserts something about delivery carries the record that authorises it. An intent claiming `Fulfilled` carries the acceptance that ratified its decomposition and the closure that ended it; the lint refuses one that does not, naming the missing record.

## What Changes

- **The corpus lint gains a state-coherence check, and `validate_live_intent()` does not.** `intent_shape.py` is the single home both enforcement points read, and `validate_live_intent()` is the surface they share. The new rules stay off it, taking the seam `validate_supersession()` already occupies: reachable from the corpus lint, unreachable from `validate_live_intent()`. That is the whole placement claim, it is what AC-0010 measures, and it is deliberately stated without asserting how far the shaping reviewer's own conditions reach — § Follow-ons records that reach as unsettled and nothing here depends on the answer.
- **Two preamble records become required by state.** Whether an intent must carry `Accepted:` or `Fulfilled:` follows from its `Status`. What a valid value looks like is not decided here: an intent preamble field's shape is `FEAT-0001`'s under the parent's § Boundary, so the value shape and the adopter field-table rows are handed to [`intent-identity-and-registration`](../../product/briefs/intent-identity-and-registration.md), whose § Post-Ready decisions carries them. This spec decides presence by state and consumes whatever shape lands.
- **`Draft` narrows to mean open.** It stops carrying shaping progress, which the three shipped shaping-progress fields already record.
- **The corpus is migrated.** Two sets, derived at migration time rather than pinned here: the intents the new rules refuse, and within them the intents that never reached `Accepted` in their history. The first owes a record; the second owes a status judgement, walked back through the parent's `Draft` → `Accepted` gate or reclassified to a state it qualifies for. The second set is the smaller one, and conflating them overstates the judgement work.

**Not changed here.** Whether `Accepted` requires its own `Accepted:` record, and every supersession rule, stay as they are and are not this spec's to settle. The value shape of the two records, and the form supersession takes, were both handed to `intent-identity-and-registration` and have since landed there: a record carries an ISO 8601 date, a space and non-empty text, and supersession is a bare `Status: Superseded` token beside a separate `Superseded by:` field. This spec consumes both and decides presence by state.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable, narrowly, and this row was corrected during delivery. The field-table **rows** still belong to `intent-identity-and-registration`, which owns their value shape — but *when* a record is required follows from `Status`, which is this spec's rule and appears on no other artifact. A reader refused by these rules cannot act without it, and the finish checklist obliges a shipped feature's user-facing documentation either way | `guides/product-engineering/reference/intent-fields-and-modes.md` and `guides/product-engineering/how-to/fix-a-refused-intent.md` | eugenelim | A per-status table saying which record each `Status` requires, permits or refuses, and a refusal section for the messages these rules emit | An adopter can clear every refusal these rules add without opening a spec, a test, or the validator source. The value shape stays the sibling's; only the presence rule is stated here |
| Current architecture | Applicable — the rules gain a declared refusal registry, and the module contract is what other checks read | `intent_shape.py` module docstring | eugenelim | The docstring names every refusal class this spec adds, and states the surface dichotomy once | The docstring names every refusal class this spec adds, and is the module's only statement of which surface a live-intent rule belongs on. The first half is AC-0013 and a test decides it; the second is a closeout judgement recorded in `notes/verification-ledger.md`, because no control catches a reworded restatement of the rule — a content pin would catch a copied one and pass a pointer, but not a paraphrase |
| Decision rationale | Applicable — the migration's per-artifact walk-back-or-reclassify call is a decision the parent's § Legal transitions grounds but does not make | `notes/migration-record.md` | eugenelim | One entry per artifact needing a status judgement | Each entry names the branch taken and the review or waiver it rests on |
| Decision rationale | Not applicable — ADR-0119 and FEAT-0005's § Legal transitions already carry the decision and its ground; this spec implements it | — | — | — | — |
| Release history | Applicable — the lint is a gate adopters' CI runs | the repository changelog | eugenelim | One entry naming the records each `Status` requires and what newly fails. **Corrected during delivery:** this read "naming the new refusal class", but the class is an internal registry token the lint never prints — `intent_corpus_lint.py` reports file, field and reason — so a release note naming it would describe output no reader can find | The entry names what newly fails, not only what was added, and carries the `Highlights` block `packs/AGENTS.local.md` requires of a release that changes an adopter's obligations |
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
- **The enforcement-point boundary (AC-0010):** TDD. A reachability differential, run once per refusing criterion rather than once overall: each fixture those criteria already pin goes to both surfaces, asserting `validate_live_intent()` returns `[]` for it while the corpus lint refuses it. One fixture cannot serve — a single rule leaked onto the shared surface leaves every other fixture's assertion green, so the criterion would hold while the boundary had moved for that rule. Its home is `test_intent_shape.py`, beside the existing seam controls, not `test_intent_corpus_lint.py`. The original instrument — a forbidden-substring control over both record names in the reviewer's rubric — is dropped as **unusable, not merely weak**: measured 2026-09-24, `packs/core/.apm/agents/shaping-reviewer.md:81` already carries the bare token `Accepted` inside § intent mode, as condition 5's `Status` value, so the control cannot tell the record name from the status token and reds on a mention that has nothing to do with either record.
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
- [ ] **AC-0010.** No rule this spec adds is reachable from `validate_live_intent()`, the surface both enforcement points share. Asserted once per refusing criterion, not once overall. The refusing criteria are exactly AC-0001, AC-0002, AC-0004, AC-0007, AC-0008 and AC-0009 — AC-0003, AC-0005 and AC-0006 accept, so no artifact of theirs belongs in this set. Every artifact those six refuse returns no violation from `validate_live_intent()`, while the corpus-lint surface refuses it. Leaking any single rule onto the shared surface therefore reds. `validate_supersession()`'s rules satisfy the same predicate and are the precedent — reachability from `validate_live_intent()`, not a count of direct callers. Name absence in the shaping reviewer's rubric is **not** asserted and is not a usable test: measured 2026-09-24, `packs/core/.apm/agents/shaping-reviewer.md:81` carries the bare token `Accepted` inside § intent mode as condition 5's `Status` value, so a substring control cannot distinguish the record name from the status token.
- [ ] **AC-0011.** Every refusal this spec adds names the offending file by the same corpus-relative name the lint reports today, and names the record at fault.
- [ ] **AC-0012.** The module defining the rules declares its refusal classes in one enumerable place, and every refusal this spec adds is constructed from a member of it.
- [ ] **AC-0013.** Every refusal class this spec adds is named in the docstring of the module that defines it. Pre-existing classes are out of scope.
- [ ] **AC-0014.** At delivery, `python3 packs/core/.apm/skills/work-intake/scripts/intent_corpus_lint.py --dir docs/product/intents --root .` exits 0 against the real tree. The standing gate is [`intent-metadata-shape-contract`](../intent-metadata-shape-contract/spec.md)'s own real-tree exit-zero criterion; this one is the migration's delivery-time condition.

## Follow-ons

- **Whether the reviewer's intent-mode condition 7 reaches a format rule, or only a closed enumeration.** Its wording is "every field whose values the contract fixes carries one of them", and `test_shaping_review_contract.py`'s condition-7 control reads "values the contract fixes" as the closed vocabularies. [`intent-preamble-lifecycle-records`](../intent-preamble-lifecycle-records/spec.md) put `_check_dated_evidence` for these two records on the shared surface, so the answer decides whether [`intent-metadata-shape-contract`](../intent-metadata-shape-contract/spec.md)'s packet-decidable enumeration still describes what that mode decides — and if it does not, that spec's AC-0026 needs revisiting through the frozen-document route. **Deliberately not settled or asserted here.** `intent_shape.py`'s docstring records that what a reviewer emits is not that module's to state, so a module probe cannot answer it; a measured reviewer run against a real packet can. This spec does not depend on the answer, because AC-0010 asserts reachability from `validate_live_intent()` and says nothing about the reviewer, and its placement holds under either answer — the plan's § Design decisions records why. **If the answer is enumerations-only**, the pairing half of that split loses the risk that motivated it and is worth revisiting, which is the second thing this follow-on owes. Owner: eugenelim, under `brief:intent-identity-and-registration`, which owns both shipped specs.

- **The two records' value shape and their adopter field-table rows.** Handed to [`intent-identity-and-registration`](../../product/briefs/intent-identity-and-registration.md) § Post-Ready decisions on 2026-09-23, because an intent preamble field's shape is `FEAT-0001`'s under the parent's § Boundary. Owner: eugenelim.
- **Making partial corpus-scoped coverage unreachable.** T2 adds `validate_corpus_scoped()` as the one entry point a consumer should call, but leaves `validate_supersession()` public beside it, so a future consumer can still call the partial name and get partial coverage — which is how `tests/roster/test_intent_template_shape_conformance.py` arrived at enumerating two surfaces by hand. Closing it means privatising `validate_supersession()`, a rename reaching the corpus lint, the roster suite and a large shipped block of `test_intent_shape.py`; that is more churn than this slice carries and serves no criterion here. Owner: eugenelim, under `brief:intent-identity-and-registration`, which owns the module's shipped surface.
- **Write-time transition enforcement.** This spec enforces resting states from a snapshot. Preventing an illegal move at the moment it is written needs a writer that knows both the current and proposed status, which is `close-work`'s path and slice 2's surface. Owner: eugenelim, under `brief:intent-lifecycle-and-closure`.

## Assumptions

- Process: the delivery brief states that A4 — whether `close-work`'s disposition contract covers a closed product bet — is settled before the slice-cut confirmation. It was not: the cut was confirmed on 2026-09-23 with A4 open, and the parent's § Validation hook still carries settling it as the zeroth owed activity. Recorded here because the precondition was missed rather than met, and it changes no criterion in this spec. **Settled 2026-09-24 against coverage**, in the parent intent's § Validation hook, which owns the reading and its evidence; the brief's retention non-goal records the consequence. This changes no criterion in this spec.
