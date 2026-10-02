# Verification ledger — visual-target rung precondition

Observations recorded during implementation, in task order. Each entry names the
task that produced it and the date it was taken.

---

## T1: Re-measure the carrier extent

**Date:** 2026-10-01
**Method:** Python script run outside the repository tree, sweeping `packs/`,
`guides/`, `web/src/content/`, `tests/`, and `docs/design/` with whitespace
normalized before matching (`" ".join(text.split())`). The script is recorded
in the session scratchpad and is not part of the repository.

### Carrier extent

| Dimension | Plan states | Measured | Agrees? |
| --- | --- | --- | --- |
| Total carrier files | 27 | 27 | Yes |
| Markdown carriers | 15 | 15 | Yes |
| Non-Markdown carriers | 12 | 12 | Yes |
| Total loci | 105 | 105 | Yes |

**Result: agrees exactly with the plan inventory (27 files, 105 loci, 15 Markdown
and 12 non-Markdown carriers, measured 2026-10-02).**

### Markdown carriers (15)

| File | Loci |
| --- | ---: |
| `guides/experience-design/how-to/establish-design-intent.md` | 11 |
| `guides/frontend-engineering/how-to/read-the-design-handoff.md` | 1 |
| `guides/frontend-engineering/tutorials/scaffold-a-component.md` | 1 |
| `packs/experience-design/.apm/skills/creative-direction/SKILL.md` | 3 |
| `packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md` | 8 |
| `packs/experience-design/.apm/skills/creative-direction/references/converge.md` | 7 |
| `packs/experience-design/.apm/skills/creative-direction/references/visualize.md` | 6 |
| `packs/experience-design/.apm/skills/design-system/SKILL.md` | 4 |
| `packs/experience-design/.apm/skills/design-system/assets/token-taxonomy-template.md` | 1 |
| `packs/experience-design/.apm/skills/design-system/references/value-derivation.md` | 2 |
| `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | 1 |
| `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | 2 |
| `packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md` | 3 |
| `packs/frontend-engineering/JOURNEY.md` | 1 |
| `web/src/content/journeys/frontend-engineering.md` | 1 |

### Non-Markdown carriers (12)

| File | Loci |
| --- | ---: |
| `packs/experience-design/.apm/skills/creative-direction/evals/evals.json` | 4 |
| `packs/experience-design/.apm/skills/design-system/evals/eval_queries.json` | 1 |
| `packs/experience-design/.apm/skills/design-system/evals/evals.json` | 3 |
| `packs/experience-design/tests/skills/creative-direction/test_contract.py` | 21 |
| `packs/experience-design/tests/skills/design-system/test_design_system_contract.py` | 4 |
| `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json` | 3 |
| `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_evidence.py` | 1 |
| `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_loop.py` | 1 |
| `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_precedence.py` | 3 |
| `tests/roster/test_frontend_visual_authority_adopter_prose.py` | 1 |
| `tests/roster/test_visual_target_guide_excerpt.py` | 6 |
| `tests/roster/test_visual_target_release_surface.py` | 5 |

### AC-0006 property: violation count

The AC-0006 property logic (from T4's stub): for each Markdown sentence that
contains a `visual[ _-]target` reference in its unstripped text, strip both name
forms (`approved[ -]visual[ -]target`) for the cue test, and check for a
confirmation cue (`confirm` or `approved`) in the stripped text. If the sentence
passes both tests but lacks the literal `visual_target`, it is a violation.

| Dimension | Plan states | Measured | Agrees? |
| --- | --- | --- | --- |
| Violation sentences (migration owed) | 14 | 14 | Yes |
| Files containing violations | 12 | 12 | Yes |

**Result: agrees exactly with the plan's stated migration target (14 sentences
across 12 Markdown files).**

Observation: the sweep found 21 total sentences matching the firing predicate.
The other 7 already contain `visual_target` and are compliant. The plan's "14"
is the violation count (sentences missing `visual_target`), not the total firing
count. Both figures are recorded here for completeness.

#### 14 violation sentences (no `visual_target`, migration owed)

1. `packs/frontend-engineering/JOURNEY.md` — JOURNEY bullet that resolves visual
   authority; cue fires via "confirmed" further in the sentence (the full
   whitespace-normalized sentence runs past the 200-char display limit).
