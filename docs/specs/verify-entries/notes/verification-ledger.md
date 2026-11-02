# Verification ledger: verify entries

Execution observations for this delivery. Paths are placeholders: `<checkout>` is the worktree root, `<scratch>` the `mktemp -d` directory a run created, and `<evidence-dir>` is `.context/verify/agentbundle-cli/<run-id>/`. `<ab>` is `PYTHONPATH=<checkout>/packages/agentbundle python3 -m agentbundle`.

## Run r1 — drift found at run start

Driven at commit `b693f1ed070738f45ea5780fc5cf88876502db65` from `docs/VERIFICATION.md` as first written.

- `<ab> render <checkout>/packs/core --target codex --output <scratch>/render` exited 0 and wrote no files.
- Classification: doc drift. `agentbundle render` selects distribution recipes by target, and a direct-install adapter target such as `codex` selects none, as the command's own module docstring states. The entry's Drive and Evidence were corrected to render with no `--target` and to check `<scratch>/render/apm/core/.apm/skills/work-loop/SKILL.md`. Run r1 reports no grade; r2 is the retry.
- Observation for the CLI's owners, not part of this delivery: a render that selects no recipe exits 0 silently. A message naming the empty selection would have made the drift visible without reading the output tree.

## Run r2 — live-verified

Driven at commit `b693f1ed070738f45ea5780fc5cf88876502db65` with the corrected entry. Grade: `live-verified`.

| Step | Command | Exit | Observed |
| --- | --- | --- | --- |
| Doctor | `<ab> --version` | 0 | `agentbundle 0.59.0 (spec 0.18, catalogue specification 0.1)` |
| Drive 1 | `<ab> render <checkout>/packs/core --output <scratch>/render` | 0 | `<scratch>/render/apm/core/.apm/skills/work-loop/SKILL.md` present |
| Drive 2 | `git init -q <scratch>/repo` | 0 | empty repository created |
| Drive 3 | `<ab> install <checkout> --pack core --scope repo --adapter codex --yes --output <scratch>/repo` | 0 | ready: `<scratch>/repo/.agentbundle-state.toml` present |
| Drive 4 | `<ab> diff --root <scratch>/repo --scope repo <checkout>/packs/core` | 0 | no output: the install matches a fresh render |
| Cleanup | remove `<scratch>` by its recorded handle | 0 | `<scratch>` gone; `<evidence-dir>` still holds all step transcripts |

## Mutation proof

- **Invariant:** the install matches a fresh render of the pack.
- **Catching test:** the entry's evidence check, `<ab> diff --root <scratch>/repo --scope repo <checkout>/packs/core` (`agentbundle diff`).
- **Exact mutation:** one line, `mutation-proof`, appended to `<scratch>/repo/.agents/skills/work-loop/SKILL.md` after Drive 4 in run r2. The deliberate break of the driven subject stands in for a revert to a pre-fix implementation, which a new entry does not have.
- **Expected failure:** `agentbundle diff` exits 1 and names `.agents/skills/work-loop/SKILL.md`.
- **Observed failure:** `agentbundle diff` printed `.agents/skills/work-loop/SKILL.md` and exited with exit 1.

## Receipts

Run r2:

```json
{
  "schema_version": 1,
  "receipt_id": "verify:agentbundle-cli:r2",
  "acceptance_fingerprint": "git:b693f1ed070738f45ea5780fc5cf88876502db65",
  "lineage": {"criterion_ref": "AC-0026"},
  "selector": {"term": "verify"},
  "freshness_mode": "exact-subject",
  "observation": {"type": "command-result"},
  "outcome": "live-verified",
  "producer": {"class": "verify-entry", "identity": "verify:agentbundle-cli"}
}
```
