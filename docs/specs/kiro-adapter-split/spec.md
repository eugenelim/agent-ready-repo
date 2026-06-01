# Spec: kiro-adapter-split

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0022](../../rfc/0022-kiro-adapter-split.md) — sole driving RFC; accepted 2026-06-01
  - [RFC-0005](../../rfc/0005-user-scope-hook-support.md) — errata E1-E3 appended by this work (T9)
  - [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md) — adapter spec + build pipeline
  - [ADR-0012](../../adr/0012-kiro-adapter-split.md) — records the six split decisions

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Split the single `kiro` adapter into two canonical adapters:

- **`kiro-ide`** — targets the Kiro VS Code-fork IDE. Projects `.md` agents (body-as-prompt via `J6`/gray-matter), activates the `kiro-ide-hook` primitive (event hooks via `.kiro.hook` files), and emits **no CLI-only fields** (`hooks`, `allowedTools`, `toolsSettings`, `mcpServers`) — any one of which causes the IDE loader to silently drop the agent.
- **`kiro-cli`** — targets the `kiro` terminal binary. Projects `.json` agents with CLI short-name tool tokens and lifecycle hooks via `hook-wiring` (`merge-into-agent-json`).

`kiro` is retained as a **deprecated alias** for `kiro-ide` with no removal timeline, so existing packs and adopter scripts keep working.

The contract bumps from v0.8 to v0.9. Errata E1–E3 are appended to RFC-0005 (T9). The `kiro-ide-hook` primitive shipped in PR #99 but was never declared in the contract; this spec activates it. Corrections to `distribution-adapters` and `agent-spec-cli` specs reconcile governance drift.

## Boundaries

**Always do:**
- Retain `kiro` as a working alias — emit a build-time deprecation warning, never a hard failure.
- Gate T1 (contract bump + `kiro-ide-hook` activation) on the Q6 probe completing *and* T9 (RFC-0005 errata) landing in the same PR.
- Gate T2 (validate rail update) on T9 landing — T9 is a hard prerequisite.
- Co-land T2 and T9 in the implementing PR (vocabulary update + errata together).
- Record RFC-0005 errata as Approver-signed (eugenelim, date of merge).
- Keep `kiro-ide-hook` at repo scope only; user-scope lift tracks kirodotdev/Kiro#5440.

**Ask first:**
- Any removal timeline for the `kiro` alias — RFC-0022 explicitly sets none.
- Changing the model id values (`claude-opus-4.6` / `claude-sonnet-4.5` / `claude-haiku-4.5`) — manually maintained, assumed stable.
- Landing T1 before Q6 probe outcome is recorded in `probes.md`.
- Adding user-scope `kiro-ide-hook` — blocked on kirodotdev/Kiro#5440.

**Never do:**
- Emit `hooks`, `allowedTools`, `toolsSettings`, or `mcpServers` keys in `kiro-ide` agent output.
- Hard-remove the `kiro` adapter block or break packs declaring `allowed-adapters = ["kiro"]`.
- Change skill, steering, or MCP projection (identical across IDE and CLI — no change needed).
- Add `kiro-ide` or `kiro-cli` to `SELF_HOST_ADAPTERS` (consistent with existing `kiro` exclusion).
- Merge T1 before Q6 probe outcome is recorded in `probes.md`.

## Testing Strategy

| Criterion | Mode | Verification |
|---|---|---|
| Contract v0.9 | goal-based | `test_contract.py` asserts `version == "0.9"` |
| `kiro-ide` `.md` projection, no CLI-only keys | TDD | `test_adapter_kiro_ide.py` — assert no `hooks`/`allowedTools`/`toolsSettings`/`mcpServers` in output |
| `kiro-ide-agent-frontmatter-v0.9` table rename (T1) | TDD | `test_frontmatter_table_renamed` — assert new key exists, old `kiro-agent-frontmatter-v0.9` does not |
| `kiro-cli` `.json` projection, CLI short-name tools | TDD | `test_adapter_kiro_cli.py` — assert `read`, `grep`, `shell`, etc. in tools array |
| `kiro` alias resolves to `kiro_ide.project` | TDD | `test_adapter_kiro.py` — registry lookup |
| Deprecation warning emitted on alias resolution | TDD | warn-log capture in alias test |
| `kiro-ide-hook` activated in contract (repo scope) | goal-based | `adapter.toml` parse round-trip + validate passes |
| validate rail rejects old vocabulary (`fileSave`, `fileEdit`, `manualTrigger`) | TDD | `test_kiro_ide_hook.py` rail — assert validation error on old terms |
| validate rail accepts E3 vocabulary | TDD | `test_kiro_ide_hook.py` rail — assert pass on verified terms |
| `cli.py` help text names all five adapters | goal-based | `--help` output contains `kiro-ide`, `kiro-cli`, `kiro` |
| `distribution-adapters/spec.md` footnote corrected (T5) | goal-based | `grep "kiro-ide projects"` returns match; `grep "confirming agents are JSON"` returns no match |
| `agent-spec-cli/spec.md` §v0.4 clarified (T6) | goal-based | `grep "contract activation deferred to RFC-0022"` returns match |
| RFC-0005 errata appended (T9) | goal-based | `grep "## Errata"` in `0005-user-scope-hook-support.md` + E1, E2, E3 all present |
| `probes.md` Q11 records RFC-0022 closure (T10) | goal-based | `grep "RFC-0022"` in `probes.md` Q11 Outcome + `grep "sessionStart"` returns match |
| Contract drift gate passes | goal-based | `make build-check` green |