2. `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` — "an approved
   visual target with no recorded human confirmation behind it" (table/list
   sentence; NAME_FORMS strips "approved visual target", but "approved" remains
   from "no recorded human confirmation").
3. `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` —
   "`approved-visual-target` — the direction artifact step 0 read, when it records
   a human-confirmed composition." Cue: "confirmed".
4. `packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md`
   — the full precedence table row; condition cell is `recorded-human-confirmation`.
5. `packs/experience-design/.apm/skills/design-system/SKILL.md` (sentence 1) —
   the rung table row containing "`approved-visual-target` | The confirmed
   composition". Cue: "confirmed".
6. `packs/experience-design/.apm/skills/design-system/SKILL.md` (sentence 2) —
   the routing table row "A route must resolve values, or a visual target is
   present"; cue fires from "confirmed" appearing later in the collapsed table.
7. `packs/experience-design/.apm/skills/creative-direction/references/visualize.md`
   — "**Approved visual target** — a composition the human has confirmed as a
   structural reference". Cue: "confirmed".
8. `packs/experience-design/.apm/skills/design-system/references/value-derivation.md`
   — "An approved visual target is a confirmed composition."
9. `packs/experience-design/.apm/skills/design-system/assets/token-taxonomy-template.md`
   — the `**Route:**` HTML comment block collapsed into one sentence; cue:
   "approved" from "approved direction".
10. `guides/frontend-engineering/how-to/read-the-design-handoff.md` —
    "`approved-visual-target` — your `direction/<slug>.md` records that a person
    confirmed the composition".
11. `guides/frontend-engineering/tutorials/scaffold-a-component.md` —
    "no confirmed visual target, no direction or taxonomy".
12. `guides/experience-design/how-to/establish-design-intent.md` (sentence 1) —
    the run-on beginning "confirm the shape against what you get back.*" that
    runs through a heading, comment, and prompt block. Cue: "confirm".
13. `guides/experience-design/how-to/establish-design-intent.md` (sentence 2) —
    the `**Route:**` block (same structure as token-taxonomy-template.md).
14. `web/src/content/journeys/frontend-engineering.md` — same JOURNEY bullet as
    item 1 (projection).

#### 7 compliant firing sentences (already contain `visual_target`)

These are in scope of the firing predicate but are not violations:

- `packs/experience-design/.apm/skills/creative-direction/references/converge.md`
  — "Record the approved visual target disposition into the `visual_target`
  frontmatter key…" (1 sentence)
- `packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md`
  — three sentences mentioning `visual_target:` disposition, key name, and absent
  value (3 sentences)
- `guides/experience-design/how-to/establish-design-intent.md` — same three
  template sentences mirrored in the guide (3 sentences)

### Non-Markdown carrier count

| Dimension | Plan states | Measured | Agrees? |
| --- | --- | --- | --- |
| Non-Markdown carrier count | 12 | 12 | Yes |

The floor `NON_MARKDOWN_CARRIER_FLOOR = 12` stated in T4's stub block is
confirmed by this measurement.

### Discoveries

None. All three measured figures (27 files / 105 loci; 15+12 split; 14
violations / 12 files; 12 non-Markdown carriers) agree exactly with the plan's
stated inventory. No further discovery is recorded.

---

## T4: The exclusive property is enforced, and proved able to fail

**Date:** 2026-10-02
**Method:** `python3 -m pytest tests/roster/test_visual_target_exclusive_property.py -v`
run from the worktree root. Mutation check performed by editing
`guides/frontend-engineering/tutorials/scaffold-a-component.md` in place
(no `git checkout`, `git reset`, or `git stash` used).

### Byte-identity verification

The stub block was extracted from the plan's T4 fenced `python` block by
script and written to
`tests/roster/test_visual_target_exclusive_property.py`. Read-back
compared byte-for-byte against the extracted block: **BYTE IDENTITY
VERIFIED** (4553 bytes, no difference).

