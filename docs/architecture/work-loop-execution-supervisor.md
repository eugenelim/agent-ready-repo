# Subsystem Design — Workspace execution supervisor

**Decision sought:** Keep `work-loop` as the public skill while a bundled,
replaceable supervisor engine owns procedure, recovery, and parallelism; Pi is
the reference native provider.
**Author:** Platform Core
**Status:** Draft
**Last updated:** 2026-10-01
**Reviewers:** `agentbundle` and Core pack maintainers

## 1. Scope and Context

| In scope | Out of scope | Why |
| --- | --- | --- |
| Task projection, capability selection, attempts, leases, recovery | Acceptance meaning | Infrastructure cannot redefine product truth |
| Sequential and parallel scheduling | Task priority policy | Skills own policy, tooling owns procedure |
| Agent, process, workspace, and journal adapters | Host UI | Presentation is an extension concern |
| Execution result production | Applying results to the canonical tree | [Product result integration](work-loop-result-integration.md) owns merge and commit |

**Goals:** a complete sequential floor, repairable mechanical state, and
equivalent accepted outcomes under sequential or parallel execution.

## 2. Structural Model

| Element | Type | Responsibility | State |
| --- | --- | --- | --- |
| Work-loop facade | Skill | Load policy, launch a provider, mediate decisions | Interaction |
| Bundled supervisor engine | Self-contained script | Default provider; invoke skills and mechanics without runtime `agentbundle` | Coordinator state |
| Task projector | Pure component | Derive tasks from criteria and plan guidance | Stateless |
| Terminal/stub guard | Pure component | Enforce `spec-plan` no-dispatch and code-mode approved-stub materialization | Stateless |
| Skill invocation adapter | Host port | Dispatch typed requests to installed skills | Attempts |
| Provider selector | Component | Validate one selected provider and its fixed capability declaration | Selected provider |
| Scheduler | Component | Derive ready tasks and choose execution mode | Active leases |
| Result-application port | Host port | Use legacy acknowledged-worktree adapter through slice 4, then protected-ref integration | Result receipts |
| Mechanical journal | Port | Store attempts, checkpoints, leases, and effect receipts | Mechanical facts |
| Effect-resolution port | Semantic port | Persist named human decisions for unknowable external effects | Resolution records |
| Runtime extensions | Adapters | Execute without control-plane writes | Private state |

```mermaid
flowchart TB
    subgraph Supervisor[Question: how does neutral procedure reach host mechanics? Zoom: component]
        Facade[Work-loop facade]
        Engine[Bundled or native engine]
        Skills[Skill invocation adapter]
        Projector[Task projector]
        Selector[Provider selector]
        Scheduler[Scheduler]
        Result[Result application port]
        Journal[Mechanical journal]
    end
    Adapters[Runtime extensions]
    Facade --> Engine
    Engine --> Skills
    Engine --> Projector
    Engine --> Selector
    Adapters --> Selector
    Selector --> Scheduler
    Scheduler --> Adapters
    Adapters --> Result
    Scheduler --> Journal
    Adapters --> Journal
```

Public choices stay orthogonal rather than becoming one larger mode enum:

| Input axis | Retained values | Effect |
| --- | --- | --- |
| Workflow policy | `light`, `full` | Select obligations and reviewer depth |
| Terminal intent | `code`, `spec-plan` | Permit implementation or stop after approval |
| Execution topology | `sequential`, `isolated`, `parallel` | Choose workspace and scheduling mechanics; degrade toward sequential |
| Invocation intent | `start`, `resume`, `recover` | Begin, rehydrate, or reconcile |

Combinations change procedure, never acceptance. Any conforming provider may
replace the bundled script; fixtures preserve every current policy/terminal
combination.

The [runtime adapter crosswalk](runtime-adapter-crosswalk.md) decomposes Pi's
packages and maps Pi, Claude Code, Codex, Conductor, and tmux to these ports.

## 3. Runtime Model

| Scenario | Trigger | Path |
| --- | --- | --- |
| Execute ready tasks | Policy selects an operation from the current approved plan revision | Normal |
| Revise plan | A new approved revision supersedes guidance | Cancel unintegrated attempts and reproject |
| Recover an attempt | Lease expires or runtime disappears | Failure and recovery |

