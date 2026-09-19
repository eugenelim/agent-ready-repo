# Verification ledger — architect-design document-architecture gates

Execution observations. The spec holds the contract and the plan holds the
strategy; neither is edited to record what happened here. Every path below is
a placeholder (`<repo-root>`, `<tmp-root>`) rather than a real absolute path,
per AC-0043.

## T2 — the two typed CLI runs

Both runs invoke the shipped script directly, exactly as an adopter or a CI
step would:

```
python3
<repo-root>/packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py
--root <target> <file...>
```

### Run 1 — a non-compliant fixture

Fixture (`<tmp-root>/non-compliant.md`):

```markdown
# Non-compliant fixture

This paragraph exists to trip the paragraph budget. It has one sentence. It has
two sentences. It has three sentences. It has four sentences, which is one
over the budget of three.
```

Command:

```
python3
<repo-root>/packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py
\
  --root <tmp-root> <tmp-root>/non-compliant.md
```

stdout:

```
'<tmp-root>/non-compliant.md':3: DA3 — paragraph of 5 sentences (budget 3)
```

stderr: empty.

Exit code: **1** (one `DA3` finding, no refusal) — matches AC-0004.

### Run 2 — the shipped `assets/*.md` templates

Command:

```
python3
<repo-root>/packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py
\
  --root <repo-root> <repo-root>/packs/architect/.apm/skills/architect-design/assets/*.md
```

stdout:

```
'<repo-root>/packs/architect/.apm/skills/architect-design/assets/design-doc.md':25:
DA3 — paragraph of 4 sentences (budget 3)
```

stderr: empty.

Exit code: **1** (one `DA3` finding, no refusal). **No criterion asserts
against this run** — see *Disposition of `assets/design-doc.md:25`* below.
The finding is expected output, not a regression.

## Superseded — AC-0018 fails against real, already-shipped content

> **Superseded 2026-09-19.** This section describes AC-0018 as it stood
> before the amendment, when its clean corpus was `assets/*.md`. **AC-0018
> still exists** — it is repointed at
> `testdata/telemetry-endpoint-default-design.md`, and its clean half is
> verified in T4a. What was withdrawn is the corpus, not the criterion. So the
> argument below that `test_da3_reports_no_finding_in_any_shipped_asset`
> "asserts AC-0018 faithfully" and must not be weakened is **reversed**: the
> plan obliges T2 to delete that test, because the corpus it asserts is no
> longer AC-0018's. The two routes offered at the end of this section were not
> the route taken; a third was, recorded under *The placeholder rule was
> withdrawn* below. Read this section as the observation that started the
> amendment, not as current obligation. Its heading is false on both halves
> and is retained only so the anchor keeps resolving.

AC-0018 requires zero `DA3` findings across every `*.md` under
`architect-design/assets/`, "including … the `design-doc.md` compatibility
pointer: a prose paragraph is a prose paragraph whatever the document routes
to, so the glob carries no exclusion." Run 2 above shows one finding, on
`design-doc.md`'s `## Context` placeholder paragraph (line 25):

```
<The user-visible problem. The constraints — deadline, regulatory, team
shape, existing system shape. The system being changed, named by module
or service. At least one constraint should be non-obvious.>
```

Read as prose this is four declarative sentences (three internal `. ` +
capital-letter boundaries, plus the final clause), one over the budget. This
content predates this branch — `git log` shows it was last touched in
`0c4768314` ("author designs from three scope-routed model-first templates"),
unrelated to this spec — and it sits outside T2's `Touches:`, which lists no
`assets/*.md` file. No task in `plan.md` touches `assets/design-doc.md`
anywhere.

`test_gate_script.py::test_da3_reports_no_finding_in_any_shipped_asset`
asserts AC-0018 faithfully (a real glob over the real assets, the same
algorithm the script itself runs) and reds on exactly this one case; 86 of
the file's 87 cases are green. This is not a parser false positive — the
manual sentence count above agrees with the script — so weakening the
assertion would hide a real gap rather than close it.

A minimal, non-semantic fix exists (splitting the paragraph's four sentences
into two, e.g. merging "The user-visible problem." with the following clause
and "The system being changed…" with the final clause) but was not applied:
`assets/design-doc.md` is outside T2's pinned `Touches:`, and the implementer
brief did not authorize the bundled-fixes carve-out. This is recorded here as
a plan/reality gap for a controlled amendment — either widening T2's
`Touches:` to include the one-paragraph fix, or a follow-on task — rather than
resolved unilaterally.

## Owner decision — amend AC-0019 rather than edit the asset

