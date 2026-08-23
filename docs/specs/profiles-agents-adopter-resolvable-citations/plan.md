# Plan: profiles-agents-adopter-resolvable-citations

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

- **Files touched:** `profiles/AGENTS.md` (source of the sync pair);
  `packages/agentbundle/agentbundle/_data/catalogue-scaffold/profiles/AGENTS.md`
  and `.../catalogue-scaffold/manifest.json` (both written only by
  `sync_authoring_scaffold.py --write`);
  `packages/agentbundle/tests/integration/test_scaffold_projection.py`;
  release surfaces `packages/agentbundle/pyproject.toml`,
  `packages/agentbundle/agentbundle/version.py`,
  `packages/agentbundle/CHANGELOG.md`, `packages/agentbundle/README-pypi.md`,
  `docs/product/changelog.md`, `tests/roster/test_okf_catalogue_discovery.py`.
- **Tests that demonstrate done:** the generalized guard fails on the
  reintroduced hyperlink and on the reintroduced `tools/` citation, and passes on
  the corrected text; `sync_authoring_scaffold.py --check` exits 0; the roster
  release-metadata test passes under the Makefile `PYTHONPATH`; `make ci`.
- **Not changing:** the profile schema, `contracts/`, any CLI verb or flag, the
  `agentbundle catalogue contracts` implementation, `packs/AGENTS.md`,
  `packs/README.md`, `guides/_shared/reference/catalogue-authoring-standards.md`,
  and the `profiles/README.md` sibling.

### Tempted and declined

- **A blanket "no unshipped path in any scaffold Markdown" lint.** Prototyped
  against `b4dae24d`: it flags twelve citations in the guides authoring-standards
  hub that a ratified acceptance criterion deliberately admitted. Declined — it
  reverses a decision instead of enforcing one.
- **Adding `profiles/AGENTS.local.md` to re-home the sync command.**
  `AGENTS.local.md:35-37` already names `profiles/` and that script by route.
  Declined — a scoped copy would give one load-bearing fact a second home.
- **Shipping `contracts/` in the scaffold so the original link resolves.**
  Declined — the profile schema is package-internal by design and already
  readable through `catalogue contracts show`; shipping a second copy creates a
  parity surface with nothing to keep it honest.
- **Fixing the identical defect in `packs/README.md`.** Declined — `workspace.toml`
  records it as blocked with measured reasoning.

## Verification mode

- Tasks 1-3: **goal-based check + TDD.** The guard is the test; AC4's mutation is
  its red state.
- Task 4: **visual / manual QA.** Run the real CLI verb the new text tells an
  adopter to run and record its observed output.
- Task 5: **goal-based check.** Release-surface pins.

## Tasks

1. **Generalize the citation guard.** (`Depends on: none`)
   Retain `test_packs_agents_md_cites_only_paths_it_ships`, because
   `workspace.toml` names that live test directly. Extract
   `_assert_cites_only_shipped_paths` from it and add the sibling
   `test_profiles_agents_md_cites_only_paths_it_ships`; both delegate to the
   helper, which retains the shipped-set construction, `rooted` prefixes,
   `<`-placeholder exclusion, and `optional_by_design` carve-out. This keeps the
   established workspace reference valid and gives each file an isolated failure
   name.
   **Tests:** this task *is* the test. Red state: it must fail on unmodified
   `profiles/AGENTS.md`, naming `contracts/profile.schema.json` and
   `tools/catalogue/sync_authoring_scaffold.py`.

2. **Correct `profiles/AGENTS.md`.** (`Depends on: 1`)
   § *Validation and ownership*: keep the ownership sentence, name the schema
   `profile.schema.json`, route the reader with
   `agentbundle catalogue contracts show profile.schema.json`, and keep the
   source/projection sentence unchanged in meaning.
   § *Deeper pointers*: keep `profiles/_example/profile.toml` (it ships) and drop
   the repo-only script path without restating the obligation.
   **Tests:** task 1's guard turns green; `tools/lint-agents-md.py` passes; the
   file stays under the 80-line scoped cap.

3. **Rewrite the projection.** (`Depends on: 2`)
   `python3 tools/catalogue/sync_authoring_scaffold.py --write`, then `--check`.
   **Done when:** `--check` exits 0 and `manifest.json` digests match.

4. **Prove the guard and the route.** (`Depends on: 3`)
   Mutation A: reintroduce the hyperlink in the scaffold copy; guard fails naming
   `contracts/profile.schema.json`. Mutation B: reintroduce the `tools/` citation;
   guard fails naming it. Restore both by editing, never by `git checkout`.
   Then run `agentbundle catalogue contracts show profile.schema.json` from the
   built artifact and record its observed output.
   **Tests:** recorded pass/fail transcript for each mutation.

5. **Move the release surfaces together.** (`Depends on: 3`)
   Bump to `0.38.5` (`0.38.3` and `0.38.4` are claimed in-repo, PyPI's max is
   `0.38.2`, and no open PR claims a version). Update all six surfaces; add the
   `## [0.38.5]` section to the package changelog and the
   `### [agentbundle][0.38.5]` heading above `0.38.4` inside `## [Unreleased]`.
   **Done when:** `tests/roster/test_okf_catalogue_discovery.py` passes under the
   Makefile `PYTHONPATH`, and the topmost `### [agentbundle][…]` heading equals
   `version.py`.

6. **Correct the decision record.** (`Depends on: 2`)
   Rewrite the falsified premises in `workspace.toml`'s
   `packs-agents-normative-pointer` entry. Assert each anchor is unique before
   replacing, and re-parse the file with `tomllib` afterwards.
   **Done when:** the file parses, and no surviving sentence in that entry
   contradicts the tree.

## Constraints

- The commit needs an `Engine-Change-RFC:` trailer. The curation guard protects
  `packages/agentbundle/**` and carves out only
  `agentbundle/build/recipes/` and any path containing `/tests/`; the scaffold
  copy, `manifest.json`, and the four release surfaces under that prefix are all
  hits. Use the `n/a -- <reason>` form; do not invent an RFC number.
- `sync_authoring_scaffold.py --write` must be run by the supervisor: the worker's
  policy refuses bare-interpreter invocations.

## Risks

- Bare `pytest tests/roster/` fails on this host because an installed
  `agentbundle 0.38.1` shadows the worktree source. Measured on `b4dae24d`:
  1 failed under bare pytest, 3 passed under the Makefile `PYTHONPATH`. Judge the
  release-surface pin only under `PYTHONPATH`.
- Editing a construction-test module in `packages/agentbundle/tests/` can void a
  byte-pin elsewhere. Confirm no digest test covers
  `test_scaffold_projection.py` before committing.

## Changelog

- `[agentbundle][0.38.5]` — the bundled authoring scaffold's `profiles/AGENTS.md`
  routes to the profile schema with a command instead of a path an adopter's tree
  does not contain.
