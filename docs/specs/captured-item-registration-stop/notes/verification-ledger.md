# Verification ledger: captured items stop being registered

## T1: the registry comparison before the stop

Run on 2026-10-27 on this spec's branch, before any writer instruction changed, as FEAT-0034's validation hook requires.

- **Command:** `python3 tools/compare-registry.py --root .`
- **Commit:** `d3f984349ca1910843622fd6fde99c56f8f2f47c`
- **Merge base with `origin/main`:** `dd4f7038cd60c649621d736358af7b1e87cd1961`
- **Exit code:** `0`, so no row is failing and captured-item registration may stop.

Full default output:

```text
registry comparison: pass
captured_item 0
legacy_shape 0
registry_stale 0
registry_closed_stale 0
registry_omission 48
registry_live_only 0
result_terminal 0
unclassified 0
commit d3f984349ca1910843622fd6fde99c56f8f2f47c
workspace.toml sha256 b16a4b52934a492a2b05caf191b942890f82d375815539aa4d758c3790a428a4
```

The 48 `registry_omission` rows are outstanding items that no registry entry names. That class is allowed and never failing.

## T2: the grammar and the closed state

Implemented in `f7d99bd90` (red), `d5617b253` (engine), `f8e7a36ce` (core 3.1.25), and `e4c002566` (packaged and projected copies). The three frozen fixtures are byte-identical to `dd4f7038c`.

AC-0005's pins were recorded once from the engine at `dd4f7038c`:

- A missing captured-item path with no receipt gives `missing_dependency` on the path.
- A missing path with a completion receipt gives `invalid_dependency` on the waiter and `missing_dependency` on the path, because the header reader refuses a completion receipt on a captured-item reference. No receipt settles a captured-item dependency at either commit.
- A cooled unregistered file gives `invalid_dependency` on the waiter, because its kind is never read.

`test_workspace_status_engine_autonomous.py::test_t2_positive_dispatch_and_reconciliation_surface` plants a registered `Closed` design record. It gains `Resolution: fixed`, as the equivalence cases do, and keeps `impossible_transition`.

## T5: the errata entries

The owner, eugenelim, approved the wording of all four entries on 2026-10-27 before they were committed: ADR-0053 § Errata, RFC-0063 § Errata, RFC-0083 § Errata, and RFC-0106 § Errata. Each is committed exactly as approved. `lint-adr-shape.py docs/adr` and both record-index checks pass.

## T7: closeout

AC-0019 live comparison, run at head `80cef728d` over this worktree's tree. A scratch script under `.context/` ran the engine from a detached `dd4f7038c` checkout and the head engine, each as `python3 -I <engine>/packs/core/.apm/skills/workspace-status/scripts/workspace_status.py status --root <head tree root>`, and compared the AC-0019 fields.

| Field | `dd4f7038c` | head | Result |
| --- | --- | --- | --- |
| `canonical.ready` paths | 0 | 0 | identical |
| `canonical.active` paths | 3 | 3 | identical |
| `canonical.blocked` paths | 28 | 28 | identical |
| `canonical.findings` by (code, path) | 65 | 65 | identical |
| `captured` object (77 items) | 77 | 77 | identical |

Result: identical on every compared field.

## Code review and the final comparison

Code review ran in two rounds over `origin/main...HEAD`, with records under `.context/reviews/captured-item-registration-stop-code-r1/` and `-r2/`.

- **Round 1:** the adversarial, security, and quality reviewers reported 1, 0, and 1 blockers, 4, 0, and 3 concerns, and 4, 1, and 3 nits. The adjudicator sustained 2 concerns and 6 nits and refuted the rest, including both blockers. The quality blocker was refuted because the one-step `Resolution:` rule is the owner's settled decision. The adversarial blocker was refuted because shipping the spec is a finish step.
- **Repairs:** the controller applied the sustained fixes itself, as `work-loop`'s FIX step allows for a short fix. The task's dispatch record carries `human-directed` because the receipt schema has no controller-applied reason.
  - `c93323151`: an unregistered captured-item dependency that becomes cooled between the two cooled checks fails closed, with a test that failed on the earlier engine.
  - `026282e34`: the guide and skill wording.
  - `3ec135ced`: the regenerated copies.
- **Round 2:** the adversarial review was clean. The security review was clean with a `## Not checked` footer, which the adjudicator found holds no finding.

AC-0019 was re-run at head `2dc1e1b5db0cd0737caa5f450056cd6e78d46071`, after the spec shipped. `workspace_status.py status --root .` ran from a detached worktree of `dd4f7038c` and from the head, each with `python3 -I`, over the head's tree. The results are identical: ready 0, active 2, blocked 28, canonical findings 65 by code and path, and 77 captured items. This ledger section is the only later change, and the engine reads no file under `notes/`.
