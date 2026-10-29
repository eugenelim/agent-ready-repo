# Verification ledger: reproducible preservation authoring on the shared-graph case

## Dispatch, 2026-10-29

The owner (Platform Core) directed the controller to implement T1–T4 itself;
each task's dispatch receipt is recorded as `human-directed`.

## T1 — reference edits and content pins, 2026-10-29

- Red: the four new `RULES` phrases in
  `packs/core/tests/skills/new-spec/test_shared_substrate_preservation.py`
  failed on the unedited reference (4 failed, 11 passed).
- Green: after Edits 1–3, `packs/core/tests/skills/new-spec/` and
  `packs/core/tests/skills/work-loop/test_preservation_evidence_reference.py`
  pass (297 passed, 82 subtests, 77 s).

## T2 — release, projection, and registration, 2026-10-29

- Core is 3.1.39 in `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json`, one patch above 3.1.38 at the base
  `b1be32193`; fragment `docs/product/changelog.d/ae86168c-4ce0-444b-929b-12c0020ce909.md`
  names `core` 3.1.39.
- `agentbundle catalogue self-host --root . --write --force` re-run leaves no
  diff; the reference's two projections changed.
- `git diff --exit-code <base> HEAD -- packs/core/.apm/skills/new-spec/evals/`
  exits 0; the only path under `packs/core/.apm/` and `contracts/` in the diff
  is the reference.
- `tests/roster/test_workspace_retirement_inventory.py`: 127 passed (136 s).
  `lint-brief-coverage.py`: 26 briefs checked, exit 0.
- `tools/check-core-release.py --base origin/main` fails with "/now/ payload
  bullets differ from the core 3.1.39 changelog entry". The same command fails
  for 3.1.38 on `main` at `b1be32193`, so it is pre-existing and outside this
  diff; captured as `docs/product/captured/pre-existing-check-core-release-now-anchor.md`
  and treated as a known skip. No CI workflow or Makefile target runs it.
