# Spec: Channel minimum width

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs/specs/rendered-page-channel-axis/spec.md`](../rendered-page-channel-axis/spec.md)
  — establishes the channel axis, its six rule rows, and the controls two
  criteria here lean on. It is `Shipped` and this work does not amend it.
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them when
> a finding is adjudicated is the reviewing surface's.

## Objective

A team using the `frontend-engineering` pack inspects a surface that has one
channel — an internal tool with a 1280-pixel minimum, a fixed-container embed, a
print-oriented report — and the step stops demanding a capture below the width
the surface supports.

The channel axis requires every band a surface has, and derives those bands from
declared breakpoints or from two default bands at `narrow <=480` and
`wide >=1024`. Every path produces at least two channels, so a single-channel
surface is required to capture at a width it does not support and is then judged
on what it renders there. The two outcomes are a finding against a width the
surface never claimed, or an adopter recording the run as incomplete and
learning to distrust the step.

A surface declares its supported minimum width. Bands lying wholly below it stop
being required, and the lowest surviving band starts at the minimum where it
would otherwise start below it, so a 1280-minimum surface needs four captures in
one channel rather than eight across two. The minimum raises a band's lower bound
and never lowers one, so it cannot invent a capture width the surface never
claimed. A breakpoint above the minimum still carries its own band, so a minimum cannot
collapse a surface that declares breakpoints above it. A minimum above every
declared breakpoint does leave one channel, and records every breakpoint it
discarded so the choice is visible.

Success for the adopter is that the step asks for the widths their surface has
and no others, and that the run records the minimum it used and any declared
breakpoint the minimum discarded.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth — rule layer | Applicable — the reference is the executable contract the step and its checks both read | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/rendered-page-inspection.md` § Channels | pack maintainer | Two new rule rows present and read by the module; deleting either reds the capture-set checks | The reference and the checks that read it agree |
| Current product truth — adopter-facing skill | Applicable — `SKILL.md` § 5a restates the capture contract for the agent that performs it | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` § 5a and its evidence-manifest table | pack maintainer | § 5a states the minimum input and its effect; the manifest records the minimum and any discarded breakpoint | Both copies state one contract |
| Current product truth — journey input | Applicable — `JOURNEY.md:12` declares what the adopter brings, and this adds an input | `packs/frontend-engineering/JOURNEY.md` **and** `web/src/content/journeys/frontend-engineering.md`, the committed web copy the journey sync writes | pack maintainer | `youProvide` names the supported minimum width in both files, with the web copy regenerated rather than hand-edited | Both copies state one input list |
| Adopter guidance | Applicable — the shipped how-to teaches the capture set by example | `guides/frontend-engineering/how-to/inspect-the-rendered-page.md` | pack maintainer | The guide walks a single-channel surface and says what the minimum does to the required set | An adopter with a desktop-only surface can produce a complete set from the guide alone |
| Decision rationale | Applicable — "drop then clamp" and the two-field record were chosen over three alternatives each, and neither is recoverable from the result | this spec's Objective, Acceptance Criteria, and Assumptions | spec owner | The criteria state the derivation and the recording; the Assumptions record what was settled and when | A future reader can see why the basis stayed two values and gained a sibling field |
| Reusable learning — eval harness | Applicable — `packs/AGENTS.md` § *Security and authoring rules* obliges a non-cosmetic pack update to update that pack's eval harness | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json` | pack maintainer | The `rendered-page-inspection` case names the minimum among the behaviours it expects | The harness exercises the shipped input |
| Interface compatibility — superseded criterion | Applicable — this delivery makes two criteria the `Shipped` predecessor carries as met false as unconditional rules | `docs/specs/rendered-page-channel-axis/spec.md` `Status:` line pointer | spec owner | A `Status:` line pointer naming this spec as the successor for that spec's AC-0001 and AC-0002; the frozen body is not edited | Both frozen ticks are traceable to the criteria that now supersede them |
| Execution observation | Applicable — a completeness test cannot show that one channel was enough to judge a page; only a performed run can | `docs/specs/channel-minimum-width/notes/verification-ledger.md` | spec owner | The run's observations, result state, verdict, minimum in force, and any discarded breakpoint | The ledger carries all five values for one real single-channel surface |
| Release history | Applicable — pack content changes | `packs/frontend-engineering/pack.toml`, `packs/frontend-engineering/.claude-plugin/plugin.json`, the root `.claude-plugin/marketplace.json` entry, `docs/product/changelog.md` | release workflow | Matching version bump in both manifests; a changelog entry led by the pack and that version | Versions and changelog agree with shipped content |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Let the shipped tables state every rule, and let the rule-reading module read
  them. A check that supplies its own quantifier asserts behaviour the pack
  never promised an adopter. One carve-out, stated rather than left implicit:
  the three band-*name* templates are module-owned and appear in no shipped
  table, because a band name is an internal identifier the walk happens to
  print, not a rule an adopter follows. This delivery keeps them where they are, and the
  reason is not the channel-name sweep: that sweep reads its expected set from
  the reference's own three-cell rows, so a row added there enters both sides of
  its equality and ships it green. The control that reds a new fallback band is
  `test_fallback_channels_are_the_two_shipped_bands`, which pins the pair
  literally. The sweep's reach is prose, and rows in any *other* `.apm/**`
  file — not a row in the file T1 edits.
