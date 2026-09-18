# Plan: architect-design scope-routed model-first templates

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0118 fixes the names; `packs/AGENTS.md` owns the
  version-bump and no-internal-citation rules and `packs/AGENTS.local.md` owns
  the release sequence. Analogous shipped asset-plus-rubric pairs:
  `architect-review`'s `assets/critique.md` with
  `references/rubric-design-doc.md`, and `architect-diagram`'s testdata-backed
  Mermaid assets. Their construction path is
  `packs/architect/tests/skills/architect-review/test_architect_review_yagni_contract.py`,
  which pins asset names from `SKILL.md` prose — the same pinning shape this
  plan's `test_document_model_contract.py` uses. Named uncertainty: the
  `architect-design` test directory is not on the pull-request path, so its
  suites are proven only by a dispatched `test-corpus` run.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

## Approach

The change is a content change to one skill plus its two downstream reviewers,
and it lands in two waves that each leave the pack coherent. Wave 1 builds the
authoring side — the three templates, the scope stage that routes to them, and
the three rubric surfaces re-mapped onto them — because routing to templates
that do not exist is the one ordering that breaks the pack mid-change. The
decomposition rubric lands in wave 1 too, ahead of the scope stage, because the
scope stage cites it and a live citation to an absent file is the same defect in
the other direction. Wave 2 adds the architecture-set index, the reviewer's
mirror of the criteria, and the release surface.

The riskiest part is not the templates. It is the rubric re-mapping: four checks
have no counterpart in the new spine and must be replaced by different checks
rather than carried across, and `architect-review` plus `design-reviewer` are
what would otherwise converge a good model-first document back toward prose.
Wave 1 therefore treats those three files as one unit of work.

## Constraints

- **ADR-0118** fixes the three asset filenames (`D1`), the retention of
  `design-doc.md` (`D2`), the eleven-section subsystem spine and its two shape
  rules (`D3`), the six decomposition criteria and three refusals (`D4`), and
  that scope is skill-level routing rather than an OKF concept (`D6`). Its
  `D5` reserves `DA1`-`DA10` for slice 2; this plan implements none of them.
- **`packs/AGENTS.md`** — the version-bump rule and the prohibition on citing
  internal records from shipped pack content.
- **`packs/AGENTS.local.md`** — the marketplace and release sequence, and the
  internal-citation grep to run before committing.
- ADR-0118's own `D1`-`D6` constraint addresses are distinct from the `D1`-`D6`
  decomposition criteria. Only the criteria ship; the addresses stay in the
  record.

## Construction tests

**Integration tests:** none beyond per-task tests. The three new suites read
shipped files; there is no runtime to integrate.

**Manual verification:** read `assets/subsystem-design.md` end to end against
the eleven-section spine and confirm each section's opening question is one a
designer can actually answer at that zoom — the text assertions prove a
question mark is present, not that the question is answerable. Record the read
in the verification ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — `SKILL.md` description | T6 | `test_yagni_contract.py` green | Description read for routing widening; no trigger added |
| Current product truth — five prose surfaces | T8 | `Google-style` grep returns no architect-owned hit | Each surface describes scope-routed authoring |
| Interface compatibility — `assets/design-doc.md` | T2 | `test_document_model_contract.py` pointer assertion | The path resolves and names the three routed templates |
| Decision rationale — ADR-0118 | none | No amendment required | Slice 1 uses the recorded names unchanged |
| Release history — changelog entry | T11 | Free-standing `## [architect][0.15.11]` with `### Highlights` | Entry not nested under `[Unreleased]` |
| Projection — web journey | T8 | `build-check` reports no staleness | Regenerated, not hand-edited |

## Design (LLD)

### Design decisions

- **Three files, not one conditional template.** A single template with
  conditional blocks makes every visible block look fillable, which is the
  accumulation failure being fixed. Rejected. Traces to: the four
  active-template inventory criteria.
- **The architecture-set index is a section of `decomposition-rubric.md`, not
  its own file.** Which children split out and what the parent keeps afterwards
  are two halves of one decision, and a reader holding one needs the other.
  Rejected alternative: a separate `architecture-set-index.md`, which adds a
  second adopter-visible surface for no routing benefit. Traces to: the two
  parent-retention criteria.
- **Section presence is asserted as an ordered list, not a set.** ADR-0118 fixes
  the spine *in order*, and a set comparison passes on a reordering. Traces to:
  the eleven-section criterion.
- **The opening question is read as a paragraph, and headings are compared with
  their numeric prefix stripped.** A throwaway parse over a two-section draft
  establishes why: a question wrapped across two source lines is correct yet
  fails a `first line ends with ?` check, and a heading authored as
  `## 1. Scope and Context` does not equal the bare recorded name. Joining to
  the next blank line and stripping a leading `<digits>. ` admits both and
  still fails a genuinely missing question. Traces to: the opening-question criterion and the eleven-section
  criterion.
