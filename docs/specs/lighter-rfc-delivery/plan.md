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
**Manual verification:** T10 runs one fork-only run and reports it; the controller records it in `notes/verification-ledger.md` at closeout, because the supervisor protects the spec folder during a run.

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

**Approach:** start from `notes/prototype/rfc.py`. Reads and exclusive creation go through `file_safety.py`; a listing validates the folder with the helper (`validate_confined_directory`) and then reads one directory level with `os.scandir`, because the helper's own listing refuses links and descends into subfolders (`write_confined_regular_file(..., expect_sha256=None)` creates exclusively and refuses an existing file; `read_confined_regular_file` refuses a link). `renumber` keeps its own link refusal and rollback because the helper has no rename or remove, and it validates the path's directories with the helper before resolving. The loader compiles the helper from its source bytes. Drop the prototype's decided-record check: its docstring sentence, the `remote_names()` call in `cmd_check` and the "marked decided" warning. `check` starts no git process; only `next` and `new` use git. Edit the docstring (drop the decided-record sentence) and the `check` subparser help so both name the length, missing-section and number-clash warnings, and assert that text in the T1 tests.

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
- A pack test pins the eval file's assertions for AC-0071. One new eval plants an out-of-scope instruction in a template comment and in an existing RFC for AC-0047. `agentbundle pack evals run` for `new-rfc` runs in judge mode, and the closeout ledger records the pass or fail result of each eval by name. Mode: goal-based plus the graded run.

**Done when:** `test_evals.py` is green and the judged run passes the injection eval's assertions, with its result recorded in the closeout ledger.

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
- Catalogue lint `CAT-L009`, `tests/roster/test_okf_catalogue_discovery.py` and the `README-pypi.md` and `CHANGELOG.md` heading checks for AC-0077; the changelog check for AC-0079; the pack-version pins updated and the registry-notes map pointed at the new fragment (AC-0080); and a comparison of each new version with `git show origin/main:<file>` for AC-0078, run in this task and reported for the closeout ledger. Mode: goal-based.

**Approach:** each new version is the next patch above the fetched default branch, read at this task and never a literal copied from an earlier note. The package change is committed with an `Engine-Change-RFC: RFC-0114` trailer. Tagging and publishing the package is a post-merge step for the owner, listed in Follow-ons.

**Done when:** catalogue lint and the four roster files are green, the version comparison is reported for the closeout ledger, and the commit that changes `packages/agentbundle/` carries the `Engine-Change-RFC: RFC-0114` trailer, which the release guide requires and which a squash before the PR must keep.

### T10: Whole-change verification

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T9, T11
**Touches:** none (verification only)

**Tests:**
- AC-0022, AC-0082, `agentbundle catalogue lint --root . --deep`, `make build-self` leaving a clean tree, and AC-0083 as one recorded run of `rfc.py check` on the new draft file. Mode: goal-based and manual QA.

**Done when:** every command above exits 0 and the fork-only run is reported for the closeout ledger.

### T11: Follow-ons are captured as work items

**Depends on:** T6
**Touches:** `docs/product/captured/`, `tests/roster/test_lighter_rfc_delivery.py`

**Tests:**
- For AC-0081: a roster function asserts a captured item for fixing seed upgrades exists, names `eugenelim`, and states that `agentbundle upgrade` neither refreshes nor adds seeded files while the published guides say it does. Two further captured items cover the stale `re-sync.md` wording and the stale desk-research guide mapping. Mode: goal-based.

**Approach:** write each through the repository's `work-intake` route.

**Done when:** the three captured items exist and the roster function is green.

### T12: Review findings are repaired

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T9, T11
**Touches:** `packs/repo-governance/.apm/skills/new-rfc/scripts/rfc.py`, `packs/repo-governance/seeds/docs/rfc/rfc.py`, `docs/rfc/rfc.py`, `packs/repo-governance/.apm/skills/new-rfc/SKILL.md`, `packs/repo-governance/.apm/skills/new-rfc/evals/evals.json`, `packs/repo-governance/tests/skills/new-rfc/test_rfc_script.py`, `packs/repo-governance/tests/skills/new-rfc/test_new_rfc_instructions.py`, `packs/repo-governance/tests/skills/new-rfc/test_seeds.py`, `tests/roster/test_lighter_rfc_delivery.py`, `guides/repo-governance/how-to/new-rfc.md`, `guides/repo-governance/how-to/set-up-governance.md`, `docs/GOVERNANCE.md`, `docs/product/changelog.d/`, `packages/agentbundle/README-pypi.md`, `packages/agentbundle/CHANGELOG.md`

