# Headless construction panel: five ways to hand a worker the same plan

Provider block `codex-headless-via-claude-runs2-5-r1`. Written 2026-09-29T01:29:09.139304Z. Status **complete**. Integration status **not-integrated**.

## What this measured

A worker was asked to decide how to construct a repository change, and was handed the planning material five different ways. Everything else was held equal: the same task text, the same ordered facts, the same visibility, the same requested model, the same limits, the same response contract, and the same construction request. The question was whether the packaging and the authority of the planning material change what the worker produces.

Nothing here was integrated into the repository, no tracked file was changed, and no model-authored code was run. Every command quoted in the task material is inert text.

## The six tasks

Six public task packages were used, three of medium size and three complex. Each carries a stable outcome that may not change, a set of acceptance atoms, ordered facts, and permitted and prohibited paths. Each also carries one piece of evidence the constructor discovers during construction — the same evidence in every arm — which a plan with amendment authority can respond to and a frozen plan cannot.

| Task | Size | Acceptance atoms | Stable outcome |
| --- | --- | --- | --- |
| decision-record-ordinal-uniqueness | medium | 3 | Decision-record ordinal allocation and the roster check together ensure that no two roster-visible ADR or RFC records hold the same ordinal, and that … |
| non-json-sso-guard | medium | 3 | Every Jira and Confluence read path recognises a non-JSON single-sign-on or login response as a typed guard failure before any JSON decode, and the re… |
| atomic-write-symlink-hardening | medium | 3 | The atomic write helper refuses to replace a target that is a symbolic link or that carries more than one hard link, it makes that decision before any… |
| pack-profiles | complex | 3 | Catalogue-owned profiles are enumerable through the CLI, installing a profile dispatches its packs in ordered dependency batches, and a profile manife… |
| catalogue-corporate-trust-store | complex | 3 | Catalogue fetch resolves system trust material before it dials out, a missing or unreadable corporate trust bundle is diagnosed before the network dia… |
| agentbundle-engine-stragglers | complex | 4 | Catalogue init emits structured, bounded next steps; list-targets help covers the package and adapter routes as well as the pack route; release-impact… |

Each task was run three times, giving 18 matched blocks. A block is the unit that holds everything constant; the task is the unit of generalization.

## The five treatments

1. **`baseline-cold-controlled-evolving-thin`** — Separate stable-outcome specification and thin controlled-evolving plan, fresh cold constructor. The constructor may amend the plan when the amendment records trigger evidence, the changed construction decision, affected tasks and checks, and the unchanged outcome digest.

2. **`run-2-frozen-thin`** — The same separate specification and equally thin plan, fresh cold constructor, but the plan is frozen: the constructor may record a conflict and may not amend a construction decision.

3. **`run-3-unified-contract`** — One unified contract instead of separate specification and plan files, fresh cold constructor, carrying the same ordered facts, boundaries, decisions, checks, visibility, amendment policy and outcome digest as the baseline.

4. **`run-4-narrative-expanded`** — The same separate specification and controlled-evolving plan as the baseline, fresh cold constructor, with rationale, transitions and sequencing prose added and no obligation added or removed.

5. **`run-5-same-worker-plan-build`** — The same separate specification and thin controlled-evolving plan, but the construction response continues the matching plan-author session, so the same worker still holds its planning context.

Arms one and five receive byte-identical planning material; they differ only in whether the constructor is a fresh process or the same worker that wrote the plan. Arm two differs from the baseline by exactly one clause, the amendment authority. Arm three carries the identical obligation set in one file instead of two. Arm four carries the identical obligation set with extra prose around it.

These are not claims. Each was proved mechanically over the rendered bytes before any construction started: every obligation line carries a marker, prose never does, and the marker lines were compared by digest.

| Proof | Blocks passing |
| --- | --- |
| Unified contract carries the baseline atom set exactly | 18/18 |
| Narrative expansion carries the baseline obligation set exactly | 18/18 |
| Same-worker artifact is byte-identical to the baseline artifact | 18/18 |
| Frozen arm differs from baseline in the authority clause only | 18/18 |

The narrative arm runs 1.475× to 1.586× the baseline word count while carrying the same obligations.

