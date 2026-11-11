# Delivery content safety

Every registered writer of Git-backed delivery state applies one versioned
content-safety policy before it persists text. Declared secrets and
scanner-detected personal identifiers never enter those records, and rejected
bytes are never retained. Accepted free text can be wrapped as typed data that
no consumer may treat as instruction.

The scanner is defense in depth, not proof
that prose is harmless: each writer's own schema validation and the inert
wrapper carry the structural guarantee. Perfect detection of prompt injection
or unknown personal data is not claimed.

## 1. One guard, one policy, one profile per record

The policy registry is `content-safety-policy.v1`, authored under
`contracts/delivery/` and projected to the package and the Core pack with byte
or schema parity. The guard and scanner are `_content_safety.py` in the
work-loop skill.

A record is evaluated once, under one named profile and policy
version; a missing profile blocks persistence, and nothing falls back to an
implicit profile. A policy's identity today is its version string
(`POLICY_VERSION`) and the boundary profile; folding a scanner corpus digest
into that identity is **STATUS: PLANNED**.[^d1]

| Component | Responsibility | Status |
| --- | --- | --- |
| Policy registry | Publishes classes, boundary profiles, scanner set, and limits | Implemented as `BOUNDARY_PROFILES` and `POLICY_VERSION` |
| Content-safety guard | `check_content_safety` applies a profile and returns a decision value; it persists nothing | Implemented |
| Protected-data scanner | Detects credential token shapes and direct personal identifiers inside the guard | Implemented |
| Executable-structure check | Rejects tool-call objects, shebangs, authority-shaped fields, and script, frame, object or embed tags inside the guard | Implemented |
| Inert-data wrapper | `wrap_as_untrusted` keeps accepted free text typed and separated from instructions | Implemented |
| Schema normalizer | Rejects unknown structures, YAML tags, and nesting depth | **STATUS: PLANNED**; each writer validates its own schema today |
| Redaction engine | Replaces only policy-approved structured diagnostic fields | **STATUS: PLANNED**; no redaction code exists in the guard |

The class vocabulary is `public`, `repository-internal`, `restricted`,
`credential`, and `personal`. Only the first two persist as bounded Git text;
restricted payloads use controlled references, whose authorization and
retention live outside Git state.

A credential or personal datum, declared by
the caller's `classification` argument or found by the scanner, rejects the
record without retaining payload or hash. Every shipped writer passes
`classification="repository-internal"` as a fixed value; producer-declared
classification per record is **STATUS: PLANNED**.

## 2. A record is accepted or rejected whole

1. A writer submits payload bytes, a source record identity, a profile, and a
   class.
2. `check_content_safety` runs nine steps in order: profile lookup, class check,
   UTF-8 decoding, control characters, the profile's byte cap, executable
   structure, credential patterns, personal-data patterns, and acceptance. The
   first failing step rejects the whole record.
3. On acceptance the guard returns the SHA-256 of the CRLF-normalized UTF-8
   bytes. A rejected decision cannot carry a digest.[^d3]
4. The writer owns everything the guard does not check: its schema and unknown
   fields, per-field limits (`_unknown_fields` and `MAX_FREE_TEXT_BYTES` in
   `_review_contracts.py`), and persistence of the normalized record.
5. Accepted free text can be wrapped as typed `UntrustedData`
   (`wrap_as_untrusted`).

The guard does not check nesting depth, YAML tags, or the no-prose rule of
`structured-control`, and no writer persists the admitting policy version; all
three are **STATUS: PLANNED**.

A rejection returns only source identity, profile, policy version, and a stable
reason code. A crash before a writer acknowledges leaves no record; the writer's
normal transaction recovery governs a crash after acknowledgement. The guard
keeps no state, so reprocessing under a new policy version never mutates an
accepted record.

The inert-consumption rule is that a consumer renders `UntrustedData` inside
fixed data delimiters and never concatenates it into system instructions,
commands, tool calls, paths, approvals, or authority, and that a consumer unable
to preserve that framing refuses the field. Two shipped callers use
`wrap_as_untrusted`: `_knowledge_projection.py` and the workspace MCP bridge in
`packages/agentbundle/agentbundle/workspace_mcp.py` (through the packaged
`_data/_content_safety.py` copy) for the supervisor gate question. Consumer-side
framing conformance is **STATUS: PLANNED** (§ 5).

