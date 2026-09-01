# Manual QA — the real CLI, 2026-09-01

Run against `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`
at core 2.21.0, over fixtures built in a scratch directory outside the repository
tree. A passing unit gate is not evidence that a maintainer sees the right thing,
so this is the observed output of the real invocation.

## Observed

| Scenario | Invocation | exit | `all_specs_shipped` | `queue_empty` | `next_action` | blockers |
| --- | --- | --- | --- | --- | --- | --- |
| fully cooled, clean record | `status` | 0 | `True` | `True` | `invoke-close-work` | `[]` |
| fully cooled, clean record | `reconcile` | 0 | `True` | `True` | `invoke-close-work` | `[]` |
| fully cooled + unreadable record | `status` | 0 | `True` | `True` | `settle-closeout-blockers` | `['cooling-context-incomplete']` |
| fully cooled + unreadable record | `reconcile` | 0 | `True` | `True` | `settle-closeout-blockers` | `['cooling-context-incomplete']` |
| uncooled control | `status` | 0 | `False` | `False` | `settle-closeout-blockers` | `['unshipped-specs']` |
| uncooled control | `reconcile` | 0 | `False` | `False` | `settle-closeout-blockers` | `['unshipped-specs']` |
| fully cooled, clean record | `repair-plan` | 0 | — | — | — | no `closeout` or `cooling` key emitted |

## What that shows

The Objective's two promises hold at the surface a maintainer actually invokes.
A fully cooled initiative reaches `invoke-close-work` instead of reporting
`unshipped-specs` forever. Add one record that cannot be read and the same
initiative still reports both consumers as excluded — but the affirmative is
withheld and named, rather than offered on a partial reading.

The two consumers agree in every row: `True`/`True`, `True`/`True`,
`False`/`False`. That is the disagreement Wave 6 reverted, gone at the observable
level and not only in a unit test.

`status` and `reconcile` are identical throughout, which matters because they use
different analysis entry points and `closeout`'s blockers come from the
reconciliation result.

## Stop point, and what is documented but not exercised here

This session exercised the closeout projection only. Not exercised by hand:

- The six repair and migration control pairs (AC17-AC22). They are covered by
  tests that assert success and a real effect in both runs before comparing —
  `returncode == 0`, a non-empty operation list, `workspace.toml` actually
  changed, `result_codes == ["applied", "applied"]` — and the migration verbs
  need self-generated confirmation files that are impractical to drive by hand.
- The MCP status tool. It shares the engine but not this CLI's builders; no
  criterion in this contract reaches it.
- An adopter tree. Every fixture here is synthetic; the repository's own
  `workspace.toml` carries no lifecycle record, so the cooled path cannot be
  observed against real repository state until one is written.
