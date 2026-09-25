# Plan: Creative direction — five operations, divergence generation, and a capability-gated visual step

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (§ Authoring or editing a skill, § Version bump rule, § Shipped pack content carries no internal-governance citations); `guides/_shared/how-to/author-a-skill.md` (four-subdirectory layout, progressive-disclosure rule); two analogous mode-carrying skills — `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` (§ Mode selection, four modes with required outputs) and `packs/core/.apm/skills/workspace-status/SKILL.md` (§ Mode selection, subcommand table); neither analogue has a construction path: no suite tests either skill's mode table, which is itself the precedent gap. The suite this delivery must not break, `tests/roster/test_experience_design_write_declaration_and_containment.py`, tests declaration lines and containment copies rather than modes. Named uncertainty: no repository precedent exists for a capability-gated operation that degrades to a text representation, so `visualize`'s contract is authored rather than copied.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> execution observations belong in `notes/verification-ledger.md`.

## Approach

This is a content delivery: no Python ships, and every artifact is markdown under
one skill directory. The shape is a redistribution rather than a rewrite — the
ten procedure steps already carry the method, and most of the work is moving each
into the operation that owns it without losing a rule on the way.

Order of operations is driven by one constraint: the byte ceiling is only
reachable once four sections have left `SKILL.md`, and each destination must
exist before its source is cut. So references land first (T2–T5), the template
grows its three new sections (T6), and `SKILL.md` is rewritten last (T7) against
destinations that already exist. Evals and release bookkeeping follow.

The riskiest part is T7. `SKILL.md` carries two byte-pinned declaration lines, a
managed block that must not move, and a folder-span rule whose violation reds a
suite in a different pack's registry check. T7 is therefore the one task with a
pre-flight assertion of its own invariants before any edit.

Verification is goal-based throughout, with seven manual-QA judgements the spec
enumerates. There is no compressible invariant here and no Python surface, so no
TDD task appears.

## Constraints

- ADR-0024 — framework agnosticism, the decision RFC-0033's pack inherits.
  `tools/lint-experience-agnostic.py`
  is the mechanical floor; it scans the whole pack and takes no file argument.
- ADR-0116 — `creative-direction` writes to `direction/`. No new `<output_dir>`
  subfolder is declared by this delivery.
- `packs/AGENTS.md` § Shipped pack content carries no internal-governance
  citations — no file under `.apm/` may cite `docs/`.
- `packs/AGENTS.md` § Version bump rule — patch, both manifests, same edit.
- The four-subdirectory layout rule: only `scripts/`, `references/`, `assets/`,
  `evals/` may exist under a skill.

## Construction tests

Cross-cutting, run after every task that edits `SKILL.md` or a reference:

```bash
python3 tools/lint-experience-agnostic.py
```

It scans the whole pack, so it is a controller check after each wave, never
task-local evidence.

## Verification command map

**Encoding a command in a cell.** An escaped pipe inside a cell's code span
renders as a bare pipe. That is correct when a bare pipe is what the command
wants — a shell pipe, or a literal matched under `grep -F`. It is wrong when the
pipe is also regex-meaningful, because a regex alternation and the markdown
escape cannot both be satisfied by one spelling: the literal text and the
rendered text then run as different commands, and neither is the one the author
tested. A row needing an alternation states its method in words instead. Four
successive authorings of the route-table row were lost to this before the rule
was written down, so verify a new row by running the text a reader copies out of
the *rendered* table, never the text as typed.

**What this map covers.** Every goal-based criterion has a command that fails if
the criterion is unmet in the respect it exists to protect; where one command
cannot reach every obligation a criterion contracts, the rest get their own. This
map holds the cross-task criteria and every measurement more than one task reads;
a task's `Tests:` covers what the map does not reach and names the map row rather
than restating a figure or literal the map owns. One criterion settled across
both surfaces is normal here, not a duplication. `spec.md`'s Testing Strategy
states the same rule and owns its wording. `S` is
`packs/experience-design/.apm/skills/creative-direction`.

