# Maintaining work intake and refresh

This reference is for catalogue maintainers changing an intake adapter, the
shared router, dispatch, refresh, or the `workspace-status` repair. The public behavior is one pipeline; each component owns a narrow part.

## Responsibility map

| Component | Owns | Must not own |
| --- | --- | --- |
| Source adapter | Bounded acquisition, provenance, profile-version hints, strict normalization | Artifact classification, repository writes, authorization |
| Upstream shaping producer | Bounded handoff content after its confirmed delivery gate; capability-negotiated portable fallback | Core imports, destination self-certification, lifecycle or delivery approval |
| `work-intake` | Neutral classification, artifact-before-dispatch sequencing, processor selection | Intent or brief authoring, tracker vocabulary, source credentials, legacy conversion |
| `intake-intent` | Minimum repository-intent creation and admission | Product-level shaping, brief lifecycle, downstream implementation |
| `author-delivery-brief` | Draft creation, Ready review, confirmed spec slices, and the six-state brief lifecycle contract | Neutral classification, implementation, governance-reference rollups, terminal closeout |
| Handoff admission | Closed-field validation, source/revision consistency, exact resolver-result reuse, stable zero-effect disposition | Raw source storage, external acquisition, new artifact/lifecycle kinds |
| Semantic-surface resolver | Six-step destination precedence, mandatory-policy rejection, locator confinement, complete read-only result | Candidate acquisition, artifact applicability, authoring method, lifecycle effects |
| Architect / governance owner | Role selection and the existing architecture or ADR method after resolution | Reimplementing precedence, coercing external locators, routing architecture into product prose |
| Canonical artifact | Requirements, decisions, acceptance state, `Status:` and `Depends on:` headers, tracker-origin authority block | A second record of its own lifecycle |
| `workspace.toml` | Leftover entries awaiting `repair-plan` and `repair-apply` | Requirements, new entries, or comment-backed routing |
| Processor | The artifact-specific workflow selected by the route | Reclassifying the source from tracker object names |
| Refresh processor | Exact-profile acquire/map/compare and declared local or remote coordination capability | Reusing intake authorization or bypassing lifecycle locks |
| `workspace-status` | `repair-plan` and `repair-apply` for leftover `workspace.toml` entries | Status reporting, authoring artifacts, or human route/authorization inputs |
| `dispatch.py` (`work-loop`) | Ready, active, and blocked specs from `Status:` and `Depends on:`; `--captured` listing | Writes |
| `close-work` | Explicit `Shipped`, `Withdrawn`, or `Cancelled` brief closeout after durable-context verification | Inferring completion from child rollup or rewriting child statuses |

Readiness comes from the artifact headers. Only an Approved spec with an
existing sibling plan is ready, and only a spec whose `Status:` is
`Implementing` is active. `workspace.toml` entries that remain are repair input:
comments, summaries, order, tracker labels, and profile hints are non-semantic.

## Maintaining brief lifecycle state

A brief's lifecycle is its `Status:` alone, repo-origin or tracker-origin, and it has no entry. Reconcile
child progress with this closed matrix:

| Brief state | Required child evidence |
| --- | --- |
| `Draft`, `Ready`, `Withdrawn` | No child is `Implementing` or `Shipped` |
| `Executing`, `Cancelled` | At least one child is `Implementing` or `Shipped` |
| `Shipped` | The map is non-empty and every mapped child is `Shipped` |

`Withdrawn` is the pre-execution terminal state. `Cancelled` is the
post-execution terminal state. Do not collapse either into `Shipped`, and do not
move an open brief back to `Ready` after a child ships. An all-shipped current
map remains `Executing` until the outcome owner confirms there are no remaining
unmaterialized slices and `close-work` performs the terminal update.

For a repair, change the brief header in one reviewed change. Preserve the child
spec statuses and source authority. Rerun `dispatch.py` and
`lint-brief-coverage.py`; never edit Spec-map status cells to make the checks
pass.

## Adapter contract

An adapter validates its destination and resource budget, acquires only bounded
fields, treats all source content as untrusted data, and emits
`normalized-intake.v1`. The shared router alone decides intent, brief, spec,
defect, direct-light, Draft-with-gaps, status, remember, or refresh behavior.
Equivalent normalized content must produce the same route for Jira, Jira Align,
GitHub, and Linear.

The optional `handoff` object is additive to `normalized-intake.v1`. Its
required arrays are boundaries, non-goals, dependencies, design context, and
delivery questions; empty arrays remain explicit and valid. Do not add raw
payload, instruction, prompt, secret, credential, lifecycle, or approval
fields. A producer sends the object only when the current Core invocation
advertises `normalized-intake.v1#handoff`. Otherwise it renders the same
bounded content and omits the unsupported object.

Core derives the semantic role from validated content: one independently
shippable feature is a delivery contract, while multi-spec or cross-repository
work is a delivery brief. Pass caller-acquired closed candidates to the
semantic-surface resolver and preserve its result unchanged. Never accept a
producer-shaped replacement for that result.

