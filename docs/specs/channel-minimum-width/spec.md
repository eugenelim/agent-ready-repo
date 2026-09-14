# Spec: Channel minimum width

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
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
claimed. A breakpoint above the minimum still carries its own band, so declaring a
high minimum cannot collapse a genuinely responsive surface to one channel.

Success for the adopter is that the step asks for the widths their surface has
and no others, and that the run records the minimum it used and any declared
breakpoint the minimum discarded.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth — rule layer | Applicable — the reference is the executable contract the step and its checks both read | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/rendered-page-inspection.md` § Channels | pack maintainer | Two new rule rows present and read by the module; deleting either reds the capture-set checks | The reference and the checks that read it agree |
| Current product truth — adopter-facing skill | Applicable — `SKILL.md` § 5a restates the capture contract for the agent that performs it | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` § 5a and its evidence-manifest table | pack maintainer | § 5a states the minimum input and its effect; the manifest records the minimum and any discarded breakpoint | Both copies state one contract |
| Current product truth — journey input | Applicable — `JOURNEY.md:12` declares what the adopter brings, and this adds an input | `packs/frontend-engineering/JOURNEY.md` | pack maintainer | `youProvide` names the supported minimum width | The journey names every input the step takes |
| Adopter guidance | Applicable — the shipped how-to teaches the capture set by example | `guides/frontend-engineering/how-to/inspect-the-rendered-page.md` | pack maintainer | The guide walks a single-channel surface and says what the minimum does to the required set | An adopter with a desktop-only surface can produce a complete set from the guide alone |
| Decision rationale | Applicable — "drop then clamp" and the two-field record were chosen over three alternatives each, and neither is recoverable from the result | this spec's Objective, Acceptance Criteria, and Assumptions | spec owner | The criteria state the derivation and the recording; the Assumptions record what was settled and when | A future reader can see why the basis stayed two values and gained a sibling field |
| Reusable learning — eval harness | Applicable — `packs/AGENTS.md` § *Security and authoring rules* obliges a non-cosmetic pack update to update that pack's eval harness | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json` | pack maintainer | The `rendered-page-inspection` case names the minimum among the behaviours it expects | The harness exercises the shipped input |
| Execution observation | Applicable — a completeness test cannot show that one channel was enough to judge a page; only a performed run can | `docs/specs/channel-minimum-width/notes/verification-ledger.md` | spec owner | The run's observations, result state, verdict, minimum in force, and any discarded breakpoint | The ledger carries all five values for one real single-channel surface |
| Release history | Applicable — pack content changes | `packs/frontend-engineering/pack.toml`, `packs/frontend-engineering/.claude-plugin/plugin.json`, `docs/product/changelog.md` | release workflow | Matching version bump in both manifests; a changelog entry led by the pack and that version | Versions and changelog agree with shipped content |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Let the shipped tables state every rule, and let the rule-reading module read
  them. A check that supplies its own quantifier asserts behaviour the pack
  never promised an adopter.
- Prove every rule row the completeness walk depends on is present before the
  walk runs, so deleting any of them raises rather than skipping the rule it
  governs.
- Record what the minimum did, not only what it was: the value in force and any
  declared breakpoint it discarded.
- Keep the minimum optional. A surface that declares none behaves exactly as it
  does today.
- Restore a mutated file by editing it back, never by `git checkout`, `git reset`
  or `git stash` — a failed restore leaves a dirty tree that reads as a defect.

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
- Name a device in shipped pack content as the definition of a channel or a
  minimum.
- Cite this repository, its paths or its records inside
  `packs/frontend-engineering/.apm/**`.

## Testing Strategy

