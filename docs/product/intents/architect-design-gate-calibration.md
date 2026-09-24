# Calibrate `DA3` and `DA10` against another author's output

- **Slug:** `architect-design-gate-calibration`
- **Status:** Fulfilled
- **Accepted:** 2026-09-20 on a clean intent-mode shaping review of this revision, after the outcome was narrowed from `DA1`-`DA10` to the two gates the script decides.
- **Level:** feature
- **Owner:** eugenelim
- **Shaping-reviewed:** 2026-09-20

## Outcome

`DA3` and `DA10` — the two document-architecture gates a script decides — measure what their own definitions state, and are calibrated against design documents their authors did not write. Any bound or implementation the evidence falsifies is corrected.

## Boundary

- Admits: running `scripts/check_document_architecture.py` over design documents authored outside the delivery that wrote it.
- Admits: correcting a `DA3` or `DA10` bound, or the implementation that decides either one, that the evidence falsifies. The implementation is named here because the probe falsified one: `DA3`'s sentence counter, not its budget.
- Admits: deciding whether `DA3` and `DA10`'s adopter-facing value rests on the script or on the reviewer checks they back.
- Excludes: `DA1`, `DA2`, `DA4`-`DA9`. The seven hybrid prechecks and judgment-only `DA5` are reviewer prose, not code, so no run of this script reaches them and no evidence it produces can calibrate them. Calibrating those needs a reviewer walking the rubric, which is different work with a different instrument.
- Excludes: adding or removing a gate identifier. The `DA1`-`DA10` set and each gate's mechanizability are fixed by ADR-0118 `D5`.
- Excludes: re-deciding which gates are mechanizable, hybrid, or judgment-only. Narrowing this intent to `DA3` and `DA10` follows that classification rather than changing it.
- Excludes: shipping telemetry to observe adopter use.
- Excludes: the hand-maintained `scripts/file_safety.py` copy the gate script imports. `docs/product/intents/shared-pack-file-projection.md` already admits it, and the architect copy is pull-request gated today.

## Owner

- architect pack maintainer.

## Unresolved questions

- Whether `DA3`'s budget stays at 3 or moves to 4. Undecidable today: the paragraph set that decides it is the four-sentence paragraphs, and the shipped counter under-reports that set, so the question cannot be answered until the counter is fixed.

## Projection

- A measurement record is the first artifact. One spec under `docs/specs/` follows only if the evidence falsifies a bound or a precheck; no delivery artifact is committed before the measurement exists.
- **What happens next, in order.** Fix `DA3`'s sentence counter first, with the defect's six-case table as its regression suite; until that lands every `DA3` number this repository holds is an under-count, including the ones in the measurement record. Only then read the four-sentence paragraphs and decide whether the budget is 3 or 4, since that set is larger than the shipped counter reports and its size is whatever the fixed counter says it is. Calibrating the seven hybrid prechecks is outside this intent's boundary and needs its own intent, since a reviewer walking the rubric is a different instrument from this script.
- **Evaluated 2026-09-20: a spec follows, on a cause this condition did not anticipate.** The measurement falsifies no *bound* and no *precheck* — `DA3`'s budget of 3 and `DA10`'s 3,300 words both stand. It falsifies `DA3`'s **implementation**: the sentence counter under-reports by 57% (81 trips where the corpus carries 127), because a sentence ending inside `**bold**`, quotes, backticks or parentheses is invisible to its boundary pattern. A gate that does not measure what its definition says it measures is the stronger reason to open a spec, not a weaker one, so the spec follows even though the literal condition reads on bounds and prechecks alone.

## Opportunity

The gates shipped resting on one design document — the telemetry endpoint-default reference — written by the same delivery that wrote the checks. An earlier five-template corpus was discarded because it measured template placeholders rather than prose, making it wider and wrong rather than wider and better. A check and the only document it has ever been run against, written together, cannot show what the check does to another author's output.

Eight of the ten gates were never reachable this way. Only `DA3` and `DA10` are decided by the script; the seven hybrid prechecks and judgment-only `DA5` live as reviewer prose in the rubric, so running the script over any corpus produces no evidence about them. This intent is scoped to the two the script decides.

A corpus was available the whole time. `docs/architecture/` holds 37 design documents across 18 independent deliveries, 20 of them subsystem-scope, every one predating the gates, and the named external candidate was reachable in an existing local clone. The scarcity this section assumed was a misreading of the criterion: it was never "outside this repository" but "outside the delivery that wrote the gates".

## Assumptions

- Whether an adopter runs `scripts/check_document_architecture.py` at all is unknown. The pack ships no telemetry, so `DA3` and `DA10`'s adopter value rests on the reviewer checks they back rather than on observed script use.


## De-risk

- **Door:** two-way. The measurement commits nothing, and a corrected threshold ships as a patch release.
- **Prototype-approach:** `validate-first`. The corpus was the probe, and the corpus is what decided whether the outcome is reachable at all.