**Provider selection.** Policy names one installed `adapter-descriptor.v1`.
The selector rejects bad identity, version, capability, conformance, or trust.
Effective authority intersects policy, request, host, and provider grants.

The grant is journaled before dispatch. Multi-provider composition waits for
two shipped providers that require it.

The scheduler derives ready tasks from dependencies, isolation, capabilities,
and leases. It never owns acceptance.

Before projection, the terminal/stub guard reads the approved plan revision.
`spec-plan` emits a terminal receipt and refuses task projection, execution
requests, or repository test writes. In `code`, each TDD task names either the
approved stub byte fingerprint plus its confined scratch compile/red receipt,
or the approved `no stub` disposition; missing or mismatched proof refuses
dispatch.

The first code-mode operation materializes the approved bytes at the declared
test path, verifies byte identity, and records the intended red before any
production edit. Recovery repeats identity and red checks after a crash; an
unexpected file or changed bytes refuse rather than merge. A reverse reader
maps these facts back to the current `plan-locked` terminal or code boundary.

Unknown external effects fail closed until a receipt or human decision resolves
them. Idempotent work may start a replacement attempt.

**Normal sequence**

1. The projector derives task contracts, operation keys, declared read/write
   sets, required access-proof mode, and code trust. Contracts also bound writes,
   network, children, and resources; omitted authority denies or uses defaults.
2. The scheduler journals a lease before provider dispatch.
3. The adapter works inside containment and returns `access-attestation.v1`.
   External effects use a stable key; acknowledgement follows receipt storage.
4. The coordinator sends the result to the active result-application port,
   which applies Product addition safety before mutation or acknowledgement.
   Slices 1–4 delegate to current worktree application and require
   `legacy-result-ack.v1`; slice 5 switches to the
   [integration boundary](work-loop-result-integration.md). Only a successful
   active-port receipt admits observations and releases the lease.

**Failure and recovery sequence**

1. A missing heartbeat expires the lease, but an attempt with an unknown
   external effect remains non-retriable.
2. After journal loss, the projector regenerates the operation key from
   semantic inputs before dispatch.
3. Reconciliation queries the external effect source by operation key. Proven
   presence restores the receipt, while proven absence permits a retry.
4. If unknowable, the supervisor reads `effect-resolution.v1`; without one it
   records `needs-decision` for named human authority.
5. `effect-confirmed` reconstructs the receipt; `do-not-retry` ends work;
   `retry-authorized` names one attempt and accepted duplicate risk. A confined
   per-key lock and revision CAS persist one checksummed claim before dispatch;
   a post-claim crash requires a new human resolution.
6. A superseded plan revision cancels unintegrated attempts and leases. Already
   integrated results and evidence remain facts and follow normal freshness.

## 4. Contracts and Invariants

