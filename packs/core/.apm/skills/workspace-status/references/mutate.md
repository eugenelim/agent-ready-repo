# Mutate — selection, repair, and prune

Load this when the chosen mode is `mutate`. Every subcommand below either
writes a file or exists to prepare a write, so read this page before invoking
any of them.

The authority rule that governs all of them: you execute a selection an
authorized person supplied, and you never author, prefill, or suggest the
confirmation that authorizes it. Pause and let them create it out of band.

## Report membership without changing anything

**`selected-membership`** — requires at least one repository-relative
`docs/specs/<slug>` directory and evaluates only the supplied selection. Each
ordered result contains `selected_directory`, `canonical_artifact_path`,
`membership_present`, and `occurrences`. An occurrence identifies its
initiative when present, lifecycle collection, zero-based entry position, and
canonical, legacy, or parse-blocked form. The selected artifact need not exist.
The command reads `workspace.toml` and reports facts only: it never changes a
file, chooses an artifact for deletion, or turns presence or absence into an
operation exit gate. Invalid selectors and invalid workspace data return a
structured reason with a concise diagnostic.

## Repair subcommands

**`repair-plan`** — runs a full reconciliation scan (Type 1+2+3) and builds a deterministic repair plan for all automatically-resolvable Type 2 queue findings: queue entries whose spec shows `Shipped` (moved to `[work].shipped`) or `Archived` (removed from `[work].queue`). Emits a JSON plan to stdout and writes it to `.workspace-repair-plan.json` (override with `--plan-file`). The plan includes a SHA-256 fingerprint of `workspace.toml` so that `repair-apply` can detect stale plans. Type 1 and Type 3 findings, and any Type 2 `active`-list entries, appear in `manual_findings` — they require human review. `Approved` entries are never touched automatically. Exit 0 on success (including empty plan); exit 1 if workspace.toml is absent; exit 2 if the plan file cannot be written (stdout is still emitted).

**`repair-apply`** — loads the plan file written by `repair-plan` (default `.workspace-repair-plan.json`; override with `--plan-file`), verifies the SHA-256 fingerprint against the current `workspace.toml`, and applies each operation atomically via `tempfile.mkstemp`. Re-reads each spec's `Status` from disk at apply time; skips the operation (with a `skipped` record in `per_operation`) if the status has changed since the plan was made. Immediately before replacing `workspace.toml`, it revalidates every spec whose operation would be applied and aborts the whole write if any status or status-line fingerprint changed. Requires `tomlkit` to preserve TOML comments; exits 2 if `tomlkit` is unavailable. The write is skipped entirely when `operations_applied == 0` (no stray temp files). Exit 0 on success or all-skipped; exit 2 for any structural error (fingerprint mismatch, plan not found, parse error, invalid schema).

**Legacy migration planning** — when a retained legacy membership includes a
`migration` finding, show its exact observed source representation, lifecycle
membership, candidate route classes, and `next_action`. Never choose among the
candidates. A human must author the closed selection JSON out of band and pass
its repository-relative path with `--migration-selection`. Do not create,
edit, prefill, or suggest substantive values for a selection or confirmation
file. Migration planning is read-only and rejects `--plan-file`; a missing
canonical artifact returns the selected owning processor as `next_action`
without writing an artifact, ledger, repair plan, or workspace change.

**Legacy migration effects** — pause while the human authors each confirmation
file out of band. Never create, edit, or prefill it. The confirmation must be
fresh, single-use, and bound to the exact action, operation ID, and digest shown
by the reviewed plan or ledger. If the human needs opaque test-safe identifiers,
tell them to run `python3 -c 'import secrets; print("confirmation-" +
secrets.token_hex(16)); print("subject-" + secrets.token_hex(16))'` themselves;
do not run it for them. Apply requires all three migration arguments and rejects
`--plan-file` or `--yes`. Rollback requires a new confirmation and never reads,
changes, or deletes the canonical artifact. A `pending` or `rollback_pending`
ledger operation is recoverable only with another fresh confirmation. Surface
the closed migration result code and `next_action`; never echo source content on
credential, unsafe-context, authorization, or write refusals.

#### 1d. Prune workflow

The prune executes a selection supplied by an authorized caller. It does not
choose, rank, or discover deletion candidates. Supply each repository-relative
directory as a separate `--select docs/specs/<slug>` argument. The selection
must be non-empty; selectors must use that exact one-directory shape and must
not contain absolute paths, drive prefixes, backslashes, dot segments, nested
paths, file paths, duplicates, or links that escape the repository.

First obtain the unsigned challenge. Preview takes the shared writer lock while
it reads repository state, but it does not change any file:

```
["<python>", "<skill-dir>/scripts/workspace_status.py", "prune", "--root", "<repo-root>", "--select", "docs/specs/<slug>", "--preview"]
```

The binding fields in the output are `operation_id` and `operation_digest`.
The output also reports the canonical `selection` and target facts for review.
It never supplies `subject`, `role`, or `confirming_identity`; those three
authorization fields must come from an independent human-authority source.
A confirmation copied from preview output alone is invalid.

Pause while the authorized person creates a confined JSON file out of band.
Do not create, edit, or prefill it. It must contain exactly the two binding
fields from the preview plus the three independently supplied authorization
fields:

