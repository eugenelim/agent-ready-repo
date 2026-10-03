# Run 1 replay on headless Codex processes — `codex-headless-via-claude-r1`

- Status: **complete**. Integration status: `not-integrated`.
- Generated 2026-09-28T18:20:01.477714Z. Requested model `gpt-5.6-luna`; the controller never observed a served model identity, so no identity claim is made.
- This is a new execution-surface block. It is not pooled with the two earlier Codex collaboration reviews or with the Claude-subagent experiment.
- Source manifest digest matched the frozen value: True. Preparation validation passed: True.

## What ran

| Block | Reservations | Terminals | CLI process starts | Model starts | Process failures | Tool-use violations |
| --- | --- | --- | --- | --- | --- | --- |
| Calibration (Run 0b packets) | 8 | 8 | 8 | 8 | 0 | 0 |
| Run 1 reviewers | 144 | 144 | 144 | 144 | 0 | 0 |
| Run 1 blind adjudicators | 12 | 12 | 12 | 12 | 0 | 0 |

Run 1 reservations and terminals: 156 reserved, 156 terminal, against the required 156. Calibration is accounted separately: 8 reserved and 8 terminal, against a ceiling of 8.

## Eight-start transport calibration

All eight calibration cells passed every gate: `True`. Each had a controller-observed model start, one terminal record, exact payload byte equality, a clean exit, a strict schema parse, an exact alias, full acceptance-atom coverage, no repair or extra prose, no privacy marker, no protocol deviation, no tool call, and complete timestamps with raw event and final-message capture.

## Measures

- Cells scored: 144. Review rounds: 144. Unit of generalization: task. Claim class: non-inferential bounded case study.
- Known-defect recall (mean per cell): 0.625. Precision: 0.9413. False-positive rate: 0.0587.
- Unique findings 335, unique sustained 308, major misses 64.
- Unchanged repeats 0, same-invariant paraphrases 49, reopened absent defects 0, out-of-aperture findings 0.
- Raw output 17527 words / 239957 bytes; churn 831 words / 13920 bytes.
- Wall clock across reviewer cells 2282.6s, up to four concurrent processes.
- Tokens: input 3270524, output 77538, telemetry present in 144 of 144 cells. Missing telemetry is reported as unavailable and never counted as zero.
- Protocol deviations 0, tool-use violations 0, process failures 0.

### Per policy

