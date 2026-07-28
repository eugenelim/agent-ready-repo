# packages/agentbundle — insider context (not exported with catalogue init)

## PyPI publishing

Tag from `main` only. Never tag from a feature or research branch — there is no branch guard on the release workflow.

**Workflow:**
1. Bump `version.py` (`CLI_VERSION`), `pyproject.toml` (`version`), and CHANGELOG in the same PR.
2. Merge to `main`.
3. `git tag agentbundle-v<version> <sha> && git push origin agentbundle-v<version>`
4. Confirm `release-agentbundle` / `publish-pypi` goes green.

**Version rule:** next after what's on PyPI — run `pip index versions agentbundle` before choosing.

## Engine-Change-RFC requirement

Every PR touching `packages/agentbundle/**` needs an `Engine-Change-RFC: <RFC-NNNN or ADR-NNNN>` trailer in at least one commit. Use ADR-0056 for general additions. `lint-catalogue-curation-guard` enforces this; missing trailer = build failure.