## Acceptance Criteria

### Prerequisite doc changes (T9, T10)

- [ ] RFC-0005 `## Errata` table appended with E1, E2, E3, Approver-signed (eugenelim, date of merge) (T9)
- [ ] `docs/specs/kiro-ide-hook/probes.md` Q11 Outcome updated: RFC-0022 closes Q11 via static analysis of `extension.js` `IDEListenableEvent` enum; no IDE-UI-authored fixture required; E3 vocabulary recorded (T10)

### Contract and `kiro-ide` adapter (T1) — depends on Q6 probe + T9

- [ ] `[contract] version` is `"0.9"` in `adapter.toml` (T1)
- [ ] `[adapter.kiro-ide]` block declared with `.md` projection, repo-scope `kiro-ide-hook` activation, no CLI-only fields (T1)
- [ ] `kiro-ide-agent-frontmatter-v0.9` mapping table (renamed from `kiro-agent-frontmatter-v0.9`); all call sites in `kiro.py` updated to the new name (T1)
- [ ] `ide-event-vocabulary` in `kiro-ide` block matches E3 list: `fileEdited`, `fileCreated`, `fileDeleted`, `userTriggered`, `promptSubmit`, `agentStop`, `preToolUse`, `postToolUse`, `preTaskExecution`, `postTaskExecution`, `sessionStart` (T1)
- [ ] `ide-action-vocabulary` in `kiro-ide` block: `["askAgent", "runCommand"]` (T1)
- [ ] Q6 probe outcome recorded in `probes.md` before T1 merges (T1 gate)

### Validate rail (T2) — depends on T9

- [ ] `kiro_ide_hook.py` validate rail updated to E3 vocabulary (T2)
- [ ] `scope_rails.py` `check_kiro_ide_hook` updated to E3 vocabulary (T2)

### `kiro-cli` adapter (T3)

- [ ] `[adapter.kiro-cli]` block declared with `.json` projection and `hook-wiring` retained (T3)
- [ ] `kiro-cli-agent-frontmatter-v1.0` mapping table with CLI short-name `tools.values`: `Read→read`, `Grep→grep`, `Glob→glob`, `Edit→write`, `Write→write`, `MultiEdit→write`, `Bash→shell`, `WebFetch→web_fetch`, `WebSearch→web_search` (T3)
- [ ] `kiro-ide-hook` is `mode = "dropped"` in `kiro-cli` block (T3)

### `kiro` deprecated alias (T4)

- [ ] `[adapter.kiro]` stub block retained in `adapter.toml` with deprecation comment (T4)
- [ ] Python adapter registry maps `"kiro"` → `kiro_ide.project` (T4)
- [ ] Deprecation warning logged on alias resolution: `"kiro: deprecated alias for kiro-ide; update allowed-adapters in pack.toml"` (T4)

### Spec corrections (T5, T6)

- [ ] `distribution-adapters/spec.md` footnote (lines 214–218) corrected: `kiro-ide` projects `.md`, `kiro-cli` projects `.json`, IDE accepts both (T5)
- [ ] `distribution-adapters/spec.md` primitive table agent row and hook-wiring row updated to reflect the split (T5)
- [ ] `agent-spec-cli/spec.md` §v0.4 carries clarification: "Code shipped in PR #99; contract activation deferred to RFC-0022" (T6)

### CLI help text (T7)

- [ ] `cli.py` adapter help-text string names all five adapters with deprecation note for `kiro` (T7)

### Test suite (T8) — depends on T1, T2, T3, T4

- [ ] `test_adapter_kiro.py` (or equivalent) updated: covers `kiro` alias + `kiro-ide` canonical projection, asserts no CLI-only keys in `kiro-ide` output (T8)
- [ ] `test_contract.py` asserts `"0.9"` (T8)
- [ ] `kiro_ide_hook` tests updated to E3 vocabulary (T8)
- [ ] Contract drift gate (`make build-check`) passes with all new adapter declarations (T8)

## Changelog

- 2026-06-01 — Spec created. Status: Implementing. Driving RFC: RFC-0022 (Accepted 2026-06-01).