- **The admissible value (AC-0001):** TDD in `packs/frontend-engineering/tests/skills/frontend-engineering/test_rendered_page_capture_contract.py`. Its fixtures are refusal cases, not derivation cases: a fractional value, zero, a negative value, and a boolean. The probe recorded no refusal, so none of these come from it.
- **The derivation (AC-0002, AC-0003, AC-0004):** TDD in the same module. Each is a compressible invariant over data — a minimum and a breakpoint list either yield the stated bands or they do not — and every expectation is read from the shipped tables. The fixtures extend the five cases the probe recorded (a minimum with no breakpoints, with a breakpoint below it, with one above it, with several above it, and absent) with the two cases the probe did not reach: a band bounded on both sides lying wholly below the minimum, and a minimum equal to an inclusive upper bound, and a minimum equal to an exclusive one.
- **The rows in force (AC-0005, AC-0015, AC-0016):** TDD in the same module. AC-0005 is presence inheritance and needs no new test — the shipped parametrized control plus the equality control already carry it once the rows land in `REQUIRED_RULE_ROWS`. AC-0015 and AC-0016 are what make the rows load-bearing, and their mutation **edits the value cell** rather than deleting the row: the presence loop reds on a deletion whether or not any code reads the row, so deletion cannot demonstrate that it is read.
- **The recorded effects (AC-0006, AC-0007):** TDD in the same module, which already reads § 5a and its manifest table. Two criteria rather than one, because the value in force and the breakpoints it discarded are separate facts with separate failure modes.
- **Adopter surfaces (AC-0008, AC-0009, AC-0010):** goal-based checks. A search over `SKILL.md` § 5a, the journey's `youProvide`, and the how-to for the minimum and its effect on the required set. Each names the string it searches for, so its reach is the artifact a reviewer inspects.
- **Eval harness (AC-0011):** TDD in `test_rendered_page_reviewer_sight.py` — a parse of `evals/evals.json` asserting the `rendered-page-inspection` case names the minimum.
- **Pack delivery (AC-0012, AC-0013):** goal-based checks compare the two manifests' version fields, confirm the changelog entry is this pack's topmost release heading and sits below the `core` heading, and run `agentbundle catalogue lint --deep` and `catalogue verify`.
- **The step performed (AC-0014):** visual / manual QA. Run the capture against a real single-channel surface with a minimum declared and record the observations, the result state, the verdict, the minimum in force, and any discarded breakpoint. A passing completeness test is not evidence that one channel was enough.

## Acceptance Criteria

