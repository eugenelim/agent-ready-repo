# Plan: Supersession splits into two fields, and two lifecycle records get a value shape

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/AGENTS.md` (pack export boundary, test loader rule, version bump rule); `docs/AGENTS.md`; [ADR-0111](../../adr/0111-intent-review-splits-well-formedness-from-assumption-attack.md); [ADR-0033](../../adr/0033-intent-level-open-recognized-set-decoupled-from-scale.md)

## Approach

Three predicates and one field-table entry, all inside a parse the module already runs. The work is additive except at `_check_status`, where one parameterized form is replaced by a bare token and a coherence rule takes over what the form used to say.

The corpus migration is one file and one character, so it lands in the same task as the rule that refuses it rather than in a task of its own.

## Constraints

- `.apm/` is the runtime export boundary. Tests never live there, and every `.apm/` edit reprojects through `make build-self`.
- A non-cosmetic pack-content change bumps matching versions in `pack.toml` and `.claude-plugin/plugin.json`.
- The shaping reviewer's intent-mode text is byte-unchanged. It is the one surface where an edit would be tempting and would cost an amendment to a `Shipped` spec.
- `docs/specs/intent-metadata-shape-contract/spec.md` is `Shipped` and is not edited. Its AC-0002 and AC-0021 record the behaviour this spec's AC-0001, AC-0002, AC-0003 and AC-0005 replace, and that record stays historical rather than being reopened. Its AC-0012 and AC-0026 are about what the reviewer emits, which this delivery establishes nothing about and therefore does not supersede: they are inherited unchanged, as the byte-unchanged reviewer is.
- Load the module under a name including its pack and skill. Several skills ship same-named scripts, and a bare import binds whichever directory reached the path first.

## Construction tests

Each rule is a fixture pair — one preamble that conforms, one that does not — driven through the module's existing parse. The suite is `packs/core/tests/skills/work-intake/test_intent_shape.py`, and pointer resolution is `test_intent_corpus_lint.py`.

Two separate controls, each credited with only what it proves. `git diff` over `packs/core/.apm/agents/shaping-reviewer.md` being empty establishes byte identity, and nothing else does — the suite asserts selected phrases and the absence of vocabulary members, so it would pass after other bytes changed. The suite re-run **unamended** establishes that the textual properties it names still hold. Neither is evidence that the reviewer decides the new rules — it passes equally against a reviewer that applies none, because the reviewer retrieves nothing and the suite only checks that a generic phrase is present and that no vocabulary member is. What a reviewer emits depends on what a caller puts in its packet, which `intent-metadata-shape-contract` owns and this delivery inherits unchanged.

The migration's oracle is the real-tree run `--dir docs/product/intents --root .` exiting 0.

## Durable-output map

| Durable output | Task | Evidence at closeout |
| --- | --- | --- |
| Interface compatibility — the adopter field table | T4 | Three new rows; the `Status` row names six bare tokens |
| Maintainer procedure — `fix-a-refused-intent.md` | T4 | One worked refusal per new rule |
| Current product truth — the inlined preambles that carried the retired form | T4 | A repository search for `Superseded by <slug>` returns only historical records |
| Release history — the changelog entry | T5 | One entry naming what newly fails and what newly parses |
| Current product truth — the A4 non-goal on `intent-lifecycle-and-closure.md` | T4 | The non-goal states that the cut was confirmed with A4 open, naming the date and the settler |
| Decision rationale — unresolved | not a task | **Closeout blocker**, not delivered here. The changed field contract answers to no decision record, and `intent-metadata-shape-contract` § Follow-ons makes adopter dependence the trigger to settle that. The spec's Durable Outputs row and first Follow-on carry it; `close-work` must find it decided either way |

## Design (LLD)

### Design decisions

- **The seam is chosen per rule kind, by condition 7's words.** Condition 7 obliges "every field whose values the contract fixes carries one of them". A *value shape* is exactly that, so the `Status` vocabulary and the dated-evidence rule go on the shared `validate_live_intent()` surface — the surface that condition refers to. A rule about which field another field's value *requires* is not, so the supersession pairing rule goes on the corpus-lint-only seam beside `validate_supersession()` — the same seam, for the same reason, that `lifecycle-transition-contract` takes for its presence-by-state rules. Applying the distinction to only one of the two rule kinds is the mistake this bullet exists to prevent: it would either put a value rule where condition 7 cannot refer to it, or put a cross-field rule where that condition's words would have to stretch to cover it.
- **The reviewer's text needs no edit, and that is the only reviewer-side fact claimed.** Condition 7 names the obligation and defers every member list to this module, so placing a value rule here keeps that arrangement true for the new rules as for the existing ones. What the reviewer then *emits* is not established by anything in this delivery: it retrieves nothing, so the answer turns on the packet a caller assembles. AC-0007 asserted that outcome and was withdrawn at round 3 for exactly this reason.
- **Resolution is one hop, and only the corpus can decide it.** One hop means exactly this: the target is in the live corpus and is not itself `Superseded`. No other status is excluded, so a `Cancelled` or `Withdrawn` target resolves — only `Superseded` names a successor the pointer would otherwise have to follow. The partition handed to `validate_supersession()` is what makes a target resolvable, so a unit test that builds that set asserts what the test believes the lint passes — the premise, not the behaviour. `resolvable_slugs()` therefore owns the exclusion and the end-to-end control runs through the corpus lint.
- **`Superseded by:` pairs with `Superseded` in both directions.** The forward rule carries what AC-0002 used to say — `Superseded by ` with an empty payload was refused, and the split form of that refusal is a `Superseded` status with no pointer field. The reverse rule is new and prevents the failure the split introduces: a pointer that outlives the status it belonged to is invisible when the value is embedded and silent when it is not.
- **Pointer *resolution* stays corpus-lint-only.** `validate_supersession()` reads other artifacts, and the shared surface is defined as deciding a rule from one artifact alone, so resolution cannot move onto it. Only its source changes: it reads the `Superseded by:` field instead of slicing a prefix off `Status:`.
- **The dated-evidence rule reuses `_is_iso_date` rather than a second pattern.** `_is_iso_date` stays whole-string anchored and stays the one home for the calendar-date rule; the new predicate partitions the value at its first space and hands the head to it. `_check_decomposed` already works this way, so the shape is the module's existing idiom rather than a new one.
- **The literal `no` is refused, and that is the load-bearing difference from `_check_date_or_no`.** A progress field offers an opt-out because an unprobed intent is a real state. These records exist to carry the evidence for a state that claims ratification or delivery, so a value that carries none is not a record.
- **Evidence text is required, not optional.** `lifecycle-transition-contract`'s plan describes these values as a date "optionally followed by free text". That line predates this decision and that spec's own § What Changes defers value shape here, so the spec is right and one line of its plan is stale. That plan is `Approved` and pinned in substance, so **nothing here edits it**: the correction is a controlled amendment that item takes, recorded in this spec's `## Follow-ons`.

