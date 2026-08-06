# Plan: pack-test-boundary

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Two workstreams in one PR because the second is caused by the first: shipping
the knowledge gate required putting a test in the pack, which is what exposed
that the pack had no test boundary. Splitting them would land a linter whose
test had nowhere correct to live.

Workstream A is prose plus one file move. Workstream B is a mechanical
relocation with a wide consumer sweep — the risk is entirely in the sweep, not
in any single edit, so verification is "every moved suite runs from its new
home" plus a positive check on the projected tree.

## Constraints

- `.apm/` is the runtime export boundary. Nothing that isn't installable goes
  there, regardless of what the current installer happens to ignore.
- Shipped content cannot reference `tools/lint-*`, `make build-self`,
  `docs/specs/`, or `.github/workflows/` — those paths do not exist in an
  adopter's tree (`packs/AGENTS.local.md`).
- `catalogue verify`'s `K-00\d\d` leak guard rejects concrete knowledge IDs in
  a shipped skill body; the documented placeholder is `K-NNNN`.
- `packs/AGENTS.md` has a hard 150-line CI cap.
- Moved tests must not silently stop running. Every relocation pairs with its
  CI wiring in the same commit.

## Tasks

### T1 — Inline the schema and the verification rule

**Depends on:** none

**Tests:** goal-based. `grep` each surface for the six keys and the unfiltered-run
instruction; `test-lint-knowledge.py` guidance layer enforces it mechanically
from T3 onward.

**Approach:** Derive the required-key set from the linter (`REQUIRED_KEYS`), not
from the README, and confirm the README agrees. State the keys plus a one-line
example in the skill's Capture-learnings step; add the unfiltered-run rule to
the skill and both READMEs; add the general anti-pattern.

