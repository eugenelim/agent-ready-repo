# RFC-0078 notes — Codex design-doc review conclusions

This file records the distilled conclusions from the eight-round Codex CLI
adversarial review of `docs/architecture/workspace-mcp/design.md` (branch
`eugene/acp-core-pack-loop-trigger`). It is the closest available de-risk
evidence for RFC-0078; it is not a substitute for running Stage 0 spikes.

## Review summary

- **Rounds:** 8 (C1–C8), run against base branch `main`
- **Model:** `gpt-5.6-sol` via `codex review -c model="gpt-5.6-sol"`
- **Convergence:** Round 8 returned **zero P1 findings**

## Substantive design issues resolved

| Round | Finding | Resolution |
| ----- | ------- | ---------- |
| C6 | Trusted spawn: no `-I` flag; checkout could shadow installed wheel | Added `-I` to all spawn examples; Module-mode spawn spike (d) added |
| C6 | FSM gate scoping via branch-name parsing (fragile) | Changed to `WORKSPACE_MCP_SPEC_PATH` env var for gate scan |
| C6 | Outbox pattern: unconditional replay on startup → phantom events if crash before state write | Added 5-step recovery protocol: verify `pending.to == engine-state.json.state` before replay |
| C6 | `elicit` blocked stdio loop; nested `elicitation/create` response never read | Bounded worker-thread pool model documented; main stdio loop never blocked |
| C6 | Deferred watcher binding: only research types deferred | Extended deferred binding to ALL non-FSM types (all have first-run layout elicitation) |
| C6 | `expanduser()` called after `is_absolute()`; `~`-paths fail | Fixed ordering: `expanduser()` before `is_absolute()` and `resolve()` |
| C7 | Response-file race: control plane write not atomic | Added temp+rename atomicity requirement for response file |
| C7 | Pack-presence filter: wrong lookup roots | Added 6 roots (3 adapters × repo+user), OR logic, returns `available: false` |
| C7 | Research watcher rescans entire vault on each 200ms poll | Two-phase watcher: shallow-list until slug dir appears, then recursive on slug dir only |
| C8 | Slug safety: `{slug}` formatted into glob patterns without validation | `_SAFE_SLUG_RE = re.compile(r'^[a-zA-Z0-9._-]+')` guard before formatting |

## P2s resolved

| Round | Finding | Resolution |
| ----- | ------- | ---------- |
| C7 | External output path acknowledgment missing | `elicit()` called to confirm before watcher starts; `confirmed_workspace_root` written on confirmation |
| C8 | Two-phase research watcher not documented | Documented Phase 1 (shallow) / Phase 2 (recursive on matched dir) |

## Residual P2s (accepted, not resolved)

| Round | Finding | Rationale |
| ----- | ------- | --------- |
| C7 | `run_id` file inode/truncation detection alongside offset reset | Design doc already addresses this in Component 1; P2 was a clarification request, not a missing feature |

## Design quality evidence

The eight rounds collectively surfaced and closed ten P1 findings across:
trusted-spawn security, FSM gate scoping, outbox crash-consistency, threading
model, watcher binding, path expansion ordering, response-file atomicity,
pack-presence filtering, research watcher performance, and slug injection safety.

None of the P1 issues require changes to the RFC's charter-level decisions
(D1/D2). They are design-level issues now addressed in `design.md`. The review
log confirms the design doc is internally consistent at the P1 level.

## What this evidence does NOT cover

Spike lettering matches RFC-0078 § Stage 0 spikes:

- Spike (a): whether instruction durability holds in production AI hosts
- Spike (b): whether `x-core/` is the correct ACP v1 notification namespace
- Spike (c): whether MCP `notifications/message` frames reach the control plane as `session/update` events
- Spike (d): whether `python3 -I -m agentbundle.workspace_mcp` is installed and accepts the required env vars
- Spike (e): whether stdlib daemon threads + bounded worker pool handle `elicit()` MCP stdio concurrency (nested `elicitation/create` re-entrancy included)
- Whether `session/new.mcpServers` is honored in production Class A AI hosts
- Whether the `permissions.allow` additive-merge projection can be added
  to the agentbundle Claude adapter without a breaking contract change