- Prove every rule row the completeness walk depends on is present before the
  walk runs, so deleting any of them raises rather than skipping the rule it
  governs.
- Record what the minimum did, not only what it was: the value in force and any
  declared breakpoint it discarded.
- Keep the minimum optional. A surface that declares none behaves exactly as it
  does today.
- Restore a mutated file by editing it back, never by `git checkout`, `git reset`
  or `git stash` — a failed restore leaves a dirty tree that reads as a defect.
- Name no channel in shipped content outside the fallback band names the
  reference declares. A shipped sweep asserts set *equality* between the channel
  names it harvests across `.apm/**` and those two declared names, so a new name
  reds it in either of the two shapes that reach it: a three-cell table row
  **inside a `## Channels` section**, and prose of the form
  `` `name` at <operator> `` **in a paragraph containing the word *channel***.
  Prose outside those two shapes ships green — that is the control's documented
  blind spot, not a licence to add names. Widening its shapes or its expected set
  to accommodate new prose would narrow the guard that also carries the
  device-name prohibition.

### Ask first

- Adding a maximum width, or any second bound on the channel range.
- Changing the band values *as the reference table states them* — the two
  fallback bands, the height bands, the scroll-position rule, or the
  capture-width rule. Clamping a band's lower bound at derivation time is what
  this delivery does and needs no sign-off; editing the shipped cells does.
- Making the minimum mandatory, or defaulting it to any value other than absent.
- Adding a third value to the channel-basis vocabulary.

### Never do

- Let a declared minimum discard a breakpoint above it. A minimum narrows the
  range a surface supports; it does not overrule a band inside that range.
- Infer the minimum from the surface's stylesheets, markup or rendered output.
  It is declared, because static analysis cannot answer what a page emits.
- Introduce a new top-level directory, a new module boundary in the pack's test
  tree, or a second rule-reading module. The existing
  `frontend_engineering_rendered_page_rules.py` is the one reader.
- Add the minimum, the basis, or the discarded breakpoints to the
  `## Capture record` table. Those five fields describe one capture each; the
  minimum is one fact per run, and a required row there would make every capture
  in every existing set unusable.
- Name a device in shipped pack content as the definition of a channel or a
  minimum.
- Cite this repository, its paths or its records inside
  `packs/frontend-engineering/.apm/**`.

## Testing Strategy