### Data & schema

| Field | Tier | Value |
| --- | --- | --- |
| `Status` | required | one of six bare tokens: `Draft`, `Accepted`, `Fulfilled`, `Withdrawn`, `Cancelled`, `Superseded` |
| `Superseded by` | unconstrained | the `Slug:` of a live, non-superseded intent. It carries **no** value rule: `Slug:` is never judged on its value, so a pointer at one must not be either. Presence-pairing and resolution are corpus-scoped |
| `Accepted` | constrained when present | `YYYY-MM-DD`, a space, then non-empty text |
| `Fulfilled` | constrained when present | `YYYY-MM-DD`, a space, then non-empty text |

### Behavior & rules

The spec's criteria own the rule set. This is the implementation's dispatch shape:

| Input | Outcome | Criterion |
| --- | --- | --- |
| `Status: Superseded by a-slug` | refused — outside the vocabulary | AC-0001 |
| `Status: Superseded`, no `Superseded by:` | refused by the corpus lint only | AC-0002 |
| `Status: Superseded`, `Superseded by:` empty after normalization | refused as absent, by the corpus lint only | AC-0002 |
| `Status: Draft`, `Superseded by: a-slug` | refused by the corpus lint only | AC-0003 |
| `Status: Superseded`, `Superseded by: a-ghost` | accepted on the shared surface, refused by the corpus lint | AC-0005 |
| `a` → `b` where `b` is itself `Superseded` | refused by the corpus lint: one hop | AC-0005 |
| `Accepted: 2026-09-20  by eugenelim` (two spaces) | accepted | AC-0004 |
| `Accepted: 2026-09-20` | refused — no evidence | AC-0004 |
| `Accepted: 2026-09-20, on a clean review` | refused — `2026-09-20,` is not a date | AC-0004 |
| `Accepted: no` | refused | AC-0004 |
| `Accepted: 2026-09-20 by eugenelim` | accepted | AC-0004 |

