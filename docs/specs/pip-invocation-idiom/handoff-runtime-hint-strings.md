# Handoff: `python -m pip` in the two runtime install-hint strings

**Why this is a separate session.** The docs sweep
(`docs/specs/pip-invocation-idiom/spec.md`) deliberately stops at documentation
and CI config. These two changes touch **shipped artifacts** — one wants an
agentbundle changelog entry and rides the next release, the other forces a pack
version bump. Neither belongs in a doc PR.

## Context to paste into the new session

> This repo just landed a documentation sweep switching every runnable
> editable-install command from `pip install -e …` to `python -m pip install -e …`.
> Rationale: bare `pip` resolves through whatever shim is first on `PATH`, which
> need not belong to the interpreter that will later run `agentbundle`.
> `python`, not `python3` — Windows ships no `python3` and this repo has Windows CI.
>
> Two runtime strings that print an install command to the user were left out of
> that PR because they change shipped artifacts. Finish them here.

## Change 1 — agentbundle self-hosted-catalogue hint

**File:** `packages/agentbundle/agentbundle/catalogue_tooling/initialise_self_hosted.py`
(in `_build_next_steps`, the vendored-tooling branch)

```diff
-            "run: pip install -e .agentbundle/tooling/agentbundle/"
+            "run: python -m pip install -e .agentbundle/tooling/agentbundle/"
```

No test asserts this string (verified by grep over both agentbundle test roots —
`packages/agentbundle/tests/` and `packages/agentbundle/agentbundle/build/tests/`).

**Also required:** a `## [Unreleased]` → `### Changed` entry in
`packages/agentbundle/CHANGELOG.md`. Note the file already has an
`## [Unreleased]` heading at line ~91, out of order between `0.29.5` and
`0.29.4` — decide whether to reuse it or add a fresh one at the top, and
consider fixing the misplacement while you are in there.

**Doc counterpart already landed:** `guides/_shared/how-to/create-a-self-hosted-catalogue.md`
now says `python -m pip install -e my-catalogue/.agentbundle/tooling/agentbundle/`.
Until this change ships, the CLI hint and the guide disagree.

## Change 2 — credential-setup missing-credbroker guard

**File:** `packs/credential-brokers/.apm/skills/credential-setup/scripts/setup.py` (~line 63)

```diff
-        "    pip install -e ./packages/credbroker\n\n"
+        "    python -m pip install -e ./packages/credbroker\n\n"
```

**Test anchors** — `packs/credential-brokers/tests/skills/credential-setup/test_setup.py`:

- **Line 186** (positive assertion): update the expected substring to match.
- **Line 218** (negative assertion, `not in proc.stderr`): do **not** just
  prefix this one. The bare substring subsumes the new form, so mechanically
  rewriting it *weakens* the test — it would stop catching a regression to the
  old hint. Re-anchor it on the guard's banner instead, which is idiom-independent:
  ```python
  # Match the guard's banner, not its install command: a negative assertion on
  # the command string silently weakens whenever the install idiom changes.
  assert "credbroker not found." not in proc.stderr
  ```

**Version bump is mandatory** — this is a published pack artifact. Three files
(`make build-self` syncs none of them):

1. `packs/credential-brokers/pack.toml` → `version = "0.2.4"`
2. `packs/credential-brokers/.claude-plugin/plugin.json` → `"version": "0.2.4"`
3. `.claude-plugin/marketplace.json` → the `credential-brokers` entry's `version`

**The bump breaks a pinned test.** `packages/agentbundle/tests/integration/test_credential_brokers_pack_install.py::PackManifestShapeTests::test_pack_name_and_version`
asserts `pack["version"] == "0.2.3"` and carries a running comment of every
prior bump. Update the assertion **and** append the `0.2.4` rationale line to
that comment block, matching the existing style.

**Doc counterparts already landed:** `guides/credential-brokers/how-to/add-a-credentialed-skill.md`
and `packages/credbroker/README.md` / `README-pypi.md` already say
`python -m pip install -e ./packages/credbroker`.

## Verification

```bash
make lint-ruff
python -m pytest packages/agentbundle/tests/integration/test_credential_brokers_pack_install.py -q
PYTHONPATH=packages/credbroker python -m pytest packs/credential-brokers/tests/skills/credential-setup/test_setup.py -q
make build-self FORCE=1 && git status --short   # expect no new drift
make build-check
```

Run the two pytest roots **separately** — collecting
`packages/agentbundle/tests/` and `packs/credential-brokers/tests/` in one
invocation aborts with `INTERNALERROR … SystemExit: 3`, because the pack's
`conftest.py` imports the skill's `setup.py`, whose module-level guard exits 3
when `credbroker` is unresolvable in that context.

## Environment note

The machine's editable installs pointed at a Conductor workspace
(`…/agent-ready-repo/trenton`) that has since been deleted, so `credbroker` no
longer imports and `agentbundle` now resolves to the PyPI wheel in
site-packages. Either re-install from your working clone
(`python -m pip install -e ./packages/credbroker`) or pass
`PYTHONPATH=packages/credbroker`, as the commands above do.

## Also unresolved (not part of this handoff)

The front-door PyPI one-liners (`pip install agentbundle`,
`pip install credbroker`) and the dependency-install family
(`pip install -r tools/requirements.txt`, `pip install ruff mypy`) still use
bare `pip`. Whether they should follow the same idiom is an open decision, not
an oversight.