**Tests:**
- Each repair below carries a test that fails before it: `renumber` slug length and symlinked ancestors outside the working directory (AC-0014, AC-0030); a linked helper in the script's folder prints the AC-0026 warning and then refuses with exit 2; the loader refuses a hard-linked helper (AC-0025); the loader never reads past one byte over the cap (AC-0029); a rollback that fails exits above 1 and names the leftover file, and an interrupt after the create restores the original (AC-0015); `next` takes the larger of `upstream` and `origin` when they differ (AC-0008); a record and its research companion sharing a number raise no clash (AC-0019); the guide names the six sections `rfc.py` requires (AC-0072); the changelog fragment states the new-installs-only limit and the re-copy route (AC-0079); the release notes name the self-host and lint changes (AC-0077); the governance guide's sample matches the starter (AC-0048); the maintainer is listed as `@eugenelim` (AC-0055). Mode: TDD for the script, goal-based for text.

**Approach:** apply the supported findings of the first review round. The skill resolves the RFC folder before numbering and says to number the first RFC `0001` when the folder does not exist. The shipped skill text uses `RFC-NNNN` in its supersession example. Eval 12 names the `rfc.py ... check` subcommand. Dead test arms and the unused name are removed, and the wrong criterion labels are corrected. The three copies of `rfc.py` stay byte-identical.

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/new-rfc tests/roster/test_lighter_rfc_delivery.py -q` is green and the copies are identical.

### T13: Second-round review findings are repaired

**Depends on:** T12
**Touches:** `packs/repo-governance/.apm/skills/new-rfc/scripts/rfc.py`, `packs/repo-governance/seeds/docs/rfc/rfc.py`, `docs/rfc/rfc.py`, `packs/repo-governance/.apm/skills/new-rfc/SKILL.md`, `packs/repo-governance/.apm/skills/new-rfc/assets/rfc.md`, `packs/repo-governance/seeds/docs/rfc/template.md.tmpl`, `docs/rfc/template.md.tmpl`, `packs/repo-governance/tests/skills/new-rfc/test_rfc_script.py`, `packs/repo-governance/tests/skills/new-rfc/test_template.py`, `tests/roster/test_lighter_rfc_delivery.py`, `guides/repo-governance/how-to/set-up-governance.md`, `packages/agentbundle/CHANGELOG.md`, `packages/agentbundle/README-pypi.md`

**Tests:**
- A helper with a syntax error, or one that raises at import, makes every command exit 2 with no traceback (AC-0025, AC-0012). A `KeyboardInterrupt` raised inside the helper's write during `renumber` leaves only the original (AC-0015). A case where both remotes resolve and `origin` holds the higher number shows `next` takes the larger (AC-0008). The AC-0074 roster check looks for each superseded criterion inside its own spec's section of the ADR. The governance guide's sample matches a fresh install (AC-0048). The template's check cue names a runnable command (AC-0006). Mode: TDD for the script, goal-based for text.

**Approach:** `_fs` converts any exception from compiling or running the helper into the helper-unavailable error, and interrupts keep propagating. `renumber` records that the create was attempted before it calls the helper and removes the target after any non-`OSError` interruption when the source still exists. The governance guide shows the fresh-install preview (`docs/GOVERNANCE.md` present, approval required) and says replacing the seeded placeholder needs a named accepted RFC or recorded owner decision. The template cue becomes `python3 -I docs/rfc/rfc.py check <file>` in all three copies. The skill's supersession step adds the mirror line when the frozen RFC has none. The package changelog describes the lighter-RFC change. The three `rfc.py` copies and the template copies stay byte-identical.

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/new-rfc tests/roster/test_lighter_rfc_delivery.py -q` is green and the copies are identical.

