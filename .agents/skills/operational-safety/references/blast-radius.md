# blast-radius — destroy/replace gating, prevent-destroy, proposer≠approver

> **Loaded when:** the change can delete or replace existing infrastructure,
> alters a resource whose replacement is destructive (a recreated database, a
> renamed stateful resource), or runs a destroy/teardown path against a shared
> or production environment.
> **Grounded in:** F3.1 (parse the plan structurally; gate on destroy/replace
> counts), F3.2 (decouple proposer identity from approver identity).
> Operational taxonomy: the destructive-op-needs-human-approval rule already in
> AGENTS.md "Check before acting".
> **Delegation legend:** `tool` = scanner / CI-gate-owned · `hybrid` = gate
> surfaces the signal, you judge the fix · `reason` = reviewer-only judgment.

The cost of a wrong line here is the highest in the loop — a single misjudged
replace can drop a production datastore. Gate on **what the plan will actually
destroy**, not on a hopeful read of the diff.

## Implementation checks

- `tool` **Parse the plan structurally; gate on destroy/replace counts.**
  Compute the planned `delete` / `replace` actions from the machine-readable
  plan (the structured plan output, not grepped text), and fail the step on a
  nonzero destructive count unless an explicit override is present. Confirm this
  parse-and-gate runs before any apply.
- `reason` **Destructive count never read from text.** Grepping apply logs or
  the human-readable diff for "destroy" is unreliable; the gate must read the
  structured plan. Flag any gate that pattern-matches prose.
- `reason` **Proposer ≠ approver for irreversible ops.** The identity that
  proposes a destructive change must not be the identity that approves it — the
  agent proposes, a *different* identity (the human) approves. This maps onto
  "get user confirmation for destructive commands" in AGENTS.md; flag a path
  where the agent could self-approve a destroy/replace.
- `reason` **Must-survive resources are pinned.** Resources that must not be
  destroyed carry an explicit prevent-destroy guard — and the reviewer notes
  that such guards are bypassable (removing the block, surgical state edits), so
  a change that *removes* a prevent-destroy guard is itself a destructive-intent
  signal worth surfacing.

## Established-pattern bypass

Resolve the repo's sanctioned destructive-op gate — the plan-parse check in CI,
the required-reviewer environment, the change-approval workflow — and flag a
change that routes a destroy around it (a direct teardown command, a
`--auto-approve` on a destructive apply). The blessed gate is where
proposer≠approver was already enforced.

*Illustrative only (never normative):* `plan -out` → structured-plan parse →
count `delete`/`replace`, or a required-reviewer rule on a protected
environment, exhibit this shape — but the check is the *property*
(parsed-plan gating + identity separation), not any one tool.
