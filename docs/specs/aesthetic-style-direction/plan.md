# Plan: Aesthetic style — parameterised direction, counterfactual gate, and divergence audit

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` § Version bump rule, § Security and
  authoring rules, § Self-hosting projection, and its Essential-commands block;
  `guides/AGENTS.md` § Essential commands; `docs/product/changelog.md`'s own
  header rules; `tools/lint-experience-agnostic.py:1-40,160-164` (RFC-0033
  value-literal ban, and that it takes no file argument); analogous multi-file
  reference set `packs/core/.apm/skills/security-checklists/references/` with
  its SKILL.md index table at `security-checklists/SKILL.md:109-123`;
  corresponding tests `tests/roster/test_experience_design_*.py`. Named
  uncertainty: the six-of-fifteen distinctness threshold is a reasoned default,
  recorded as a Follow-on. Named conflict: `packs/AGENTS.local.md:29` versus
  root `AGENTS.local.md:60` on `FORCE=1`, recorded as an `Ask first` boundary.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records
> its baseline.

**Criterion references are by section and quoted opening, never by number.**
Four review rounds broke numbered cross-references every time the criteria
moved; positional references are the defect, so this plan does not use them.

## Approach

Five content additions across two skills in one pack, plus the release and
registration bookkeeping the pack's scoped rules owe. The shape is wide and
shallow: no Python changes, no new module boundary, no behaviour a test can
drive. The risk is **silent inconsistency** between files that must agree on
one set of fifteen axis names and one token vocabulary per axis.

The approach removes that risk two ways. The axis block is pinned verbatim in
`Design (LLD)` so every task copies one shape rather than inventing its own,
and a token-set comparison in T9 mechanically catches drift if a task deviates
anyway. That turns what would be a serial chain into one parallel wave of six
disjoint-file tasks.

The riskiest part is `tools/lint-experience-agnostic.py`. It fails on colour
literals, dimension and duration literals, contrast and scale ratios, named
easing curves, ARIA roles, CSS syntax, UI-framework names, and it scans the
whole pack. **It takes no file argument** (`:160-164`, "this lint takes no
arguments"), so a worker running it mid-wave reads other workers' in-flight
edits and cannot attribute a failure to its own task. It is a single
post-wave controller check in T9 and appears in no task's evidence. Each task
instead self-checks inline against the rule list.

## Constraints

- RFC-0033: the pack ships portable method, never a stack or a values
  cheat-sheet. Roles, classifications, and relationships only.
- `creative-direction/SKILL.md:83` already refuses "palette, font name, or
  spacing/timing value". Preset content must satisfy the skill's own
  anti-pattern, not merely the lint.
- The exact strings `**Writes:** <output_dir>/direction/<slug>.md` and
  `**Confinement:** references/containment.md` are asserted by the roster suite.
- `containment.md` copies are compared byte-for-byte across skills, and module
  citations must agree bidirectionally with shipped copies. Touch none of them.
- The managed `agentbundle:output-rendering` block in each `SKILL.md` is
  synchronised by `tools/add-rendering-directives.py`; edit outside it only.
- No new `<output_dir>/<folder>/` declaration.
- `make build-self` is run **unforced**. If it refuses, surface; do not add
  `FORCE=1` (see the spec's `Ask first`).

## Construction tests

Every criterion is goal-based or manual QA; there is no compressible invariant
and no Python surface, so no task carries a compilable red stub. Each task
records `no stub (goal-based)`.

Each task states its own commands with a literal path and an expected result.
A `grep -c` prints a count and exits 0 when the count is non-zero, so every
expected **count** is stated, not merely an exit status.

The controller-run checks, after the parallel wave, in T9's order:

```
python3 tools/lint-experience-agnostic.py                        # exit 0
python3 -m pytest tests/roster/test_experience_design_write_declaration_and_containment.py \
    tests/roster/test_experience_design_artifact_folder_registry.py \
    tests/roster/test_experience_design_guide_agreement.py -q    # exit 0
