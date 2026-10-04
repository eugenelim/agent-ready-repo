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


## T5: The superseded rule is annotated where it lives

**Date:** 2026-10-02
**Method:** Extracted T5 stub byte-identically from plan.md fenced `python` block.
Wrote to `tests/roster/test_visual_authority_supersession.py`. Read-back compared
byte-for-byte: **BYTE IDENTITY VERIFIED** (1408 bytes, sha256 `c169733ae84cb416`,
`stub_from_plan == written` is `True`).

### Intended red — before Status annotation

`python3 -m pytest tests/roster/test_visual_authority_supersession.py -q` reds with:

```
AssertionError: AC-0008: Status does not name ADR-0132
```

Agrees with the plan's stated intended red (`AssertionError: AC-0008: Status does
not name ADR-0132`).

### Status line annotation

Appended a second supersession clause to `docs/specs/frontend-visual-authority/spec.md`
line 3 — one physical line, left end to right end unchanged except the insertion before
the comment marker.

**Full Status line as written:**

```
- **Status:** Shipped (superseded in part by ADR-0130 — 960-line body budget; everything else stands) (superseded in part by ADR-0132 — rung condition (Always do, line 80) and AC-0003a; everything else stands) <!-- Draft | Approved | Implementing | Shipped | Archived -->
```

All five stub assertions verified manually against the lowercased, whitespace-normalized line:

| Assertion | Value | Passes |
| --- | --- | --- |
| `"adr-0132" in flat` | present | yes |
| `"rung condition" in flat` | present | yes |
| `"ac-0003a" in flat` | present | yes |
| `flat.count("everything else stands") == 2` | 2 | yes |
| `flat.index("adr-0130") < flat.index("adr-0132")` | ADR-0130 is first | yes |

### Property violation count

`python3 -m pytest tests/roster/test_visual_target_exclusive_property.py -q` reds with
**11 violations** — unchanged from post-T7. T5 touches no swept Markdown carrier,
so the count does not change.

### Non-Markdown carrier count

`test_the_non_markdown_carrier_count_has_not_fallen` passes with 12 carriers.
The T5 module does not contain `visual[ _-]target` and is not a carrier.

### Gate results

- `make lint-ruff lint-mypy`: **All checks passed** / **Success: no issues found
  in 149 source files**. Exit 0.
- `python3 tools/test-lint-pack-test-boundary.py`: **ok — 154 cases passed**. Exit 0.
- `python3 -m pytest tests/roster/test_visual_authority_supersession.py -q`:
  **1 passed** in 0.26s. Exit 0.

---

## T3: Migrate the restating carriers

**Date:** 2026-10-02
**Method:** Direct file edits in the worktree.
- Markdown loci: hand-edited each of the 11 remaining violation sentences.
- AC-0005 loci: hand-migrated the two loci outside the property.
- AC-0011 eval harness: updated assertion text in three eval JSON files.
- AC-0011 tests: added `test_the_rung_resolution_eval_assertions_name_the_field`
  to `test_visual_authority_precedence.py`; added
  `test_the_visual_target_eval_case_assertion_names_the_field` to
  `test_design_system_contract.py`.

### Property test result

`python3 -m pytest tests/roster/test_visual_target_exclusive_property.py -q`:
**2 passed** in 5.36s. Exit 0. Down from 11 violations at T3 start.

### Pack suite result

`python3 -m pytest packs/frontend-engineering/tests/skills/frontend-engineering packs/experience-design/tests -q`:
**487 passed** in 2.98s. Exit 0.

### AC-0005 observations

AC-0005 defines loci that carry a visual-target reference with a confirmation
cue but lie outside all four mechanisms — no property enforcement, no guide
test, no eval test, no test module assertion. Two such loci were migrated by
hand:

**AC-0005 locus 1 — `packs/experience-design/.apm/skills/design-system/SKILL.md`,
Procedure step 2.**

Before: `and the visual target when one exists.`
After: `and the \`visual_target: confirmed\` target when one exists.`

This sentence is inside Procedure step 2 ("Read the authority"). It fires the
property's cue test (cue `approved` from the rung table row that collapses with
it), but the word `exists` is not a confirmation cue — the cue fires from the
collapsed sentence, not from this sentence on its own. Migrated here rather
than left, because the sentence is describing a confirmed target and naming the
field is the correct documentation.

**AC-0005 locus 2 — `guides/frontend-engineering/how-to/read-the-design-handoff.md`,
rung 1 "You are here if" sentence.**

Before: `**You are here if** the artifact says somewhere that the composition
was approved or signed off, rather than merely proposed or picked.`
After: `**You are here if** the direction's \`visual_target\` field is
\`confirmed\`, recording that the composition was signed off.`

This sentence's only trigger cue is `approved`, which NAME_FORMS strips (it
is part of `approved visual target`). After stripping both name forms, no
confirmation cue remains, so the property does not fire on it. Migrated here
because the sentence is the guide's definition of the rung condition, and the
correct definition is the field value, not a prose description that predates
the field.