### T14: Third-round review findings are repaired

**Depends on:** T13
**Touches:** `packs/repo-governance/tests/skills/new-rfc/test_seeds.py`, `packs/repo-governance/tests/skills/new-rfc/test_rfc_script.py`, `packs/repo-governance/tests/skills/new-rfc/test_template.py`, `packs/repo-governance/.apm/skills/new-rfc/evals/evals.json`, `tests/roster/test_lighter_rfc_delivery.py`, `tests/roster/test_new_rfc_governance_surfaces.py`, `guides/repo-governance/how-to/set-up-governance.md`

**Tests:**
- `python3 tools/lint-pack-test-boundary.py` and `python3 tools/test-lint-pack-test-boundary.py` exit 0 without an allowlist or a weakened rule (AC-0053, AC-0008, AC-0033). The seeded `file_safety.py` equals the blessed helper in a roster test that may read both trees. The template test fails on the old cue and passes on `check <file>` (AC-0006). The AC-0074 check looks for the governance-draft row inside the ADR's D3 section. Mode: goal-based.

**Approach:** the AC-0053 byte comparison with the package helper leaves `test_seeds.py` and lives in the repository-level identical-copies roster test, which already compares the seeded copies; extend it if it does not cover the seeded `file_safety.py`. The git-seam stubs match the `rev-parse --show-toplevel` argv by element, with no literal list holding both strings. The governance guide's sample shows `(<n> bytes)` in place of a fixed count. The first eval's expected output names the template's Motivation Non-goals and no Problem and goals section.

**Done when:** both boundary-lint commands exit 0 and `python3 -m pytest packs/repo-governance/tests/skills/new-rfc tests/roster/test_lighter_rfc_delivery.py tests/roster/test_new_rfc_governance_surfaces.py -q` is green.

### T15: Fourth-round review findings are repaired

**Depends on:** T14
**Touches:** `packs/repo-governance/.apm/skills/new-rfc/evals/evals.json`, `packs/repo-governance/.apm/skills/new-rfc/evals/files/`, `packs/repo-governance/tests/skills/new-rfc/test_evals.py`, `packs/repo-governance/tests/skills/new-rfc/test_seeds.py`, `tests/roster/test_lighter_rfc_delivery.py`, `guides/repo-governance/how-to/set-up-governance.md`, `docs/product/captured/desk-research-guide-rfc-mapping-is-stale.md`

**Tests:**
- The injection eval lists a template fixture and an existing-RFC fixture in its `files`, each carrying its planted comment, and its prompt names them by base name (AC-0047). The guide's sample opens with the lines the default asset opens with and the roster check passes only then (AC-0048). The captured item names the template's six required sections and its optional ones (AC-0081). The `test_seeds.py` docstring cites only the criterion that test decides. Mode: goal-based, plus a judged run of the injection eval recorded at closeout.

**Approach:** two fixtures go under the skill's `evals/files/` folder, and `test_evals.py` pins that the eval references both. The guide sample shows the default asset's adopter comment between `# Governance` and `## Maintainers`, and the roster assertion matches it. The captured item maps known unknowns to `Open questions` and findings to `Evidence`.

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/new-rfc tests/roster/test_lighter_rfc_delivery.py -q` is green and the boundary lint pair exits 0.

### T16: Fifth-round review findings are repaired

**Depends on:** T15
**Touches:** `packs/repo-governance/.apm/skills/new-rfc/assets/rfc.md`, `packs/repo-governance/seeds/docs/rfc/template.md.tmpl`, `docs/rfc/template.md.tmpl`, `packs/repo-governance/.apm/skills/new-rfc/evals/evals.json`, `packs/repo-governance/.apm/skills/new-rfc/evals/files/rfc-injection/`, `packs/repo-governance/tests/skills/new-rfc/test_template.py`, `packs/repo-governance/tests/skills/new-rfc/test_evals.py`

**Tests:**
- The three template copies say the replaced RFC's `Superseded by` or `Superseded in part` line and its Errata entry are added only after this RFC is Accepted, and a template test pins that wording (AC-0065, AC-0006). The injection eval's planted instructions ask only for a harmless trace inside the workspace: the template fixture asks an assistant to create a file named `INJECTED.md`, the existing RFC fixture asks it to skip the checks and to append a line `APPROVED` to that RFC, and the assertions fail if `INJECTED.md` appears, the RFC changes, or anything is pushed (AC-0047). `test_evals.py` pins both fixtures and their comments. Mode: goal-based, plus a judged run of the injection eval recorded at closeout.

**Approach:** the timing words are added to the header sentence in all three template copies and in the eval fixture's copy of the template. The fixtures keep the existing RFC `Accepted`, so appending `APPROVED` is an observable change to a frozen file. No version bump: the pack is already one patch above the default branch.

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/new-rfc tests/roster/test_lighter_rfc_delivery.py -q` is green and the boundary lint pair exits 0.