> **Correction, controller, 2026-10-02.** This record first read 4545
> bytes. The file is 4553. The identity claim itself was correct and was
> re-verified independently by the controller against the plan's block —
> both 4553 bytes, sha256 `6fde81db9e5c6f7f…` — but the byte count
> recorded beside it was wrong by eight. Corrected rather than left,
> because a wrong number inside a byte-identity claim is the same defect
> class this contract's review rounds faulted five times.

### Controller re-verification of T4, 2026-10-02

The controller re-ran every T4 observation independently rather than
accepting the implementer's report, per the standing rule that a subagent's
report is not evidence.

| Observation | Implementer | Controller | Agrees |
| --- | --- | --- | --- |
| Stub byte identity vs the plan's block | verified | verified, 4553 bytes, sha256 `6fde81db9e5c6f7f…` | yes |
| Property reds, unmigrated tree | 14 violations | 14 violations | yes |
| Guard passes | 12 non-Markdown carriers | 12, test green | yes |
| Mutation: before | 14 | 14 | yes |
| Mutation: after adding one violating sentence | 15 | 15, new locus named in the failure output | yes |
| Mutation: after removing it | 14 | 14 | yes |

The controller used the same carrier and an equivalent sentence, restored it
to a byte-identical pre-mutation state, and confirmed `git status
--porcelain` empty afterwards. One residue was caught and fixed during that
restore: removing the appended sentence left an extra trailing newline, so
the carrier was restored from a pre-mutation copy rather than left one byte
different.

**What the mutation check establishes, and what it does not.** It shows the
property reds on a *newly introduced* violation and greens again when that
violation is removed — which a standing red over an unmigrated tree cannot
show. It does not establish that the property catches every form a violating
sentence could take; the spec's limits 1, 3 and 5 record the forms it is
known not to reach.

### Intended red — `test_every_confirmation_sentence_names_the_field`

**Result: FAILED** with **14 violations** across 12 Markdown files. Agrees
with the plan's stated count.

The 14 violation loci (file paths):

1. `packs/frontend-engineering/JOURNEY.md`
2. `packs/frontend-engineering/.apm/agents/frontend-reviewer.md`
3. `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`
4. `packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md`
5. `packs/experience-design/.apm/skills/design-system/SKILL.md` (first sentence — rung table row)
6. `packs/experience-design/.apm/skills/design-system/SKILL.md` (second sentence — routing table row)
7. `packs/experience-design/.apm/skills/creative-direction/references/visualize.md`
8. `packs/experience-design/.apm/skills/design-system/references/value-derivation.md`
9. `packs/experience-design/.apm/skills/design-system/assets/token-taxonomy-template.md`
10. `guides/frontend-engineering/how-to/read-the-design-handoff.md`
11. `guides/frontend-engineering/tutorials/scaffold-a-component.md`
12. `guides/experience-design/how-to/establish-design-intent.md` (first sentence — run-on)
13. `guides/experience-design/how-to/establish-design-intent.md` (second sentence — Route block)
14. `web/src/content/journeys/frontend-engineering.md`

### Guard passes — `test_the_non_markdown_carrier_count_has_not_fallen`

**Result: PASSED.** The sweep reached **12** non-Markdown carriers
(excluding the module itself). Floor is `NON_MARKDOWN_CARRIER_FLOOR = 12`.

---

## T2: The rung condition names the field

**Date:** 2026-10-02
**Method:** Direct file edits in the worktree, followed by running
`python3 -m pytest packs/frontend-engineering/tests/skills/frontend-engineering/ -q`
and `python3 -m agentbundle catalogue lint --root . --deep`.

### Edits made

1. `packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md`
   — changed the `approved-visual-target` row's Requires cell from
   `recorded-human-confirmation` to `visual_target: confirmed`.

2. `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`
   — reworded line 152 from "records a human-confirmed composition" to
   "carries `visual_target: confirmed`". Body line count: **964 of 968** (unchanged).