This section is the in-flight amendment's **`reason_ref`**, which `state.json`
records as a working-tree path, so it resolves to the text below and tells the
current truth.

Its **`owner_authority_ref` is different and cannot be corrected**:
`state.json` pins it to `git:61a5db98f#owner-decision-amend-ac-0019`, and that
revision carries the pre-correction text — it authorises adding the
placeholder exclusion, rests on the false `AC-0024` claim, and says nothing
about the reversal. An auditor following the recorded authority lands on
approval for a change this delivery no longer makes. The authority for what
the amendment actually delivers is the 2026-09-19 reversal recorded below;
re-issuing the transition with corrected references is refused by the
procedure, which rejects a second amendment carrying changed authority facts.

**First decision, recorded 2026-09-19 at `61a5db98f`.** T2 reported AC-0018
red on `assets/design-doc.md:25`, a `<…>` placeholder holding four
sentences. The
owner authorised a controlled amendment adding a placeholder exclusion to
AC-0019, over the alternative of editing that one asset. The justification
that survives scrutiny is recurrence: splitting the placeholder would green
the suite while leaving `DA3` judging template instructions, so the next
four-sentence instruction reds again.

A second reason recorded at the time was false — that "AC-0024 already strips
every `<…>` placeholder when `DA10` counts words". It does not. AC-0023 is
`DA10`'s counting rule and removes YAML frontmatter and HTML-comment spans
only; AC-0024's strip belongs to the one-off command that measured the
752-word scaffolding figure. The owner approved on a framing that carried that
false claim.

**Reversed later the same day.** Two placeholder-span rules were
drafted and both failed review, the second introducing a silent under-count.
The owner then chose to withdraw the rule entirely and change `DA3`'s clean
corpus instead. That is what the in-flight amendment now delivers, and it is
recorded in full under *The placeholder rule was withdrawn* below. The
exclusion this section originally authorised is **not** in the contract;
AC-0019 carries its pre-amendment list.

**Disposition of `assets/design-doc.md:25`.** The paragraph stays as it is. It
is still detected — the script reports it, and the shipped-templates CLI run
that `spec.md` keeps as a standing manual-QA artifact reproduces it at exit 1.
What changed is that no criterion asserts against it: the templates are no
longer `DA3`'s clean corpus. The recorded exit-1 run is therefore expected
output, not a regression. It needs no follow-on: a placeholder holding four
sentences
is a template instructing its author, which is what a template is for. The
plan/reality gap this ledger opened for it is closed by that, not left waiting
on a trigger that no longer fires.

## The placeholder rule was withdrawn; the corpus was the defect

2026-09-19. Two placeholder-span rules were drafted and both failed review. A
same-line span missed `assets/design-doc.md:25`, the very case it was written
for, because that placeholder opens on one line and closes two lines later. A
joined-paragraph span fixed that and introduced a silent under-count:
`Keep p95 <200ms. Throughput must exceed >1k rps. Third. Fourth.` masks from
`<200ms.` through `>` and counts three sentences, so a four-sentence paragraph
passes the budget. `<` followed by a digit is ordinary comparison prose.

**Retracted measurement.** A table recorded here after the second attempt
reported zero `DA3` findings across the shipped assets and three counted
negative cases. It was produced by a reimplementation run in a shell, not by
`check_document_architecture.py`, which carries no placeholder handling and is
unchanged since `b5c957cb9`. It measured something adjacent to the system and
was reported as measuring the system. The table is withdrawn rather than
reproduced, because the rule it described is withdrawn too.

**What the owner decided instead.** `DA3`'s clean corpus stops being
`assets/*.md` and becomes the authored reference document T4a creates. A
template is a skeleton whose placeholders are instructions to its author, so a
finished-document check run against one measures the placeholders — the same
reason AC-0047 already keeps `assets/*.md` out of the precheck corpus. With an
authored corpus there are no placeholders, so AC-0081, AC-0082 and AC-0083 are
removed and the under-count path does not exist. The clean half of AC-0018
moves from T2 to T4a, which is the task that creates the document.

## Owner decision — a task to carry the prechecks into the reviewer's two homes

> **Superseded 2026-09-19.** The decision in force is the section titled
> *Owner decision — the prechecks hold in the authoring rubric alone*: the prechecks bind to the authoring rubric only and T4b is withdrawn.
> An intermediate position sits between this section and that one; skip it.
> The pending amendment's `reason_ref` points here, which is why this banner
> names the final decision directly rather than the next one.

2026-09-19. T4 reported, correctly, that the contract and the plan disagree,
and did not widen its own scope to paper over it.

