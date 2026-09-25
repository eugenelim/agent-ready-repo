# Verification ledger — creative-direction-modes

This file holds two things the spec contracts: the pre-change readings T1 takes
before any edit, and the seven manual-QA verdicts. A verdict is a named
reviewer's recorded judgement; it is the result, not evidence for one.

## Pre-change readings (T1)

Taken 2026-09-24, before any edit to the pack.

| Reading | Value | How it was taken |
| --- | --- | --- |
| `SKILL.md` authored body | **9,699 B** | The authored-body measurement in `plan.md`: file bytes minus frontmatter minus the managed `agentbundle:output-rendering` block, both delimiter comments included |
| Frontmatter `description` | **784 characters** | The description measurement in `plan.md`, scoped to the frontmatter block before the `description:` line |
| `**Writes:**` lines | **1** | `grep -c '^\*\*Writes:\*\* `' ` |
| `**Confinement:**` lines | **1** | `grep -c '^\*\*Confinement:\*\* `' ` |
| Skill directory | **73,274 B** across 14 files | `find "$S" -type f -exec cat {} + \| wc -c` |
| Five roster suites | **43 passed**, 0.62 s | The five suites the spec's Gates criterion names |
| `lint-experience-agnostic.py` | exit 0 | Whole-pack scan; takes no file argument |
| Pack version | **2.0.9** | `pack.toml` and `.claude-plugin/plugin.json` |

### Pinned revisions

| What | Revision | Why it is pinned |
| --- | --- | --- |
| `SKILL.md` pre-change | `9748dd256c555c3bb17b8ce42a948520bf787700` | T7 rewrites this file. After T7 the pre-change version exists nowhere in the working tree, and manual-QA judgement 1 must run the four eval cases against it. Retrieve with `git show 9748dd256:packs/experience-design/.apm/skills/creative-direction/SKILL.md`. |
| Delivery base | `b59becf264ac36399c62c2c93190338b38d70e0c` | `git merge-base origin/main HEAD`. The `DESIGN.md`-untouched check compares against this, not the working tree: a working-tree diff goes clean the moment an earlier task commits an edit. |

### Departing-section subtotals

Measured under the convention the context-footprint criterion owns — a section
runs from its `##` heading through its body's last newline, excluding the blank
line before the next heading.

| Section | Bytes |
| --- | ---: |
| `## Procedure` | 4,062 |
| `## Genre canonical reference tier` | 2,557 |
| `## Style presets` | 342 |
| `## Anti-patterns to refuse` | 1,165 |
| **Total departing** | **8,126** |

Gate 2 and its preamble's count word leave separately, a further 152 bytes net.

## Manual-QA verdicts

Seven judgements, each recorded with the reviewer's name and the date. None is
recorded yet; T9 writes verdict 5 and T11 writes the rest.

| # | Judgement | Artifact read | Verdict | Reviewer | Date |
| --- | --- | --- | --- | --- | --- |
| 1 | The four behavioural eval cases distinguish old behaviour from new — A and D pass, B and C fail, run against the pre-change skill | `evals/evals.json` against `SKILL.md` at `9748dd256` | — | — | — |
| 2 | Each operation's stability contract is complete and non-overlapping | `SKILL.md` for `frame`; `references/explore.md`, `visualize.md`, `converge.md`, `refine.md` for the other four | — | — | — |
| 3 | The operation-selection rubric is decidable without loading a reference | `SKILL.md`, read without opening any reference | — | — | — |
| 4 | The anti-pattern reference's era labelling is honest — a dated observation is distinguished from a durable one | `references/referents.md` | — | — | — |
| 5 | The guide is sufficient | `guides/experience-design/how-to/establish-design-intent.md` | Sufficient. The guide now names all three routes (`inherit`, `extend`, `originate`) with their triggers and operations, and all five operations (`frame`, `explore`, `visualize`, `converge`, `refine`) with their purposes, key behaviors, and write boundaries. A reader can determine which route applies to their situation and what each operation does — including that only `converge` writes a file and that `visualize` is a named skip on harnesses that cannot produce it — without opening `SKILL.md`. Craft details (referent derivation, divergence audit, containment) remain in the references as the progressive-disclosure model intends; a guide reader does not need those to understand the operational model. | eugenelim | 2026-09-24 |
| 6 | No sentence makes a visual artifact a precondition for writing the direction doc | `SKILL.md` and every file under `references/` | — | — | — |
| 7a | The four departing sections left `SKILL.md`, each with its method intact in the reference that now owns it and nothing paraphrased back into the body | post-change `SKILL.md` against `9748dd256` | — | — | — |
| 7b | The three enumerations are exact and complete — three routes each with trigger and operations, five operations each with a one-line purpose, three representations | post-change `SKILL.md`, and `references/visualize.md` for the third | — | — | — |

## Execution observations

**The directory ceiling is breached transiently, by the plan's own ordering.**
References land in wave 2 and `SKILL.md` shrinks in wave 3, so the directory
peaks after T6 — projected about 95,600 against a 95,000 ceiling — and falls to
about 91,300 once T7 lands. The criterion is a completion gate on the finished
delivery, not an invariant at every wave boundary, so this is expected rather
than a failure. Recorded here so a wave-2 gate reading is not mistaken for one.

**T3 passed all eleven of its greps while having lost four obligations.**
`converge.md` arrived at 4,878 bytes with every contracted string present and
greppable. Read against the procedure it redistributes, it had dropped: the
push-back remedy for an ungrounded goal ("ground it or push it back" became "is
still an opinion"); the rule that the first seven axes are structural and must
not be left at `[platform-default]`; the positional rule that a cell opens with
its tokens, which the divergence audit depends on because it compares tokens and
ignores prose; and the enumeration of what the captured doc is filled with,
including what would violate each goal. All four were restored, taking the file
to 5,409 bytes. This is the failure mode manual-QA judgement 7a exists for, and
the first evidence that a grep-based check cannot stand in for reading the moved
text against its source.

**T5 lost obligations too, and its own report said it had not.** `referents.md`
arrived with every contracted string greppable and a side-by-side showing six of
seven refusals carried verbatim. Read against the source, the genre tier's three
prohibitions were absent — do not copy the surface treatment, do not name any of
these as required implementation tools, do not reproduce their values — along
with the "study subjects, not prescriptive tools" framing that governs them. The
report described that removal as condensing "elaboration, not obligation". It
was three prohibitions.

Separately, refusal 7's parenthetical — Apple HIG, Material 3, MDN responsive —
was dropped on the stated ground that `Material 3` risks the agnosticism lint.
That rationale is false: the pre-change `SKILL.md` carries the parenthetical and
`tools/lint-experience-agnostic.py` exits 0 on the unmodified pack. Restored.

Two of two move tasks lost obligations while passing every grep. Judgement 7a is
the only check that reaches this class, and on this evidence it should be read
against the pinned revision sentence by sentence, not sampled.

**A sibling fold is being edited concurrently in this worktree.**
`docs/specs/xd-genre-router/spec.md` carries 184 insertions and 41 deletions
this delivery did not make — substantive work on that fold's own Testing
Strategy, its three-way `containment.md` copy reconciliation, and its Tier-A
activation grading. No task here touches `docs/specs/` outside
`creative-direction-modes/`, and every implementer was scoped to the skill
directory. Owner decision: leave the file untouched and stage this delivery by
explicit path rather than `git add -A`, so the two folds stay independent as the
spec requires. Recorded because a later reader seeing both in one branch would
otherwise read them as one change.
