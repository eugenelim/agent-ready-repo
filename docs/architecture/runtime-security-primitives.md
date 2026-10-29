# Subsystem Design — Runtime security primitives

**Decision sought:** Move filesystem and process confinement out of work-loop
logic into versioned, reusable infrastructure capabilities.
**Author(s):** Platform Core maintainers
**Status:** Draft
**Last updated:** 2026-10-01
**Reviewers:** Security and `agentbundle` maintainers

## 1. Scope and Context

| In scope | Out of scope | Why |
| --- | --- | --- |
| Confined reads, lists, hashes, creates, replaces, and deletes | Delivery policy | Security mechanics must be correct once |
| Process argument, environment, timeout, and output controls | Command selection | The caller owns intent, the primitive bounds effect |
| Capability grants and a verified-containment contract | Platform-specific sandbox implementation | Hosts provide different isolation mechanisms |

**Goals**

- Every path or process effect that a conforming adapter derives from untrusted
  data crosses the primitive before reaching the operating system.
- Uncertainty fails closed with stable redacted diagnostics.
- Work-loop never explains or reimplements filesystem algorithms.

**Non-goals**

- Claiming that Pi extensions, tmux, or a local process provide a sandbox.
- Confining malicious same-process adapter code without verified OS containment.

## 2. Structural Model

| Element | Type | Responsibility | State |
| --- | --- | --- | --- |
| Capability issuer | Infrastructure component | Grant operations over an exact root and action set | Active grants |
| Path confinement primitive | Library | Validate, open, recheck identity, and bound data | Stateless |
| Atomic mutation primitive | Library | Stage and replace without following links or tearing state | Temporary staged bytes |
| Process primitive | Library | Execute an identified binary with fixed argv, explicit environment, confined cwd, bounded stdin, process-tree timeout, and redacted output | Process handle |
| Audit emitter | Port | Record allowed and denied operation metadata without payload leakage | Security events |
| Containment launcher | Infrastructure boundary | Launch untrusted code under a verified host sandbox or restricted security principal | Containment attestation |
| Effect broker | Optional sandbox bridge | Perform explicitly granted effects that the contained child cannot perform directly | Broker session and grants |

| Boundary | Trust statement | Enforced guarantee |
| --- | --- | --- |
| Skill policy → supervisor | Policy is interpreted input, not an OS control | Supervisor validates a typed operation before selecting a capability |
| Supervisor → same-process adapter | Adapter code is trusted infrastructure; its task data is untrusted | Conformance tests and capability-only APIs prevent accidental bypass, not malicious direct OS calls |
| Adapter → primitive | Primitive receives untrusted paths, argv values, and payloads | Canonicalization, bounds, identity checks, and fail-closed errors apply before effect |
| Supervisor → containment launcher | Untrusted adapter or executable code has no same-process mode | Verified sandbox or restricted principal denies direct access to control-plane paths and ungranted process or network effects |
| Contained child → effect broker | OS enforcement, not the broker API, removes the child's direct authority | Broker validates grants and performs the only approved outward effect |
| Primitive or broker → operating system | OS sandbox strength is host-specific | The design claims only the confinement actually supplied by the selected deployment |

## 3. Runtime Model

**Normal sequence**

1. The supervisor issues the narrowest grant for a validated operation and
   journals the grant ID without sensitive values. The grant carries write
   roots, product-read allowlist or trace mode, network, child authority, and
   resource limits; omitted v1 network and child fields deny all.
2. A trusted adapter passes untrusted values to the primitive. Untrusted code
   requires verified OS containment; parallel work additionally requires an
   enforced read allowlist or complete trace. Otherwise access is incomplete
   and the attempt serializes.
3. The contained child sends approved outward requests to the effect broker;
   it cannot reach the original repository control plane by direct syscall.
4. The primitive or broker validates and performs the bounded effect. The
   writer port that calls it emits the redacted security event: an allow
   before the effect is acknowledged, and a denial for a refused effect. The
   confined file-mutation primitive is I/O only. Its two callers, the
   evidence store and the shadow facade, audit every file write they make,
   with the allow and any denial sharing one operation ID. That covers log
   creation, appends, recovery truncation, and shadow records. Two writes are
   not audited: the append that stores a security event, because that append
   is the audit record, and the shadow folder's self-ignoring `.gitignore`,
   which must exist before the audit log can be written into that folder.
   Until it exists the shadow audit store is unavailable, so a refused
   `.gitignore` create fails closed with the primitive's stable denial code
   and stores no event.