```json
{
  "operation_id": "<operation identity from preview>",
  "operation_digest": "<operation digest from preview>",
  "subject": "<independently supplied subject>",
  "role": "<independently supplied role>",
  "confirming_identity": "<independently supplied identity>"
}
```

Then execute the same selection with that file:

```
["<python>", "<skill-dir>/scripts/workspace_status.py", "prune", "--root", "<repo-root>", "--select", "docs/specs/<slug>", "--confirmation-file", "<repository-relative-confirmation.json>"]
```

The command uses the same confined confirmation-file reader as
`repair-apply`. A missing confirmation, malformed confirmation, stale
challenge, mismatched binding, or changed baseline refuses without mutation.
The repository-root `.workspace-prune-protected.toml` file may name selectors
that must never be pruned; an absent file means no selectors are protected, and
a malformed file fails closed.

Exit 0 means one observation under the held shared lock proved that every
selected artifact directory was absent and that no canonical, supported
legacy, or parse-blocked membership resolving to it survived. The two writes
are sequential, not atomic. A non-zero result names a stable refusal code:

- Selection and routing: `empty_selection`, `invalid_selector`, `unknown_subcommand`.
- Coordination and protection: `lock_busy`, `protected_target`, `nothing_to_remove`.
- Confirmation: `confirmation_missing`, `confirmation_invalid`, `confirmation_stale`, `confirmation_binding_mismatch`.
- Baseline and closure: `baseline_stale`, `closure_failed`.
- Repository input: `invalid_workspace`, `malformed_toml`.
- Platform capability: `unsupported_platform`, when the host offers no no-follow
  directory primitive. Confined removal depends on it, so the command declines
  rather than deleting with weaker protection. Nothing was attempted and nothing
  about the repository is wrong.

#### Recovering an interrupted prune

The two writes are sequential, so an interrupted run can leave the artifact
removed and its memberships present, and the shared lock file behind. Recover in
this order, and read rather than guess at each step.

1. `lock_busy` reports the lock file name and the process id recorded in it.
   Check whether that process is still running. If it is, wait — another writer
   holds the lock legitimately. Only if it is gone is the lock stale.
2. Remove a stale lock file by hand. Nothing removes it for you, because a tool
   cannot distinguish a crashed holder from a slow one.
3. `closure_failed` reports the selection and the last phase that completed.
   `artifacts_removed` means the directories are gone and their memberships are
   not; `memberships_removed` means both writes landed but the closure
   observation could not be established.
4. Re-run the prune for the same selection. It refuses `nothing_to_remove` when
   the artifact is already gone, because it will not report success for a run
   that removed nothing. Finish that case by removing the surviving memberships
   through the repair route, which reports them, rather than by editing the
   register by hand.

A re-run is safe: it re-derives its own baseline and confirmation, and refuses
rather than acting on a stale one.

Two residual limits remain. The shared lock excludes only writers that also
take it. A valid confirmation can be replayed if the exact same repository
state is reconstructed; no durable replay receipt is written.

#### 1e. Repair workflow

Use `repair-plan` + `repair-apply` to deterministically clean up stale queue entries without manual `workspace.toml` editing:

```
# Step 1 — inspect the plan (no writes to workspace.toml)
["<python>", "<skill-dir>/scripts/workspace_status.py", "repair-plan", "--root", "<repo-root>"]

# Step 2 — review the plan JSON; then apply (--yes is required to confirm the write)
["<python>", "<skill-dir>/scripts/workspace_status.py", "repair-apply", "--root", "<repo-root>", "--yes"]
```

**When to use:** after `reconcile` or `status` shows Type 2 stale-queue findings and you want automated cleanup without manual editing. The two-step design lets you review the plan before committing.

**`--plan-file <path>`** — override the plan file location for both subcommands. The path must resolve inside `<repo-root>`; symlinks that escape the root are rejected (exit 2, `plan_file_outside_root`).

**`tomlkit` availability** — `repair-apply` requires `tomlkit` (comment-preserving TOML writer). If absent, `repair-apply` exits 2 with `reason: "tomlkit_unavailable"`; surface to the user and install only with consent: `pip install tomlkit==0.15.1`. See `## Prerequisites` above. `repair-plan` does not require it.

**`repair-apply` result JSON key fields:**

```
schema_version     — 1
mode               — "repair-apply"
applied            — true if write succeeded; false on any structural error
operations_applied — count of operations actually written (0 when all skipped or empty plan)
per_operation      — list of {path, applied, reason?} for all operations
reason             — error reason string when applied:false (top-level field, structural errors)
```

**Interpreting `per_operation`:** each entry records `"applied": true` (written) or `"applied": false` with a `reason`:
- `spec_status_changed` — spec Status changed between plan and apply; human review needed
- `spec_status_unreadable` — spec.md not found or Status field missing
- `initiative_not_found` — ini_slug absent from workspace.toml
- `entry_not_found_in_queue` — path no longer in the queue (already removed or never present)

**`.workspace-repair-plan.json` and temp files** — both are written inside the repo root. Add them to `.gitignore` to avoid accidental commits (the temp files are cleaned up automatically on success).