- **The admissible value (AC-0001):** TDD in `packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_capture_contract.py`. Its fixtures are refusal cases, not derivation cases: a fractional value, zero, a negative value, and a boolean. The probe recorded no refusal, so none of these come from it.
- **The derivation (AC-0002, AC-0003, AC-0004):** TDD in the same module. Each is a compressible invariant over data — a minimum and a breakpoint list either yield the stated bands or they do not — and every expectation is read from the shipped tables. The fixtures extend the five cases the probe recorded (a minimum with no breakpoints, with a breakpoint below it, with one above it, with several above it, and absent) with the three cases the probe did not reach: a band bounded on both sides lying wholly below the minimum, a minimum equal to an inclusive upper bound, and a minimum equal to an exclusive one. The minimum-absent case is not a fixture here — it is the shipped five-case derivation suite, which this delivery leaves passing unchanged, and AC-0019's second fixture, which requires an absent minimum to keep a single-channel set incomplete.
- **The verdict (AC-0019, AC-0020):** TDD in the same module. AC-0019 asserts `evaluate_capture_set` and AC-0020 asserts `inspection_result` above it, because the result an adopter records is the outermost observable and every frame below it can be right while that one ignores the minimum. Paired fixtures, with and without the minimum, so the criterion measures the minimum's effect rather than the walk's baseline.
- **Channel disjointness (AC-0017):** TDD in the same module, swept over the cross product AC-0017 names — every minimum against every breakpoint list appearing in these criteria — not over the fixture inputs alone, which their own exact-equality assertions already pin.
- **The rows in force (AC-0005, AC-0015, AC-0016):** TDD in the same module. AC-0005 is presence inheritance and needs no new test — the shipped parametrized control plus the equality control already carry it once the rows land in `REQUIRED_RULE_ROWS`. AC-0015 and AC-0016 are what make the rows load-bearing, and their mutation **edits the value cell** rather than deleting the row: the presence loop reds on a deletion whether or not any code reads the row, so deletion cannot demonstrate that it is read.
- **The recorded effects (AC-0006, AC-0007, AC-0018):** TDD in the same module. AC-0006 and AC-0007 assert what the two recording readers return from run inputs; AC-0018 asserts the § 5a manifest row that actually carries the record, which is a different surface and needs its own fixture. Two reader criteria rather than one, because the value in force and the breakpoints it discarded are separate facts with separate failure modes.
- **Superseded claims (AC-0021):** TDD in `test_rendered_page_shipped_content_limits.py`, which already owns the universal claims over shipped prose and states each one's search vocabulary in the open. One sweep over a named anchor set rather than a clause per surface, because the per-surface form regenerated a new instance in each of three consecutive rounds; its reach is its anchor list, and that list is the blind spot a reviewer inspects.
- **Adopter surfaces (AC-0008, AC-0009, AC-0010):** TDD, not goal-based checks — each is a literal search over shipped text, so each has an owning module and a named test rather than a one-line command. AC-0008 joins the § 5a assertions in `test_rendered_page_capture_contract.py`; AC-0009 goes in `test_rendered_page_journey_promise.py`, which owns what the journey promises; AC-0010 goes in `test_rendered_page_verdict.py`, the one pack module that already reads the shipped how-to. Each names the string it searches for, so its reach is the artifact a reviewer inspects.
- **Eval harness (AC-0011):** TDD in `test_rendered_page_reviewer_sight.py` — a parse of `evals/evals.json` asserting the `rendered-page-inspection` case names the minimum.
- **Pack delivery (AC-0012, AC-0013):** goal-based checks compare the two manifests' version fields, confirm the changelog entry is this pack's topmost release heading and sits below the `core` heading, and run `agentbundle catalogue lint --deep` and `catalogue verify`.
- **Interface compatibility (AC-0022):** TDD in `tests/roster/test_channel_minimum_width_supersession.py`, matching the predecessor's own supersession test rather than inventing a shape. Roster rather than the pack suite, because the assertion is about a governance artifact in `docs/specs/`, not about pack content.
- **The step performed (AC-0014):** visual / manual QA. Run the capture against a real single-channel surface with a minimum declared and record the observations, the result state, the verdict, the minimum in force, and any discarded breakpoint. A passing completeness test is not evidence that one channel was enough.

## Acceptance Criteria

