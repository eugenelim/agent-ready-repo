# Verification ledger: specs stop being registered

## Registry comparison before the stop (AC-0035)

Run 2026-10-29 on this branch at commit `62ed2dddfbb369d2d5b086facac4b1f0513b6ee6`, whose merge base with `origin/main` is `c8d1d817a536e72b19a0f5733752c50ac1e3d77b`, before any writer instruction, router branch, repair step, or registry entry changed:

```
python3 tools/compare-registry.py --root .
```

Exit code: `0`.

```
registry comparison: pass
captured_item 0
legacy_shape 0
registry_stale 0
registry_closed_stale 0
registry_omission 164
registry_live_only 0
result_terminal 0
unclassified 0
commit 62ed2dddfbb369d2d5b086facac4b1f0513b6ee6
workspace.toml sha256 cd2bb92c4a952ee5acbddfc9f05fbaae79179ad474529238144732cc32644ddc
```

## Live replay before the stop (AC-0035)

Run 2026-10-29 with this branch's `tools/replay-dispatch.py` and `packs/core/.apm/skills/work-loop/scripts/dispatch.py` at git blob `e2e4942c6a3dc3a0abb434ccad8762bfe706979f` (unchanged on this branch), over a `git worktree` of the merge base `c8d1d817a536e72b19a0f5733752c50ac1e3d77b`, before any writer instruction, router branch, repair step, or registry entry changed:

```
python3 tools/replay-dispatch.py --root <worktree> --base-engine <worktree>/packs/core/.apm/skills/workspace-status/scripts/workspace_status.py
```

Exit code: `0`.

```
base canonical.ready 0 []
base canonical.active 2 ["docs/specs/execution-supervisor-cutover/spec.md", "docs/specs/workspace-retirement/spec.md"]
dispatch ready 0 []
dispatch active 3 ["docs/specs/execution-supervisor-cutover/spec.md", "docs/specs/plan-evolution-experiments/spec.md", "docs/specs/workspace-retirement/spec.md"]
workspace.toml sha256 cd2bb92c4a952ee5acbddfc9f05fbaae79179ad474529238144732cc32644ddc
lifecycle records 0
differing specs 2
DIFF * argless_start base={"action": "ask", "path": null, "candidates": ["docs/specs/execution-supervisor-cutover/spec.md", "docs/specs/workspace-retirement/spec.md"]} dispatch={"action": "ask", "path": null, "candidates": ["docs/specs/execution-supervisor-cutover/spec.md", "docs/specs/plan-evolution-experiments/spec.md", "docs/specs/workspace-retirement/spec.md"]}
DIFF * argless_resume base={"action": "ask", "path": null, "candidates": ["docs/specs/execution-supervisor-cutover/spec.md", "docs/specs/workspace-retirement/spec.md"]} dispatch={"action": "ask", "path": null, "candidates": ["docs/specs/execution-supervisor-cutover/spec.md", "docs/specs/plan-evolution-experiments/spec.md", "docs/specs/workspace-retirement/spec.md"]}
DIFF docs/specs/experience-pack-0.6.0/spec.md start base={"action": "refuse", "path": null, "candidates": []} dispatch={"action": "invalid_selector", "path": null, "candidates": []}
DIFF docs/specs/experience-pack-0.6.0/spec.md resume base={"action": "refuse", "path": null, "candidates": []} dispatch={"action": "invalid_selector", "path": null, "candidates": []}
DIFF docs/specs/plan-evolution-experiments/spec.md active base=false dispatch=true
DIFF docs/specs/plan-evolution-experiments/spec.md resume base={"action": "refuse", "path": null, "candidates": []} dispatch={"action": "resume", "path": "docs/specs/plan-evolution-experiments/spec.md", "candidates": []}
```

### Classification

Every difference falls under a case that the [`header-derived-dispatch`](../../header-derived-dispatch/notes/verification-ledger.md) ledger classified, with the owner's 2026-10-29 approval recorded there; no difference is unclassified.

