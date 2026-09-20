# Measurement record — `DA3` and `DA10` against documents the gate authors did not write

The title names `DA3` and `DA10` because those are the only two gates this
probe could measure. The other eight are reviewer prose, not code; § *What
this probe can and cannot measure* says why, and § *What remains
uncalibrated* says what that leaves open.

- **Probe:** `docs/product/intents/architect-design-gate-calibration.md`, validation hook `status: to-validate`
- **Run date:** 2026-09-20
- **Baseline:** `7c794b793` (current merged `main`), worktree `architect-probe`
- **Gates under test:** shipped at `c4b2f5912`, 2026-09-19 12:56:19 -0500
- **Instrument:** `packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py`, run once per document with `--root .`
- **Changed files:** none. **Commits:** none.

## Verdict

**SURVIVED on the corpus line — and the probe found a defect in `DA3`.**

The headline result is not a threshold judgement. `DA3`'s sentence counter
**under-counts by 57%**: it reports 81 trips on this corpus where the true
number is 127, because a sentence ending inside `**bold**`, quotes, backticks
or parentheses is invisible to it. See § *Counter fidelity*. Every number in
this record is therefore given twice, as shipped and as corrected.

The predeclared line asks for at least five independent design
documents, of which at least three are subsystem-scope. The corpus supplies
**37 documents across 18 independent deliveries spanning 2026-05-03 to
2026-09-15**, of which **20 are subsystem-scope**, plus one document from a
second repository. Every one predates the gates.

## Instrument check

Both predeclared smoke tests reproduce exactly:

```
'docs/architecture/loop-contract.md':100: DA3 — paragraph of 5 sentences (budget 3)
'docs/architecture/loop-contract.md':117: DA3 — paragraph of 5 sentences (budget 3)
'docs/architecture/binder-publishing/resolution.md':37: DA3 — paragraph of 4 sentences (budget 3)
'docs/architecture/binder-publishing/resolution.md':239: DA3 — paragraph of 4 sentences (budget 3)
```

Neither trips DA10. Setup confirmed.

## What this probe can and cannot measure

The script implements **DA3 and DA10 only** — the two ADR-0118 classifies as
mechanizable. `packs/architect/.apm/skills/architect-design/scripts/` holds
exactly two files, the gate and its `file_safety.py` helper. The seven hybrid
prechecks (`DA1`, `DA2`, `DA4`, `DA6`, `DA7`, `DA8`, `DA9`) live as reviewer
prose in `references/design-doc-rubric.md` §§ 194–258 and are decided by a
reviewer, not a program. Judgment-only `DA5` carries no precheck at all.

So "per document, per gate" is answerable for DA3 and DA10 and **not**
answerable for the other eight. A hand-rolled approximation of, say, DA1's
`will be` / `previously` precheck would produce a number that is not the
gate's, and reporting it as DA1's result would be worse than reporting
nothing. The seven prechecks remain uncalibrated after this probe, and that
is the probe's own limit, not a finding about them.

## Corpus

