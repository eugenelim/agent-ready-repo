# packages/credbroker — insider context (not exported with catalogue init)

## PyPI publishing

**Publish only from `main`.** Never push a `credbroker-v*` tag from a feature
branch, research branch, or worktree. Tags pushed from non-`main` refs trigger
the release workflow and will publish to PyPI — there is no branch guard.

**After every merge to `main` that bumps the version, tag and push immediately.**
A merged version bump that isn't tagged leaves PyPI stale. The release workflow
runs on tag push only (`push: tags: credbroker-v*`); it does not run on merge.

**Workflow:**
1. Bump `pyproject.toml` `version` and CHANGELOG in the same PR.
2. Merge to `main`.
3. Tag the merge commit: `git tag credbroker-v<version> <sha> && git push origin credbroker-v<version>`.
4. Confirm the `release-credbroker` workflow's `publish-pypi` job completes green.

**Version rule:** the next version after what is currently on PyPI. Check
`pip index versions credbroker` before choosing a version number.

**Name-registration note:** the first real publish to PyPI claims the `credbroker`
package name. This is the maintainer's call (see the RFC that governs this decision).
