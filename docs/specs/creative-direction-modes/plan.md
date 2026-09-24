# Plan: Creative direction — five operations, divergence generation, and a capability-gated visual step

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
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

Verification is goal-based throughout, with six manual-QA judgements the spec
enumerates. There is no compressible invariant here and no Python surface, so no
TDD task appears.

## Constraints

- RFC-0033 / ADR-0024 — framework agnosticism. `tools/lint-experience-agnostic.py`
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

**What this map covers.** Cross-task criteria, gate invocations, and the
measurements more than one task reads. Criteria local to a single task are
settled by that task's `Tests:` instead, so the two surfaces partition the
spec's goal-based set rather than duplicating it. `spec.md`'s Testing Strategy
states the same division. `S` is
`packs/experience-design/.apm/skills/creative-direction`.

| Criterion group | Command | Expected |
| --- | --- | --- |
| Route table, five operations, rubric, delegation statement | `grep -c '^| *`\`\``inherit`\`\`' "$S/SKILL.md"` and per-string `grep -q` | each present once |
| Step-to-operation mapping complete | one `grep -q` per assignment: for each of the ten steps, its owning operation's section in `SKILL.md` or its reference names that step's subject | ten hits, no step unassigned |
| Ten-step procedure body gone from `SKILL.md` | count numbered steps under `## Procedure` | `0` |
| Every shipped reference reachable **from its owning operation** | per reference, `grep -q` scoped to the owning operation's section in `SKILL.md` or to that operation's own reference file, per the step-to-operation mapping | one hit each. A repo-wide grep would pass on a link between two references, which is not reachability from an operation. |
| `**Writes:**` / `**Confinement:**` exactly once and unchanged | a `grep -c` per line, then `git diff --exit-code` scoped to `SKILL.md` and inspected for those two lines | `1` each; the two lines absent from the diff. A count alone does not establish byte-identity, which is what the roster suite compares. |
| Authored-body ceiling ≤ 6,500 B | the **authored-body measurement** (below) | ≤ 6500 |
| Directory ≤ 95,000 B | `find "$S" -type f -exec cat {} + \| wc -c` | ≤ 95000 |
| Description ≤ 1024 chars | the **description measurement** (below) | ≤ 1024; reads **784** today |
| Fifteen axis rows intact | count pipe rows in the Direction sheet section | `17` — header + separator + fifteen axes |
| Template frontmatter `status` enum | `grep -qE '^status: (proposed\|selected\|inherited)'` on the template | exit 0 (absent today; T6 adds it) |
| Evals carry cases A–D | assert the four case ids exist **and** one distinguishing assertion string per case (no-divergence-round for A; default-and-opposite for B; audience-domain-majority for C; only-named-axes for D) | four ids, four strings. A bare length check passes on four empty entries. |
| Containment byte-equality across copies | `python3 -m pytest tests/roster/test_experience_design_write_declaration_and_containment.py -q` | pass |
| Folder registry | `python3 -m pytest tests/roster/test_experience_design_artifact_folder_registry.py -q` | pass |
| Guide agreement | `python3 -m pytest tests/roster/test_experience_design_guide_agreement.py -q` | pass |
| Journey composition | `python3 -m pytest tests/roster/test_experience_journey_composition.py -q` | pass |
| Handoff contract corpus | `python3 -m pytest tests/roster/test_design_handoff_contract_matches_corpus.py -q` | pass |
| Versions read `2.0.10` | `grep -c '"\?2\.0\.10"\?' packs/experience-design/pack.toml packs/experience-design/.claude-plugin/plugin.json` and `python3 -c "import json;print([p['version'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins'] if p['name']=='experience-design'])"` | `1` per source manifest; `['2.0.10']` from the projection. A bare `grep -h version` is not usable: `pack.toml` alone already matches three lines. |
| `DESIGN.md` § 10 untouched | `git diff --exit-code packs/experience-design/DESIGN.md` | exit 0 — this delivery does not edit it; the genre fold does |
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

