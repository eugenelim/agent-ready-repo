# Cut a package release

This page covers how to publish a new version of `agentbundle` or `credbroker` to
PyPI. Pushing a tag on `main` starts the release workflow, and the workflow builds
and publishes the package. Your job is to make the version files agree before the
merge, push the right tag, and approve and watch the run.

Whether a change needs a release at all is covered in
[release coupling](../explanation/release-coupling.md). This page starts once you
know it does.

## Rules for both packages

- Publish only from `main`. Both release workflows refuse a tag whose commit is not
  on `origin/main`. Never push a release tag from a feature, research, or worktree
  branch.
- Move every version file in the same PR as the change it releases. The tag job
  fails when `pyproject.toml` and the tag disagree.
- After a version-bumping PR merges, tag and push straight away. An untagged bump
  leaves `main` claiming a version that PyPI does not have.
- Choose the next version from the published index, not from `main` alone. Run
  `python3 -m pip index versions <package> --index-url https://pypi.org/simple`.
  Pass `--index-url`, because a machine set up for a private index answers from
  that index instead.
- Never reuse a version number that reached any index. Fix forward with the next
  patch version.
- Run the manual rows in
  [`docs/product/release-checklist.md`](../../product/release-checklist.md) that
  apply to the change, and tick them in the PR description.

## Release agentbundle

The workflow is
[`.github/workflows/release-agentbundle.yml`](../../../.github/workflows/release-agentbundle.yml).
It runs on any `agentbundle-v*` tag.

### Files that move together

Bump all six in the feature PR. `X.Y.Z` is the new version, and the date is the
release date in `YYYY-MM-DD` form.

| File | What changes |
| --- | --- |
| `packages/agentbundle/agentbundle/version.py` | `CLI_VERSION = "X.Y.Z"` |
| `packages/agentbundle/pyproject.toml` | `[project].version = "X.Y.Z"` |
| `packages/agentbundle/CHANGELOG.md` | A new top entry `## [X.Y.Z] — YYYY-MM-DD` in Keep a Changelog form, with breaking items marked |
| `packages/agentbundle/README-pypi.md` | A new first `## What's new in X.Y.Z` heading. This file is the PyPI project page |
| `docs/product/changelog.d/<uuid>.md` | A product changelog fragment for `agentbundle` `X.Y.Z` |
| `tests/roster/test_okf_catalogue_discovery.py` | The `expected = "X.Y.Z"` pin |

The roster test checks that `version.py`, `pyproject.toml`, the first
`README-pypi.md` heading, the first `CHANGELOG.md` heading, and the newest product
changelog release all name the same version. It runs only in the dispatch-only
`test-roster.yml`, so PR CI stays green when you forget the pin.

Create the fragment with the command that
[`docs/product/AGENTS.md`](../../product/AGENTS.md) describes, then edit the file
it writes:

```bash
python3 tools/changelog.py new --package agentbundle --version X.Y.Z \
  --date YYYY-MM-DD --highlight "Describe the released outcome."
```

### Steps before merge

1. Add an `Engine-Change-RFC:` trailer to each commit that touches
   `packages/agentbundle/`. Name the RFC that governs the change, or write
   `n/a — <reason>` when none does. `tools/lint-catalogue-curation-guard.py`
   enforces this in `build-check.yml`. Locally, run it with `--base origin/main`,
   because without a base it skips the check.
2. If the change edits a scaffold source, run
   `python3 tools/catalogue/sync_authoring_scaffold.py --write`, then `--check`.
   The script's `--help` lists the source files. A stale copy breaks
   `catalogue init` with `Scaffold integrity error`.
3. Run the local gate: `make lint-ruff lint-mypy`, then
   `python3 -m pytest tests/roster/test_okf_catalogue_discovery.py -q` to check
   the version pin.
4. Run two checks that Gate H, the workflow's pre-release job, repeats only on the
   tag:
   - `python3 -m agentbundle catalogue sync-defaults --root . --check`
   - `diff contracts/catalogue.schema.json packages/agentbundle/agentbundle/_data/catalogue.schema.json`
5. Push and open the PR. `build-check` and `ci-security` always run.
   `release-agentbundle.yml` also runs its `build-and-smoke` job on the PR, because
   the change touches `packages/agentbundle/`.
6. Dispatch the suites the PR does not trigger:
   `gh workflow run test-corpus.yml --ref "$B"` and
   `gh workflow run test-roster.yml --ref "$B"`, where `$B` is the branch name.
   The root [`AGENTS.md`](../../../AGENTS.md) "Build and test commands" lists
   them.
