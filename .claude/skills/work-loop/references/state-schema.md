# Work-loop state

A spec-driven loop carries a small amount of session-scoped state — how
many iterations have run, what budget is left, what findings the last
review surfaced. Putting that in prose ("we cap at 5 iterations…") leaves
it un-enforceable. Putting it on disk as data lets a tiny tool gate
each phase. That tool is [`scripts/loop-cohort.py`](../scripts/loop-cohort.py);
the data lives at `docs/specs/<feature>/state.json`, and the template
lives at [`assets/state.json`](../assets/state.json).

**State mutation is owned by `loop-cohort`.** The tool's verbs (`init`,
`approve-plan`, `auto-parallel`, `review record`, `worktree {add, record,
list, merge, cleanup, preflight}`) are the only sanctioned way to write
`state.json`.
Do not edit the file by hand or invoke `git worktree` directly — the
tool guarantees atomic writes, fingerprint algorithm consistency, and
match-first/write-second/state-last ordering. SKILL prose calls each
verb at the appropriate phase.

**Fields:**

| Field | Meaning |
|---|---|
| `feature` | spec slug (informational) |
| `iteration_count` / `max_iterations` | how many in-session loops have run / hard cap |
| `token_budget_used_pct` / `token_budget_cap_pct` | session token budget — **advisory in Phase 1**; the kill criterion fires only if the orchestrator populates `_used_pct`, which is wired up in a later phase |
| `consecutive_same_error_count` / `consecutive_same_error_threshold` | gate-error stuck-loop counter / cap. **Advisory in Phase 1** — the SKILL doesn't yet prescribe when to increment `_count`. Threshold lives in data so a project can tune it. |
| `plan_review_status` | `pending` until the spec-mode adversarial review clears, then `approved` (flipped by `loop-cohort approve-plan`). Enforced as a gate on **all phases** (not just `--phase plan`) — `implement` and `review` also reject a `pending` state. |
| `auto_parallel` | per-run unattended pre-authorization (default `false`; flipped by `loop-cohort auto-parallel` / `--off`). When `true`, supervisor mode fans out a wave that has **already cleared the gate** without the follow-on-1 human opt-in. **GO-approval-only**: never a gate input, never parallelizes a non-cleared wave, and a failed parallel wave still Surfaces and stops (no auto-recover). Per-run session scratch — a fresh run defaults `false`. Flat top-level field, distinct from the dry-run-gated `worktrees` schema. |
| `last_commit_sha` | latest commit produced by the loop (informational; advisory in Phase 1) |
| `finding_fingerprints` / `previous_finding_fingerprints` | hashes of reviewer findings, rotated each REVIEW iteration by `loop-cohort review record`; used to detect circling. Algorithm: `sha1("<file>|<line>|<title>")`, anchored on the adversarial-reviewer's documented `**N. <title>.** \`file:line\`. … Fix: …` format. |
| `worktrees` | one entry per `implementer` subagent dispatched in the current session's supervisor pass: `{task_id, branch, path, status, report_path}` where status is `in-progress` / `ready` / `blocked` / `failed` and `report_path` points at the implementer's markdown report under `docs/specs/<feature>/notes/`. Report files are gitignored (`docs/specs/**/notes/implementer-*.md`) — session-scratch like `state.json`, not history. Entries persist with their terminal status for the rest of the loop so a future reader can reconstruct what each task did. Empty in single-agent loops. See [`supervisor-mode.md`](supervisor-mode.md) for the dispatch/merge procedure. |

**Exit contract.** `loop-cohort check` exits 0 when the phase is
satisfied and non-zero when it isn't, with a one-line reason on stderr.
Treat non-zero as "stop and surface" — with one deliberate exception:
the SKILL's PLAN-init step calls the tool with `--phase plan`
*expecting* exit 1 with `plan not approved`. That exit-1 is the cue to
run the spec-mode reviewer, not a real stop. Any other non-zero exit
terminates the loop.

**Lifecycle.** `state.json` is **per-session scratch**, not history. The
file is gitignored (`docs/specs/**/state.json` in
[`.gitignore`](../../../../.gitignore)); `loop-cohort init` writes it
from the template at PLAN start. Across sessions, a fresh run
re-initializes — intentionally; a new session deserves a fresh budget.

**Atomic writes.** `loop-cohort` updates `state.json` mid-iteration and
reads it between phases. Every write goes through `tempfile.mkstemp` +
`os.replace`, so a partial-write doesn't present as malformed JSON and
falsely stop the loop.

**Changing the cap.** Editing `assets/state.json` changes the
*starting point* for any **newly-initialized** spec. To change the cap
for a spec that's already running, edit that spec's own (gitignored)
`docs/specs/<feature>/state.json` — the template edit doesn't propagate
backward. The numbers move with the data, not the SKILL prose. (Editing
a running `state.json` is the only sanctioned by-hand write; all other
mutations go through `loop-cohort`.)