<!-- Derivation -->
- [ ] **AC-0020.** The inspection result an adopter records honours the minimum, so a supported surface reads as a completed inspection. Construction test: `test_the_inspection_result_honours_the_declared_minimum`; fixtures: `inspection_result` over the four-capture single-channel set at 1280 with no findings and a 1280 minimum returns `{"state": "completed", "verdict": "pass"}` and `is_completed_inspection_result` returns `True`; the same call with no minimum returns `state: "incomplete"` and `is_completed_inspection_result` returns `False`. `inspection_result` forwards only the breakpoints to the walk today, so AC-0019 stops one call frame short of what an adopter sees — and a run recorded as incomplete for a surface captured at every width it supports is verbatim the outcome the Objective exists to remove. AC-0014 records this state but obliges no value, so it cannot substitute.
- [ ] **AC-0019.** The completeness walk takes the declared minimum as a run input and honours it, so a capture set covering only the surviving channels is `complete`. Construction test: `test_the_walk_honours_the_declared_minimum`; fixtures: a four-capture single-channel set at 1280 against a 1280-minimum fallback surface, which returns `("complete", [])`; that same set under a **480** minimum, which drops nothing because `narrow`'s `<=480` survives, and so stays `incomplete` naming the missing narrow channel; and that set against breakpoints `[768]` with a 1280 minimum, whose one surviving channel `>=1280` is captured at 1280, which returns `("complete", [])`. The 480 fixture is the discriminating pair, not a no-minimum run: a no-minimum run over this set is already asserted by the shipped `test_a_single_channel_set_is_incomplete`, so pairing against it would add no observation the suite does not already make, while the 480 case catches a walk that treats any declared minimum as one channel. The declared-breakpoints fixture is required because the derivation returns the fallback bands on its own fork, so a walk that forwards the minimum only when no breakpoints are declared would otherwise pass. This is the criterion that reaches the delivery's outcome: the derivation criteria below assert `required_channels` in isolation, and an implementation can satisfy every one of them while the walk still derives its bands without the minimum and reports a supported surface incomplete. The second fixture is what makes the first mean something — without it, a walk that ignores channels entirely would pass.
- [ ] **AC-0001.** A declared minimum width is a positive whole number of CSS pixels, and a run refuses any other value while admitting absence, on the same footing as a declared breakpoint. Construction test: `test_a_declared_minimum_must_be_a_positive_whole_number`; fixtures: a fractional value, zero, a negative value, and a boolean, which `isinstance(True, int)` admits unless excluded, each refused; and `None`, which is admitted, because *Always do* keeps the minimum optional and a refusal contract stated only on one side would read as refusing absence too.
- [ ] **AC-0002.** A band whose entire width range lies below the declared minimum is not a required channel, whether that band is bounded below or not. Construction test: `test_a_band_wholly_below_the_minimum_is_dropped`; fixtures: the two fallback bands under a 1280 minimum, where `narrow` is dropped; a declared breakpoint of 768 under the same minimum, where its lower band is dropped; breakpoints `[400, 800]` under a 1280 minimum, where two bands are dropped and one of them — `>=400 <800` — is bounded on both sides, yielding one channel captured at 1280; a minimum of 768 against breakpoints `[768, 1024]`, where `<768` admits no width at or above the minimum and is dropped, yielding two channels at 768 and 1024; and a minimum of 480 against the fallback bands, where `narrow`'s `<=480` admits exactly 480 and therefore survives, yielding two channels. Every fixture asserts exact equality on the full returned band list as `(lower, upper)` pairs, never on channel counts or capture widths alone: `[(">=1280", "")]`; `[("from-1280", ">=1280", "")]` as a full name-bearing triple; `[(">=1280", "")]`; and `[(">=768", "<1024"), (">=1024", "")]`. The `[768]` fixture carries the name because a clamped *unbounded top* band is the delivery's motivating shape, and the rename rule AC-0003 states for the `{lower}-to-{upper}` template must reach the `from-{bn}` one too: an implementation recomputing only the two-bound template leaves a channel named `from-768` starting at 1280, which the walk then prints in its incomplete report. The 480 fixture asserts full `(name, lower, upper)` triples — `[("narrow", ">=480", "<=480"), ("wide", ">=1024", "")]` — because it is the only input that produces a clamped *fallback* band, and the rule that such a band keeps its table name would otherwise be unfalsifiable: an implementation applying the breakpoint renaming convention uniformly would emit `480-to-480` with every other fixture green, and the band name reaches the walk's incomplete report. Three fixtures exist to close a cheaper filter: keying on an absent lower bound satisfies the first two while wrongly keeping a both-sides-bounded band below the minimum, and comparing an upper bound's value without its operator satisfies the first four while wrongly dropping `<=480` under a 480 minimum. The drop condition is that the upper bound admits no width at or above the minimum — `u <= minimum` for `<u`, `u < minimum` for `<=u`, and a band with no upper bound is never dropped, which is what keeps `wide >=1024` and `>=1440` alive under every minimum.
- [ ] **AC-0003.** The clamp raises a band's lower bound to the declared minimum and never lowers one: a surviving band's lower bound is the greater of the minimum and its own. Construction test: `test_the_clamp_raises_a_lower_bound_and_never_lowers_one`; fixtures, each asserting the full band list and its capture widths: a 1280 minimum against the fallback bands, yielding `[(">=1280", "")]` captured at 1280; a 600 minimum against the fallback bands, yielding `[(">=1024", "")]` captured at 1024, because `wide` already starts above the minimum and the clamp leaves it untouched; and a 100 minimum against breakpoints `[400, 800]`, dropping no band and yielding `[(">=100", "<400"), (">=400", "<800"), (">=800", "")]` captured at 100, 400 and 800. A clamped band's name follows the same three templates the derivation already applies — `below-{b1}`, `{lower}-to-{upper}` and `from-{bn}` — so the 100 fixture asserts full `(name, lower, upper)` triples and the lowest band is `100-to-400`, not `below-400`: the walk names the band in its incomplete report, and a band starting at 100 reported as `below-400` would misdescribe what is missing. A clamped fallback band keeps the name its table row gives it. Those templates are module-owned, not table-stated — see *Always do* on why this one rule is not a shipped row. The 600 fixture is the one that bites: assigning the minimum rather than raising to it would demand a capture at 600, a width the reference states satisfies neither fallback channel by deliberate design.
- [ ] **AC-0004.** A declared breakpoint above the minimum still bounds its own band, so a minimum cannot reduce a surface to fewer channels than its breakpoints above the minimum require. Construction test: `test_a_breakpoint_above_the_minimum_keeps_its_band`; fixtures, each asserting the full band list: a 1280 minimum with breakpoints `[1536]` yielding `[(">=1280", "<1536"), (">=1536", "")]`, and with `[1440, 1920]` yielding `[(">=1280", "<1440"), (">=1440", "<1920"), (">=1920", "")]`.
- [ ] **AC-0005.** Both channel-minimum rule rows join the set the completeness walk proves present before it runs, so removing either makes the capture-set checks raise rather than skip. Discharged by the shipped `test_every_required_rule_row_raises_when_deleted`, parametrized over that set, together with the equality control that compares the set against the rule-row keys the shipped tables state; this criterion adds no test. It claims presence only — the presence loop reds on a deletion whether or not any code reads the row, so it cannot show the row governs anything. AC-0015 and AC-0016 carry that.
- [ ] **AC-0015.** The derivation refuses rather than deriving when `channel-minimum-derivation` states any value other than `drop-bands-below-clamp-lowest-survivor`, on the same footing as `channel-capture-width`. Construction test: `test_the_derivation_refuses_an_unknown_minimum_rule`; fixture: the reference with that row's **value cell** rewritten to another token, against which the derivation raises on all four calls crossing both axes — declared breakpoints or none, minimum or none. Crossing the basis axis is what makes this bite: the derivation returns the fallback bands before it validates `channel-derivation` or `channel-boundary-belongs-to`, so a check placed beside those siblings leaves the no-breakpoints path ungated — and that path is this delivery's motivating surface, an internal tool with a minimum and no declared breakpoints. `channel_capture_width` is the precedent: it validates its token on every call rather than only on the path that uses it. The row is present throughout, so a passing presence loop cannot account for either result.
- [ ] **AC-0017.** No two required channels admit a common width, under every minimum. Construction test: `test_no_two_required_channels_admit_a_common_width`, swept over the cross product of every minimum named anywhere in these criteria — absent, 100, 480, 600, 768, 1280 and 12800 — with every breakpoint list named in them: none, `[768]`, `[400, 800]`, `[768, 1024]`, `[1536]`, `[1440, 1920]`, `[768, 1536]` and `[768, 1024, 1440]`. The sweep is deliberately wider than the fixtures its siblings pin: on an input where AC-0002, AC-0003 or AC-0004 already asserts the full band list by exact equality, disjointness follows from that equality and this criterion adds nothing, so its whole value is the combinations no fixture enumerates. It is what a clamp that widens the upper bound away fails — dropping `<=480` while raising the lower bound to 480 yields `>=480` and `>=1024`, both of which admit 1024, so one capture would satisfy two required channels. The reference states the property for the no-minimum case: if one width could satisfy both, a single-channel set would read as covering two.

