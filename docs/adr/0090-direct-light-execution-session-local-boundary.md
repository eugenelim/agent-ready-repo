# ADR-0090: Direct-light execution is session-local outside workspace dispatch

- **Status:** Accepted
- **Date:** 2026-08-20
- **Decision-makers:** eugenelim
- **Supersedes:** ADR-0014 (in part — light mode's persisted inline-spec obligation; its trigger set, light/full selection, and no-new-executable-code, skill, or artifact-type boundary stand); ADR-0076 (in part — its dispatch-only wording; workspace dispatch remains spec-and-plan based); ADR-0078 (in part — its start-route materialization rule and its "every executable work item has a reviewable canonical contract and plan" consequence, both narrowed to workspace-indexed items; workspace-entry dispatchability stands)
- **Related:** RFC-0092; ADR-0014; ADR-0076; ADR-0078; ADR-0088

## Decision summary

- **Decision:** Persisted spec-and-plan contracts remain mandatory for workspace-indexed, queued, or resumable work; an explicit direct-light request is session-local, never indexed, and never eligible for argless dispatch or fresh-session resumption.
- **Because:** durable coordination needs a durable contract, while a bounded current-session request does not.
- **Applies to:** `work-loop`, `work-intake`, `workspace.toml`, workspace dispatch, and direct-light execution.
- **Tradeoff accepted:** eligibility is caller-declared doctrine with eval coverage, not a technical provenance guarantee.
- **Revisit if:** a runtime can distinguish trusted invocation provenance from undifferentiated prompt context.

## Context

Three accepted clauses require a narrower scope after RFC-0092 accepts direct-light execution. The decision does not make direct-light a workspace route: it has no workspace entry, no durable artifact, no argless dispatch, and no fresh-session resumption.

This is one boundary decision. It preserves the durable contract where a repository index, queue, or later session needs it, while allowing the explicit invocation itself to authorize one bounded session-local change.

## Decision

**We will require persisted spec-and-plan contracts for workspace-indexed, queued, or resumable work, and permit only an explicit direct-light request to execute session-locally without creating or indexing a durable planning artifact.**

The explicit request is not workspace dispatch. It is authorized by the invocation itself, remains unavailable to argless dispatch and fresh-session resumption, and does not weaken the workspace reader's fail-closed behavior.

### ADR-0014 refinement

ADR-0014 states: "**Light mode (the default for low-risk work).** A lean spec written inline — Objective + Acceptance Criteria + a short task list." This is refined as follows: light mode retains the objective, acceptance checks, and bounded task list **in the session**; it persists no artifact.

ADR-0014's risk-trigger set, light/full selection, and boundary of no new executable code, skill, or artifact type stand. Its deferred mode-selection mechanism also stands as a deferral: ADR-0014 explicitly assigns the auto-classify-versus-explicit-user-flag choice to the implementation spec, which now fixes it as an explicit request to start.

### ADR-0076 refinement

ADR-0076 states: "agents may dispatch work only from structured workspace entries that reference those files." This remains true of **workspace dispatch**. An explicit direct-light request is not workspace dispatch and is authorized by the invocation itself.

### ADR-0078 refinement

ADR-0078 states: "**Start or do this:** classify normalized content, materialize the canonical artifact, register it, and invoke the processor that owns the next step." Its accepted tradeoff says that "every captured item must materialize a canonical artifact before it can become executable." These rules govern **captured and indexed** items. A direct-light request is never captured or indexed, so it is outside their scope rather than an exception to them.

ADR-0078 also records an unqualified consequence: "Every executable work item has a reviewable canonical contract and plan." Direct-light work is executable and deliberately has neither, so that consequence is refined too: it holds for every **workspace-indexed** work item. A session-local direct-light request is executable without being a work *item* in the index, and its reviewable substitute is the pre-write decision record plus the pull request, neither of which is a durable repository artifact.

ADR-0078's dispatchability rule is preserved unchanged: an entry is dispatchable only when it names an existing Approved spec and sibling plan. That rule already scopes itself to workspace entries, which direct-light never creates.

## Decision drivers

- Preserve fail-closed, deterministic workspace dispatch.
- Avoid durable artifacts and shared-index writes for a bounded current-session request.
- Keep existing persisted specs and workspace entries compatible.
- State the authority limitation honestly rather than inventing an unenforceable provenance mechanism.

## Consequences

**Positive:**

- Workspace-indexed, queued, and resumable work keeps an existing spec and sibling plan.
- Direct-light execution gains no hidden path into the workspace lifecycle.
- Existing persisted light specs stay readable and resumable.

**Negative:**

- Direct-light work cannot be resumed or dispatched after context loss; it must escalate when it needs durability.
- Eligibility remains a caller-declared semantic signal. The boundary is doctrine with eval coverage rather than a technical guarantee.

**Revisit if:** a runtime can distinguish trusted invocation provenance from undifferentiated prompt context.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** RFC-0092 and the implementing spec preserve the three refinements, leave accepted bodies unchanged, and retain workspace dispatch's existing-spec-and-plan requirement.
- **Owner:** maintainers

## Alternatives considered

**Keep the persisted inline lean spec for every light run.** Rejected because it gives session-local work durability it cannot use without workspace dispatch or resumption.

**Create a separate no-spec workflow.** Rejected because it would duplicate the existing workflow rather than narrow an existing mode branch.

**Make direct-light a workspace entry without files.** Rejected because it would contradict the preserved fail-closed workspace-dispatch boundary.

## References

- RFC-0092: direct-light execution without durable planning artifacts.
- ADR-0014: light/full modes and its deferred mode-selection mechanism.
- ADR-0076: workspace dispatch from structured entries referencing a spec and plan.
- ADR-0078: standalone intake and workspace-entry dispatchability.
- ADR-0088: the risk-trigger block's single documented home; unchanged by this decision.
- RFC-0090: change sizing; unchanged by this decision.

