# Plan: Lighter RFC delivery

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing
- **Repository anchors:** `packs/AGENTS.md` (pack bump, shipped-text rules, pack tests), `tests/AGENTS.md` (roster steps), `packages/agentbundle/AGENTS.md`, `docs/guides/how-to/cut-a-package-release.md`. Analogous production code: `packs/repo-governance/.apm/skills/new-rfc/scripts/governance.py` with its tests under `packs/repo-governance/tests/skills/new-rfc/`. Index behavior: `packs/repo-governance/.apm/skills/new-rfc/scripts/index-records.py` and `tests/roster/test_index_records.py`. Named uncertainty: none beyond the helper's missing rename and remove, which `renumber` covers itself.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections or its `Terminal Intent`. A change to tasks, tests, stubs, design, or
> approach is an in-envelope working-plan change made while no attempt is open.
> `Touches`, `Tests` and `Done when` are what a completion gate reads; `Design`,
> `Approach` and `Risks` are working material.

## Approach

Build the script first, because the template, seeds, skill and repository copies depend on its shape. `docs/specs/lighter-rfc-delivery/notes/prototype/` holds the reviewed prototype of `rfc.py`, the template, the starter and the issue template; T1 and T2 promote them into the pack, replacing the prototype's hand-written confinement with the shared `file_safety.py`, loading that helper from source bytes. Seeds, the skill's copies and this repository's copies follow from the pack sources, then the skill, guide, ADR and release bookkeeping. The riskiest part is breadth: pinned tests in several suites name the old template, the old pack and package versions and the old guide, so each task runs the suite it could break.

## Constraints

- RFC-0114 decides D1 to D7; this plan implements them and does not reopen them.
- RFC-0091 keeps the rule for when an RFC is warranted; the starter repeats it with its reserved categories.
- ADR-0089 keeps Decision weight as the lever for gate depth.
- `packs/AGENTS.md` and `tests/AGENTS.md` bind versions, shipped text, pack tests and roster steps.
- Seed upgrade handling is out of scope.

## Construction tests

Cross-cutting tests are the install snapshot, `python3 packs/repo-governance/.apm/skills/new-rfc/scripts/index-records.py --type rfc --check docs/rfc`, `rfc.py check` over the real corpus, and `navigate-decisions` lineage over fixture RFCs.
**Integration tests:** `agentbundle install` of `repo-governance` into an empty temp repo.
**Manual verification:** T10 records one fork-only run in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| ADR and spec Status pointers | T8 | ADR file; Status pointers | `navigate-decisions` health `ok` |
| Guide | T7 | guide lints and pinning suites | guide names six sections, no Approver |
| Changelog fragment and versions | T9 | fragment; `CAT-L009`; `test_okf_catalogue_discovery.py` | versions agree |
| This repository's `docs/GOVERNANCE.md` and architecture page | T6 | self-host check | file names the maintainer; page lists it |
| Captured follow-ons | T11 | three captured items | each names an owner |

## Design (LLD)

### Design decisions
- `rfc.py` loads `file_safety.py` from its own source bytes, read as a confined regular file and executed without consulting a bytecode cache, because isolated mode removes the script folder from `sys.path` and a by-path import still reads a planted bytecode cache. Rests on: the loader being the only reader of that file. Traces to: AC-0024, AC-0025.
- The skill carries the same `rfc.py` bytes it seeds and calls it with `--dir`, so numbering has one implementation; it needs no template beside it for `next` and `check`. `next` numbers from the repository that contains the RFC folder. Traces to: AC-0052, AC-0058, AC-0008.
- The template's one text is the source for both copies, and the starter is the source for governance mode's default; pack tests pin both equalities. Traces to: AC-0001, AC-0048.
Owned by: T1, T2, T4

### Interfaces & contracts
- `rfc.py [--dir PATH] {next | new TITLE [--author H] [--number N] [--slug S] | renumber FILE N | check [FILE...] [--strict]}`; exit 0, 1 (strict warnings, or a refusal), 2 (usage or unreadable). Test seams: `main(argv)` takes an argument list and a folder; the git lookup sits behind one function, and a second seam sits at the single process-spawn call so a test sees the final argv, environment and subcommand.
Owned by: T1

