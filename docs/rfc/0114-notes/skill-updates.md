# Skill updates required by RFC-0114

Input for the follow-on spec. Each row is a correction from the review of RFC-0114, the place in the `new-rfc` skill it lands, and the required change. Line numbers refer to `packs/repo-governance/.apm/skills/new-rfc/SKILL.md` at the time of writing. The skill is not rewritten until the spec.

## Writing

| Correction | Where | Required change |
| --- | --- | --- |
| Conclusion first, then support, in every section | Line 10 ("answer-first"), step 5 (lines 189-192), template comments | Draft in pyramid order. The Summary states the proposal and its reason, then one bullet per decision. Each section opens with its conclusion. |
| Terse, professional, no filler | Skill prose and template comments | Rewrite the drafting guidance in that register. No hedging or filler. Define a term, or cite an RFC or ADR, in a phrase on first use. |
| Evidence as footnotes, no narrative | Step 5, step 6, template | Cite evidence as `[n]` and list it under `## Evidence`: fact, source, method. No first-person account of the work and no history of how it was found. Long research goes in `NNNN-notes/`. |
| No invented dates | Lines 163-174 (`decide-by: <date>`), open-question guidance | Remove decide-by dates from the research-findings block and from open questions. Keep owner and default. The only dates are `Date opened` and `Date closed`, set from the system clock. |
| Diagrams help | Template, step 5 | Add a Mermaid diagram to Proposal or Design details where structure, flow or state is clearer as a picture. Follow `docs/AGENTS.md`: no raw HTML, no `;` in labels. |
| One claim per decision | Step 6 | Check that each Summary bullet is a single claim that can be accepted alone, and that links between decisions are stated. |

## Graph metadata

| Correction | Where | Required change |
| --- | --- | --- |
| The graph carries supersession for RFCs | "Recording corrections" (lines 324-334), template, step 5 | The draft carries `Supersedes` or `Supersedes in part` header lines, with D-numbers such as `RFC-0014 D1,D3`. |
| Frozen RFCs are touched only after acceptance | "After acceptance" section (line 313 onward) | The skill adds the mirrored `Superseded by` or `Superseded in part` line to each frozen RFC, and an `## Errata` entry naming the superseding RFC, only after the superseding RFC is Accepted. It never does so for a draft. |
| Headers and Errata only | Same | The skill never edits a frozen RFC's body. It changes only the one header line and appends the Errata entry. |
| A checked edge needs both sides | Same | After writing the mirrors, run `navigate-decisions` lineage in both directions and confirm the edge is checked, with equal scopes. |
| Whole-RFC supersession | Line 334 | Record it as header lines on both records plus the Errata entry. This replaces "Errata entry naming the superseding RFC" as the only record. |
| Errata are signed by merge | Lines 326-329 | The merge by a maintainer the repository's rules name signs an entry. Drop "Approver-signed". |

## Numbering

| Correction | Where | Required change |
| --- | --- | --- |
| One numbering path | Step 1 (`next-ordinal.py`) | Call the bundled `rfc.py` with `--dir <resolved RFC folder>` for `next` and `check` instead of `next-ordinal.py`. The bundled copy is byte-identical to the seeded one, and a test keeps it so. `next-ordinal.py` stays for ADRs. |
| Parity with `next-ordinal.py` | `rfc.py` | Before the switch, `rfc.py` must match what `next-ordinal.py` does for RFCs: the union with the default branch, companions (`NNNN-notes/` and `NNNN-<slug>-research.md`), duplicate reporting, confined reads, and a non-zero exit when the folder cannot be read. Decide whether to keep the 5-digit prefix tolerance. |
| Tests move with it | `packs/repo-governance/tests/skills/new-rfc/test_next_ordinal.py`, `tests/roster/test_typed_ordinal_collision_equivalence.py`, `tests/roster/test_decision_record_ordinal_uniqueness.py` | Repoint the RFC cases at `rfc.py`. |

## Process and gates

| Correction | Where | Required change |
| --- | --- | --- |
| No Approver field | Line 214 (checklist), lines 310-311 (receipt) | "Approver named" becomes "who decides is clear". The receipt reports who decides. |
| The skill never reads the governance file | Governance mode, step 0 | The pinned rule that RFC mode never reads or names `GOVERNANCE.md` stays. A stricter local rule reaches the skill through project instructions. |
| Governance mode target | Governance mode, "Choose the target" | An existing governance file at any allowed location is the target. Update the test that pins "next to the charter". |
| Citations resolve | Step 6 | Every `[n]` resolves to an Evidence item, and every item is cited. |
| Each date has a source | Step 6 | Every date in the RFC comes from the system clock or a cited source. |
| Anti-patterns | Lines 336-347 | Add: narrative history in the body, a mirror line on a frozen RFC before acceptance, an invented date or deadline, filler. |

## Evals and guide

- Rewrite the first eval for the new template, and keep two assertions: it "reads from zero prior context", and it carries the Decision-weight field.
- Add assertions for Summary-first order, footnoted evidence without narrative, no decide-by dates, a diagram where structure matters, supersession header lines at draft, and no mirror line before acceptance.
- Rewrite `guides/repo-governance/how-to/new-rfc.md` in the same register.

## Check

The rewritten skill text and guide pass the same checks as an RFC: a cold reader can state the point from the opening, and the prose has no first-person narrative and no unsourced date.