### Run-on locus cost

The first violation sentence in
`guides/experience-design/how-to/establish-design-intent.md` is a
segmentation artefact: whitespace normalization collapses a run of text
beginning at `confirm the shape against what you get back.*` and ending at
`and any approved visual target.` — which is inside a copy-paste user prompt
in a fenced code block. The normalizer does not strip code blocks before
splitting, so the prompt text lands in the same "sentence."

The migration adds `(visual_target: confirmed)` inside the prompt code block.
This satisfies the property (the collapsed sentence now contains the literal),
but the phrase appears inside a prompt that gives no instruction about the
field — it records the user asking the agent about the target without stating
a condition. A reader of the prompt sees the field name as additional context,
not as a requirement. This cost is the minimum unavoidable consequence of the
segmentation artefact: the literal must appear somewhere in the collapsed
sentence, and the only editable surface is the prompt text.

---

## T8: Register both roster modules in CI

**Date:** 2026-10-02
**Method:** Direct edits to `.github/workflows/build-check.yml`,
`tools/lint-ci-parity.py`, and `.workspace-prune-protected.toml`, followed by
running the four `Done when` conditions.

### Step placement (condition 1)

Both new steps were inserted between the `pytest visual-target release surface
(roster-owned)` step (line 684) and the bulk `pytest catalogue-test carve-out
destinations (RFC-0082)` step.

| Step name | Line | Bulk step line | Above bulk? |
| --- | ---: | ---: | --- |
| `pytest visual-target exclusive property (roster-owned)` | 692 | 706 | yes |
| `pytest visual-authority supersession (roster-owned)` | 702 | 706 | yes |

Verified by `grep -n` on the modified file; both 692 and 702 are numerically
less than 706.

### Disposition entries (condition 2)

Entries added on both axes of `tools/lint-ci-parity.py`:

| Axis | Step name | Line |
| --- | --- | ---: |
| `_LOCAL_STEP_DISPOSITION` | `pytest visual-target exclusive property (roster-owned)` | 669 |
| `_LOCAL_STEP_DISPOSITION` | `pytest visual-authority supersession (roster-owned)` | 671 |
| `_GATE_MAIN_CHECKS` | `pytest visual-target exclusive property (roster-owned)` | 971 |
| `_GATE_MAIN_CHECKS` | `pytest visual-authority supersession (roster-owned)` | 972 |

### Prune entry (condition 3)

Added `"docs/specs/frontend-visual-authority"` to `.workspace-prune-protected.toml`
between `docs/specs/foo-bar` and `docs/specs/group` (alphabetical order).
`test_visual_target_exclusive_property.py` names no `docs/specs/<slug>` literal
and owes no entry.

### Gate results (condition 4)

| Command | Result | Exit code |
| --- | --- | --- |
| `python3 tools/lint-ci-parity.py --root .` | ok — 125 step(s), all dispositioned | 0 |
| `python3 -m pytest tests/roster/test_two_sided_prune_closure_invariant.py -q` | 47 passed in 9.41s | 0 |
| `ruff check .` | All checks passed | 0 |
| `make lint-ruff lint-mypy` | All checks passed / no issues in 149 source files | 0 |

### git status

`git status --porcelain` shows only the three files T8 may touch:
- `M .github/workflows/build-check.yml`
- `M .workspace-prune-protected.toml`
- `M tools/lint-ci-parity.py`

The verification ledger itself is under
`docs/specs/visual-target-rung-precondition/notes/verification-ledger.md`, also
a T8 touch.

---

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


## T6 — the release surface is consistent

Recorded 2026-10-02 by the controller, after a post-gates review finding
established that this task had no entry here. The observations below were taken
at the time T6 ran; only their placement in this ledger was missing. AC-0009's
evidence per the Testing Strategy is "a recorded baseline reading for each pack
taken before the bump", and that is what the first table is.

### Slice-start baselines, read before the bump

Read directly from the tree at delivery commit `13e3b7aa9`, **before** T6 was
dispatched, because once the bump lands the tree no longer shows what the branch
carried when the slice began.

| Pack | `pack.toml` | `plugin.json` | `marketplace.json` |
| --- | --- | --- | --- |
| `frontend-engineering` | 0.4.0 | 0.4.0 | 0.4.0 |
| `experience-design` | 4.1.2 | 4.1.2 | 4.1.2 |

### After the bump

| Pack | `pack.toml` | `plugin.json` | `marketplace.json` |
| --- | --- | --- | --- |
| `frontend-engineering` | 0.4.1 | 0.4.1 | 0.4.1 |
| `experience-design` | 4.1.3 | 4.1.3 | 4.1.3 |

Patch for both, per `packs/AGENTS.md` § *Version bump rule*: patch for changed
content. This contract publishes no new skill, subagent, command or hook.

### The release pin

`packs/frontend-engineering/tests/skills/frontend-engineering/test_visual_authority_release.py:90`
moved from `"0.4.0"` to `"0.4.1"`, and its docstring now names this delivery.
Moved **with** the bump in the same change, as the pin's own message requires.

