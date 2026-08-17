---
title: Close two build-check coverage gaps — seven ungated tests and a missing bandit registry
slug: build-check-coverage-gaps
---

# Spec: build-check closes two coverage gaps

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** none — see § Named deviation
- **Mode:** full (governance surface — it edits `.github/workflows/build-check.yml`,
  the one workflow `tools/lint-ci-parity.py` holds in scope, and changes which
  gates block a merge. A change to what CI proves is a CI-integrity change even
  when every line of it is additive.)
- **Constrained by:**
  [ADR-0017](../../adr/0017-adopt-bandit-pip-audit-semgrep-sast-gate.md)
  (the SAST gate whose tooling install this makes partly unconditional);
  [ADR-0084](../../adr/0084-nosec-reason-delimiter-and-stderr-as-a-gate.md)
  (bandit's stderr as a gate — the mechanism `lint-nosec-form`'s unknown-ID
  check is defence-in-depth for);
  [`local-gate-ci-parity`](../local-gate-ci-parity/spec.md)
  (the `STEP_DISPOSITION` roster every new step must join)
- **Contract:** none (CI wiring; no published interface)
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Named deviation from full mode

The `loop-engine` / `loop-cohort` state machine was not run, and there is no
`plan.md`. The two human approval gates it sequences — **spec-approved** and
**plan-approved** — were **granted up front by the requester**, as a standing
instruction to carry this through to merge. The merge decision itself was
explicitly retained. `adversarial-reviewer` and `security-reviewer` were run.
Same deviation shape as the sibling specs of this batch
(`bandit-nosec-form-lint`, `frozen-spec-supersession`).

## Objective

Two independent holes in `build-check.yml`, bundled because the fix to each is
an edit to that file plus a `tools/lint-ci-parity.py` disposition, and because
reviewing one CI-coverage change is cheaper than reviewing two.

**Gap 1 — seven tests gate nothing remotely.** `make test` runs thirteen
`tools/test_*.py` files on one line of the `Makefile`. Seven of them are a
`run:` step in **no** workflow under `.github/workflows/`. They gate `make ci`
on a contributor's machine and nothing on the way to `main`.

This is not hypothetical. It is exactly how #958 merged green while leaving
`main` red on `test_catalogue_navigation` — a failure PR #967 then had to record
as a known skip, and a later spec had to fix.

**Gap 2 — `lint-nosec-form`'s unknown-ID check is inert where it matters.**
`build-check.yml` installs `tools/requirements-sast.txt` only when
`skip_sast != 'true'`. `tools/lint-nosec-form.py` runs in `make build-check`
unconditionally, but its unknown-ID check needs bandit's test registry, so on a
`SKIP_SAST` PR it silently no-ops. Where bandit *is* installed, `make sast` runs
too and `run-bandit-gate.py` already fails on bandit's own stderr for the same
shape — so the check's CI reach today is nil, on exactly the PRs it was written
for. `bandit-nosec-form-lint` AC4b states this and defers the fix here.

## Decision 1 — install bandit unconditionally, the rest of the SAST tools conditionally

The register entry offered two shapes: drop the `if:` on the existing install
step, or add an unconditional bandit-only install. The second wins on cost.
`tools/requirements-sast.txt` pins three tools; `semgrep` and `pip-audit` are
the expensive half of that install and neither is needed by any gate that runs
under `SKIP_SAST`. Bandit alone is what `lint-nosec-form` needs.

**The pin is read, not restated.** The new step installs
`$(grep -E '^bandit' tools/requirements-sast.txt)` rather than naming a version.
A second copy of `bandit>=1.9,<2` is a thing that can drift from the canonical
one; deriving it cannot. Same principle `lint-ci-parity.py` applies to its own
reachable-target set ("*derived* from the Makefile, never declared").

The conditional full-SAST install stays exactly as it is. When it runs, pip
finds bandit already satisfied and moves on.

## Decision 2 — two grouped steps, not seven, and not one

Seven separate steps would put seven near-identical rows in `STEP_DISPOSITION`
for no gain. One step would merge two unrelated concerns behind a single
disposition, which is the residual `lint-ci-parity` documents and does not need
feeding. Two steps, grouped by what they gate:

- **guides and catalogue navigation** — `test_validate_guides`,
  `test_check_guide_index`, `test_catalogue_navigation`,
  `test_documentation_entry_links`
- **site build and link rewriting** — `test_build_site_link_rewrites`,
  `test_check_rendered_site_links`, `test_build_site_routing`

This follows the existing `pytest guides sidebar generation` step, which already
groups three related `tools/test_build_site_*.py` files under one disposition.

## Decision 3 — the count is seven, and it is counted per file across every workflow

Stated because getting it wrong is the easy path, and two specific shapes make
it easy:

1. `test_check_rendered_site_links.py` appears in `pages.yml` twice — as a
   `paths:` trigger, never as a `run:` step. A grep for the filename finds it
   and reports it covered.
2. `test_catalogue_tooling_rewire.py` and `test_catalogue_tooling_docs.py`
   **are** run, by Gate F of `catalogue-tooling-ci-gates.yml`. They are
   therefore **not** in the seven. Wiring them here would duplicate Gate F.