- **The C4 refusal is scanned per asset, not pack-wide.** `architect-diagram`
  legitimately ships `C4Context` in
  `tests/skills/architect-diagram/testdata/c4-context.mmd`; a pack-wide scan
  would red on shipped, correct content. Traces to: the C4-directive criterion.
- **Four homeless rubric checks are replaced, not moved.** TL;DR
  sentence-count → structured header fields; implement-from-Proposal-alone →
  the complete model set plus Implementation Mapping is sufficient; prose
  references the diagram → every diagram states one named question and one zoom
  level; empty Open Questions is fine → omit the section when empty. Traces to:
  the five `design-doc-rubric.md` criteria.

### Component / module decomposition

New: three assets, one reference, three test modules. Reused: the existing
rubric files are re-mapped in place rather than replaced, so an adopter's
reference to either path keeps resolving. `assets/concept.md` is untouched —
Stage 0 is unchanged by this slice.

### Behavior & rules

The scope stage resolves two things and both precede template choice. Altitude
is one of three values. Document count routes through the decomposition rubric.
The ordering is what the test asserts, because a scope stage placed after
template selection would read as correct prose while routing nothing.

### Dependencies & integration

No new dependency. `pyyaml` is already used by `test_yagni_contract.py` in the
same directory; the new suites need only `pathlib` and `re`.

## Tasks

### T1: The three routed templates carry their spines, forms, and opening questions

**Depends on:** none

**Touches:** packs/architect/.apm/skills/architect-design/assets/subsystem-design.md, packs/architect/.apm/skills/architect-design/assets/application-system-design.md, packs/architect/.apm/skills/architect-design/assets/architecture-change-design.md

**Tests:**
- `packs/architect/tests/skills/architect-design/test_document_model_contract.py`
  asserts the ordered eleven `##` headings of `subsystem-design.md` equal the
  ADR-0118 spine, and the ordered eight of `architecture-change-design.md`
  equal the delta-shaped list.
- The same module asserts each `##` section's first non-blank body *paragraph*
  — lines joined to the next blank line, whitespace collapsed — ends with `?`
  in each routed template.
- The same module asserts the Contracts and Invariants table header carries all
  nine column names, and that Quality Scenarios names all six scenario parts
  plus business consequence, mechanism, and verification.
- The same module asserts `Appendix` is absent from every routed template, and
  that none contains `C4Context`, `C4Container`, or `architecture-beta`.
- The same module holds the model-bearing section names as a literal set per
  template, transcribed from the criterion rather than parsed from the asset.
  It asserts each named section exists, contains exactly one `<!-- model -->`
  and exactly one `<!-- rationale -->`, and that the model index is lower. The
  domain is in the test because any domain read from the asset lets the asset
  shrink its own coverage — deleting a token, or dropping a section from a
  declared list, would excuse the section instead of failing it.
- Two mutation cases, run against a copy in `tmp_path`: deleting one
  `<!-- model -->` token from a named section, and renaming a named section's
  heading. Both must red. The second is what proves the domain is independent
  of the asset.
- Stub (`stub: true`): the ordered-heading assertion for `subsystem-design.md`
  compiles against the eleven recorded names and reds on an absent file.

**Approach:**
- Author `subsystem-design.md` first; the other two are defined as deltas from
  it (zoom changes and omissions), so writing them first would invent a spine
  twice.

**Done when:** AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009,
AC-0010, AC-0011, AC-0012, AC-0041, AC-0042 and AC-0013 are green in
`test_document_model_contract.py`, and the module's C4 scan reds when a
directive is pasted into an asset.

### T2: `design-doc.md` is a self-describing unrouted pointer

**Depends on:** T1

**Touches:** packs/architect/.apm/skills/architect-design/assets/design-doc.md

**Tests:**
- `test_document_model_contract.py` asserts the assets directory's Markdown set
  equals exactly `concept.md`, `design-doc.md`, and the three routed names.
- The same module asserts `design-doc.md` names all three routed templates and
  states it is not routed.

**Done when:** AC-0001 and AC-0002 are green in
`test_document_model_contract.py`, and the inventory assertion reds on a fifth
asset.

### T3: Scope determination precedes Stage 0 and template choice

**Depends on:** T1, T9

**Touches:** packs/architect/.apm/skills/architect-design/SKILL.md

**Tests:**
- `packs/architect/tests/skills/architect-design/test_design_scope_routing.py`
  asserts the scope stage's text index is lower than the Stage 0 heading's and
  lower than the template-selection step's.
