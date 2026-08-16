# Plan: workspace-backlog-reconciliation

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `workspace.toml` — `[backlog]` only.
- `docs/specs/workspace-backlog-reconciliation/{spec.md,plan.md}` — this contract.

**What demonstrates done**
- Goal-based: `python3 .claude/skills/workspace-status/scripts/workspace_status.py status --root .` exits 0 and reports 143 open entries (AC9).
- Goal-based: `git diff workspace.toml` shows hunks inside `[backlog]` only (AC8).
- Each corrected claim re-verified by the command recorded in its entry.

**What I am NOT changing**
- No code, no lint, no CI. The `pyyaml` audit gap AC2 names is recorded, not fixed
  — fixing it is a Makefile change and belongs in its own PR.
- No `type` values on the five reanchor entries (AC6 corrects the comment only).
- No `[work]` / `[shaping_queue]` / `[brief_queue]` / initiative membership.

## Declined patterns

- **Tempted:** migrate all 141 `unsupported_legacy` entries to canonical target
  entries in this PR. **Declined:** a target entry requires a real artifact `path`;
  backlog ideas have none, so every one would be a fabricated path. The engine's own
  remediation forbids inferring one.
- **Tempted:** fix the `pyyaml` SCA gap while I'm looking at it. **Declined:** it is
  a Makefile gate change in a file this PR does not otherwise touch — outside the
  bundled-fixes carve-out (different area, behavior change to a gate).
- **Tempted:** retype the five `type = "spec"` entries to `shape` so they become
  `legacy_entry`. **Declined:** that changes which room they display in and which
  guard sees them — a routing decision, not a comment fix. Recorded as AC7.
- **Tempted:** close `ast07-sca-scanner-agentbundle` outright, since the headline
  concern is covered. **Declined:** the `[lint]` extra is genuinely unaudited, so
  closing it would make the backlog assert something false.

## Tasks

### T1 — Verify every claim (no writes)
- **Mode:** goal-based. `Done when:` each of the seven commands in the spec has been
  run and its output recorded here.
- **Tests:** no stub (goal-based).

### T2 — Apply the `[backlog]` edits
- **Mode:** goal-based. `Done when:` AC1–AC7 edits are in `workspace.toml` and it
  parses (`tomllib.load`).
- **Tests:** no stub (goal-based).

### T3 — Verify scope and backend
- **Mode:** goal-based. `Done when:` AC8 (diff confined to `[backlog]`) and AC9
  (backend exit 0, count 143) both hold.
- **Tests:** no stub (goal-based).

## Verification log

- **AC1** `grep -oE 'href=(\{[^}]*\}|"[^"]*")' web/src/pages/primitives-fixture.astro` -> 2 hits, both live. 0 of the 8 named placeholders remain.
- **AC2** `tomllib` on both pyproject.toml -> `dependencies = []` for agentbundle and credbroker; agentbundle `[lint]` extra = `['pyyaml>=6.0']` (unaudited residual).
- **AC3** `grep -rn "install research" guides/` -> 0 hits.
- **AC4a** `python3 tools/repo/check_contract_drift.py` -> exit 0, no output (2nd clean pass).
- **AC4b/c** AC4 checked `[x]` at docs/specs/jira-check-sso-auto-login/spec.md:307; AC11 satisfied in the same spec.
- **AC5** `grep -rl "^## Acceptance criteria" docs/specs/*/spec.md | wc -l` -> 17 (canonical casing: 299).
- **AC6** `_SHAPING_TYPES` = {design, research, shape, signal, strategy}; `parse_legacy_workspace_entry('backlog.open', {'slug':'x','type':'spec'})` -> `unsupported_legacy`.
- **AC8** tomllib section-diff vs `git show HEAD:workspace.toml` -> only `backlog` changed.
- **AC9** backend exit 0; `repo_backlog.open` = 143 (was 143; -1 AC1, +1 AC7).
- **GATES** lint-spec-status exit 0 ("spec metadata clean"); `make lint-ruff` exit 0; `SKIP_SAST=1 make build-check` exit 0 (diff touches no SAST-relevant path).
- **REVIEW** `adversarial-reviewer` = named skip (session instruction prohibits subagent dispatch unless requested). Self-review run against the spec-less checklist instead.