| Criterion group | Command | Expected |
| --- | --- | --- |
| Route table names its three routes | one `grep -q` per route name in `SKILL.md`, each scoped to a line that opens a table row | three hits. Exactness and the trigger/operations columns are judgement 7b, not a command. |
| `inherit` runs no divergence and no visual step | two `grep -q`, each scoped to the `inherit` table row: one for the no-divergence statement, one for the no-visual-step statement | exit 0 each. Scoped to the row, because the criterion contracts what the table states, not what the file mentions. |
| A section, component, state or feature inside a surface that already has a direction takes `inherit` | scoped to the `inherit` row's trigger cell: one `grep -q` per named subject — section, component, state, feature — plus one asserting the row's route cell names `inherit` | five hits. A bare file-wide grep for the trigger phrase passes on a row that routes it to `extend`. |
| The route rule directs an evidence-gathering lookup of the direction folder | two `grep -q` scoped to the route-rule section: one for `evidence-gathering, not a reference load`, one for the prefixed span naming the direction folder as the lookup target | exit 0 each. The folder-registry suite constrains which spans may appear anywhere in the file, not that the route rule names this one. |
| Five operation names present | one `grep -q` per operation name in `SKILL.md` | five hits. That there are exactly five, each with a one-line purpose, is judgement 7b. |
| The agent does not choose alone, and a delegated choice is recorded as delegated | `grep -q 'does not choose' "$S/SKILL.md" && grep -q 'recorded as delegated' "$S/SKILL.md"` | exit 0 each |
| Step-to-operation mapping complete | one `grep -q` per assignment: the ten steps make twelve assignments, because the sheet fill splits across `explore` and `converge` and the floor hold across `converge` and `refine`; each owning operation's section in `SKILL.md` or its reference names that act's subject | twelve hits, no act unassigned. Ten would pass while one half of each split went unwritten. |
| Every shipped reference reachable **from its owning operation** | per reference, `grep -q` scoped to the owning operation's section in `SKILL.md` or to that operation's own reference file, per the step-to-operation mapping | one hit each. A repo-wide grep would pass on a link between two references, which is not reachability from an operation. |
| `**Writes:**` / `**Confinement:**` exactly once and unchanged | a `grep -c` per line, then `git diff --exit-code` scoped to `SKILL.md` and inspected for those two lines | `1` each; the two lines absent from the diff. A count alone does not establish byte-identity, which is what the roster suite compares. |
| Authored-body ceiling ≤ 6,500 B | the **authored-body measurement** (below) | ≤ 6500 |
| Directory ≤ 97,000 B | `find "$S" -type f -exec cat {} + \| wc -c` | ≤ 97000 — amended from 95,000 on 2026-09-25; the spec criterion owns the arithmetic |
| Description ≤ 1024 chars | the **description measurement** (below) | ≤ 1024; reads **784** today |
| Fifteen axis rows intact | count pipe rows in the Direction sheet section | `17` — header + separator + fifteen axes |
| Template frontmatter `status` placeholder | `grep -qF 'status: "<proposed \| selected>"' "$S/assets/creative-direction-template.md"` | exit 0 (absent today; T6 adds it). `-F` because the value carries regex metacharacters. |
| Evals carry cases A–D | assert the four case ids exist **and** every distinguishing assertion string the criterion names: no-divergence-round and no-second-doc for A; default-and-opposite and six-axis distinctness for B; audience-domain-majority for C; only-named-axes, goals-unchanged and amended-not-replaced for D | four ids and all eight strings — two for A, two for B, one for C, three for D. A count of four passes while half the assertions are absent, including two of Case D's three. |
| Containment byte-equality across copies | `python3 -m pytest tests/roster/test_experience_design_write_declaration_and_containment.py -q` | pass |
| Folder registry | `python3 -m pytest tests/roster/test_experience_design_artifact_folder_registry.py -q` | pass |
| Guide agreement | `python3 -m pytest tests/roster/test_experience_design_guide_agreement.py -q` | pass |
| Journey composition | `python3 -m pytest tests/roster/test_experience_journey_composition.py -q` | pass |
| Handoff contract corpus | `python3 -m pytest tests/roster/test_design_handoff_contract_matches_corpus.py -q` | pass |
| Versions read `2.0.10` | `grep -c '"\?2\.0\.10"\?' packs/experience-design/pack.toml packs/experience-design/.claude-plugin/plugin.json` and `python3 -c "import json;print([p['version'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins'] if p['name']=='experience-design'])"` | `1` per source manifest; `['2.0.10']` from the projection. A bare `grep -h version` is not usable: `pack.toml` alone already matches three lines. |
| The three presets stay reachable by link | `grep -q 'assets/presets' "$S/references/referents.md"` — T5 writes the link, T7 removes the section that held it | exit 0 |
| Changelog entry is well-formed | parse `docs/product/changelog.md`: the new entry is a `##` heading, its position is directly beneath the `[Unreleased]` section rather than nested inside it, it carries exactly one `Highlights` subsection, and every heading it adds has exactly one blank line above and below | all four hold. `tools/build-site.py` fails closed on a nested entry — it withholds it as unreleased rather than rejecting it — so the site build exits 0 either way and cannot serve as this check. |
| Gates 1, 3 and 4 survive unchanged | `git show 9748dd256:"$S/SKILL.md"` and the working copy, comparing the three surviving `## When to invoke` gate lines byte for byte | identical. The criterion's other two conjuncts — gate 2 gone, the preamble asking for three — are separately greppable; this row covers the conjunct that has no string to grep, which is how a deleted clause reached the ledger unobserved. |
| `DESIGN.md` § 10 untouched | `git diff --exit-code "$(git merge-base origin/main HEAD)" -- packs/experience-design/DESIGN.md` | exit 0 — against the delivery's base, not the working tree. A working-tree diff goes clean the moment an earlier task commits the edit, so it cannot see a violation this eleven-task delivery introduces. |
| Agnosticism | `python3 tools/lint-experience-agnostic.py` | exit 0 |
| Catalogue | `agentbundle catalogue lint --root . --deep && agentbundle catalogue verify --root .` | exit 0 |
| Guides | the five commands in `guides/AGENTS.md` § Essential commands | each exit 0 |
| Repo lint | `make lint-ruff lint-mypy` | exit 0 |
| Spec-status | `python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .` | exit 0 |

