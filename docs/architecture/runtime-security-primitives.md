# Runtime security primitives

Filesystem and process confinement live in versioned, reusable work-loop
libraries, not in skill procedure. A trusted adapter passes untrusted paths,
argv values, and payloads to a primitive, and the primitive refuses on any
uncertainty with a stable redacted code.

A library is not a sandbox: only a
verified host sandbox or restricted principal confines untrusted code, and the
sequential adapter refuses untrusted code when the host cannot supply one. The
execution supervisor sits on top of these primitives and assumes a worker may
write files directly, so its own controls (§ 7) detect naive tampering and
nothing more.

## 1. Seven components share five contracts

| Component | Responsibility | State | Source (under `packs/core/.apm/skills/work-loop/scripts/`) |
| --- | --- | --- | --- |
| Capability issuer | Grants operations over an exact root and action set; a child grant is never broader than its parent | Active grants | `_security_capability.py` |
| Path confinement | Validates, opens without following links, rechecks identity, bounds data | None | `file_safety.py`, `_file_safety.py` |
| Atomic mutation | Stages and replaces without following links or tearing state | Staged bytes | `_confined_mutation.py` |
| Process primitive | Runs an identified binary with fixed argv, explicit environment, confined cwd, bounded stdin, process-tree timeout, and redacted output | Process handle | `_process_safety.py` |
| Audit emitter | Records allowed and denied operations without payload leakage | Security events | `_security_events.py` |
| Containment launcher | Launches untrusted code under a verified host sandbox or restricted principal | Attestations and child handles | `_containment.py` |
| Effect broker | Performs explicitly granted outward effects the contained child cannot perform directly | Process-scoped grants and receipts | `_effect_broker.py` |

The authoritative schemas are in `contracts/delivery/`; the Core pack projects
the work-loop scripts, not schema copies.[^r1]

| Contract | Producer → consumer | Invariant | Refuses on |
| --- | --- | --- | --- |
| `security-capability.v1` | Issuer → adapter, primitive, launcher, broker | Delegation cannot widen authority or claim unsupported read coverage. Omitted `network` and `children` deny. | An unknown version, a missing grant, or missing containment |
| `confined-file.v1` | Adapter or broker client → path and mutation primitives | The resolved target stays inside the root. Additive bounds may tighten only through a new grant. | An unsafe or changed identity, or an unknown version |
| `safe-process.v1` | Adapter or broker client → process primitive | No `PATH` search, shell reinterpretation, ambient environment, open stdin, orphan child that stayed in the process group, or unredacted durable output. Ambient environment inheritance defaults to none. | Identity drift, an ungranted environment or cwd, an unsupported tree kill, a timeout, a launch error, or a bound breach |
| `containment-attestation.v1` | Verified launcher → supervisor and broker | Authority is narrower than the grant, and an adapter cannot omit a required denial or coverage. | Missing, unverifiable, or broader enforcement |
| `security-event.v1` | Primitive or broker → audit sink | Sensitive payloads never enter diagnostics. An audit failure cannot turn a denial into an allow. | An unknown major version; sinks ignore additive fields |

Each primitive holds state that its lifecycle keeps consistent:

- The issuer's child grant is never broader than its parent (`intersect_grants`).
- The file primitive validates and effects on the same identity, and a failed commit leaves the original bytes intact.
- No durable process state or output bypasses redaction (`_process_safety.py`).
- The containment launcher never starts a child until denied roots and OS limits are proven (`_containment.py`).
- A broker grant is started, used once, and expired (`_effect_broker.py` `request_effect`, `_is_expired`), and an untrusted child has no direct access to denied control-plane paths.
- An event failure never authorizes an effect.[^r4]

Unsupported operations fail closed, and each platform's exact capability set is what the host mode reports (`race_free_mutation()`, § 4).

Security owners approve contract changes. Readers deploy before writers, sinks
ignore additive fields, and every contract rejects an unknown major version.

## 2. Trust boundaries decide which guarantee applies