| Policy | Cells | Starts | Recall | Precision | FPR | Major misses | Unique | Sustained | Out-of-aperture | Repeats | Paraphrases | Raw words | Churn words | Wall clock (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| closure | 36 | 36 | 0.625 | 0.9574 | 0.0426 | 12 | 81 | 77 | 0 | 0 | 13 | 4410 | 136 | 567.77 |
| delta-affected | 54 | 54 | 0.6111 | 0.9494 | 0.0506 | 28 | 129 | 119 | 0 | 0 | 19 | 6764 | 308 | 873.25 |
| full-replay | 54 | 54 | 0.6389 | 0.9225 | 0.0775 | 24 | 125 | 112 | 0 | 0 | 17 | 6353 | 387 | 841.58 |

### Per task

| Task | Cells | Recall | Precision | Major misses | Unique sustained | Raw words | Churn words |
| --- | --- | --- | --- | --- | --- | --- | --- |
| agentbundle-engine-stragglers | 24 | 0.5 | 0.7729 | 15 | 49 | 3151 | 545 |
| atomic-write-symlink-hardening | 24 | 0.6458 | 1.0 | 8 | 57 | 3048 | 0 |
| catalogue-corporate-trust-store | 24 | 0.5 | 1.0 | 15 | 51 | 2796 | 0 |
| decision-record-ordinal-uniqueness | 24 | 0.6667 | 0.9861 | 11 | 39 | 2445 | 39 |
| non-json-sso-guard | 24 | 0.9375 | 0.9375 | 0 | 54 | 3065 | 137 |
| pack-profiles | 24 | 0.5 | 0.9514 | 15 | 58 | 3022 | 110 |

### Per revision

| Revision | Cells | Recall | Precision | Out-of-aperture | Repeats | Reopened absent |
| --- | --- | --- | --- | --- | --- | --- |
| revision-1 | 54 | 0.5833 | 0.9444 | 0 | 0 | 0 |
| revision-2 | 36 | 0.5972 | 0.963 | 0 | 0 | 0 |
| revision-3 | 54 | 0.6852 | 0.9238 | 0 | 0 | 0 |

### Matched task-replication contrasts

Each row compares one policy against full replay inside the same task and replication.

| Task | Rep | Policy | Cells | Recall | Δ recall | Precision | Δ precision | Major misses | Raw words | Churn words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agentbundle-engine-stragglers | 1 | closure | 2 | 0.5 | 0.0 | 0.8333 | 0.1444 | 1 | 266 | 30 |
| agentbundle-engine-stragglers | 1 | delta-affected | 3 | 0.5 | 0.0 | 0.9167 | 0.2278 | 2 | 411 | 29 |
| agentbundle-engine-stragglers | 1 | full-replay | 3 | 0.5 | 0.0 | 0.6889 | 0.0 | 2 | 365 | 105 |
| agentbundle-engine-stragglers | 2 | closure | 2 | 0.5 | 0.0 | 0.75 | 0.0833 | 1 | 221 | 33 |
| agentbundle-engine-stragglers | 2 | delta-affected | 3 | 0.5 | 0.0 | 0.9167 | 0.25 | 2 | 407 | 27 |
| agentbundle-engine-stragglers | 2 | full-replay | 3 | 0.5 | 0.0 | 0.6667 | 0.0 | 2 | 321 | 79 |
| agentbundle-engine-stragglers | 3 | closure | 2 | 0.5 | 0.0 | 0.9 | 0.2611 | 1 | 324 | 36 |
| agentbundle-engine-stragglers | 3 | delta-affected | 3 | 0.5 | 0.0 | 0.7 | 0.0611 | 2 | 446 | 111 |
| agentbundle-engine-stragglers | 3 | full-replay | 3 | 0.5 | 0.0 | 0.6389 | 0.0 | 2 | 390 | 95 |
| atomic-write-symlink-hardening | 1 | closure | 2 | 0.75 | -0.0833 | 1.0 | 0.0 | 0 | 281 | 0 |
| atomic-write-symlink-hardening | 1 | delta-affected | 3 | 0.6667 | -0.1666 | 1.0 | 0.0 | 1 | 400 | 0 |
| atomic-write-symlink-hardening | 1 | full-replay | 3 | 0.8333 | 0.0 | 1.0 | 0.0 | 0 | 383 | 0 |
| atomic-write-symlink-hardening | 2 | closure | 2 | 0.75 | 0.0833 | 1.0 | 0.0 | 0 | 216 | 0 |
| atomic-write-symlink-hardening | 2 | delta-affected | 3 | 0.3333 | -0.3334 | 1.0 | 0.0 | 3 | 384 | 0 |
| atomic-write-symlink-hardening | 2 | full-replay | 3 | 0.6667 | 0.0 | 1.0 | 0.0 | 1 | 348 | 0 |
| atomic-write-symlink-hardening | 3 | closure | 2 | 0.75 | 0.25 | 1.0 | 0.0 | 0 | 262 | 0 |
| atomic-write-symlink-hardening | 3 | delta-affected | 3 | 0.6667 | 0.1667 | 1.0 | 0.0 | 1 | 415 | 0 |
| atomic-write-symlink-hardening | 3 | full-replay | 3 | 0.5 | 0.0 | 1.0 | 0.0 | 2 | 359 | 0 |
| catalogue-corporate-trust-store | 1 | closure | 2 | 0.5 | 0.0 | 1.0 | 0.0 | 1 | 274 | 0 |
| catalogue-corporate-trust-store | 1 | delta-affected | 3 | 0.5 | 0.0 | 1.0 | 0.0 | 2 | 358 | 0 |
| catalogue-corporate-trust-store | 1 | full-replay | 3 | 0.5 | 0.0 | 1.0 | 0.0 | 2 | 368 | 0 |
| catalogue-corporate-trust-store | 2 | closure | 2 | 0.5 | 0.0 | 1.0 | 0.0 | 1 | 226 | 0 |
| catalogue-corporate-trust-store | 2 | delta-affected | 3 | 0.5 | 0.0 | 1.0 | 0.0 | 2 | 371 | 0 |
| catalogue-corporate-trust-store | 2 | full-replay | 3 | 0.5 | 0.0 | 1.0 | 0.0 | 2 | 324 | 0 |
| catalogue-corporate-trust-store | 3 | closure | 2 | 0.5 | 0.0 | 1.0 | 0.0 | 1 | 215 | 0 |
| catalogue-corporate-trust-store | 3 | delta-affected | 3 | 0.5 | 0.0 | 1.0 | 0.0 | 2 | 347 | 0 |
| catalogue-corporate-trust-store | 3 | full-replay | 3 | 0.5 | 0.0 | 1.0 | 0.0 | 2 | 313 | 0 |
| decision-record-ordinal-uniqueness | 1 | closure | 2 | 0.75 | -0.0833 | 1.0 | 0.1111 | 1 | 232 | 0 |
| decision-record-ordinal-uniqueness | 1 | delta-affected | 3 | 0.5 | -0.3333 | 1.0 | 0.1111 | 2 | 284 | 0 |
| decision-record-ordinal-uniqueness | 1 | full-replay | 3 | 0.8333 | 0.0 | 0.8889 | 0.0 | 1 | 363 | 39 |
| decision-record-ordinal-uniqueness | 2 | closure | 2 | 0.5 | -0.3333 | 1.0 | 0.0 | 1 | 167 | 0 |
| decision-record-ordinal-uniqueness | 2 | delta-affected | 3 | 0.8333 | 0.0 | 1.0 | 0.0 | 1 | 306 | 0 |
| decision-record-ordinal-uniqueness | 2 | full-replay | 3 | 0.8333 | 0.0 | 1.0 | 0.0 | 1 | 336 | 0 |
| decision-record-ordinal-uniqueness | 3 | closure | 2 | 0.5 | -0.1667 | 1.0 | 0.0 | 1 | 158 | 0 |
| decision-record-ordinal-uniqueness | 3 | delta-affected | 3 | 0.5 | -0.1667 | 1.0 | 0.0 | 2 | 326 | 0 |
| decision-record-ordinal-uniqueness | 3 | full-replay | 3 | 0.6667 | 0.0 | 1.0 | 0.0 | 1 | 273 | 0 |
| non-json-sso-guard | 1 | closure | 2 | 0.75 | -0.0833 | 0.75 | -0.1389 | 0 | 265 | 37 |
| non-json-sso-guard | 1 | delta-affected | 3 | 1.0 | 0.1667 | 0.8889 | 0.0 | 0 | 371 | 38 |
| non-json-sso-guard | 1 | full-replay | 3 | 0.8333 | 0.0 | 0.8889 | 0.0 | 0 | 396 | 30 |
| non-json-sso-guard | 2 | closure | 2 | 1.0 | 0.1667 | 1.0 | 0.0 | 0 | 258 | 0 |
| non-json-sso-guard | 2 | delta-affected | 3 | 1.0 | 0.1667 | 1.0 | 0.0 | 0 | 400 | 0 |
| non-json-sso-guard | 2 | full-replay | 3 | 0.8333 | 0.0 | 1.0 | 0.0 | 0 | 366 | 0 |
| non-json-sso-guard | 3 | closure | 2 | 1.0 | 0.0 | 1.0 | 0.0 | 0 | 257 | 0 |
| non-json-sso-guard | 3 | delta-affected | 3 | 1.0 | 0.0 | 0.8889 | -0.1111 | 0 | 374 | 32 |
| non-json-sso-guard | 3 | full-replay | 3 | 1.0 | 0.0 | 1.0 | 0.0 | 0 | 378 | 0 |
| pack-profiles | 1 | closure | 2 | 0.5 | 0.0 | 1.0 | 0.0 | 1 | 284 | 0 |
| pack-profiles | 1 | delta-affected | 3 | 0.5 | 0.0 | 1.0 | 0.0 | 2 | 421 | 0 |
| pack-profiles | 1 | full-replay | 3 | 0.5 | 0.0 | 1.0 | 0.0 | 2 | 363 | 0 |
| pack-profiles | 2 | closure | 2 | 0.5 | 0.0 | 1.0 | 0.0 | 1 | 277 | 0 |
| pack-profiles | 2 | delta-affected | 3 | 0.5 | 0.0 | 0.8889 | -0.1111 | 2 | 379 | 40 |
| pack-profiles | 2 | full-replay | 3 | 0.5 | 0.0 | 1.0 | 0.0 | 2 | 374 | 0 |
| pack-profiles | 3 | closure | 2 | 0.5 | 0.0 | 1.0 | 0.1667 | 1 | 227 | 0 |
| pack-profiles | 3 | delta-affected | 3 | 0.5 | 0.0 | 0.8889 | 0.0556 | 2 | 364 | 31 |
| pack-profiles | 3 | full-replay | 3 | 0.5 | 0.0 | 0.8333 | 0.0 | 2 | 333 | 39 |

## Blind adjudication

Twelve fresh headless processes judged 86 finding statements across two stable-hash shards per task. Each adjudicator saw only randomized finding statements, evidence excerpts and its task's atoms and document revisions; policy, replication, aliases, chronology and provider source were withheld, and no registry key was placed in any payload.

- Sustained: 64. Refuted: 21. Indeterminate: 0.
- Candidates that received no judgment: 4. These are preserved and counted as not sustained; they are never imputed.

## Checkpoints

Checkpoints are preliminary and pre-adjudication: an unmatched candidate counts as not sustained until the blind adjudicators run, so checkpoint precision is a lower bound on the final figure.

- `.context/experiments/codex-headless-via-claude-r1/checkpoints/checkpoint-024.json`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/checkpoint-024.md`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/checkpoint-048.json`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/checkpoint-048.md`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/checkpoint-072.json`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/checkpoint-072.md`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/checkpoint-096.json`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/checkpoint-096.md`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/checkpoint-120.json`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/checkpoint-120.md`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/checkpoint-144.json`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/checkpoint-144.md`

Void checkpoints, superseded and kept for audit:

- `.context/experiments/codex-headless-via-claude-r1/checkpoints/void-controller-error/README.md`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/void-controller-error/checkpoint-048.json`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/void-controller-error/checkpoint-048.md`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/void-controller-error/checkpoint-072.json`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/void-controller-error/checkpoint-072.md`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/void-controller-error/checkpoint-096.json`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/void-controller-error/checkpoint-096.md`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/void-controller-error/checkpoint-120.json`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/void-controller-error/checkpoint-120.md`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/void-controller-error/checkpoint-144.json`
- `.context/experiments/codex-headless-via-claude-r1/checkpoints/void-controller-error/checkpoint-144.md`

## Failures and exclusions

- **Run 1 provider-study ordinal 1, first attempt: zero-model-start infrastructure failure** — The provider rejected the request with HTTP 400 invalid_json_schema because the frozen response schema carries `no_edit_confirmation: {const: true}` with no `type` key. The CLI emitted turn.started and then turn.failed; no assistant item and no usage record were produced, so no model start occurred. Every artifact is preserved under run-1/infrastructure-failures/001-attempt-1/. Disposition: quarantined and relaunched; permitted because the process reached no model start.
- **Controller-side transport schema adaptation applied before the Run 1 block** — An implied `type` was added beside every `const` node in the controller-side --output-schema files. Worker payload bytes, including the response_schema the worker reads, are unchanged and byte-identical to the frozen corpus. The adaptation is uniform across all 144 reviewer cells and 12 adjudicator cells and is recorded in controller/transport-schema-adaptation.json. Disposition: declared, uniform, semantics-preserving.
- **Five void checkpoints written at the wrong terminal boundary** — A shell-quoting defect in the chunk driver passed each launch window as one unsplit argument, so checkpoints 48, 72, 96, 120 and 144 were written while only 24 terminal review starts existed and no worker launched between them. No reservation, model start or terminal record was affected. The files are preserved under checkpoints/void-controller-error/ and superseded by checkpoints written at the correct counts. Disposition: voided, preserved, superseded.
- **Controller-side acceptance-atom coverage rule corrected before the calibration gate closed** — The first coverage implementation assumed every acceptance atom carried an A-prefixed id and that workers echoed the id. Four Run 0b packets use B-prefixed ids and workers echoed the atom text. The rule now accepts an id-prefix or an exact-text match. The correction is scoring-side only, applied to already-frozen response bytes, and launched no process. Disposition: corrected before the gate closed; no re-run.

## Execution-surface limitations

- The controller requested model gpt-5.6-luna and never observed a served model identity; no identity claim is made.
- Codex emitted no model field in its event stream, so only the requested model argument is on record.
- Enterprise-managed configuration requirements overrode approval_policy to OnRequest and are captured per cell as configuration notices, not model failures.
- The provider rejected the frozen response schema until an implied `type` was added beside `const`; only the controller-side --output-schema transport file changed and worker payload bytes are identical.
- Workers ran with a read-only sandbox in the repository working directory; no tool call was observed in any cell, but filesystem visibility is a standing limitation rather than a hard confinement proof.
- Wall clock includes controller orchestration overhead and up to four concurrent processes.
- Findings are a bounded, non-inferential case study; the task is the unit of generalization.

## Digests

| Artifact | SHA-256 |
| --- | --- |
| provider_adjudication_materialization | `sha256:7c4fecfe63ece6f7b07ab7047676f93071eb3a121c79bf90429e0ed7e28f8928` |
| provider_calibration_field_comparison | `sha256:1021bc58314bd1428806131095656f39be055cb6511755290e948cd12a533104` |
| provider_calibration_gate | `sha256:bcbb7a6a98b0396859a0ba9c90602861d2cf1b6c625adafbc0641a5afa896205` |
| provider_calibration_launch_order | `sha256:0b4e217f5c3638ac1133a1b97bcbd6d6038deff4ec902b6d7359cf277085ba45` |
| provider_run1_field_comparison | `sha256:e3abb3a0dfbb94434bf156391150e9a04e5e8fd0fee68ae07ca201774c78fcac` |
| provider_run1_launch_order | `sha256:44af1e803c264949273cea98da547c7b451d9794e7a984d828f081504835305b` |
| source_dispatch_manifest | `sha256:9f9e705327f8b6be5a011153cb6b21886569398d1f4b7f50e58182f04fc717f7` |
| source_hidden_defect_registry | `sha256:4db4d81b6c082d1fd73a72472623d5137ea975512d8ca15db4c87b1e02121cd8` |
| source_preparation_validation | `sha256:18e343b70773363217afe5d2342088e90beec84eefce035d72801a206c580b8b` |
| source_scoring_rules | `sha256:94c0bd50d5773baa851657e72a8606495830801c04362e72f13e30f0d9a0f9ee` |
| transport_schema_adaptation | `sha256:bc370ba474ddb3a866ba417b53e11d4ed106612fd485ee9d825f3cf88fd38408` |
| worker_payload_blinding_check | `sha256:7e632601a52f45fa646227cf028a300053619249213a451775e2b1686ed488f1` |

All artifacts live under `.context/experiments/codex-headless-via-claude-r1`.
