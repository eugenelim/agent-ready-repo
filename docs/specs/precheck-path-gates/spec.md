# Spec: Path-triggered precheck

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

A contributor or agent changing this repository runs `make precheck` before the first push and learns about the failures that otherwise surface only in CI: projection drift, skill-spec lint, a wrong core version bump, and bandit findings. The command runs only the checks the changed paths trigger, so it adds no cost to the existing local gate.

## What Changes

- A stdlib-only runner that maps changed paths to cheap checks and reports each check it skipped — `tools/precheck.py`, with its suites beside it.
- A `precheck` make target, and the suites registered where CI runs them — `Makefile`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`, `tools/test_local_ci_shared_test_deduplication.py`.
- The root commands block names `make precheck` beside the lint pair, and the `build-self` line says it writes projections after `.apm/` edits — `AGENTS.md`.
- A rule in the `AGENTS.md` lint that every make target named beside "local gate" exists — `tools/lint-agents-md.py`.
- The existing routing row also covers the precheck surface, and a precheck entry joins the verification entries — `AGENT_RULES.md`, `docs/VERIFICATION.md`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable: the precheck is how a contributor verifies a repository change | `docs/VERIFICATION.md`, root `AGENTS.md`, `AGENT_RULES.md` | repository maintainers | the entry's recorded run; `lint-agents-md.py` passes | the entry names the command, its skips, and what it does not prove |
| Release history | Absent: no pack or package content changes, so no version moves | none | none | none | none |
| User promise, architecture, interface compatibility, operations | Absent: a local maintainer tool | none | none | none | none |

## Agent Rules

### Always do

- Keep `tools/precheck.py` pure standard library, with every subprocess in list form.
- Name each skipped check in the output with the reason.
- Reuse `tools/run-bandit-gate.py`'s floor and `tools/check-core-release.py`'s checks rather than copying their flags or rules.
- Run only the suites this spec names; dispatch the heavy ones to CI.

### Ask first

- Chaining `precheck` into any other make target.
- Adding a check to the runner beyond the four it names: self-host, deep catalogue lint, core release, bandit.
- Raising any `AGENTS.md` line cap.

### Never do

- Edit `packs/**/.apm/` or `packages/agentbundle/` in the delivered change, or anything under `docs/specs/*/delivery/`. The manual run touches a `.apm` file only on a throwaway branch that is never merged.
- Add a top-level directory or a dependency.
- Let a missing optional tool pass or fail silently: it is named and skipped.

## Testing Strategy

- **TDD (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010):** the runner's path mapping, skips and base handling, because the mapping is a pure function over a path list and the executor can be injected.
- **TDD (AC-0015):** the `AGENTS.md` lint rule, against fixture files; the red case asserts on the rule's own diagnostic, because a scratch fixture repository already exits non-zero on unrelated structure checks.
- **Goal-based (AC-0011, AC-0012):** the make wiring and registration, checked by `make -n precheck`, a Makefile grep, `lint-ci-parity.py` and the dedup suite.
- **Goal-based (AC-0013, AC-0014, AC-0016):** the guidance edits, checked by `tools/lint-agents-md.py` and the three suites that pin those files.
- **Manual QA (AC-0017):** the precheck entry, with one real run on a throwaway branch that touches a `packs/**/.apm` file, recorded in the ledger.

## Acceptance Criteria

- [x] **AC-0001.** `tools/precheck.py` given a changed-path list that matches no trigger prints `no trigger matched` and starts no subprocess.
- [x] **AC-0002.** Given a changed path under `packs/<pack>/.apm/`, it runs `agentbundle catalogue self-host --root . --check` and exits with that command's status.
- [x] **AC-0003.** Given a changed `SKILL.md` under `packs/`, it runs `agentbundle catalogue lint --root . --deep` and exits with that command's status.
- [x] **AC-0004.** Given a changed path in core pack content (`packs/core/seeds/**`, `packs/core/.apm/**`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`), it runs `tools/check-core-release.py` against the resolved base and exits with its status.
- [x] **AC-0005.** Given a change confined to `packs/core/tests/**`, it does not run `tools/check-core-release.py`.
- [x] **AC-0006.** Given changed `.py` files, it scans exactly those that exist in the working tree with bandit, at the severity and confidence floor `tools/run-bandit-gate.py` defines, limited to changed files under the gate's scan roots, so a file with only LOW findings exits 0, and a MEDIUM finding or any bandit stderr exits non-zero.
- [x] **AC-0007.** When `agentbundle`, PyYAML (which the deep catalogue lint imports) or bandit is not installed in the interpreter, the checks that need it print `skipped: <tool> not installed` and leave the exit status unchanged.
- [x] **AC-0008.** When the base ref cannot be resolved, it exits with status 2 and a message naming the base, and runs no check.
- [x] **AC-0009.** Without `--with-tests` it runs no pytest suite and prints the pytest command for each touched pack.
- [x] **AC-0010.** With `--with-tests` it runs `python -m pytest packs/<pack>/tests -q` for each touched pack and exits non-zero when a run does.
- [x] **AC-0011.** No Makefile target other than `precheck` names `precheck` in its prerequisites or recipe.
- [x] **AC-0012.** The new suites are registered in the batch, mirror and disposition that run them in CI: `python3 tools/lint-ci-parity.py` and `python3 -m pytest tools/test_local_ci_shared_test_deduplication.py -q` both pass.
- [x] **AC-0013.** Root `AGENTS.md` names `make precheck` in its commands block beside `make lint-ruff lint-mypy`, and `python3 tools/lint-agents-md.py` passes.
- [x] **AC-0014.** The root `build-self` line states that it writes projections and that `.apm/` edits require it.
- [x] **AC-0015.** `tools/lint-agents-md.py` exits non-zero with the diagnostic `local-gate target not defined: <target>` on a fixture whose fenced command block names `local gate` beside a `make` line of two targets when the second is missing from the fixture Makefile, and exits zero on this repository.
- [x] **AC-0016.** The existing `AGENT_RULES.md` row that reads `docs/VERIFICATION.md` has a `when` that also covers the precheck surface.
- [x] **AC-0017.** `docs/VERIFICATION.md` holds a precheck entry carrying each field named under § Verify entries → Fields in the work-loop `references/verification-modes.md`.

## Follow-ons

none

## Assumptions

- Defaulted: Technical: precheck runs only triggered checks and no full suites — default: an empty diff finishes in about 2 s and a `packs/**` diff in about 60 s, recorded in the ledger; if wrong: tighten the checks or drop one (settled by: owner).
- Defaulted: Technical: a missing optional tool is a named skip, not a failure — default: skip and print; if wrong: make it a failure (settled by: owner).
- Defaulted: Technical: `make precheck` is the only wiring — default: chained into no other target; if wrong: chain it and accept the cost (settled by: owner).
- Defaulted: Technical: pack tests are opt-in via `--with-tests` — default: print the command, because the CI-only failures in this class lived in `tools/` and `tests/roster/` and a pack suite can take minutes; if wrong: run them by default (settled by: owner).
- Defaulted: Process: no `Engine-Change-RFC:` trailer applies — default: `packages/agentbundle/` is untouched; if wrong: add the trailer (settled by: owner).
- Defaulted: Process: the hardcoded-`/tmp` rule (owned by `packages/AGENTS.md` and bandit B108), the 500-line skill limit (owned by `skill_spec_lint.py`) and the `astro dev` paragraph overlap in `docs-site/` and `web/` stay out of this spec — default: precheck's deep lint and bandit run catch the first two, and the third is unrelated cleanup; if wrong: a separate spec (settled by: owner).

## Terminal Intent

`code` — `make precheck` runs the path-triggered checks and the guidance, lint and verification-entry edits are in place.

## Accepted Risk

none
