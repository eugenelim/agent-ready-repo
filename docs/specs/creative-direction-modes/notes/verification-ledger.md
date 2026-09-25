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

> **Attribution.** Each verdict below was reached by the agent session reading the
> named artifact, and reviewed and accepted by **eugenelim on 2026-09-25**. The
> reviewer column records who read; this line records who accepted. Both are kept
> because they are different acts, and recording only the second would misstate
> how the judgement was formed.


Seven judgements, each recorded with the reviewer's name and the date.
Judgement 7 is recorded as two rows, 7a and 7b, so seven judgements fill eight
rows.

| # | Judgement | Artifact read | Verdict | Reviewer | Date |
| --- | --- | --- | --- | --- | --- |
| 1 | The four behavioural eval cases distinguish old behaviour from new — A and D pass, B and C fail, run against the pre-change skill | `evals/evals.json` against `SKILL.md` at `9748dd256` | **Pass — the cases still discriminate.** Re-run against `SKILL.md` at `9748dd256` after case A's assertion was reworded. **A passes**: pre-change there is no route rule and no divergence generation, so no round runs and no candidates are produced. **B fails**: nothing names or excludes the category default. **C fails**: the genre tier directs referents to named software products. **D passes**: gate 2 and the re-deriving-taste refusal together give amend-not-replace. | agent session (controller), accepted by eugenelim | 2026-09-25 |
| 2 | Each operation's stability contract is complete and non-overlapping | `SKILL.md` for `frame`; `references/explore.md`, `visualize.md`, `converge.md`, `refine.md` for the other four | **Sufficient.** All five operations carry `May change:` and `Must remain stable:`, and `refine.md`'s contract names all five fixed things — ranked goals, dominant goal, grounding referents, signature device, every unnamed axis. The visualize/converge overlap noted in the first reading stands and is benign: `visualize` writes nothing and its commitments now reach the file through `converge`'s capture, which names them explicitly. | agent session (controller), accepted by eugenelim | 2026-09-25 |
| 3 | The operation-selection rubric is decidable without loading a reference | `SKILL.md`, read without opening any reference | **Sufficient.** Five bullets keyed on the shape of the request, every term defined in `SKILL.md`. Reaching an operation requires no reference load. | agent session (controller), accepted by eugenelim | 2026-09-25 |
| 4 | The anti-pattern reference's era labelling is honest — a dated observation is distinguished from a durable one | `references/referents.md` | **Honest.** 21 entries classified across all three tiers, 10 model-era entries each carrying the period they describe. The tier now also states where a declared genre comes from, so a reader can tell which genre applies rather than guessing. | agent session (controller), accepted by eugenelim | 2026-09-25 |
| 5 | The guide is sufficient | `guides/experience-design/how-to/establish-design-intent.md` | **Sufficient, re-taken after a correction.** The guide names all three routes and all five operations and a reader can act without opening `SKILL.md`. The first verdict was wrong and is superseded: it asserted the guide stated `visualize` correctly when the guide gated the whole operation on harness capability, telling a markdown-only adopter the operation does not run for them. The gate now falls on the rendered comp. That error sat outside every manual-QA surface, because judgement 6's sweep is scoped to `SKILL.md` and `references/`. | agent session (controller), accepted by eugenelim | 2026-09-25 |
| 6 | No sentence makes a visual artifact a precondition for writing the direction doc | `SKILL.md` and every file under `references/` | **Pass.** Swept `SKILL.md` and every file under `references/`. No sentence makes writing the direction doc conditional on producing a visual. `visualize.md` states the inverse: a text schematic is the default, and a rendered comp's absence is a named skip. | agent session (controller), accepted by eugenelim | 2026-09-25 |
| 7a | The four departing sections left `SKILL.md`, each with its method intact in the reference that now owns it and nothing paraphrased back into the body | post-change `SKILL.md` against `9748dd256` | **Pass, re-taken on the reachability test.** The earlier verdict asked whether every departing obligation had a home, and answered yes. That is the weaker question. Round three showed the genre tier's precedent directive surviving verbatim in `references/referents.md` while `converge`, which owns grounding, loaded neither the file nor the rule — present, and unreachable from the operation that needs it. `converge` now names it. Re-checked on the stronger test: each of the four departing sections is gone from `SKILL.md`, and each obligation is reachable from the operation whose route needs it, not merely present somewhere in the pack. Obligations were lost and restored in every pass over this prose, in three recurring shapes: a rule stated as an observation read as commentary and was cut; a rule moved into a file the relevant operation never loads became unreachable; and a correct edit to one surface left the surfaces that restate it unswept. No running count is given here, because the two this verdict previously carried were each wrong by the time they were read. None was visible to a contracted grep or to a 108-clause deontic inventory. | agent session (controller), accepted by eugenelim | 2026-09-25 |
| 7b | The three enumerations are exact and complete — three routes each with trigger and operations, five operations each with a one-line purpose, three representations | post-change `SKILL.md`, and `references/visualize.md` for the third | **Pass, re-taken against the shipped artifacts.** The earlier verdict was formed before commit `1c8c24948` rewrote the `originate` row and three paragraphs of `visualize.md`; it happened to survive, but it had not read what ships. Re-read now: the route table carries exactly three rows, each with a filled trigger and operations cell; `SKILL.md` names exactly five operations; `visualize.md` defines exactly three representations, each with its binding force and each reachable on a route that runs the operation. | agent session (controller), accepted by eugenelim | 2026-09-25 |

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

## Reviewer dispositions

| Reviewer | Disposition | Basis |
| --- | --- | --- |
| `adversarial-reviewer` | Ran, three post-gates rounds | 8, 6 and 1 findings sustained; all closed |
| `experience-reviewer` | Ran, one round | SHIP WITH CHANGES, 23 findings; in-scope correctness closed, the rest routed to Follow-ons at the owner's direction |
| `security-reviewer` | Not warranted | No security boundary, data flow or guarding control changes. The one candidate finding — `refine` amending without `containment.md`'s controls — was refuted: the spec states the `**Writes:**` / `**Confinement:**` contract has no other operative procedure, so a second containment procedure is what it forbids; `containment.md` is declared at skill level in the always-loaded body and covers amendment explicitly. The write declaration is byte-unchanged. |
| `quality-engineer` | Not warranted | No new module boundary, dependency, abstraction layer or top-level directory; no `operational-safety` module is reached; no human asked for the pass. |
| `frontend-reviewer` | Not warranted | No HTML, CSS or JS in the diff. |
| `design-reviewer` | Not warranted | No architect-pack integration activated it. |

