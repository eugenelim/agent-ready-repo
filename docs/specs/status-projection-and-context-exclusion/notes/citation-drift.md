# Citation drift recorded after the EXECUTE-boundary rebase

`plan.md` is hash-pinned by `loop-cohort approve-plan` (plan_hash `0c70a6bc944a`).
Any edit to it beyond a status flip or a checkbox check-off strands every
`CODE-*` transition except `done`. These corrections are therefore recorded here
rather than in the plan. **The plan's prose names each anchor by symbol, so the
line drift is cosmetic — implement against the symbol, not the number.**

Rebased from `9d9b5904c` onto `origin/main` at 47 commits, 2026-08-30. Only one
cited file moved: `tests/roster/test_workspace_status_projection.py`
(commit `fb0be768f`, "register both slice-2 specs and correct the INI-009
milestone").

| Plan citation | Says | Actually | Effect |
| --- | --- | --- | --- |
| Repository anchors — finding-code documentation gate | `tests/roster/test_workspace_status_projection.py:486-495` | `:488-497`; `finding_codes = set(engine._FINDING_NEXT_ACTIONS)` is at `:488` | none — AC46 cites no line number, only the two owning files and the reason/next-action requirement |
| Design → four selection points → dependency probe | "the `structurally_blocked_paths` refusal (`:2358`)" | `:2359`; `:2358` is the closing `) -> tuple[bool, RoutingFinding | None]:` of the signature | none — the plan names the symbol, and the rule is "place the short-circuit *after* that guard" |

## Anchors re-verified as unmoved after the rebase

- `workspace_status_engine.py` is still 5239 lines.
- The Wave 4 guard is still `raise ValueError("Wave 4 cannot exclude cooling context")` at `:552-553`.
- `test_workspace_status_refuses_wave6_context_exclusion` is still at
  `packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py:469`.
- No commit in the range touched `packs/core/.apm/skills/workspace-status/scripts/`,
  `packs/core/.apm/skills/close-work/scripts/`,
  `packages/agentbundle/agentbundle/workspace_mcp.py`,
  `packages/agentbundle/agentbundle/build/self_host.py`,
  `tools/test_workspace_status_cli.py`, or
  `packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py`.

## Standing rule for the rest of this delivery

Re-run this check at every phase boundary. A line citation in `plan.md` is
evidence of what was true at sealing time, not a live coordinate; resolve every
anchor by symbol before editing.