| Contract | Producer → consumer | Identity | Compatibility and change authority | Failure semantics | Invariant |
| --- | --- | --- | --- | --- | --- |
| `task-contract.v1` | Projector → terminal guard, scheduler, and adapter | Subject, plan revision, terminal intent, work, task, operation; approved stub fingerprint or `no stub` disposition | Contract owners approve; unknown majors refuse; reverse reader preserves the current terminal choice | Invalid graph, authority, scratch receipt, stub identity, or proof capability refuses | `spec-plan` produces no execution request; code-mode TDD dispatch follows byte-identical approved red proof |
| `adapter-descriptor.v1` | Extension → selector | Provider, version, implementation, trust, capabilities, conformance | Contract owners approve; unknown majors refuse | Missing, duplicate, insufficient, or untrusted stays unavailable | Selection grants no authority |
| `runtime-capability.v1` | Provider → scheduler/coordinator | Capability, major, provider | Owners approve; majors match | Missing capability refuses | Grants intersect request, policy, host, provider |
| `skill-request.v1` | Engine → skill adapter | Subject, task, skill, request, attempt | Core policy owners approve; unknown skill or major refuses | Missing or interrupted skill leaves an incomplete attempt | Output is behavior or observation, never authority |
| `execution-request.v1` | Coordinator → runtime adapter | Request, attempt, operation, grant fingerprint | `agentbundle` owners approve; adapters negotiate | Unsupported restriction or capability refuses | Authority never exceeds task, policy, host, or adapter bounds |
| `execution-result.v1` | Runtime adapter → coordinator and result port | Subject, plan revision, task, attempt, operation, trees, change digest, access-attestation fingerprint | Canonical schema owns fields; readers precede writers | Partial, canceled, or unverifiable result stays isolated | Authority begins only at active-port acknowledgement |
| `access-attestation.v1` | Verified read allowlist or tracer → scheduler and result port | Attempt, source, mechanism/version, declared and observed sets, coverage, containment | Security owners approve mechanisms; unknown or unverifiable coverage becomes incomplete | Missing proof forbids parallel admission | Only enforced allowlist or complete trace is complete; otherwise serialize and require exact source |
| `legacy-result-ack.v1` | Slice-4 compatibility adapter → coordinator, subject source, evidence port | Subject, plan revision, task, attempt, operation, acknowledged worktree manifest | Canonical schema owns fields; valid only while legacy provider is active | Unsafe addition, stale authority, or ambiguous worktree refuses | Ack proves addition admission; slice 5 disables it after parity |
| `mechanical-journal.v1` | Scheduler/adapters → store/reconciler | Run and attempt IDs | `agentbundle` owners approve; stores advertise versions | Corruption or loss triggers operation-key reconciliation | Never owns completion or sole effect proof |
| `effect-resolution.v1` | Human authority via resolution port → reconciler | Subject, operation, attempt, decision, revision | Policy owners approve; records append only | Revision loss, duplicate claim, or bad authority refuses | Lock and CAS admit one durable retry claim |

Plans declare dependencies and isolation, not waves.

## 5. Data and State

| Element | State it owns | Lifecycle | Consistency requirement |
| --- | --- | --- | --- |
| Task projector | Stateless | n/a | Same inputs, same graph |
| Provider selector | Descriptor/selection | Selected, rejected, retired | Explicit ID yields one provider or refusal |
| Scheduler | Leases | Acquired, renewed, expired, released | One live lease per task and execution scope |
| Journal | Attempts, sessions, checkpoints, cached effect receipts | Append, delete, rebuild, and reconcile | Loss triggers operation-key reconciliation before dispatch |
| Effect-resolution store | Checksummed `delivery/effect-resolutions.jsonl` | Locked revision CAS | Semantic, single-claim, journal-independent |
| Terminal/stub guard | None | Re-evaluated before projection and dispatch | Same approved plan, product tree, and scratch receipt produce the same refusal or materialization permission |
| Adapter | Opaque host handles | Created, observed, retired | Handles are never semantic authority |
| External effect source | Result keyed outside journal | Created, queried | Idempotent, queryable, or non-retriable |

## 6. Deployment and Operations

| Unit | Runs as | Scaling | Observability |
| --- | --- | --- | --- |
| Bundled provider | Self-contained script inside `work-loop`; no `agentbundle` install | Sequential floor | Provider, request, operation, result, duration |
| Native provider | Pi or another selected extension behind the same facade | Declared capacity | Capabilities, degradation, conformance digest |
| Legacy result adapter | Bundled compatibility service calling current engine application | One result at a time through slice 4 | Operation, manifest, acknowledgement, refusal |
| Sequential adapter | Local adapter; containment for untrusted code | One task | Trust, roots, containment/refusal |
| Pi adapter | Trusted Pi extension; verified host containment for untrusted executable code | Session or child-session capacity | Pi session and tool event references |
| Workspace/process adapters | Contained local extensions | Host capacity | Workspace/process status |
| Mechanical journal | Local or adapter store | 1,000,000 records or 1 GiB; then refuse | Records, bytes, rebuild duration |
| Effect-resolution port | Semantic append store | One confined interprocess lock per operation key | Revision, claim winner, contention, recovery reason |

Same-process adapters are trusted infrastructure, not sandboxes. Untrusted code
requires verified host containment; otherwise execution refuses. A named human
classifies code as trusted.

## 7. Quality Scenarios and Verification