## How responses were measured

Every response was graded against a registry frozen before any start, which no worker ever saw. Three kinds of measure were used.

**Structural checks**, which are exact: does a proposed path fall outside the permitted paths, is every acceptance atom mapped exactly once, does the amendment echo the unchanged outcome digest, did any tool event occur.

**Lexical checks**, which are deterministic but shallow: a semantic atom counts as covered when every keyword in one of its frozen alternative groups appears in the response. This detects whether the wording is present, not whether the reasoning is right. It is the main measurement limit of this block.

**Self-audit accuracy**, which compares what a response claimed about its own drift against what the controller independently found, giving true positives, false positives and missed risks.

## Calibration

Four fresh calibration starts ran before the panel: two disposable plan-author packets and two disposable construction packets. All four passed every check — exact payload equality, an observed model start, strict schema validation, exact alias echo, no prose outside the JSON, no tool event, both timestamps, token telemetry, and one terminal record each. Gate passed: **True**.

Prior transport evidence was bound as a precondition and not pooled into any measure here. Both prior digests were verified against the integrated durable record:

| Prior artifact | Digest verified |
| --- | --- |
| handoff_json | True |
| calibration_gate | True |

## The shared baseline: 18 plan authors

Eighteen fresh plan-author processes each produced a stable-outcome specification and a thin controlled-evolving plan. All 18 returned schema-valid JSON, all 18 echoed the stable outcome digest exactly, and all 18 covered and verified every acceptance atom with a named task and a named check. One response echoed its alias one character short; it had reached a model start, so it was recorded as a protocol deviation rather than repaired. Author semantic coverage was 1.0 across the board, which means the baseline these arms build on is uniformly strong, and leaves that particular measure little room to move.

## Results by treatment

| Arm | n | Semantic coverage | Scope additions | Acceptance correct | Missed risks | Words | Output tokens | Seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline-cold-controlled-evolving-thin | 18 | 0.9889 | 0.0 | 3.1667 | 0.2222 | 351.9444 | 1172.1111 | 25.9851 |
| run-2-frozen-thin | 17 | 1.0 | 0.0 | 3.1765 | 0.1765 | 275.2941 | 1070.1765 | 24.5835 |
| run-3-unified-contract | 17 | 0.9882 | 0.0 | 3.1765 | 0.1765 | 336.5294 | 1101.7647 | 25.1841 |
| run-4-narrative-expanded | 16 | 0.9875 | 0.0 | 3.1875 | 0.125 | 329.9375 | 1166.875 | 26.4284 |
| run-5-same-worker-plan-build | 18 | 0.9778 | 0.0 | 3.1667 | 0.1667 | 252.5556 | 1930.8333 | 22.7372 |

Amendment behaviour, which is where the treatments were expected to separate most:

| Arm | Amended | Valid | Invalid | Missing | Unnecessary | Conflict recorded instead |
| --- | --- | --- | --- | --- | --- | --- |
| baseline-cold-controlled-evolving-thin | 18 | 17 | 1 | 0 | 0 | 0 |
| run-2-frozen-thin | 0 | 0 | 0 | 0 | 0 | 14 |
| run-3-unified-contract | 17 | 16 | 1 | 0 | 0 | 0 |
| run-4-narrative-expanded | 16 | 16 | 0 | 0 | 0 | 0 |
| run-5-same-worker-plan-build | 18 | 16 | 2 | 0 | 0 | 0 |

In the frozen arm an amendment is by definition unnecessary rather than valid: the arm grants no amendment authority, so the correct response to the construction evidence is a recorded conflict.

## Matched contrasts

Each contrast is computed inside a block against that block's own baseline, averaged over the three replications to give a task effect, then summarised across the six tasks. Intervals come from resampling the six task clusters and describe spread; they are not significance tests.

### `run-2-frozen-thin` minus baseline

Isolates: amendment authority (frozen plan vs controlled-evolving plan).

