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
4. The primitive or broker validates, performs the bounded effect, and emits a
   redacted security event before acknowledging success.
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
| `safe-process.v1` | Adapter or broker client → process primitive | Absolute executable plus identity, fixed argv, grant, confined cwd, environment allowlist, stdin mode, process-tree and output bounds | Security maintainers approve changes; readers deploy before writers; unknown versions refuse; ambient environment inheritance defaults to none | Identity drift, ungranted env or cwd, unsupported tree kill, timeout, launch error, or bound breach refuses | No `PATH` search, shell reinterpretation, ambient environment, open stdin, orphan child, or unredacted durable output |
| `containment-attestation.v1` | Verified launcher → supervisor and broker | Host mechanism, principal/sandbox, roots, read enforcement or trace coverage, network, children, limits | Security owners approve guarantees; adapters cannot omit required denial or coverage | Missing, unverifiable, or broader enforcement refuses | Authority is narrower than the grant; only verified read coverage can support complete access attestation |
| `security-event.v1` | Primitive or broker → audit sink | Operation and correlation IDs | Security maintainers approve redaction schema; sinks ignore additive fields and reject unknown major versions | Audit failure cannot turn denial into allow | Sensitive payloads never enter diagnostics |

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
| Process request relies on ambient state or outlives timeout | Primitive rejects undeclared env, cwd, executable, or stdin and kills the full tree on breach | Zero inherited variables, orphan children, or unbounded durable bytes | Environment, cwd escape, executable-swap, stdin, process-tree kill, and redaction fixtures |

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
