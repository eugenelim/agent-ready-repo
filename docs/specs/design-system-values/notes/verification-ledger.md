# Verification ledger — design-system-values

Execution observations, in order. Each entry records what was run and what it
returned, not what it was expected to return.

## Baseline, before any edit — 2026-09-27

| Check | Result |
| --- | --- |
| `python3 tools/lint-experience-agnostic.py` | clean |
| `python3 -m pytest packs/experience-design/tests tests/roster/test_experience_design_write_declaration_and_containment.py tests/roster/test_design_handoff_contract_matches_corpus.py -q` | 24 passed, 0.47s |
| `python3 -m pytest packs/frontend-engineering/tests -q` | 421 passed, 1.65s |

Measured footprint of the always-loaded skill body before the change:
`packs/experience-design/.apm/skills/design-system/SKILL.md` — 7,799 bytes,
107 lines. Of that, the shared output-rendering block spans lines 15–32 and is
mandatory boilerplate present in every skill in the catalogue, so it is counted
separately when the change is compared. No repository mechanism enforces a
skill-body budget; this is a measurement, not a gate.

## T2 red run — 2026-09-27

`python3 -m pytest packs/experience-design/tests/skills/design-system/test_contract.py -q`

**First red, before the contract was revised:** 14 failed. Every failure named
a contract anchor absent from today's skill — the four routes, the two-clause
invariant, the ordered precedence, the non-rankable floor, the axis-to-domain
map, the `[platform-default]` rule, the visual-target reading rule, the
artifact's authority / rules / proving-set / unresolved sections, the
retained-extended-replaced record, the surviving obsolete wording, the
technology-agnostic binding shapes, the failure-mode inventory, the control-plane
structure, and the eval scenarios. The two reference files the suite reads do
not exist yet, which is why several assertions fail at the read rather than the
assertion.

**Second red, after the pre-EXECUTE review corrections:** 14 failed, 1 passed.
The added `test_the_eval_corpus_carries_no_value_shapes` passes against the
current eval files, which is the correct result — the guard exists to catch a
value introduced later through the one door the agnosticism lint does not
watch, and today's corpus carries none.

No failure was caused by a broken import, a missing fixture, or a path error.

## T3 — 2026-09-28

| Check | Result |
| --- | --- |
| `python3 -m pytest packs/experience-design/tests/skills/design-system/test_design_system_contract.py -q` | 15 passed, 0.32s |
| `python3 tools/lint-experience-agnostic.py` | clean |

Two failures on the way through were the suite's fault, not the skill's, and
both were fixed in the suite rather than worked around in the prose. A phrase
pin matched against raw bytes failed on a line wrap, so every phrase assertion
now runs against a whitespace-collapsed copy. A negative pin banning the string
`required binding` matched the sentence stating that prohibition — a check that
fires on its own rule — so it was replaced with named products only.

The test file was renamed from `test_contract.py` to
`test_design_system_contract.py`: pytest refused to collect two test modules
sharing a basename, which is the module-name collision `packs/AGENTS.md` warns
about.

Measured footprint, `git show HEAD:` against the working tree:

| | Before | After |
| --- | ---: | ---: |
| `SKILL.md` total | 7,777 bytes | 14,017 bytes |
| lines | 107 | 211 |
| shared output-rendering block | 2,552 bytes | 2,552 bytes |
| executable body | 5,225 bytes | 11,465 bytes |

The always-loaded body slightly more than doubled. Stating that plainly matters
more than framing it well: the entrypoint got bigger, not smaller. What it
bought is four routes with a selection rubric, a six-rung authority table, the
five-step test for when a value must be resolved, the downstream handoff
questions, and nine refused failure modes — each of which changes what a run
does, which is the only thing that earns space in a control plane.

What did not go in is the per-domain method: 16,983 bytes across
`value-derivation.md` and `incumbent-systems.md`, loaded only by the route that
needs them. `inherit` on a coherent system loads neither in full.

Had that material been inlined, the body would be near 28,000 bytes on every
invocation.

The baseline note earlier in this ledger recorded 7,799 bytes and a block
spanning lines 15–32; the measured figure is 7,777 with a 2,552-byte block. The
first pair were counted by hand and were wrong. An intermediate revision of
this entry also recorded 13,459/205 and 16,471, which the review-fix pass then
moved. The figures in the table above are the shipped ones. No repository
mechanism enforces a budget on this pack, so these are measurements, not a
gate.
(The `frontend-engineering` pack does enforce one, at 960 lines; that is how
the handover to its slice 2 came to carry the line-count constraint.)

