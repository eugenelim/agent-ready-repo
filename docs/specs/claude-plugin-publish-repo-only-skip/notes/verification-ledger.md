# Verification ledger: Claude plugin publish skips repo-only pack changes

Execution observations for `docs/specs/claude-plugin-publish-repo-only-skip`.

## Evidence

- Replay: the 200 most recent first-parent commits on `main` (2026-11-12) through the old and new push filters. The old filter, with the two catch-alls, starts a publish run on 128 of them; the new one on 68, which is 60 fewer (47%). The old filter's own comment claimed 40 of 200.
- Owner check of the remaining 68: none touches a file of a repo-only pack. 37 touch a published pack's shipping `.apm/` source, 29 touch a publish job input (`packages/agentbundle/**` 13, `Makefile` 9, the workflow and other inputs), and 2 touch only a README or JOURNEY file of a published pack.
- Tests: `tools/test-lint-plugin-roster.py` asserts the narrower expected set, the rejection of each removed catch-all, that repo-only packs' manifests and a skill file match no path in the real workflow, that published packs' manifests and the workflow file match, that `workflow_dispatch` and the `claude-plugin-publish` environment remain, that both lints are registered `_script_step` calls (read from the parsed source), and that promoting or withdrawing a pack with the workflow list unchanged fails the lint and passes once the list moves. Mutations (re-adding a glob, dropping a published pack, renaming the environment, making `expected_paths` ignore `PUBLISHED`, commenting out a lint registration) each fail a case.
- `python3 tools/lint-plugin-roster.py` reports 16 published, 7 withheld, 26 push paths pinned. `tools/test-publish-claude-plugins.py`, `lint-plugin-membership`, `lint-plugin-route-docs`, `actionlint` and `zizmor` pass on the edited workflow. `make lint-ruff lint-mypy` and `make precheck` pass.
- Review: Codex adversarial and security reviews of the spec and plan (three rounds) and of the code (two rounds). The security review found two test gaps in the code; both were repaired test-first. The last round was clean for both roles.

## Known limits

- Files of a published pack that never ship (tests, README, JOURNEY) still start a run; recorded as a follow-on in the spec.
- `Makefile` and `packages/agentbundle/**` edits start a run although most do not change the plugins; they are real inputs to the builder and cannot be told apart by path.
- `python3 tools/lint-claude-plugin-publish-control.py` fails with "evidence observed_at is older than 90 days; recapture publish-control evidence". It fails the same way on `main`, so this change did not cause it. Recapturing needs a live check of the publisher App and is the repository owner's.