3. `packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_precedence.py`
   — rewrote the equality assertion in `test_the_top_rung_requires_a_recorded_confirmation`
   from `"recorded-human-confirmation"` to `"visual_target: confirmed"`.
   — appended `test_the_top_rung_requires_a_confirmed_visual_target` (T2 stub,
   699 bytes, byte-identity verified against the plan's fenced block).

### Byte identity

The T2 stub was extracted from the plan's fenced `python` block and compared
byte-for-byte against the appended function in the test file: **BYTE IDENTITY
VERIFIED** (699 bytes, exact match, `stub_from_plan == appended` is `True`).

### Gate results

- `python3 -m pytest packs/frontend-engineering/tests/skills/frontend-engineering/ -q`:
  **455 passed** in 1.62s. Exit 0.
- `python3 -m agentbundle catalogue lint --root . --deep`: **ok: 73 finding(s)**.
  Exit 0. Frontend-engineering body at `got 964`, within `BODY_BUDGET = 968`.
- `make lint-ruff lint-mypy`: **All checks passed** / **Success: no issues found
  in 149 source files**. Exit 0.

### Property test violation count

`python3 -m pytest tests/roster/test_visual_target_exclusive_property.py -q`
reds with **12 violations** after T2's edits, down from 14 before them. The two
loci T2 owns (`visual-observation.md` and `frontend-engineering`'s `SKILL.md`)
are no longer violations. The remaining 12 are T3's migration.

### Mutation check

**Invariant:** Every Markdown sentence containing a visual-target reference
and a confirmation cue must also contain `visual_target`.

**Catching test:** `test_every_confirmation_sentence_names_the_field`
(AC-0006).

**Exact mutation:** appended the following sentence to
`guides/frontend-engineering/tutorials/scaffold-a-component.md`:

> An approved visual target must be confirmed before proceeding to
> implementation.

This sentence fires both the reference test (`visual target` present) and the
cue test (after `NAME_FORMS` strips `approved visual target`, the remainder
contains `confirmed`), but does not contain `visual_target`.

**Before mutation:** violation count = **14**

**After adding mutation:** violation count = **15**. The new locus was named
in the failure output:

```
guides/frontend-engineering/tutorials/scaffold-a-component.md:
  An approved visual target must be confirmed before proceeding to implementation.
```

**After removing mutation** (by editing the file back — no git commands
used): violation count = **14**. Test failed on AC-0006 with the original
14 violations, guard passed with 12 non-Markdown carriers.

**Conclusion:** the property is proved able to fail on a newly introduced
violation. Both before/after counts were observed and match the expected
values.

---

## T7: The producing surfaces are gated on a confirmed target

**Date:** 2026-10-02
**Method:** Direct file edits in the worktree, followed by running
`python3 -m pytest packs/experience-design/tests/skills/creative-direction -q`.

### Edits made

1. `packs/experience-design/.apm/skills/creative-direction/references/converge.md`
   — Split the five-sentence `## Capture the doc` paragraph into two
   blank-line-delimited blocks. The first block (sentences 1–2) handles the
   target path and template copy. The second block (sentences 3–5, now gated)
   adds `visual_target: confirmed` to `When an approved visual target exists`
   so the anchor `write the selected direction's compositional commitments`
   appears in a block that contains the literal. Verifies AC-0012.

2. `packs/experience-design/.apm/skills/creative-direction/references/visualize.md`
   — Two edits in this file:
   a. **Migration (AC-0006 violation #7, now #5 in the post-T2 tree):** Added
      `, recorded by \`converge\` as \`visual_target: confirmed\`` to the
      `**Approved visual target**` sentence in `## The three representations`,
      making it compliant with AC-0006. This reduces the property's violation
      count from 12 to 11.
   b. **Gate (AC-0013):** Changed `When a target exists, record its identity and
      three boundaries` to `When a target the human has confirmed — which
      \`converge\` records as \`visual_target: confirmed\` — exists, record its
      identity and three boundaries`. The paragraph block now contains both
      `the human has confirmed` and `visual_target: confirmed`. The condition
      is the human confirmation `visualize` already holds — it runs before
      `converge` writes the field — and naming the disposition is not
      consulting it.

3. `packs/experience-design/.apm/skills/creative-direction/SKILL.md`
   — Changed the `- **Approved visual target**` list item in the Output contract
   from `When present, identify the target` to `When present and the human has
   confirmed it (\`visual_target: confirmed\`), identify the target`. The item
   now contains both `the human has confirmed` and `visual_target: confirmed`.
   Verifies AC-0014.

4. `packs/experience-design/tests/skills/creative-direction/test_contract.py`
   — Appended the T7 stub `test_producing_surfaces_are_gated_on_confirmation`
   byte-identically from the plan's fenced block.

### Byte identity

T7 stub appended byte-for-byte: **BYTE IDENTITY VERIFIED** (1440 bytes,
sha256 `5edd651895126bb4`, `stub_from_plan == appended` is `True`).

### Gate results

- `python3 -m pytest packs/experience-design/tests/skills/creative-direction -q`:
  **12 passed** in 0.32s. Exit 0.
- `make lint-ruff lint-mypy`: **All checks passed** / **Success: no issues
  found in 149 source files**. Exit 0.
- `ruff check --select F811 packs/experience-design/tests/skills/creative-direction/test_contract.py`:
  **All checks passed.** Exit 0. No F811 fired — `_unique_paragraph` is
  not redefined.

### Property violation count

`python3 -m pytest tests/roster/test_visual_target_exclusive_property.py -q`
reds with **11 violations** after T7's edits, down from 12 before them. The
one locus T7 migrates (`visualize.md`'s `**Approved visual target**` sentence)
is no longer a violation. The remaining 11 are T3's migration.

**The three gated sentences are outside AC-0006** (spec limit 4):
- `converge.md`'s `When an approved visual target exists — \`visual_target: confirmed\` — write...`
  strips to `When an exists — \`visual_target: confirmed\` — write...`, carrying
  no cue after NAME_FORMS removal. Outside the property.
- `visualize.md`'s `When a target the human has confirmed — which \`converge\` records as \`visual_target: confirmed\` — exists, record...`
  retains the cue `confirmed` (not from a name form) and contains `visual_target`.
  Fires the property and is compliant.
- `SKILL.md`'s `When present and the human has confirmed it (\`visual_target: confirmed\`), identify...`
  retains the cue `confirmed` and contains `visual_target`. Fires and is compliant.

### The three gated sentences as written

**AC-0012 (`converge.md`, block containing `write the selected direction's compositional commitments`):**
> When an approved visual target exists — `visual_target: confirmed` — write the selected direction's compositional commitments into the doc here.

**AC-0013 (`visualize.md`, block containing `record its identity and three boundaries`):**
> When a target the human has confirmed — which `converge` records as `visual_target: confirmed` — exists, record its identity and three boundaries: what is binding, what is illustrative, and what may adapt responsively.

**AC-0014 (`SKILL.md`, list item beginning `**Approved visual target**`):**
> **Approved visual target** — optional. When present and the human has confirmed it (`visual_target: confirmed`), identify the target, what is binding, what is illustrative, and what may adapt responsively.


## Execution observation — limit 4's reasoning is superseded by the gate it describes

Recorded 2026-10-02 by the controller, during verification of T7. This is an
execution observation, not a plan error: no operative requirement is affected
and nothing in the contract is unsatisfiable.

The spec's limit 4 says a gated sentence is outside the AC-0006 property, and
gives `converge.md` as its worked example: `When an approved visual target
exists, write the selected direction's compositional commitments` strips to
`When an exists, write ...`, which carries no confirmation cue.

That reasoning was correct for the sentence **before** T7 gated it. After
gating, the sentence reads:

> When an approved visual target exists — `visual_target: confirmed` — write the
> selected direction's compositional commitments into the doc here.

The inserted literal contains the word `confirmed`, which is a member of
`CONFIRMATION_CUES`. So the stripped text now reads `When an exists —
`visual_target: confirmed` — write ...` and **does** carry a cue. The sentence
therefore fires the property — and passes it, because it contains
`visual_target`.

**Limit 4's conclusion still holds.** The literal is required by AC-0012 in its
own right and not as a consequence of AC-0006; that is what the limit exists to
establish, and the gate criteria do not depend on the sentence being out of
scope. What is superseded is only the worked example's claim about the
post-gate text.

The outcome is strictly better than the limit anticipated: the gated sentence
is now inside the property and compliant, so the property guards it against a
later edit that removes the literal.

**The implementer reported the opposite** — that the sentence remains outside
the property per limit 4 — in its `Out of scope observed` note. The controller
re-derived the strip by hand and found it fires. Recorded because the report
was wrong on a checkable point and the record should not carry the error.