## T6 — 2026-09-28

| Check | Result |
| --- | --- |
| `python3 tools/validate_guides.py` | OK — 0 errors, 0 warnings, 231 checked |
| `python3 tools/lint-guidebook-steps.py guides/experience-design` | OK — 1 guidebook directory |
| `python3 tools/lint-web-journey-parity.py` | all 19 journeys in parity |
| `python3 tools/lint-journey-contract.py` | all 19 journeys conform |
| `python3 tools/lint-pack-journeys.py` | all 14 JOURNEY.md files valid |
| `FORCE=1 make build-self` | ok; marketplace regenerated |
| `make lint-ruff lint-mypy` | All checks passed; no issues in 149 source files |
| `python3 -m pytest tests/roster -q` | 1 failed, 1851 passed, 6 skipped, 428.81s |
| `python3 -m pytest tests/roster/test_verification_ledger_contract.py -q` (after fix) | 13 passed, 0.62s |

The roster failure was real and mine:
`test_the_core_release_heading_sits_directly_beneath_unreleased` requires the
`[core]` heading to be the first versioned heading under `[Unreleased]`, and
the new release entry had been inserted above it. Moved below the core block.

`web/src/content/journeys/experience-design.md` carries `generated: true` but
no tool writes it — `make build-self` left it untouched and the three journey
lints only compare the `skills:` list, so a stale body would have passed every
check. It was synced by hand and is now byte-identical to the pack file apart
from that one frontmatter line.

## T5 — not in this slice

Both `frontend-engineering` edits were written, verified against that pack's
suite, and reverted. `packs/frontend-engineering/` is unmodified and its 421
tests pass. The pack's next version is reserved by
`docs/specs/frontend-visual-authority/` slice 2 and enforced by
`test_the_pack_pins_the_slice_one_version`. The owner chose to hand the edits
to that slice rather than contend for the version.

The receiving session replied that it has taken both edits as its AC-0028 and
AC-0028a and that it merges behind this work. **That is its claim, not
something this tree shows**: `docs/specs/frontend-visual-authority/spec.md` on
this branch carries no criterion above AC-0025a, so the receiving criteria are
not yet visible here. What this tree does show is the version reservation the
handover turned on — AC-0025a reserves `0.3.5` — and that
`packs/frontend-engineering/` is unmodified with its 421 tests passing.

While the edits were briefly in place they surfaced a second gate:
`test_the_entrypoint_body_stays_within_budget` holds that skill at exactly 960
of 960 lines, so the replacement had to be four lines for four. That constraint
went across with the handover.

## Review round 1 — 2026-09-28

Two reviewers ran against the staged change. Dispositions, and the two findings
that changed behaviour rather than prose:

- **Route selection had two contradictory orders of operations** in the same
  file — a route rule keyed on incumbent coherence, a rubric keyed on request
  wording, and a procedure that read authority after selecting. Repaired to one
  order: search first, ordered rubric on what the search found, request wording
  as tie-break only.
- **The structural-axis carve-out sat after the case that would already have
  resolved it.** Both statements matched the same input — a structural axis at
  `[platform-default]` on a direction naming a target surface — and prescribed
  opposite actions, with only prose ordering them, inside a list that says take
  the first answer that applies. AC-0007 requires the report-back behaviour, so
  the structural exclusion is now a condition of the platform-convention case
  in both `SKILL.md` and `value-derivation.md`.
- **The eval-JSON value guard was a hand-copied subset of the lint's rules.**
  It kept the digit-requiring hex lookahead but dropped the companion rule for
  `#fff`, and dropped `vmin`/`vmax` and the decimal-seconds rule, so `#ccc`,
  `0.3s` and `24vmin` passed the test while the lint would have caught each.
  The test now imports the lint's own rule list and asserts the four value
  labels are still present, so the two cannot drift again. Probed after the
  change: `#fff`, `#ccc`, `0.3s`, `0.3 s`, `24vmin`, `12 vmax`, `4.5:1` and
  `ease-in-out` all match. `#abcdef` matches neither, because the lint
  deliberately requires a digit in a hex literal so word-slugs like `#facade`
  do not false-positive — the test now has exactly the lint's coverage,
  including that limitation.

Also repaired: `extend` fired on partial coverage in
`references/incumbent-systems.md` while `SKILL.md` routed a gap inside an
existing system to `inherit`; the template permitted deleting the Accessibility,
Proving-set and Unresolved sections that AC-0005 and AC-0007 depend on; the
reference guide listed the authority sources in an order that was not the
precedence; the guide used "rung" without defining it; ADR-0128 D4 enumerated
one fewer authority than the rung table it governs; and two claims — one public
changelog Highlight and one line of `DESIGN.md` — asserted the lint covers
every file in the pack when it reads Markdown only.