**The authored-body measurement** — inlined at each use site; no file ships,
because a script under the skill would count against the directory ceiling and
appears in neither the spec's What Changes nor its Durable Outputs. Both regex
matches must be guarded: an absent frontmatter or managed block is a hard error,
not an `AttributeError`.

```bash
python3 - "$S/SKILL.md" <<'PY'
import re,sys
t=open(sys.argv[1]).read()
fm=re.match(r'---\n.*?\n---\n',t,re.S).group(0)
blk=re.search(r'<!-- agentbundle:output-rendering:start -->.*?<!-- agentbundle:output-rendering:end -->',t,re.S).group(0)
print(len(t.encode())-len(fm.encode())-len(blk.encode()))
PY
```

Pre-fold reading: **9,699**, confirmed 2026-09-24.

**Section-boundary convention.** Owned by the context-footprint criterion in
`spec.md`, which states the convention and both totals. Measurements here use
it; this plan does not restate the figures.

**The description measurement** — the frontmatter description only. A greedy
`description: "(.*)"` with `re.S` swallows the whole file and reports ~12,500;
the match must be scoped to the frontmatter block first, then to the
`description:` line within it. Reads **784** today.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current product truth — six references under `<S>/references/` | T2–T5 | Each file exists and carries the strings its task tests | Pack lint clean; manual-QA judgements 2 and 4 recorded |
| Current product truth — template at `<S>/assets/creative-direction-template.md` | T6 | Three new sections and the `status` field present; fifteen axes and `type:` intact | Roster suites green |
| Current product truth — `<S>/SKILL.md` | T7 | Authored body ≤ 6,500 B; both declaration lines unchanged | All five roster suites green |
| Current product truth — reviewer lens at `.apm/agents/experience-reviewer.md` | T6 | The four grounding terms match the template | Lens and template agree |
| Reusable learning — `<S>/evals/` | T8 | Both files parse; four cases with their assertions | Manual-QA judgement 1 recorded |
| User promise — `guides/experience-design/how-to/establish-design-intent.md` | T9 | Guide-agreement suite green | Manual-QA judgement 5 recorded |
| Interface compatibility + release history — three manifests and the changelog | T10 | All three read `2.0.10`; changelog entry well-formed | Both catalogue commands exit 0 |
| Verification record — `notes/verification-ledger.md` | T1, T9, T11 | Pre-change readings and pinned revision; seven verdicts | Every judgement named with reviewer and date |

## Design (LLD)

### Design decisions

**The operations are a vocabulary, not a state machine.** `SKILL.md` carries a
route rule and a selection rubric; it does not carry transitions. A state machine
would need state to live somewhere, and the only durable state this skill has is
the direction doc's `status` field. Three values in frontmatter are cheaper than a
transition table and are readable by a consumer that already parses frontmatter.