5. The adapter returns containment, `access-attestation.v1`, and effect receipts.

**Failure and recovery sequence**

1. An escape, identity race, timeout, or unsupported guarantee refuses before
   commit and emits a stable denial code.
2. A staged mutation is discarded; the original file remains intact and no
   success receipt is written.
3. Restart recovery expires grants and reconciles only acknowledged effect
   receipts. The caller must create a new operation rather than weakening the
   denied request.

An adapter requests a typed capability rather than a raw path helper. The
primitive validates the lexical path, resolves the existing link chain,
confirms containment, opens without following links, and rechecks identity
before returning data or committing a mutation.

Any identity change, non-regular file, oversized input, escape, unsupported
platform condition, or timeout returns a closed refusal. The caller cannot
downgrade the refusal by retrying through another helper.

For a process, validation resolves an absolute executable without `PATH`
search, pins its file identity, confines the working directory, and builds an
environment only from grant-allowlisted names and bounded supplied values.
Stdin is closed unless the grant supplies bounded bytes or a confined file.
Timeout or limit breach terminates the whole process group or platform job;
captured output is bounded and redacted before any durable write.

## 4. Contracts and Invariants

| Contract | Producer → consumer | Identity | Compatibility and change authority | Failure semantics | Invariant |
| --- | --- | --- | --- | --- | --- |
| `security-capability.v1` | Issuer → adapter, primitive, launcher, broker | Grant, roots, operations, trust, writes, product-read proof mode, control denies, network, children, limits | Security owners approve; omitted network/children deny; unknown versions refuse | Missing containment or grant refuses | Delegation cannot widen authority or claim unsupported read coverage |
| `confined-file.v1` | Adapter or broker client → path and mutation primitives | Canonical root plus relative path | Security maintainers approve changes; additive bounds may tighten only through a new grant; unknown versions refuse | Unsafe or changed identity refuses | Resolved target stays inside root |
| `safe-process.v1` | Adapter or broker client → process primitive | Absolute executable plus identity, fixed argv, grant, confined cwd, environment allowlist, stdin mode, process-tree and output bounds | Security maintainers approve changes; readers deploy before writers; unknown versions refuse; ambient environment inheritance defaults to none | Identity drift, ungranted env or cwd, unsupported tree kill, timeout, launch error, or bound breach refuses | No `PATH` search, shell reinterpretation, ambient environment, open stdin, orphan child that stayed in the process group, or unredacted durable output |
| `containment-attestation.v1` | Verified launcher → supervisor and broker | Host mechanism, principal/sandbox, roots, read enforcement or trace coverage, network, children, limits | Security owners approve guarantees; adapters cannot omit required denial or coverage | Missing, unverifiable, or broader enforcement refuses | Authority is narrower than the grant; only verified read coverage can support complete access attestation |
| `security-event.v1` | Primitive or broker → audit sink | Operation and correlation IDs | Security maintainers approve redaction schema; sinks ignore additive fields and reject unknown major versions | Audit failure cannot turn denial into allow | Sensitive payloads never enter diagnostics |

