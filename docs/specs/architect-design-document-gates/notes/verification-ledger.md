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

> **Superseded 2026-09-19** by *Owner decision — `design-reviewer.md` is not a
> precheck carrier* below, which narrows T4b to one reviewer home. The pending
> amendment's `reason_ref` points here; read both sections together, and take
> the scope from the later one.

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

**Date:** 2026-09-19

**Question.** T4b was opened to carry the seven precheck bodies into both
homes a reviewer reads. Review of the amendment found that doing so
contradicts a frozen criterion, so the owner was asked which homes T4b writes.

**Correction, before the decision.** This section first recorded the conflict
as AC-0054 requiring the agent to read the rubric *"for the fuller per-gate
text and prechecks"*, and the agent's file as frozen. Both were wrong.
AC-0054 (`spec.md:537-541`) contains the word "precheck" zero times; it says
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