**Divergence generation reuses the existing audit rather than scoring its own.**
`divergence-audit.md` already computes minimum pairwise distance over the fifteen
axes. `explore` produces candidates and hands them to it. Writing a second
distinctness measure would create two thresholds that drift.

**`refusals.md` is separate from `referents.md`.** They read as one "anti-pattern"
concern and are not: refusals are about this skill's own failure modes and bind
every operation; referents are named products used to calibrate craft, and carry
an era label. Merging them would put a dated product list inside a durable rule
set.

**`frame` ships no reference.** Its method is short and its two existing
references already exist. A third file holding six bullets would cost a load
without reducing the body.

### Component / module decomposition

```
creative-direction/
  SKILL.md              route rule, five operations, rubric, output contract
  references/
    explore.md          NEW  rut naming, referent derivation, family spread
    converge.md         NEW  comparison, standing exit, donation, counterfactual
    visualize.md        NEW  three representations and their binding force
    refine.md           NEW  wording→axis map, stability contract
    referents.md        NEW  craft-calibration tier, era-labelled; carries
                             the assets/presets link SKILL.md drops
    refusals.md         NEW  the seven existing anti-patterns
    audience-jtbd.md         unchanged, linked from frame
    interrogation-sequence.md unchanged, linked from frame
    grounding.md             unchanged, linked from converge
    coherence-arbitration.md unchanged, linked from converge
    divergence-audit.md      unchanged, linked from explore
    containment.md           unchanged, byte-pinned
    agentbundle-layout.md    unchanged
  assets/                    template + three presets
  evals/                     eval_queries.json, evals.json
```

### Failure, edge cases & resilience

- Harness without image generation: `visualize` produces a text schematic and
  records a named skip. No operation blocks.
- A surface with no existing direction on the `inherit` route: the route rule's
  lookup finds nothing and routes to `extend` or `originate`.
- A `refine` request naming an axis outside the fifteen: refused, with the axis
  vocabulary as the answer.

## Tasks

### T1: The pre-flight invariants are recorded and green

**Depends on:** none

**Tests:**
- The authored-body measurement — the inlined block under the Verification
  command map, not a shipped script — reads the pre-fold figure that map records.
- The two declaration lines each `grep -c` to exactly `1`.
- The five roster suites the map lists pass before any edit.

**Approach:** the ledger records the pre-change git revision of `SKILL.md`
explicitly, not only the byte readings. T7 rewrites that file, so after T7 the
pre-change skill exists nowhere in the working tree — and manual-QA judgement 1
requires running the four eval cases against it. A pinned revision is how T11
retrieves it.

**Done when:** `notes/verification-ledger.md` records the pre-change readings and
the git revision they were taken at.

**Touches:** docs/specs/creative-direction-modes/notes/verification-ledger.md

### T2: `explore.md` generates candidates the existing audit can score

**Depends on:** T1

**Why held:** this task and its three siblings author independent files and could
run in parallel. They are held behind T1 so no authoring begins before the
pre-change readings and the pinned revision exist, because T7's comparison and
judgement 1 both depend on them and neither is recoverable afterwards.

**Tests:**
- `grep -q` for the category-default-and-opposite exclusion rule.
- `grep -q` for each of the eight named source classes, and `grep -q` for the
  statement that other software products are not the primary source — the
  criterion's second conjunct, and a different claim from the named-software-
  product test below.
- `grep -q` for the material-family spread rule.
- `grep -q "divergence-audit.md"` — the handoff exists.
- `grep -q` for the statement that candidate sheets stay in the session and are
  not written to disk. Persisting them would be a second write target against a
  roster suite that pins one, and would make `experience-status` count rejected
  candidates as directions.
- `grep -q` for the statement that a candidate drawn from a named software
  product has not left the category default.
- `grep -q` for the requirement that each surviving candidate carries its own
  filled direction sheet.
- `grep -q` for the rule that a set failing the six-of-fifteen minimum is not a
  candidate set and sends the author back to derive more.

**Done when:** `references/explore.md` exists and every string above is present.

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/explore.md

### T3: `converge.md` owns selection and the four steps that move with it

**Depends on:** T1

**Tests:**
- `grep -q` for equal-salience presentation and the differing-axes-only rule.
- `grep -q` for each of the standing exit's four obligations in turn: the
  category standard played straight, offered in every divergence round, never
  recommended by the agent, and executed at full commitment when chosen. The
  every-round and full-commitment obligations are what stop the exit becoming a
  token option, and neither is reachable from the never-recommend wording.
