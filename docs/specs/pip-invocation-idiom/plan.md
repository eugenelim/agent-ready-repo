# Plan: cross-OS `python -m pip` invocation idiom

**Status:** Done

## Assumption trio

**Files touched** (20 files, docs + CI config only):

| Group | Files |
|---|---|
| Repo context | `AGENTS.md`, `Makefile` (requirement comment) |
| Architecture doc | `docs/architecture/catalogue.md` |
| Site (hand-authored) | `docs-site/src/content/docs/getting-started/install.md` |
| Guides | `guides/_shared/explanation/install-routes.md`, `guides/_shared/how-to/install-agentbundle-from-clone.md`, `guides/_shared/how-to/create-a-self-hosted-catalogue.md`, `guides/_shared/how-to/build-an-org-stack-pack.md`, `guides/credential-brokers/how-to/add-a-credentialed-skill.md` |
| Package READMEs | `packages/credbroker/README.md`, `packages/credbroker/README-pypi.md` |
| CI workflows | `build-check.yml`, `build-check-windows.yml`, `catalogue-tooling-ci-gates.yml`, `docs.yml`, `pack-evals.yml`, `publish-catalogue.yml`, `publish-claude-plugins.yml`, `release-agentbundle.yml` |

**What demonstrates done:** `make build-check` and `make lint-ruff` exit 0; the
sweep grep returns only the AC4 prose lines; `git diff --name-only` touches no
shipped artifact.

**What is not changing:** `docs/adr/`, `docs/rfc/`, `docs/specs/` (frozen
records); the AC4 descriptive-prose lines; every shipped artifact under
`packs/**` and `packages/*/{agentbundle,credbroker}/`; the front-door
`pip install agentbundle` one-liners; the `pip install -r` /
`pip install <package>` dependency family.

## Declined patterns

- **A lint rule forbidding bare `pip install` in tracked files.** Tempting —
  it would keep the idiom from regressing. Declined: one caller, no second
  need. A permanent gate to defend a one-time substitution is scaffolding.
- **Normalising the descriptive prose mentions** (`an editable clone
  (\`pip install -e\`) defaults to itself`). Declined: those name the
  mechanism, not a command to run, and `catalogue.md:66` must stay
  byte-identical to `source_defaults.py`'s error string.
- **Backfilling the historical `pip install -e` lines in `docs/specs/*/plan.md`
  and the ADR/RFC set.** Declined: those record what was decided and run at the
  time. Rewriting them would make the record lie.
- **Adding `--upgrade` while touching every line anyway.** Declined on
  evidence — dry-run shows identical resolution plans.
- **Sweeping the `-r tools/requirements.txt` family.** Applied mid-loop to
  `AGENTS.md` and `CONTRIBUTING.md`, then **reverted**: it left five other
  sites of the same command untouched, which is the cross-file drift the sweep
  exists to remove. Either all of them or none; scoped out as none.
- **Widening to the front-door `pip install agentbundle` one-liners.**
  Declined: a decision about the public entry line, not about editable local
  development. Surfaced to the user rather than folded in.

## Resolve-vs-surface disposition record

| Item | Disposition | Note |
|---|---|---|
| Which `python` spelling | resolved | `python` — `python3` is absent on Windows and this repo has Windows CI. |
| Whether `--upgrade` belongs | resolved | No — verified by `pip install --dry-run` comparison; plans identical. |
| Is `docs-site/.../install.md` generated | resolved | Hand-authored; `tools/build-site.py` generates only `packs/`, `guides/`, `changelog.md`, `contributing.md` (all gitignored). |
| Is root `AGENTS.md` projected from `packs/core/seeds/AGENTS.md` | resolved | No — the seed carries no `pip install` block. |
| The two runtime hint strings | **surfaced → descoped** | Shipped artifacts; one wants a changelog + release, the other forces a pack version bump that breaks a pinned test. Handed off in `handoff-runtime-hint-strings.md`. |
| `-r` / front-door `pip install` families | **surface** | Open decision; named in the PR, not silently deferred. |

## Tasks

### T1 — Docs, guides, READMEs, `AGENTS.md`, `Makefile` — **done**

Substituted the runnable commands only, including AC3's snapshot-install form.

**Verified:** the sweep grep returns only AC4 prose lines; a line-by-line
comparison against `HEAD` confirms all eight AC4 lines byte-identical.

### T2 — CI workflows — **done**

16 `run:` steps across eight workflow files. The `build-check.yml:165`
explanatory comment left alone.

**Verified:** `lint-ci-parity` passes — 50 steps across the in-scope workflow
dispositioned, 73 extracted targets corroborated.

### T3 — Runtime hint strings + version bump — **descoped**

Implemented, then reverted on instruction: a doc update must not cut a release.
`packages/agentbundle/tests/integration/test_credential_brokers_pack_install.py`
pins `credential-brokers` at `0.2.3`, so the pack bump turned the suite red —
concrete evidence that the change is release-shaped, not doc-shaped.
Handed off to a separate session.

### T4 — Gates — **done**

## Anchor-test sweep

`packs/credential-brokers/tests/skills/credential-setup/test_setup.py:186,218`
and `packages/agentbundle/tests/integration/test_credential_brokers_pack_install.py:67`
pin strings and versions this change originally touched. All three are now out
of scope and reverted; they are the reason T3 was descoped, and they are
documented in the handoff.

## Late finding — the curation guard only sees committed changes

`make build-check` passed locally and then failed on CI. The failing leg,
`lint-catalogue-curation-guard`, reads `git diff --name-only origin/main...HEAD`
— **committed** state. Running it against an uncommitted working tree gates an
empty changeset and passes vacuously. Any local build-check run intended to
predict CI must happen *after* the commit.

It flagged `packages/agentbundle/README.md`: RFC-0059 D6 protects the whole
`packages/agentbundle/**` tree behind an `Engine-Change-RFC:` trailer. The file
was dropped from the changeset rather than clearing the gate with a trailer
that would assert an RFC this change does not have.

## Risks

- **A workflow `run:` step on Windows uses a shell where `python` is not the
  setup-python interpreter.** `build-check-windows.yml` is itself in the diff,
  so CI proves it on the platform that matters. `lint-ci-parity` corroborates
  the extracted step targets locally.
- **Local gates ran against a broken editable install.** The machine's
  editable installs pointed at a deleted Conductor workspace (`…/trenton`)
  mid-session, so `credbroker` stopped importing. Worked around with
  `PYTHONPATH=packages/credbroker` rather than mutating the environment; noted
  in the handoff. Does not affect this diff, which contains no Python.