Architecture consumers use the same boundary without changing it. Proposed or
future designs request `architecture-design`; implemented-system descriptions
request `current-architecture`; ADRs request `decision-record`. Resolve each
applicable artifact independently. A mandatory policy may reject an explicit
destination, and configuration remains optional candidate evidence. The
resolver never decides that an artifact should exist: Architect and `new-adr`
retain their existing applicability, authoring, preview, and confirmation gates.
A boundary change may yield current-architecture and decision-record handoffs,
but never implies product prose.

For a repository locator, read content only after resolution through
`read_confined_regular_file` or the tested standalone equivalent. Refuse
symlinks, reparse points, multiply linked or non-regular files, oversized
content, identity swaps, and uncertain confinement. For an external locator,
perform no fetch, search, probe, DNS, tracker, credential, shell, or
locator-derived filesystem operation. Only already-acquired bounded content at
the matching pinned revision can continue.

Intake adapters are read-only at the tracker boundary. A configured refresh
processor is a separate capability. It resolves by exact profile ID and version;
missing or mismatched registration returns a no-effect result. Any supported
remote coordination action needs a fresh confirmation for its exact action,
target, profile, and payload digest.

## Authority and refresh

Source mode is closed to `repo-origin` or `tracker-origin`.
Tracker-origin artifacts carry exactly one closed `source-authority.v1` block.
Its field ownership map assigns each field to `source` or `local`, while
compared/accepted revisions, decisions, conflicts, and receipts make changes
auditable. Repository-origin work remains locally authoritative.

Lifecycle locks are enforced by the refresh processor, not inferred by an
adapter. Draft, Accepted, Ready, Approved, Implementing, Executing, Shipped,
Withdrawn, and Cancelled must each remain represented in the versioned
evaluation matrix. Local field decisions and remote coordination are separate
effects and separate evidence.

## Dispatch findings

Dispatch finding codes are public behavior. Add or change one only with its stable safe
next action, CLI projection, tests, guide reference, and evaluation result.
Dispatch fails closed for malformed headers, missing plans, invalid
transitions or provenance, unresolved refresh state, and dependency failures.
It refuses with `unmigrated_workspace` while a `workspace.toml` entry remains,
and a former legacy shape surfaces as `unsupported_legacy`; both stay
non-dispatchable and point to `repair-plan`. Unknown or private shapes also
return a manual-routing finding without mutation.

## Repair

`workspace-status` runs `repair-plan` and `repair-apply`. `repair-plan` is
read-only apart from its plan file. `repair-apply` needs explicit confirmation
and rechecks each operation before it writes. Each operation moves a fact onto
its artifact and drops the entry; `references/mutate.md` in the skill owns the
shapes. An adopter with a recorded migration operation
finishes or rolls it back on the old version first, as the
[upgrade guide](../../../guides/core/how-to/upgrade-from-a-workspace-registry.md)
says.

## Release discipline

New writers, receipts, guides, and seeds emit only canonical names.
`author-brief` forwards only to `author-delivery-brief create`, and
`receive-brief` forwards only to `author-delivery-brief continue`. Each alias
emits one deprecation notice and adds no classifier, writer, reviewer, tool,
or boundary. `capture-work` is removed in Core 3.0.0. The brief aliases stay
for at least two minor Core releases and 90 days, whichever is later. Removal
requires advance notice and a named Approver decision at the first eligible
release.

Dispatch no longer accepts former legacy workspace shapes; adopters rewrite
them in canonical form by hand, then run `repair-plan`.

## Evaluation and release checklist

When any component changes:

1. Update the shared routing matrix and the affected profile matrix.
2. Preserve acquisition → normalization → routing → authority/refresh coverage.
   Refresh remains writable for Draft/Accepted/Ready/Approved, locked for
   Implementing/Executing/Shipped, and returns the stable locked codes
   `withdrawn_requirements_locked` or `cancelled_requirements_locked` for the
   two terminated brief states.
3. Run the integrated evaluator in two independent clean roots and require
   byte-identical normalized results and next actions.
4. Run the `workspace-status` repair planning, apply, and CLI tests, including
   failure seams.
5. Update the owning pack and plugin versions together, add user-facing release
   notes, then regenerate self-hosted projections and marketplace metadata.
6. Build marketing before docs, audit emitted links, and inspect generated
   canonical and compatibility routes rather than editing generated output.
7. For a handoff change, run the completion matrix twice and require
   byte-identical records plus unchanged filesystem fingerprints. Check
   repository brief/contract, acquired external content, aliases, standalone
   direct/durable routes, absent and older Core fallback, ambiguity, absence,
   policy conflict, unsafe paths, symlink escape/loop, prompt-like data,
   authority independence, and optional configuration.
8. Confirm every producer and consumer that reads offered content declares
   `filesystem_read_untrusted`, and inspect each generated adapter projection
   for the same boundary metadata.
9. For an architecture or decision consumer, run the real-resolver portability
   matrix, verify custom repository and external destinations, and prove
   refusal, ambiguity, absence, and unsafe locators perform no directory,
   numbering, index, configuration, or artifact write. Exercise Architect's
   chat-only, personal-workspace, compatible-repository, and repository-handoff
   modes in the installed projection.

The schemas under `contracts/jsonschema/`, the scripts under the owning
`.apm/skills/` directories, and their construction tests are mechanically
authoritative. This page explains how those contracts fit together; it does not
replace them.