| Boundary | Trust statement | Enforced guarantee |
| --- | --- | --- |
| Skill policy → supervisor | Policy is interpreted input, not an OS control | The supervisor validates a typed operation before selecting a capability. |
| Supervisor → same-process adapter | Adapter code is trusted infrastructure; its task data is untrusted | Conformance tests and capability-only APIs prevent accidental bypass, not malicious direct OS calls. |
| Adapter → primitive | The primitive receives untrusted paths, argv, and payloads | Canonicalization, bounds, identity checks, and fail-closed errors apply before any effect. |
| Supervisor → containment launcher | Untrusted adapter or executable code has no same-process mode | A verified sandbox or restricted principal denies direct access to control-plane paths and ungranted process or network effects. |
| Contained child → effect broker | OS enforcement, not the broker API, removes the child's direct authority | The broker validates grants and performs the only approved outward effect. |
| Primitive or broker → OS | OS sandbox strength is host-specific | The design claims only the confinement the selected deployment supplies. |

Same-process adapters (a separately installed Pi extension, Claude Code, Codex,
and tmux integrations) remain trusted code. The primitive does not claim to
confine malicious same-process adapter code. The effect broker never substitutes
for OS containment.

Core security code imports no runtime-specific adapter
package. Untrusted grants deny writes to `.git`, protected integration refs, and
delivery-control paths; a broker may expose bounded read-only Git queries, and
only the supervisor's Git helper creates integration objects or moves the run's
product ref.

## 3. Every operation validates, effects, and audits in a fixed order

1. The supervisor issues the narrowest grant for a validated operation and
   journals the grant ID without sensitive values. A grant carries write roots,
   product-read proof mode, network, child authority, and resource limits.
2. A trusted adapter passes untrusted values to the primitive. Untrusted code
   requires verified OS containment.
3. A contained child sends approved outward requests to the effect broker. It
   cannot reach the repository control plane by direct syscall.
4. The primitive or broker validates and performs the bounded effect. The writer
   port that calls it emits the redacted security event: an allow before the
   effect is acknowledged, and a denial for a refused effect.
5. The adapter returns the containment attestation and effect receipts.

The confined file-mutation primitive is I/O only. Its callers, the evidence
store and the shadow facade, audit every file write they make, with the allow
and any denial sharing one operation ID. That covers log creation, appends,
recovery truncation, and shadow records.

Two writes are not audited: the append
that stores a security event, because that append is the audit record, and the
shadow folder's self-ignoring `.gitignore`, which must exist before the audit
log can be written there. Until it exists the shadow audit store is
unavailable, so a refused `.gitignore` create fails closed with the primitive's
stable denial code and stores no event.

An escape, identity race, timeout, or unsupported guarantee refuses before
commit with a stable denial code. A staged mutation is discarded, the
original file stays intact, and no success receipt is written.

Restart recovery expires grants and reconciles only
acknowledged effect receipts. The caller must create a new operation rather than
weaken the denied one, and cannot downgrade a refusal by retrying through
another helper.

**STATUS: PLANNED** — Parallel task execution needs an enforced read allowlist or
a complete trace, recorded in an `access-attestation.v1` that the adapter
returns; hosts that cannot supply one mark access incomplete and the attempt
serializes. The supervisor dispatches one request at a time. See
[ADR-0156](../adr/0156-work-loop-concurrency-needs-attested-read-coverage.md),
[`loop-parallelism.md`](loop-parallelism.md), and
[`work-loop-result-integration.md`](work-loop-result-integration.md).

**Observability.** The writer port's `security-event.v1` records the event
type, outcome, reason code, operation ID, correlation ID, and timestamp, so an
allow and a denial share one operation ID. Root ID and duration fields, and a
primitive-level emitter that does not depend on the calling writer, are
**STATUS: PLANNED**.

## 4. Path confinement fails closed on any identity change

An adapter requests a typed capability (`CapabilityIssuer` grants,
`request_effect` in `_effect_broker.py`) rather than calling a raw path helper.
The primitive validates the lexical path, resolves the existing link chain,
confirms containment, opens without following links, and rechecks identity
before returning data or committing a mutation.