| Stimulus | Mechanism and response | Target | Verification |
| --- | --- | --- | --- |
| Provider lacks parallelism | Selector uses the sequential scheduler | 100% semantic coverage retained | Capability-degradation fixture |
| Crash after external effect | Effect-receipt invariant refuses duplicate execution | Zero automatic repeats without receipt or idempotency key | Crash-point fixture |
| Parallel schedule changes order | Task graph plus protected-ref integration preserves both non-conflicting results | Same product tree and acceptance verdict as sequential run | Paired execution and integration-permutation fixture |
| Journal is deleted after an external effect | Stable operation key reconciles the external source before dispatch | Zero duplicated effects | Crash-after-effect, delete-journal, rebuild fixture |
| External effect remains unknowable after journal loss | Durable resolution reconstructs, stops, or authorizes one linked retry | Zero dispatches without a current resolution | One fixture per resolution outcome |
| Two reconcilers claim one authorized retry | Per-key lock and revision CAS admit one claim before either dispatches | Exactly one durable winner and at most one dispatch | Concurrent claim and crash-after-claim fixtures |
| Worker tries to modify a semantic record | Write-root containment denies the control-plane path | Zero forged criteria, evidence, reports, or dispositions across adapters | Cross-adapter negative conformance fixture |
| Provider is missing, duplicated, or under-capable | Refuse before dispatch | One provider or refusal | Identity, capability, conformance, authority fixtures |
| Host proposes broader network, child-process, or resource authority | Grant intersection narrows to requested policy bounds or refuses | Zero overgranted executions and deny-all omission behavior | Network, child-process, and resource-limit property fixtures |
| Task graph or journal reaches its bound | Refuse before partial scheduling | Scheduling p95 ≤2 s; cold rebuild ≤10 s on the CI worker | Bound stress fixtures |
| Approved plan revision supersedes active guidance | Scheduler cancels unintegrated attempts and reprojects; integrated facts remain | Zero old-revision integrations after acknowledgement and zero delivery resets | Revision race, task regeneration, and evidence-preservation fixtures |
| `spec-plan` or code-mode TDD reaches dispatch | Guard stops without product writes, or materializes exact approved bytes and proves red first | Zero `spec-plan` test files and zero production edits before byte-identical red | Terminal, scratch, crash, byte-mismatch, red-to-green, and reverse-reader fixtures |
| Slice-4 supervisor returns a result | Legacy adapter delegates application and binds the acknowledged manifest | Same tree/evidence boundary as current engine | Worktree application, crash, stale-ack, and slice-5 parity fixtures |
| B reads undeclared input changed by A | Enforcement denies the read or tracing expands B's attested set; otherwise B is incomplete | Zero stale parallel integration | Cross-adapter undeclared-read fixture |

| Runtime surface | Support status | Capability declaration | Required conformance |
| --- | --- | --- | --- |
| Sequential local | Reference floor | Coordinator, scheduler, process, journal, containment | Truth-table, crash, review, forgery |
| Pi | First adapter | Agent/session plus process, journal, containment | Shared suite; session-loss recovery |
| Claude Code | Target | Agent, hook, process, journal | Shared suite; hook/subagent interruption |
| Codex | Target | Agent, tool, process, journal | Shared suite; tool interruption/refusal |
| Conductor workspace | Composition, not agent loop | Workspace plus conforming agent adapter | Shared suite; archive, resume, branch isolation |
| tmux | Mechanics, never isolation | Terminal/process plus agent and containment adapters | Shared suite; detach, server loss, process recovery |

## 8. Implementation Mapping

`contracts/delivery/supervisor-bundle.toml` is the authoritative input manifest.
`tools/build-work-supervisor.py` embeds listed schemas and standard-library-only
runtime modules into `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`,
records source and bundle digests, and rejects undeclared imports. Tests run the
artifact with repository packages absent from `sys.path`; `agentbundle` is a
builder and test host, not a runtime dependency.

Slice 1 exposes subject, approval, evidence, and content-safety subcommands to
the current engine. Slice 2 adds review services. Slice 3 adds stateless
knowledge projection. Slice 4 makes the same artifact the procedure owner.

