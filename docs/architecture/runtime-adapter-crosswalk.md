# Runtime mechanism crosswalk

**STATUS: PLANNED** — runtime adapters, the capability selector, and Pi
conformance are later slices of the
[acceptance-centered work loop brief](../product/briefs/acceptance-centered-work-loop.md#proposed-delivery-slices)
(slices 6 and 7), under [ADR-0144](../adr/0144-work-loop-supervisor-owns-procedure.md).
Only the supervisor-realization column below is current.

The work-loop supervisor reaches an agent runtime only through typed request
and result contracts, so a runtime changes how a step is hosted and never what
acceptance means. This page maps each concern to its contract target and to the
supervisor's current realization.

How packs are projected into runtimes is in
[distribution-routes.md](distribution-routes.md). The comparison of Pi, Claude
Code, Conductor, and tmux mechanisms is research input in
[`runtime-mechanism-comparison.md`](../product/research/runtime-mechanism-comparison.md).

## 1. Ownership

The [execution supervisor](work-loop-execution-supervisor.md) owns the
contracts. No runtime owns acceptance meaning or becomes mandatory. Pi is a
reference decomposition and optional compatibility target: Core does not
import, bundle, install, select by default, or depend on Pi.[^1]

## 2. Contract targets and supervisor realization

| Concern | Contract target | Supervisor realization |
| --- | --- | --- |
| Policy and context | Skills state obligations | `SKILL.md` states obligations; procedure lives in the supervisor |
| Agent loop | Runtime extension | The host agent issues one supervisor request at a time[^2] |
| Tool and model binding | Provider capability | Host is implicit |
| Transport | Request and result contracts | `work-supervisor.py` CLI requests and results[^2] |
| Recovery state | Replaceable journal | State re-derived from `HEAD`, the product ref, and `delivery/`; the journal is advisory[^3] |
| Parallelism | Scheduler plus workspace and agent capabilities | Sequential; parallel scheduling is `STATUS: PLANNED` in [loop-parallelism.md](loop-parallelism.md) |
| Verification and review | Evidence and reports | Gates and reviewer results recorded as delivery records |
| Security | Shared file and process confinement | Confined-file and process-spec helpers in the `work-loop` scripts[^4] |

## 3. Adapter invariants

**STATUS: PLANNED.** No runtime adapter, selector, shared adapter suite, or Pi
conformance environment exists in the tree.[^5] The supervisor's
[§ 9](work-loop-execution-supervisor.md) hands runtime adapters to this
mapping as later slices. Each row is a target for those slices.

| Invariant | Enforcement target |
| --- | --- |
| Runtime sophistication cannot change delivery meaning | Every adapter passes the shared semantic and recovery suite |
| A workspace or terminal is not a sandbox | Untrusted execution requires a verified host containment capability |
| Session loss cannot erase acceptance facts | Sessions and journals contain only repairable mechanical state (current for the supervisor journal; see recovery above) |
| Missing runtime capabilities degrade safely | The selector chooses the sequential floor or refuses before dispatch |
| Provider-specific APIs do not enter skill policy | Typed requests and results terminate at the adapter boundary |
| Optional compatibility cannot become a critical-path dependency | Pi conformance runs from a separately installed environment; supervisor cutover, result integration, parallelism, and legacy removal pass with Pi absent |

## 4. Verification authority

No runtime support matrix exists. Support status, capability declarations, and
required conformance are defined with the adapter slices; until then this page
adds no runtime-specific proof obligation.

## Evidence

[^1]: [`work-loop-execution-supervisor.md`](work-loop-execution-supervisor.md) § 6: the supervisor never imports or executes anything from `tools/`, `packages/`, or another installed package. No script under `packs/core/.apm/skills/work-loop/scripts/` references Pi.

[^2]: `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`.

[^3]: `packs/core/.apm/skills/work-loop/scripts/_supervisor_journal.py`; [supervisor §§ 4–5](work-loop-execution-supervisor.md).

[^4]: `_file_safety.py`, `_confined_mutation.py`, and `_process_safety.py` in `packs/core/.apm/skills/work-loop/scripts/`.

[^5]: Brief slice table: [slices 6 and 7](../product/briefs/acceptance-centered-work-loop.md#proposed-delivery-slices).
