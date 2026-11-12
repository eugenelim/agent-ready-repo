# Plan: Discovery supervisor

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** E1 core/gates specs and plans; discovery-loop SKILL.md, gate-state-machine.md and sidecar-schema.md; core lint-traceability.py docstring and main(); unattended-delivery-runner pages 05 and 03c.

> **Plan contract:** Touches, Tests and Done when govern completion. Design and approach are working material; spec contract changes require amendment. Execution evidence belongs in `notes/verification-ledger.md`.

## Approach

Build the installed script and manifest around the E1 seam, then add routing, gate answers and recovery tests. Use real Git fixtures and the existing lint as external oracles. Instructions, eval, how-to and release registrations follow the behavior they describe.

Each task is a bounded review unit; T1–T3 are DEEP and reviewed separately. The draft's unresolved integrity, payload, bounds and binding questions are approval prerequisites, not implementation defaults.

## Constraints

- ADR-0162 and spec:supervisor-manifest-contract own the six commands and envelope; `answer` stays outside the manifest command list.
- RFC-0116 D1 preserves worker judgment and slot ownership; its broader tier/ticket scope is narrowed by the spec's settled decisions.
- ADR-0157 D4 governs every approval pause, including G3; no automatic Ready write is authorized.
- eugenelim holds all owner roles; E1 owns shared E3 routing/prerequisites.
- This plan introduces no new lint and changes no work-loop pinned script.

## Construction tests

Use subprocess-driven temporary repositories, real commits, a pseudo-terminal for answer tests and fresh processes for resume checks. Keep pack tests inside their pack boundary; repository-content comparisons belong in registered repository tests.

The disconfirming source probe is the read of lint-traceability.py's docstring and `main()`: default orphans and unexpected checker errors return 0. T2 therefore measures exit parity, not a claim that exit 0 proves the graph complete.

## Durable-output map

| Output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Runtime/instructions | T1, T2, T3, T4, T5 | pack tests, live receipt, instruction checks | behavior and resume pass |
| User procedure | T6 | guide and install checks | one indexed how-to |
| Release | T5, T7 | eval, versions, build, fragment, registrations | all release gates pass |
| Architecture | T8 | page 05 comparison | Ready row agrees with spec |

## Design (LLD)

### Interfaces and installed dependencies

The new script path is `packs/product-engineering/.apm/skills/discovery-loop/scripts/discovery-supervisor.py`; the manifest sits at the skill root. T1 discovers reusable E1 code only after the dependencies land, using their contracts as the oracle rather than guessing exported helpers.

Use subprocess invocation of repository-installed `work-loop/scripts/lint-traceability.py` with `--root` and, at G2/G3, `--strict`. Resolve repository core independently of the supervisor's own install scope; pin the resolved executable inputs and disable bytecode writes with a scrubbed environment.

The E1 reuse packaging is implementation-discovered: compare any carried standard-library seam with E1 fixtures without runtime core imports. Stop and amend if reuse requires a new public dependency or changes the protected contract.

Owned by: T1, T2

### Routing and sidecar reads

Build a deterministic phase reducer over committed slot state, meta counters and consumed answers. Worker result validation compares the pre-attempt revision and changed paths with the issued request before recording completion.

Keep the discovery schema as the slot authority and use its existing names rather than duplicate schema prose. A request's node/phase selects the task; the agent's judgment is data in its bounded result, never authority to skip a gate.

Trace to AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0018. The exact gate artifact/write inventory remains the spec's approval prerequisite.

Owned by: T2

### Answers and durable state

Adapt E1's record binding from the pair to the discovery input inventory. Preserve committed request identity and compare answer, parked revision and current input before consuming a verdict.

Record the supplied verdict row without promoting slots; a worker's later authorized transition is checked against that answer. Keep answer persistence and verdict consumption separately replay-safe so a kill between them does not duplicate either record.

ADR-0157 D4 applies to every consent, including the cap and G3. The post-G3 human-decision is a parked handoff, not another approval or a Ready-writing shortcut.

Trace to AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0029, AC-0030. Exact answer payload and anchored-log integration remain approval prerequisites in the spec.

Owned by: T3

### Recovery and protected content

