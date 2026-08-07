# Spec: cross-OS `python -m pip` invocation idiom

**Status:** Shipped
**Mode:** light (no risk trigger fired)

## Objective

Every operative editable-install instruction in this repo reads
`pip install -e <path>`. Bare `pip` resolves through whatever shim is first on
`PATH`, which need not belong to the interpreter that will later run
`agentbundle` — the classic "installed it, but the command isn't there" failure.
`python -m pip` binds the installer to the interpreter by construction.

`python`, not `python3`: Windows ships `python` and generally has no `python3`,
and this repo runs Windows CI (`.github/workflows/build-check-windows.yml`).
`python3` would be a cross-OS regression, not a fix.

Switch every **runnable** install command for *this project* — editable local
installs (AC1–AC3) and the front-door PyPI one-liners (AC8) — in
**documentation and CI configuration** from `pip install …` to
`python -m pip install …`. Third-party dependency installs are out of scope.

## Acceptance criteria

- [x] AC1 — Every runnable `pip install -e …` command in `AGENTS.md`,
  `Makefile`, `docs/architecture/catalogue.md`, `docs-site/src/content/docs/`,
  `guides/**`, `packages/credbroker/README.md`, and
  `packages/credbroker/README-pypi.md` reads `python -m pip install -e …`.
- [x] AC2 — Every `pip install -e …` / `pip install <path>` step in
  `.github/workflows/*.yml` reads `python -m pip install …`.
- [x] AC3 — The snapshot-install exception in
  `guides/_shared/how-to/install-agentbundle-from-clone.md` (the non-`-e`
  `pip install ./packages/agentbundle` form) uses the same idiom, so the two
  forms stay directly comparable.
- [x] AC4 — Descriptive prose that *names the mechanism* rather than giving a
  command is left byte-identical. Specifically unchanged:
  `docs/architecture/catalogue.md:50,66`, `guides/_shared/reference/agentbundle.md:155`,
  `packages/agentbundle/README-pypi.md:33,364`,
  `guides/_shared/how-to/install-agentbundle-from-clone.md:59`,
  `.github/workflows/build-check.yml:165`.
  `catalogue.md:66` in particular quotes `source_defaults.py`'s error string and
  must stay byte-identical to it.
- [x] AC5 — `docs/adr/`, `docs/rfc/`, and `docs/specs/` are untouched — frozen
  governance records describe what was decided and run at the time.
- [x] AC6 — **No shipped artifact changes.** No file under
  `packages/*/agentbundle/`, `packages/*/credbroker/`, or `packs/**` is
  modified; no package or pack version is bumped; no changelog entry is added.
  This is a documentation change and must not force a release.
- [x] AC7 — `make build-check` and `make lint-ruff` pass, and `make build-self`
  produces no projection drift.
- [ ] AC8 — Every runnable **front-door** install command — `pip install
  agentbundle` / `pip install credbroker` and their pinned and extra-bearing
  variants — reads `python -m pip install …` across `README.md`,
  `CONTRIBUTING.md`, `web/`, `docs-site/`, `docs/guides/`, `guides/**`, and
  `packages/credbroker/README-pypi.md`, subject to the AC6 and AC9 exclusions.
- [ ] AC9 — `guides/_shared/reference/catalogue-ci-contract.md` is **unchanged**.
  `tools/catalogue/sync_authoring_scaffold.py` holds it byte-identical to a copy
  inside `packages/agentbundle/agentbundle/_data/catalogue-scaffold/`, enforced
  by `test_scaffold_projection.py`, so editing it forces a write into the
  curation-guarded tree. Same reasoning for
  `guides/_shared/reference/catalogue-authoring-standards.md`.

## Boundaries

**Not in scope — runtime hint strings.** Two shipped code paths print an
install command to the user:
`packages/agentbundle/agentbundle/catalogue_tooling/initialise_self_hosted.py`
and `packs/credential-brokers/.apm/skills/credential-setup/scripts/setup.py`.
Both were changed during an earlier pass of this loop and **reverted**: the
first is agentbundle tooling and would want a changelog entry and a release;
the second is a published pack artifact, so it forces a
`credential-brokers` version bump across `pack.toml`, `plugin.json`, and
`marketplace.json` — and that bump fails
`packages/agentbundle/tests/integration/test_credential_brokers_pack_install.py`,
which pins the version. A doc sweep must not cut a release. Handed off to a
separate session; see `handoff-runtime-hint-strings.md` beside this spec.

