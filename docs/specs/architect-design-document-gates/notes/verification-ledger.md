# Verification ledger — architect-design document-architecture gates

Execution observations. The spec holds the contract and the plan holds the
strategy; neither is edited to record what happened here. Every path below is
a placeholder (`<repo-root>`, `<tmp-root>`) rather than a real absolute path,
per AC-0043.

## T2 — the two typed CLI runs

Both runs invoke the shipped script directly, exactly as an adopter or a CI
step would:

```
python3 <repo-root>/packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py --root <target> <file...>
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
python3 <repo-root>/packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py \
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
python3 <repo-root>/packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py \
  --root <repo-root> <repo-root>/packs/architect/.apm/skills/architect-design/assets/*.md
```

stdout:

```
'<repo-root>/packs/architect/.apm/skills/architect-design/assets/design-doc.md':25: DA3 — paragraph of 4 sentences (budget 3)
```

stderr: empty.

Exit code: **1** (one `DA3` finding, no refusal).

## AC-0018 fails against real, already-shipped content — a plan/asset gap, not a script defect

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

2026-09-19. The scope owner authorised a controlled contract amendment in
response to the AC-0018 failure above.

**What was measured before deciding.** One `<…>` placeholder span across all
five shipped assets carries more than three sentences:
`assets/design-doc.md:25`, at four. No other asset has one.

**Why the amendment rather than the one-line asset edit.** Splitting the one
placeholder would make the suite green while leaving `DA3` judging template
instructions, so the next template edit that writes a four-sentence
instruction reds again. That recurrence is the justification.

**Correction, 2026-09-19.** The decision was originally recorded with a second
reason that is false: that the contract was inconsistent because "AC-0024
already strips every `<…>` placeholder when `DA10` counts words". It does not.
AC-0023 is `DA10`'s counting rule and removes YAML frontmatter and
HTML-comment spans only; AC-0024's placeholder strip belongs to the one-off
command that measured the 752-word scaffolding figure, not to the gate. The
owner approved on a framing that carried that false claim. The recurrence
argument above is unaffected and is the whole justification. AC-0047 supplies
the principle that a placeholder is an author's slot rather than content to
judge; it does not supply a rule about span shape, and its own remedy for
template placeholders is corpus exclusion, which AC-0018 refuses for `DA3`.

**What the amendment changes.** AC-0019 gains a `<…>` placeholder span to its
non-prose list. AC-0018's claim is unaffected: every asset stays in the glob,
and a placeholder simply is not a prose paragraph.

**Correction to this spec's own evidence.** The probe that produced the
"zero false positives across the shipped assets" claim during authoring
skipped any line beginning with `<`, so it never examined a placeholder and
could not have found this. The claim was true of what that probe measured and
false of what it asserted; T2's parser is correct and the probe was not.

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