| Measure | Mean task effect | Task-cluster interval | Tasks favouring arm | Tasks favouring baseline |
| --- | --- | --- | --- | --- |
| semantic_coverage | 0.0111 | 0.0 to 0.0333 | 1 | 0 |
| semantic_omissions | -0.0555 | -0.1666 to 0.0 | 1 | 0 |
| contradictions | 0.1111 | 0.0 to 0.3333 | 0 | 1 |
| scope_additions | 0.0 | 0.0 to 0.0 | 0 | 0 |
| acceptance_correct | 0.0 | 0.0 to 0.0 | 0 | 0 |
| acceptance_missing | 0.0 | 0.0 to 0.0 | 0 | 0 |
| decisions_correct | -0.4166 | -0.9444 to 0.1111 | 1 | 5 |
| self_audit_true_positives | 0.1111 | 0.0 to 0.2222 | 2 | 0 |
| self_audit_false_positives | 0.2778 | 0.0555 to 0.6111 | 0 | 3 |
| self_audit_missed_risks | -0.0555 | -0.3889 to 0.2778 | 2 | 1 |
| unresolved_questions | -0.0833 | -0.5 to 0.4167 | — | — |
| raw_words | -81.4445 | -107.1667 to -56.5556 | — | — |
| output_tokens | -110.0278 | -237.5278 to 16.4444 | — | — |
| wall_clock_seconds | -1.5987 | -3.8225 to 0.5324 | — | — |

### `run-3-unified-contract` minus baseline

Isolates: packaging (one unified contract vs separate specification and plan).

| Measure | Mean task effect | Task-cluster interval | Tasks favouring arm | Tasks favouring baseline |
| --- | --- | --- | --- | --- |
| semantic_coverage | 0.0 | 0.0 to 0.0 | 0 | 0 |
| semantic_omissions | 0.0 | 0.0 to 0.0 | 0 | 0 |
| contradictions | -0.0555 | -0.2222 to 0.1111 | 2 | 1 |
| scope_additions | 0.0 | 0.0 to 0.0 | 0 | 0 |
| acceptance_correct | 0.0 | 0.0 to 0.0 | 0 | 0 |
| acceptance_missing | 0.0 | 0.0 to 0.0 | 0 | 0 |
| decisions_correct | -0.25 | -0.8611 to 0.2778 | 2 | 3 |
| self_audit_true_positives | 0.0 | 0.0 to 0.0 | 0 | 0 |
| self_audit_false_positives | 0.0 | 0.0 to 0.0 | 0 | 0 |
| self_audit_missed_risks | -0.0555 | -0.2222 to 0.1111 | 2 | 1 |
| unresolved_questions | -0.3889 | -0.7222 to -0.0555 | — | — |
| raw_words | -19.6389 | -37.4166 to 0.0556 | — | — |
| output_tokens | -83.1111 | -122.1111 to -44.3333 | — | — |
| wall_clock_seconds | -1.0779 | -2.536 to 0.4367 | — | — |

### `run-4-narrative-expanded` minus baseline

Isolates: prose volume (narrative-expanded vs thin, obligations proved equal).

| Measure | Mean task effect | Task-cluster interval | Tasks favouring arm | Tasks favouring baseline |
| --- | --- | --- | --- | --- |
| semantic_coverage | 0.0 | 0.0 to 0.0 | 0 | 0 |
| semantic_omissions | 0.0 | 0.0 to 0.0 | 0 | 0 |
| contradictions | -0.0555 | -0.1666 to 0.0 | 1 | 0 |
| scope_additions | 0.0 | 0.0 to 0.0 | 0 | 0 |
| acceptance_correct | 0.0 | 0.0 to 0.0 | 0 | 0 |
| acceptance_missing | 0.0 | 0.0 to 0.0 | 0 | 0 |
| decisions_correct | -0.6389 | -1.4722 to -0.0 | 1 | 4 |
| self_audit_true_positives | 0.0 | 0.0 to 0.0 | 0 | 0 |
| self_audit_false_positives | 0.0 | 0.0 to 0.0 | 0 | 0 |
| self_audit_missed_risks | -0.0555 | -0.1666 to 0.0 | 1 | 0 |
| unresolved_questions | -0.4444 | -0.7222 to -0.2222 | — | — |
| raw_words | -22.9167 | -39.4444 to -8.6666 | — | — |
| output_tokens | -10.4166 | -93.9722 to 59.8889 | — | — |
| wall_clock_seconds | 0.4207 | -0.3839 to 1.2516 | — | — |