### Behavior & rules
- A record is `NNNN-<slug>.md` with exactly four digits and `[a-z0-9-]`; `XXXX-<slug>.md` is an unnumbered draft read as a record; `NNNN-<slug>-research.md` and `NNNN-notes/` are companions. The counted text is everything except the title and the header field block. Non-terminal means the status word is not Accepted, Rejected, Withdrawn, Experimental or Superseded. Slug length is capped only on names the script creates.
- Supersession on the skill side: the draft carries `Supersedes` lines with D-numbers; after acceptance, one header line and one Errata entry per frozen RFC, then a lineage query in both directions.
Owned by: T1, T4

### Failure, edge cases & resilience
- The nine controls in `docs/rfc/0114-notes/security-controls.md` are the failure model. `renumber` writes the target exclusively, removes the source, and removes the target only if it is the file just created when the second step fails.
Owned by: T1, T3

### Dependencies & integration
- `file_safety.py` already has many byte-identical copies under `packs/` and the package; the seeded copy joins the existing identical-copies roster test. `self_host.py` and `lint.py` are the only `agentbundle` source files touched, and the package's six release surfaces move with them.
Owned by: T3, T6, T9

## Tasks

### T1: `rfc.py` passes its behavior and security tests

**Depends on:** none
**Touches:** `packs/repo-governance/.apm/skills/new-rfc/scripts/rfc.py`, `packs/repo-governance/tests/skills/new-rfc/test_rfc_script.py`

**Tests:**
- Function-level tests drive `main(argv)` over `tmp_path` folders with the git seam replaced, covering AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0032, AC-0033, AC-0034, AC-0084. Verification mode: TDD. The module is loaded under a pack-and-skill-specific name.
- One subprocess test runs `python3 -I rfc.py` beside a planted `argparse.py` and a planted unchecked-hash bytecode file written at `importlib.util.cache_from_source` of the helper's path, whose marker must not appear. A positive control in the same test shows a by-path loader does run that file, so the fixture is proven live. It is the only spawned interpreter.
- A test at the process-spawn seam asserts every git invocation's argv carries the four `-c` settings (`core.fsmonitor=`, `core.hooksPath`, `protocol.allow=never`, `safe.bareRepository=explicit`), its environment carries `GIT_TERMINAL_PROMPT=0`, its subcommand is in the read-only allowlist, and its working directory is the RFC folder's repository; the seam sits below argv and environment construction, so deleting any one turns it red.
- A `--dir` test uses different records in each folder and a planted `PATH/file_safety.py`, and asserts every read, listing and write targets `PATH` and the planted helper never runs.
- A walk over every `renumber` failure path asserts the folder holds exactly the original file; an AST test asserts the imports.

