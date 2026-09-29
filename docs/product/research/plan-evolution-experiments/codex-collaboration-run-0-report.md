# Codex Collaboration Run 0 Calibration Report

Run 0 is complete and failed closed on 2026-09-28. The result is non-inferential: it calibrates document-only collection mechanics, not build performance, secure confinement, model quality, or policy superiority.

## Decision

Run 0 is not released. All eight document subjects reached a terminal JSON record, but the frozen rendering gate failed because the actual compact dispatch messages were not byte-identical to the stored prompts and omitted exact response-schema enum/type details. Two subject responses also failed the frozen schema: `run-0:006` used non-enum status/risk prose, and `run-0:007` did the same plus returned an object for `task_summary`, which must be a string.

Later document collections stay closed: Run 1, Runs 2-5, Run 6, Run 7, and the holdout all remain unreleased. All inferential release flags remain false.

## Accounting

| Measure | Count |
| --- | ---: |
| Reserved ordinals | 8 |
| Subject starts | 8 |
| Terminal reports | 8 |
| Strict JSON parse pass | 8 |
| Frozen schema pass | 6 |
| Frozen schema fail | 2 |
| Candidate subprocess starts | 0 |
| Later collection releases | 0 |

## Evidence Limits

The requested route was `gpt-5.6-luna` for every subject. The served model identity, session identity, token usage, and reliable wall-clock timing are unavailable from controller-observable evidence and are not estimated.

Subjects were instructed not to use tools, web, delegation, repository inspection, messaging, code execution, shell commands, or external files. Tool use remains controller-unobservable; the record says no observed external effect, not proof of no tool use.

The hidden static registry stayed controller-only. Static grading used only parsed JSON text and the frozen registry; no subject output was executed, imported, shell-expanded, or evaluated as code.

## Slot Results

| Slot | Artifact | Task | Parse | Schema | Required atoms present | Controller deviations |
| --- | --- | --- | --- | --- | ---: | --- |
| run-0:001 | artifact-blue | disposable-1 | pass | pass | 6 | controller-dispatch-message-not-byte-identical-to-frozen-prompt, actual-transport-schema-detail-omission |
| run-0:002 | artifact-green | disposable-1 | pass | pass | 6 | controller-dispatch-message-not-byte-identical-to-frozen-prompt, actual-transport-schema-detail-omission |
| run-0:003 | artifact-amber | disposable-1 | pass | pass | 6 | controller-dispatch-message-not-byte-identical-to-frozen-prompt, actual-transport-schema-detail-omission |
| run-0:004 | artifact-slate | disposable-1 | pass | pass | 6 | controller-dispatch-message-not-byte-identical-to-frozen-prompt, actual-transport-schema-detail-omission |
| run-0:005 | artifact-blue | disposable-2 | pass | pass | 6 | controller-dispatch-message-not-byte-identical-to-frozen-prompt, actual-transport-schema-detail-omission |
| run-0:006 | artifact-green | disposable-2 | pass | fail | 6 | controller-dispatch-message-not-byte-identical-to-frozen-prompt, actual-transport-schema-detail-omission |
| run-0:007 | artifact-amber | disposable-2 | pass | fail | 6 | controller-dispatch-message-not-byte-identical-to-frozen-prompt, actual-transport-schema-detail-omission |
| run-0:008 | artifact-slate | disposable-2 | pass | pass | 6 | controller-dispatch-message-not-byte-identical-to-frozen-prompt, actual-transport-schema-detail-omission |

## Durable Evidence

- Run record: `docs/product/research/plan-evolution-experiments/codex-collaboration-run-0.json` (`sha256:9d992bfc2b62fd034a33761c7fb5e72a71fb32d570d2d7251ff33e7124df62f5`)
- Evidence index: `docs/product/research/plan-evolution-experiments/codex-collaboration-evidence-index.json` (`sha256:e77352b7398ebe11c5a8eecbb979571bc7c1a09fb009054621cc199527fba7b4`)
- Hidden registry: `.context/experiments/codex-collaboration-r1/run-0/controller/hidden-static-registry.json` (`sha256:b051b8f83b9e5d594634625b6ccdd4445796cf9e945f4b29ab51bd655db7f540`)
- Raw terminal reports and receipts: `.context/experiments/codex-collaboration-r1/run-0/`