7. Merge to `main` once the owner approves.

### Tag the merge commit

1. Update `main` and find the merge commit:
   `git fetch origin main && git log -1 --format='%H %s' origin/main`.
2. Create an annotated tag on that commit. The message is `agentbundle X.Y.Z`, a
   blank line, then a one-paragraph summary of what adopters get, with breaking
   changes named. To see the format, run
   `git for-each-ref refs/tags/agentbundle-v0.53.0 --format='%(contents)'`.

   ```bash
   git tag -a agentbundle-vX.Y.Z <merge-sha> -F <message-file>
   git push origin agentbundle-vX.Y.Z
   ```

The tag must match `agentbundle-vX.Y.Z` exactly. The workflow refuses
pre-release or build-metadata suffixes.

### Watch the release workflow

Find the run with
`gh run list --workflow release-agentbundle.yml --limit 3`, then follow it with
`gh run view <run-id>` or `gh run watch <run-id>`.

The run has four jobs:

1. `build-and-smoke` checks that the tag matches `pyproject.toml` and
   `CLI_VERSION`, and that the commit is on `origin/main`. It then builds the wheel
   and sdist, checks the artifact test boundaries, runs `twine check`, and
   smoke-installs the wheel with a `credbroker` wheel built from this repository.
2. `Gate H — pre-release gates` runs on Python 3.11 and 3.12. It runs the full
   `packages/agentbundle/tests/` suite, the `sync-defaults` check, an enterprise
   install-defaults smoke, a package-config test, a catalogue archive round trip,
   and the schema-copy check.
3. `publish-artifactory` needs only `build-and-smoke`. It uploads to a private
   index when all three `ARTIFACTORY_*` secrets are set, and skips with a notice
   when they are not.
4. `publish-pypi` needs `build-and-smoke` and both Gate H jobs. It runs in the
   `pypi` GitHub environment, which requires a reviewer. The job shows `waiting`
   until a maintainer approves it under **Review deployments** on the run page.

### Confirm publication

1. `gh run view <run-id>` shows every job as `success`.
2. `python3 -m pip index versions agentbundle --index-url https://pypi.org/simple`
   lists `X.Y.Z`.
3. In a fresh virtual environment, `pip install agentbundle==X.Y.Z` succeeds and
   `agentbundle --version` reports `X.Y.Z`.

### Recover from a failed run

Each failure point has its own recovery, because of the order the jobs run in.

- **`build-and-smoke` failed.** Nothing was published, because both publish jobs
  need this job. A version mismatch or a commit outside `main` means the tag is
  wrong. With the owner's go-ahead, delete it (`git push origin
  :refs/tags/agentbundle-vX.Y.Z` and `git tag -d agentbundle-vX.Y.Z`), fix
  `main` through a PR, and tag the corrected merge commit.
- **A Gate H job failed.** PyPI did not receive the release. `publish-artifactory`
  may already have uploaded `X.Y.Z` to the private index, because it does not wait
  for Gate H. For a transient failure, such as a network error, rerun with
  `gh run rerun <run-id> --failed`. For a real defect, fix it on `main` and
  release the next patch version. Leave the failed tag in place.
- **`publish-pypi` failed after approval.** Read the job log first. If the upload
  never reached PyPI, rerun the failed job. If PyPI already has the files, the
  release is out. A version that reached PyPI cannot be uploaded again, so any
  fix ships as the next patch version.

## Release credbroker

The workflow is
[`.github/workflows/release-credbroker.yml`](../../../.github/workflows/release-credbroker.yml).
It runs on any `credbroker-v*` tag.

### Files that move together

| File | What changes |
| --- | --- |
| `packages/credbroker/credbroker/version.py` | `__version__ = "X.Y.Z"`. `credbroker/__init__.py` re-exports it |
| `packages/credbroker/pyproject.toml` | `[project].version = "X.Y.Z"` |
| `packages/credbroker/CHANGELOG.md` | A new top entry `## [X.Y.Z] — YYYY-MM-DD` in Keep a Changelog form |
| `packages/credbroker/README-pypi.md` and `README.md` | New or changed public behavior. `README-pypi.md` is the PyPI project page. Unlike agentbundle, it has no "What's new" heading |
| `docs/product/changelog.d/<uuid>.md` | A product changelog fragment from `python3 tools/changelog.py new --package credbroker --version X.Y.Z ...` |
| Version pins in tests | Every literal of the old version |