**The gap.** The prechecks group's preamble binds every criterion in it to all
three rubric homes, and no task writes two of them — an obligation with no
owner. Measured by
`grep -o precheck` (case-sensitive, counting occurrences not lines), the word
appears 15 times in `design-doc-rubric.md`, zero times in
`architect-review/references/rubric-design-doc.md`, and once in
`design-reviewer.md`; no `#### DA6` body exists in either of the latter two.

> **Erratum, 2026-09-19.** This paragraph first gave the
> `design-doc-rubric.md` figure as 19, which reproduces under no counting
> rule: the file holds 15 case-sensitive occurrences and 20 case-insensitive
> (15 `precheck` plus 5 `Precheck`). The corrected figure and its counting
> rule are above. The zero and the one reproduce as stated, so the gap this
> paragraph establishes is unchanged — only the supporting figure was wrong.
>
> **Second erratum, same date.** This paragraph also gave the preamble's
> reason as the two reviewer homes being "unable to tell a hybrid from
> judgment-only `DA5`". That is false. AC-0034 requires `DA5`'s
> judgement-alone sentence in all three homes and T4 shipped it:
> `design-doc-rubric.md:224`, `rubric-design-doc.md:183` and
> `design-reviewer.md:142` each carry it verbatim. The distinction holds in
> every home. The gap is ownership — criteria bound to homes no task writes —
> and the sentence above now states it that way.

**Why no task can close it.** The plan assigns AC-0035 through AC-0042 to T3,
whose `Touches:` reaches `design-doc-rubric.md` alone. T4 owns the other two
homes and was never given those criteria. An obligation spanning three files
has one owning task that touches one of them. That is a plan error execution
falsified, which is the controlled-amendment path.

**What the owner chose.** Amend, adding a new task that carries the seven
precheck bodies into the reviewing rubric and the agent, over the alternative
of narrowing the obligation to the authoring rubric. Narrowing would be
cheaper to implement and would discard the reason the preamble gives: the
reviewer's two homes would keep the 🧭 tag with nothing behind it.

Completed task sections cannot be edited, so this is a new dependency-ordered
task rather than a widening of T4.

## Owner decision — `design-reviewer.md` is not a precheck carrier

> **Superseded 2026-09-19** by *Owner decision — the prechecks hold in the
> authoring rubric alone* below, which unbinds the reviewer-side home
> entirely and withdraws T4b. This section's narrowing of T4b to one reviewer
> home was an intermediate position; the later section is the decision in
> force.

**Date:** 2026-09-19

**Question.** T4b was opened to carry the seven precheck bodies into both
homes a reviewer reads. Review of the amendment found that doing so
contradicts a frozen criterion, so the owner was asked which homes T4b writes.

**Correction, before the decision.** This section first recorded the conflict
as AC-0054 requiring the agent to read the rubric *"for the fuller per-gate
text and prechecks"*, and the agent's file as frozen. Both were wrong.
AC-0054 (`spec.md`, the AC-0054 line) contains the word "precheck" zero times; it says
"for the fuller per-gate text". The phrase "and prechecks" is in the shipped
file alone (`design-reviewer.md:148`). And only T4's *plan section* is
hash-pinned — the agent file is editable by a later task, which is why T4b's
original `Touches:` could name it. The owner was re-asked on the corrected
facts and kept the same scope; what follows is the ground that survives.

**The conflict.** AC-0054 has the agent hold the gate set at baseline depth
and point at `architect-review/references/rubric-design-doc.md` for the
fuller per-gate text. Its degradation design already gives the agent a route
to precheck depth without carrying it, so a condensed second copy in the
agent would duplicate what the pointer reaches.

**Why the preamble was amended rather than reinterpreted.** A ledger note
cannot narrow a contract, so the preamble itself was amended in this
amendment. It needed amending on its own evidence: AC-0036 and AC-0037 say in
their own text that `DA7` and `DA8` carry their identifier, severity and tag
on *the authoring rubric's* existing checklist item, so two criteria inside
the group cannot hold in three homes by their own wording. The reviewing
rubric's corresponding items carry no identifier, severity or tag, so copying
those two bodies across would assert something untrue. Five prechecks cross,
not seven.

**Why nothing is lost.** Not because the agent carries `DA5`'s
judgement-alone sentence — the reviewing rubric carries it too, under
AC-0034, so that argument would equally dissolve T4b's remaining home and
proves too much. What the agent keeps is its AC-0054 pointer: a reviewer
needing precheck depth reads the reviewing rubric, which is exactly where T4b
puts it. The agent degrades in depth, never to nothing, which is the
behaviour AC-0054 specifies.