| Element | Source owner | Build unit | Verification |
| --- | --- | --- | --- |
| Bundle manifest and builder | `contracts/delivery/supervisor-bundle.toml`; proposed `tools/build-work-supervisor.py` | Build tooling | Reproducible digest, source parity, clean-environment import fence |
| Task projector/contracts | Proposed `work_supervisor/projector.py`; `contracts/delivery/` schemas | Bundle source/contracts | Schema and graph fixtures |
| Terminal/stub guard | Proposed `work_supervisor/terminal_guard.py`; approved plan stub fields in `task-contract.v1` | Supervisor bundle | No-dispatch, scratch receipt, byte identity, crash recovery, and reverse-read tests |
| Facade and engine | `work-loop/SKILL.md` plus `scripts/work-supervisor.py` | Core pack; `agentbundle` builds/tests | Import-fence, invocation, scheduling, recovery |
| Provider protocol and scheduler | `contracts/delivery/` plus proposed `work_supervisor/supervisor.py` | Contracts, build tooling, providers | Schema parity and conformance |
| Provider selector | Proposed `packages/agentbundle/agentbundle/work_supervisor/provider.py` | Bundle source | Identity, capability, trust, and refusal tests |
| Slice-4 legacy result adapter | Proposed `work_supervisor/legacy_result.py`; delegates current `loop-cohort.py` task completion and active legacy subject source | Supervisor bundle | Application, acknowledgement, crash, and protected-ref parity tests |
| Mechanical journal | Proposed `packages/agentbundle/agentbundle/work_supervisor/journal.py` | `agentbundle` | Crash and reconciliation fixtures |
| Effect-resolution port | Proposed `packages/agentbundle/agentbundle/work_supervisor/effect_resolutions.py` | `agentbundle` | Authority, journal-loss, and one-shot retry tests |
| Runtime extensions | Proposed `packages/agentbundle/agentbundle/work_supervisor/adapters/` | Pi package and host adapters | Cross-adapter conformance |
| Result integration boundary | [Product result integration](work-loop-result-integration.md) | `agentbundle` | Merge, CAS, cancellation, and crash conformance |
| Compatibility extension | `packs/core/.apm/skills/work-loop/scripts/loop-engine.py` and `loop-cohort.py` behind the supervisor facade; `.claude/skills/work-loop/` is generated output | Core pack | [Quality scenarios](#7-quality-scenarios-and-verification) |

## 9. Decisions, Alternatives, and Risks

- **Decision:** Select one provider behind neutral capability contracts.
- **Alternative:** Move the current FSM intact. **Rejected because:** it keeps
  runtime mechanics as the portable contract.
- **Alternative:** Delegate mechanics to one hosted orchestrator. **Rejected:**
  it removes the sequential floor and adds an external dependency.
- **Alternative:** Ship multi-provider dependency resolution now. **Rejected:**
  no first-release case requires its conflict graph.
- **Risk:** Adapter capability claims drift from behavior. **Mitigation:**
  conformance tests exercise every declared capability.
- **Risk:** A leaked lease stalls work. **Mitigation:** expiry and idempotent
  reconciliation restore state without changing acceptance.
- **Risk:** Parallel workers contend for files or services. **Mitigation:** task
  contracts carry isolation constraints and the scheduler serializes when it
  cannot prove separation.

## 10. Rollout, Migration, and Reversal

The existing `work-loop` invocation remains stable. Its thin facade first
calls the bundled service CLI from the current engine, then launches it as the
procedure owner after slice-4 parity; Pi is the first native provider. The
compatibility projector imports the approved spec and plan pair through the
[authority migration](work-loop-authority-migration.md).

Each cutover bundle
also retains a reverse reader for every semantic schema introduced so far; it
projects the latest approved plan for an older engine without deleting revision
history and refuses a lossy downgrade.

During slice 4, `legacy_result.py` remains the result port and the existing
engine applies worktree changes. Slice 5 shadow-integrates the same results,
compares manifests, then switches the port and subject provider together.

| Responsibility | Owner |
| --- | --- |
| Facade, bundled provider, and cutover | Core pack maintainers; `agentbundle` maintainers own build and conformance tooling |
| Runtime adapter operation | Owning adapter maintainer |
| Rollback authorization | `agentbundle` maintainer on call after parity or recovery failure |
