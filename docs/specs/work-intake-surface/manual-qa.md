# Manual QA: work-intake cold-adopter flows

- Date: 2026-08-15
- Pack: core 2.6.0
- Surface: Codex projection from a fresh core-only `agentbundle install`
- Method: clean-workspace installation and backend execution, contract and
  failure-injection checks, and live conversational walkthroughs. The first
  walkthrough exposed release-blocking drift; its evidence, fixes, and fresh
  corrective reruns are recorded below.

## Setup

A clean temporary workspace received only `core` through the Codex adapter.
Installation completed without catalogue diagnostics and projected
`work-intake`, its routing fixtures, its minimal-intent asset and transaction
coordinator, plus the `capture-work` compatibility alias.

The installed `workspace-status` backend ran against the untouched adopter
seed. It returned schema version 1, `workspace_present: true`, empty lifecycle
collections, and no findings. The SHA-256 of `workspace.toml` was identical
before and after
(`86e9327a283e3bfcbc9553377bc0df78add418711980533bc081cc05577d5754`),
proving the installed status path was
read-only.

## Flows

| User request | Contract result | Membership | Processor | Verified evidence |
| --- | --- | --- | --- | --- |
| `Start work on adding export retention controls for workspace owners.` | One independently shippable contract routes to `docs/specs/export-retention/spec.md` | Awaiting approval; executable only after an Approved spec and sibling plan exist | `new-spec` | Fresh v4 conversation plus installed reconciliation reporting only `unapproved_spec` |
| `Remember that workspace owners need export retention controls. Do not start implementation.` | Draft intent at `docs/product/intents/export-retention-controls.md` | Draft, non-dispatchable | None | Fresh v5 materialization plus installed reconciliation with no findings |
| `workspace-status` | Existing lifecycle, findings, and next actions | Unchanged | `workspace-status` | Fresh v4 conversation plus unchanged before/after checksum |
| `Refresh requirements for docs/specs/export-retention/spec.md.` | `requirements refresh unavailable` | Unchanged | Existing processor is resolved but not invoked for refresh | Fresh v4 existing-target conversation plus unchanged artifact and workspace checksums |

## Fail-closed observations

- Ambiguous content remains Draft or produces one smallest-missing-choice
  question; it does not become Ready by inference.
- Absolute, traversing, symlink-escaped, and symlink-looping artifact targets
  are rejected by the transaction helper before any write callback.
- Invalid secret-, credential-, prompt-, instruction-, and raw-payload-shaped
  envelopes produce no artifact, stdout, or stderr. A confidentiality mismatch
  likewise stops before materialization, while prompt-like evidence is omitted
  from minimal-intent rendering and common personal/secret values are redacted.
- A failed registration rolls back the artifact when safe or leaves an explicit
  non-dispatchable reconciliation finding. Partial state never dispatches.
- Executable filesystem failure injection covers partial artifact writes,
  partial registration writes, rollback failure, reconciliation recording, and
  successful dispatch ordering. A processor exception returns the safe
  `dispatch_failed` state without raw exception text while preserving the two
  already-durable writes.
- `capture-work` announces deprecation and forwards to `work-intake`; it has no
  independent classifier or legacy storage path.

## First conversational walkthrough

A reviewer ran all four prompts in one installed core-only workspace. Status
passed through without mutation. The remaining flows did not satisfy the
published walkthrough:

- Start classified the named actor-plus-capability request as a Draft intent
  instead of invoking `new-spec` for the direct spec promised by the README and
  routing contract.
- The generated intent initially used `Status: Draft`, which the canonical
  workspace parser does not recognize; the reviewer corrected it to
  `- **Status:** Draft` before reconciliation could pass.
- Remember reused the start artifact, so it did not independently prove fresh
  Draft materialization.
- Refresh ran against a missing target because start had not created the
  expected spec, so it proved no mutation but not existing-target resolution.

Root-cause coverage now requires the minimal-intent asset and renderer to round
trip through the canonical preamble parser. The published start prompt is also
pinned as an actor-plus-capability direct-spec eval; missing product details are
owned by `new-spec` elicitation and do not demote that request to an intent.

## Corrective reruns

Each prompt was exercised in its own fresh core-only workspace:

- Start created a Draft `spec.md` and sibling Drafting `plan.md`, registered the
  spec in `ini-001.work.queue`, invoked `new-spec`, and stopped for requirements
  confirmation. Installed reconciliation reported only `unapproved_spec`; no
  implementation started.
- Remember created a canonical Draft intent and stopped without a processor.
  The first v4 registration copied normalized `source.locator` directly and the
  target parser correctly rejected it as `invalid_entry`. The source-mapping
  boundary now writes workspace-entry `source.ref`; a fresh v5 rerun reconciled
  with no findings and remained non-dispatchable. The resulting workspace and
  artifact SHA-256 values were
  `e24609e0ee98c6024443040eec34066b5c2844f2491e68875aabea4b2f8e2a6b` and
  `c710e533df74dc2d739a18f0abc973f103020ec4a510eb7f175d6babb01f671e`.
- Status returned empty lifecycle collections and no findings. Its
  `workspace.toml` checksum remained
  `86e9327a283e3bfcbc9553377bc0df78add418711980533bc081cc05577d5754`.
- Refresh resolved the existing Draft spec and `new-spec`, reported refresh
  unavailable, and changed nothing. Workspace and spec checksums remained
  `b69aed19a0ff234d96256101a751bd851eeb2e91e17ccd0e18101da7dd41f587`
  and `4d61195a755131bae47a31df6b5229af6428295542e12ed1e205c06d40a6f59e`.

The cold install also exposed an unconditional link from the composed
`AGENTS.md` to maintainer-only `AGENTS.local.md`. The footer now describes that
file as optional without linking to an absent path. A separate fresh install
verified that every relative link in the composed guidance resolves.

## Review disposition

- Applied: canonical intent preamble, actor-plus-capability direct-spec routing,
  structurally inert single-pass template rendering, normalized-to-workspace
  source mapping, conditional local-guidance wording, and complete source-map
  contract assertions.
- Deferred: none.
- Surfaced: the local SAST/SCA leg cannot provision its Python audit environment
  in this enterprise runtime. All offline build-check stages pass; CI must run
  the scanner leg before merge.

## Documentation result

The generated technical site exposed all three new pages under the Core guide
navigation. The marketing site, technical site, search index, and rendered
internal-link audit completed successfully.