**Decision.** T4b writes `rubric-design-doc.md` only. `design-reviewer.md` is
left final at T4 and its AC-0054 pointer stays true.

**Schedule consequence.** T4a depended on T4b solely because AC-0059
dispatches `design-reviewer.md` and that file was in T4b's `Touches:`. With
the agent out of T4b's scope, T4a depends on T4 instead. T4b and T4a then
share no file and schedule into one wave, leaving two waves to run:
`[T4b, T4a]` then `[T7]`.

## Owner decision — the prechecks hold in the authoring rubric alone

**Date:** 2026-09-19

**What was decided.** The prechecks bind to
`architect-design/references/design-doc-rubric.md` only. The group's preamble
is replaced by an explicit per-criterion home table, and **T4b is withdrawn**.
Remaining tasks: T4a, then T7.

**Why the preamble was replaced rather than patched again.** Three review
rounds produced 6, then 8, then 12 findings — diverging, not converging — and
the blockers in each round were one defect: the preamble stated a universal
over sixteen heterogeneous criteria and patched it with exceptions. The group
mixes rubric text, testdata files and recorded manual walks, so every rule
general enough to cover all three was wrong about some of them, and each
exception added created a fresh set the universal now wrongly covered. Round
3 showed the amended rule still binding AC-0044 through AC-0046 and AC-0049
through AC-0051 to a rubric home, and still unable to derive the scopes it
asserted for AC-0042 and AC-0048, which name no home at all. A table states
each home instead of deriving it, so there is no universal left to be wrong.

**Why the reviewer homes are unbound.** The reason first recorded for binding
them was that a reviewer could not otherwise tell a hybrid from judgment-only
`DA5`. That was false — AC-0034 puts `DA5`'s judgement-alone sentence in all
three homes and T4 shipped it. The replacement reason offered, that an
unowned obligation needs an owner, does not support a binding either:
unowned-ness follows from the binding, and is discharged just as well by
unbinding, which is what this decision does. The substantive ground is that a
precheck is a narrowing hint for whoever reads a document closely first,
which is the author; a reviewer needs each gate's identifier, severity, tag
and question to return a verdict, and both reviewer homes already carry those.

**What this costs.** No shipped file is edited, but one shipped sentence
becomes permanently false, so the cost is not zero.

`packs/architect/.apm/agents/design-reviewer.md:148` tells a reviewer to read
`architect-review/references/rubric-design-doc.md` "for the fuller per-gate
text and prechecks". Measured today, that rubric carries zero occurrences of
`precheck` and no per-gate bodies at all — its gate section is the same table
and the same `DA5` sentence the agent already holds, plus an intro paragraph.
So the pointer was already false on both halves when T4 shipped it, and this
decision removes the only route by which it would have become true.

Nothing reds. AC-0054 requires only that the agent *state* it reads that
rubric for fuller per-gate text; no criterion and no test checks that the
target holds any. That is the defect class — a pointer whose target is never
verified — and it is why the falsity survived a passing gate chain.

This is out of the contract's scope rather than free: the contract requires
the pointer, not the target's depth, and no remaining task owns the agent
file. It is recorded below and in the spec's `## Follow-ons`, to land after T7. T3's authoring-rubric prechecks stand and the reviewer homes keep T4's
gate table; the withdrawn work is T4b alone, which had not started.

## Follow-on — the agent's degradation pointer promises depth that is not there

**Found:** 2026-09-19, verifying the T4b withdrawal.

`design-reviewer.md:148` promises "fuller per-gate text and prechecks" in
`rubric-design-doc.md`. That rubric has neither, and under the decision above
it never will. A reviewer who follows the pointer at baseline depth finds
nothing more than the agent already gave them.

Two repairs are open, and the choice is the owner's: correct the agent's
sentence to promise only what the reviewing rubric holds, or give the
reviewing rubric the per-gate depth the sentence claims. The first is
consistent with the decision above; the second reopens what that decision
closed.

Whichever is chosen also needs AC-0054 revisited, because AC-0054 is what
requires the pointer, and it pins the agent's statement without pinning the
target. A criterion that requires a claim about another file should reach
that file.

This is unbounded by the spec/plan contract and does not block T4a or T7.

## T4a — the prechecks walked against a document, not a template

Two files are committed at `testdata/`:
`telemetry-endpoint-default-design.md` (the reference corpus, AC-0045) and
`precheck-defects.md` (the planted-defect variant, AC-0049). Both are
authored from `assets/subsystem-design.md` and describe the layer-5
enterprise-telemetry-endpoint-default subsystem
`docs/product/intents/catalogue-level-telemetry-endpoint-default.md` frames.