<!-- Derivation -->
- [ ] **AC-0001.** A declared minimum width is a positive whole number of CSS pixels, and a run refuses any other value while admitting absence, on the same footing as a declared breakpoint. Construction test: `test_a_declared_minimum_must_be_a_positive_whole_number`; fixtures: a fractional value, zero, a negative value, and a boolean, which `isinstance(True, int)` admits unless excluded, each refused; and `None`, which is admitted, because *Always do* keeps the minimum optional and a refusal contract stated only on one side would read as refusing absence too.
- [ ] **AC-0002.** A band whose entire width range lies below the declared minimum is not a required channel, whether that band is bounded below or not. Construction test: `test_a_band_wholly_below_the_minimum_is_dropped`; fixtures: the two fallback bands under a 1280 minimum, where `narrow` is dropped; a declared breakpoint of 768 under the same minimum, where its lower band is dropped; breakpoints `[400, 800]` under a 1280 minimum, where two bands are dropped and one of them — `>=400 <800` — is bounded on both sides, yielding one channel captured at 1280; a minimum of 768 against breakpoints `[768, 1024]`, where `<768` admits no width at or above the minimum and is dropped, yielding two channels at 768 and 1024; and a minimum of 480 against the fallback bands, where `narrow`'s `<=480` admits exactly 480 and therefore survives, yielding two channels captured at 480 and 1024. Three of these exist to close a cheaper filter: keying on an absent lower bound satisfies the first two while wrongly keeping a both-sides-bounded band below the minimum, and comparing an upper bound's value without its operator satisfies the first four while wrongly dropping `<=480` under a 480 minimum. The drop condition is that the upper bound admits no width at or above the minimum — `u <= minimum` for `<u`, and `u < minimum` for `<=u`.
- [ ] **AC-0003.** The clamp raises a band's lower bound to the declared minimum and never lowers one: a surviving band's lower bound is the greater of the minimum and its own. Construction test: `test_the_clamp_raises_a_lower_bound_and_never_lowers_one`; fixtures: a 1280 minimum against the fallback bands, yielding one channel captured at 1280; a 600 minimum against the fallback bands, yielding one channel captured at 1024, because `wide` already starts above the minimum; and a 100 minimum against breakpoints `[400, 800]`, dropping no band and yielding three channels captured at 100, 400 and 800. The 600 fixture is the one that bites: assigning the minimum rather than raising to it would demand a capture at 600, a width the reference states satisfies neither fallback channel by deliberate design.
- [ ] **AC-0004.** A declared breakpoint above the minimum still bounds its own band, so a minimum cannot reduce a surface to fewer channels than its breakpoints above the minimum require. Construction test: `test_a_breakpoint_above_the_minimum_keeps_its_band`; fixtures: a 1280 minimum with breakpoints `[1536]` yielding two channels at 1280 and 1536, and with `[1440, 1920]` yielding three at 1280, 1440 and 1920.
- [ ] **AC-0005.** Both channel-minimum rule rows join the set the completeness walk proves present before it runs, so removing either makes the capture-set checks raise rather than skip. Discharged by the shipped `test_every_required_rule_row_raises_when_deleted`, parametrized over that set, together with the equality control that compares the set against the rule-row keys the shipped tables state; this criterion adds no test. It claims presence only — the presence loop reds on a deletion whether or not any code reads the row, so it cannot show the row governs anything. AC-0015 and AC-0016 carry that.
- [ ] **AC-0015.** The derivation refuses rather than deriving when `channel-minimum-derivation` states any value other than `drop-bands-below-clamp-lowest-survivor`, on the same footing as `channel-capture-width`. Construction test: `test_the_derivation_refuses_an_unknown_minimum_rule`; fixture: the reference with that row's **value cell** rewritten to another token, against which the derivation raises both when a minimum is supplied and when none is — matching `channel_capture_width`, which validates its token on every call rather than only on the path that uses it. The row is present throughout, so a passing presence loop cannot account for either result.

<!-- Recorded effects -->
- [ ] **AC-0006.** A run records the declared minimum in force, or that none was declared, in a field separate from the channel basis, and the basis value stays one of the two shipped tokens under every minimum including one in force. Construction test: `test_the_minimum_is_recorded_beside_the_basis`; fixtures, each naming both expected values: a 1280 minimum against the fallback bands, where the basis reader returns exactly `fallback` and the minimum reader returns `1280`; breakpoints with a 1280 minimum, where the basis reader returns exactly `declared-breakpoints`; and a run with no minimum, where the minimum reader returns the recorded none-token. The basis assertion is an exact-equality check on the whole value, not a prefix or substring match, because a reader that returned `declared-breakpoints+1280` would satisfy a looser one — and that is the third-vocabulary-value shape *Ask first* gates, which the shipped `test_the_channel_basis_is_recorded_not_inferred` cannot see, since it never passes a minimum.
- [ ] **AC-0007.** A run records exactly those declared breakpoints the minimum discarded, and no breakpoint it kept. Construction test: `test_discarded_breakpoints_are_recorded`; fixtures: a 1280 minimum against breakpoints `[768, 1536]`, where the record is exactly `[768]` and excludes 1536; a 12800 minimum against `[768, 1024, 1440]`, where all three are discarded and the record names all three; and a 768 minimum against `[768, 1024]`, where the record is empty, because a breakpoint equal to the minimum still bounds a surviving channel. Two fixtures each close a cheaper predicate: under the all-discarded fixture alone, recording the input list verbatim is indistinguishable from recording the discarded set, and `b <= minimum` satisfies both non-equality fixtures while contradicting AC-0002's own `[768, 1024]` case, which requires 768 to bound a channel captured at 768. A breakpoint is discarded only when it is strictly below the minimum.
- [ ] **AC-0016.** Both recording readers refuse rather than returning silently when `channel-minimum-recorded` is switched off, on the same footing as `channel-basis-recorded`. Construction test: `test_the_recording_refuses_when_switched_off`; fixture: the reference with that row's **value cell** set to `not-required`, against which the minimum-in-force reader and the discarded-breakpoints reader each raise, asserted by its own call. Per reader rather than per row, because one reader raising satisfies a row-level claim while the other stays fail-open. The row is present throughout, so the presence loop cannot account for either result.