python3 tools/validate_guides.py                                 # exit 0
python3 tools/check-guide-index.py                               # exit 0
python3 tools/lint-guide-titles.py                               # exit 0
python3 tools/lint-guidebook-steps.py guides/experience-design   # exit 0
python3 tools/build-site.py                                      # exit 0
```

The **token-agreement check**, which is the only thing that catches cross-file
axis drift. For each of the fifteen axis rows, the set of bracketed tokens used
in each preset must be a subset of that row's vocabulary in the template:

```
python3 tools/../- <<'EOF'   # run as an inline script by the controller
# For each axis row label, extract [tokens] from the template's vocabulary
# column and from each preset's cell, then assert preset ⊆ template per row
# and that all three presets carry all fifteen row labels.
EOF
```

The controller writes that comparison as a throwaway script in its scratch
directory — it is verification, not shipped tooling, so it does not land in
`tools/`. Its expected result: no row reported, exit 0.

The **eval-assertion check** (`json.tool` proves only syntax, which is not what
the criterion asks):

```
python3 -m json.tool <evals path> >/dev/null                     # exit 0, per file
grep -c 'direction sheet' .../creative-direction/evals/evals.json   # >= 1
grep -c 'counterfactual' .../creative-direction/evals/evals.json    # >= 1
grep -ciE 'VisAWI|UEQ' .../design-review/evals/evals.json           # >= 1
```

## Durable-output map

| Spec durable role | Task | Evidence path |
| --- | --- | --- |
| Current product truth | T1–T5 | the five edited or added file sets |
| Interface compatibility | T7 source manifests, T9 projection | `pack.toml`, `plugin.json`, `marketplace.json` |
| Release history | T7 | `docs/product/changelog.md` |
| Reusable learning | T6 | the two `evals/evals.json` files |
| User promise | T8 | `guides/experience-design/` |
| Decision rationale | already landed | `spec.md` Follow-ons and Assumptions |

## Design (LLD)

### Design decisions

**D1. The axis block is pinned here, once.** Every task that emits an axis
sheet copies this block verbatim. Seven structural axes lead, because
structural factors have broader and greater aesthetic effects than colour
factors (blueprint §F2.1b). A cell carrying two independent parameters carries
two tokens, so the audit can compare both; one token would hide the second.

```
## Direction sheet

<!-- Fifteen axes; the first seven are structural. Each cell OPENS with one or
     more tokens in square brackets from that row's vocabulary, then prose
     saying what it means here. Tokens are what the divergence audit compares;
     the prose is not compared. Every cell ships filled with its
     [platform-default] token — replace it, never blank it. -->

