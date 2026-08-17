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

**The pin is read, not restated.** The new step greps the `bandit` line out of
`tools/requirements-sast.txt` rather than naming a version. A second copy of
`bandit>=1.9,<2` is a thing that can drift from the canonical one; deriving it
cannot. The pattern is anchored `^bandit([^A-Za-z0-9._-]|$)` so a future
`bandit-extras` line cannot be picked up instead. Same principle `lint-ci-parity.py` applies to its own
reachable-target set ("*derived* from the Makefile, never declared").

The conditional full-SAST install stays exactly as it is. When it runs, pip
finds bandit already satisfied and moves on.

**The step asserts its own success, and runs last.** A provisioning step that
quietly does nothing would leave the required check green with the gate it
enables inert — the exact shape this change exists to remove, reintroduced one
level up. Security review found three routes to that, all since measured:

| Route | Measured | Closed by |
| --- | --- | --- |
| The grep matches nothing → `pip install ""` exits **0 with no output**, and a failing command substitution inside a `run:` block does not fail the step on its own | Confirmed against pip and `bash -e` | `set -euo pipefail` with the substitution in an *assignment*, whose status `set -e` does honour |
| bandit installs but its registry import raises — an API move inside `>=1.9,<2`, a broken plugin entry point — so `id_checker()` returns `None` and `lint-nosec-form` degrades to a caveat and exit 0 | Confirmed by reading `id_checker`'s `except Exception: return None` | A `python -c` assertion reaching for the same API, checking **both** directions: a real id resolves, a nonexistent one does not |
| A later `pip install` replaces a shared transitive dep of bandit, exiting 0 while breaking it | Standard pip resolver behaviour | Moving the step to **last before `Run make build-check`**, so nothing runs in between |

Each is mutation-tested: with no bandit line in the requirements file, with the
registry import broken, and with a `check_id` that resolves everything, the step
body exits non-zero. An unmutated assertion is an unverified one.

## Decision 2 — two grouped steps, not seven, and not one

Seven separate steps would put seven near-identical rows in `STEP_DISPOSITION`
for no gain. One step would merge two unrelated concerns behind a single
disposition, which is the residual `lint-ci-parity` documents and does not need
feeding. Two steps, grouped by what they gate — `pytest guides + catalogue
navigation` and `pytest site build + link rewriting`. **AC1 is the canonical
list of which file goes where; this section does not restate it**, so a
regrouping cannot leave two lists disagreeing.

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

- [x] **AC3 — bandit is present on every build-check run, and the step fails
      when it is not.** A new, unconditional install step is the **last** step
      before `Run make build-check`; it installs the `bandit` line read out of
      `tools/requirements-sast.txt`, and asserts the registry resolved by
      calling the same API `id_checker()` reaches for, in both directions. The
      existing conditional `Install SAST/SCA tools` step is unchanged.

- [x] **AC3a — the fail-closed path is mutation-tested, not asserted.** With
      (i) no `bandit` line in the requirements file, (ii) the registry import
      broken, and (iii) a `check_id` that resolves every id, the step body exits
      non-zero. Run, not reasoned about.

- [x] **AC4 — the unknown-ID check is demonstrably live, and demonstrably was
      not.** `lint-nosec-form.scan_source` is run against a well-formed but
      nonexistent ID both with `id_checker()` and with `None`, and the two
      results differ — one `unknown-id` violation versus none. Measured by
      running it, not read off the docstring.

- [x] **AC4b — the install step itself is pinned, and the pin is verified by
      deletion.** `tools/test_build_gate_chain.py` gains
      `BanditRegistryProvisioningTest`: it parses `build-check.yml`, asserts the
      step exists, carries no `if:`, and is the step immediately before `Run
      make build-check` — then **extracts and executes that step's real body**
      with `pip` stubbed, once against the tree (passes) and twice against
      mutated input (fails). Four mutations of the workflow — delete the step,
      restore its `if:`, insert a step before the gate, drop the registry probe
      — each turn the suite red; the restored control is green. Two further
      mutations cover the probe's own halves: deleting either
      `check_id("B307")` or `check_id("B999")` reddens the suite, so neither
      direction can be dropped unnoticed. Without any of this, deleting the step
      *and its roster row* passes `lint-ci-parity` in both directions and the
      gate is silently inert again.

      The test parses `build-check.yml` with a **stdlib** line-structured scan,
      not PyYAML: this module is pure stdlib per `AGENTS.md`, and it also runs
      in Gate F of `catalogue-tooling-ci-gates.yml`, whose job installs only
      `agentbundle` (which declares no dependencies) — so a `yaml` import would
      fail at collection there. A pin that cannot run in one of the two jobs
      that run it is not a pin. Verified by running the suite with `yaml` made
      unimportable.