**The description measurement** — the frontmatter description only. A greedy
`description: "(.*)"` with `re.S` swallows the whole file and reports ~12,500;
the match must be scoped to the frontmatter block first, then to the
`description:` line within it. Reads **784** today.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current product truth — six references under `<S>/references/` | T2–T5 | Each file exists and carries the strings its task tests | Pack lint clean; manual-QA judgements 2 and 4 recorded |
| Current product truth — template at `<S>/assets/creative-direction-template.md` | T6 | Four new sections present; fifteen axes and `type:` intact | Roster suites green |
| Current product truth — `<S>/SKILL.md` | T7 | Authored body ≤ 6,500 B; both declaration lines unchanged | All five roster suites green |
| Current product truth — reviewer lens at `.apm/agents/experience-reviewer.md` | T6 | The four grounding terms match the template | Lens and template agree |
| Reusable learning — `<S>/evals/` | T8 | Both files parse; four cases with their assertions | Manual-QA judgement 1 recorded |
| User promise — `guides/experience-design/how-to/establish-design-intent.md` | T9 | Guide-agreement suite green | Manual-QA judgement 5 recorded |
| Interface compatibility + release history — three manifests and the changelog | T10 | All three read `2.0.10`; changelog entry well-formed | Both catalogue commands exit 0 |
| Verification record — `notes/verification-ledger.md` | T1, T11 | Pre-change readings and pinned revision; six verdicts | Every judgement named with reviewer and date |

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
    referents.md        NEW  craft-calibration tier, era-labelled
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
- `body-bytes.sh` prints `9699`.
- The two declaration lines each `grep -c` to exactly `1`.
- All five roster suites pass before any edit.

**Approach:** the ledger records the pre-change git revision of `SKILL.md`
explicitly, not only the byte readings. T7 rewrites that file, so after T7 the
pre-change skill exists nowhere in the working tree — and manual-QA judgement 1
requires running the four eval cases against it. A pinned revision is how T11
retrieves it.

**Done when:** `notes/verification-ledger.md` records the pre-change readings and
the git revision they were taken at.

**Touches:** docs/specs/creative-direction-modes/notes/verification-ledger.md

### T2: `explore.md` generates candidates the existing audit can score

**Depends on:** T1 — deliberate. T2–T6 author independent files and could run in
parallel; they are held behind T1 so no authoring begins before the pre-change
readings and the pinned revision exist, because T7's comparison and judgement 1
both depend on them and neither is recoverable afterwards.

**Tests:**
- `grep -q` for the category-default-and-opposite exclusion rule.
- `grep -q` for each of the eight named source classes.
- `grep -q` for the material-family spread rule.
- `grep -q "divergence-audit.md"` — the handoff exists.
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
- `grep -q` for the standing exit and its never-recommend clause.
- `grep -q` for the borrowed-discipline record.
- `grep -q` for the counterfactual check as a required doc field.
- `grep -q` for the fifteen-axis sheet fill.
- `grep -q "quality-floor.md"` — the floor hold survives the move.

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
- `visualize.md`: three representations named; the never-binds-values clause; the
  commitments-into-the-direction-doc clause; the text-schematic default stated
  without any `docs/` citation (`grep -c 'docs/' "$S/references/visualize.md"` → `0`).
- `refine.md`: the seven request wordings each map to axes; the stability
  contract names goals, dominant goal, referents, signature device, unnamed axes;
  the floor obligation is present; the amendment-not-new-doc rule is present; and
  it refuses to reopen goals, audience or product strategy, naming where each
  belongs.
- `visualize.md`: a rendered comp is produced only when the harness can produce
  one **and** the route is `originate`, and its absence is a named skip rather
  than a blocker — this is the clause the whole capability gate rests on.

**Done when:** both files exist and every string above is present, with the
`docs/` count at zero in both.

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/visualize.md, packs/experience-design/.apm/skills/creative-direction/references/refine.md

### T5: `referents.md` and `refusals.md` receive what leaves `SKILL.md`

**Depends on:** T1

**Tests:**
- `referents.md` carries the seven genre tiers, the craft-calibration statement,
  the not-a-source-for-explore statement, the per-entry classification, an era
  label on every model-era entry, the pointer to the shared quality floor, and
  the existing requirement to name which qualities of a reference are taken and
  which are left.
- `refusals.md` carries all seven existing anti-pattern entries; a diff of their
  obligation wording against the pre-change `SKILL.md` shows no weakening.

**Approach:** the two files are authored together because the split between them
is the decision — an entry naming a product goes to `referents.md`, an entry
naming a failure mode goes to `refusals.md`. Authoring them apart invites an
entry landing in both or neither.

**Done when:** both exist, the seven refusals are present, and every
`referents.md` entry carries one of the three classifications.

**Touches:** packs/experience-design/.apm/skills/creative-direction/references/referents.md, packs/experience-design/.apm/skills/creative-direction/references/refusals.md

### T6: The template carries the four new records

**Depends on:** T1

**Tests:**
- `experience-reviewer.md`'s grounded-aesthetic-fit lens and the template share
  the exact four-term set: `persona`, `precedent`, `standards`,
  `platform conventions` — one `grep -q` per term in each file.
- Frontmatter carries a `status` key; the three permitted values appear in the
  template's documenting prose, which is where an enum can live (a YAML field
  holds one value).