### The three `Done when` runs, each read from its exit status

| Command | Exit | Result |
| --- | ---: | --- |
| `make lint-ruff lint-mypy` | 0 | clean |
| `pytest tests/conformance/test_pack_metadata.py -q` | 0 | 49 passed |
| `pytest packs/frontend-engineering/tests/skills/frontend-engineering/ -q` | 0 | 457 passed |

The third is the one that matters for AC-0009. It was added to T6's closure at
review round 4, because neither of the other two reaches
`test_visual_authority_release.py` and no lint can see a wrong pin value — so
without it the pin clause had no predicate after the bump.

### The projection was regenerated, not assumed

`make build-self` ran without `FORCE=1`, which the root `AGENTS.local.md:49-60`
forbids from automation. `.claude-plugin/marketplace.json` then changed by
exactly two insertions and two deletions — the two version strings and nothing
else — verified from the committed diff rather than from the command's own
report. A stale projection is the failure this check exists for.

### The changelog

Both entries carry a free-standing `##` heading, a `### Highlights`
subsection, and one `-` bullet naming `visual_target`. The bullet form is
load-bearing rather than cosmetic: `docs/product/AGENTS.md` records that the
`/now/` projection extracts only bullets and drops a paragraph silently. The
projection tests were run — 17 passed — rather than the form being judged by eye.

### Dispatch receipt, and who applied the repair

T6 was dispatched to an implementer subagent and is recorded `--receipt`. The
post-gates repair to its changelog bullet was applied by the **controller**, not
by an implementer, and the receipt vocabulary has no value for that — it admits
only `--receipt`, or `--decline` with `no-implementer-installed` or
`human-directed`. Following the owner's ruling of 2026-10-01 on the same
situation, the receipt records the dispatch and this ledger records the
authorship. The same holds for the three other post-gates repairs, which touched
T2's and T4's surfaces: all four were controller-applied from sustained findings.

`loop-cohort wave reopen` superseded T6's original receipt when the review
findings reopened wave 4, so the receipt was re-recorded afterwards. That is the
verb working as designed: a reopened wave has no live record until one is
re-asserted, and `wave-complete` refuses until it is.

The `experience-design` bullet was rewritten after post-gates review: its first
form said the three producing surfaces "act on the target only when
`visual_target: confirmed` appears in the direction artifact", which casts
`converge` — the surface that *writes* the value — as a surface that reads it.
AC-0013 forbids stating `visualize`'s condition as a field read. Both post-gates
reviewers found the same sentence independently.

## Execution observation — the T4 stub's floor diverges from the plan

Recorded 2026-10-02 by the controller.

`NON_MARKDOWN_CARRIER_FLOOR` reads **13** in
`tests/roster/test_visual_target_exclusive_property.py`. The approved stub in
`plan.md` carries **12**, so the shipped module no longer matches the stub it was
materialized from byte-identically at EXECUTE.

The divergence is a sustained post-gates finding, not drift. The floor is a
measurement, and this slice's own work moved what it measures: T6's release-pin
docstring put the phrase `visual-target rung precondition` into
`test_visual_authority_release.py`, making it a swept carrier it was not on
`origin/main`. Measured 2026-10-02: 14 non-Markdown carriers, 13 excluding the
property module's self-exclusion. A floor of 12 left one carrier of slack, so
AC-0011's only mechanical guard could have stayed green while a real carrier
lost its reference.

The adjudicator refused the reviewer's proposed mechanism — making the guard red
per file "present at merge" — because that reinstates the closed surface set the
spec's `Never do` forbids. Raising the floor to the measured count is the
smallest change that restores what AC-0011 states, and it adds no mechanism.

**The plan is not edited.** It is immutable in substance after approval, and its
stub records the value that was correct when the plan was approved. This entry is
the record that the shipped value supersedes it, and why.


## Correction — two recorded numbers, after post-gates round 2

Recorded 2026-10-02 by the controller.

**The third `Done when` count read 456 and the command returns 457.** The table
above now records 457. The cause is this delivery's own repair: commit
`79b91f4a3` added `test_the_skill_rung_bullet_names_the_confirmed_field` to the
swept directory *in the same change that wrote the table*, so the number was
stale the moment it was written. Measured: `457 passed` at HEAD, and
`456 passed, 1 deselected` with that one assertion deselected, which fixes the
delta at exactly that test.

The adjudicator could not settle this from reads and said so — a grep of test
functions cannot establish a collected total, because parametrization expands
it. It declared the finding indeterminate and named the missing input. The
controller supplied the run; that is not a second adjudication pass.

**The release-pin anchor read `:89` and the asserted literal is on `:90`.**
Line 89 is `version = _pack()["pack"]["version"]`; line 90 carries
`assert version == "0.4.1"`. Corrected above.

Both are unpinned observations and no gate reads either, which is why both were
graded Nit rather than blocking. They are corrected anyway: a verification
ledger whose numbers do not reproduce is weaker evidence than one that says
less.