- `grep -q` for the borrowed-discipline record in both its permitted forms: a
  named discipline taken from a rejected candidate, and the explicit statement
  that none was. Without the second, the field is unfillable when nothing was
  borrowed.
- `grep -q` for the counterfactual check as a required doc field.
- `grep -q` for the fifteen-axis sheet fill.
- `grep -q "quality-floor.md"` — the floor hold survives the move.
- The capture sequence keeps the control order: read `references/containment.md`'s
  control headings in file order, then assert `references/converge.md` names them
  in that same order, with its `output_dir` resolution named before the first
  control. This is the criterion whose loss is a confinement failure, so it is
  tested directly rather than inferred from `containment.md` being unchanged.

**Approach:** grounding, ranking, arbitration, the floor hold, the capture
sequence and the handoff all land here rather than being split, because each
consumes the selected direction and none of them can run before selection. The
capture sequence in particular must stay whole: `containment.md`'s controls are
ordered and the spec forbids reordering them.

**Done when:** `references/converge.md` exists, carries all six strings, and
`containment.md` is unchanged (`git diff --exit-code` on that file).

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/converge.md

### T4: `visualize.md` and `refine.md` state their contracts

**Depends on:** T1

**Tests:**
- `visualize.md`: all three representations named, each with its binding force
  stated — the semantic direction binding, the visualised candidate illustrative
  and non-binding, the approved visual target binding on composition only. One
  `grep -q` per representation's force; the never-binds-values clause below is a
  different criterion and does not reach the first two.
- `visualize.md`: the never-binds-values clause; the
  commitments-into-the-direction-doc clause; the text-schematic default stated
  with no internal-governance citation — the pattern `packs/AGENTS.local.md`
  commits finds nothing in the file, asserted so success exits 0.
- `refine.md`: the statement that these are request wordings, not separate
  operations — the clause that stops `bolder` and `quieter` reading as
  operations alongside the five.
- `refine.md`: the seven request wordings each map to axes; the stability
  contract names goals, dominant goal, referents, signature device, unnamed axes;
  the floor obligation is present; the amendment-not-new-doc rule is present; and
  it refuses to reopen goals, audience or product strategy, naming where each
  belongs.
- Neither new file names a specific design tool. `tools/lint-experience-agnostic.py`
  carries no rule for tool names, so `DESIGN.md` § 10's invariant is checked here
  or nowhere; tool categories remain allowed.
- `visualize.md`: `grep -q` for the statement that it writes no file of its own.
- `visualize.md`: `grep -q` for the wireframe-over-screenshot rule, stated
  directly. It is the reason the text schematic is the default, and the only
  conjunct of its criterion with no other carrier.
- `visualize.md`: a rendered comp is produced only when the harness can produce
  one **and** the route is `originate`, and its absence is a named skip rather
  than a blocker — this is the clause the whole capability gate rests on.

**Done when:** both files exist, every string above is present, and neither
file carries an internal-governance citation under the committed pattern.

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/visualize.md, packs/experience-design/.apm/skills/creative-direction/references/refine.md

### T5: `referents.md` and `refusals.md` receive what leaves `SKILL.md`

**Depends on:** T1

**Tests:**
- `referents.md` carries the seven genre tiers, the craft-calibration statement,
  the not-a-source-for-explore statement, the per-entry classification, an era
  label on every model-era entry, the statement that the accessibility floor is
  **not** among its entries, the pointer to the shared quality floor, and
  the existing requirement to name which qualities of a reference are taken and
  which are left.
- `refusals.md` carries all seven existing anti-pattern entries; a diff of their
  obligation wording against the pre-change `SKILL.md` shows no weakening.

**Approach:** the two files are authored together because the split between them
is the decision — an entry naming a product goes to `referents.md`, an entry
naming a failure mode goes to `refusals.md`. Authoring them apart invites an
entry landing in both or neither.

- `referents.md` carries no `step <n>` reference. Two of the sentences it
  inherits say "step 3" today, including the take-and-leave requirement above;
  each is re-anchored to the operation that now owns the act.
- `referents.md` links `assets/presets`, which is where the three presets stay
  reachable once `SKILL.md`'s `## Style presets` section leaves in T7. Precedent
  material is this reference's concern, so the link belongs here.

