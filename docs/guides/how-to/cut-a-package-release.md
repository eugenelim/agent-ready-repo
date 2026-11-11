# Release agentbundle and credbroker

This internal maintainer page covers when a change needs a new `agentbundle` or
`credbroker` release, and how to publish one to PyPI. It is not adopter
documentation: `docs/guides/` is not mirrored into the published docs site.

Pushing a tag on `main` starts the release workflow, and the workflow builds and
publishes the package. Your job is to decide whether a release is due, make the
version files agree before the merge, push the right tag, and approve and watch
the run.

## Does this change need a release?

The version bump rule in [`packages/AGENTS.md`](../../../packages/AGENTS.md)
applies to both packages: a non-cosmetic package change updates both
`version.py` and `pyproject.toml`. The rest of this section is about when that
bump must also be published.

agentbundle's public surface is what adopters call: the `agentbundle catalogue *`
command group and the `catalogue.toml` and `pack.toml` schemas. A change to that
surface needs a release. A change that stays inside repository tooling, or that
keeps observable CLI behaviour, does not.

### Changes that need an agentbundle release

| Change | Why |
| --- | --- |
| Adding a new `agentbundle catalogue <sub>` command | Adopters need to call it; it can't exist until released |
| Removing or renaming a `catalogue` sub-command | Callers break |
| Changing required CLI flags or flag semantics | Callers break |
| Changing the output layout of `dist/` or archive file names | Downstream tools expect a fixed layout |
| Changing `catalogue.toml` or `pack.toml` schema in a way that invalidates previously valid files | Adopter catalogues fail validation |
| Adding a required field to either schema | Existing catalogues fail until updated |

### Changes that do not need a release

| Change | Why |
| --- | --- |
| Refactoring internal helpers that preserve observable CLI behaviour | Callers see no difference |
| Adding optional CLI flags with backward-compatible defaults | Callers not using the flag are unaffected |
| Updating `docs/guides/` or `tools/` without touching the package | No installed code changes |
| Improving error messages without changing exit codes | Observable behaviour is exit code plus stdout schema |
| Adding or changing tests | Never reaches the installed surface |
| Updating Makefile targets that delegate to existing commands | Repository governance, not a public interface |

### Where new behaviour belongs

- `packages/agentbundle/agentbundle/` holds portable mechanics. It is installed in
  every adopter's environment, so changes there are release-gated.
- `tools/` holds repository-only policy. It runs only in this checkout and needs no
  release.

Put a purely repository-governance capability, such as a new lint or gate, in
`tools/`. Put something every catalogue author needs in their own CI in
`packages/agentbundle/`, and plan a release.

Where you can, drive variation through `catalogue.toml` configuration rather than
new CLI flags or sub-commands. An optional, backward-compatible config field needs
no release, and adopters can adjust it without updating their tooling.

## Rules for both packages

- Both release workflows refuse a tag whose commit is not on `origin/main`, so
  every tag goes on a merge commit on `main`.
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
changelog release all name the same version. It runs on every PR through the
`build-check` `gate-main` job, whose `python -m pytest tests/ -q` step collects
every roster module, so a forgotten pin turns the PR red.

Create the fragment with the command that
[`docs/product/AGENTS.md`](../../product/AGENTS.md) describes, then edit the file
it writes:

```bash
python3 tools/changelog.py new --package agentbundle --version X.Y.Z \
  --date YYYY-MM-DD --highlight "Describe the released outcome."
```

### Steps before merge

1. Add an `Engine-Change-RFC:` trailer to a commit in the PR. Name the RFC that
   governs the change, or write `n/a — <reason>` when none does.
   `tools/lint-catalogue-curation-guard.py` enforces this in `build-check.yml` for
   any PR that touches `packages/agentbundle/`, except
   `packages/agentbundle/agentbundle/build/recipes/` and `tests/` paths. One
   trailer anywhere in the commit range satisfies it. Locally, run
   `python3 tools/lint-catalogue-curation-guard.py --root . --base origin/main`.
   It fails when the base ref is missing.
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
6. Dispatch the two suites that have no PR trigger:
   `gh workflow run test-corpus.yml --ref "$B"` and
   `gh workflow run test-roster.yml --ref "$B"`, where `$B` is the branch name.
   `test-corpus.yml` runs `make test`. The root [`AGENTS.md`](../../../AGENTS.md)
   "Build and test commands" lists both as partial evidence, not required checks.
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
   index when all three `ARTIFACTORY_*` secrets are set. It skips with a notice
   when none are set, and skips with a warning when only some are set.
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
`tests/roster/test_portable_catalogue_authentication_packaging.py`. `build-check`
runs the roster file on every PR as its own step.

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
- A PR that touches `packs/credential-brokers/` needs an `Engine-Change-RFC:`
  trailer on one of its commits. `tools/lint-catalogue-curation-guard.py` exempts
  no path in that tree.
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
   `credbroker X.Y.Z`. The `credbroker-v0.6.0` and `credbroker-v0.7.0` tags
   carry only that line.

   ```bash
   git tag -a credbroker-vX.Y.Z <merge-sha> -m "credbroker X.Y.Z"
   git push origin credbroker-vX.Y.Z
   ```

2. Watch the run with `gh run list --workflow release-credbroker.yml --limit 3`
   and `gh run view <run-id>`. It has three jobs:
   - `build-and-smoke` checks the tag against `pyproject.toml` and that the commit
     is on `origin/main`. It then builds, runs `twine check`, and smoke-imports the
     base wheel. A second smoke adds the `[crypto]` extra from PyPI.
   - `publish-artifactory` needs only `build-and-smoke`. It skips with a notice
     when no `ARTIFACTORY_*` secret is set, and with a warning when only some are.
   - `publish-pypi` needs only `build-and-smoke`. It runs in the same `pypi`
     environment and waits for a reviewer's approval.
