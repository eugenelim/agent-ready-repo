# Calibrate the document-architecture gates against another author's output

- **Status:** Accepted
- **Level:** feature

## Outcome

The `DA1`-`DA10` document-architecture gates are calibrated against design documents their authors did not write, and any threshold or precheck that evidence falsifies is corrected.

## Boundary

- Admits: running the shipped gates over design documents authored outside the delivery that wrote them.
- Admits: correcting a `DA3` or `DA10` threshold, or a hybrid gate's structural precheck, that the evidence falsifies.
- Admits: deciding whether `DA3` and `DA10`'s adopter-facing value rests on the script or on the reviewer checks they back.
- Excludes: adding or removing a gate identifier. The `DA1`-`DA10` set and each gate's mechanizability are fixed by ADR-0118 `D5`.
- Excludes: re-deciding which gates are mechanizable, hybrid, or judgment-only.
- Excludes: shipping telemetry to observe adopter use.
- Excludes: the hand-maintained `scripts/file_safety.py` copy the gate script imports. `docs/product/intents/shared-pack-file-projection.md` already admits it, and the architect copy is pull-request gated today.

## Owner

- architect pack maintainer.

## Unresolved questions

- Where design documents written by another author can be obtained, given the repository holds one such document today.
- Whether a falsified threshold is corrected in place, or the gate is demoted to a reviewer check it can no longer mechanically decide.

## Projection

- A measurement record is the first artifact. One spec under `docs/specs/` follows only if the evidence falsifies a bound or a precheck; no delivery artifact is committed before the measurement exists.

## Opportunity

The gates shipped resting on one design document — the telemetry endpoint-default reference — written by the same delivery that wrote the checks. An earlier five-template corpus was discarded because it measured template placeholders rather than prose, making it wider and wrong rather than wider and better. A check and the only document it has ever been run against, written together, cannot show what the check does to another author's output.

## Assumptions

- Whether an adopter runs `scripts/check_document_architecture.py` at all is unknown. The pack ships no telemetry, so `DA3` and `DA10`'s adopter value rests on the reviewer checks they back rather than on observed script use.


## De-risk

- **Door:** two-way. The measurement commits nothing, and a corrected threshold ships as a patch release.
- **Prototype-approach:** `validate-first`. The probe is assembling the corpus, and the corpus is the thing that decides whether the outcome is reachable at all.

**Riskiest assumption:** design documents written outside the delivery that wrote the gates can be obtained in enough number and variety to calibrate against.

**What would have to be true:** independent documents exist; enough of them sit at subsystem scope, where `DA3` and `DA10` actually bite; and they were authored without knowledge of the gates, so they are not already shaped to pass.

**Kill condition (predeclared 2026-09-19):** proceed only if at least five design documents authored outside this delivery can be assembled, of which at least three are subsystem-scope. Below that line the calibration is killed rather than run thin — and the honest consequence is to demote `DA3` and `DA10` to reviewer checks rather than ship a mechanical bound whose only evidence is a document its own authors wrote.

```
validation_hook:
  assumption: Enough independent design documents exist to calibrate DA3's and DA10's bounds against.
  kill_condition: Fewer than five independent documents, or fewer than three at subsystem scope, are obtainable.
  activity: Collect design documents from repositories outside this delivery and run the shipped gate script over each, recording every trip and every clean pass before any bound is changed.
  status: to-validate
```

**One named candidate, unverified.** The ~1,930-line subsystem design that motivated this whole effort — `docs/architecture/pydantic-ai-worker-runtime/worker-runtime.md` in the `company-intelligence-desk` repository — is by another author, in another repository, and predates every gate. It is the adversarial case the gates were built from descriptions of but have never actually been run against. It has not been fetched or verified from here, so it is a named candidate, not evidence.

**Verdict:** pending — the corpus has not been assembled. The predeclared line above is fixed.

## Decomposition

**Not decomposable yet, and deliberately so.** The approach is `validate-first`: the corpus is the probe, and the probe decides whether the outcome is reachable at all. Emitting a delivery contract now would contract work whose shape is set by a measurement nobody has taken — and if the kill condition fires, the delivery is not a smaller version of this spec but a different one (demote `DA3` and `DA10` to reviewer checks).

**What runs first, and it is not a spec.** Assemble the corpus against the predeclared line — five independent design documents, three at subsystem scope — and run the shipped gate script over each, recording every trip and every clean pass. That measurement record is the first artifact. It needs no spec: it changes no shipped file and commits nothing.

**Then one of two cuts, chosen by the result.** A surviving verdict cuts toward correcting the falsified bounds, and only the bounds the evidence actually falsified. A killed verdict cuts toward demotion, which is a smaller change to the rubric homes and the script rather than a threshold edit. Recording both cuts here keeps the killed branch from being re-proposed as if it had never been considered.

## Source

- Mode: repo-origin
- Locator: docs/specs/architect-design-document-gates/spec.md
- Revision: c4b2f5912bad080f095ffb32d354b54c31d6c54f
- Authority: repo-origin