- [ ] **AC-0021.** No shipped **sentence** states a band enumeration or a per-route capture floor without naming the declared minimum. Construction test: `test_no_shipped_surface_states_a_superseded_capture_claim`, sweeping every `.md` and `.json` file under `packs/frontend-engineering/.apm/**` plus `guides/frontend-engineering/how-to/inspect-the-rendered-page.md`.

  Mechanization, in this order, because the order decides whether the check can fail. Split each file on blank lines into paragraph units — for JSON, each string value is one unit. Normalize runs of whitespace *within* a unit. Split the unit into sentences on `. `, `; `, `: ` and unit-final `.`, **not breaking on a period adjacent to another period**, because anchor 2 contains an ellipsis. Then require the *sentence* carrying an anchor to contain that anchor's **conditioning literal**, listed beside it below. Two weaker forms were rejected: normalizing before splitting erases every blank-line boundary and collapses the predicate to "this file mentions the minimum somewhere"; and a paragraph-scoped predicate is satisfied by appending one unrelated sentence, which is the cheapest possible discharge and leaves the claim itself false.

  The conditioning literals are a closed set of three, each reserving the phrase `declared minimum`, which occurs nowhere in the swept files today. A bare `minimum` would not do: `SKILL.md` alone carries nine case-insensitive occurrences of it in unrelated senses — a minimum viable property set, a critical-states minimum, the WCAG 2.1 minimum, a minimum contrast ratio — so a predicate keyed on it would grade a WCAG sentence near an anchor as conditioned. Naming the satisfier is also what stops the cheapest discharge surviving at sentence scope: `… needs four times n + 1, and a declared minimum is a separate matter` mentions the minimum in the anchor's own sentence while the claim before the comma stays false, and it does not contain `above the declared minimum`.

  The anchor set is the control's entire reach, and each anchor's carrier file set is part of the assertion. **Every anchor must match in exactly the files listed**, not merely somewhere in the sweep: anchors 3, 4 and 5 have several carriers each, so an existential check would let a rephrase in one carrier pass on the strength of the others while putting that carrier outside the control's reach. Removing a carrier deliberately is an amendment to this map, not a green run.
  1. `these two apply` — the reference. Conditioner: `no declared minimum`.
  2. ``For breakpoints `b1 < ... < bn`` — the reference. Conditioner: `before the declared minimum`, because this sentence describes the derivation's first pass, which the plan deliberately keeps separable, so it stays true once it says where it sits in the order. AC-0002's `[400, 800]` fixture contradicts it only as an unconditional statement of the result.
  3. `Declare none and two apply` — `SKILL.md` § 5a and the how-to. Conditioner: `no declared minimum`.
  4. `eight captures per route` — the reference, `SKILL.md` § 5a and the how-to, all three. Conditioner: `no declared minimum`. The existing "on the fallback bands" qualifier does not discharge it: that names the basis, which a minimum leaves unchanged.
  5. `four times *n + 1* where you declare *n* breakpoints` — `SKILL.md` § 5a and the how-to, both of which wrap it mid-phrase. Conditioner: `above the declared minimum`, since the floor counts only breakpoints the minimum did not discard. In both carriers this anchor and anchor 4 currently sit in **one** sentence, which under the stated splitter would have to carry both conditioners at once; the edit therefore splits that sentence in two, one clause per claim. That split is an obligation of the tasks editing those two files, not an implementation detail.
  6. `needs four times` — the reference. Its variant of the same floor in `## Required captures`, which anchor 5 does not match because it is backticked and omits "where you declare". Conditioner: `above the declared minimum`.
  7. `the narrow and wide fallback bands when none are declared` — `evals.json`. A judge grades against it. Conditioner: `no declared minimum`.
  8. `Two here because no breakpoints were declared` — `SKILL.md` § 5a's JS worked example, the block an agent performing the step copies. Conditioner: `no declared minimum`. It is its own paragraph unit, so conditioning the prose around it does not reach it. The array keeps both of its entries and stays a correct no-minimum example: the comment is what teaches the falsified inference, and the anchor must keep matching, so a one-entry array under a comment reading "Two here" is not an available edit.

  Fixture: the pre-change tree, where every anchor matches in exactly its listed files and no anchor's sentence contains its conditioning literal. One criterion rather than one clause per surface: eight carriers state some form of this claim, and five consecutive review rounds each found the next one after the last was closed per-surface. An anchor-and-carrier map is a thing a reviewer inspects; "did the author think of the eighth carrier" is not.