Neither is fixed here. Gate F's own `paths-ignore` covers `docs/**`,
`guides/**`, `docs-site/**` and `web/**`, so it does not gate doc-surface PRs
either — but that is Gate F's gap to close, in `catalogue-tooling-ci-gates.yml`,
not something to paper over by adding a second runner in `build-check.yml`.

## Acceptance Criteria

- [x] **AC1 — the seven run in CI.** `build-check.yml` gains two `run:` steps
      that between them invoke exactly
      `tools/test_validate_guides.py`, `tools/test_check_guide_index.py`,
      `tools/test_catalogue_navigation.py`,
      `tools/test_documentation_entry_links.py`,
      `tools/test_build_site_link_rewrites.py`,
      `tools/test_check_rendered_site_links.py`, and
      `tools/test_build_site_routing.py`.

- [x] **AC2 — the count is verified by construction, not by grep.** A scan that
      parses every `.github/workflows/*.yml`, walks it for `run:` scalars, and
      tests each of the thirteen `Makefile` filenames against them reports
      exactly these seven as absent from every workflow — before the change.
      After it, zero. `test_check_rendered_site_links.py`'s `pages.yml`
      appearance is classified non-`run:` by that scan, not by reading the YAML.

- [x] **AC3 — bandit is present on every build-check run.** A new,
      unconditional install step precedes `Run make build-check` and installs
      the `bandit` line read out of `tools/requirements-sast.txt`. The existing
      conditional `Install SAST/SCA tools` step is unchanged.

- [x] **AC4 — the unknown-ID check is demonstrably live, and demonstrably was
      not.** `lint-nosec-form.scan_source` is run against a well-formed but
      nonexistent ID both with `id_checker()` and with `None`, and the two
      results differ — one `unknown-id` violation versus none. Measured by
      running it, not read off the docstring.

- [x] **AC5 — every new step carries a disposition.** `STEP_DISPOSITION` in
      `tools/lint-ci-parity.py` gains one entry per new step: `LOCAL("test")`
      for the two pytest steps (the `Makefile`'s `test` target runs all seven
      and is reachable from `make ci`), `CI_ONLY(...)` for the install step,
      with a reason that names *why* it is unconditional rather than saying
      "Provisioning."

- [x] **AC6 — the parity gate agrees.** `python3 tools/lint-ci-parity.py` exits
      0 and its summary count rises by three steps.

- [x] **AC7 — gates pass.** `python3 tools/lint-ruff.py`, `make lint-mypy`,
      `SKIP_SAST=1 make build-check`, `make sast`, and
      `lint-spec-status.py --root . --base-ref origin/main` all exit 0.

- [x] **AC8 — both register entries are closed.**
      `catalogue-site-tests-absent-from-ci` and
      `build-check-installs-bandit-unconditionally` are removed from
      `workspace.toml [backlog].open`, verified with `tomllib` rather than by
      reading the diff.

## Boundaries

### Always do

- Always count CI coverage per file across every workflow in
  `.github/workflows/`, and only against `run:` scalars.
- Always give a new `build-check.yml` step a `STEP_DISPOSITION` entry in the
  same commit; the gate fails closed if you do not, and that is the point.

### Ask first

- Ask before pulling `catalogue-tooling-ci-gates.yml` Gate F's `paths-ignore`
  gap into this change. It is a real gap and a different workflow's.

### Never do

- Never restate the `bandit` version pin. Read it from
  `tools/requirements-sast.txt`.
- Never widen the unconditional install to the whole of
  `requirements-sast.txt`; `semgrep` and `pip-audit` are the cost this decision
  exists to avoid paying on every PR.
- Never spell a bandit suppression directive out inside a Python comment, in
  this change or any other. A comment quoting the form **is** the form —
  `bandit.yaml` says so and `lint-nosec-form.py` enforces it. Describe it, or
  point at `bandit.yaml`.

## Testing Strategy

Goal-based, plus one measured before/after.

| What | How |
| --- | --- |
| AC1, AC2 | The workflow scan described in AC2, run on the base and on the change. |
| AC3 | Read the edited workflow; assert the new step has no `if:` and precedes `Run make build-check`. |
| AC4 | `scan_source(src, path, id_checker())` vs `scan_source(src, path, None)` on a `B`-shaped nonexistent ID. |
| AC5, AC6 | `python3 tools/lint-ci-parity.py`; exit code and summary line. |
| AC7 | The four gate commands. |
| AC8 | `tomllib.load` on `workspace.toml`; assert neither slug is present. |

No new unit test file. `tools/test-lint-ci-parity.py` already pins the roster
invariants in both directions — a step without a disposition and a disposition
without a step both fail — so the roster edit is covered by an existing gate
rather than a new one.

## Honest scope

The seven tests now gate `main`, and bandit's registry is now present on every
run. Two things this does **not** do:

1. **Gate F's `paths-ignore` still excludes doc surfaces.** A PR touching only
   `docs/**` does not run `test_catalogue_tooling_rewire` or
   `test_catalogue_tooling_docs`. Out of scope, and left in the register.
2. **`lint-nosec-form`'s unknown-ID check gains CI reach, not novelty.** Where
   `make sast` runs, `run-bandit-gate.py` already catches the same shape via
   bandit's stderr. What changes is that a `SKIP_SAST` PR is now covered too.