- [x] **AC4c — closing the two register entries leaves no dangling pointer.**
      `bandit-nosec-form-lint/spec.md` (AC4b names
      `build-check-installs-bandit-unconditionally`) and
      `guides-readme-outcome-label-drift/spec.md` (names
      `catalogue-site-tests-absent-from-ci`) each carry a `Status`-line
      annotation recording that the anchor was closed and by what. Both are
      Frozen; no body line changes; the carrier is the one `CONVENTIONS.md`
      § *Superseding a frozen document* licenses.

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
| AC3, AC3a | Read the edited workflow; assert the new step has no `if:` and is the last step before `Run make build-check`. Then run the step body verbatim against three mutated inputs and assert each exits non-zero. |
| AC4 | `scan_source(src, path, id_checker())` vs `scan_source(src, path, None)` on a `B`-shaped nonexistent ID. |
| AC4b | `pytest tools/test_build_gate_chain.py -k Bandit`, then the same against four mutated copies of `build-check.yml`; assert red each time and green on restore. |
| AC4c | `parse_status` on both edited files; `git diff --unified=0` showing only `- **Status:**` lines. |
| AC5, AC6 | `python3 tools/lint-ci-parity.py`; exit code and summary line. |
| AC7 | The four gate commands. |
| AC8 | `tomllib.load` on `workspace.toml`; assert neither slug is present. |

No new unit test file. `tools/test-lint-ci-parity.py` already pins the roster
invariants in both directions — a step without a disposition and a disposition
without a step both fail — so the roster edit is covered by an existing gate
rather than a new one.

## Deferred

Four findings from `security-reviewer`, each recorded in `workspace.toml
[backlog].open` with a cold-start-sufficient comment:

| Slug | Why not here |
| --- | --- |
| `lint-nosec-form-require-id-registry` | The tool degrades to an exit-0 caveat when the registry is unreachable. In CI that is now closed on three counts — the step fails if the pin is unresolvable, fails if the registry is unusable, and AC4b's test fails if the step is deleted, made conditional, or displaced. What remains is a **local** `SKIP_SAST=1 make build-check` without bandit. Fixing that in the linter makes bandit a hard prerequisite for every contributor — a real cost, and its own decision. |
| `build-check-yml-no-permissions-block` | Adding `permissions: contents: read` changes the job's token scope. That is a behaviour change, which the bundled-fixes carve-out fails closed on, and it applies to three other workflows too. |
| `sast-requirements-hash-locked` | Needs a generated locked file and a refresh procedure. |
| `sast-requirements-not-audited` | `pip-audit` covers `tools/requirements.txt` and the pack files, not the CI-tooling ones. Confirmed by reading the `Makefile` invocations. A different file set and a different decision (audit vs. Dependabot). |

Two more from `adversarial-reviewer`:

| Slug | Why not here |
| --- | --- |
| `tools-test-runner-boundary` | Closing the **class** means extending `lint-pack-test-boundary.py`'s runner discipline from `packs/**/tests` to `tools/`. Eight `tools/` test files are invoked by nothing at all today — two of them landed in the last two merges — so it is worth doing and is its own change. |
| `site-test-source-substring-assertions` | Re-expressing two suites' substring assertions against parsed structure. Needed, but it is a rewrite of tests this change only *wires up*. |

## Honest scope

The seven tests now gate `main`, and bandit's registry is now present — and
proven present — on every run. Four things this does **not** do:

1. **Gate F's `paths-ignore` still excludes doc surfaces.** A PR touching only
   `docs/**` does not run `test_catalogue_tooling_rewire` or
   `test_catalogue_tooling_docs`. Out of scope, and left in the register.
2. **`lint-nosec-form`'s unknown-ID check gains CI reach, not novelty.** Where
   `make sast` runs, `run-bandit-gate.py` already catches the same shape via
   bandit's stderr. What changes is that a `SKIP_SAST` PR is now covered too.
3. **The recurrence class stays open.** Nothing stops the *next* `tools/` test
   from landing gated by nothing — `lint-ci-parity` only enforces
   workflow-step → local-target, never the reverse, and the reverse discipline
   exists only for `packs/**/tests`. Measured: **eight** `tools/test*.py` files
   are invoked by no `Makefile` target, no workflow, and no tool script, two of
   them arriving in the last four merges (#980, #982). The measurement and its
   method live in the register entry `tools-test-runner-boundary`; this bullet
   points at it rather than restating the list.
4. **This couples every PR to formatting elsewhere.** Two of the seven suites
   assert on raw substrings of `pages.yml`, `web/src/lib/catalogue-navigation.ts`
   and two `.astro` files — including occurrence *counts* of quoted `paths:`
   entries. `build-check.yml` has no `paths:` filter, so a cosmetic requote in
   `pages.yml` now reddens the required check for an unrelated PR. The coupling
   already existed in `make ci`; wiring the suites makes it block merges. Those
   assertions are also the shape
   `docs/knowledge/observations/antipattern/2026-08.jsonl` names — they do not
   detect removal of what they pin. Registered as
   `site-test-source-substring-assertions`.