<!-- Recorded effects -->
- [ ] **AC-0006.** A run records the declared minimum in force, or that none was declared, in a field separate from the channel basis, and the basis value stays one of the two shipped tokens under every minimum including one in force. Construction test: `test_the_minimum_is_recorded_beside_the_basis`; fixtures, each naming both expected values: a 1280 minimum against the fallback bands, where the basis reader returns exactly `fallback` and the minimum reader returns `1280`; breakpoints with a 1280 minimum, where the basis reader returns exactly `declared-breakpoints`; and a run with no minimum, where the minimum reader returns exactly the non-empty token `none-declared`. The token is named rather than described so that "no minimum was declared" is a stated value a reader can assert on, distinct from a field nobody wrote. It is a run-level fact, so it lives in the § 5a manifest row AC-0018 pins and not in the `## Capture record` table, whose five fields describe one capture each and whose reader treats an empty value as an absent field. The basis assertion is an exact-equality check on the whole value, not a prefix or substring match, because a reader that returned `declared-breakpoints+1280` would satisfy a looser one — and that is the third-vocabulary-value shape *Ask first* gates, which the shipped `test_the_channel_basis_is_recorded_not_inferred` cannot see, since it never passes a minimum.
- [ ] **AC-0007.** A run records exactly those declared breakpoints the minimum discarded, and no breakpoint it kept. Construction test: `test_discarded_breakpoints_are_recorded`; fixtures: a 1280 minimum against breakpoints `[768, 1536]`, where the record is exactly `[768]` and excludes 1536; a 12800 minimum against `[768, 1024, 1440]`, where all three are discarded and the record names all three; and a 768 minimum against `[768, 1024]`, where the record is empty, because a breakpoint equal to the minimum still bounds a surviving channel. Two fixtures each close a cheaper predicate: under the all-discarded fixture alone, recording the input list verbatim is indistinguishable from recording the discarded set, and `b <= minimum` satisfies both non-equality fixtures while contradicting AC-0002's own `[768, 1024]` case, which requires 768 to bound a channel captured at 768. A breakpoint is discarded only when it is strictly below the minimum.
- [ ] **AC-0016.** Both recording readers refuse rather than returning silently when `channel-minimum-recorded` is switched off, on the same footing as `channel-basis-recorded`. Construction test: `test_the_recording_refuses_when_switched_off`; fixture: the reference with that row's **value cell** set to `not-required`, against which the minimum-in-force reader and the discarded-breakpoints reader each raise, asserted by its own call, with declared breakpoints and with none. Per reader rather than per row, because one reader raising satisfies a row-level claim while the other stays fail-open; and with both breakpoint states, because the discarded-breakpoints reader most naturally returns an empty list before consulting the switch when no breakpoints were declared. The row is present throughout, so the presence loop cannot account for either result.

