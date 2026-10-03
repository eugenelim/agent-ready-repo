# Subsystem Design — Delivery content safety

**Decision sought:** Give every supported semantic writer and reader boundary
one versioned classification, size, protected-data, normalization, and
inert-consumption contract.
**Author(s):** Security and `agentbundle` maintainers
**Status:** Draft
**Last updated:** 2026-10-01
**Reviewers:** Security, Core pack, and project-knowledge maintainers

## 1. Scope and Context

| In scope | Out of scope | Why |
| --- | --- | --- |
| Classification vocabulary, size profiles, reject or redact rules | Deciding whether evidence proves a criterion | Content safety cannot grant semantic authority |
| Secret and personal-data scanning before persistence | General content moderation | The boundary protects repository and downstream agent context |
| Typed inert-data framing for downstream consumers | Reviewer or agent prompt design | Untrusted text must never become procedure |

**Goals**

- Evidence, review, integration, and knowledge boundaries make the same safety
  decision for the same content.
- Declared credentials and scanner-covered personal identifiers never enter
  Git-backed semantic state.
- Stored reviewer or tool prose remains data when another agent reads it.

**Non-goals**

- Claiming perfect natural-language prompt-injection or personal-data detection.

## 2. Structural Model

| Element | Type | Responsibility | State |
| --- | --- | --- | --- |
| Policy registry | Contract data | Publish classes, boundary profiles, scanner set, and limits | Versioned policy |
| Schema normalizer | Pure component | Reject unknown structures, tags, encodings, and executable forms | Stateless |
| Protected-data scanner | Pure component | Detect declared secret and personal-data patterns | Stateless |
| Redaction engine | Pure component | Replace only policy-approved structured diagnostic fields | Stateless |
| Content-safety guard | Port | Apply a profile before a semantic write or transient projection | Stateless decision value |
| Inert-data wrapper | Consumer boundary | Keep accepted free text typed and separated from instructions | Stateless |

The policy vocabulary is `public`, `repository-internal`, `restricted`,
`credential`, and `personal`. Only the first two persist as bounded Git text.
Restricted payloads use controlled references.

Producer-declared or
scanner-detected credentials and personal data reject without payload or hash
retention; unknown personal data remains a stated residual risk.

## 3. Runtime Model

**Normal sequence**

