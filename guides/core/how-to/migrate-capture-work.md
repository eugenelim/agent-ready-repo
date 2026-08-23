---
title: Migrate a legacy workspace entry safely
summary: Plan, apply, recover, and roll back one reviewed legacy workspace entry without deleting its canonical artifact.
pack: core
kind: how-to
---

# Migrate a legacy workspace entry safely

Use this when `workspace-status` reports `legacy_entry` and the canonical
artifact already exists. Start read-only:

```text
Plan migration for this legacy workspace entry from the reviewed selection.
Do not apply it.
```

You receive a stable operation ID and digest. `workspace.toml`, the canonical
artifact, and `.workspace-migrations.json` remain unchanged until a person
reviews the plan and supplies fresh effect confirmation.

## Before you start

Run `workspace-status` and inspect the exact legacy collection, index, source
slice digest, candidate routes, and next action. A legacy entry is visible but
never dispatchable.

Create and review the canonical artifact through its owning processor first.
Migration tooling never creates, edits, or deletes that artifact. A spec also
needs its existing sibling `plan.md` before migration can be planned.

The repository must declare the closed effect policy:

```toml
[authorization.migration]
contract_version = "work-intake-migration-authorization.v1"
approver_roles = ["migration-approver"]
```

Use only the public roles accepted by the policy. The ledger retains a digest
of the matched role, not the raw role.

## Supply the reviewed selection

A person authors the closed `work-intake-migration-selection.v1` JSON file in
an out-of-band current-human session. It binds the observed legacy finding,
workspace fingerprint, exact collection/index/slice digest, selected target
entry and membership, owning processor, provenance reference, and positive
privacy attestation.

The agent and migration tooling may show observed candidates and required
bindings. They must not create, prefill, choose, or edit the selection.

Plan with the installed workspace-status script:

```bash
python3 .agents/skills/workspace-status/scripts/workspace_status.py \
  repair-plan \
  --root . \
  --migration-selection reviewed-selection.json
```

Migration planning rejects `--plan-file`. `artifact_missing` names the owning
processor as the next action. Manual, sensitive, stale, duplicate, unsafe, or
impossible routes fail without writes.

## Confirm and apply one operation

A person authors a fresh closed `work-intake-migration-confirmation.v1` file.
It binds `action = "apply"`, the exact operation ID and digest, two independently
generated opaque values, an authorized public role, the current RFC 3339 time,
and `authorization_source = "current-human-session"`.

Generate each opaque value outside migration tooling with an OS-backed CSPRNG,
for example:

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

Migration apply rejects `--plan-file` and `--yes`. It writes a pending ledger
receipt before changing `workspace.toml`, replaces the exact reviewed legacy
slice with the target entry, then records the applied fingerprint. A stale
workspace, artifact, selection, ledger, or confirmation refuses before the
effect.

## Recover an interrupted apply

Rerun the same apply command with a new current-session confirmation. The
ledger and current workspace bytes determine whether recovery completes the
pending operation or returns an idempotent `already_applied` result. Never
reuse the interrupted confirmation.

## Roll back the representation

Review the applied operation, then author another fresh confirmation with
`action = "rollback"`. Run:

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

## Verify the result

Run `workspace-status` again. After apply, the target entry should be canonical
and uniquely registered. After rollback, the legacy finding should be visible
and non-dispatchable, while the artifact remains on disk. Keep
`.workspace-migrations.json`; it is the durable recovery and rollback record.

Next, either continue with the now-dispatchable canonical route or resolve the
finding that caused a refusal. For the exact entry and ledger boundaries, see
[workspace.toml schema reference](../reference/workspace-toml-schema.md).