Reuse E1's first-parent history checks, pin/ledger/protected-content refusal order and request-local replay. Exercise sidecar disagreement as a refusal rather than repairing it from a preferred source.

Protected Ready tests compare committed records and content, including a matching approve and an earlier unauthorized Ready edit by the same named author. Record authorship never substitutes for a matching answer.

Trace to AC-0025, AC-0026, AC-0027, AC-0028, AC-0031, AC-0043. Test status and gates through fresh processes as read-only views using the shared contract.

Owned by: T1, T3

## Tasks

### T1: Installed script admits and describes a tracked discovery

**Depends on:** none

**Touches:** `packs/product-engineering/.apm/skills/discovery-loop/scripts/`, `packs/product-engineering/.apm/skills/discovery-loop/supervisor.toml`, `packs/product-engineering/tests/`

**Tests:**

Mode: TDD; temporary Git repositories and E0 schema validation.

- AC-0001, AC-0002: preserve committed intent bytes; create the tracked sidecar in admission; test each invalid-adoption member with before/after tree and commit comparisons.
- AC-0003, AC-0004: drive each subject verb with traversal, symlink swaps, non-regular files and missing sidecars; include a valid confined path.
- AC-0005, AC-0006, AC-0007: validate the actual manifest and captured envelopes against E0; drive all kinds including the post-G3 human-decision and compare the captured set with the manifest.
- AC-0008: repeat next while a lens request is pending; verify one request identity across separate processes and refuse unsupported width arguments.
- AC-0043: mutate each pinned input, including core lint and layout, then restore it; combine pin and ledger faults to test precedence and verify installation-record mismatch at admission.

**Done when:** T1 tests pass with the installed entry point and manifest.

### T2: Phase routing and real lint checks govern each next request

**Depends on:** T1

**Touches:** discovery-loop scripts, product-engineering pack tests

**Tests:**

Mode: TDD; table-driven sidecars and real core lint subprocesses.

- AC-0009, AC-0010, AC-0011: build one valid fixture per gate-ladder phase; mutate schema stamp, status and output paths separately, including untracked additions and forbidden slot promotion.
- AC-0012, AC-0013: use two writer definitions and independent reconcile profiles; reuse each writer profile as a negative case, remove each required reviewer result, and exercise unavailable reviewers without silently skipping them.
- AC-0014, AC-0015, AC-0016: run the existing lint on a clean graph, dangling edge, cycle, orphan and UNREACHABLE subtree in both modes; compare actual exits with supervisor records and consent availability.
- Check nonfatal unresolved cross-repository references and empty graphs separately; neither fixture proves semantic validity (AC-0014).
- AC-0017: exercise user-supervisor/repository-core and repository-supervisor/repository-core layouts, then remove only repository core while leaving a user-scope copy.
- AC-0018: test round below/at/above cap and a confirmed extension with a new bound; resume retains counters and offers no free extra round.

**Done when:** T2 tests pass without a replacement lint or a mocked lint exit oracle.

### T3: Human answers, protected records and restart preserve the gate

**Depends on:** T2

**Touches:** discovery-loop scripts, product-engineering pack tests

**Tests:**

Mode: TDD; real commits, pseudo-terminal answers and interruption injection.

- AC-0019, AC-0020, AC-0021: enumerate verdicts at G0/G1.5/G2/G3; malformed, wrong-request, wrong-digest, pre-park and absent answers fail; each valid answer produces one verdict row after replay.
- AC-0022: drive every transition using the gate-state-machine as oracle, including constraint re-convergence, confirmed impact before steer, alternatives, abandon, defer/resume and bound extension.
- AC-0023, AC-0024: compare record fields with E1, test no terminal, failed confirmation, duplicate/conflicting answers, and kills before answer commit and after commit before consumption.
- AC-0025, AC-0026: kill before the step commit and after it but before attempt closure; fresh status/next/report retain the request and exactly one completed step.
- AC-0027, AC-0028: alter sidecar, ledger, verdict row and answer independently; edit Ready before G3 answer under both matching and different Git authors; only recorded authority affects the result.
- AC-0029, AC-0030: snapshot slot bytes across every supervisor-owned write; G3 approve leaves brief Draft and parks the stated human-decision; a later explicit human/agent Ready commit permits acknowledgement, while stale binding does not.
- AC-0031: send control, escape, bidi, oversized and malformed data through every visible channel, including lint stderr; compare sanitization with E1's corpus.