Declined, with reasons: `design-principles/SKILL.md` still routes to
`design-system` "for token taxonomy", which is outside this slice's write
boundary and harmless while `type: token-taxonomy` remains the artifact
identity. The `establish-design-intent` guide marks `design-system` Optional
while its done-criterion assumes token roles exist — a pre-existing
inconsistency this change did not introduce. A finding that `Signature device`
is undefined jargon was refuted: it is a real `## Signature device` field in
the upstream direction template.

Two mechanical checks caught authoring errors before review did, which is the
better outcome: `lint-guidebook-steps.py` rejected a stale template excerpt in
the guide, and the rung-order assertion failed because a bare substring search
matched the filename `incumbent-systems.md` rather than the `incumbent-system`
rung. The test was wrong there, not the prose, and was tightened to match the
table cell.

## T7 — one real invocation, 2026-09-28

**Input:** a greenfield distinctive direction — *Tidewatch*, a tide and weather
instrument for commercial shellfish harvesters, `status: selected`, target
surface responsive-web. Fourteen of fifteen axes decided; Motion character left
at `[platform-default]`. No incumbent system. One stated constraint: legible in
direct daylight on a boat deck.

**Confinement outcome, exercised first and reported as it happened.** Neither
`./agentbundle-layout.toml` (absent) nor `~/.agentbundle/agentbundle-layout.toml`
(present, `[research]` only) carries a `[design]` section, so resolution
correctly reached two-branch elicitation and did not guess a path. That is the
control working. No write was made to the user's vault or to the repository.
To exercise the content contract the artifact was written to this session's
scratchpad at `tidewatch-tokens.md`. **The real write path was therefore not
exercised**, and this run establishes nothing about final-target confinement.

**Route:** `originate`, selected from a search that found no token source, no
theme module, no constants file and no component library.

**Authority record as written.** Seven of eight domains resolved; one recorded
unresolved.

| Domain | Rung that supplied it |
| --- | --- |
| Typography | `approved-direction` |
| Color | `approved-direction` + `stated-constraint` (daylight legibility) |
| Spacing and rhythm | `approved-direction` |
| Shape and containment | `approved-direction` |
| Depth | `approved-direction` |
| Motion | `unresolved` |
| Graphic language | `approved-direction` |
| Spatial structure | `approved-direction` |

No rung below `approved-direction` was reached, which is the expected shape for
`originate`: there was no incumbent system to hand anything down, and
responsive-web supplied no platform convention for the one axis the direction
left open.

**The unresolved domain, as recorded.** Motion. Missing authority: the
direction left Motion character at `[platform-default]`, and the named target
surface (responsive-web) owns no motion-character convention, so nothing
reaches the axis. Named resolver: `creative-direction refine`, which maps a
`delight` request onto that axis. Until then no duration, easing or transition
is resolved, and a build changes state without animation while honouring the
platform's reduced-motion signal.

**Proving set as written.** Six needs, chosen as the smallest set covering all
seven resolved domains.

| Product need | Domains exercised | Outcome |
| --- | --- | --- |
| Primary reading surface, six live readings | typography, color, spacing, spatial structure | held |
| Tide table, 24 timestamped rows | typography, shape and containment, spacing | **fault** — 24 rows did not fit one screen at the first resolved data size; the instrument stopped being glanceable |
| Threshold editor, the one form | shape and containment, color | **fault** — with no panels anywhere, the editable region had nothing marking it |
| Alert state | color, contrast budget | held |
| Narrow channel | spatial structure, spacing | **fault** — the left-weighted balance stacked forecast prose above the readings |
| Confirm dialog | depth | held |

Three observations worth keeping:

- The proving set earned its place: three of six needs exposed faults invisible
  from the token table, and two of those were relationship inversions rather
  than missing values.
- The direction's rejection of the category default survived into values. The
  threshold-editor fault is the interesting one — the system needed to mark an
  editable region and reached for a rule rather than admitting a panel, which
  is exactly the point at which a generic default would have re-entered.
- The accessibility floor bit and behaved as specified. The quietest label
  resolved below the floor at its size; the relationship was kept, the value
  darkened until it cleared, and the adaptation recorded rather than traded.

**Durability limit.** The written artifact lives in this session's scratchpad
and is not in the repository, so the tables above are the durable record of the
run rather than a pointer to one. They are transcribed from the artifact, not
summarised from memory.