The scanner corpus covers repository-defined credential shapes, high-confidence
token patterns, direct personal identifiers, control characters, unsafe
encodings, and structured executable forms. Natural-language instruction
detection and unknown personal data carry no completeness claim. Writer-side
schema validation and inert consumption bound what free text can do; producer
classification, reject-unknown behavior, and schema allowlists at every boundary
are **STATUS: PLANNED**.

## 3. Profiles set the size and shape limit for each boundary

| Profile | Maximum persisted content | Additional rule |
| --- | --- | --- |
| `structured-control` | 64 KiB | The guard enforces only the size cap. The allowlist of identifiers, enums, digests, numbers, and repository-relative paths, with no opaque prose, is **STATUS: PLANNED** |
| `evidence-embedded-record` | 64 KiB | Raw output is a controlled reference, never embedded |
| `review-report` | 1 MiB total, 64 KiB per free-text field | Protected data or executable or authority-shaped structure rejects the whole report; natural prose is `UntrustedData` |
| `integration-diagnostic` | 256 KiB and 1,000 conflict paths | Paths are repository-relative and classified |
| `knowledge-observation` | 64 KiB | Raw transcripts and unbounded tool output reject |
| `product-addition` | The existing result byte cap | Explicit task-added, non-ignored regular files only; repository product-admission and scanner policy apply |

The decision and contract schemas are `content-safety-decision.v1` (only
`accepted` supplies bytes to a writer, and no rejected payload metadata is
additive) and `untrusted-data.v1` (data cannot request tools, grant authority,
or alter procedure; unknown majors stay opaque). Change authority sits with the
security and privacy owners; tighter or incompatible rules need an explicit
policy version, and unknown majors refuse.

## 4. The owning writer port applies the profile, never its caller

Any new writer is closed to structured-only content until a table below names
its profile, and readers refuse or quarantine an unnamed profile. Two registries
are implemented.

`SLICE_1_WRITER_BOUNDARIES` in `_content_safety.py` is the
single declared source for the durable semantic writers and replay boundaries
below, and `tests/roster/test_content_safety_boundary_matrix.py` keeps it in
agreement with this table. `REVIEW_WRITER_BOUNDARIES` in `_review_contracts.py`
names the review writers.[^d2]

| Slice 1 writer boundaries | Required profile |
| --- | --- |
| `initial-plan-review.v1` | structured-control |
| `approval-record.v1` | structured-control |
| `reviewed-execution-envelope.v1` | structured-control |
| `security-event.v1` | structured-control |
| `semantic-evidence-transaction.v1` | structured-control |
| `evidence-receipt.v1` | evidence-embedded-record |
| `evidence-supersession.v1` | evidence-embedded-record |
| `delivery-subject.v1` | structured-control |
| `acceptance-property.v1` | structured-control |
| `acceptance-verdict.v1` | structured-control |

The last three rows are written only by the opt-in shadow compatibility
path. Each shadow record passes its profile first, and a `delivery-subject.v1`
manifest over 64 KiB is refused, so the shadow path records no subject for a
large repository. The subject is optional there and does not feed the verdict.

The review writers apply these profiles through `REVIEW_WRITER_BOUNDARIES`:

| Review writer boundary | Required profile |
| --- | --- |
| `review-subject.v1`, `review-obligation.v1` | `structured-control` |
| `review-report.v1`, `finding.v1` | `review-report` |
| `finding-assessment.v1`, `finding-disposition.v1` | `structured-control`; referenced report prose is not copied |

### Planned semantic boundaries

**STATUS: PLANNED** — These boundaries name a profile in the design but no
shipped writer calls the guard for them. They belong to the parallel result
integration of [`work-loop-result-integration.md`](work-loop-result-integration.md)
(Slice 7) and the project-knowledge intake work; the roster test does not cover
them, and cross-boundary conformance for every row is not yet built.

| Planned semantic boundary | Required profile |
| --- | --- |
| Result-integration receipt port | `structured-control` |
| Integration conflict port | `integration-diagnostic` |
| Active result-application port, before legacy acknowledgement or any Git-object write | `product-addition` for every added path |
| Subject-source task-addition admission | `product-addition` revalidation |
| Project-knowledge intake port | `knowledge-observation` |
| Project-knowledge committed-store reader | The record's declared bounded profile; unknown or missing profile quarantines |
| Reversal and build-manifest port | `structured-control` plus release provenance policy |

The `integration-diagnostic` and `product-addition` profiles exist in
`BOUNDARY_PROFILES`, and no writer applies them yet.

### Knowledge records need read-time validation