**Done when:** both exist, the seven refusals are present, every `referents.md`
entry carries one of the three classifications, and the preset link resolves.

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/referents.md, packs/experience-design/.apm/skills/creative-direction/references/refusals.md

### T6: The template carries three new sections and the `status` field

**Depends on:** T1

**Tests:**
- `experience-reviewer.md`'s grounded-aesthetic-fit lens and the template share
  the exact four-term set: `persona`, `precedent`, `standards`,
  `platform conventions` — one `grep -q` per term in each file.
- The map's `status`-placeholder row passes; that row owns the literal, and the
  form matches the template's existing `surface` field. What this task adds
  beyond it is the documenting prose naming which operation writes each value:
  `converge` writes `proposed` on capture when the human has not yet confirmed
  the direction, and `selected` once they have. `explore` writes no file at all,
  and `inherit` writes no doc, so neither names a value.
- The borrowed-discipline section exists and carries a field for each thing the
  criterion names: the donor candidate, and the discipline taken. An empty
  heading satisfies an existence test and satisfies neither of these.
- The refinement-amendment section exists and carries a field for each thing the
  criterion names: which axes moved, the token each moved from, the token each
  moved to, and why.
- A compositional-commitments section exists.
- The map's axis-row measurement still holds. `## Counterfactual check` is
  still present, and `type: creative-direction` is still in frontmatter.

- `python3 tools/lint-guidebook-steps.py guides/experience-design` exits 0. The
  guide's `**What it looks like:**` excerpt is checked as a contiguous verbatim
  run of the template, so adding the `status` field breaks it: measured, the
  lint exits 0 before the field is added and 1 after, reporting
  `artifact_preview: excerpt does not appear verbatim in its declared source`.
  The excerpt is re-synced here, in the task that breaks it, rather than
  surfacing unowned at T10's gates.

**Done when:** the three new sections and the `status` frontmatter field all
exist, the three pre-existing invariants still hold, and the guidebook-steps
lint is green.

**Touches:** packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md, packs/experience-design/.apm/agents/experience-reviewer.md, guides/experience-design/how-to/establish-design-intent.md

### T7: `SKILL.md` is the route rule, five operations and the output contract, under the ceiling

**Depends on:** T2, T3, T4, T5, T6

**Tests:**
- The inlined authored-body measurement reads at or below the map's ceiling.
- The two declaration lines still `grep -c` to exactly `1` and are byte-identical
  to their pre-change form (`git diff` shows those lines unchanged).
- No unprefixed bare folder span.
- The map's route-table, inherit, already-has-a-direction, lookup,
  five-operations and delegation rows all pass.
- The route rule states the no-second-direction-doc obligation in `SKILL.md`
  itself, not only in `references/refine.md`: `grep -q` scoped to the route-rule
  section. `inherit` never loads `refine.md`, so a rule living only there does
  not reach the route Case A tests.
- Each of the four operations links the reference carrying its own method, by
  name: `explore` → `explore.md`, `visualize` → `visualize.md`, `converge` →
  `converge.md`, `refine` → `refine.md`. "Four operations link a reference"
  passes when `converge` links `explore.md`.
- `frame` links its two existing references plus `refusals.md`.
- No internal-governance citation: the pattern `packs/AGENTS.local.md` commits
  finds nothing in the file. A bare `docs/` substring is not the test.
- `frame` states its seven-item terse set: one `grep -q` each within `frame`'s
  section for audience, ranked JTBD, target surface, incumbent constraints,
  intended effect, what must stay recognisable, what would read as generic, and
  the named goals the interrogation produces — eight hits, the goals included.
- `frame` states it does not recreate product discovery or journey design, and
  names the skill each belongs to.
- `frame` ships no reference of its own: `! test -e "$S/references/frame.md"`.
  This sits with the rest of its criterion's conjuncts rather than in the map.
- Every operation links `refusals.md`: one `grep -q 'refusals.md'` scoped to each
  of the five operation sections in turn — five hits. The criterion binds every
  operation, not only `frame`, and `refusals.md` is new, so the shipped-reference
  reachability row does not reach it.
- The fifteen axis names stay reachable by link: `SKILL.md` names
  `divergence-audit.md`, which carries the axis table.
- No numbered-procedure-step reference survives: `! grep -rqiE '\bstep [0-9]' "$S/SKILL.md" "$S/references/"`.
  Verified non-vacuous — no file under `references/` carries one today, and
  `SKILL.md` carries five, two of them inside the text T5 moves.