### `run-5-same-worker-plan-build` minus baseline

Isolates: planning-context continuity (same worker resumed vs fresh cold worker).

| Measure | Mean task effect | Task-cluster interval | Tasks favouring arm | Tasks favouring baseline |
| --- | --- | --- | --- | --- |
| semantic_coverage | -0.0111 | -0.0333 to 0.0 | 0 | 1 |
| semantic_omissions | 0.0555 | 0.0 to 0.1666 | 0 | 1 |
| contradictions | -0.1111 | -0.3889 to 0.1111 | 2 | 1 |
| scope_additions | 0.0 | 0.0 to 0.0 | 0 | 0 |
| acceptance_correct | 0.0 | 0.0 to 0.0 | 0 | 0 |
| acceptance_missing | 0.0 | 0.0 to 0.0 | 0 | 0 |
| decisions_correct | -0.7778 | -1.6111 to -0.1111 | 1 | 5 |
| self_audit_true_positives | 0.0 | 0.0 to 0.0 | 0 | 0 |
| self_audit_false_positives | 0.0 | 0.0 to 0.0 | 0 | 0 |
| self_audit_missed_risks | -0.0556 | -0.3333 to 0.2222 | 2 | 2 |
| unresolved_questions | -0.1111 | -0.3889 to 0.1111 | — | — |
| raw_words | -99.3889 | -131.5 to -67.0 | — | — |
| output_tokens | 758.7222 | 705.7222 to 800.5556 | — | — |
| wall_clock_seconds | -3.2479 | -4.4214 to -1.9679 | — | — |

## Results by task

| Task | Size | n | Semantic coverage | Scope additions | Acceptance correct | Valid amendments | Words |
| --- | --- | --- | --- | --- | --- | --- | --- |
| decision-record-ordinal-uniqueness | medium | 15 | 1.0 | 0.0 | 3.0 | 12 | 329.4 |
| non-json-sso-guard | medium | 15 | 0.9867 | 0.0 | 3.0 | 12 | 268.8667 |
| atomic-write-symlink-hardening | medium | 14 | 0.9429 | 0.0 | 3.0 | 7 | 283.0 |
| pack-profiles | complex | 12 | 1.0 | 0.0 | 3.0 | 10 | 328.5 |
| catalogue-corporate-trust-store | complex | 15 | 1.0 | 0.0 | 3.0 | 12 | 325.2 |
| agentbundle-engine-stragglers | complex | 15 | 1.0 | 0.0 | 4.0 | 12 | 320.3333 |

## Results by task size

| Size | Tasks | n | Semantic coverage | Scope additions | Acceptance correct | Missed risks | Words |
| --- | --- | --- | --- | --- | --- | --- | --- |
| medium | 3 | 44 | 0.9773 | 0.0 | 3.0 | 0.1364 | 294.0 |
| complex | 3 | 42 | 1.0 | 0.0 | 3.3571 | 0.2143 | 324.4048 |

## Checkpoints

Immutable checkpoints were written at 30, 60 and 90 terminal construction responses. Each records transport and accounting only. No interim grading result was computed at a checkpoint, none was revealed to any later worker, and no prompt, treatment, order, sample size, grading rule or stopping rule changed because of one.

The boundary a checkpoint was written for and the number of terminals it actually observed are recorded separately below, and for the earlier boundaries they differ. The driver was restarted twice during the continuity-arm transport recovery, so the 30- and 60-terminal checkpoints were written after the panel had already passed those boundaries. The discrepancy is shown rather than smoothed over.

| At | Terminals | Model starts | Continuations | Tool violations | Schema failures | Seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 30 | 60 | 56 | 12 | 0 | 4 | 1412.37 |
| 60 | 60 | 56 | 12 | 0 | 4 | 1412.37 |
| 90 | 90 | 86 | 18 | 0 | 4 | 2145.9 |

## Exact accounting