**Not in scope — `packages/agentbundle/README.md`.** RFC-0059 D6's
`lint-catalogue-curation-guard` path-gate protects **all** of
`packages/agentbundle/**` (carve-outs only for `build/recipes/**` and
`.../tests/...`), so any change there needs an `Engine-Change-RFC:` commit
trailer. This sweep has no RFC behind it, and asserting one to clear a gate
would be a false claim. The file keeps bare `pip install -e` until either an
RFC covers it or the guard grows a docs carve-out — the latter is a change to
an RFC-governed guard and does not belong in a doc PR.

**In scope as of the second pass — the front-door PyPI one-liners** (AC8).
Originally surfaced as an open decision and taken: the same
bind-the-installer-to-the-interpreter argument applies most strongly at the
entry line an adopter copies first, and a half-swept repo reads worse than
either endpoint. `packages/agentbundle/README-pypi.md:12,282` stays bare for
the curation-guard reason above; `catalogue-ci-contract.md` stays bare for the
scaffold reason in AC9.

**Still not in scope — the dependency-install family**
(`pip install -r tools/requirements.txt`, `pip install ruff mypy`,
`pip install docling`, `pip install 'httpx>=0.27'`). Those install *third-party
prerequisites*, not this project, and they span CI setup, SAST tooling, and
optional per-skill runtime deps — a different decision with a different blast
radius. An earlier pass applied the `-r` rewrite to `AGENTS.md` and
`CONTRIBUTING.md`, then reverted it: it left five other sites of the same
command untouched, which is precisely the cross-file drift this sweep exists to
remove.

**No `--upgrade`.** Verified by dry-run against this workspace's venv: `pip
install -e packages/agentbundle` and `pip install --upgrade -e
packages/agentbundle` produce identical resolution plans
(`Would install agentbundle-0.29.6`). Path requirements are always rebuilt and
pip's default upgrade strategy is `only-if-needed`, so the flag adds a token
readers must reason about for zero behaviour change.

## Testing strategy

Goal-based throughout — this is a string substitution across prose and CI
config with no logic to exercise.

- **Done when** (AC1–AC5): an unfiltered `git grep` over the operative surfaces
  returns zero bare `pip install -e` / `pip install <path>` commands, and a
  line-by-line comparison against `HEAD` confirms the AC4 prose lines are
  unchanged.
- **Done when** (AC6): `git diff --name-only` matches no
  `^packs/`, `^packages/[^/]*/(agentbundle|credbroker)/`, or `CHANGELOG.md`.
- **Done when** (AC7): `make build-check` and `make lint-ruff` exit 0;
  `make build-self FORCE=1` adds no files to `git status`. Because
  `lint-catalogue-curation-guard` reads `git diff origin/main...HEAD`
  (committed state), `build-check` runs **after** the commit or it gates an
  empty changeset and passes vacuously.
- **Done when** (AC8): `git grep "pip install \(agentbundle\|credbroker\|'agentbundle\|'credbroker\)"`
  over the in-scope surfaces returns only prose mentions and the AC6/AC9
  exclusions.
- **Done when** (AC9): `pytest packages/agentbundle/tests/integration/test_scaffold_projection.py`
  passes and `git status` shows no `packages/agentbundle/**` entry.

## Assumptions

- GitHub Actions runners with `actions/setup-python` put the selected
  interpreter on `PATH` as `python` on all three OSes, so `python -m pip` is
  correct in workflow `run:` steps without a `shell:` change. The
  `lint-ci-parity` gate corroborates the extracted step targets.
- `docs-site/src/content/docs/getting-started/install.md` is hand-authored, not
  generated — `tools/build-site.py` generates only `packs/`, `guides/`,
  `changelog.md`, and `contributing.md` under `src/content/docs/`, and those are
  gitignored. Editing `guides/**` therefore propagates to the site by itself.