**Riskiest assumption:** design documents written outside the delivery that wrote the gates can be obtained in enough number and variety to calibrate against.

**What would have to be true:** independent documents exist; enough of them sit at subsystem scope, where `DA3` and `DA10` actually bite; and they were authored without knowledge of the gates, so they are not already shaped to pass.

**Kill condition (predeclared 2026-09-19):** proceed only if at least five design documents authored outside this delivery can be assembled, of which at least three are subsystem-scope. Below that line the calibration is killed rather than run thin — and the honest consequence is to demote `DA3` and `DA10` to reviewer checks rather than ship a mechanical bound whose only evidence is a document its own authors wrote.

```
validation_hook:
  assumption: Enough independent design documents exist to calibrate DA3's and DA10's bounds against.
  kill_condition: Fewer than five independent documents, or fewer than three at subsystem scope, are obtainable.
  activity: Collect design documents from repositories outside this delivery and run the shipped gate script over each, recording every trip and every clean pass before any bound is changed.
  status: survived
  validated: 2026-09-20
  record: docs/specs/architect-design-document-gates/notes/gate-calibration-probe.md
```

**The named candidate is now evidence, pinned at `1003fb0`.** The subsystem design that motivated this whole effort — `docs/architecture/pydantic-ai-worker-runtime/worker-runtime.md` in the `company-intelligence-desk` repository — was present in an existing local clone and was run, with nothing fetched or cloned. It is another repository, another delivery and another month, but `git log` reports the same author identity on both, so "by another author" overstated it and is corrected here. **Re-runs must use `1003fb0`, not `HEAD`:** a rewrite of that document using `architect-design` would replace an independent document with one authored by the skill that owns the gates, and any later read of the path is no longer independent evidence.

**The kill condition was tested and did not fire.** It would have killed the calibration below five independent design documents, or below three at subsystem scope. The corpus reached 37 documents across 18 independent deliveries, 20 of them subsystem-scope. The line was not moved. `validation_hook.status` above owns the verdict; these four counts are repeated here because the kill condition is declared in this file and a reader must be able to check it against something.

**What the probe found, in one paragraph.** The corpus line clearing is not a finding about the gates. The finding is that `DA3`'s sentence counter under-reports: it requires whitespace immediately after a terminator, so a sentence ending inside `**bold**`, quotes, backticks or parentheses is invisible to it, and this repository's house style uses bold lead-in sentences constantly. `DA10` is untouched by that defect and looks sound. `DA3`'s budget cannot be judged until the counter is fixed. `AC-0018` is **not** falsified — the reference document is clean under both the shipped and the corrected counter. Eight gates were not measured, because no script reaches them.

**Every figure behind those statements lives in [`gate-calibration-probe.md`](../../specs/architect-design-document-gates/notes/gate-calibration-probe.md) and is deliberately not copied here.** Fixing the counter changes them, and a copy in this file would go stale silently while reading as current.

## Decomposition

**Not decomposable, and deliberately so.** The approach is `validate-first`: the corpus is the probe, and the probe decides whether the outcome is reachable at all. Emitting a delivery contract before it ran would have contracted work whose shape a measurement had not yet set.

**The probe ran on 2026-09-20 and needed no spec.** It assembled the corpus against the predeclared line and ran the shipped gate script over each document, recording every trip and every clean pass. It changed no shipped file and committed nothing. Its record is [`gate-calibration-probe.md`](../../specs/architect-design-document-gates/notes/gate-calibration-probe.md).

**Two cuts were anticipated, and neither fired.** A surviving verdict was to cut toward correcting the falsified bounds; a killed verdict toward demoting `DA3` and `DA10` to reviewer checks. Both are recorded here so neither is re-proposed as if it had never been considered.

**Why neither fired.** Both cuts assumed the evidence would decide something about a *bound*: survive and correct it, or kill and demote. The measurement found a defective counter instead — the bound is untested rather than wrong, because the instrument meant to test it under-reports by more than half. `DA10` is corroborated rather than corrected. Eight gates turned out to be unreachable by any script, so no cut could have touched them.

**Narrowed on 2026-09-20, which is what made the remaining work fit.** The outcome used to span `DA1`-`DA10`, and the work the evidence pointed at did not partition it — a counter repair was narrower, calibrating the seven hybrid prechecks was wider. Narrowing the outcome to `DA3` and `DA10` puts the counter repair inside it and puts the prechecks outside the boundary entirely, where they are now an explicit exclusion rather than an unowned remainder.

**No child intents, because this is the leaf.** `Level` is `feature`, so what follows is a spec under `docs/specs/`, not another intent. `Projection` carries it and its ordering.

## Source

- Mode: repo-origin
- Locator: docs/specs/architect-design-document-gates/spec.md
- Revision: c4b2f5912bad080f095ffb32d354b54c31d6c54f
- Authority: repo-origin