- The same module asserts the scope stage names all three altitudes and cites
  `references/decomposition-rubric.md`.
- Stub (`stub: true`): the index-comparison assertion, which reds while no
  scope stage exists.

**Approach:**
- Renumber the procedure rather than inserting an unnumbered stage, and re-run
  `test_architect_design_skill_engineering_reference_boundary.py` immediately —
  the provider block is located by marker, but its opening scope restriction is
  asserted outright and a renumbering pass is where it gets clipped.

**Done when:** AC-0021, AC-0022, AC-0023 and AC-0024 are green in
`test_design_scope_routing.py`, and the boundary suite is green.

### T4: The authoring rubric checks the model-first spine

**Depends on:** T1

**Touches:** packs/architect/.apm/skills/architect-design/references/design-doc-rubric.md

**Tests:**
- `test_design_scope_routing.py` runs the same derived-union subset check over
  `design-doc-rubric.md`, which is what makes `TL;DR` fail rather than a
  hand-listed forbidden-string sweep that a fifth retired section would escape.
- The same module asserts the three sentences `test_yagni_contract.py:78-80`
  pins are still present.

**Approach:**
- Re-map in place. A rewrite from scratch is how the three pinned sentences get
  dropped and `test_yagni_contract.py` reds for an unrelated reason.

**Done when:** AC-0025, AC-0026, AC-0027, AC-0028 and AC-0029 are green in
`test_design_scope_routing.py`, and `test_yagni_contract.py` is green with its
three pinned rubric sentences intact.

### T5: The reviewing rubric and the cold reviewer recognise three scopes

**Depends on:** T4

**Touches:** packs/architect/.apm/skills/architect-review/references/rubric-design-doc.md, packs/architect/.apm/agents/design-reviewer.md, packs/architect/.apm/skills/architect-review/SKILL.md

**Tests:**
- `test_design_scope_routing.py` derives the union of the three routed
  templates' `##` headings by parse, subtracts the three declared cross-cutting
  headings, and asserts the review rubric's remaining `##` set is a subset. A
  rubric heading naming a retired section fails.
- The same module asserts `design-reviewer.md` and `architect-review/SKILL.md`
  each match all three scope names and neither matches `Google-style`. The
  artifact-type list in `architect-review/SKILL.md` is the second router and is
  asserted alongside the agent, because either one left on the old genre routes
  a model-first document to the retired rubric.
- `packs/architect/tests/pack/test_design_reviewer_rubric_parity.py` stays green
  unmodified — it pins verdict, severity, and mechanical-judgment tokens, none
  of which this task moves.

**Done when:** AC-0031 and AC-0033 are green, and the parity suite is
unmodified in the diff.

### T6: The description promises scope-routed model-first output

**Depends on:** T1, T3

**Touches:** packs/architect/.apm/skills/architect-design/SKILL.md

**Tests:**
- `test_yagni_contract.py` stays green unmodified — the rewrite lands between
  `routing_head` and `routing_tail`.

**Approach:**
- Rewrite only the span between `NFR trade-offs. ` and ` Do NOT use`. No test
  reaches a routing widening inside that span, so the check is a read, not a
  run: confirm the middle adds no trigger phrase, no new applicable situation,
  and no authority beyond naming what the skill produces.

**Done when:** AC-0034 holds — `test_yagni_contract.py` is green with its
assertion file unmodified — and the read above is recorded in the verification
ledger.

### T7: The evals require model-first scope-routed output

**Depends on:** T1, T6

**Touches:** packs/architect/.apm/skills/architect-design/evals/evals.json

**Tests:**
- `tests/roster/test_architecture_decision_surface_portability.py` stays green —
  it keys by `item["id"]`, so ids 3-7 must keep their current meaning.
- Eval 1 is rewritten and three new evals are added, one per routed template,
  each asserting the model precedes its rationale. No eval text retains an
  old-shape expectation: the eight-section list and the `Google-style` string
  are both absent from the file.

**Approach:**
- Take new ids above the existing numeric maximum rather than renumbering;
  renumbering is what would move ids 3-7 under the roster test.

**Done when:** AC-0035 and AC-0036 hold, and the roster suite is green.

### T8: No architect-owned surface promises a Google-style doc

**Depends on:** T1, T5, T6, T7

**Touches:** packs/architect/README.md, packs/architect/DESIGN.md, packs/architect/JOURNEY.md, packs/architect/docs/index.md, guides/architect/how-to/shape-an-architecture-concept.md, web/src/content/journeys/architect.md

**Tests:**
- `grep -rn "Google-style" packs/architect/ guides/architect/` returns nothing.
  The grep is pack-wide, so it also covers the two routers T5 changes and the
  eval text T7 rewrites; those tasks are dependencies for that reason.