| Axis | Token vocabulary | This direction commits to |
| --- | --- | --- |
| Grid grammar | `[manuscript]` `[column]` `[modular]` `[hierarchical]` `[compound]` `[broken]` `[platform-default]`, then `[rigid]` `[relaxed]` `[platform-default]` | `[platform-default]` `[platform-default]` <track count; which transformations are permitted> |
| Alignment and equilibrium | `[edge]` `[centred]` `[baseline]` `[platform-default]`, then `[symmetric]` `[asymmetric]` `[platform-default]` | `[platform-default]` `[platform-default]` <how many distinct axes> |
| Spatial density | `[sparse]` `[comfortable]` `[dense]` `[platform-default]` | `[platform-default]` <information and group count per screenful> |
| Whitespace distribution | `[compact]` `[even]` `[expansive]` `[platform-default]` | `[platform-default]` <macro margins, gutters, section gaps; micro spacing> |
| Hierarchy and scale contrast | `[flat]` `[moderate]` `[steep]` `[platform-default]` | `[platform-default]` <hero dominance; span and size jumps> |
| Containment and boundary strength | `[open-field]` `[ruled]` `[panelled]` `[carded]` `[platform-default]` | `[platform-default]` <whether overlap is permitted> |
| Section and scroll rhythm | `[continuous]` `[episodic]` `[platform-default]`, then `[regular]` `[varied]` `[platform-default]` | `[platform-default]` `[platform-default]` <bleed cadence; pacing of a long page> |
| Type voice | `[serif]` `[sans-geometric]` `[sans-humanist]` `[monospace]` `[mixed]` `[platform-default]` | `[platform-default]` <the weight and width range used> |
| Type hierarchy | `[flat]` `[moderate]` `[dramatic]` `[platform-default]` | `[platform-default]` <the scale relationship; how many levels> |
| Chromatic intensity | `[monochrome]` `[restrained]` `[saturated]` `[high-chroma]` `[platform-default]` | `[platform-default]` <how many hues; tonal range; where accent is spent> |
| Form | `[rectilinear]` `[softened]` `[organic]` `[platform-default]` | `[platform-default]` <corner treatment across the scale; icon stroke character> |
| Material and depth | `[flat]` `[layered]` `[deep]` `[platform-default]` | `[platform-default]` <how many elevation levels; how depth is signalled> |
| Ornament and texture | `[none]` `[pattern]` `[grain]` `[illustration]` `[platform-default]` | `[platform-default]` <the ratio of image to text> |
| Image treatment | `[photographic]` `[illustrative]` `[abstract]` `[none]` `[platform-default]` | `[platform-default]` <how images are cropped; how they are toned> |
| Motion character | `[still]` `[productive]` `[expressive]` `[platform-default]` | `[platform-default]` <how far things move; relative duration; continuous or discrete> |
```

Three rows carry two tokens: grid grammar (type, then rigidity — Gerstner's
point that a grid is a programme with permitted transformations, not only a
shape); alignment and equilibrium (alignment, then symmetry — these are
independent, and conflating them was the category error the first draft made);
and section rhythm (continuity, then regularity).

**D2. Presets live in `assets/presets/`, not `references/`.** A preset is
copied and filled like the template beside it, not loaded like a reference
module. Filenames: `swiss-international-typographic.md`,
`editorial-broadsheet.md`, `bauhaus.md`.

**D3. Each preset is a pre-filled instance of the template**, so a designer
copies one and edits rather than translating a description. Sections:
frontmatter matching the template's `type: creative-direction`; formal
commitments; what a direction borrowing it leaves behind; `Best used for:`; the
D1 sheet with every row filled with real tokens, not `[platform-default]`.

**D4. The counterfactual record is a template section, not free prose**, so a
reviewer can see whether the gate ran:

```
## Counterfactual check

<!-- Work through a similar brief and compare. Any part of this direction that
     matches what any similar brief would produce is a default, not a choice.
     Revise it, then record what changed. An empty table means the check has
     not run — it does not mean nothing needed revision. -->