**Reference document, measured.** `check_document_architecture.py`'s own
`count_words`, loaded the same way `test_gate_text.py` and
`test_gate_script.py` both load it:

```
word count: 2096
ratio vs the 2,178-word density figure: 0.9624   (AC-0025's 20% window: 0.80–1.20)
DA3 over-budget paragraphs: none
evaluate_target(...) findings: []
```

Zero `DA3` findings and zero `DA10` findings (2,096 words is well under the
3,300-word bound), satisfying AC-0018. The word count sits inside the 20%
window, satisfying AC-0025.

**Defect document, diffed against the reference document.** `diff -u` between
the two files shows exactly eight hunks: the leading HTML-comment header
(swapped from the corpus-baseline note to the deliberately-non-conforming
declaration — framing, not a planted defect) and one hunk per precheck —
`DA1`, `DA2`, `DA4`, `DA6`, `DA7`, `DA8`, `DA9`. No other line differs. This
is the reading of AC-0049's "exactly those seven edits and nothing else"
this task adopted: the seven content edits are the defects; the header is
metadata that necessarily differs because the two files serve opposite
purposes, and AC-0049 itself requires the defect document to "state in its
own body that it is deliberately non-conforming" — that statement has to
live somewhere, and the header is where the reference document's own
AC-0044 note already lives.

### AC-0046 — no precheck fires on the reference document (walked by hand)

| Precheck | Mechanism used to walk it | Fires? |
| --- | --- | --- |
| `DA1` (future-tense/prior-state) | Scanned the body for `will be`, `previously`, `used to`, and any deprecation date | No |
| `DA2` (unnamed cross-reference) | Scanned the body for the eight closed-list phrases | No |
| `DA4` (model before prose) | Read the first block after each modelled section's opening question | Every section's first block is `<!-- model -->`; no |
| `DA6` (Revision History / Decision Log) | Scanned headings | No such heading | No |
| `DA7` (diagram states one question, one zoom) | Read every diagram: section 1 and 2's rationale each name the diagram's question and zoom in prose beside it; both section 3 sequence diagrams carry `Question:`/`Zoom:` in their `Note` line | No |
| `DA8` (mapping row resolves to a modelled element) | Compared Implementation Mapping's three "Semantic element" values against Structural Model's three element names | All three match | No |
| `DA9` (evidence-accumulating heading) | Scanned headings for `Appendix`, `References`, `Evidence` | No such heading | No |

Command used for the mechanical half (DA1/DA2/DA6/DA9 token scans, and the
DA8 name comparison):

```
python3 - <<'PY'
from pathlib import Path
import re
text = Path("<repo-root>/packs/architect/tests/skills/architect-design/testdata/telemetry-endpoint-default-design.md").read_text(encoding="utf-8")
# token scans against each precheck's closed list; see test_gate_text.py's
# own DA1/DA2/DA6/DA9 token lists for the exact strings used
PY
```

stdout for that scan: no token from any of the four closed lists is present.
`DA4` and `DA7` were walked by reading the document's structure directly
(the first block after each opening question; the presence of a stated
question and zoom beside every diagram), because neither is a fixed-string
scan.

### AC-0051 — every precheck fires on the planted defect (walked by hand)

| Precheck | Location of the planted defect | Fires? |
| --- | --- | --- |
| `DA1` | Section 1 rationale: `already-shipped` → `previously-shipped` | Yes — `previously` present |
| `DA2` | Section 6 rationale: `in section 2` → `as described above` | Yes — `as described above` present, names no target |
| `DA4` | Section 2: a prose sentence ("The subsystem is composed of three cooperating elements.") inserted between the opening question and `<!-- model -->` | Yes — first block after the question is prose, not the model |
| `DA6` | `## Revision History` heading added near the end of the body | Yes — heading present |
| `DA7` | Section 3's first sequence diagram: the `Note` line's `· Question: ... · Zoom: component` clause removed | Yes — that diagram states no question or zoom |
| `DA8` | Implementation Mapping row renamed `Merge Projector` → `Config Merge Service`, which section 2's Structural Model does not name | Yes — the row resolves to no modelled element |
| `DA9` | `## Evidence` heading added at the end of the body | Yes — heading present |

Same scan command as above, run against `precheck-defects.md` instead:
`DA1`, `DA2`, `DA6` and `DA9`'s tokens are each present exactly once; `DA4`'s
structural check finds prose before the model in section 2 only; `DA7`'s
diagram-by-diagram read finds the first sequence diagram's `Note` line
carries no `Question:`/`Zoom:` clause; `DA8`'s name comparison finds
`Config Merge Service` absent from the three Structural Model names.

### AC-0043 — host-cleanliness over this task's diff

