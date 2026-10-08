---
title: Recover or roll back a migration operation
summary: Recover an interrupted apply or roll back an operation already recorded in a migration ledger.
pack: core
kind: how-to
---

# Recover or roll back a migration operation

Use this only when `.workspace-migrations.json` already records an operation
from a previous run — either `pending` (interrupted apply), `applied` (ready
for optional rollback), or `rollback_pending` (interrupted rollback).

To update a former legacy workspace entry that is not in a migration ledger,
rewrite it in canonical form by hand. Ordinary status no longer accepts legacy
shapes; they surface as `unsupported_legacy` findings. Write a target entry
directly:

```toml
{path = "docs/specs/<slug>/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "<current outcome>", needs = []}
```

Then remove the legacy record. Run `workspace-status` to confirm the entry
reconciles as expected.

## Recover an interrupted apply

Rerun the same apply command with a new current-session confirmation. The
ledger and current workspace bytes determine whether recovery completes the
pending operation or returns an idempotent `already_applied` result. Never
reuse the interrupted confirmation.

The repository must declare the closed effect policy:

```toml
[authorization.migration]
contract_version = "work-intake-migration-authorization.v1"
approver_roles = ["migration-approver"]
```

Generate each opaque value outside migration tooling with an OS-backed CSPRNG:

```bash
python3 -c 'import secrets; print(secrets.token_hex(16)); print(secrets.token_hex(16))'
```

Do not put a name, email, account ID, credential, or organization identifier in
either opaque field. Confirmations expire after five minutes and are
single-use.

Apply exactly the reviewed operation:

```bash
python3 .agents/skills/workspace-status/scripts/workspace_status.py \
  repair-apply \
  --root . \
  --migration-selection reviewed-selection.json \
  --operation-id migration-<digest> \
  --confirmation-file apply-confirmation.json
```

Migration apply rejects `--plan-file` and `--yes`.

## Roll back an applied operation

Review the applied operation in `.workspace-migrations.json`, then author a
fresh confirmation with `action = "rollback"`. Run:

```bash
python3 .agents/skills/workspace-status/scripts/workspace_status.py \
  repair-rollback \
  --root . \
  --operation-id migration-<digest> \
  --confirmation-file rollback-confirmation.json
```

Rollback restores the exact legacy TOML slice at its original membership and
index. It never deletes or rewrites the canonical artifact. Interrupted
rollback follows the same rule: retry with a new confirmation and let the
ledger recover from `rollback_pending`.

## Plan a migration (recovery path only)

If you have a prior selection on record but need to re-derive the plan before
re-applying, run planning read-only:

```bash
python3 .agents/skills/workspace-status/scripts/workspace_status.py \
  repair-plan \
  --root . \
  --migration-selection reviewed-selection.json
```

Migration planning rejects `--plan-file`. `artifact_missing` names the owning
processor as the next action. Manual, sensitive, stale, duplicate, unsafe, or
impossible routes fail without writes.

## Verify the result

Run `workspace-status` again. After apply, the target entry should be canonical
and uniquely registered. After rollback, the former legacy finding should be
visible and non-dispatchable, while the artifact remains on disk. Keep
`.workspace-migrations.json`; it is the durable recovery and rollback record.

For the exact entry and ledger boundaries, see
[workspace.toml schema reference](../reference/workspace-toml-schema.md).