| Stage | Expected | Reservations | CLI starts | Model starts | Continuations | Terminals | Tool violations | Schema failures | Process failures | Zero-start quarantines | Seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| authors | 18 | 18 | 18 | 18 | 0 | 18 | 0 | 0 | 0 | 0 | 411.85 |
| calibration | 4 | 4 | 4 | 4 | 0 | 4 | 0 | 0 | 0 | 0 | 36.19 |
| construction | 90 | 90 | 101 | 86 | 18 | 90 | 0 | 4 | 4 | 11 | 2145.9 |

Totals: 112 reservations, 123 CLI process starts, 108 controller-observed model starts, 18 continuations, 112 terminal records, 11 zero-model-start infrastructure failures quarantined, 0 tool-use violations, 2593.94 seconds of controller wall clock. Every stage reconciles: **True**.

No response was repaired, retried or replaced after a model start. 4 construction cells returned no response at all and are excluded from the measures; they are named below and counted above. Every response that did return bytes is graded exactly as returned. Token telemetry:

| Stage | Rows with telemetry | Rows without | Input tokens | Cached input | Output tokens |
| --- | --- | --- | --- | --- | --- |
| authors | 18 | 0 | 406768 | 201216 | 17202 |
| calibration | 4 | 0 | 86436 | 0 | 291 |
| construction | 86 | 4 | 2497646 | 1754368 | 111446 |

A field the controller could not observe is reported as unavailable and counted. Nothing missing was recorded as zero. The served model identity was not exposed by the surface in any of 112 records, so the requested model `gpt-5.6-luna` is the only model fact on record and no identity claim is made.

## Failures and deviations

| Where | Ordinal | Kind | Handling |
| --- | --- | --- | --- |
| plan author | 5 | alias-echo-inexact | recorded as a protocol deviation; the response reached a model start and was therefore terminal, so it was not repaired, retried or replaced |

Rows excluded from the measures: 4. A response that reached a model start and returned bytes is graded exactly as returned and is never excluded. The only exclusions are cells that returned no response at all; they are named, counted in the accounting, and never imputed a value.

### Continuity-arm transport quarantine

`codex exec resume` accepts neither `-s` nor `-C`; the continuity arm's first dispatch was rejected by the CLI argument parser before any request was built. Exit status non-zero, zero jsonl events, no session identity, no assistant item, no usage record, no final message, in every quarantined cell. 11 cells were quarantined and relaunched under byte-identical payloads. A zero-model-start infrastructure error may be quarantined and relaunched once under the same frozen payload. No quarantined cell reached a model start, so no terminal response was retried, repaired or replaced. The read-only sandbox is now requested through `-c sandbox_mode="read-only"` and the working directory through the child process cwd. The sandbox and working directory a worker sees are unchanged; only the flag spelling differs on the continuation transport.

### Four cells that returned nothing

`pkill -f construct.py` matched only the Python driver. The four `codex exec` children then lost the stdout pipe they were streaming to and died without writing a final message. A cell that may have reached a model start may not be retried or replaced. The controller cannot rule out a model start here, so the conservative reading applies and no later start was made on these four reservations. A quarantine is legal only when a model start provably did not occur. These four cells had been running for up to twenty seconds against a typical response time of sixty to one hundred and fifty seconds, so a model start is plausible.

Effect on the design: pack-profiles replication 1 loses three arms and atomic-write-symlink-hardening replication 3 loses one. Matched contrasts skip an incomplete pair and report the dropped-pair count rather than imputing a value. The kill time was set by the continuity-arm transport bug, which is unrelated to the content of any cold-arm response, so the exclusion is not correlated with response content.

| Ordinal | Task | Replication block | Arm |
| --- | --- | --- | --- |
| 50 | atomic-write-symlink-hardening | atomic-write-symlink-hardening\|r3 | run-4-narrative-expanded |
| 51 | pack-profiles | pack-profiles\|r1 | run-3-unified-contract |
| 53 | pack-profiles | pack-profiles\|r1 | run-2-frozen-thin |
| 54 | pack-profiles | pack-profiles\|r1 | run-4-narrative-expanded |

### One contaminated continuity session