The `safe-process.v1` identity check and tree kill have owner-accepted
residuals, recorded in the Accepted Risk section of the
[acceptance authority and evidence spec](../specs/acceptance-authority-and-evidence/spec.md#accepted-risk):
- the pin checks only the executable's own bytes, once, before launch, so
  it does not protect them afterwards or cover anything loaded by path;
- a path swap before exec on hosts without `/proc/self/fd` exec;
- a child that leaves the process group;
- group-ID reuse on Pythons without `os.waitid`;
- interrupt handling is best effort.

The primitive preserves the repository's blessed helper behavior in
`file_safety.py` (the work-loop skill's local copy at
`packs/core/.apm/skills/work-loop/scripts/file_safety.py`).
Existing confined reads, lists, and hashes already resolve and confine paths,
reject link-like or non-regular entries, bound input, open without following
links, and recheck identity. This design reuses those controls and adds atomic
mutation, capability issuance, process confinement, containment attestations,
and the optional effect broker.

Same-process adapters—including a separately installed Pi extension, Claude
Code, Codex, and tmux integrations—remain trusted code. An untrusted adapter or
child runs only through a verified host sandbox or restricted security
principal; the sequential adapter refuses it when the host cannot supply that
enforcement. The effect broker grants selected outward effects but never
substitutes for OS containment. Core security code imports no runtime-specific
adapter package.

Untrusted grants deny writes to `.git`, protected integration refs, and
delivery-control paths. A broker may expose bounded read-only Git queries, but
only the result-integration port may create integration objects or update its
protected ref.

## 5. Data and State

| Element | State it owns | Lifecycle | Consistency requirement |
| --- | --- | --- | --- |
| Issuer | Active grants | Issued, narrowed, expired | A child grant is never broader than its parent |
| File primitive | Stateless | n/a | Validation and effect operate on the same identity |
| Mutation primitive | Staged content | Created, committed, discarded | Failed commit leaves original bytes intact |
| Process primitive | Process-group or job handle and bounded in-memory streams | Validated, launched, terminated, reaped | No durable process state or output bypasses redaction |
| Audit emitter | Redacted events | Appended | Event failure never authorizes an effect |
| Containment launcher | Attestations and child handles | Verified, launched, terminated | Child never starts until denied roots and OS limits are proven |
| Effect broker | Process-scoped grants and receipts | Started, used once, expired | Untrusted child lacks direct access to denied control-plane paths |

## 6. Deployment and Operations

| Unit | Runs as | Scaling | Observability |
| --- | --- | --- | --- |
| Primitive library | In harness or projected runtime support | Per operation | Allow, deny code, root ID, duration |
| Host containment launcher | Runtime-specific verified sandbox or restricted-principal adapter | Per session or process | Attested filesystem, network, process, and resource bounds |
| One-shot effect broker | Bridge outside the contained child | Per operation | Trust class, grants, denied roots, and effect receipt |

## 7. Quality Scenarios and Verification

| Stimulus | Mechanism and response | Target | Verification |
| --- | --- | --- | --- |
| Path crosses a symlink outside root | Path primitive canonicalizes and refuses before effect | 100% adversarial fixtures refused | Symlink and junction suite |
| File changes between validation and use | Identity recheck refuses the stale descriptor | Zero stale-descriptor effects | Replacement race fixture |
| Extension requests broader authority | Capability issuer rejects grant widening | Zero child grants exceed parent | Capability property tests |
| Untrusted adapter lacks verified host containment | Trust-boundary rule refuses activation | Zero untrusted same-process adapters receive direct authority | Adapter activation fixture |
| Worker writes a semantic record directly | Verified sandbox or restricted principal denies every control-plane path | Zero forged criteria, evidence, reports, or dispositions through every adapter | Cross-adapter forgery suite |
| Contained child issues a direct filesystem syscall | Verified OS containment denies it before the control plane | Zero broker-bypass writes | Direct-syscall bypass fixture |
| Worker writes Git metadata or the protected product ref | Grant and host containment deny direct mutation | Zero integration-boundary bypasses | Git-ref and object-store forgery fixture |
| Launcher proposes network, child-process, or resource bounds broader than the grant | Attestation comparison refuses launch | Zero host-selected overgrant and deny-all omission behavior | Network, process-tree, CPU, memory, time, output, and process-count fixtures |
| Parallel task reads an undeclared product path | Enforced allowlist denies it or complete tracing records it; other hosts mark access incomplete | Zero false complete attestations | Cross-adapter undeclared-read and trace-gap fixtures |
| Process request relies on ambient state or outlives timeout | Primitive rejects undeclared env, cwd, executable, or stdin and kills the full process group on breach | Zero inherited variables, unbounded durable bytes, or orphan children that stayed in the process group (see the accepted residuals in §4) | Environment, cwd escape, executable-swap, stdin, process-tree kill, and redaction fixtures |

## 8. Implementation Mapping

| Element | Source owner | Build unit | Verification |
| --- | --- | --- | --- |
| Capability issuer | `packs/core/.apm/skills/work-loop/scripts/_security_capability.py` (Slice 1) | Work-loop skill scripts | Delegation property tests |
| Path confinement and atomic mutation primitives | `packs/core/.apm/skills/work-loop/scripts/file_safety.py` plus `_confined_mutation.py` beside it (Slice 1) | Work-loop skill scripts | Boundary and race suite |
| Process primitive | `packs/core/.apm/skills/work-loop/scripts/_process_safety.py` (Slice 1) | Work-loop skill scripts | Argument, timeout, and output-bound tests |
| Audit emitter | `packs/core/.apm/skills/work-loop/scripts/_security_events.py` (Slice 1) | Work-loop skill scripts | Redaction and denial-path tests |
| Containment launcher | `packs/core/.apm/skills/work-loop/scripts/_containment.py` with host adapters (Slice 1) | Work-loop skill scripts and host adapters | Attestation and direct-syscall negative tests |
| Effect broker | `packs/core/.apm/skills/work-loop/scripts/_effect_broker.py` (Slice 1) | Work-loop skill scripts | Process-boundary and authority-negative tests |
| Portable contracts and runtime wrappers | Authoritative `contracts/delivery/`; Core pack projects work-loop skill scripts, not schema copies | Contract source and Core pack | Source-to-projection parity and cross-adapter conformance |

## 9. Decisions, Alternatives, and Risks

- **Decision:** Security confinement is infrastructure, not skill procedure.
- **Alternative:** Keep detailed secure-file instructions in work-loop.
  **Rejected because:** every caller can interpret or implement them differently.
- **Alternative:** Treat same-process wrappers as a sandbox. **Rejected because:**
  code with the user's OS authority can call around a library boundary.
- **Alternative:** Broker every effect in every deployment. **Rejected because:**
  the sequential trusted-adapter floor does not need process isolation, while
  untrusted adapters still require it.
- **Risk:** A trusted adapter accidentally bypasses the primitive. **Mitigation:**
  dependency lint, capability-only APIs, and adapter conformance make direct
  effects visible; malicious adapters remain outside the guarantee.
- **Risk:** Platform-specific link semantics weaken a guarantee. **Mitigation:**
  unsupported operations fail closed and conformance declares each platform's
  exact capability set.
- **Risk:** The broker or audit sink is unavailable at 3 a.m. **Mitigation:**
  security-sensitive effects refuse, staged mutations discard cleanly, and
  operators receive a redacted denial code rather than a partial success.

## 10. Rollout, Migration, and Reversal

Existing blessed helpers implement the first contract. Callers migrate one
operation family at a time; old entry points remain wrappers until dependency
checks show no bypass, so rollback restores the wrapper without weakening the
primitive.

| Responsibility | Owner |
| --- | --- |
| Primitive and broker cutover | `agentbundle` security maintainers |
| Adapter trust classification | Owning adapter maintainer with security reviewer approval |
| Rollback authorization | Security maintainer on call; rollback cannot select a weaker guarantee than the declared adapter trust class |

## 11. Execution supervisor controls

The execution supervisor (`work-supervisor.py` and its `_supervisor_*.py`
modules) assumes a worker attempt may write files directly. It is a host
subagent that these controls never contain. They catch naive writes to trusted
files, Git control state, and `delivery/`, and nothing more. A deliberate
worker acts with the supervisor's own authority. Network denial and write roots
for processes the supervisor launches are enforced only under verified
containment (§2).

**Windows process branch.** On Windows the process primitive creates the child
suspended and assigns it to a Job Object before it runs. The job denies
breakaway and ends every member when its last handle closes. The child inherits
only its three standard-stream handles. A timeout ends the job, so no
descendant survives. Any failure to create, configure, or assign the job
refuses with `denied-job-object` and ends the process. The launcher also
refuses a batch script, an NTFS stream name, and a UNC or device path. POSIX
behavior is unchanged.

**Git hardening.** Every supervisor `git` call goes through one helper
(`_supervisor_git.py`). It ignores system and global config, carries only the
line-ending and `core.excludesFile` settings, and turns off hooks, fsmonitor,
external diff, textconv, replace refs, signing, and every filter that
repository config defines. Before each call it checks Git control state by
direct file reads: against the open attempt's manifest when one exists, and
otherwise against the Git and common directories this invocation's discovery
pinned. It also refuses if `info/grafts` exists. Each invocation first refuses
`unsupported-git-version` on a Git older than 2.32, which would not honour an
empty `GIT_CONFIG_GLOBAL`. It then runs the helper's Git-directory discovery,
which carries the helper-call environment and fixed flags; it runs before
anything is pinned, so it has no control state to compare yet, and its result
becomes the pins. The only `git` calls outside the helper
are two config reads that run no configured code: the effective config at
admission, and the commit identity once per run. Both pass the pinned
`--git-dir` and none of the helper's fixed flags, check control state first, and
carry the out-of-helper environment form that the
[spec's Launch grants section](../specs/execution-supervisor-attempt-security/spec.md#launch-grants) states. `start` refuses with
`unsupported-git-config` when repository config sets a code-running key, or
when any config scope defines a filter that an attributes file uses.

**Attempt checks and residue.** Each time the supervisor issues a worker,
`run-gates`, or `regenerate` request, or launches a red proof or scratch receipt
with no attempt open, it records a manifest (path, size, sha256) of the trusted
files and Git control state in its store, `<git dir>/agentbundle-supervisor/<run id>/`.
Trusted files are the spec, the plan, every cited record, and the installed
skill. Every later `next` and `report` compares against the manifest first. A
difference refuses the attempt, leaves `attempt-residue` naming each path until
the paths are restored, and is never committed. During an attempt, `HEAD` may
move only through commits the store lists as the supervisor's. After each
supervisor-launched run of repository code the check runs again before any
commit. Residue lives in the store, so deleting the journal, `run.json`, or
the local security log clears nothing.

**Pinning and regeneration.** The first admitted `start` records the sha256 of
every installed `scripts/` file and of the two policy files in the store. Every
entry point compares them before it imports a sibling and refuses
`supervisor-changed` on a mismatch, and each sets no-bytecode so a planted
`.pyc` never runs. A run with an open or uncleared refused attempt guards every
spec in the work tree. When `HEAD` holds the Core work-loop source, review
readiness holds, and the installed skill differs, `next` emits one `regenerate`
request. The supervisor admits it only when every installed file equals that
source, then re-pins. When the installed skill is tracked in the work tree,
`next` answers `uncommitted-changes` until the controller commits the
regenerated skill.

**Untrusted code.** Under an `untrusted` classification with no verified
containment, the supervisor launches no red proof or scratch receipt, emits no
`implement-task`, `run-gates`, or `regenerate` request, and asks for a human decision.

**Result acceptance.** `report` admits only the facts a request kind's row
lists, and refuses the rest before reading any state. The table is the
[spec's Result acceptance table](../specs/execution-supervisor-attempt-security/spec.md#result-acceptance):

| Request kind (from `execution-supervisor-core`) | Facts the result may assert | Everything else |
| --- | --- | --- |
| `implement-task` | The controller-run gate outcome only; the supervisor computes the change set | Refused |
| `write-stub` | Nothing; the supervisor computes the change set and runs the red proof | Refused |
| `review-role` | One `review-report.v1` bound to the requested subject, or a selection record | Refused |
| `assess-finding` | One finding assessment for the requested finding | Refused |
| `run-gates` | The gate outcome — its commands, exit codes, and output digests — and the criteria outcomes the readiness reader requires | Refused |
| `external-effect`, `effect-query` | Presence, absence, or unknowability, whether the attempt has ended, and the effect receipt | Refused |
| `regenerate` | Completion only; the supervisor computes the new digests | Refused |
| `human-decision` | The decision and its authority reference | Refused |
| Any other kind | Nothing | Refused |

An extra fact refuses `result-fact-refused`. An unknown kind refuses
`result-kind-refused`.

**Launch grants.** No supervisor launch goes through the process primitive, so
none records a `safe-process.v1` record or a `security-capability.v1` grant. The
[spec's Launch grants table](../specs/execution-supervisor-attempt-security/spec.md#launch-grants) holds each launch kind's grant
row. Only the `git` row's Environment column is adopted today; the rest is owned
by
[`supervisor-launch-routing-for-plan-authored-commands`](../product/intents/supervisor-launch-routing-for-plan-authored-commands.md).

`red-proof` and `scratch` are unrouted because the interpreter a plan-authored
command names cannot be pinned without letting the launched code decide what the
next launch loads. They run with the supervisor's own environment inherited
whole and a timeout on the direct child only, which does not reach that child's
descendants.

`git` is unrouted because the primitive redacts every environment value from
the output it returns, which would alter Git's data output: `HOME` prefixes a
normal repository path and the helper parses git's stdout everywhere. The
helper's stdin-bearing calls have no route either. The hardened helper does
bound the child environment itself, in two forms — one for a helper call and
one for an out-of-helper config read. The
[spec's Launch grants section](../specs/execution-supervisor-attempt-security/spec.md#launch-grants) is their single statement;
AC-0020 is checked against it.

**What needs verified containment.** Write roots and network denial are neither
recorded nor enforced today. The post-run check of trusted files is the only
detection of a write, and a descendant that outlives an exempt launch can write
after it.