## Tasks

### T1: Split supersession into a status token and a pointer field

**Depends on:** none

**Mode:** TDD

**Approach:** `STATUS_BARE_VALUES` becomes `STATUS_VALUES` and gains `Superseded`; `SUPERSEDED_PREFIX`, its branch in `_check_status`, and the prefix slice in `superseding_slug()` all go. `superseding_slug()` reads the `Superseded by:` field. The pairing rule goes in `_check_supersession_pair`, called from `validate_supersession()` — the corpus-lint-only seam — and **not** from `validate_live_intent()`, per the seam decision above. `Superseded by:` gets no value rule of its own.

**Tests:**
- `Status: Superseded` is accepted; `Status: Superseded by a-slug` and `Superseded by ` are refused — AC-0001.
- `Superseded` with no pointer, and with a pointer emptied by the normalization stage, are each refused naming the field — AC-0002.
- A pointer beside each of the five non-`Superseded` tokens is refused — AC-0003. Its own case, not a variant of AC-0002's: an implementation that refuses every `Superseded by:` passes AC-0002's fixtures.
- A conforming `Superseded` + `Superseded by:` pair is accepted, so neither rule refuses the state it exists to admit — AC-0001, AC-0002, AC-0003.
- A pointer value is accepted wherever the same value is accepted as a `Slug:`, fed to both fields in one case so the two cannot drift apart — AC-0006.

**Done when:** its `Tests:` pass.

### T2: Resolve the pointer from its own field

**Depends on:** T1

**Mode:** TDD

**Approach:** `validate_supersession()` keeps its signature and its seam; only the value it reads moves.

**Tests:**
- A pointer naming a live intent's `Slug:` is accepted; one naming no live slug is refused, and the message names both the intent and the slug — AC-0005.
- A pointer whose target is itself superseded is refused, pinning the single-hop rule AC-0005 states — AC-0005.
- The corpus-lint path reports the refusal with the corpus-relative name it already reports — AC-0005.

**Done when:** its `Tests:` pass.

### T3: A dated-evidence value rule, and the one intent that fails it

**Depends on:** none

**Mode:** TDD

**Approach:** One predicate partitioning at the first space and delegating the head to `_is_iso_date`, registered in `VALUE_RULES` at both field names. The corpus edit removes the comma from `architect-design-gate-calibration.md`'s `Accepted:` date token; the record's evidence text is untouched.

**Tests:**
- At `Accepted:` and at `Fulfilled:` independently: a date with evidence is accepted; a bare date, the literal `no`, `2026-09-20,` with evidence, the basic form `20260920` with evidence, and a date followed only by whitespace are each refused — AC-0004.
- `_is_iso_date` is unchanged, asserted by the shipped `De-risked:`/`Shaping-reviewed:`/`Decomposed:` cases passing unamended — AC-0004.
- The real-tree run exits 0 — AC-0012.

**Done when:** its `Tests:` pass and the real-tree run exits 0.

### T4: The projected surfaces

**Depends on:** T1, T3

**Mode:** Goal-based check

**Approach:** The prose surfaces that carried a copy of what the module now decides. `intake-intent`'s template is not one of them — it seeds `Status: Draft` and never offered the retired form — so it is unchanged and only has to keep passing conformance. `lifecycle-transition-contract`'s plan is **not** touched: it is `Approved` and therefore pinned in substance, so its two stale lines are recorded as a Follow-on and noted on its `workspace.toml` entry as non-blocking context for a human reader, from which dispatch derives nothing.

**Tests:**
- The field table carries a row for `Superseded by`, `Accepted` and `Fulfilled`, and its `Status` row names six bare tokens — AC-0009.
- A repository search for `Superseded by <slug>` over the five named projection surfaces returns nothing — AC-0010.
- `fix-a-refused-intent.md` names each of the three new refusal messages with its remedy, and the message strings match the module's — AC-0011.
- `intent-lifecycle-and-closure.md`'s retention non-goal records that its slice cut was confirmed with A4 open. Outside this spec's criteria and bundled on explicit owner instruction; the spec's `## What Changes` records that authority.
- `lifecycle-transition-contract/plan.md` is byte-unchanged against its committed state, and its `needs` stays empty: it does not wait on this spec reaching a terminal state, so an edge would assert a dependency that does not exist. Its entry comment is non-blocking context, not a dispatch signal. Its two stale lines are recorded in this spec's `## Follow-ons` as controlled-amendment work that item owns, and its workspace entry carries a comment saying so. That comment is context for a human reader and nothing more: `work-loop` forbids reconstructing a requirement from a comment, so nothing derives a block from it and the entry stays dispatchable.
- The renderer's output and the resolved template each pass `validate_live_intent()` **and** `validate_supersession()`, and each control is paired with a mutation that seeds a stranded pointer, so a stubbed rule fails them — AC-0013.