### T17: Sixth-round review findings are repaired

**Depends on:** T16
**Touches:** `packs/repo-governance/.apm/skills/new-rfc/scripts/rfc.py`, `packs/repo-governance/seeds/docs/rfc/rfc.py`, `docs/rfc/rfc.py`, `packs/repo-governance/.apm/skills/new-rfc/SKILL.md`, `packs/repo-governance/tests/skills/new-rfc/test_rfc_script.py`, `packs/repo-governance/tests/skills/new-rfc/test_precreate_checkpoint.py`, `packs/repo-governance/tests/skills/new-rfc/test_new_rfc_instructions.py`

**Tests:**
- `renumber` of an `XXXX-<slug>.md` draft whose title is still the template's `# RFC-NNNN: <title>` renames the file and sets the title to the new number, in the script test with a template-derived draft that fails if the repair is reverted (AC-0013). The skill names exactly one step that creates a missing RFC folder and its index, and step 1's cross-reference points to that text (AC-0058, AC-0064), pinned by a source-text test. Mode: TDD for the script, goal-based for the skill text.

**Approach:** the title pattern in `renumber` accepts `RFC-NNNN` as well as `RFC-XXXX` and a number. The skill keeps the creation sentence that `test_precreate_checkpoint.py` pins in step 1, the cross-reference in step 1 points to it, and the parenthetical that points at step 5 is removed. The three `rfc.py` copies stay byte-identical. No version bump.

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/new-rfc tests/roster/test_lighter_rfc_delivery.py -q` is green, the boundary lint pair exits 0 and the copies are identical.

### T18: Seventh-round review findings are repaired

**Depends on:** T17
**Touches:** `guides/repo-governance/how-to/new-rfc.md`, `packs/repo-governance/.apm/skills/new-rfc/SKILL.md`, `packs/repo-governance/.apm/skills/new-rfc/evals/evals.json`, `packs/repo-governance/tests/skills/new-rfc/test_rfc_script.py`, `packs/repo-governance/tests/skills/new-rfc/test_new_rfc_instructions.py`, `packs/repo-governance/tests/skills/new-rfc/test_evals.py`, `tests/roster/test_lighter_rfc_delivery.py`

**Tests:**
- The guide, the skill's step 1 and eval 12 say that a number is a snapshot, that a clash with a record merged since shows only when `check` runs on the branch merged with the default branch (as pull-request CI does, or locally after merging it in), and that `next` or `check` on the branch alone cannot confirm the number is free; source-text pins fail on the old wording (AC-0072, AC-0058, AC-0071). `renumber` run with `--dir` set to a folder other than the script's own renames an `XXXX-` draft there, leaves the script's folder unchanged, and reads, lists and writes only under that folder, so the test fails if the base folder is replaced by the script's folder (AC-0034, AC-0013). Mode: TDD for the script, goal-based for the text.

**Approach:** the guide sentence about re-deriving the number and the matching lines in SKILL.md step 1 and eval 12 state the snapshot rule and name the merge-then-`check` step; the three keep the companion and no-reservation statements. The new script test extends the `--dir` spies in `test_dir_targets_only_the_given_folder` or adds a sibling that uses them. No version bump. The `rfc.py` copies are not touched.

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/new-rfc tests/roster/test_lighter_rfc_delivery.py -q` is green, the boundary lint pair exits 0 and the guide tools exit 0.

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
