# Live publish-control state — read 2026-08-17

Read-only API reads against `eugenelim/agent-ready-repo`. Recorded because
`tools/lint-claude-plugin-publish-control.py` compares the desired-state file
against hardcoded literals and a hand-committed capture whose `observed_at` need
only be a non-empty string — no gate in this repository reads GitHub.

## Result: the desired state matches live state, and the chain closes

| Desired (`.github/claude-plugin-publish-control.json`) | Live | Match |
| --- | --- | --- |
| `branch.target: refs/heads/claude-plugins-dist` | ruleset 20750027 `conditions.ref_name.include: ["refs/heads/claude-plugins-dist"]`, `exclude: []` | yes |
| `restrict_updates: true` | rule `update` present | yes |
| `restrict_deletions: true` | rule `deletion` present | yes |
| `block_force_pushes: true` | rule `non_fast_forward` present | yes |
| `bypass.actor_type: Integration`, `mode: always` | sole `bypass_actors` entry: `{actor_id: 4570570, actor_type: Integration, bypass_mode: always}` | yes |
| `bypass.actor_binding: environment_app_id` | env-scoped variable `CLAUDE_PLUGIN_PUBLISHER_APP_ID = 4570570` — **equals the bypass actor_id** | yes |
| `environment.name: claude-plugin-publish` | exists | yes |
| `environment.deployment_branches: ["main"]` | one custom branch policy, `main` | yes |
| `environment.required_reviewers: 1` | one `required_reviewers` rule, reviewer `eugenelim` | yes |
| `environment.private_key_secret` | env secret `CLAUDE_PLUGIN_PUBLISHER_PRIVATE_KEY` present | yes |

Ruleset `enforcement: active`, created 2026-08-12, updated 2026-08-12.

The binding that matters: the *only* actor able to bypass the ruleset is the App
whose ID lives in a variable scoped to the `claude-plugin-publish` environment,
and that environment gates on `main` with a required reviewer. So ADR-0072's
"branch protection is a precondition of this decision" holds in live state as of
this read.

## Two residuals — both maintainer decisions, neither blocking this spec

1. **`live_branch_negative_tested: false`.** Nobody has proven an ordinary actor
   is actually *rejected* by the live ruleset. The canary branch
   (`claude-plugins-dist-control-canary`) that carried the 2026-08-12 control test
   returns 404 — it was consumed and deleted, so the canary evidence cannot be
   re-derived without recreating it. A control asserted only by its configuration,
   never by an attempted violation, is a configuration claim rather than a
   demonstrated control.
2. **`prevent_self_review: false` with a single reviewer who is the repository
   owner.** This matches the recorded desired state, so it is a deliberate choice,
   not drift — but it means the environment gate is a speed bump rather than a
   separation of duties. Worth re-confirming as intent rather than inheritance.

## What this does and does not change for this spec

It does not change the design. The parity gate closes the gap between the
desired-state file and what the build advertises — which was the actual defect.
It cannot detect a settings-side removal, and this read is a point-in-time
observation, not a gate. That residual stays registered as
`publish-control-evidence-freshness-unbounded`; this file is the dated evidence
the slug's `Unblocks when:` should reference.