<!-- Adopter surfaces -->
- [ ] **AC-0008.** `SKILL.md` § 5a states that a surface may declare a supported minimum width and that bands below it stop being required, so an agent performing the step knows the input exists. Construction test: `test_the_skill_states_the_minimum_input`; fixture: the shipped § 5a text, which names no minimum. This criterion is presence only — § 5a's superseded claims are anchors 3, 4, 5 and 8 of AC-0021's sweep, which is where their conditioning is asserted, because the same claims appear in the how-to and the reference, and a per-surface clause here would reach only one copy. The edit keeps the literal phrase `` `narrow` at ≤480 `` in that paragraph, because a shipped per-shape control anchors on that exact site.
- [ ] **AC-0018.** The `SKILL.md` § 5a evidence-manifest `viewports` row states the minimum in force and the declared breakpoints the minimum discarded, so the record an agent writes carries both. Construction test: `test_manifest_viewports_field_records_the_minimum`; fixture: the pre-change row, which records channels-as-predicates and the basis and names no minimum. The minimum and the discarded breakpoints are written as bare numbers, not as backticked comparisons, because the shipped `test_the_manifest_example_is_a_band_set_the_derivation_produces` harvests every backticked predicate in the row and compares the set to what the derivation yields — a backticked `>=1280` would be read as part of the worked example and red it. This is the adopter-facing surface that holds the record, and the shipped `test_manifest_viewports_field_records_channels` passes after this delivery without it — so AC-0006 and AC-0007, which assert what the readers return, cannot reach it.
- [ ] **AC-0009.** The journey's `youProvide` declaration names the supported minimum width among the inputs the adopter brings, in both committed copies. Construction test: `test_rendered_page_journey_promise.py::test_the_journey_declares_the_minimum_input`; fixtures: the pre-change declaration in `packs/frontend-engineering/JOURNEY.md`, which names routes, breakpoints and viewports and not a minimum; and the copy at `web/src/content/journeys/frontend-engineering.md`, which carries the same sentence one line lower because the sync injects a `generated: true` key above it, which the journey sync generates, is committed rather than ignored, and which no shipped lint compares against its source — so a stale web copy publishes an input list omitting the minimum while every gate stays green.
- [ ] **AC-0010.** The shipped how-to walks a surface that declares a minimum and states the required set that minimum produces. Construction test: `test_the_how_to_walks_a_single_channel_surface`, asserting the guide contains the minimum-width input token and a per-route floor of four captures for a single channel; fixture: the pre-change guide, which names no minimum. Presence only, for the same reason as AC-0008: the guide's superseded claims are anchors 3, 4 and 5 of AC-0021's sweep. The "on the fallback bands" qualifier does **not** condition the eight-capture figure and does not exempt it: the qualifier names the basis, which a minimum leaves unchanged — AC-0006 fixes the basis at exactly `fallback` for a 1280-minimum surface — while the required-set size is what the minimum changes. That surface is on the fallback bands and needs four captures per route, not eight.
- [ ] **AC-0011.** The `rendered-page-inspection` eval case names the declared minimum among the behaviours it expects of a completed inspection. Construction test: `test_the_harness_expects_the_minimum`; fixtures: the pre-change case's `assertions` entry and its `expected_output` prose, both named, because the shipped `HARNESS_SUPERSEDED_FLOOR` pins both and a test asserting on `assertions` alone would leave the judge's grading prose silent on the minimum while the graded rubric mentions it. Its superseded coverage expectation is anchor 7 of AC-0021's sweep — appending an expectation here would otherwise leave a judge grading a correct single-channel run as failing coverage.

<!-- Delivery -->
- [ ] **AC-0012.** Every committed surface that pins this pack's version carries the same value — `packs/frontend-engineering/pack.toml`, `packs/frontend-engineering/.claude-plugin/plugin.json`, and this pack's entry in the repository-root `.claude-plugin/marketplace.json`, which is regenerated from `plugin.json` and is committed, not generated at publish time — and that version is one patch above the pack's version on `origin/main` at seal time — `0.2.5` unless a peer bump moves origin first, which is why the value is stated as a rule and not only as a literal. Origin: `packs/AGENTS.md` § *Version bump rule* yields a patch bump from `0.2.4`, because this adds no adapter-projected primitive — `docs/CONVENTIONS.md` § *Version bump rule* names those as `skills/`, `agents/`, `hooks/`, `commands/` and `hook-wiring/`.
- [ ] **AC-0013.** `docs/product/changelog.md` carries an entry led by the `frontend-engineering` pack at the released version, that entry is the topmost release heading for this pack, the `core` heading remains directly beneath `[Unreleased]` — which is machine-enforced, not a style preference: `tests/roster/test_verification_ledger_contract.py::test_the_core_release_heading_sits_directly_beneath_unreleased` asserts the first versioned heading after `[Unreleased]` is `[core]` at `packs/core/pack.toml`'s version, so this pack's entry goes below the `core` block even though it carries a later date — and the entry's `Highlights` disposition is discharged one of the two ways the pack release pipeline admits: a `### Highlights` subsection of outcome-led bullets, or the none-verdict and its reason recorded in the pull request. This delivery changes what a consumer of the pack can do, so the expected disposition is the subsection; the criterion admits the recorded verdict so that the decision is visible either way. Nothing downstream makes this call — the `/now/` projection is a pure parser over the file's bytes and no model runs in the build, so an unwritten block is a release the public page never mentions.
- [ ] **AC-0014.** One end-to-end run of the step against a real single-channel surface with a minimum declared is recorded, with its observations, its result state, its verdict, the minimum in force, and any discarded breakpoint, in `docs/specs/channel-minimum-width/notes/verification-ledger.md` — the destination the Durable Outputs *Execution observation* row names.