**Done when:** T3 tests pass, including the resolved spec integrity prerequisites.

### T4: Pack integration and a live discovery prove resume

**Depends on:** T3

**Touches:** `packs/product-engineering/tests/`, `docs/specs/discovery-supervisor/notes/verification-ledger.md`

**Tests:**

Mode: integration plus manual QA.

- AC-0032: run the pack suite under both supported install layouts, using actual installed scripts and isolated module names; include refusal coverage for every verb and side-by-side E1 operation.
- AC-0033: record one real G0–G3 session with human answers; lose context at an open gate and resume from status alone, comparing request IDs and committed record counts.

**Done when:** the pack runs pass and the live receipt records T4's observations.

### T5: Instructions and eval exercise the session route

**Depends on:** T3

**Touches:** discovery-loop SKILL.md, references/gate-state-machine.md, discovery-lead agent, discovery-loop/evals/evals.json, discovery-loop/evals/eval_queries.json

**Tests:**

Mode: goal-based content and eval checks.

- AC-0034: compare the owning instruction table to the actual manifest/result schemas; check human-only answer, status-first resume, generic file-tool wording and one command per verb.
- Check the edited source sections remove the conflicting no-engine/supervisor-role wording while retaining prose fallback and existing integrity controls; added pack lines contain no internal citations (AC-0034).
- AC-0035: run an eval case requiring parked resume without agent-written consent; assert the expected behavior cites shipped instructions rather than the draft spec.

**Done when:** T5 checks pass and the eval harness contains the exercised case.

### T6: One indexed how-to covers adoption and human handoff

**Depends on:** T4, T5

**Touches:** `guides/product-engineering/how-to/`, guide index, repository-level guide test and its registrations

**Tests:**

Mode: goal-based guide checks, outside pack tests.

- AC-0036: follow the guide in both installation layouts through adopt, park, separate-terminal answer, context-loss resume and post-G3 Ready choice; check manual ticket intake and Tier-A-only scope.
- AC-0037: run lint-guide-titles.py, check-guide-index.py and lint-guides-no-repo-only-refs.py; use a registered repository test for any content pins.

**Done when:** T6 checks pass with exactly one discovery how-to.

### T7: Minor release and registered checks are complete

**Depends on:** T4, T5, T6

**Touches:** product-engineering pack.toml and .claude-plugin/plugin.json, self-host projections, docs/product/changelog.d/, test-boundary and parity registrations

**Tests:**

Mode: goal-based release verification.

- AC-0038: compare both version files with the next minor above fetched main at release time; no literal version is pinned in this plan.
- AC-0039: run make build-self and the self-host drift check; regenerate projections from source rather than editing them.
- AC-0040: run python3 tools/changelog.py validate with the release fragment.
- AC-0041: run tools/lint-pack-test-boundary.py and tools/lint-ci-parity.py; discover the new suite's required inventory/workflow registrations and update their owning sources, including build_gate_chain.py/test_build_gate_chain.py when repository tests join that chain.
- Record targeted pack tests and make precheck with tests against origin/main; verify no work-loop pinned source or projection changes (AC-0041).

**Done when:** T7 checks pass and the verification ledger records their results.

### T8: Page 05 states the Ready boundary correctly

**Depends on:** T3

**Touches:** `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`

**Tests:**

Mode: goal-based comparison of the discovery session row with the spec.

- AC-0042: replace the row assigning verdict/slot/Ready writes to sibling report with the separate answer-recording, worker slot-transition and human or explicitly requested session-agent Ready roles.
- Check the row requires a committed G3 approve before Ready and cites ADR-0157 D4 without claiming commit authorship proves authority (AC-0042).

**Done when:** T8's page comparison passes.

## Rollout

Ship after the three dependency specs, through the product-engineering minor release. Existing plain intents require explicit adoption; prose discovery remains available. Rollback removes the optional script entry path without deleting committed discovery records.

## Risks

The spec owns accepted risks and unresolved approval prerequisites. Test registration and cross-scope lookup are implementation risks checked by T1, T4 and T7; a failed prerequisite stops implementation rather than weakening a gate.

## Changelog