| Axis or goal | What the generic default was | What it became | Why |
| --- | --- | --- | --- |
```

**D5. The divergence audit is a reference module**, following the
`security-checklists/references/` house shape. It compares candidate directions
pairwise across the D1 axes on their token tuples, reports the **minimum**
pairwise figure, states why the mean is not reported (a set where four of five
candidates are near-identical has a respectable mean), and treats a pair as
distinct at **six of fifteen** axes differing. Six is the earlier four-of-ten
reasoned default carried across proportionally; it is not measured, and the
module says so.

**D6. The two rating instruments are quoted, attributed, and kept separate.**
VisAWI-S: four items, one per facet, seven-point agreement. UEQ Novelty: four
word pairs, seven-position differential. Never combined into a score.

### Behavior & rules

- A preset never closes a direction. The existing grounding requirement still
  applies; a preset supplies precedent only.
- The counterfactual gate runs before the doc is captured, so a revision lands
  in the artifact rather than as a note about it.
- The divergence audit fires only when more than one candidate direction exists.

### Dependencies & integration

No new dependency, no new top-level directory. `assets/presets/` is a
subdirectory of an existing skill's existing `assets/`.

## Tasks

Wave 1 is T1–T5 and T7 — six tasks over disjoint files, dispatched as parallel
headless Codex workers. Wave 2 is T6 and T8. Wave 3 is T9.

### T1: The template carries the fifteen-axis sheet and the counterfactual section

**Depends on:** none
**Touches:** packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md

**Tests:** no stub (goal-based). Satisfies *The direction sheet* — all six
criteria except the manual-QA one — and supplies the template section *The
counterfactual gate*'s third criterion needs. Against the template:

- `grep -c '^## Direction sheet$'` prints `1`.
- `grep -c '^## Counterfactual check$'` prints `1`.
- `grep -c '^| .* | \`\[' ` prints `15` — fifteen axis rows, each with a
  vocabulary column.
- `grep -c 'platform-default' ` prints at least `33` — fifteen vocabularies
  plus eighteen filled cell tokens.
- `grep -c '^| Motion character |'` prints `1`, and likewise for each of the
  other fourteen row labels.

**Approach:**
- Insert the D1 block after `## What each goal means` and before
  `## Dominant goal for arbitration`; insert D4 after it.
- Leave the frontmatter, goal sections, and open-questions section unchanged.

**Done when:** every count above matches and no cell is blank.

### T2: The skill directs the author through the sheet, the gate, and the presets

**Depends on:** none
**Touches:** packs/experience-design/.apm/skills/creative-direction/SKILL.md

**Tests:** no stub (goal-based). Satisfies *The counterfactual gate*'s first two
criteria and *The presets*' last criterion. Against the SKILL.md:

- `grep -ci 'direction sheet'` prints at least `1`.
- `grep -ci 'counterfactual'` prints at least `1`.
- `grep -c 'divergence-audit.md'` prints at least `1`.
- `grep -c 'presets/'` prints at least `1`.
- `grep -cF '**Writes:** <output_dir>/direction/<slug>.md'` prints `1`.
- `grep -cF '**Confinement:** references/containment.md'` prints `1`.

**Approach:**
- Add a numbered step after the current step 5 that fills the fifteen-axis
  sheet.
- Add a numbered step after it for the counterfactual check, wording the gate
  as the spec states it and requiring the revision record.
- Renumber the remaining steps.
- Name the three presets; state that a preset supplies precedent only and is
  never a finished direction.
- Point at `references/divergence-audit.md` for the multi-candidate case.
- Touch neither the managed output-rendering block, the `## Output` block, nor
  any existing anti-pattern.

**Done when:** every count above matches. **Do not run the pack lint** — it is
whole-pack and belongs to T9.

### T3: Three presets exist, each a pre-filled direction