Any identity change, non-regular
file, oversized input, escape, unsupported platform condition, or timeout
returns a closed refusal. Confined reads, lists, and hashes also reject
link-like and non-regular entries and bound input.

### Hosts without descriptor-relative directory walking

Windows has no descriptor-relative directory walking. There the work-loop
confined create, append, and replace run in a path-checked mode: they check every
component and the staged file's identity by path before writing, re-check after,
and report state unknown on a difference.

One race stays open, an ancestor
swapped for a junction just before the commit call, and
[ADR-0152](../adr/0152-path-checked-confined-writes-on-hosts-without-descriptor-walking.md)
accepts it for trusted runs. `race_free_mutation()` is false on such hosts, and
every supervisor verb refuses untrusted or undetermined code there.[^r2]

## 5. The process primitive removes ambient authority

Validation resolves an absolute executable without `PATH` search, pins its file
identity, confines the working directory, and builds an environment only from
grant-allowlisted names and bounded supplied values. Stdin is closed unless the
grant supplies bounded bytes or a confined file.

A timeout or limit breach
terminates the whole process group or platform job. Captured output is bounded
and redacted before any durable write.

**Windows.** The primitive creates the child suspended and assigns it to a Job
Object before it runs. The job denies breakaway and ends every member when its
last handle closes, so no descendant survives.

The child inherits only its three
standard-stream handles, and a timeout ends the job. A failure to create, configure, or assign the job
refuses with `denied-job-object` and ends the process. The launcher also
refuses a batch script, an NTFS stream name, and a UNC or device path.

POSIX
behavior is unchanged.

### Accepted residuals of the identity pin and tree kill