1. A producer submits a typed record, declared class, provenance, and the named
   profile in the [semantic writer matrix](#4-contracts-and-invariants).
2. The guard validates schema, UTF-8, control characters, nesting, field and
   record bytes, and the policy's exact scanner set.
3. A known structured diagnostic field may be replaced by a fixed redaction
   token. A credential, personal datum, unknown class, or match in opaque prose
   rejects the whole semantic record.
4. The normalizer rejects unknown YAML tags, tool-call objects, executable
   markup, and authority-shaped fields outside the schema. Accepted free text
   is wrapped as typed `UntrustedData` for every downstream consumer.
5. The owning semantic port persists only the normalized record and the policy
   version that admitted it.

**Failure and recovery sequence**

1. Rejection returns only source identity, profile, policy version, and a stable
   reason code; it retains no rejected bytes or content-derived hash.
2. A crash before a writer acknowledges leaves no semantic record. Its normal
   transaction recovery governs a crash after acknowledgement.
3. A transient projection discards its decision after returning normalized
   bytes or refusal. Reprocessing under a new policy version creates a new
   decision identity and never mutates a prior accepted record.

Content scanning is defense in depth, not proof that prose is harmless. The
hard downstream guarantee comes from an allowlisted schema and a typed wrapper
that consumers render inside fixed data delimiters and never concatenate into
system instructions, commands, tool calls, paths, approvals, or authority.

## 4. Contracts and Invariants

| Contract | Producer → consumer | Identity | Compatibility and change authority | Failure semantics | Invariant |
| --- | --- | --- | --- | --- | --- |
| `content-safety-policy.v1` | Authoritative contract source → every persistence guard and consumer | Policy version, scanner corpus digest, boundary profile | Security and privacy owners approve classes and handling; tighter or incompatible rules require explicit policy version; unknown majors refuse | Missing policy or profile blocks persistence | One record is evaluated once under one named profile and policy version |
| `content-safety-decision.v1` | Persistence guard → owning semantic port | Source record, policy, profile, normalized-record digest, decision code | Additive redacted diagnostics are allowed; no rejected payload metadata is additive | Rejected content produces no semantic payload | Only `accepted` supplies bytes to a writer |
| `untrusted-data.v1` | Persistence guard → agent or tool consumer | Accepted record, field path, policy version | Consumer support is required before writer rollout; unknown majors remain opaque | A consumer unable to preserve inert framing refuses the field | Data cannot request tools, grant authority, or alter procedure |

| Boundary profile | Maximum persisted content | Additional rule |
| --- | --- | --- |
| Structured control | 64 KiB | Allowlisted identifiers, enums, digests, numbers, and repository-relative paths only; no opaque prose |
| Evidence embedded record | 64 KiB | Raw output is a controlled reference, never embedded |
| Review report | 1 MiB total, 64 KiB per free-text field | Protected data or executable or authority-shaped structure rejects the whole report; natural prose is `UntrustedData` |
| Integration diagnostic | 256 KiB and 1,000 conflict paths | Paths are repository-relative and classified |
| Knowledge observation | 64 KiB | Raw transcripts and unbounded tool output reject |
| Product addition | Existing result byte cap | Explicit task-added, non-ignored regular files only; repository product-admission and scanner policy apply |

| Semantic boundary | Required profile |
| --- | --- |
| Approval and effect-resolution ports | Structured control |
| Evidence transaction port | Evidence embedded record; transaction frame is structured control |
| Review report port | Review report |
| Finding assessment and disposition ports | Structured control; referenced report prose is not copied |
| Result-integration receipt port | Structured control |
| Integration conflict port | Integration diagnostic |
| Active result-application port, before legacy acknowledgement or any Git-object write | Product addition for every added path |
| Subject-source task-addition admission | Product addition revalidation |
| Project-knowledge intake port | Knowledge observation |
| Project-knowledge committed-store reader | Record-declared bounded profile; unknown or missing profile quarantines |
| Reversal/build-manifest port | Structured control plus release provenance policy |

The owning writer port, never its caller, applies the assigned profile before
append. Any new writer is closed structured-only until this matrix names a
profile; readers refuse or quarantine an unnamed profile. Cross-boundary
conformance covers every row.

The Slice 1 writer boundary registry is the single declared source that every
Slice 1 durable semantic writer and replay boundary must use. T5 and T7 writers
are forward-registered here; a writer in a later task that is not listed here
must add its entry to both this table and the code registry before first use.
The pack-side registry at
`packs/core/.apm/skills/work-loop/scripts/_content_safety.py`
(`SLICE_1_WRITER_BOUNDARIES`) and this table are kept in agreement by the
roster test `tests/roster/test_content_safety_boundary_matrix.py`.

| Slice 1 writer boundaries | Required profile |
| --- | --- |
| `initial-plan-review.v1` | Structured control |
| `approval-record.v1` | Structured control |
| `reviewed-execution-envelope.v1` | Structured control |
| `security-event.v1` | Structured control |
| `semantic-evidence-transaction.v1` | Structured control |
| `evidence-receipt.v1` | Evidence embedded record |
| `evidence-supersession.v1` | Evidence embedded record |

The delivery observation projector also applies the Knowledge observation
profile, but it is not a semantic writer. Its decision is ephemeral: delivery
persists no safety receipt, acknowledgement, or capture state. Only the
project-knowledge intake port may persist admission or lifecycle state.

Project-knowledge enquiry and distillation also apply the record's named
profile when reading committed knowledge. Records introduced by a Git merge do
not carry trusted write-time admission merely because they are committed;
invalid or unsafe records remain inert, are excluded, and appear only in a
bounded quarantine view.

The required scanner corpus covers repository-defined credential shapes,
high-confidence token patterns, direct personal identifiers, control
characters, unsafe encodings, and structured executable forms. Natural-language
instruction detection and unknown personal data have no completeness claim;
producer classification, reject-unknown behavior, schema allowlists, and inert
consumption supply the closed boundary.

## 5. Data and State

| Element | State it owns | Lifecycle | Consistency requirement |
| --- | --- | --- | --- |
| Policy source | `content-safety-policy.v1` under `contracts/delivery/` | Authored, reviewed, versioned, projected | Source is authoritative; package and pack copies pass byte or schema parity |
| Guard | None; returns a decision value | Evaluated, consumed, discarded | Accepted digest matches the exact normalized bytes supplied to a projection or writer |
| Rejected payload | None | Inspected in memory, discarded | No byte, excerpt, or content-derived hash persists |
| Controlled reference | Restricted external content locator | Created, expired, deleted | Authorization and retention are external to Git state |

## 6. Deployment and Operations

| Unit | Runs as | Scaling | Observability |
| --- | --- | --- | --- |
| Guard library | Every semantic writer in the matrix | Linear to profile byte limit | Accept/refusal counts, bytes, duration, policy version |
| Contract projection | Build tooling | Once per source policy change | Source-to-package and source-to-pack parity |

## 7. Quality Scenarios and Verification

| Stimulus | Mechanism and response | Target | Verification |
| --- | --- | --- | --- |
| Same protected payload reaches four ports | Shared policy returns the same refusal | 100% cross-boundary decision parity | Shared credential, personal-data, encoding, and size corpus |
| A semantic writer omits or names the wrong profile | Owning port refuses before append | Zero implicit-profile writes | One negative fixture per matrix row |
| Reviewer prose contains instructions or a tool-call object | Schema rejects executable structure; accepted prose remains `UntrustedData` | Zero payload-directed tool calls or authority changes | Prompt-injection and consumer-framing fixtures |
| Record exceeds its profile by one byte or path | Guard refuses without truncation | 100% edge-plus-one refusal | Per-profile boundary fixtures |
| Scanner or policy version is missing | Port refuses semantic persistence | Zero fallback to an older or implicit policy | Missing-version fixture |
| Rejection contains a scanner-covered credential | Reason-only receipt discards bytes and hashes | Zero corpus matches in Git and logs | Repository and diagnostic leak scan |
| A committed knowledge record bypassed its intake port | Reader revalidates and excludes it before use | Zero invalid merged records reach enquiry or distillation | Merge-bypass and quarantine corpus |

## 8. Implementation Mapping

| Element | Source owner | Build unit | Verification |
| --- | --- | --- | --- |
| Policy and schemas | Proposed `contracts/delivery/content-safety-policy.v1.yaml` and related schemas | Portable contract source | Schema and projection parity |
| Guard, scanner, and redactor | `packs/core/.apm/skills/work-loop/scripts/_content_safety.py` (Slice 1) | Work-loop skill scripts | Shared corpus and property tests |
| Inert-data wrappers | Proposed supervisor and pack support projections | Supervisor bundle and Core pack | Consumer-negative conformance |

## 9. Decisions, Alternatives, and Risks

- **Decision:** One shared policy governs all Git-backed delivery content.
- **Alternative:** Let each semantic port define redaction. **Rejected because:**
  identical content could be safe in one record and leak through another.
- **Alternative:** Trust a prompt-injection classifier. **Rejected because:** no
  detector can prove arbitrary natural language is non-instructional.
- **Risk:** A novel secret pattern passes scanning. **Mitigation:** producer
  classification, schema minimization, controlled references, and leak scans.
- **Risk:** Free text contains an unknown personal identifier. **Mitigation:**
  minimize prose, require producer classification, use controlled references
  for restricted material, and state that detection is incomplete.
- **Risk:** Redaction removes evidence meaning. **Mitigation:** opaque evidence
  rejects or uses a controlled reference instead of partial redaction.
- **Risk:** A consumer drops the inert wrapper at 3 a.m. **Mitigation:** unknown
  consumer capability refuses, and negative conformance exercises tool denial.

## 10. Rollout, Migration, and Reversal

Ports first run the shared corpus in shadow mode against existing decisions.
Cutover requires no unexplained disagreement and consumer framing conformance;
rollback selects the prior retained policy and matching readers only when its
profile is at least as restrictive for data already admitted.

| Responsibility | Owner |
| --- | --- |
| Classification and handling policy | Security and privacy maintainers |
| Guard implementation and projection | `agentbundle` maintainers |
| Consumer conformance | Owning evidence, review, integration, or knowledge maintainer |