**Done when:** its `Tests:` pass.

### T5: Reviewer evidence, reprojection, version bump and changelog

**Depends on:** T1, T2, T3, T4

**Mode:** Goal-based check

**Tests:**
- `git diff` over `packs/core/.apm/agents/shaping-reviewer.md` is empty, which is what establishes AC-0008's byte identity — AC-0008.
- `packs/core/tests/pack/test_shaping_review_contract.py` passes **unamended**, establishing that the textual properties it asserts still hold. It does not establish byte identity and is not evidence about reviewer output; see the Construction tests note above.
- `packs/core/tests/skills/work-intake/` passes whole, inherited cases included.
- `pack.toml` and `.claude-plugin/plugin.json` carry matching bumped versions, `make build-self` reprojects cleanly, and the changelog entry names what newly fails.

**Done when:** its `Tests:` pass.

## Rollout

- **Delivery:** big bang. No intent carries `Status: Superseded` today, so the vocabulary change has an empty corpus; the one dated-evidence edit is a single character and is not reversed by removing the rules.
- **Infrastructure:** none.
- **External-system integration:** none.

## Changelog

- 2026-09-23 — approved by eugenelim alongside the spec, on the basis its `Approved:` line records.
- 2026-09-23 — drafted as slice 6 of `brief:intent-identity-and-registration`, from the two 2026-09-23 inbound entries in that brief's § Post-Ready decisions.
- 2026-09-23 — T1–T5 complete. `packs/core/tests/skills/work-intake/` 493 passed in 8.7s; `packs/core/tests/skills/intake-intent/` and the roster template file pass; `packs/core/tests/pack/test_shaping_review_contract.py` 37 passed **unamended** with `git diff` over `shaping-reviewer.md` empty; the real-tree corpus lint exits 0 after one migration (`architect-design-gate-calibration.md`).
- 2026-09-23 — five Blockers from an independent Codex review, all sustained after probing, all repaired: one-hop resolution was claimed in the guides but not enforced (a chain exited 0 through the real lint); the dated-evidence criterion overclaimed "one space"; the supersession pairing rule was on the wrong seam for its own rule kind; the changed field contract's missing decision record was marked not-applicable rather than recorded as a closeout blocker; and an `Approved` sibling plan was edited in substance and is now reverted.
- 2026-09-23 — three CI-only failures on the dispatched roster and corpus runs, all real and none reachable from the local gate: `tests/roster/test_intent_field_reference_parity.py` derives a documented field's tier from `VALUE_RULES` membership, so moving every `Superseded by` rule off that table made the published page state a tier the validator did not hold; and `test_workspace_status_projection.py` raised `impossible_transition` for an `Implementing` spec whose workspace entry sat in `queue`. Repaired by separating the pointer's own value rule (AC-0014, shared surface) from the pairing rule (corpus-only), and by moving the entry to `active`.
- 2026-09-23 — round 2 raised seven Blockers; five sustained and repaired, one was already correctly placed, one refuted. Sustained: AC-0014 was a parity-test shim whose premise was false — `Slug: two words` is accepted and resolvable, so refusing the same value as a pointer would refuse a target the contract admits; it is withdrawn and `Superseded by:` is published as `unconstrained`, which is what the validator holds. AC-0005 now states the precondition the code enforces. Four surfaces still said "one space" against a contract the brief handed over as "a space". Tasks T1 and T4 still described the pre-repair seam and an edit that was reverted. The stale sibling plan was flagged on its `workspace.toml` entry rather than only in a Follow-on (round 4 reverted the blocking form of this; see below). Already placed: the missing decision record is a closeout blocker on an `Implementing` spec, which is where the spec template puts an unresolved destination. Refuted: fenced refusal examples wrap across lines, and the pre-existing guide at `HEAD~1` wraps them the same way, so that is house style rather than a defect this change introduced.
- 2026-09-23 — round 3 raised five Blockers and two Concerns. Repaired: plan remnants of the withdrawn AC-0014; AC-0007 withdrawn, because it asserted what a shaping reviewer emits and the reviewer retrieves nothing, so no evidence here can establish it — the surface placement it stood in for is now stated directly and AC-0006 states it; the `unconstrained` tier definition on the adopter page now admits a corpus-scoped rule, which is what `Superseded by:` has; AC-0013 and both template controls now exercise the corpus-scoped surface too, since passing `validate_live_intent()` alone is not passing the contract; and the stale sibling plan is blocked by a real `needs` edge rather than a comment, because the workspace contract says a comment is not semantic and dispatch does not reconstruct a requirement from one. Two items are gates rather than code and are surfaced to the owner unresolved: the decision record the changed field contract owes, and the spec-mode shaping review that did not run before approval.
- 2026-09-23 — round 4 raised five Blockers, and **every one was the class round 3 named**, which is the confirmation that the class is real and the repairs were local. The withdrawn reviewer-outcome claim survived on four further surfaces (brief, changelog, workspace summary, plan) after being cut from the spec — repaired the class this time, with a sweep. Both new template controls passed against a stubbed rule; each now carries a mutation that seeds a stranded pointer, verified to fail 2 of 29 with the rule stubbed and pass 29 of 29 restored. The round-3 `needs` edge asserted a dependency both briefs deny — `needs` means the target must reach a terminal state, and the sibling needs its own plan amended, not this spec shipped; reverted to empty, with the amendment tracked in Follow-ons. The plan's T4 and T5 still cited the reverted comment and the withdrawn AC-0007, and its durable-output map omitted the decision-rationale blocker. The guides and changelog said the check requires text naming who decided and on what evidence; it requires only non-empty text, and all four surfaces now say so and mark the rest as author guidance.
- 2026-09-23 — round 5 raised five Blockers, the same class a fifth time, all in the record rather than the code. AC-0008 asserted six reviewer tokens where there are seven; it now states byte identity, which is the thing actually checked, and asserts no count. The withdrawn reviewer-outcome claim survived in the plan's seam bullets and in two module docstrings — swept again, this time including the shipped `.apm/` prose. The unamended contract suite was credited with byte identity it cannot establish; the empty diff establishes that and the suite is now credited only with the textual properties it asserts. The plan still mapped withdrawn AC-0007 as a superseding criterion and still said T4 corrects the sibling plan, which was reverted at round 2. And the A4 non-goal correction on `intent-lifecycle-and-closure.md` — bundled on explicit owner instruction with the slice request — was in the diff with nothing in the record admitting it; the spec's `## What Changes` now carries that authority and the durable-output map carries its verification.
- 2026-09-23 — round 6 raised six Blockers. Five were the same class a sixth time and one was a real missing control. The spec forbade "a seventh `MALFORMED` token" and elsewhere named "seven", both counting a reviewer this delivery does not touch; AC-0008 and its Agent Rule now assert byte identity and no count. The plan's supersession map claimed this spec's corpus-only criteria supersede the shipped AC-0012 and AC-0026, which are about reviewer output — those are inherited, not superseded, and the map now says so. T4 still described the sibling's entry comment as somewhere "dispatch reads"; it is non-blocking context and the plan now says that too. Two findings landed on prose this delivery inherited rather than wrote — `intent_shape.py`'s module docstring and `fix-a-refused-intent.md`'s opening, both from `intent-metadata-shape-contract`. They are living files, not frozen records, and they now contradicted corrected prose lower in the same files, so both were corrected here rather than left as two answers to one question. The real control: AC-0006's seam was proven one-way only. An implementation that also judged `Status:` or a dated record inside `validate_supersession()` passed every case in the file. The new reverse control fails against exactly that mutant, verified 1 failed of 235.
- 2026-09-23 — round 7 raised seven Blockers, a Concern and a Nit. Three were real and four were the class again. **A gate violation:** round 6's seam docstring cited `docs/specs/lifecycle-transition-contract/`, and `packs/AGENTS.md` forbids an internal-governance citation in shipped pack content; the rationale is now stated portably, and the canonical grep in `packs/AGENTS.local.md` is clean for this delivery's lines. **Two controls that could not fail:** AC-0009 had no artifact that fails when a documented row is deleted — the parity suite exempts every `unconstrained` row by design, so dropping the `Superseded by` row left it green; two named controls now fail on a deleted row and on a drifted `Status` member list, verified 1 of 7 each way. And the one-home date test ran matching examples through both paths, which a duplicated implementation also passes; it now substitutes `_is_iso_date` and asserts the dated-evidence rule changes with it. The rest: the brief still listed AC-0012 and AC-0026 among the criteria this slice supersedes, when they are inherited; round 6's guide repair over-corrected into a new false claim, that a shaping review emits `MALFORMED(shape)` "and nothing else", ignoring one token per failed condition and the owner suppression; T4 still said "dispatch reads"; the round counts were stale at three and five; the slice-6 comment sat above the sibling's queue row rather than its own; and T2 pointed at Assumptions for a rule AC-0005 owns.
- 2026-09-23 — round 8 raised four Blockers and a nit, and three were the same shape: a control added in round 7 covered `Accepted` and left `Fulfilled` to drift. The named row control now asserts the whole dated-evidence rule at both fields independently, the delegation control runs at both, and the `Status` control compares an exact set parsed from the row's enumeration rather than checking membership — the membership form passed with a seventh token documented. Verified by mutation, 1 failed of 7 for each of: a further `Status` token, a gutted `Fulfilled` rule, and a deleted `Superseded by` row. The count word was also dropped from the `Status` row, for the same reason every other count was. The changelog said the value rules are seen by "any surface reading one intent", which is wider than `validate_live_intent`; it now names the function.
- 2026-09-23 — round 9 raised two Blockers, down from seven and four. Round 8's `Status` control parsed only the value cell's first sentence, so a token documented after the first full stop stayed invisible — the blind spot had moved rather than closed. Rather than add an exclusion list, the row was made free of any backticked name that is not a member (it now refers to the pointer field in prose), so the control scans the whole cell and converges. Verified 1 failed of 7 for a token in the first sentence, a token after it, and a removed member. The second Blocker is this record committing its own named class: three current surfaces carried a review-round total and all three went stale when round 8 ran. Every live total is now gone — the per-round entries here are the record — and "state no running total of anything a later round changes" is the third lesson in the spec's Follow-on.
- 2026-09-23 — round 10 raised two Blockers, both proven by the reviewer running the mutations. The `Status` parity control had a third blind spot: it took the *first* matching row, so a duplicate `Status` row documenting an extra token was invisible, and its character class allowed only letters and hyphens, so `Draft2` slipped through. Three attempts at this control each moved the blind spot rather than closing it — scoped to a sentence, then narrowed by a character class. It now requires exactly one `Status` row and compares an exact set of every backticked run in the value cell, which needs no exclusion list and has nowhere left to hide. Verified 1 failed of 7 against a digit token, a duplicate row, a token after the first full stop, and a removed member. The brief still said `architect-design-gate-calibration.md` "is refused" — present tense about a file this delivery migrated on its first commit. Rewritten as the pre-migration evidence it is, naming the delivered state.
- 2026-09-23 — round 11 raised three Blockers, and one of them ended the loop the parity control had been in. **The decisive finding:** those controls asserted keywords in prose, and a keyword check cannot tell `resolution is one hop` from `resolution is *not* one hop` — negating any documented rule left all seven green. Together with the duplicate-row check that recognised only one spelling of a valid table row, that is the third consecutive round in which tightening this control moved its blind spot rather than closing it: a sentence-scoped parse, then a character class, then a literal row spelling. A predicate welded to prose has no convergent form, so the prose assertions were **removed rather than tightened again**. What stays is what a test can settle: which fields are documented, at which tier, with exactly one row each (parsed with the same tolerant spacing the file's own row regex uses), and the `Status` vocabulary as an exact set derived from `STATUS_VALUES`. Whether the prose is *true* is now a closeout condition on the Interface-compatibility row, and the test file states that boundary where the next author will find it. Verified 1-2 failed of 8 against seven mutations, including the padded-spacing duplicate row that defeated round 10's version. Third: the brief restated `intent-metadata-shape-contract`'s live `Shipped` token in prose, which the auto-derived Spec map column owns; the prose now says it has shipped and points at the column.
- 2026-09-23 — round 12 raised three Blockers, and the first is the best finding of the review. **The `## Outcome`** — written before round 1 and never revisited through eleven rounds of correcting everything below it — promised that "a state claiming delivery cannot be made without saying what delivered it". That is presence-by-state, which is `lifecycle-transition-contract`'s and not this slice's: `Status: Fulfilled` with no `Fulfilled:` record passes both validators here. The Outcome now claims only the shape enforced when a record is present, and hands presence back to the contract that owns it. The lesson generalises — every round attacked the criteria and the evidence, and the one section nobody re-read was the one written first. Second: the duplicate-row check compared raw field names while the file's own `_documented()` strips them, so `| ` Status ` |` was a second row the parser saw and the check did not. Both now normalise the same way; verified against padded names and padded pipes. Third: the how-to told a reader that `MALFORMED(shape)` stands for one of its messages. It does not — an unsettled condition fails closed, and the corpus-only supersession rules never produce that token at all. The page now says the token means run the check, and that a token with no corpus line behind it points at the packet rather than the intent.
- 2026-09-23 — round 13 raised three Blockers, all prose, all the same class. The brief still restated `intent-metadata-shape-contract`'s live status in its own words after round 11 pointed it at the auto-derived Spec map column; the assertion is now gone rather than rephrased. The record counted `intake-intent`'s template among the surfaces migrated off `Superseded by <slug>` — it seeds `Status: Draft` and never carried the retired form, so it is unchanged and is named as a conformance target instead. And the one-hop rationale said a pointer must reach the bet "actually running now", which claims an active-status rule `resolvable_slugs()` does not enforce: it excludes only tombstones and `Superseded` targets, so a `Cancelled` or `Withdrawn` target resolves. All three surfaces — the guide, the module docstring and the plan — now state the contracted rule and nothing beyond it.
- 2026-09-23 — round 14 was framed as a termination round, asked only for findings that would mislead a reader, break at runtime, let a defect through a gate or misrepresent what shipped — and it found a real gate violation fourteen rounds late. **`packs/AGENTS.md` requires a non-cosmetic pack update to update that pack's eval harness.** Both packs were version-bumped and neither harness was touched, so every rule this slice ships sat outside the pack-eval gate. `work-intake` gains three cases (the split supersession form, the stranded-pointer refusal and its corpus-only attribution, and the dated ratification record); `frame-intent` gains one for the template's bare-token `Status` and its separate pointer field. Both files keep their own formatting — the first attempt un-escaped existing sequences and was redone as pure additions. Second: the brief still counted `intake-intent`'s template among the migrated surfaces after the spec and plan were corrected in round 13. It seeds `Status: Draft`, never carried the retired form, and is unchanged; four surfaces were migrated, not five. AC-0010 is unaffected — it is a negative guard over a named set, not a migration claim.
- 2026-09-24 — round 15 raised one Blocker, and it was a defect introduced by round 14's own repair: the new `frame-intent` eval said `Superseded by:` carries "the replaced bet's slug". It carries the **successor's**. Its prompt was wrong-footed the same way, asking about the intent that *did* the replacing rather than the one retired — so the case would have rewarded a backward pointer, which is worse than the absent coverage it was added to fix. Prompt, expected output and all four assertions rewritten; the three `work-intake` cases were audited for the same error and are correct. `pack-evals` passed on the previous revision, so the harness shape was already valid — the gate could not have caught this, because a wrong assertion is still a well-formed one.
- 2026-09-24 — closeout. Every durable-output condition was checked rather than asserted: all four documented tiers match the module and the `Status` vocabulary is an exact set (Interface compatibility); all six new refusal messages appear byte-exact in `fix-a-refused-intent.md`, compared by running the module (Maintainer procedure); and the retired `Superseded by <slug>` form survives only in historical records (Current product truth) — which took two further corrections found by the check itself, `intent-renumber-and-reissue/spec.md` (Draft, and it also still called the pointer's home an open question this slice settled) and, on owner instruction, the two stale lines in `lifecycle-transition-contract/plan.md`. One named exception stands: `lifecycle-transition-contract/spec.md` § What Changes still spells the retired form inside a deferral. That spec is `Approved` and pinned in substance, the owner's instruction named its plan, and the sentence's function — "not changed here" — remains true, with its next clause routing the reader to this brief. Recorded rather than edited. The Decision-rationale blocker was settled by the owner on 2026-09-24: no decision record is owed, on the three grounds the spec's Follow-on states. Spec `Shipped`, plan `Done`, workspace entry moved to `shipped`.