**Done when:** all six keys and an example appear inline at the point of
writing; the two READMEs' Verify sections are byte-identical.

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`,
`docs/knowledge/README.md`, `packs/core/seeds/docs/knowledge/README.md`.

### T2 — Ship the linter and gate it automatically

**Depends on:** T1

**Tests:** goal-based, then integration. `tools/test-pre-pr.sh`'s
`knowledge-fail` case must trip from the *shipped* hook rather than the
catalogue hook; a new pytest case drives a malformed entry end-to-end.

**Approach:** Move `tools/lint-knowledge.py` into the pack beside
`loop-cohort.py`. Generalise `_find_loop_cohort()` to
`_find_work_loop_script(name)` and add a knowledge-lint step to the shipped
`pre-pr.py`, guarded on the file existing. Drop the step from the repo-native
catalogue gate, which inherits it by delegation. Add the Windows cp1252 guard
the other shipped work-loop scripts carry.

**Done when:** `pre-pr.py` prints `✓ knowledge lint` on a clean tree and
`✖ knowledge lint failed` on an entry missing `source`.

**Touches:** `packs/core/.apm/skills/work-loop/scripts/lint-knowledge.py`
(moved), `packs/core/.apm/hooks/pre-pr.py`, `tools/catalogue/pre_pr_catalogue.py`.

### T3 — Port the self-test and add the guidance-drift layer

**Depends on:** T2

**Tests:** TDD. Write the drift layer, confirm it fails when a surface omits
`source` from its key list and when an example loses `source`, then confirm it
passes once restored.

**Approach:** Port `tools/test-lint-knowledge.sh` to Python beside the script it
tests. Match the required-key list on the **sentence** and its bolded key run,
not the line — prose wraps, and a line-scoped scan sees half the list. Discover
surfaces by `os.walk(followlinks=False)` rather than enumerating them (and not
`Path.glob("**/…")`, whose symlink behaviour changed in 3.13); exclude
`fixtures`/`tests` trees, which are frozen snapshots. Assert the surface count
so a discovery bug fails rather than quietly checking less.

**Done when:** 28 cases pass and both falsifications fail red.

**Touches:** `packs/core/tests/skills/work-loop/test-lint-knowledge.py` (new),
`tools/test-lint-knowledge.sh` (deleted).

### T4 — Relocate every core-pack test out of `.apm/`

**Depends on:** T2

**Tests:** each moved suite is its own oracle — all must pass from the new home.

**Approach:** `git mv` the Python suites and bash runners to
`packs/core/tests/{skills/<skill>,hooks,pack}/`. Repoint each at the pack source
via a shared `parents[N] / ".apm" / ...` anchor rather than sibling resolution.
Sweep `packages/agentbundle/tests/` in the same pass and move out every suite
whose *subject* is pack content — a core-pack helper rename had already broken
the package's suite once during this change. Classify by subject, not by
mention: a test that drives `install`/`upgrade`/projection using core as fixture
data is an engine test and stays.

Do not create a repository-root `tests/` tree for the one cross-cutting case
(`test_reference_architecture.py`) — a new top-level directory is RFC-gated
here, and on inspection every pack subject in that file is core's
`adapt-to-project`, so it is core-owned anyway.

**Done when:** every relocated suite runs green from its new location;
`find packs/core/.apm -name 'test*'` is empty; and no suite left in
`packages/agentbundle/tests/` takes pack content as its subject.

**Touches:** `packs/core/tests/**` (new), `packs/core/.apm/skills/*/scripts/test-*.py`
(moved), `packages/agentbundle/tests/hooks/` (moved).

### T5 — Sweep consumers and stale projections

**Depends on:** T4

**Tests:** goal-based — `grep` for every old path across operative code; run the
full gate set.

**Approach:** Update `docs.yml` (path triggers and run commands),
`catalogue-tooling-ci-gates.yml` (add an explicit Linux step — Gate A's
`working-directory` is the package, so the relocated suites would otherwise run
on Windows only), `Makefile`, `tools/test-all.py`,
`tools/repo/build_gate_chain.py`, `tools/test_build_gate_chain.py`,
`self_host_windows.py`, `tools/hooks/README.md`. Delete the now-stale
`.claude/`/`.agents/` projections of the moved tests.

**Done when:** no operative reference to an old path survives; the projected
tree carries no test file.

### T5a — Release the `agentbundle` change

**Depends on:** T5

**Tests:** goal-based — `test_cli_version_matches_pyproject` passes; the full
package suite is green after the removals.

**Approach:** Removing suites changes the package, so it takes a release:
bump `pyproject.toml` **and** the hardcoded `CLI_VERSION` in `version.py` (they
drift independently), add a `CHANGELOG.md` entry, and update `README-pypi.md`
— the pack-layout diagram there is what adopters read on PyPI and it predates
`tests/` entirely.

**Done when:** 0.29.3 → 0.29.4 in both places, changelog entry present, the
PyPI README documents the three boundaries.

**Touches:** `packages/agentbundle/{pyproject.toml,CHANGELOG.md,README-pypi.md}`,
`packages/agentbundle/agentbundle/version.py`.

### T6 — Encode the policy

**Depends on:** T4

**Tests:** goal-based — the shipped guide renders in the doc-site index;
`lint-agents-md.py` stays green.

**Approach:** Normative rules into `guides/_shared/reference/catalogue-authoring-standards.md`
§ 4, the one copy that travels with a catalogue and feeds the doc site.
`docs/architecture/pack-layout.md` gains the shape and defers to it rather than
restating. `author-a-skill.md` gets the rule at the point of authoring;
`packs/AGENTS.md` gets the one-line agent-facing form.

**Done when:** all four carry it; `packs/AGENTS.md` is under 150 lines.

## Risks

- **Silent CI coverage loss.** Relocating a test whose only runner is a path in
  one workflow removes it from CI without failing anything. Mitigated by the
  consumer sweep being a task in its own right, and by re-running `test-all.py`
  after the move rather than trusting `build-check`.
- **`build-check` does not cover the hook pytest suites.** It was green while
  all 30 hook tests were broken by a wrong `parents[]` depth. Verification runs
  the full set, not the aggregate gate alone.
- **Version-parity gate has a blind spot.** `verify.py:_step_version_parity`
  probes `pack_dir / "plugin.json"`, not `pack_dir / ".claude-plugin" / "plugin.json"`,
  so it no-ops on this layout. The `plugin.json` bump was caught by the
  agentbundle suite, not by `build-check`. Noted as a follow-up.
- **Partial adoption.** Core follows the new boundary and
  `packs/core/tests/pack/test-runtime-boundary.py` enforces it there; 22 packs
  do not, and the check is deliberately core-scoped so it fails on regressions
  rather than on deferred work. Nothing stops a *new* pack from putting tests
  under `.apm/`. Tracked as `pack-test-boundary-remaining-packs`.

## Changelog

- Started as a light-mode prose fix for the knowledge-entry schema. Escalated
  to full mode when the work moved a linter into the published pack, added an
  adopter-facing gate, and changed the pack format's directory contract — three
  published-interface or structural triggers.
- An earlier draft placed evals at `packs/<pack>/evals/`. Corrected: the
  enforced layout is `.apm/skills/<skill>/evals/`, and the adversarial pass
  caught the shipped docs asserting the unbuilt state as fact. ADR-0071 records
  the three-boundary model that resulted.
- T6 grew a fifth surface — ADR-0071 — after review flagged that eleven
  MUST-level rules were shipping with no recorded decision behind them.
