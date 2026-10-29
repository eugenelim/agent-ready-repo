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
canonical or parse-blocked form. The selected artifact need not exist.
The command reads `workspace.toml` and reports facts only: it never changes a
file, chooses an artifact for deletion, or turns presence or absence into an
operation exit gate. Invalid selectors and invalid workspace data return a
structured reason with a concise diagnostic.

## Repair subcommands

**`repair-plan`** — runs a full reconciliation scan (Type 1+2+3) and builds a deterministic repair plan for all automatically-resolvable Type 2 queue findings: queue entries whose spec shows `Shipped` (moved to `[work].shipped`) or `Archived` (removed from `[work].queue`). Emits a JSON plan to stdout and writes it to `.workspace-repair-plan.json` (override with `--plan-file`). The plan includes a SHA-256 fingerprint of `workspace.toml` so that `repair-apply` can detect stale plans. Type 1 and Type 3 findings, and any Type 2 `active`-list entries, appear in `manual_findings` — they require human review. `Approved` entries are never touched automatically. Exit 0 on success (including empty plan); exit 1 if workspace.toml is absent; exit 2 if the plan file cannot be written (stdout is still emitted).

**`repair-apply`** — loads the plan file written by `repair-plan` (default `.workspace-repair-plan.json`; override with `--plan-file`), verifies the SHA-256 fingerprint against the current `workspace.toml`, and applies each operation atomically via `tempfile.mkstemp`. Re-reads each spec's `Status` from disk at apply time; skips the operation (with a `skipped` record in `per_operation`) if the status has changed since the plan was made. Immediately before replacing `workspace.toml`, it revalidates every spec whose operation would be applied and aborts the whole write if any status or status-line fingerprint changed. Requires `tomlkit` to preserve TOML comments; exits 2 if `tomlkit` is unavailable. The write is skipped entirely when `operations_applied == 0` (no stray temp files). Exit 0 on success or all-skipped; exit 2 for any structural error (fingerprint mismatch, plan not found, parse error, invalid schema).

