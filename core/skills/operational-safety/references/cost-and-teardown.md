# cost-and-teardown — cost-ceiling-as-gate, destroy-on-fail, TTL, no orphans

> **Loaded when:** the change provisions billable resources, creates ephemeral
> or per-iteration infrastructure, or runs a teardown path — anything that can
> leave a paid-for resource running after the work is done.
> **Grounded in:** F3.4 (cost is a first-class CI gate, not a post-deploy
> surprise), F3.5 (tag-at-creation TTL + destroy-on-close prevents orphans;
> destroy needs its own plan). Operational taxonomy: AWS Well-Architected Cost
> Optimization; the ephemeral-environment lifecycle pattern.
> **Delegation legend:** `tool` = scanner / CI-gate-owned · `hybrid` = gate
> surfaces the signal, you judge the fix · `reason` = reviewer-only judgment.

An agentic loop that provisions on each iteration leaks money invisibly: the
failure mode is not a crash but a bill. Estimate cost **from the plan, before
apply**, and make teardown as deliberate as creation.

## Implementation checks

- `tool` **Cost is estimated from the plan and gated on a ceiling.** A
  cost-diff runs on the planned change and a budget ceiling (absolute, percent,
  or budget) blocks the apply when exceeded. Confirm the cost gate is wired; if
  none is detected, flag `degraded: no cost gate` rather than passing silently.
- `reason` **Destroy-on-fail / no half-built stacks.** A failed apply or smoke
  must tear down what it created rather than leaving a partial stack accruing
  cost. Flag a path where a failed run exits leaving resources up with no
  cleanup.
- `reason` **TTL / tag-at-creation for ephemeral resources.** Resources created
  for iteration carry a TTL or ownership tag a scheduled cleanup can find, so an
  abandoned run is reclaimable. Untagged, unbounded-lifetime ephemeral resources
  are the orphan source.
- `reason` **Destroy has its own plan.** A teardown is a destructive operation
  in its own right — preview the destroy plan before running it (it inherits the
  `blast-radius` gating), don't fire an unreviewed bulk destroy.
- `hybrid` **No orphans after a normal run.** After a successful iterate-and-
  teardown cycle, no created resource is left behind. Confirm the teardown
  enumerates everything the apply created.

## Established-pattern bypass

Resolve the repo's sanctioned lifecycle harness — the cost-diff CI gate, the
ephemeral-environment create/destroy automation, the TTL-tag-and-sweep
convention — and flag a change that provisions billable resources outside it
(no cost gate, no teardown, no TTL tag).

*Illustrative only (never normative):* a cost-diff status check on PRs plus a
TTL tag swept by a scheduled cleanup, or create-on-open / destroy-on-close
per-PR environments, exhibit this shape — but the check is the *property*
(cost-as-gate + bounded lifecycle + no orphans), not any one tool.