- A borrowed-discipline section exists.
- A refinement-amendment section exists.
- A compositional-commitments section exists.
- `grep -c '^| \*\*'` still returns `15`; `## Counterfactual check` still present;
  `type: creative-direction` still present.

**Done when:** all four new sections exist and the three pre-existing invariants
still hold.

**Touches:** packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md, packs/experience-design/.apm/agents/experience-reviewer.md

### T7: `SKILL.md` is the route rule, five operations and the output contract, under the ceiling

**Depends on:** T2, T3, T4, T5, T6

**Tests:**
- `body-bytes.sh` ≤ `6500`.
- The two declaration lines still `grep -c` to exactly `1` and are byte-identical
  to their pre-change form (`git diff` shows those lines unchanged).
- No unprefixed bare folder span.
- Zero numbered procedure steps remain.
- The route table names `inherit`, `extend`, `originate`.
- Five operations named; four link a reference; `frame` links its two plus
  `refusals.md`.
- No `docs/` citation anywhere in the file.
- Description ≤ 1024 chars and still names the three boundary skills.
- All five roster suites pass.

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
  referents from the audience's domain; D asserts only named axes moved.
- `eval_queries.json` parses and carries refinement-shaped positives and
  `design-system` / `design-review` negatives.

**Done when:** both files parse and carry the named cases.

**Touches:** packs/experience-design/.apm/skills/creative-direction/evals/evals.json, packs/experience-design/.apm/skills/creative-direction/evals/eval_queries.json

### T9: The guide describes the route rule and the five operations

**Depends on:** T7

**Tests:**
- `python3 -m pytest tests/roster/test_experience_design_guide_agreement.py -q` passes.
- The guide's `**Where it lands:**` path matches `SKILL.md`'s declared target.

**Done when:** the suite passes, the guide covers all five operations, and
manual-QA judgement 5 (guide sufficiency) is recorded — it is this output's
closeout condition in the spec, not a T11 afterthought.

**Touches:** guides/experience-design/how-to/establish-design-intent.md

### T10: The release is registered

**Depends on:** T7, T8, T9

**Tests:**
- Both source manifests read `2.0.10`; `marketplace.json` matches and was
  regenerated by `make build-self` rather than hand-edited (`git diff` shows it
  changed only in the generated region).
- The changelog entry is free-standing directly beneath `[Unreleased]`, carries
  one `Highlights` subsection, and every added heading has one blank line above
  and below.
- `agentbundle catalogue lint --root . --deep` and `verify --root .` exit 0.

**Done when:** all three version surfaces agree and both catalogue commands pass.

**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

### T11: The six manual-QA judgements are recorded

**Depends on:** T10

**Tests:**
- Six verdicts, each naming the judgement by number, the artifact it read, the
  reviewer, and the date:
  1 — the four eval cases against the pinned pre-change `SKILL.md`;
  2 — each operation's stability contract in `SKILL.md`;
  3 — the selection rubric in `SKILL.md`, read without opening a reference;
  4 — the era labelling in `references/referents.md`;
  5 — the guide (also T9's closeout);
  6 — the visual-precondition sweep across `SKILL.md` and `references/`.
- Judgement 1 names the pinned pre-change revision it ran the cases against.

**Approach:** last, because judgement 1 needs both sides — the post-change eval
cases from T8, and the pre-change `SKILL.md`, retrieved at the git revision T1
pinned rather than from the working tree, where T7 has replaced it.

**Done when:** the ledger records all six with names and dates.

**Touches:** docs/specs/creative-direction-modes/notes/verification-ledger.md

## Rollout

Single PR. No migration: the artifact path, its `type:`, and the fifteen axes are
unchanged, so an existing `direction/<slug>.md` stays valid and a consumer reading
it sees no difference. An adopter on `2.0.9` who upgrades gains operations and
loses no artifact.

No feature flag and no staged rollout — the unit of delivery is a markdown skill,
and a partial install is not a state the installer produces.

## Risks

- **The ceiling is tight.** Measured margin is roughly 900 bytes. If T7 cannot
  reach 6,500 without cutting a rule, the ceiling is the thing that moves, not the
  rule — and the criterion is amended through the controlled path rather than
  quietly missed.
- **A rule is lost in redistribution.** Ten steps and seven refusals move between
  files. T5 and T7's diff-based tests catch wording weakening; the six manual-QA
  judgements catch what a grep cannot.
- **The folder-span rule bites late.** A bare `` `references/` `` anywhere in T7's
  rewrite reds a registry suite in a cross-cutting test, not in T7's own. T7 lists
  it explicitly for that reason.

## Changelog

<!-- Approvals only. Drafting history does not belong here. -->