To find the test pins, search for the old version string:
`grep -rn '"<old-version>"' packages/credbroker/tests tests/roster`. At 0.7.0 the
pins are in `packages/credbroker/tests/unit/test_http_access_version.py` and
`tests/roster/test_portable_catalogue_authentication_packaging.py`. The roster
file runs only in the dispatch-only `test-roster.yml`.

### The vendored copy and the credential-brokers pack

The `credbroker` source is copied byte for byte into two committed places:

- `packs/credential-brokers/.apm/user-libs/credbroker/`
- `.agentbundle/lib/credbroker/`

`make build-self` rewrites both copies. `packages/agentbundle/agentbundle/build/user_libs.py`
owns that projection, and `tests/roster/test_credential_broker_source_invariants.py`
fails when either copy differs from the package source.

A source change therefore also changes the `credential-brokers` pack, and three
more things follow:

- The pack's own version moves, under the version bump rule in
  [`packs/AGENTS.md`](../../../packs/AGENTS.md#version-bump-rule):
  `packs/credential-brokers/pack.toml`, `.claude-plugin/plugin.json`, and the
  version assertion in `packs/credential-brokers/tests/pack/test_pack_install.py`.
  [`packs/AGENTS.local.md`](../../../packs/AGENTS.local.md) "Marketplace and
  release pipeline" owns the rest of the pack release.
- Each commit that touches `packs/credential-brokers/` needs an
  `Engine-Change-RFC:` trailer. That tree has no exemptions in
  `tools/lint-catalogue-curation-guard.py`.
- `tests/roster/test_portable_catalogue_authentication_packaging.py` reads the
  previous minor release from its git tag, for example `credbroker-v0.6.0`.
  Keep old tags in place.

### Steps before merge

1. Run `make lint-ruff lint-mypy`.
2. Run the package suite:
   `PYTHONPATH=packages/agentbundle:packages/credbroker python3 -m pytest packages/credbroker -q`.
3. Push and open the PR. `release-credbroker.yml` runs `build-and-smoke` on the
   PR when the change touches `packages/credbroker/`. `build-check` runs the
   credbroker suite in its `gate-credbroker` job.
4. Dispatch `test-roster.yml` and `test-corpus.yml` against the branch, as for
   agentbundle.
5. Merge to `main` once the owner approves.

### Tag, watch, and confirm

1. Create an annotated tag on the merge commit. Its message is at least
   `credbroker X.Y.Z`. Past tags carry only that line.

   ```bash
   git tag -a credbroker-vX.Y.Z <merge-sha> -m "credbroker X.Y.Z"
   git push origin credbroker-vX.Y.Z
   ```

2. Watch the run with `gh run list --workflow release-credbroker.yml --limit 3`
   and `gh run view <run-id>`. It has three jobs:
   - `build-and-smoke` checks the tag against `pyproject.toml` and that the commit
     is on `origin/main`. It then builds, runs `twine check`, and smoke-imports the
     base wheel. A second smoke adds the `[crypto]` extra from PyPI.
   - `publish-artifactory` needs only `build-and-smoke`. It skips when the
     `ARTIFACTORY_*` secrets are not set.
   - `publish-pypi` needs only `build-and-smoke`. It runs in the same `pypi`
     environment and waits for a reviewer's approval.
3. Confirm publication with
   `python3 -m pip index versions credbroker --index-url https://pypi.org/simple`.
   Then, in a fresh virtual environment, run `pip install credbroker==X.Y.Z` and
   `python -c "import credbroker; print(credbroker.__version__)"`.

Recovery follows the agentbundle rules above. credbroker has no Gate H, so a
`build-and-smoke` failure publishes nothing, and anything after it is fixed
forward with the next patch version.

## When both packages release together

agentbundle depends on credbroker: `packages/agentbundle/pyproject.toml` declares
`credbroker>=0.7,<0.8`.

- A credbroker version outside that range needs an agentbundle release that
  widens the range. Ship both changes in one PR.
- Push the `credbroker-v*` tag first and confirm it reached PyPI. Then push the
  `agentbundle-v*` tag on the same merge commit. Installing the new agentbundle
  from PyPI resolves credbroker from PyPI, so the dependency has to be there
  first. `credbroker-v0.7.0` and `agentbundle-v0.51.0` sit on one commit, and the
  credbroker tag was created first.
- The agentbundle smoke job builds credbroker from the tagged commit, not from
  PyPI. A green agentbundle run therefore does not show that the credbroker
  version it needs is published.

`agentbundle catalogue sync --package credbroker` is an adopter command that
writes into a target repository's `packages/credbroker/`. It is not a release
step in this repository.
