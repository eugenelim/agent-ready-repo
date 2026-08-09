# ADR-0078: Standalone intake with an artifact-backed workspace index

- **Status:** Accepted
- **Date:** 2026-08-09
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0083](../rfc/0083-work-intake-and-artifact-routing.md),
  [ADR-0030](0030-consolidated-pack-output-layout-contract.md),
  [ADR-0051](0051-workspace-toml-toml-format-and-main-branch-coordination.md),
  [ADR-0076](0076-briefs-persist-dispatch-starts-from-specs.md)

## Decision summary

- **Decision:** Core will expose standalone `work-intake`, own the shared
  minimal intent contract, and use `workspace.toml` only as a deterministic
  index of canonical artifacts and lifecycle facts.
- **Because:** a cold-start session must reach the same route without an
  optional shaping pack, comment interpretation, or prior conversational
  context.
- **Applies to:** shared intake, minimal intents, the `[core]` relocatable
  layout, workspace entries and reconciliation, status, and work dispatch.
- **Tradeoff accepted:** every captured item must materialize a canonical
  artifact before it can become executable, and index/artifact drift must be
  reconciled explicitly.
- **Revisit if:** a canonical artifact plus structured index cannot reproduce
  routing and dispatch across supported adopters, or repository-confined
  `[core]` layout relocation cannot serve a supported installation shape.

## Context

Incoming work currently reaches several public skills with different routing
rules. `capture-work` can register a future `spec/<slug>` without creating its
spec and relies on comments rich enough for a later session to reconstruct the
contract. Tracker adapters also make local artifact choices independently. A
fresh session can therefore see apparently ready work while lacking the files
needed to reproduce why it is ready or what should execute.

Putting the missing requirements into `workspace.toml` would make parsing more
deterministic but would create a second requirements store beside intents,
briefs, and specs. Scanning the repository without an index avoids duplicated
requirements but loses explicit lifecycle membership, provenance, and hard
dependencies. Neither option provides one clear public entry point for an
adopter that uses no optional shaping pack.

ADR-0076 establishes the key execution boundary: a brief may persist without
specs, and dispatch starts only from an existing spec and plan. ADR-0051 keeps
`workspace.toml` as TOML and as the main-branch coordination artifact, but its
comments previously carried enough meaning to reconstruct work. ADR-0030
provides a shared relocatable output contract but leaves core intake as a
possible future consumer.

RFC-0083 resolves these as one intake-boundary decision: core owns a standalone
router and the smallest shared intent it may need to create; canonical artifacts
own requirements; and the workspace records only the structured facts required
to find, sequence, display, and reconcile them.

## Decision

**We will make `work-intake` the standalone core entry point, place the minimal
intent contract in that shared layer, and treat `workspace.toml` as a
deterministic index over canonical artifacts rather than as a requirements
store.**

`work-intake` exposes four adopter intents:

- **Start or do this:** classify normalized content, materialize the canonical
  artifact, register it, and invoke the processor that owns the next step.
- **Remember this for later:** materialize a Draft canonical artifact, register
  non-executable lifecycle state, and stop.
- **Where are we?:** render structured status and next actions without creating
  an artifact.
- **Refresh this from the source:** resolve an existing artifact and invoke its
  configured refresh processor; missing support fails closed.

The router is part of core and has no dependency on an optional discovery,
prioritization, or shaping pack. Optional workflows may enrich the same
artifacts by reference, but they cannot redefine their shared fields, identity,
classification, or lifecycle semantics. `capture-work` becomes a temporary
compatibility alias rather than a second permanent intake meaning.

Core owns the minimal intent contract required when intake identifies a product
outcome or opportunity. It contains `Status`, `Level`, `Outcome`, `Opportunity`,
`Assumptions`, and `Source`. Its shared lifecycle is Draft, Accepted, Fulfilled,
or Superseded. Optional workflows may expose more detailed working stages only
if they map them to those shared states at the intake boundary.

Shared intake opts into ADR-0030's `agentbundle-layout.toml` as a `[core]`
consumer. The default parent is `docs/product`, producing
`docs/product/intents/<slug>.md`. An adopter may relocate that parent through
the existing layout contract without changing artifact identity or routing,
but the resolved parent must remain inside the repository. Intake refuses an
out-of-repository parent because workspace entries require portable,
repository-relative paths.

Every target-state workspace lifecycle entry records exactly these semantic
facts:

- `path`: repository-relative path to a canonical artifact;
- `kind`: `intent | research | design | brief | spec | defect`;
- `source`: origin mode, durable source reference and revision, and applicable
  parent or coordination reference;
- `summary`: display-only text; and
- `needs`: typed hard artifact dependencies.