- `SKILL.md` names `referents.md`. This task deletes the two sections holding
  the only live link to `assets/presets`, so without it the craft-calibration
  tier and the presets it inherits are reachable from nothing.
- The description measurement stays within the map's character limit and the
  description still names the three boundary skills.
- The description names refining or amending an existing direction among its
  trigger phrasings: `grep -qiE 'refin|amend' ` over the frontmatter block. The
  pre-change description carries none of those words, so this fails before the
  edit and is what makes T8's refinement positives able to pass.
- The five roster suites the map lists pass.

**Approach:** rewrite last, against destinations that already exist, so no step
is cut before its new home is readable. Assert the two declaration lines before
and after rather than trusting the edit — the roster suite compares a parsed set
against a single expected value, so a second `**Writes:**` line fails even when
the first is correct.

**Done when:** every test above passes. The agnosticism lint is not a task-local
condition here — it scans the whole pack, so it runs as a Construction test after
the wave, per this plan's own Construction tests section.

**Touches:** packs/experience-design/.apm/skills/creative-direction/SKILL.md

### T8: The four behavioural cases separate old behaviour from new

**Depends on:** T7

**Tests:**
- `evals.json` parses; four new cases present with ids and assertion arrays.
- Case A asserts no divergence round and no second doc; B asserts default and
  opposite named and excluded plus six-axis distinctness; C asserts a majority of
  referents from the audience's domain; D asserts all three of its conjuncts —
  only the named axes moved, the ranked goals and dominant goal are unchanged,
  and the existing doc was amended rather than replaced. The last two are what
  make D a refinement case rather than a rewrite.
- `eval_queries.json` parses and carries the refinement-shaped positives this
  change adds. The `design-system` / `design-review` negatives are not tested
  here: the file already carries four, so that assertion passes on the
  unmodified file and would not catch their loss either.

**Done when:** both files parse and carry the named cases.

**Touches:** packs/experience-design/.apm/skills/creative-direction/evals/evals.json, packs/experience-design/.apm/skills/creative-direction/evals/eval_queries.json

### T9: The guide describes the route rule and the five operations

**Depends on:** T6, T7

**Why both:** two tasks touch this guide. T6 re-syncs the template excerpt its
own edit breaks; this task writes the operation coverage. The edge keeps them
ordered rather than editing one file with nothing between them.

**Tests:**
- The map's guide-agreement row passes.
- The guide's `**Where it lands:**` path matches `SKILL.md`'s declared target.
- `python3 tools/lint-guidebook-steps.py guides/experience-design` exits 0. That
  lint closes the page's `##` set to `What you will run`, one `` Run `<skill>` ``
  per skill in run order, and `Where this leads` — nothing else at that level.
  Covering the route rule and five operations under a new `##` reds it, so the
  new content goes inside the existing headings. T6 carries this lint for the
  template edit; T9 carries it for the guide edit, by the same rule.

**Done when:** the suite passes, the guide covers all five operations, and T9
writes verdict 5 (guide sufficiency) into the ledger — it is this output's
closeout condition in the spec, not a T11 afterthought. T9 owns writing that one
verdict; T11 writes the other six and checks all seven are present.

**Touches:** guides/experience-design/how-to/establish-design-intent.md, docs/specs/creative-direction-modes/notes/verification-ledger.md

### T10: The release is registered

**Depends on:** T7, T8, T9

**Tests:**
- The map's version row holds across all three surfaces. `marketplace.json` is
  regenerated by the unforced `make build-self`, which runs
  `agentbundle catalogue self-host --root . --write`; `git diff` shows it
  changed only in the generated region. The `FORCE=1` form is not used, and the
  unforced form is what regenerates the projection, so no refusal is reached.
- The changelog entry is free-standing directly beneath `[Unreleased]`, carries
  one `Highlights` subsection, and every added heading has one blank line above
  and below.
- `agentbundle catalogue lint --root . --deep` and `verify --root .` exit 0.

**Done when:** all three version surfaces agree and both catalogue commands pass.

**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

### T11: The seven manual-QA judgements are recorded

**Depends on:** T10