**Depends on:** none
**Touches:** packs/experience-design/.apm/skills/creative-direction/assets/presets/*

**Tests:** no stub (goal-based). Satisfies *The presets*' first, second and
third criteria; its fourth is manual QA in T9.

- `ls .../assets/presets/ | wc -l` prints `3`.
- In each file: `grep -c 'Best used for:'` prints `1`;
  `grep -c '^| .* | \`\[' ` prints `15`; `grep -ci 'leaves behind'` prints at
  least `1`.
- No cell contains `[platform-default]` — a preset decides every axis.

**Approach:**
- Write the three files using D2 names and the D3 shape, copying the D1 rows and
  filling every cell with real tokens from that row's vocabulary.
- Carry **every** commitment its style has in blueprint §F2.2 — that table is
  the closed source, so a partial inventory fails the criterion. Swiss includes
  near-zero ornament and restrained colour alongside the grid, sans-serif,
  asymmetry, flush-left ragged-right, and photography over illustration.
  Editorial keeps its grammar **rigid**, not merely multi-column, and includes
  rules alongside the column count, type hierarchy, modular story units, and
  image-caption relationships. Bauhaus covers function-led construction, simple
  balanced geometry, limited geometric primitives, and type integrated with
  composition.
- State commitments as roles and relationships. No typeface name, no hex, no
  measurement, no easing curve, no framework name.
- If a commitment cannot be stated without a forbidden literal, **do not drop
  it** — surface it. Dropping one goes green on the lint while failing the
  preset-commitment criterion.

**Done when:** three files exist, each with fifteen fully decided rows.

### T4: The divergence audit specifies a minimum-pairwise comparison

**Depends on:** none
**Touches:** packs/experience-design/.apm/skills/creative-direction/references/divergence-audit.md

**Tests:** no stub (goal-based). Satisfies *The divergence audit*'s first three
criteria; its fourth is manual QA in T9.

- `grep -ci 'minimum pairwise'` prints at least `1`.
- `grep -ci 'mean'` prints at least `1`.
- `grep -c 'six of the fifteen'` prints at least `1`.
- `grep -c 'platform-default'` prints at least `1`.

**Approach:**
- Follow the `security-checklists/references/` house shape: when it loads, what
  it compares, what it reports, what it refuses.
- Per D5. State the comparison rules for all three cases the criterion names:
  differing token tuples, paraphrased prose after identical tokens (not a
  difference), and `[platform-default]` on both sides (not a difference).

**Done when:** every count matches and all three comparison cases are stated.

### T5: The taste critique carries both rating instruments

**Depends on:** none
**Touches:** packs/experience-design/.apm/skills/design-review/references/taste-critique.md

**Tests:** no stub (goal-based). Satisfies all three *rating instruments*
criteria.

- `grep -c 'Everything goes together on this site'` prints `1`, and likewise for
  the other three VisAWI-S items.
- `grep -c 'conventional'`, `grep -c 'leading edge'`, `grep -c 'dull'`,
  `grep -c 'conservative'` each print at least `1` — all four UEQ pairs.
- `grep -ci 'VisAWI'` and `grep -ci 'UEQ'` each print at least `1`.
- `grep -ci 'seven'` prints at least `2` — both response formats stated.

**Approach:**
- Add a rating section after the existing finding-shape section.
- VisAWI-S, seven-point agreement, one item per facet: Simplicity —
  "Everything goes together on this site"; Diversity — "The layout is
  pleasantly varied"; Colorfulness — "The colour composition is attractive";
  Craftsmanship — "The layout appears professionally designed".
- UEQ Novelty, seven-position differential: dull/creative,
  conventional/inventive, usual/leading edge, conservative/innovative.
- State that items are reported individually and never combined into one score.
- Do **not** edit `design-review/SKILL.md`: its step 69 already loads this file
  as the full method (adjudicated finding 6, refuted).

**Done when:** every count matches.

### T6: The eval harness records the new behaviour

**Depends on:** T1, T2, T5
**Touches:** the two `evals/evals.json` files

**Tests:** no stub (goal-based). Satisfies the two *eval* criteria. Verified by
the eval-assertion check in Construction tests — `json.tool` for syntax plus
a `grep` per required assertion, because syntax alone is not the criterion.

**Approach:**
- Add a creative-direction assertion naming the direction sheet, and one naming
  the counterfactual revision record.
- Add a design-review assertion naming the two rating instruments.
- Match each file's existing assertion shape exactly; do not restructure.

**Done when:** both files parse and every required `grep` matches.

### T7: The release is recorded in both manifests and the changelog

**Depends on:** none
**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, docs/product/changelog.md

**Tests:** no stub (goal-based). Satisfies the source-manifest criterion and the
three changelog criteria.

- `grep -c '2.0.6'` prints at least `1` in each source manifest.
- `grep -c '^## \[experience-design\]\[2.0.6\]' docs/product/changelog.md`
  prints `1`.
- A `Highlights` heading follows it one level down.

**Approach:**
- Set both source manifests to `2.0.6`. A **patch** bump: `packs/AGENTS.md`
  reserves minor for new primitives, and assets and reference modules added
  inside an existing skill are changed content. That file is the sole authority
  for this classification.
- Do not touch `.claude-plugin/marketplace.json`; T9 regenerates it.
- Add the release entry to `docs/product/changelog.md` following that file's own
  header rules: free-standing `## [experience-design][2.0.6] — <date>` at the
  **top level directly beneath `[Unreleased]`**, never nested inside it — a
  nested versioned entry is permanently invisible to the `/now/` projection.
  One `Highlights` subsection one level down. Exactly one blank line above and
  below every heading added.
- Write `Highlights` bullets as outcome-led user-facing sentences; they publish
  at `/now/`, which forbids development vocabulary.

**Done when:** both manifests read `2.0.6`, the entry sits at the top level
beneath `[Unreleased]` with its `Highlights`, and every added heading has single
blank lines around it.

### T8: The guide covers the four new capabilities

**Depends on:** T1, T2, T3, T4, T5
**Touches:** guides/experience-design/

**Tests:** no stub. Satisfies the *Documentation* criterion, whose sufficiency
verdict is manual QA in T9. The mechanical floor beneath it: in the edited page,
`grep -ci 'direction sheet'`, `grep -ci 'counterfactual'`, `grep -ci 'preset'`
and `grep -ci 'divergence'` each print at least `1`. Passing those four counts
is necessary and explicitly **not** sufficient.

**Approach:**
- Locate the existing creative-direction and design-review guide surfaces and
  extend them; add a new page only if none exists.
- Declare no new output path: presets and the reference module are skill
  payload, not artifacts the adopter's repository receives.

**Done when:** the four counts match and the guide-agreement test passes.

### T9: Gates are green, projections regenerated, judgements recorded

**Depends on:** T1-T8

**Tests:** no stub. Satisfies every *Gates* criterion, the marketplace
criterion, and all four manual-QA verdicts.

**Approach — order is load-bearing.** `catalogue verify` includes a self-host
drift step, so it fails against a stale `marketplace.json`; self-host refuses a
dirty tree, so the source changes are committed first.

1. `make lint-ruff lint-mypy`.
2. `python3 tools/lint-experience-agnostic.py` — the single whole-pack run, and
   the only place this lint is evidence.
3. The three roster suites.
4. The token-agreement check from Construction tests.
5. The eval-assertion check from Construction tests.
6. The five commands in `guides/AGENTS.md` § Essential commands.
7. **Record the four manual-QA verdicts** in
   `docs/specs/aesthetic-style-direction/notes/verification-ledger.md`, with the
   reviewer's name and the date: read every axis cell in the template and each
   preset and judge whether each names a role rather than a value; compare each
   preset against blueprint §F2.2; read the divergence audit's comparison rules;
   read the guide. These verdicts **are** the result for those criteria.
8. **Commit T1–T8 and the ledger** so the tree is clean.
9. `make build-self` — the worktree-owned self-host (`Makefile` sets
   `PYTHONPATH`). Never a bare `agentbundle` on `PATH`, which resolves to a
   stale install here. Run it **unforced**; if it refuses, surface rather than
   adding `FORCE=1`.
10. `make lint-packs`, then, for the two forms with no Makefile target,
    `PYTHONPATH=packages/agentbundle python3 -m agentbundle catalogue lint
    --root . --deep` and `... catalogue verify --root .`.
11. Commit the regenerated projection.

**Done when:** every command exits 0 in that order, `marketplace.json` reads
`2.0.6` for `experience-design`, the ledger carries four dated verdicts, and
`git status` is **empty**.

## Rollout

Single PR. No migration, no feature flag, no runtime surface. The pack version
bump is the release signal; adopters pick the change up on their next install.

**This is an additive behaviour change, not a no-op.** Both skills gain
mandatory procedure steps, the direction artifact gains two required sections,
and a critique gains rating items. Nothing existing is weakened or removed, and
a direction doc written before this change stays valid prose — it simply lacks
the new sections — so no artifact migration or compatibility shim is needed.

**Rollback.** Before publication, revert the commit range and restore `2.0.5`.
After adopters receive `2.0.6`, a lower version is not installable, so a
rollback ships *forward* as `2.0.7` carrying the reverted content and its own
changelog entry.

## Risks

- **A worker runs the whole-pack lint and reports a neighbour's failure.**
  Mitigated by removing the lint from every task's evidence; it appears only in
  T9. A worker that runs it anyway must not treat the result as its own.
- **The lint rejects preset prose.** No concrete required commitment has been
  shown to collide — the stack-token list omits Swiss, Bauhaus, sans-serif and
  geometry, and the CSS rule deliberately permits "grid" as a concept.
  Mitigated by D3's role-level commitments. A commitment that genuinely cannot
  be stated without a value is a contract question, not an implementer's call.
- **Axis names or tokens drift between files.** Mitigated by D1 pinning one
  block, and caught by T9's token-agreement check if a task deviates anyway.
- **`make build-self` refuses.** It refuses a dirty tree; T9 commits first. If
  it still refuses, surface — `FORCE=1` is an `Ask first` boundary.
- **A preset reads as a finished direction and skips grounding.** Mitigated by
  T2 stating the constraint in the skill and T3 stating it in each preset, so
  the warning travels with the copied file.

## Changelog

- 2026-09-18: **delivered in light mode at the owner's direction**, without the
  two G-plan human approvals. After five pre-EXECUTE review rounds the owner
  chose to stop the contract loop and implement, on the finding that this
  change is almost entirely prose and prose criteria do not mechanize. The spec
  and plan therefore record the design rather than a gated contract; the
  verification that actually ran is in `notes/verification-ledger.md` and the
  gate output on the PR.

- 2026-09-18: initial plan.
- 2026-09-18: applied 7 sustained round-1 findings — version bump corrected to
  patch `2.0.6`, the two catalogue gates added, the divergence threshold moved
  into the spec's criterion, closed comparison sources given, the lint
  re-described as a whole-pack post-wave check, and the Material exclusion
  re-grounded as a product-scope choice. Finding 6 refuted, so T5 no longer
  edits `design-review/SKILL.md`.
- 2026-09-18: applied 9 sustained round-2 findings — the changelog release
  record and its `Highlights` added, T9 resequenced so self-host precedes
  `catalogue verify`, the five guide commands added, the lint removed from
  task evidence, per-axis token vocabularies introduced so the divergence audit
  has real comparison semantics, and T3 required to carry every §F2.2
  commitment.
- 2026-09-18: axis set expanded from ten to fifteen, seven structural, on the
  layout evidence in blueprint §F2.1b–f. Seckler et al. 2015 shows structural
  factors have broader and greater aesthetic effects than colour factors; the
  old vocabulary conflated grid grammar with equilibrium; density and
  whitespace separated. Owner-approved.
- 2026-09-18: applied 10 sustained round-3 findings — every cell ships filled
  with `[platform-default]`, prose-semantics criteria accepted as recorded
  manual QA rather than pretending to a grep, catalogue commands moved to
  worktree-owned entrypoints, the ledger pulled inside the commit, rollback
  split into pre- and post-publication, and three unsupported claims removed.
- 2026-09-18: **rewrote spec and plan clean** after round 4 found fourth
  instances of two named defect classes. Four rounds of patch-amendment left
  stale cross-references every time; the structural fix is that criteria are
  now grouped under headings and referenced by section and quoted opening,
  never by number. Also from round 4: the fifteen-axis scope propagated
  everywhere, three axes given two tokens so no cell conflates independent
  parameters, the threshold settled at six of fifteen, the token-agreement and
  eval-assertion checks made real, manual QA declared in the Testing Strategy,
  and the `FORCE=1` conflict between `packs/AGENTS.local.md` and root
  `AGENTS.local.md` recorded as an `Ask first` boundary and a Follow-on.