**`needs-to-header` and `needs-drop-cooled` operations** — a registry entry that still carries typed `needs` is refused by `status` with `unmigrated_needs`, and `repair-plan` moves its edges to the waiting item. For each non-cooled canonical membership with a non-empty typed `needs` array, the plan holds one `needs-to-header` operation: `waiting_path`, `waiting_sha256`, the `registry_edges`, the `depends_on_items` (a typed reference — `spec:<dir>`, `brief:<slug>`, or `<intent kind>:<slug>` — for a spec, brief, or intent target, and the target's path for a captured item), and the `receipt_items` (one `<reference> completion …` or `<reference> coordination …` receipt per edge that carries one). A cooled membership gets a `needs-drop-cooled` operation instead: `waiting_path` and `dropped_cooled`, with no read of the waiting item, because a cooled item contributes no edge. An edge the header cannot hold as the same edge becomes a manual finding naming the waiting path and the target, and its membership gets no operation: a brief or intent target that is missing, retired, or has no `Slug:`; a captured item that carries a completion receipt; a registry `kind` that differs from the target's own kind; a cross-repo edge whose `path` differs from its `containing_brief`; a receipt value outside the receipt grammar; a path holding a comma, a space, or a control character; and a waiting item that is unreadable, a link, multiply linked, or has no `- **Field:**` line to anchor on. When the workspace itself is invalid (`invalid_workspace` or `configuration_mismatch`), the plan holds no operation of any type and no such finding. The plan file holds every path, item, and receipt whole. The plan and `repair-apply` output show each part of an echoed value only when it is a valid reference, path, or receipt token of at most 200 characters with no control character, and show a part that fails as an empty string.

On `repair-apply --yes`, each `needs-to-header` operation is checked under the writer lock: the waiting path must be the `path` of exactly one non-cooled canonical membership, the plan's items must equal the items re-derived from that entry's current `needs`, the waiting file's SHA-256 must match the plan, and the file must be a regular, singly linked file inside the repository with no link in any segment. A failed check refuses that operation and leaves its `needs` as it was. Otherwise the operation adds its items after the last `- **Field:**` line of the preamble, appending to an existing `Depends on:` or `Dependency receipts:` line and skipping an item or a receipt already present for the same reference, and replaces the file atomically. One atomic `workspace.toml` write then sets `needs = []` on the entries that applied and changes no other byte. A `needs-drop-cooled` operation is refused, keeping `needs`, when its membership is no longer cooled or the cooled state cannot be read. An interrupted run leaves `needs` in place, so `unmigrated_needs` keeps refusing the entry, and a rerun of `repair-plan` and `repair-apply` adds nothing twice and clears `needs`.

The output of `repair-apply` compares edges, where an edge is a waiting path, a reference, and a receipt: `header_edges_before` (read from each waiting item before the write; every item counts), `registry_edges` (the registry's edges, without the dropped ones), `dropped_cooled`, and `header_edges_after` (read back from each waiting item; only items the reader accepts count), with `edges_equal` true when the read-back set equals `header_edges_before` plus `registry_edges`. It exits 1 when they differ, and an operation whose edges differ keeps its `needs`.

**`captured-to-file` operation** — a captured item registered outside `docs/product/captured/` is refused by `status` with `unmigrated_captured_item`, and `repair-plan` writes one record for it under `docs/product/captured/`. The command pair is `repair-plan`, then `repair-apply --yes` on the plan file. Show the owner the whole plan file and apply nothing until the owner confirms that exact file: it holds every record slug, kind, and the full record text. Each operation carries `record_path`, `record_text`, and the `entry_locator`; a membership also carries its `source_path`, `source_sha256`, and `registry_fingerprint`, and a legacy captured entry (a slug-only entry) carries its `slug`. A record holds the title, `Status:`, `Kind:`, `Type:` (a legacy entry whose type is a shaping type), `Resolution:` (a closed defect), `Parent intent:`, `Detail:` naming the old note, and then the summary under `## Summary`. The old note's `Depends on:` and `Dependency receipts:` lines are copied into the record, not moved, because the repair never writes a source file; after the repair the old note's copies are inert and may be deleted by hand.

On `repair-apply --yes`, under the shared writer lock, each operation re-derives its content from the current tree and is refused when the plan no longer matches: a changed source file, a changed registry, an edited operation, a membership cooled after planning, a record path now holding other bytes, a record directory that is a link, or cooling state that cannot be read. A refused operation leaves its entry where it was. Records are created exclusively at their final path, then one atomic `workspace.toml` write re-points the applied memberships' `path` and changes no other byte. A record cut short by a crash is a regular file with other bytes; the next `repair-plan` reports it as a manual finding naming its path, the owner removes it, and the next run finishes. The repair never deletes a file. `repair-apply` compares the items before and after: `captured_before` (each item's slug, kind, and source path), `captured_after` (each record read back), the copied dependency lines as `header_edges_before` and `header_edges_after`, and `captured_equal`. It exits 1 when `captured_equal` is false, for example after a record is edited by hand between the write and the read-back. Manual findings in the plan name the item and the reason, such as a status that conflicts with its collection, a typed `needs` still on the entry, an item that is a dependency target, a slug that is invalid or collides, or a record that differs from the one derived.

**`intent-brief-drop` operation** — an intent or brief needs no registry entry, so `repair-plan` holds one `intent-brief-drop` operation for each canonical repo-origin entry that is an intent with a `path` under `docs/product/intents/` or a brief with a `path` under `docs/product/briefs/`, cooled or not. A captured item's entry is never dropped, whatever its `kind`, including one the same run's `captured-to-file` operation moves. Each carries an `entry_locator` (the initiative key, empty for a top-level collection; the collection label such as `brief_queue.executing`; and the index in that collection), the entry's `path` and `kind`, and its `registry_fingerprint`. A tracker-origin entry, an entry of any other kind or location, and a legacy entry get none. `repair-apply --yes` runs every `needs-to-header` and `needs-drop-cooled` operation first. Before it changes anything, it checks each drop against the `workspace.toml` it read under the writer lock: the entry at that initiative, collection, and index must have the planned `path` and `kind`, match the planned fingerprint, and still qualify by that rule at its planned path; the check then holds that entry. After the other operations run, it removes each held entry in the same atomic, comment-preserving `workspace.toml` write, so an array a queue operation shortened cannot redirect a drop. A drop is refused, and its entry kept, when that check fails or when the entry still has `needs` after the needs operations ran, as it does when its `needs-to-header` operation was refused. A run where every needs operation applies leaves no repo-origin intent or brief entry, and the next `repair-plan` holds no `intent-brief-drop` operation. If an intent rename is pending (an `.intent-rename-*` stage exists), tell the user to recover or roll back that rename before `repair-apply`, so the drop reads the registry the rename left.

**`spec-entry-drop` operation** — a spec is registered by its own header, so `repair-plan` holds one `spec-entry-drop` operation for each repo-origin spec entry in a `work.` or `backlog.` collection whose `needs` is empty, or that a `needs-to-header` or `needs-drop-cooled` operation of the same plan empties. Each carries the same `entry_locator`, `path`, `kind`, and `registry_fingerprint` as an `intent-brief-drop` operation. An entry in any other collection, a tracker-origin spec, an entry of another kind, a legacy entry, and a table with no `needs` key get none and keep the finding they have today. A candidate gets no `queue-to-shipped` or `queue-remove` operation: the drop removes it in the same run.

*Held entry.* A cooled candidate is held when its `source.parent` key is present and declares a parent, but its lifecycle record carries no `parent`. The declared parent is `none` when the value is `none`; otherwise it is the value as the provenance normalizer resolves it (a `brief:<slug>` pointer becomes a path), when that path is a brief file listed in `docs/product/briefs/` and matches `docs/product/briefs/<slug>.md` with a lowercase alphanumeric slug of at most 128 characters. An absent key, or any other value, declares no parent, so the entry is dropped and the record is left as it is. A held entry gets no `spec-entry-drop` operation and keeps its collection. The plan holds one manual item for it (`finding_type` 6, reason `held-record-lacks-parent`) naming the entry `path`, the lifecycle record's path (`record_path`), and the `parent` value to add to that record. `workspace-status` never writes a lifecycle record: a person adds the `parent` to the record, and the next `repair-plan` drops the entry. When cooling state cannot be read, the plan holds no `spec-entry-drop` operation.

On `repair-apply --yes`, every `needs-to-header` and `needs-drop-cooled` operation runs first, then the queue operations, then the drops, all in one atomic, comment-preserving `workspace.toml` write. Under the writer lock, each drop is re-derived from the registry read there by the rule the plan used: the entry at the planned locator must still be a candidate with the planned `path`, `kind`, and fingerprint, and must not be held, with its record read again. A drop is refused, and its entry kept, when that check fails or when the entry still has `needs` after the needs operations ran. A run where every planned operation applies leaves no candidate except held entries, and the next `repair-plan` holds no `spec-entry-drop` operation.

**Legacy migration recovery and rollback** — use `repair-plan --migration-selection`
and `repair-apply` only when `.workspace-migrations.json` already records an
operation from a previous run. For a `pending` (interrupted apply) or
`rollback_pending` (interrupted rollback) operation, the same command is rerun
with a new confirmation. For an `applied` operation, a rollback confirmation
restores the exact legacy TOML slice. In every case the human authors that
confirmation out of band while you pause; you never write one.

The plan file includes a derived operation ID. For recovery of an existing
operation, use the operation ID recorded in `.workspace-migrations.json` — not
the re-derived plan's ID. A re-derived plan's ID does not match an operation
planned under an earlier Core version.

A former legacy entry with no prior ledger operation is rewritten by the user
in canonical form by hand. Tell the user which entry is affected and that the
legacy record goes in the same edit. Do not choose its target collection or
delete the legacy record yourself; make that edit only when the user asks and
names the target entry and collection, then run `workspace-status` to confirm.

**Legacy migration planning** — show the exact observed ledger operation, its
lifecycle membership, its `candidate_routes`, and `next_action`. Never choose
among the candidate routes. A
human must author the closed selection JSON out of band and pass its
repository-relative path with `--migration-selection`. Do not create, edit,
prefill, or suggest substantive values for a selection or confirmation file.
Migration planning is read-only and rejects `--plan-file`; surface the
`next_action` without writing an artifact, ledger, repair plan, or workspace
change.

**Legacy migration effects** — pause while the human authors each confirmation
file out of band. Never create, edit, or prefill it. The confirmation must be
fresh, single-use, and bound to the exact action, operation ID, and digest shown
by the reviewed plan or ledger. If the human needs opaque test-safe identifiers,
tell them to run `python3 -c 'import secrets; print("confirmation-" +
secrets.token_hex(16)); print("subject-" + secrets.token_hex(16))'` themselves;
do not run it for them. Apply requires all three migration arguments and rejects
`--plan-file` or `--yes`. Rollback requires a new confirmation and never reads,
changes, or deletes the canonical artifact. Surface the closed migration result
code and `next_action`; never echo source content on credential, unsafe-context,
authorization, or write refusals.

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
- `entry_locator_mismatch` — the registry read under the lock holds no entry at an `intent-brief-drop` or `spec-entry-drop` operation's planned locator, including an entry that is gone, or holds one whose path, kind, or fingerprint differs from the plan
- `entry_not_droppable` — the entry at the planned locator matches the plan but is no longer a repo-origin intent under `docs/product/intents/` or brief under `docs/product/briefs/`
- `entry_not_droppable` (for a `spec-entry-drop` operation) — the entry matches the plan but is no longer a repo-origin spec in a `work.` or `backlog.` collection with empty `needs`
- `entry_held` — the entry is now held: it is cooled and declares a parent its lifecycle record still lacks
- `cooling_state_unavailable` — a `spec-entry-drop` could not be checked because cooling state is unreadable
- `entry_not_found` — the editable `workspace.toml` has no matching table at the planned locator although the parsed registry does, or an earlier operation in the same run already claimed or removed that entry
- `entry_has_needs` — the entry still has `needs` after the needs operations ran; resolve them, then re-plan

**`.workspace-repair-plan.json` and temp files** — both are written inside the repo root. Add them to `.gitignore` to avoid accidental commits (the temp files are cleaned up automatically on success).
