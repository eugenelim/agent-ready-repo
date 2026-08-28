# ADR-0076: Briefs persist; dispatch starts from specs

- **Status:** Accepted (superseded in part by [ADR-0098](0098-artifact-admission-and-delivery-brief-lifecycle.md) — public readiness and selected-slice handling move to `author-delivery-brief continue`; brief persistence and spec/plan-only dispatch stand)
- **Date:** 2026-08-08
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Carried forward by:** ADR-0078 records standalone intake and deterministic workspace indexing while preserving this ADR's persistent-brief and spec/plan-only dispatch rules.
- **Related:** [ADR-0009](0009-product-brief-layer-and-plan-owned-lld.md),
  [ADR-0019](0019-product-intent-ontology-and-brief-projection.md),
  [ADR-0033](0033-intent-level-open-recognized-set-decoupled-from-scale.md),
  [ADR-0051](0051-workspace-toml-toml-format-and-main-branch-coordination.md),
  [`work-intake-and-artifact-routing.md`](../architecture/work-intake-and-artifact-routing.md)

## Decision summary

- **Decision:** An accepted brief may remain Ready without specs; only selected
  delivery slices become spec/plan pairs, and agents may dispatch work only from
  structured workspace entries that reference those files.
- **Because:** a cold-start session needs a complete, reviewable contract and
  deterministic routing rather than requirements reconstructed from comments.
- **Applies to:** briefs, derived specs and plans, `workspace.toml`,
  `receive-brief`, `new-spec`, `workspace-status`, and `work-loop`.
- **Tradeoff accepted:** choosing work from a brief requires an explicit
  materialization step before execution.
- **Revisit if:** adopters need briefs themselves to be executable, or a
  spec/plan pair stops being the smallest safe dispatch unit.

## Context

A brief and a spec answer different questions. A brief holds a shared outcome,
its decomposition, and work that may be deferred. A spec is the complete
contract for one independently shippable slice. Its plan describes how that
contract will be built and verified.

The current workspace model weakens this distinction. `capture-work` creates no
spec artifact and instead asks for comments detailed enough that a later session
can reconstruct one. Other workflow paths register tracker collections or brief
prose before a shippable contract exists. Two sessions can therefore interpret
the same queue differently because routing depends on prose, nearby comments, or
context retained from an earlier conversation.

Forcing the opposite extreme is also wrong. A valid brief may sit for weeks or
months before the team chooses a slice. Creating every possible spec and plan as
soon as the brief is accepted produces speculative delivery contracts that will
age before anybody intends to build them.

This decision refines ADR-0019 part 2. A feature does not automatically become an
immediately executable brief. A brief may persist as the repo-local planning
envelope; selected delivery materializes below it. ADR-0019 otherwise remains
Accepted. ADR-0009's brief layer and plan-owned LLD, ADR-0033's open `Level`
model, and ADR-0051's TOML/main-branch decisions remain in force.

## Decision

**We will allow accepted briefs to persist without specs, materialize only
selected delivery slices as spec/plan pairs, and use `workspace.toml` as a
deterministic index over those artifacts rather than as a requirements store.**

A brief follows this lifecycle:

- **Draft:** its load-bearing fields or acceptance are incomplete.
- **Ready:** it is accepted and has no active child spec. It may have no specs,
  queued specs, or shipped specs, and may remain Ready indefinitely.
- **Executing:** at least one derived spec is active.
- **Shipped:** the brief is explicitly closed, no in-scope work remains, and
  every materialized child spec is shipped.

When delivery is chosen from a Ready brief:

1. `receive-brief` presents the proposed cut for the current delivery.
2. The user confirms the independently shippable slices.
3. `new-spec` creates `spec.md` and `plan.md` for each selected slice.
4. Each spec records its `Brief:` back-link and source provenance.
5. Structured work entries are added only after the files exist.
6. `work-loop` reads the spec and plan; it never reconstructs requirements from
   workspace comments.
7. After the current batch ships, the brief returns to Ready if scope remains.

Deferred work stays in the brief. It does not need a placeholder work entry and
must not be stored only in a comment.

Routing may use only parsed entry fields, file existence, machine-readable
artifact status, and explicit hard dependencies. Comment text, list order,
nearby prose, and prior-session memory have no routing meaning.

A dispatchable entry must reference an existing `spec.md` with a sibling
`plan.md`. A derived spec's `Brief:` value must match the brief path recorded in
the workspace source index. Missing artifacts, mismatched links, malformed
entries, duplicate lifecycle membership, and impossible transitions are
reconciliation failures. Readers fail closed; they never fall back to comments.

## Decision drivers

- **Deterministic cold starts.** The same files must produce the same ready,
  blocked, active, and reconciliation sets in every session.
- **One responsibility per artifact.** Briefs hold shared intent and deferred
  scope; specs hold delivery contracts; plans hold build strategy; the workspace
  indexes and sequences them.
- **Safe dispatch.** An agent begins only from a reviewed, existing contract.
- **Useful deferral.** Accepting a brief must not force speculative specs.
- **Visible drift.** Broken references become findings rather than hidden
  inference.

## Consequences

**Positive:**

- A Ready brief remains useful even when no delivery work has been selected.
- Work cannot become executable until its spec and plan exist.
- Deleting or rewriting comments cannot change routing.
- `workspace-status` can report missing files and inconsistent provenance
  mechanically.
- A completed delivery batch does not falsely close a brief that still has
  deferred scope.

**Negative:**

- Starting work from a brief takes an extra, explicit materialization step.
- The brief relationship appears in both spec metadata and the workspace index;
  readers must reconcile mismatches.
- Ready briefs can age. Tracker-origin sources may need a reviewed refresh before
  a deferred slice is materialized.
- Existing comment-rich queue entries cannot remain dispatchable and will need
  migration or classification as non-dispatchable captures.
- `brief_queue` needs a structured Shipped state to retain completed history.

**Revisit if:** adopters need briefs themselves to be executable, or a spec/plan
pair stops being the smallest safe dispatch unit.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** every dispatchable entry resolves to `spec.md` and sibling
  `plan.md`; brief links agree; changing comments leaves routing unchanged; two
  reads of the same tree return identical lifecycle and reconciliation sets; a
  Ready brief with no specs remains valid and non-dispatchable.
- **Owner:** maintainers

## Alternatives considered

**Dispatch briefs directly.** `work-loop` could infer a spec from the brief when
execution starts. Rejected because a multi-spec brief does not identify one
complete delivery contract, and inference would vary across sessions.

**Create all specs when a brief becomes Ready.** This makes every planned slice
immediately indexable. Rejected because it turns deferred work into speculative
contracts that drift before implementation.

**Keep requirements in workspace comments.** This is cheap at capture time and
keeps everything in one file. Rejected because comments are untyped,
unvalidated, and not a stable contract boundary.

**Store full requirements as structured TOML.** This could make workspace-only
dispatch deterministic. Rejected because it duplicates briefs and specs,
creates a second requirements schema, and forces workspace changes whenever
requirements change.

## References

- [`docs/architecture/work-intake-and-artifact-routing.md`](../architecture/work-intake-and-artifact-routing.md)
- [ADR-0009](0009-product-brief-layer-and-plan-owned-lld.md)
- [ADR-0019](0019-product-intent-ontology-and-brief-projection.md)
- [ADR-0033](0033-intent-level-open-recognized-set-decoupled-from-scale.md)
- [ADR-0051](0051-workspace-toml-toml-format-and-main-branch-coordination.md)