3. Confirm publication with
   `python3 -m pip index versions credbroker --index-url https://pypi.org/simple`.
   Then, in a fresh virtual environment, run `pip install credbroker==X.Y.Z` and
   `python -c "import credbroker; print(credbroker.__version__)"`.

Recovery follows the agentbundle rules above, without the Gate H case:

- A `build-and-smoke` failure publishes nothing. Fix the tag the same way.
- A failed publish job that never reached its index can be rerun with
  `gh run rerun <run-id> --failed`.
- Once `X.Y.Z` reached PyPI or the private index, any fix ships as the next patch
  version.

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

## Cut the next catalogue specification version

The catalogue specification has its own version, `MAJOR.MINOR`, such as `0.1`. It
is separate from the `agentbundle` version. Each release is frozen: its members
keep one `$id` for good, and the site serves it at a fixed URL. This section
covers cutting the next one, `N.M` below.

### Files that move together

| File or path | What changes |
| --- | --- |
| `contracts/*.json` and the `_data/` copies | `python3 tools/catalogue/rewrite_member_ids.py --version N.M` moves every member `$id` to `N.M` |
| `contracts/releases/catalogue/N.M/` | The new snapshot: a byte copy of every member file and every page source, such as `overview.md` |
| `contracts/catalogue-spec.toml` | A new `[[release]]` row |
| `packages/agentbundle/` version files | The version bump, because the `_data/` copies changed. Follow "Release agentbundle" above |

Never edit a file under an older `contracts/releases/catalogue/<MAJOR.MINOR>/`
directory to cut a new version. A released member file is never corrected. A new
version supersedes it.

### Steps before merge

1. Edit the member files and page sources for the new version.
2. Run `python3 tools/catalogue/rewrite_member_ids.py --version N.M`. It changes
   only the `$id` value, adds a missing `$id` or `$schema` line, and changes
   nothing on a second run.
3. Copy the members and page sources into
   `contracts/releases/catalogue/N.M/`. Keep the file names the same.
4. Compute a SHA-256 for each copied file, for example
   `shasum -a 256 contracts/releases/catalogue/N.M/*`.
5. Add the release row to `contracts/catalogue-spec.toml`. It has these fields:
   - `version`: `"N.M"`, in `MAJOR.MINOR` form.
   - `date`: the date you author the row.
   - `adapter_contract`: the version in `contracts/adapter.toml`.
   - `[release.members]`: one digest per member file, keyed by its path inside
     the snapshot.
   - `[release.pages]`: one digest per page source, keyed the same way.

   The two tables are keyed separately. A path may appear in only one of them.
   The loader rejects a row that breaks this, and rejects a duplicate version.
6. Run `python3 tools/catalogue/sync_contract_inventory.py --write`, then
   `python3 tools/catalogue/check_contract_parity.py`.
7. Run `python3 tools/catalogue/check_spec_version.py`. It fails when a member
   `$id` and the releases disagree, and its message names the rewrite command.
8. Run `python3 tools/catalogue/check_release_immutability.py`. It fails when a
   released row, snapshot path or member digest from the base branch changed.
9. Open the PR with an `Engine-Change-RFC:` trailer, as in "Release agentbundle".

### Merge, let Pages deploy, then tag

Keep this order.

1. Merge to `main`.
2. Wait for the Pages deploy to finish. The deployed
   `/docs/spec/catalogue/index.json` must list `N.M`.
3. Push the `agentbundle-v*` tag, as in "Tag the merge commit".

Check 4 (`tools/catalogue/check_release_gate.py`) runs in the tag-push run. It
fetches the deployed index and fails when `N.M` is not there with the same member
digests as the bundled bytes. A tag pushed before the deploy finishes therefore
fails check 4. That is the intended safe failure: the CLI must not ship a version
the site does not serve yet. Do not work around it. Wait for the deploy, then
rerun the failed job with `gh run rerun <run-id> --failed`.

### Correct a released page

A correction row is the only sanctioned way to change a released page source,
such as a typo in `overview.md`. It never touches a member file.

1. Edit the page source under `contracts/releases/catalogue/<MAJOR.MINOR>/`.
2. Compute its new SHA-256.
3. Append a `[[correction]]` row to `contracts/catalogue-spec.toml`:

   ```toml
   [[correction]]
   version = "0.1"
   date = "YYYY-MM-DD"
   note = "Fix a typo in overview.md."
   supersedes = "0.1"

   [correction.pages]
   "overview.md" = "<new sha-256>"
   ```

   - `version` names an existing release row.
   - `date` must differ from every other correction date for that version.
   - `note` says what changed.
   - `pages` holds new digests for page sources the release row already lists.
     It has no `members` table. The loader rejects a correction row that has one.
   - `supersedes` names what this row replaces. For the first correction of a
     version, write the version string, such as `"0.1"`. For a later one, write
     the `date` of the correction it replaces.

The governing row for a version is the head of its `supersedes` chain: the
correction that no other correction supersedes. Row order in the file does not
matter. The chain must start at the release, have no repeated link, and have no
link that points at nothing. The loader rejects a chain that breaks these rules.

Check 3 accepts a page-source edit only when the path is a key of that release's
`pages` table and the governing correction row carries the new bytes' digest.
Run `python3 tools/catalogue/check_release_immutability.py` before you push.