**Approach:** start from `notes/prototype/rfc.py`. Reads, listing and exclusive creation go through `file_safety.py` (`write_confined_regular_file(..., expect_sha256=None)` creates exclusively and refuses an existing file; `read_confined_regular_file` refuses a link). `renumber` keeps its own link refusal and rollback because the helper has no rename or remove, and it validates the path's directories with the helper before resolving. The loader compiles the helper from its source bytes. Drop the prototype's decided-record check: its docstring sentence, the `remote_names()` call in `cmd_check` and the "marked decided" warning. `check` starts no git process; only `next` and `new` use git. Edit the docstring (drop the decided-record sentence) and the `check` subparser help so both name the length, missing-section and number-clash warnings, and assert that text in the T1 tests.

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/new-rfc/test_rfc_script.py -q` is green.

### T2: Template asset and seed are one text with the required shape

**Depends on:** none
**Touches:** `packs/repo-governance/.apm/skills/new-rfc/assets/rfc.md`, `packs/repo-governance/seeds/docs/rfc/template.md.tmpl`, `packs/repo-governance/tests/skills/new-rfc/test_template.py`

**Tests:**
- A pack test compares the two files byte for byte (AC-0001), parses the headings and header fields against AC-0002, AC-0003, and checks AC-0004, AC-0005, AC-0006, AC-0007 and the template half of AC-0038. Verification mode: goal-based.
- `tests/roster/test_rfc_template_contract.py` and `tests/roster/test_decision_record_destination_contract.py` still pass: the Decision-weight line keeps the cue text they pin.

**Approach:** copy `notes/prototype/template.md.tmpl`, keep the current Decision-weight cue from `assets/rfc.md`, and add the header-comment pointer to `python3 -I docs/rfc/rfc.py`. The supersession example stays generic. Add a sentence saying a decider named inside an RFC is a suggestion and that only the repository's rules and a listed maintainer's merge accept an RFC.

**Done when:** `test_template.py`, `tests/roster/test_rfc_template_contract.py` and `tests/roster/test_decision_record_destination_contract.py` are green.

### T3: Seeds ship, declare their shapes, and pass the install snapshot

**Depends on:** T1, T2
**Touches:** `packs/repo-governance/seeds/docs/GOVERNANCE.md`, `packs/repo-governance/seeds/docs/rfc/rfc.py`, `packs/repo-governance/seeds/docs/rfc/file_safety.py`, `packs/repo-governance/seeds/.github/ISSUE_TEMPLATE/proposal-idea.md`, `packages/agentbundle/agentbundle/catalogue_tooling/lint.py`, `tests/fixtures/install_snapshot/repo-governance.paths.txt`, `packs/repo-governance/tests/skills/new-rfc/test_seeds.py`

**Tests:**
- A pack test checks AC-0052, the starter, issue-template and guidance statements in AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0042, AC-0043, AC-0044, the citation scan in AC-0045, and the `python3 -I` scan over the seeded files, the script's help and the template header for AC-0046. Mode: goal-based.
- `tests/roster/test_new_rfc_governance_surfaces.py`, the identical-copies roster test, with the seeded `file_safety.py` included (AC-0053), `tests/roster/test_install_snapshot.py` with the golden updated for AC-0050, and `agentbundle catalogue lint --root . --deep` for AC-0051.

**Approach:** the starter and issue template come from `notes/prototype/`; the starter gains the four-rung ladder, RFC-0091's four reserved categories, the maintainer-owned list and its close-review sentence, the trusted-copy and CI guidance and the suggestion sentence, all without internal citations. `lint.py` gets one declared-shape entry per new seed. Regenerate the snapshot golden once and review its diff.

**Done when:** `test_seeds.py`, `tests/roster/test_new_rfc_governance_surfaces.py`, `tests/roster/test_install_snapshot.py` and catalogue lint are green.

### T4: The skill uses the script, one governance text, and the new rules

**Depends on:** T1, T2, T3
**Touches:** `packs/repo-governance/.apm/skills/new-rfc/SKILL.md`, `packs/repo-governance/.apm/skills/new-rfc/assets/governance-default.md`, `packs/repo-governance/.apm/skills/new-rfc/scripts/governance.py`, `packs/repo-governance/tests/skills/new-rfc/test_new_rfc_instructions.py`, `packs/repo-governance/tests/skills/new-rfc/test_governance_script.py`, `packs/repo-governance/tests/skills/new-rfc/test_supersession_flow.py`

**Tests:**
- Source-text pins in `test_new_rfc_instructions.py` for AC-0058, AC-0059, AC-0060, AC-0061, AC-0063, AC-0064, AC-0065, AC-0067, AC-0068, AC-0069, AC-0070; the pin for the old target-rule sentence is replaced, and the pin that RFC mode never names `GOVERNANCE.md` stays. The `python3 -I` scan covers the skill text.
- `test_governance_script.py` for AC-0048, AC-0049, AC-0062: the asset equals the seeded starter, the draft check accepts it with a handle in place of the placeholder, and an existing governance file at each allowed location is the target.
- `test_supersession_flow.py` over fixture RFCs for AC-0066: after the mirrored line and Errata are written, a `navigate-decisions` lineage query returns a checked edge with equal scopes in both directions. The skill's wording for AC-0064, AC-0065 is decided by the source-text pins and by T5's judged assertions, not by this fixture.
- `test_next_ordinal.py` stays green: the skill's `next-ordinal.py` copy is untouched and still equal to the ADR copy.

**Approach:** edit only the sections `docs/rfc/0114-notes/skill-updates.md` names. The relaxed draft check drops the three-owned-path requirement and nothing else.

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/new-rfc -q` is green.

