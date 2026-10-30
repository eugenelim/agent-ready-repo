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
| `docs/rfc/0106-stop-registering-derivable-work.md` § Errata, last sentence (AC-0027) | "The tracker-origin spec entries, and their writers, stay until slice 9." (re-approved: one word added for the `tracker-origin` literal) | eugenelim (owner), 2026-10-29T15:24-05:00 |
| `docs/specs/workspace-retirement/spec.md` AC-0021 (controlled amendment of that Implementing spec) | "…is a `contract` row, unless the file no longer mentions `workspace.toml`, `workspace-status` or `workspace_status`." | eugenelim (owner), 2026-10-29T17:24-05:00 |

## The repair on this repository (AC-0036, AC-0037, AC-0038)

Run 2026-10-29 on this branch after every writer task (T2, T3, T4, T6, T7, T8) had landed.

```
python packs/core/.apm/skills/workspace-status/scripts/workspace_status.py repair-plan --root . --plan-file .context/repair/plan.json
python packs/core/.apm/skills/workspace-status/scripts/workspace_status.py repair-apply --root . --plan-file .context/repair/plan.json --yes
```

Plan: `plan_id` `8e62a2e96129b382264224494d68bdf9070cfa081aebb1fefbc1dfcb64c2bc95`, file SHA-256 `6826caa6b83cb18b3bc2f5cc282fe6854d8bb2506ceeccbe37fdc3bcc7816c3b`, registry fingerprint `777a6c01f31f322884bede5d743da02f222b15ca2b228601f63da7a903f07fb0`. The owner was shown the plan file path, its SHA-256 and its operation counts, and approved the apply before it ran (2026-10-29, eugenelim).

| Planned | Count |
| --- | ---: |
| `needs-to-header` operations | 0 |
| `needs-drop-cooled` operations | 0 |
| held entries | 0 |
| needs manual items | 0 |
| `type1-untracked` items | 0 |
| `spec-entry-drop` operations | 243 (214 `work.shipped`, 20 `backlog.open`, 5 `work.queue`, 4 `work.active`) |

Apply: exit `0`, `applied: true`, `operations_applied: 243`; 243 entries removed; `workspace.toml` SHA-256 `777a6c01f31f322884bede5d743da02f222b15ca2b228601f63da7a903f07fb0` before, `f9ebb555f640a756e487d9e6112af626f9ce85f9580d16b89764c9c9c820ec09` after. A following `repair-plan` held no operation and no manual item, and `tools/compare-registry.py --root .` still passed. The rebase onto `7933d2fcb635ab3373281756bf2e878fbd6747c9` then brought in two more repo-origin spec entries, which the second run below removed.

| Stdout of | SHA-256 before the apply | SHA-256 after the apply |
| --- | --- | --- |
| `dispatch.py --root .` | `96d8f586fcb5315e3187f56734d8832eb35397b7119541c25f47a69c6c9f3a7f` | `96d8f586fcb5315e3187f56734d8832eb35397b7119541c25f47a69c6c9f3a7f` |
| `dispatch.py --root . --resume docs/specs/spec-registration-stop/spec.md` | `06d395d484a0e49c3c7a2c8360adcb072dd42810af27ce90ed05b74f633c622d` | `06d395d484a0e49c3c7a2c8360adcb072dd42810af27ce90ed05b74f633c622d` |

Both pairs are equal, and the plan held no needs operation and no held entry.

### Second run, after the rebase onto `7933d2fcb`

Run 2026-10-29 on this branch at commit `3f436fab9c57c32cb7ecc069ea90d81531d2d2ea`. The rebase had added two repo-origin spec entries to `workspace.toml`, both in `["ini-002".work].shipped` with `needs = []`.

```
python3 packs/core/.apm/skills/workspace-status/scripts/workspace_status.py repair-plan --root . --plan-file .context/repair/plan-r2.json
python3 packs/core/.apm/skills/workspace-status/scripts/workspace_status.py repair-apply --root . --plan-file .context/repair/plan-r2.json --yes
```

Plan: `plan_id` `e242f4e04336d84dbfc6ac3b20c04d772ab74054a9ef82458a95729446f644ac`, file SHA-256 `fe6a0f93ac7c620a771ef49f52fc46f46e94a6a0c01327100a4c71759298c243`, workspace fingerprint `197dc322ca9c4c081dd45be81f1077c8bc6ffa5d93f391e27377e9d318da17cd`. The owner was shown the plan file path, its SHA-256, its 2 operations and its 0 manual items, and approved the apply before it ran (2026-10-29, eugenelim).

| Planned | Count |
| --- | ---: |
| `needs-to-header` operations | 0 |
| `needs-drop-cooled` operations | 0 |
| held entries | 0 |
| needs manual items | 0 |
| `type1-untracked` items | 0 |
| `spec-entry-drop` operations | 2 (2 `work.shipped`: `docs/specs/grounding-preservation-authoring-reproducibility/spec.md`, `docs/specs/grounding-preservation-review/spec.md`) |

Apply: exit `0`, `applied: true`, `operations_applied: 2`; `workspace.toml` SHA-256 `197dc322ca9c4c081dd45be81f1077c8bc6ffa5d93f391e27377e9d318da17cd` before, `1213450dbc24a77a77b524033e6c92b80c9cfcc29be9fd5da238e739c6a45603` after. A following `repair-plan` (`.context/repair/plan-r3.json`, SHA-256 `1d26e9b02fc2bd902d447636f4cdfa5c84c839347bd617ded7af856ab40452b8`) holds 0 automatic operations and 0 manual findings. No repo-origin spec table is left in `workspace.toml`; the only `kind = "spec"` text is the template comment on line 11. `tools/compare-registry.py --root .` passes.

The digests below were taken in the same shell command as the apply, immediately before and immediately after it.

| Stdout of | SHA-256 before the apply | SHA-256 after the apply |
| --- | --- | --- |
| `dispatch.py --root .` | `96d8f586fcb5315e3187f56734d8832eb35397b7119541c25f47a69c6c9f3a7f` | `96d8f586fcb5315e3187f56734d8832eb35397b7119541c25f47a69c6c9f3a7f` |
| `dispatch.py --root . --resume docs/specs/spec-registration-stop/spec.md` | `06d395d484a0e49c3c7a2c8360adcb072dd42810af27ce90ed05b74f633c622d` | `06d395d484a0e49c3c7a2c8360adcb072dd42810af27ce90ed05b74f633c622d` |

Both pairs are equal, and the plan held no needs operation and no held entry.