- `build-check` reports the web journey is not stale.

**Approach:**
- Edit `packs/architect/JOURNEY.md`, then regenerate with
  `python3 tools/build-site.py --journeys-only`. Editing the web copy directly
  is the projection drift `build-check` catches.

**Done when:** AC-0037 and AC-0038 hold — the grep is empty and the journey
projection reports fresh.

### T9: The decomposition rubric states its criteria, refusals, and the size rule

**Depends on:** none

**Touches:** packs/architect/.apm/skills/architect-design/references/decomposition-rubric.md

**Tests:**
- `packs/architect/tests/skills/architect-design/test_decomposition_rubric_criteria.py`
  holds a literal ID-to-criterion map transcribed from the governing record and
  asserts each ID's row carries its own distinguishing phrase — boundary for
  `D2`, release-or-failure unit for `D3`, system shape or workload class for
  `D4`, owners or reviewers for `D5`, quality scenarios for `D6`. Two swapped
  definitions fail, which an ID-presence check passes.
- The same module asserts the `D1`-plus-one-other rule and `D1`'s stopping-rule
  role.
- The same module maps each refusal to a distinct sentinel phrase and asserts
  all three map to a match, so one refusal silently dropped fails alone rather
  than being masked by its siblings.
- **Negative case:** the same module asserts the rubric states size alone never
  justifies a split, and that no size threshold, page count, line count, or
  byte figure appears anywhere in the file. This is the assertion that reds if a
  later slice wires a number in here rather than into its own gate.
- Stub (`stub: true`): the negative case, which reds while no rubric file
  exists.

**Done when:** AC-0014, AC-0015, AC-0016, AC-0017 and AC-0018 are green in
`test_decomposition_rubric_criteria.py`, and its negative case reds when a
threshold is added to the rubric.

### T10: The rubric states what a parent keeps and the reviewer can raise the finding

**Depends on:** T9, T5

**Touches:** packs/architect/.apm/skills/architect-design/references/decomposition-rubric.md, packs/architect/.apm/skills/architect-review/references/rubric-design-doc.md

**Tests:**
- `test_decomposition_rubric_criteria.py` asserts the five parent-retained items
  and the no-restatement rule.
- The same module asserts the review rubric matches all six criterion IDs as
  whole words, so `D1` inside `DA10` cannot satisfy the check.

**Done when:** AC-0019, AC-0020 and AC-0032 are green.

### T11: The release surface is complete

**Depends on:** T1-T10

**Touches:** packs/architect/pack.toml, packs/architect/.claude-plugin/plugin.json, docs/product/changelog.md, .claude-plugin/marketplace.json

**Tests:**
- Both version files read `0.15.11`.
- `docs/product/changelog.md` carries a free-standing `## [architect][0.15.11]`
  with a `### Highlights` subsection.
- `FORCE=1 make build-self` regenerates `marketplace.json` and leaves no other
  diff.
- The `packs/AGENTS.local.md` internal-citation grep returns no hit in the new
  pack content.

**Approach:**
- Highlights is YES for this release: the consumer authors at three scopes and
  decides document count from a stated rubric. Draft outcome-led bullets rather
  than a file inventory.

**Done when:** AC-0039 and AC-0040 hold, `make build-self && FORCE=1 make
build-self` is clean, and the changelog entry is at top level.

## Rollout

No deployment. The change ships with the pack release; adopters pick it up on
their next install or upgrade. Reversal is a revert of the content commit —
`design-doc.md` is retained throughout, so an adopter reference never breaks in
either direction.

## Risks

- **The rubric re-mapping converges good documents back toward prose.** If
  `architect-review` or `design-reviewer` is missed, step 6's convergence loop
  actively rewrites model-first output into the old shape. Mitigated by making
  T5 depend on T4 and asserting both files in one module.
- **The new suites do not run on a pull request.** Recorded as the spec's one
  assumption; mitigated by dispatching `test-corpus` before merge, which is
  partial evidence rather than a gate.
- **A routing widening hides in the description's free middle.** No test
  reaches it. Mitigated by T6's recorded read, which is the only available
  instrument and is stated as such rather than implied covered.

## Changelog

<!-- Approvals only. -->

- 2026-09-18 — spec approved by eugenelim at SPEC-HUMAN-GATE. Scope accepted
  as drafted, including the DA7/DA8 boundary note and the not-run-on-PR
  residue; the residue is answered by a dispatched `test-corpus` run rather
  than a gate-chain edit.
- 2026-09-18 — plan approved by eugenelim at PLAN-HUMAN-GATE. Eleven tasks in
  the reviewed dependency order, with T9 ahead of T3 and both review routers in
  T5.