While diagnosing the continuation transport failure, the controller sent one probe turn to a live plan-author session to establish whether `codex exec resume` works and whether planning context is retained. The probe asked only for the literal object {"ok":true}. This affects exactly 1 cell: construction ordinal 78, block `agentbundle-engine-stragglers|r1`. The cell is kept and graded with every other cell. The probe added one trivial unrelated exchange to that session's history and no task, treatment, grading or interim result content. The contamination is reported rather than hidden, and the affected cell is named so a reader can discount it.

The probe also produced the block's clearest evidence that continuation works: input_tokens 45892 with cached_input_tokens 9984 on the resumed session, which is the controller's evidence that a resumed session genuinely carries the plan-author context forward rather than starting clean.

### One voided checkpoint

The 30-terminal checkpoint counted 11 continuity-arm cells as terminal responses when they were zero-model-start CLI argument rejections. Those cells were quarantined and relaunched under the same frozen payload bytes, so the checkpoint's terminal count, model start count and schema-failure count no longer describe the panel. The original bytes are preserved here unchanged rather than edited, and a corrected checkpoint is written at the same 30-terminal boundary. Nothing about the design, prompts, treatments, order, sample size, grading or stopping rules changed.

## Grading amendment

A contradiction marker that appears verbatim in the worker-visible material a response was given — its block's task facts, acceptance atoms, stable outcome, evidence trigger, or the obligation set carried by its planning artifact — is void for that block. A response quoting its own input faithfully would otherwise be scored as contradicting the stable outcome.

Two collisions were found mechanically. 'pack route only' is verbatim worker-visible fact F2 for agentbundle-engine-stragglers, describing the present behaviour the change fixes. 'unbounded' was written into specification atoms by plan authors stating the obligation in negated form. Scoring either as a contradiction would produce a false positive on faithful work. The rule is mechanical, with 0 hand-picked exceptions. It voided 4 marker instances across 4 blocks and left 101 live. It was applied before the first construction start, after the plan authors had run. Both counts are reported in the row-level data so its effect is visible.

## Limits

- The controller requested model gpt-5.6-luna and never observed a served model identity. No identity claim is made.
- Grading of semantic coverage, contradiction and unsupported promises is lexical: a frozen keyword group either appears in the response text or does not. It measures presence of wording, not correctness of reasoning, and it is the main measurement limit of this block. Scope drift and acceptance mapping are structural checks and do not share this limit.
- Two frozen contradiction markers collided with worker-visible text and were voided before any construction start by a mechanical rule. Both the as-frozen and the corrected contradiction counts are reported.
- The narrative expansion in the fourth arm is controller-generated meta-prose keyed to item identifiers. It isolates prose volume with obligations proved equal; it does not test the quality of human- or model-written rationale.
- Plan-author sessions were persisted rather than ephemeral, because the continuity arm has to resume them. Every construction cold start was ephemeral.
- Workers ran in a read-only sandbox in the repository working directory. No tool call was observed in any cell, but repository visibility remains a standing limitation rather than a confinement proof.
- Wall clock includes controller orchestration overhead at up to four concurrent processes and is not a clean per-response latency measure.
- Eighteen blocks are six tasks by three replications. The task is the unit of generalization; intervals resample six task clusters and are descriptive spread, not significance tests. Findings are non-inferential.
- The plan-author baseline scored at ceiling on semantic coverage in every block, which compresses the room any arm has to improve that particular measure.
- Four construction cells returned no response because the controller terminated the driver process mid-flight while fixing the continuity-arm transport. A model start could not be ruled out, so they were closed terminal and not relaunched. They are excluded from the measures and leave two blocks with incomplete arm sets.
- The continuity arm reaches the CLI through `codex exec resume`, which accepts neither the sandbox flag nor the working-directory flag used by a cold start. The same read-only sandbox and working directory were requested through configuration and the child process working directory, so what a worker sees is equal across arms, but the invocation is not byte-identical and that is a transport difference beyond the intended treatment.
- One plan-author session received a single trivial controller probe during that diagnosis, which contaminates exactly one continuity-arm cell. The cell is named and kept; the probe carried no task, treatment, grading or interim-result content.

## What is on disk

Working artifacts, including every payload, raw event stream, final-message byte record, reservation and receipt, are under `.context/experiments/codex-headless-via-claude-runs2-5-r1`. The fixed JSON record beside this report carries the row-level data, every digest, and the full accounting.