Criterion applied: authored outside the delivery that wrote the gates, and
without knowledge of them. Every candidate's last-touch date is **before
2026-09-18**, so none was edited by or after the gate delivery. Subsystem-scope
judgement follows `references/design-doc-rubric.md:18` — a document is
subsystem-scope when it describes one subsystem's own internals (entrypoints,
owned state, contracts, runtime behaviour, failure modes) rather than the
whole system's containers or a delta to an existing architecture.
Marked `no`: `overview.md`, `README.md`, `reference.md`, `pack-layout.md` and
`skill-and-pack-format.md` (system/reference scope);
`agent-skill-engineering.md` (explicitly `STATUS: PLANNED` future-state);
`verification-graph.md` (its own first line: "This is a facts document, not a
design document"); `security.md`, `agentbundle.md` and the binder-publishing
`README`/`overview`/`history`/`decisions`/`rollout`/`examples`/
`verified-findings` and `catalogue/README.md` (subsystem-set or
cross-cutting rather than one subsystem). That is 17 excluded against 20
subsystem-scope, totalling the 37 documents in the sweep.

| Document | Lines | Words | Introduced | Last touched | Subsystem-scope | Prose ¶ | DA3 trips | DA3 trip lines | DA10 |
| --- | ---: | ---: | --- | --- | :-: | ---: | ---: | --- | :-: |
| `docs/architecture/README.md` | 66 | 383 | b69e4d405 2026-05-22 | 2026-09-17 | no | 8 | 0 | — | pass |
| `docs/architecture/agent-skill-engineering.md` | 332 | 2262 | c29929a8e 2026-08-26 | 2026-09-09 | no | 30 | 7 | 55(4), 130(4), 155(4), 228(5), 266(4), 275(6), 290(8) | pass |
| `docs/architecture/agentbundle.md` | 219 | 1452 | a573493ed 2026-05-25 | 2026-09-15 | no | 26 | 0 | — | pass |
| `docs/architecture/binder-publishing/README.md` | 82 | 690 | 1d0c8e7c7 2026-08-06 | 2026-08-20 | no | 5 | 0 | — | pass |
| `docs/architecture/binder-publishing/binder-recipe.md` | 311 | 2364 | 1d0c8e7c7 2026-08-06 | 2026-08-19 | yes | 17 | 1 | 278(4) | pass |
| `docs/architecture/binder-publishing/decisions.md` | 100 | 3295 | 1d0c8e7c7 2026-08-06 | 2026-08-20 | no | 7 | 0 | — | pass |
| `docs/architecture/binder-publishing/editorial-model.md` | 389 | 2542 | 1d0c8e7c7 2026-08-06 | 2026-08-20 | yes | 29 | 2 | 124(4), 314(4) | pass |
| `docs/architecture/binder-publishing/examples.md` | 158 | 351 | 1d0c8e7c7 2026-08-06 | 2026-08-19 | no | 11 | 1 | 75(5) | pass |
| `docs/architecture/binder-publishing/history.md` | 36 | 249 | 6c0069331 2026-08-07 | 2026-08-19 | no | 0 | 0 | — | pass |
| `docs/architecture/binder-publishing/invocation.md` | 339 | 2458 | 1d0c8e7c7 2026-08-06 | 2026-08-20 | yes | 39 | 1 | 123(5) | pass |
| `docs/architecture/binder-publishing/outline-and-templates.md` | 297 | 1977 | 1d0c8e7c7 2026-08-06 | 2026-08-19 | yes | 24 | 0 | — | pass |
| `docs/architecture/binder-publishing/overview.md` | 187 | 1185 | 1d0c8e7c7 2026-08-06 | 2026-08-20 | no | 18 | 4 | 47(4), 68(4), 98(4), 183(5) | pass |
| `docs/architecture/binder-publishing/resolution.md` | 400 | 2864 | 1d0c8e7c7 2026-08-06 | 2026-08-20 | yes | 26 | 2 | 37(4), 239(4) | pass |
| `docs/architecture/binder-publishing/resolved-index.md` | 312 | 2035 | 1d0c8e7c7 2026-08-06 | 2026-08-20 | yes | 24 | 0 | — | pass |
| `docs/architecture/binder-publishing/rollout.md` | 148 | 943 | 1d0c8e7c7 2026-08-06 | 2026-08-20 | no | 15 | 1 | 117(5) | pass |
| `docs/architecture/binder-publishing/runtime.md` | 316 | 2379 | 1d0c8e7c7 2026-08-06 | 2026-08-20 | yes | 41 | 1 | 207(4) | pass |
| `docs/architecture/binder-publishing/security-profile.md` | 338 | 2912 | 1d0c8e7c7 2026-08-06 | 2026-08-19 | yes | 34 | 1 | 98(4) | pass |
| `docs/architecture/binder-publishing/verified-findings.md` | 87 | 571 | 1d0c8e7c7 2026-08-06 | 2026-08-19 | no | 3 | 0 | — | pass |
| `docs/architecture/binder-publishing/zensical-adapter.md` | 600 | 4374 | 1d0c8e7c7 2026-08-06 | 2026-08-20 | yes | 60 | 1 | 423(4) | **TRIP** 4374 |
| `docs/architecture/catalogue/README.md` | 139 | 867 | 351ea3eab 2026-09-15 | 2026-09-15 | no | 13 | 2 | 11(4), 32(4) | pass |
| `docs/architecture/catalogue/derived-catalogue.md` | 175 | 1253 | 351ea3eab 2026-09-15 | 2026-09-15 | yes | 21 | 4 | 101(4), 111(4), 130(4), 137(4) | pass |
| `docs/architecture/catalogue/state.md` | 100 | 620 | 351ea3eab 2026-09-15 | 2026-09-15 | yes | 12 | 0 | — | pass |
| `docs/architecture/catalogue/upstream-sync.md` | 281 | 1872 | 351ea3eab 2026-09-15 | 2026-09-15 | yes | 29 | 2 | 100(4), 218(6) | pass |
| `docs/architecture/credentials.md` | 164 | 980 | a573493ed 2026-05-25 | 2026-08-19 | yes | 18 | 5 | 9(4), 58(4), 92(4), 98(6), 109(4) | pass |
| `docs/architecture/knowledge-capture.md` | 121 | 691 | 18c17eb5d 2026-08-13 | 2026-08-31 | yes | 16 | 1 | 42(4) | pass |
| `docs/architecture/loop-contract.md` | 214 | 1826 | 95754ea45 2026-09-11 | 2026-09-17 | yes | 20 | 2 | 100(5), 117(5) | pass |
| `docs/architecture/loop-infrastructure.md` | 154 | 724 | 217925dab 2026-07-31 | 2026-09-11 | yes | 14 | 0 | — | pass |
| `docs/architecture/overview.md` | 125 | 734 | 5d00780a6 2026-05-03 | 2026-09-17 | no | 3 | 1 | 41(5) | pass |
| `docs/architecture/pack-layout.md` | 355 | 2227 | a573493ed 2026-05-25 | 2026-09-17 | no | 25 | 4 | 44(7), 58(5), 86(4), 343(5) | pass |
| `docs/architecture/pack-manifest.md` | 119 | 793 | f94ce040a 2026-06-13 | 2026-08-30 | yes | 10 | 2 | 7(6), 79(4) | pass |
| `docs/architecture/reference.md` | 95 | 638 | 0fc558283 2026-08-20 | 2026-09-12 | no | 2 | 0 | — | pass |
| `docs/architecture/security.md` | 231 | 1880 | f1a07e6fe 2026-07-04 | 2026-09-19 | no | 22 | 3 | 9(4), 62(4), 72(4) | pass |
| `docs/architecture/skill-and-pack-format.md` | 90 | 681 | 503f6305f 2026-06-30 | 2026-09-15 | no | 8 | 1 | 65(4) | pass |
| `docs/architecture/telemetry.md` | 510 | 4158 | c2e782bad 2026-09-11 | 2026-09-17 | yes | 63 | 12 | 9(7), 28(4), 42(4), 57(4), 73(4), 201(5), 206(4), 244(5), 251(4), 256(4), 290(7), 367(4) | **TRIP** 4158 |
| `docs/architecture/verification-graph.md` | 790 | 6168 | 6145ac954 2026-09-04 | 2026-09-15 | no | 97 | 8 | 138(4), 178(4), 273(5), 446(4), 509(4), 637(4), 657(4), 676(4) | **TRIP** 6168 |
| `docs/architecture/work-intake-and-artifact-routing.md` | 419 | 3057 | 352595bd2 2026-08-08 | 2026-09-17 | yes | 34 | 11 | 5(4), 18(4), 31(4), 40(4), 121(4), 131(4), 137(4), 143(4), 164(5), 305(4), 313(6) | pass |
| `docs/architecture/workspace-mcp/design.md` | 98 | 506 | 8d1a35c7e 2026-08-03 | 2026-08-19 | yes | 12 | 1 | 65(4) | pass |

Totals (**shipped counter**): 37 documents, 836 prose paragraphs, 81 DA3 trips (9.7%), DA10 trips 3. The corrected DA3 figure is 127 trips (15.2%); the DA3 trip lines in the column above are the shipped counter's and therefore incomplete.
Sentence-count distribution: {1: 233, 2: 326, 3: 196, 4: 58, 5: 14, 6: 5, 7: 3, 8: 1}

### Delivery independence

The 37 documents enter the tree in **18 distinct introducing commits**, the
earliest `5d00780a6` (2026-05-03), the latest `351ea3eab` (2026-09-15). The
eleven `binder-publishing/` documents share one introducing commit
(`1d0c8e7c7`, 2026-08-06), so they are one delivery, not eleven; the
predeclared line is still cleared without them — `telemetry.md`
(`c2e782bad`), `work-intake-and-artifact-routing.md` (`352595bd2`),
`loop-contract.md` (`95754ea45`), `credentials.md` (`a573493ed`),
`workspace-mcp/design.md` (`8d1a35c7e`) and `catalogue/upstream-sync.md`
(`351ea3eab`) are six subsystem-scope documents from six separate deliveries.

## Totals per gate — in-repository corpus (37 documents)

| Gate | Documents tripping | Documents clean | Trips | Denominator | Trip rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `DA3` *(shipped counter)* | 26 | 11 | 81 | 836 prose paragraphs | 9.7% |
| `DA3` *(counter corrected)* | 29 | 8 | **127** | 836 prose paragraphs | **15.2%** |
| `DA10` | 3 | 34 | 3 | 37 documents | **8.1%** |
| `DA1`, `DA2`, `DA4`–`DA9` | not measurable — reviewer prose, no script | | | | |

Sentence-count distribution across all 836 prose paragraphs:

| Sentences | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Paragraphs | 233 | 326 | 196 | 58 | 14 | 5 | 3 | 1 |

Under the shipped counter 90.3% of paragraphs sit at or under the budget.
**Under the corrected counter that falls to 84.8%**, and the corrected
distribution is 1×215, 2×292, 3×202, 4×95, 5×18, 6×10, 7×1, 8×3.

Budget sensitivity, corrected: raising the budget to 4 drops the trip count
from 127 to 32 (3.8%); to 5, to 14 (1.7%). The 95 four-sentence paragraphs —
not 58 — are what a budget decision turns on.

`DA10` word counts, 37 documents: median 1,872; largest clean document
`binder-publishing/decisions.md` at **3,295 words, five words under the
3,300 bound**; the three trips at 4,158, 4,374 and 6,168.

## The adversarial case — second repository

`docs/architecture/pydantic-ai-worker-runtime/worker-runtime.md` in
`company-intelligence-desk` **is present in a local clone**, referred to below as
`<local-clone>/company-intelligence-desk`. Nothing was fetched or cloned. It was **read at `1003fb0`**, its HEAD state on 2026-09-20; pin that SHA,
because a rewrite of this document using `architect-design` would replace an
independent document with one authored by the skill that owns the gates, and
any later read of the path is no longer independent evidence. At that commit
it is 2,183 lines and 18,915 gate-counted words, introduced by
`07b4fcc` at 2026-09-18 00:33 -0500 and last touched by `1003fb0` at
2026-09-18 01:23 -0500 — roughly 35 hours before the gates shipped, in a
repository where `ls .claude/skills/` shows the core pack only and **no
`architect-design` skill**. The gates were never available to its author.

| Gate | Result |
| --- | --- |
| `DA10` | **TRIP** — 18,915 words against a 3,300-word bound, **5.7× over** |
| `DA3` *(shipped counter)* | 38 trips across 197 prose paragraphs — 19.3% |
| `DA3` *(counter corrected)* | **61 trips** across 197 prose paragraphs — **31.0%** |

Its distribution: 1×34, 2×85, 3×40, 4×23, 5×8, 6×5, 7×1, 8×1. DA3 trip lines:
9, 54, 369, 415, 468, 580, 640, 700, 895, 922, 941, 1000, 1264, 1302, 1338,
1390, 1481, 1491, 1523, 1600, 1613, 1702, 1723, 1743, 1760, 1774, 1793, 1814,
1822, 1850, 1865, 1874, 1890, 1910, 1934, 1965, 2008, 2131.

**This is the load-bearing comparison in the whole record, and it survives the
correction.** In-repository 9.7% versus 19.3% on the shipped counter;
**15.2% versus 31.0%** on the corrected one. The ratio is almost exactly two
either way, so the finding — a document written further from this repository's
house style trips `DA3` at twice the rate — does not depend on the defect.

## Counter fidelity — a defect, found by reading the output

**`DA3`'s sentence counter under-counts, and the headline 9.7% is wrong.**
This was found by reading the 58 four-sentence paragraphs the first pass
enumerated: `telemetry.md:251` reads as five sentences and the gate bucketed
it as four.

The cause is in `count_sentences`. The boundary pattern is

```python
_SENTENCE_BOUNDARY_PATTERN = re.compile(r"[.!?]+(?=\s+\S)")
```

which requires whitespace **immediately** after the terminator. Any closing
delimiter sitting between the two swallows the boundary:

| Input | Counted | Actual |
| --- | ---: | ---: |
| `One. Two. Three. Four.` | 4 | 4 |
| `**One.** Two. Three. Four.` | **3** | 4 |
| `One. *Two.* Three. Four.` | **3** | 4 |
| `One. He said "go." Three. Four.` | **3** | 4 |
| `One. (An aside.) Three. Four.` | **3** | 4 |
| ``One. Two is `x.` Three. Four.`` | **3** | 4 |

This is the exact failure class the function's own docstring claims to have
avoided. It reasons carefully about what *opens* a sentence — "an allowlist of
sentence-initial characters has unbounded holes … which is the under-count
`DA3` exists to catch" — and enumerates the holes on that side. The same hole
exists on the **closing** side and was not considered. A bold lead-in sentence,
which this repository's house style uses constantly, is invisible to the gate.

### What it costs, measured

Re-run over the same 37 documents with the terminator class widened to
`[.!?]+[)\]"'’”*`]*(?=\s+\S)`:

| | Shipped counter | Corrected | Change |
| --- | ---: | ---: | --- |
| `DA3` trips | 81 | **127** | +46, a **57% under-report** |
| Trip rate | 9.7% | **15.2%** | |
| Documents tripping | 26 of 37 | **29 of 37** | |
| Paragraphs mis-counted | — | **126 of 836 (15.1%)** | |
| Paragraphs missed entirely | — | **46** | crossed the budget unseen |

Corrected distribution: 1×215, 2×292, 3×202, 4×95, 5×18, 6×10, 7×1, 8×3.

**The corrected pattern is a measuring instrument, not a proposed fix.**
It was written to size the defect, not to ship. It is right on the dominant
case — a terminator followed by closing markup then whitespace — and it is
knowingly loose on at least one: a mid-sentence code span holding a period,
as in ``set `x.` and continue``, now reads as a boundary where the shipped
pattern read none. That case is rare in this corpus and cuts the other way
from the defect, so 127 should be read as approximately right rather than
exact. The direction and the order of magnitude are not in doubt — 121 of
the 126 mis-counts are a bold-terminated sentence, which is unambiguous. A
real fix belongs in the spec that follows, with the six-case table above as
its regression suite.

The swallowing delimiter is `**` in 121 of 126 cases; the rest are `"`,
`` ` ``, `)` and combinations. On the adversarial `worker-runtime.md` the
shipped counter reports 38 trips where the corrected one reports **61** —
31.0% of its 197 paragraphs, against the 19.3% first reported.

### What is *not* falsified

- **AC-0018 holds.** The reference document at
  `packs/architect/tests/skills/architect-design/testdata/telemetry-endpoint-default-design.md`
  reports **zero** `DA3` findings under the shipped counter *and* zero under
  the corrected one. Its clean half is genuinely clean; it is not clean
  because the counter is broken. This was the obvious suspicion and it is
  wrong, so it is recorded as a negative rather than left implied.
- **The over-count classes are absent.** All 119 shipped trips were scanned
  for the two over-counts the docstrings knowingly accept — an uppercase lone
  initial, and a terminator before a Starlight `:::` fence. **Zero** carried
  either. Five were read by hand and each is a genuine paragraph of the
  reported length. Every trip the gate reports is real; the defect is
  one-directional, and it is under-reporting.

### Correction to this record

An earlier version of this section concluded "the instrument reporting against
it is sound on this corpus." **That was wrong**, and it was wrong because the
check behind it only looked for over-counts. Scanning for the over-count
classes cannot find an under-count, and I treated a clean over-count scan as
evidence of fidelity in both directions. The defect surfaced only on reading
the paragraphs themselves.

## Independence limitation — stated plainly

**These documents are independent of the gates. They are not independent of
the conventions the gates encode, and in one specific way that matters.**

1. **Same repository, same house style.** 36 of the 37 documents live in the
   repository that ships the gates, and share its output-rendering rules,
   its section spines, and its author.

2. **A directive that approximates DA3's own threshold.** This repository's
   rendering directives instruct agents to use "2–3 sentence paragraphs"
   (`tools/add-rendering-directives.py:121`, projected verbatim into
   `packs/architect/.apm/skills/architect-design/SKILL.md:36`). DA3 flags a
   paragraph carrying **more than three** sentences. The directive first
   entered the tree at `7ba66d542`, 2026-07-24 — before the earliest corpus
   document's last touch, so every document was authored while it existed.

   Two bounds on how far that goes. It is a claim about **instruction, not
   enforcement**: it appears in no `AGENTS.md` or `CLAUDE.md`, nothing gates
   it over `docs/architecture/**`, and `tools/check-output-readability.py`
   does not scan that tree. And the data does not look like a followed rule —
   215 one-sentence paragraphs is not what "2–3 sentences" produces, and
   15.2% exceed three outright on a corrected count.

3. **The second repository carries the directive too, but not the gates.**
   `company-intelligence-desk` has the core pack's `work-loop` skill, which
   carries the same "2–3 sentence paragraphs" line, and does **not** have
   `architect-design`. So the 15.2% versus 31.0% gap is measured between two
   trees that share the directive and differ in the gates — which is the right
   contrast for the gate question, and does not control for the directive.

4. **Same git author identity.** `git log` reports the same author on the
   documents in both repositories. The probe brief described
   `worker-runtime.md` as "by another author"; git does not support that. It
   is another project, another delivery, and another month — not another
   person. The record says so rather than claiming the stronger thing.

**What this weakens, and what it does not.** It weakens any claim that 15.2%
is what DA3 does to arbitrary architecture prose — the corpus is plausibly
shaped toward the budget. It does not weaken the finding that DA3 fires on
well-regarded architecture prose at all, because it fires in 29 of 37
documents including every one of the largest. And it *strengthens* the DA10
finding, since no directive anywhere approximates a 3,300-word bound.

## What the numbers mean — and what I will not read into them

**The primary finding is the defect, not a threshold judgement.** `DA3` does
not currently measure what its own definition says it measures. Any budget
decision taken on the shipped counter's output would have been taken on a
number 57% too low, and on a set of 58 four-sentence paragraphs when the real
set is 95. The budget question cannot be answered until the counter is fixed,
and this probe therefore does not answer it.

**`DA3` is not inert, and on a corrected count it is noisier than it looked.**
It fires on 15.2% of paragraphs and in 29 of 37 documents — every one of them
merged, reviewed and accepted. That is a lot of findings for a 🟨 gate, and it
is the strongest argument available that the budget of 3 deserves re-examining
once the counter is trustworthy. It is an argument, not a verdict: whether the
95 four-sentence paragraphs are defects is a reading nobody has done.

**`DA10` behaves as designed, and the adversarial case vindicates it.** Three
of 37 documents trip, the median document sits at 57% of the bound, and the
document the gates were conceived from is 5.7× over. That is the shape a size
trigger should have: quiet on ordinary documents, unmissable on the document
that motivated it. `DA10` is untouched by the counter defect, which lives
entirely in `DA3`'s sentence splitting. One datum deserves flagging rather
than acting on: `binder-publishing/decisions.md` clears the bound by **five
words**, so the nearest non-trip sits inside any plausible measurement noise
of the threshold. That is a reason not to move the bound by a small amount in
either direction without a stated reason, because a small move reclassifies a
document nothing else distinguishes.

**What the evidence falsifies.** Not a bound, and not a precheck — `DA3`'s
budget of 3 and `DA10`'s 3,300 words both stand, and `DA10` is corroborated.
What is falsified is `DA3`'s **implementation**: the gate under-reports
against its own stated criterion. The classification in ADR-0118 `D5` is
untouched and was not re-decided; a gate that mis-counts is still a
mechanizable gate.

## What remains uncalibrated

The seven hybrid prechecks and judgment-only `DA5` are exactly as evidenced
after this probe as before it: one document, written by the delivery that
wrote them. This probe could not reach them, because they are reviewer prose
rather than code. If their calibration matters, it needs a different
instrument — a reviewer walking the rubric over this same corpus — not a
longer run of this one.

## Filing

This record lives here, beside the ledger of the spec whose evidence it
extends: `AC-0018` and `AC-0045` rest on the single reference document at
`packs/architect/tests/skills/architect-design/testdata/telemetry-endpoint-default-design.md`,
and this is the measurement that widens that corpus. It is a sibling of
`verification-ledger.md` rather than an entry in it, because it verifies no
acceptance criterion — the spec is frozen and neither it nor the plan is
edited to record what happened here.

Two alternatives were considered and not taken. A new
`docs/product/intents/notes/` would put the record beside the intent whose
`validation_hook` it discharges, but creates a new directory and so is a
structural decision rather than a filing one. A
`docs/specs/architect-design-gate-calibration/` directory holding notes and no
spec was rejected outright: the intent's `## Decomposition` states that no
delivery artifact is committed before the measurement exists, and a spec
directory without a spec reads as a spec that went missing.

**The intent was updated and narrowed on 2026-09-20.** Its `validation_hook`
now reads `status: survived` and points at this record. Its outcome was
narrowed from `DA1`-`DA10` to `DA3` and `DA10` — the two gates this script
decides — on the strength of § *What this probe can and cannot measure*; the
seven hybrid prechecks and `DA5` are now an explicit boundary exclusion
needing their own intent and their own instrument.

## Reproduction

```sh
S=packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py
for f in $(find docs/architecture -name '*.md' | sort); do
  echo "### $f"; python3 "$S" --root . "$f"; echo "exit=$?"
done
```

The adversarial case, local clone only, nothing fetched:

```sh
D=<local-clone>/company-intelligence-desk
python3 "$S" --root "$D" "$D/docs/architecture/pydantic-ai-worker-runtime/worker-runtime.md"
```