| Spec path | Field | Base | Dispatch | Case | Class |
| --- | --- | --- | --- | --- | --- |
| `*` | `argless_start` | `ask` over 2 candidates | `ask` over 3 candidates | `unregistered-implementing` | accepted removal (RFC-0106 D1) |
| `*` | `argless_resume` | `ask` over 2 candidates | `ask` over 3 candidates | `unregistered-implementing` | accepted removal (RFC-0106 D1) |
| `docs/specs/experience-pack-0.6.0/spec.md` | `start` | `refuse` | `invalid_selector` | `dotted-slug-selector` | accepted removal (RFC-0106 § Errata, 2026-10-29, item 10) |
| `docs/specs/experience-pack-0.6.0/spec.md` | `resume` | `refuse` | `invalid_selector` | `dotted-slug-selector` | accepted removal (RFC-0106 § Errata, 2026-10-29, item 10) |
| `docs/specs/plan-evolution-experiments/spec.md` | `active` | `false` | `true` | `unregistered-implementing` | accepted removal (RFC-0106 D1) |
| `docs/specs/plan-evolution-experiments/spec.md` | `resume` | `refuse` | `resume` | `unregistered-implementing` | accepted removal (RFC-0106 D1) |

## Owner approvals of wording (AC-0031)

| Target | Wording | Approval |
| --- | --- | --- |
| `cooled_child_scope_unknown` next action (AC-0005): `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, its packaged copy, `packs/core/.apm/skills/navigate-intents/scripts/intent_readiness.py`, `packs/core/.apm/skills/workspace-status/SKILL.md`, `guides/core/reference/workspace-toml-schema.md` | "Set parent on the spec's lifecycle record: a resolving brief path, or none only when that spec has no parent brief; a tracker-origin entry declares source.parent instead." | eugenelim (owner), 2026-10-29T14:31-05:00 |
| `docs/rfc/0064-ini-001-ai-native-ecosystem.md` § Errata, Current state row 13 and History (AC-0027) | the 2026-10-29 "Spec writer rows stop registering repo-origin specs" entry, as shown to the owner | eugenelim (owner), 2026-10-29T15:19-05:00 |
| `docs/rfc/0106-stop-registering-derivable-work.md` § Errata (AC-0027) | the 2026-10-29 spec registration stop entry: the spec entry removal, the readiness bridge's first-ready mark, tracker-origin | eugenelim (owner), 2026-10-29T15:19-05:00 |
| `docs/adr/0110-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md` § Errata (AC-0027) | the 2026-10-29 "Revisit if (1) met" entry | eugenelim (owner), 2026-10-29T15:19-05:00 |
| `docs/adr/0076-briefs-persist-dispatch-starts-from-specs.md` new § Errata (AC-0027) | the 2026-10-29 "D3, D4, D6 and D7 read through a spec's own headers" entry | eugenelim (owner), 2026-10-29T15:19-05:00 |
| `docs/product/intents/FEAT-0005-lifecycle-and-closure.md` amendment (AC-0028) | "no terminal registration move for a repo-origin spec" | eugenelim (owner), 2026-10-29T15:19-05:00 |
| `docs/product/intents/FEAT-0007-work-item-promotion-routing.md` amendment (AC-0028) | "the start and remember routes register no repo-origin spec" | eugenelim (owner), 2026-10-29T15:19-05:00 |
| `docs/product/AGENTS.md` § Status has one home (AC-0029) | "A spec's own `Brief:` header is the confirmation evidence…" | eugenelim (owner), 2026-10-29T15:19-05:00 |
| `docs/product/briefs/agent-skill-engineering.md` (AC-0030) | the three registration phrases rewritten as shown | eugenelim (owner), 2026-10-29T15:19-05:00 |
| `docs/product/briefs/workspace-registry-retirement-delivery.md` Non-goals (AC-0045) | "…adds, removes or rewords a finding code…" | eugenelim (owner), 2026-10-29T15:19-05:00 |