The canonical artifact owns requirements, detailed source authority, acceptance
decisions, and closure evidence. `workspace.toml` owns local lifecycle
membership and the minimal structured index needed for routing and display.
Comments may explain an entry to a person, but comments, `summary`, list order,
nearby prose, tracker vocabulary, and previous-session memory have no routing,
readiness, dependency, or processor meaning. This narrows ADR-0051's comment
consequence without changing its TOML format or main-branch coordination
decision.

Reconciliation compares index membership with the files, statuses, plans,
provenance, and dependencies it names. Missing artifacts or plans, unsafe paths,
mismatched brief/spec links, duplicate membership, unknown kinds, malformed
entries, unresolved source conflicts, and impossible lifecycle transitions are
findings. Readers fail closed: they report a non-dispatchable entry and the
smallest safe next action; they never reconstruct a contract from comments.

Carrying ADR-0076 forward, an entry is dispatchable only when it appears exactly
once in an active initiative's work queue, names an existing Approved spec and
sibling plan, has consistent source and brief provenance, has no reconciliation
finding or unresolved refresh conflict, and has every typed hard dependency
satisfied. Claiming and lifecycle transitions are guarded operations over the
spec and workspace state. A remembered Draft remains visible but cannot become
executable without materializing and approving its contract.

## Decision drivers

- **Standalone adoption:** core intake must work when no optional product or
  shaping pack is installed.
- **Deterministic cold starts:** the same repository files must produce the same
  route, lifecycle, dependency, and dispatch results in every session.
- **One authoritative home per fact:** artifacts own requirements; the workspace
  owns index and lifecycle facts.
- **Safe execution:** no agent may begin implementation from comments, missing
  files, or an inferred contract.
- **Relocatable but portable output:** adopters may move intent output through
  the shared layout contract without producing unindexable external paths.
- **Visible drift:** mismatches must become findings rather than implicit repair
  or fallback behavior.

## Consequences

**Positive:**

- Adopters get one public route for starting, deferring, checking, and
  refreshing work.
- Core can materialize a minimal product intent without an optional pack.
- Every executable work item has a reviewable canonical contract and plan.
- Changing comments, summaries, ordering, or tracker labels cannot change
  routing.
- `workspace-status` and `work-loop` can share one deterministic reconciliation
  result.
- Artifact paths remain portable across repository clones.

**Negative:**

- Remembering work now creates a Draft artifact rather than only a lightweight
  queue comment.
- Every writer must update the canonical artifact and structured index
  consistently.
- The same relationship may appear in artifact metadata and the index, so
  reconciliation must detect mismatches.
- Legacy comment-rich and shorthand entries require a bounded compatibility
  reader and human-reviewed migration.
- Core becomes another consumer of the shared layout contract and must enforce
  repository confinement at its write boundary.

**Revisit if:** a canonical artifact plus structured index cannot reproduce
routing and dispatch across supported adopters, or repository-confined `[core]`
layout relocation cannot serve a supported installation shape.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** shared contract fixtures prove identical content routes
  identically across entry points; minimal intents validate at the default and
  relocated repository-confined paths; changing comments, summaries, or order
  leaves classification and dependencies unchanged; malformed or inconsistent
  entries fail closed; every dispatchable entry resolves to an Approved
  `spec.md` and sibling `plan.md`; two clean reads produce identical lifecycle
  and reconciliation results.
- **Owner:** maintainers

## Alternatives considered

**Keep the existing public entry points.** Rejected because users must know
internal skill boundaries and semantically equivalent input routes differently.

**Add `work-intake` beside `capture-work` permanently.** Rejected because two
public capture meanings preserve the ambiguity instead of resolving it.

**Leave classification inside each tracker adapter.** Rejected because adapter
drift becomes structural and external vocabulary determines local ontology.

**Require an optional shaping pack to own intake and intents.** Rejected because
core adopters must be able to start or remember work without adopting a
particular upstream method.

**Keep requirements in workspace comments.** Rejected because comments are
untyped, unvalidated, and cannot support reproducible cold-start dispatch.

**Copy complete requirements into `workspace.toml`.** Rejected because it
duplicates canonical artifacts and creates a second requirements schema and
authority surface.

**Discover everything by scanning artifacts.** Rejected because scanning alone
does not encode explicit lifecycle membership, provenance, or hard dependencies.

## References

- [RFC-0083](../rfc/0083-work-intake-and-artifact-routing.md) — accepted intake,
  artifact, workspace, and rollout decision.
- [ADR-0030](0030-consolidated-pack-output-layout-contract.md) — shared
  relocatable output contract extended here with a `[core]` consumer.
- [ADR-0051](0051-workspace-toml-toml-format-and-main-branch-coordination.md) —
  TOML format and main-branch coordination decision whose comment consequence
  is narrowed here.
- [ADR-0076](0076-briefs-persist-dispatch-starts-from-specs.md) — persistent
  briefs and spec/plan-only dispatch carried forward here.