### T5: Evals describe the new behavior

**Depends on:** T4
**Touches:** `packs/repo-governance/.apm/skills/new-rfc/evals/evals.json`, `packs/repo-governance/.apm/skills/new-rfc/evals/eval_queries.json`, `packs/repo-governance/tests/skills/new-rfc/test_evals.py`

**Tests:**
- A pack test pins the eval file's assertions for AC-0071. One new eval plants an out-of-scope instruction in a template comment and in an existing RFC for AC-0047. `agentbundle pack evals run` for `new-rfc` runs in judge mode, and the verification ledger records the pass or fail result of each eval by name. Mode: goal-based plus the graded run.

**Done when:** `test_evals.py` is green and the judged run passes the injection eval's assertions, with its result recorded in the ledger.

### T6: This repository adopts the starter and keeps its copies equal

**Depends on:** T1, T2, T3
**Touches:** `docs/GOVERNANCE.md`, `docs/rfc/rfc.py`, `docs/rfc/file_safety.py`, `docs/rfc/template.md.tmpl`, `docs/architecture/pack-layout.md`, `packages/agentbundle/agentbundle/build/self_host.py`, `tests/roster/test_lighter_rfc_delivery.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`

**Tests:**
- `tests/roster/test_lighter_rfc_delivery.py` is created here with the equality and governance tests for AC-0054, AC-0055, AC-0057; later tasks add their functions to it. `agentbundle catalogue self-host --root . --check` passes (AC-0056). `tools/test-lint-ci-parity.py` and the new `build-check.yml` step agree. Mode: goal-based.

**Approach:** the roster file needs a named step above the bulk step and a `LOCAL("test-after-build-check")` entry. `docs/GOVERNANCE.md` lists `eugenelim`, this spec's Owner, as the maintainer.

**Done when:** the roster file, the self-host check and the CI-parity test are green.

### T7: The guide matches the new process

**Depends on:** T2, T4, T6
**Touches:** `guides/repo-governance/how-to/new-rfc.md`, `tests/roster/test_lighter_rfc_delivery.py`

**Tests:**
- A roster function greps the guide for `Approver`, `Reviewer brief` and `The ask`, finds none, and finds the six section names (AC-0072), plus the `python3 -I` scan over the guide. The guide keeps its readiness-summary, proof and fresh-context wording (AC-0073), checked by the suites that pin it: `tests/roster/test_decision_record_destination_contract.py`, `tests/roster/test_conventions_retirement.py`, `tests/roster/test_spec_index_retirement.py` and `tools/test_stasis_retirement_claims.py`. `python3 tools/validate_guides.py`, `tools/check-guide-index.py` and `tools/lint-guide-titles.py` pass.

**Done when:** the three guide tools and the four pinning suites exit 0.

### T8: One ADR supersedes the pinned criteria

**Depends on:** T4, T6, T7
**Touches:** `docs/adr/`, `docs/specs/new-rfc-two-humans/spec.md`, `docs/specs/new-rfc-readability/spec.md`, `docs/specs/new-rfc-governance/spec.md`, `tests/roster/test_lighter_rfc_delivery.py`

**Tests:**
- `python3 packs/repo-governance/.apm/skills/new-adr/scripts/lint-adr-shape.py` on the ADR, `python3 packs/repo-governance/.apm/skills/new-rfc/scripts/index-records.py --type adr --check docs/adr`, `navigate-decisions health` reports `ok` (AC-0076), and a roster function checks that each spec's Status line carries a pointer naming the superseded criteria (AC-0075) and that the ADR lists each criterion in `superseded-criteria.md` (AC-0074). Mode: goal-based.

**Approach:** the ordinal is re-derived when the ADR is written. Rows come from `docs/rfc/0114-notes/superseded-criteria.md`, each criterion number re-checked against the spec text; only Status lines of the specs change.