<!-- Interface compatibility -->
- [ ] **AC-0022.** `docs/specs/rendered-page-channel-axis/spec.md` carries a `Status:` line pointer naming this spec's AC-0002 and AC-0003 as the successors to its AC-0001 and AC-0002, and both of those criteria are still present in its body verbatim and still ticked. Construction tests, matching the predecessor's three: `tests/roster/test_channel_minimum_width_supersession.py::test_the_status_line_points_at_the_successors`, `::test_the_superseded_criteria_are_still_present_verbatim`, and `::test_the_successors_state_the_criteria_that_supersede_them`, which asserts the pointer's targets exist and still hold the obligation. Fixture: the frozen file, pinning each superseded criterion's **entire `- [x]` line verbatim**, not a fragment of it — a pin on "exactly two" would survive almost any rewrite of that criterion, which is the opposite of what the pointer is for. The pointer is spec-to-spec rather than ADR-to-spec, deviating from `docs/CONVENTIONS.md` § *Superseding a frozen document* rule 2: no ADR governs this lineage — there is none for the rendered-page inspection at all — so there is nothing to point at, and the predecessor's own `Status:` line established the spec-to-spec form for this same contract one delivery earlier. That section is convention-enforced rather than machine-enforced, so the deviation is recorded here rather than left for a reviewer to infer. The predecessor is `Shipped` and states as met that declared breakpoints yield "exactly the bands those breakpoints bound" and that declaring none yields "exactly two" channels. This delivery falsifies both as unconditional rules — AC-0002's `[400, 800]` fixture drops two of three bands, and a 1280-minimum fallback surface has one channel, not two. Its *Ask first* binds this work through `Constrained by`: a superseded criterion takes a `Status:` line pointer and its body is not edited. The mechanism, the roster-test shape and the "still ticked verbatim" assertion are the predecessor's own precedent, which it built for the spec it superseded.

## Follow-ons

None identified at authoring time.

## Assumptions

- Technical: the derivation lives in `required_channels`
  (`required_channels` in
  `packs/frontend-engineering/tests/skills/frontend-engineering/frontend_engineering_rendered_page_rules.py`),
  and a clamped band needs no new predicate grammar — it is two existing
  one-operator cells — `>=1280` and `<1536`, and the inclusive-upper clamped band
  `>=480` with `<=480` that a minimum equal to a band's upper bound produces — all
  of which `satisfies()` already parses (read-only probe, 2026-09-14).
- Technical: the derivation is total over every case the contract can produce,
  and every derived width satisfies both of its own band's bounds — walked across
  ten cases: a minimum with no breakpoints, one below it, one equal to it, one
  above it, several above it, one inside the fallback gap, one equal to an
  inclusive upper bound, one above every breakpoint, and absent. The original
  probe measured the assignment clamp this spec no longer states; the walk that
  covers the raising clamp is the ten-case table in the plan's Design section
  (desk walk, 2026-09-14).
- Technical: adding a rule row trips the `REQUIRED_RULE_ROWS["Channels"]`
  equality control, so the constant moves with the row rather than being
  discovered mid-EXECUTE (anchor-test sweep, 2026-09-14). AC-0005 is the
  canonical statement of what that inherited coverage discharges; this entry
  records only when and how it was established.
- Technical: this pack's suite is reached by `Makefile` only and by no
  pull-request runner — `explore-grounding.py` reports
  `gates UNREACHED — no runner names this path` for the reference. The
  `test-corpus.yml` dispatch is therefore this delivery's evidence, as it was
  for the axis itself, and the gap is already registered in `workspace.toml`
  `[backlog].open` against `tools/repo/build_gate_chain.py`.
- Process: a *primitive* is an adapter-projected artifact — `skills/`, `agents/`,
  `hooks/`, `commands/`, `hook-wiring/` (`docs/CONVENTIONS.md` § *Version bump rule*). This
  delivery adds none, so the bump is a patch to `0.2.5`; the channel axis itself
  took a patch bump for a larger contract change (`82899ac36`, `0.2.3` →
  `0.2.4`).
- Process: shipped `.apm/` content may not cite this repository's identifiers,
  so the surfaces that motivated this change cannot be named inside the pack
  (`packs/AGENTS.md` § *Shipped pack content carries no internal-governance
  citations*).
- Product: the channel basis stays `declared-breakpoints` or `fallback`, and the
  minimum is recorded in a separate field, because a minimum composes with
  either basis and one field cannot carry both facts without inventing
  combinations (user confirmation 2026-09-14).
- Product: a minimum that discards every declared breakpoint is accepted, and
  the run records which breakpoints it discarded, so a mistyped minimum is
  distinguishable from a deliberate single-channel surface (user confirmation
  2026-09-14).