<!-- Adopter surfaces -->
- [ ] **AC-0008.** `SKILL.md` § 5a states that a surface may declare a supported minimum width and that bands below it stop being required. Construction test: `test_the_skill_states_the_minimum_input`; fixture: the shipped § 5a text.
- [ ] **AC-0009.** The journey's `youProvide` declaration names the supported minimum width among the inputs the adopter brings. Construction test: `test_rendered_page_journey_promise.py::test_the_journey_declares_the_minimum_input`; fixture: the pre-change declaration, which names routes, breakpoints and viewports and not a minimum.
- [ ] **AC-0010.** The shipped how-to walks a surface that declares a minimum and states the required set that minimum produces. Construction test: `test_the_how_to_walks_a_single_channel_surface`, asserting the guide contains both the minimum-width input token and a per-route floor of four captures for a single channel; fixture: the pre-change guide, which states eight as the floor unconditionally and names no minimum.
- [ ] **AC-0011.** The `rendered-page-inspection` eval case names the declared minimum among the behaviours it expects of a completed inspection. Construction test: `test_the_harness_expects_the_minimum`; fixture: the pre-change case.

<!-- Delivery -->
- [ ] **AC-0012.** `packs/frontend-engineering/pack.toml` and `packs/frontend-engineering/.claude-plugin/plugin.json` carry the same version, and that version is one patch above the pack's version on `origin/main` at seal time — `0.2.5` unless a peer bump moves origin first, which is why the value is stated as a rule and not only as a literal. Origin: `packs/AGENTS.md` § *Version bump rule* yields a patch bump from `0.2.4`, because this adds no adapter-projected primitive — `docs/CONVENTIONS.md` § *Version bump rule* names those as `skills/`, `agents/`, `hooks/`, `commands/` and `hook-wiring/`.
- [ ] **AC-0013.** `docs/product/changelog.md` carries an entry led by the `frontend-engineering` pack at `0.2.5`, that entry is the topmost release heading for this pack, and the `core` heading remains directly beneath `[Unreleased]`.
- [ ] **AC-0014.** One end-to-end run of the step against a real single-channel surface with a minimum declared is recorded, with its observations, its result state, its verdict, the minimum in force, and any discarded breakpoint, in `docs/specs/channel-minimum-width/notes/verification-ledger.md` — the destination the Durable Outputs *Execution observation* row names.

## Follow-ons

None identified at authoring time.

## Assumptions

- Technical: the derivation lives in `required_channels`
  (`required_channels` in
  `packs/frontend-engineering/tests/skills/frontend-engineering/frontend_engineering_rendered_page_rules.py`),
  and a clamped band needs no new predicate grammar — it is two existing
  one-operator cells, `>=1280` and `<1536`, both of which `satisfies()` already
  parses (read-only probe, 2026-09-14).
- Technical: the derivation is total over every case the contract can produce,
  and every derived width satisfies both of its own band's bounds — verified
  across a minimum with no breakpoints, one below it, one above it, several
  above it, and absent (read-only probe, 2026-09-14).
- Technical: adding a rule row trips the `REQUIRED_RULE_ROWS["Channels"]`
  equality control at `test_the_required_rule_rows_match_what_the_tables_state`, so the
  constant moves with the row rather than being discovered mid-EXECUTE
  (anchor-test sweep, 2026-09-14).
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