**Done when:** the lint, the index check, the health report and the roster function pass.

### T9: Versions, changelog and pinned tests agree

**Depends on:** T3, T4, T5, T6, T7, T8
**Touches:** `packs/repo-governance/pack.toml`, `packs/repo-governance/.claude-plugin/plugin.json`, `packages/agentbundle/pyproject.toml`, `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/CHANGELOG.md`, `packages/agentbundle/README-pypi.md`, `docs/product/changelog.d/`, `tests/roster/test_new_rfc_governance_surfaces.py`, `tests/roster/test_repo_governance_rename_completeness.py`, `tests/roster/test_registry_upgrade_notes.py`, `tests/roster/test_okf_catalogue_discovery.py`

**Tests:**
- Catalogue lint `CAT-L009`, `tests/roster/test_okf_catalogue_discovery.py` and the `README-pypi.md` and `CHANGELOG.md` heading checks for AC-0077; the changelog check for AC-0079; the pack-version pins updated and the registry-notes map pointed at the new fragment (AC-0080); and a comparison of each new version with `git show origin/main:<file>` for AC-0078, run in this task and recorded in the ledger. Mode: goal-based.

**Approach:** each new version is the next patch above the fetched default branch, read at this task and never a literal copied from an earlier note. The package change is committed with an `Engine-Change-RFC: RFC-0114` trailer. Tagging and publishing the package is a post-merge step for the owner, listed in Follow-ons.

**Done when:** catalogue lint and the four roster files are green, the ledger holds the version comparison, and the commit that changes `packages/agentbundle/` carries the `Engine-Change-RFC: RFC-0114` trailer, which the release guide requires and which a squash before the PR must keep.

### T10: Whole-change verification

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T9, T11
**Touches:** `docs/specs/lighter-rfc-delivery/notes/verification-ledger.md`

**Tests:**
- AC-0022, AC-0082, `agentbundle catalogue lint --root . --deep`, `make build-self` leaving a clean tree, and AC-0083 as one recorded run of `rfc.py check` on the new draft file. Mode: goal-based and manual QA.

**Done when:** every command above exits 0 and the ledger records the fork-only run.

### T11: Follow-ons are captured as work items

**Depends on:** T6
**Touches:** `docs/product/captured/`, `tests/roster/test_lighter_rfc_delivery.py`

**Tests:**
- For AC-0081: a roster function asserts a captured item for fixing seed upgrades exists, names `eugenelim`, and states that `agentbundle upgrade` neither refreshes nor adds seeded files while the published guides say it does. Two further captured items cover the stale `re-sync.md` wording and the stale desk-research guide mapping. Mode: goal-based.

**Approach:** write each through the repository's `work-intake` route.

**Done when:** the three captured items exist and the roster function is green.

## Rollout

Reversible: the template and skill revert by reverting the change; seeded files already installed in adopter repositories stay, inert. Sequencing: script, then template, then seeds and skill, then repository adoption, guide and ADR, then versions last so no task borrows an unreleased version. The `agentbundle` tag and publish follow the merge. Seeded files reach fresh installs only; existing adopters can run `agentbundle scaffold` to add them.

## Risks

- **Pinned tests across suites.** The old pack version, package version, template, guide and numbering text are pinned in several places. Each task runs the suite it could break, and T10 runs them together.
- **Tests that need history.** Three roster tests need git history or a remote and run only in a full clone, so T10 runs in the real repository.
- **Roster step placement.** A new roster test placed below the bulk CI step reports failures twice. T6 places it above.
- **Dirty-tree refusal.** `make build-self` refuses a dirty tree, so projections are regenerated with the self-host command before each commit.
- **ADR number moves.** Another change may take the ordinal. T8 re-derives it and renumbers before the PR.
- **Unpublished package version.** Until the owner tags the release, `main` claims a version PyPI lacks. The Follow-ons entry names the step.

## Changelog

<!-- Approvals only; written at the approval gates. -->

- 2026-11-06: plan approved by eugenelim (build strategy)