**Tests:**
- Seven verdicts, each naming the judgement by number, the artifact it read, the
  reviewer, and the date:
  1 — the four eval cases against the pinned pre-change `SKILL.md`;
  2 — each operation's stability contract, read across `SKILL.md` for `frame`
      and `references/explore.md`, `visualize.md`, `converge.md` and `refine.md`
      for the other four. Only `frame` is inline; the 6,500-byte ceiling and
      judgement 7a's no-paraphrase-back rule both forbid restating the rest in
      the body, so a read scoped to `SKILL.md` cannot settle completeness or
      non-overlap;
  3 — the selection rubric in `SKILL.md`, read without opening a reference;
  4 — the era labelling in `references/referents.md`;
  5 — the guide (written by T9, which owns this verdict; T11 checks it is
      present rather than writing it again);
  6 — the visual-precondition sweep across `SKILL.md` and `references/`;
  7a — the four departing sections, read in the post-change `SKILL.md` against
      the revision T1 pinned, each confirmed gone with its method intact in the
      operation reference that now owns it;
  7b — all three enumerations 7b names, read as rendered: in the post-change
      `SKILL.md`, the route table carries exactly three routes, each with a
      trigger condition and the operations it runs, and exactly five operations
      are named, each with a one-line purpose; and in
      `references/visualize.md`, exactly three representations are defined. The
      third lives outside `SKILL.md` and is the one a ledger scoped to that file
      silently drops. A ledger recording 7a without 7b fails: 7b is
      where the deleted route-table measurement's criterion half now lives, and
      it is the only surface that reaches it.
- Judgement 1 names the pinned pre-change revision it ran the cases against.

**Approach:** last, because judgement 1 needs both sides — the post-change eval
cases from T8, and the pre-change `SKILL.md`, retrieved at the git revision T1
pinned rather than from the working tree, where T7 has replaced it.

**Done when:** the ledger records all seven with names and dates.

**Touches:** docs/specs/creative-direction-modes/notes/verification-ledger.md

## Rollout

Single PR. No migration: the artifact path, its `type:`, and the fifteen axes are
unchanged, so an existing `direction/<slug>.md` stays valid and a consumer reading
it sees no difference. An adopter on `2.0.9` who upgrades gains operations and
loses no artifact.

No feature flag and no staged rollout — the unit of delivery is a markdown skill,
and a partial install is not a state the installer produces.

## Risks

- **The ceiling is tight.** The context-footprint criterion in `spec.md` owns
  the arithmetic and the margin; this plan does not restate the figure. If T7 cannot
  reach 6,500 without cutting a rule, the ceiling is the thing that moves, not the
  rule — and the criterion is amended through the controlled path rather than
  quietly missed.
- **A rule is lost in redistribution.** Ten steps and seven refusals move between
  files. T5 and T7's diff-based tests catch wording weakening; the seven manual-QA
  judgements catch what a grep cannot.
- **The folder-span rule bites late.** A bare `` `references/` `` anywhere in T7's
  rewrite reds a registry suite in a cross-cutting test, not in T7's own. T7 lists
  it explicitly for that reason.

## Changelog

<!-- Approvals only. Drafting history does not belong here. -->

- 2026-09-24 — Scope approved by eugenelim. Nine pre-EXECUTE adversarial rounds ran
  before this gate; 74 findings were sustained and applied, 12 refuted, one
  indeterminate resolved by measurement. Two rules were replaced during that
  sequence: the Testing Strategy's per-conjunct coverage rule, which proved
  unachievable across the criteria list, and the "exactly one surface"
  partition claim, which was false and so could not detect an uncovered
  criterion. Round 9's eight findings were applied but not re-reviewed; the
  owner directed approval at that point, accepting that residual, with a
  confirmatory review scheduled before T7.
- 2026-09-24 — Build strategy approved by eugenelim. T1-T11 in dependency order, single
  PR, no migration. Verification is goal-based plus seven manual-QA judgements;
  the route table's and the five operations' exactness, and the four departing
  sections, are judgement 7 rather than commands, because a pattern written
  against a file no one has authored cannot bound a count — four such patterns
  were written and each failed for a reason unrelated to its criterion.
- 2026-09-24 — Baseline re-pinned after a non-substantive
  correction: `loop-cohort schedule` refused with a dependency cycle across T2
  and T9, because `Depends on:` is parsed for task IDs and both fields carried
  rationale prose naming other tasks — T2's "T2–T6 author independent files"
  and T9's "T9 writes the operation coverage" each read as a self-edge. The
  rationale moved to a `Why held:` / `Why both:` line below each field; the
  dependency set is unchanged. T2's form was pre-existing in the approved plan.
  Nine adversarial rounds passed over these fields without catching it, because
  no round ran the scheduler.