The delivery observation projector (`_knowledge_projection.py`) applies the
`knowledge-observation` profile but is not a writer: its decision is ephemeral, and delivery persists no safety
receipt, acknowledgement, or capture state. Only the project-knowledge intake
port persists admission or lifecycle state.

A record introduced by a Git merge does not carry write-time admission merely
because it is committed. The project-knowledge reader validates and quarantines
records with its own validators in `project_knowledge.py`, bounded by
`QUARANTINE_MAX_ENTRIES`, and does not call this guard. Revalidation under the
record's named profile is **STATUS: PLANNED** (the committed-store reader row
above).

## 5. Operations: the guard is a library; rollout controls are planned

The guard runs as a library in every writer in the implemented table and scales
linearly with the profile byte limit. Build tooling checks source-to-package and
source-to-pack parity once per policy change.

**STATUS: PLANNED** — The guard emits no accept or refusal counts, byte totals,
or durations. A new port will run the shared corpus in shadow mode against
existing decisions, and cutover will need no unexplained disagreement and
consumer-framing conformance.

Rollback selects the prior retained policy and
matching readers only when its profile is at least as restrictive for data
already admitted. Consumer support for `untrusted-data.v1` is required before a
writer rolls out.

| Responsibility | Owner |
| --- | --- |
| Classification and handling policy | Security and privacy maintainers |
| Guard implementation and projection | `agentbundle` maintainers |
| Consumer conformance | The owning evidence, review, integration, or knowledge maintainer |

## 6. Quality scenarios and the fixtures that verify them

The roster test covers the Slice 1 registry row for row, and
`packs/core/tests/skills/work-loop/test_content_safety.py` exercises the guard.
Fixtures for the planned ports, the missing-version case, and consumer framing
are the design's targets and carry **STATUS: PLANNED**.

| Stimulus | Response | Verification |
| --- | --- | --- |
| Same protected payload reaches four ports | Shared policy returns the same refusal | Shared credential, personal-data, encoding, and size corpus |
| A writer omits or names the wrong profile | Owning port refuses before append | One negative fixture per table row |
| Reviewer prose contains instructions or a tool-call object | Schema rejects executable structure; accepted prose stays `UntrustedData` | Prompt-injection and consumer-framing fixtures |
| Record exceeds its profile by one byte or path | Guard refuses without truncation | Per-profile boundary fixtures |
| Profile is missing | Guard returns `rejected-missing-profile`; the port refuses persistence | Missing-profile fixture |
| Rejection contains a scanner-covered credential | Reason-only receipt discards bytes and hashes | Repository and diagnostic leak scan |
| A committed knowledge record bypassed its intake port | Reader revalidates and excludes it | Merge-bypass and quarantine corpus |

## 7. Risks and their mitigations

- A novel secret pattern passes scanning. Mitigation: producer classification,
  schema minimization, controlled references, and leak scans.
- Free text contains an unknown personal identifier. Mitigation: minimize prose,
  require producer classification, use controlled references for restricted
  material. Detection is incomplete by design.
- Redaction removes evidence meaning. Mitigation: opaque evidence rejects or
  uses a controlled reference instead of partial redaction.
- A consumer drops the inert wrapper. Mitigation: an unknown consumer capability
  refuses, and negative conformance exercises tool denial.

[^d1]: `contracts/delivery/content-safety-policy.v1.schema.json`, `content-safety-decision.v1.schema.json`, `untrusted-data.v1.schema.json`; `packs/core/.apm/skills/work-loop/scripts/_content_safety.py` (`BOUNDARY_PROFILES`, `check_content_safety`, `wrap_as_untrusted`, `POLICY_VERSION`).
[^d2]: `_content_safety.py` (`SLICE_1_WRITER_BOUNDARIES`); consumers include `_evidence_store.py`, `_review_contracts.py`, `_knowledge_projection.py`, `_policy_import.py`, and `_security_events.py` in the same directory.
[^d3]: `_content_safety.py` (`ContentSafetyDecision`, whose constructor refuses a digest on rejection and requires one on acceptance).

## Governing records

- [`docs/specs/acceptance-authority-and-evidence/spec.md`](../specs/acceptance-authority-and-evidence/spec.md): evidence and writer boundaries.
- [`docs/specs/structured-review-boundary/spec.md`](../specs/structured-review-boundary/spec.md): review writers.
- [`docs/specs/delivery-knowledge-projection/spec.md`](../specs/delivery-knowledge-projection/spec.md): the knowledge observation projector.
- [`docs/specs/execution-supervisor-core/spec.md`](../specs/execution-supervisor-core/spec.md): supervisor event records.