Command:

```
git diff --name-only origin/main...HEAD | while read -r f; do
  [ -f "$f" ] && grep -nE '/Users/|/home/[a-z]|/Volumes/' "$f"
done
```

Every hit returned belongs to a file outside this task's `Touches:` (other
specs' verification ledgers and evidence JSON already scrubbed to the
`<user>` placeholder convention, and `spec.md`'s own restatement of the
grep pattern). Both files this task adds —
`testdata/telemetry-endpoint-default-design.md` and
`testdata/precheck-defects.md` — return zero hits, and this file (the
ledger entry above this line) uses `<repo-root>` throughout rather than a
real path.

### AC-0050 — the defect document's placement relative to the repository-wide sweep

Recorded per `plan.md`'s T4a `Tests:`: the choice is the first branch,
unwidened. `tools/lint-agents-md.py:94-95`'s `_is_fixture` excludes a path
only when **both** `fixtures` and `tests` appear in its `Path.parts`.
`testdata/precheck-defects.md`'s parts are `("packs", "architect", "tests",
"skills", "architect-design", "testdata", "precheck-defects.md")` — it
carries `tests` but not `fixtures`, so `_is_fixture` returns `False` and the
file is not excluded from that sweep's `rglob("*.md")` walk. The collision
stays latent, exactly as the plan predicted, because the sweep this
predicate feeds (10g, the risk-trigger marker check) looks for the literal
`<!-- risk-triggers:start` marker, which no planted defect in this file
carries. No file under `tools/` is touched by this task, and the predicate
is not widened — the alternative the criterion offers is recorded here, not
taken, because widening `_is_fixture` to match `testdata/` would be a
change to a shared repository-wide lint on a task whose `Touches:` names no
`tools/` file.

### AC-0059 — the design-reviewer copy/removal, dispatch left to the controller

This implementer session is itself a subagent and cannot dispatch another
subagent (`design-reviewer`), so the roll-call dispatch this criterion asks
for is **not** performed here. What follows is the copy/removal mechanics
the criterion also pins, exercised and recorded so the controller's own
dispatch has a verified starting state to run against, and so a record
naming only a path and a hash does not stand in for the post-state:

1. **Pre-state.** `.claude/agents/design-reviewer.md` did not exist before
   this step (`ls` exited non-zero). The destination was therefore not
   refused — the refusal branch AC-0059 requires when the destination
   already exists was not exercised on this run, because nothing was there
   to refuse.
2. **Copy.** `packs/architect/.apm/agents/design-reviewer.md` was copied to
   `.claude/agents/design-reviewer.md`, inside the repository working tree
   and nowhere else — never to `~/.claude/agents/`. Both files are 12,287
   bytes and share the SHA-256 digest
   `d2335bb7d2ba1cdb1493f1bbac11d25f4ecdd7a462b3f3b902d271acf5c7598b`.
3. **No dispatch.** No `design-reviewer` invocation happened in this
   session. The reference document was not reviewed, and no returned block
   exists to record.
4. **Removal.** The copy was deleted immediately after step 2, in the same
   step and before any dispatch was attempted. `ls
   .claude/agents/design-reviewer.md` exits non-zero afterward, and `git
   status --short .claude/` shows no change — `.claude/agents/` is back to
   its pre-step content, matching `tests/roster/test_core_agent_projection.py:60-61`'s
   equality pin.

**What remains for the controller.** Repeat the copy (refusing if the
destination already exists), dispatch `design-reviewer` against
`testdata/telemetry-endpoint-default-design.md`, record the returned block
here showing ten `DA1`-`DA10` verdicts, and remove the copy in the same
step regardless of outcome. Until that dispatch is recorded, T4a's `Done
when:` clause requiring "the dispatched review's returned block in the
ledger showing ten verdicts" is open.

## AC-0059 — the design-reviewer dispatch, and what two roll-calls found

**Date:** 2026-09-19. Controller-run, because an implementer subagent cannot
spawn another subagent; T4a's implementer performed the copy/removal mechanics
and correctly declined to fabricate a returned block.

**The copy, both times.** `packs/architect/.apm/agents/design-reviewer.md` was
copied to `.claude/agents/design-reviewer.md` inside the working tree and
nowhere else, byte-identical at SHA-256 `d2335bb7d2ba1cdb…`. The destination
was checked absent before each copy and the write refused otherwise. After
each dispatch the copy was removed; `git status --short .claude/` is empty and
`tests/roster/test_core_agent_projection.py` passes (1 passed in 2.02s), which
is the equality pin on that generated tracked space. No copy survives.
`~/.claude/agents/design-reviewer.md` was never written.

**Which body was served.** AC-0059 warns that without a copy the dispatch
reads the operator profile's definition. A discriminator was fixed before
dispatching: the pack body names `DA10` three times, the profile body zero.
Both returned blocks carried a full ten-gate roll-call, so the branch's body
was served both times and the agent-definition staleness risk did not
materialise. Note that AC-0059's byte figures are stale — the pack source is
12,287 bytes, not 9,140, having grown with T3's and T4's gate content; the
profile copy is 8,633 as recorded. The criterion's point stands; its numbers
do not.

**Roll-call 1 (pre-fix).** Verdict MAJOR REWRITE. `DA1`, `DA2`, `DA3`, `DA4`,
`DA6`, `DA9`, `DA10` PASS; `DA5`, `DA7`, `DA8` FAIL. `DA7` fired because the
two flowcharts stated no question or zoom while the section rationale asserted
they did — the obligation satisfied in the prose instead of the diagram.

**Roll-call 2 (at `b5557ff83`, after the first fix).** Verdict MAJOR REWRITE.
`DA1`, `DA3`, `DA4`, `DA6`, `DA9`, `DA10` PASS; `DA2`, `DA5`, `DA7`, `DA8`
FAIL. `DA7` fired again, and the reason is worth keeping: the first fix put
the question in a mermaid `%%` comment, which is stripped at render, so a
reader of the rendered diagram still saw nothing. The document already held
the pattern that works — `Note over` in the sequence diagrams renders.

**Second fix and manual re-walk (AC-0046).** Both flowcharts now open with a
mermaid `---` / `title:` block, which renders above the diagram, carrying the
question and the zoom; the ad-hoc third zoom term was dropped so the labels
use the Zoom column's vocabulary. Walked by reading, all four diagrams: two
rendered titles, two rendering `Note over` labels, zero `%% Question` lines
remaining. `DA7`'s precheck no longer fires.

**Why the other FAILs do not breach AC-0046.** AC-0046 forbids a *precheck*
firing, not a judgement verdict. `DA5` is judgment-only and carries no
precheck. `DA8`'s precheck asks only that every implementation-mapping row
resolve to an element the models name, which the reviewer confirmed holds —
its FAIL is a sufficiency judgement. `DA2`'s precheck is a closed list of
phrases; the reviewer's `DA2` FAIL is about an unnamed intent
("this design's owning intent"), which is not on that list, so the precheck
does not fire. Only `DA7` was a precheck firing, and it is fixed.

**One finding refuted on the contract.** Roll-call 2's Major 6 objects to the
reference document's opening HTML comment as corpus governance that does not
belong in a design body, citing a repository-internal ledger path. AC-0044
*requires* that header: the corpus obligation must live in the document
because a pack test may not climb to `docs/`
(`tools/lint-pack-test-boundary.py` check 8), and a criterion verified by
asserting that the spec says something is its own comparison value. The
`packs/AGENTS.md` prohibition the finding echoes governs shipped pack content
under `.apm/`; `tests/skills/.../testdata/` is not projected. Refuted, not
deferred.

**The design's own quality is not this delivery's subject.** Both roll-calls
returned MAJOR REWRITE with blockers against the telemetry subsystem design
itself — an excluded mechanism, two incompatible write targets, an
unvalidated egress endpoint, absent consent. Those are findings about a
corpus document written to exercise the gates, not about the gates. No
criterion requires the reference document to be a *good* design; AC-0045
requires it filled and placeholder-free, AC-0046 requires no precheck to fire
on it. Both hold. Recorded here so a later reader does not mistake the silence
for an oversight.

## Resolved — the agent's degradation pointer now promises only what the rubric holds

**Date:** 2026-09-19. Closes the "Follow-on — the agent's degradation pointer
promises depth that is not there" section above, chosen from its own two open
repairs: correct the agent's sentence rather than reopen the withdrawn T4b
depth.

`design-reviewer.md:148` read "for the fuller per-gate text and prechecks";
the words "and prechecks" are deleted, leaving "for the fuller per-gate
text" — exactly what `rubric-design-doc.md` holds, measured in the section
above at zero `precheck` occurrences and no per-gate bodies. AC-0054 requires
only the pointer's existence, not the target's depth, and the pointer still
names `rubric-design-doc.md` for the fuller per-gate text, so AC-0054 still
holds after the edit.

A delivery review of the finished slice raised this and eight other findings
in the same pass (escaped-refusal injection, the DA3 sentence-boundary
undercount, the `--root .` CLI join, the AC-0070 closed-set eval assertion,
a misdirected script path in `rubric-design-doc.md`, the file-wide DA5 parity
assertions, and a changelog overclaim). Each is fixed on
`eugenelim/architect-slice-2`; this entry records only the one this ledger
was already tracking as an open follow-on.

## Owner decision — amend three criteria whose stated oracles the tree refutes

**Date:** 2026-09-19. Raised by the delivery review at the CODE-REVIEW gate.

**What was wrong.** Three criteria state a number or a procedure that does not
hold. In each case the criterion's *substance* holds and only its stated
oracle is wrong, which is the worst shape: the criterion reads as verified and
cannot be.

- **AC-0024.** Its reproduction — strip frontmatter, strip HTML-comment spans,
  replace every `<…>` placeholder with a space, count `[A-Za-z0-9]` tokens —
  yields **388**, not the 752 it records. Measured on this tree: 752 appears
  only when `<…>` is read as *not* spanning a newline (`<[^<>\n]*>`), and that
  decisive detail, worth 364 words, is the one the criterion never states.
  Its stated rationale is separately false: it claims substituting the empty
  string "joins its neighbours and gives a different figure", but space and
  empty both give **752** under the single-line reading, so the note explains
  nothing.
- **AC-0043.** Its scan returns **19** hits over this delivery's diff. Every
  one is either the pattern quoting itself or a path already scrubbed to the
  `<user>` placeholder — that is, the oracle matches its own remedy. No real
  account name is present, so the substance holds and the check cannot show it.
- **AC-0059.** It cites the pack source at 9,140 bytes; the file is **12,287**,
  having grown with T3's and T4's gate content.

**Decision.** Amend all three so each states something true and re-derivable,
rather than defer them or tick them on an erratum. The reasoning is that the
spec is the durable artifact and the ledger is the one that stops being read
once the spec ships, so a false statement left in the criteria tier outlives
any note about it. A deferral token would have the same effect, because it
marks the criterion unmet without correcting what it says.

**The replacements, each measured before being written.**

- AC-0024 carries a runnable command that actually yields 752, with the
  single-line placeholder reading stated explicitly, and the false
  empty-vs-space rationale removed.
- AC-0043's scan becomes `/(Users|home)/[A-Za-z0-9._-]+/|/Volumes/[A-Za-z0-9._-]+`,
  which requires a real name segment. Proven differentially: it returns
  nothing over this delivery's diff, and a throwaway file written outside the
  tracked tree, carrying a home path with a real name segment, still matches.
  The probe is kept out of the repository deliberately — written into a
  tracked file it becomes the hit it exists to rule out, which is how the
  first attempt at this criterion failed review.
- AC-0059 drops its byte figures. A criterion that pins a file's size goes
  stale whenever that file is edited, which is what happened here; the point
  it makes — the operator profile's copy is a different, smaller definition —
  does not need a number.

**Scope note on the release.** Three shipped `.apm/` files changed after the
`0.15.12` version bump, which would normally mean one version string naming
two code states. It does not here: the branch has no upstream, so `0.15.12`
has never left it, and the fixes fold into that version rather than needing
`0.15.13`. `FORCE=1 make build-self` was re-run and the adapter projections
are current.

## Erratum — four ledger figures the tree no longer produces

**Date:** 2026-09-19, from the closing review.

- The reference document's recorded word count of 2,096 (ratio 0.9624) was
  taken at `4c913e5cd`; the document grew at `eaf90c258` and `count_words`
  now gives **2,113**, ratio **0.970**. AC-0025 holds at either figure — both
  sit well inside the 0.80–1.20 window — but the recorded number is the one
  the tree stopped producing.
- The reference-versus-defect diff is recorded as eight hunks. It shows
  **seven**: the `DA6` and `DA9` defects are both appended at the file end
  and land in one hunk. AC-0049's substance is unchanged — eight logical
  edits, nothing else differs — but the hunk count is not the observable it
  was written as.
- The AC-0046 walk table's `DA7` row describes the question and zoom as
  living "in prose beside" the diagram. `b5557ff83` removed that prose and
  `eaf90c258` moved it into a mermaid `title:` block. The superseding
  re-walk is recorded above; the table row describes a document state that
  no longer exists.
- The note correcting AC-0059's byte figures now reads against a criterion
  that carries none, the amendment having removed them.

Recorded rather than silently corrected, because a figure that moved is
evidence about how the delivery ran.

## Superseded — the first AC-0043 record

The earlier AC-0043 section runs the retired loose pattern
`'/Users/|/home/[a-z]|/Volumes/'` and explains its hits away by `Touches:`
scope. Both the pattern and that reasoning are replaced by the amended
criterion and the record above. Read the later one.