The owner accepted these in the
[Accepted Risk section](../specs/acceptance-authority-and-evidence/spec.md#accepted-risk)
of the acceptance authority and evidence spec:

- The pin checks only the executable's own bytes, once, before launch. It does
  not protect them afterwards or cover anything loaded by path.
- A path swap before exec on hosts without `/proc/self/fd` exec.
- A child that leaves the process group.
- Group-ID reuse on Pythons without `os.waitid`.
- Interrupt handling is best effort.

## 6. Quality scenarios and the fixtures that verify them

| Stimulus | Response | Verification |
| --- | --- | --- |
| Path crosses a symlink outside root | Canonicalizes and refuses before effect | Symlink and junction suite |
| File changes between validation and use | Identity recheck refuses the stale descriptor | Replacement race fixture |
| Extension requests broader authority | Issuer rejects grant widening | Capability property tests |
| Untrusted adapter lacks verified containment | Trust-boundary rule refuses activation | Adapter activation fixture |
| Worker writes a semantic record directly | Verified sandbox or restricted principal denies every control-plane path | Cross-adapter forgery suite |
| Contained child issues a direct filesystem syscall | OS containment denies it before the control plane | Direct-syscall bypass fixture |
| Worker writes Git metadata or the protected product ref | Grant and host containment deny it; the supervisor's attempt check refuses a result whose attempt changed this run's product ref | Git-ref and object-store forgery fixture; the attempt suite |
| Launcher proposes bounds broader than the grant | Attestation comparison refuses launch | Network, process-tree, CPU, memory, time, output, and process-count fixtures |
| Process request relies on ambient state or outlives timeout | Rejects undeclared env, cwd, executable, or stdin; kills the process group on breach | Environment, cwd escape, executable-swap, stdin, process-tree kill, and redaction fixtures |

A trusted adapter that accidentally bypasses a primitive is made visible by
dependency lint, capability-only APIs, and adapter conformance. If the broker or
audit sink is unavailable, security-sensitive effects refuse, staged mutations
discard cleanly, and the operator receives a redacted denial code rather than a
partial success.[^r3]

## 7. The execution supervisor assumes a worker may write files directly

The supervisor (`work-supervisor.py` and its `_supervisor_*.py` modules) is a
host subagent that these controls never contain. They catch naive writes to
trusted files, Git control state, and `delivery/`.

A deliberate worker acts with
the supervisor's own authority. Network denial and write roots for launched
processes are enforced only under verified containment (§ 2).

### Git hardening

Every supervisor `git` call goes through one helper, `_supervisor_git.py`. It
ignores system and global config, carries only the line-ending and
`core.excludesFile` settings, and turns off hooks, fsmonitor, external diff,
textconv, replace refs, signing, and every filter repository config defines.
Before each call it checks Git control state by direct file reads, against the
open attempt's manifest when one exists and otherwise against the Git and common
directories that this invocation's discovery pinned.

It refuses if `info/grafts`
exists. Each invocation refuses `unsupported-git-version` on a Git older than
2.32, which would not honour an empty `GIT_CONFIG_GLOBAL`. Git-directory
discovery runs before anything is pinned, so it has no control state to compare
yet, and its result becomes the pins.

Two `git` calls run outside the helper, and neither runs configured code: the
effective-config read at admission and the commit-identity read once per run.
Both pass the pinned `--git-dir`, none of the helper's fixed flags, check
control state first, and use the out-of-helper environment form stated in the
[spec's Launch grants section](../specs/execution-supervisor-attempt-security/spec.md#launch-grants).
`start` refuses `unsupported-git-config` when repository config sets a
code-running key, or when any config scope defines a filter an attributes file
uses.

### Attempt checks and residue

Each time the supervisor issues a worker, `run-gates`, or `regenerate` request,
or launches a red proof or scratch receipt with no attempt open, it records a
manifest (path, size, sha256) of the trusted files and Git control state in its
store, `<git dir>/agentbundle-supervisor/<run id>/`. Trusted files are the spec,
the plan, every cited record, and the installed skill.

Every later `next` and
`report` compares against the manifest first. A difference refuses the attempt,
leaves `attempt-residue` naming each path until the paths are restored, and is
never committed.

A `config` or `config.worktree` entry records a config fingerprint
(`config-view:` plus the size and sha256 of the file with its canonical tracking
blocks removed). The excluded keys are `branch.<name>.remote`, `merge`,
`pushremote`, `rebase`, and `description`, and `remote.<name>.gh-resolved`, and
they are removed only in the exact form Git writes them in a file that ends in a
newline with no `\r` and no line ending in a backslash.

Every other byte stays in
the digest, so any other change refuses. A manifest recorded as a raw-file
fingerprint is compared against the raw file.

During an attempt, `HEAD` may move only through commits the store lists as the
supervisor's. After each supervisor-launched run of repository code, the check
runs again before any commit. Residue lives in the store, so deleting the
journal, `run.json`, or the local security log clears nothing.

### Product ref

The run's result lives in `refs/agentbundle/delivery/<run-id>/<token>/product`,
which the supervisor moves with `HEAD` in one compare-and-swap per step. An
attempt during which this run's ref changes, other than by the supervisor's own
move, is refused, and another run's ref never counts against it.

The trust rule,
the classification of `HEAD` and the ref, and the `adopt-history` decision are in
the [execution supervisor page](work-loop-execution-supervisor.md#product-ref). A
deliberate worker acting as the same user can still write the store's record.

### Pinning and regeneration

The first admitted `start` records the sha256 of every installed `scripts/` file
and of the two policy files. Every entry point compares them before it imports a
sibling and refuses `supervisor-changed` on a mismatch, and each sets no-bytecode
so a planted `.pyc` never runs. A run with an open or uncleared refused attempt
guards every spec in the work tree.

When `HEAD` holds the Core work-loop source,
review readiness holds, and the installed skill differs, `next` emits one
`regenerate` request. The supervisor admits it only when every installed file
equals that source, then re-pins, and commits the rebuilt install as a
`regenerate` step when the installed skill is tracked. The
[execution supervisor page](work-loop-execution-supervisor.md#product-ref) owns
which copies count and when it acts.

### Untrusted code

Under an `untrusted` classification with no verified containment, the supervisor
launches no red proof or scratch receipt, emits no `implement-task`,
`run-gates`, or `regenerate` request, and asks for a human decision.

### Result acceptance

`report` admits only the facts a request kind's row lists and refuses the rest
before reading any state. An extra fact refuses `result-fact-refused`; an
unknown kind refuses `result-kind-refused`. The table mirrors the
[spec's Result acceptance table](../specs/execution-supervisor-attempt-security/spec.md#result-acceptance).

| Request kind | Facts the result may assert |
| --- | --- |
| `implement-task` | The controller-run gate outcome only; the supervisor computes the change set |
| `write-stub` | Nothing; the supervisor computes the change set and runs the red proof |
| `review-role` | One `review-report.v1` bound to the requested subject, or a selection record |
| `assess-finding` | One finding assessment for the requested finding |
| `run-gates` | The gate outcome (commands, exit codes, output digests) and the criteria outcomes the readiness reader requires |
| `external-effect`, `effect-query` | Presence, absence, or unknowability, whether the attempt has ended, and the effect receipt |
| `regenerate` | Completion only; the supervisor computes the new digests |
| `human-decision` | The decision and its authority reference |

### Launch grants

No supervisor launch goes through the process primitive, so none records a
`safe-process.v1` record or a `security-capability.v1` grant. The
[spec's Launch grants table](../specs/execution-supervisor-attempt-security/spec.md#launch-grants)
holds each launch kind's grant row, and only the `git` row's Environment column
is adopted.

- `red-proof` and `scratch` are unrouted because the interpreter a
  plan-authored command names cannot be pinned without letting the launched code
  decide what the next launch loads. They run with the supervisor's own
  environment inherited whole and a timeout on the direct child only, which does
  not reach that child's descendants.
- `git` is unrouted because the primitive redacts every environment value from
  the output it returns, which would alter Git's data output: `HOME` prefixes a
  normal repository path, and the helper parses Git's stdout everywhere. The
  helper's stdin-bearing calls have no route either. The hardened helper bounds
  the child environment itself, in one form for a helper call and one for an
  out-of-helper config read.

Write roots and network denial are neither recorded nor enforced. The
post-run check of trusted files is the only detection of a write, and a
descendant that outlives an exempt launch can write after it.

**STATUS: PLANNED** — A primitive cutover or rollback may not select a weaker guarantee than the declared adapter trust class; no code enforces this yet. See [acceptance authority and evidence](../specs/acceptance-authority-and-evidence/spec.md).

**STATUS: PLANNED** — Route `red-proof`, `scratch`, and `git` through the
process primitive under a recorded grant:
[`supervisor-launch-routing-for-plan-authored-commands`](../product/intents/supervisor-launch-routing-for-plan-authored-commands.md).
Moving product-ref creation to a result-integration port is Slice 7 of
[`work-loop-result-integration.md`](work-loop-result-integration.md).

[^r1]: `contracts/delivery/security-capability.v1.schema.json`, `confined-file.v1`, `safe-process.v1`, `containment-attestation.v1`, `security-event.v1`; scripts under `packs/core/.apm/skills/work-loop/scripts/`. `file_safety.py` is the work-loop's local copy of the blessed confinement helpers in `agentbundle.catalogue_tooling.file_safety`.

[^r2]: `_confined_mutation.py` (`race_free_mutation`, `_host_mode`); `work-supervisor.py` and `_supervisor_admission.py` refuse untrusted code when it is false.

[^r3]: `tools/lint-adapter-layer-boundary.py`; work-loop tests under `packs/core/tests/skills/work-loop/` (for example `test_process_safety.py`); `docs/specs/execution-supervisor-attempt-security/spec.md`.

[^r4]: `_security_capability.py` (`intersect_grants`, `CapabilityIssuer`), `_confined_mutation.py`, `_process_safety.py`, `_containment.py` (`denied-*` codes), `_effect_broker.py` (`request_effect`, `_is_expired`), `_security_events.py`.
