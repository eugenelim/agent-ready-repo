# Plan: parked approvals

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, self-host, eval harness, no internal citations, UTF-8 streams, pack-test loader rule); `_supervisor_admission.start` and `_policy_import.import_policy` as the approval seam; `_loop_guards.canonical_contract` as the only canonicalizer; `_supervisor_attempt` `_put` and `_confined_mutation.confined_create` / `confined_atomic_replace` as the store-write path; `_file_safety.list_confined_regular_files` / `read_confined_regular_file` as the store-read path; `_supervisor_git.HardenedGit` as the only Git launcher; `supervisor_harness.py` and `test_supervisor_admission.py` as the analogous integration tests.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open, and
> the run continues with every finished task still finished. Execution
> observations belong in `docs/specs/<feature>/notes/verification-ledger.md` (or
> the adopter's equivalent). A genuine error in a protected section follows the
> controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place, before or after approval, while no
> attempt is open.

## Approach

The gate digest lands first (T1), because `park` (T2), `gates` (T3), and the `start` check (T4) all call it. T4 changes every existing `start` call site in the pack tests in the same task, so the integration lane never sees a half-migrated harness. T5 is the cross-verb no-default property and runs after the three verbs exist. Guidance, evals, and docs (T6) follow the code they describe. The release (T7) is last. The riskiest part is T4: a required argument on `start` breaks every caller that is not updated, so the task's done-when is the whole supervisor integration lane, not only the new suite.

This delivery runs from the installed supervisor copy, which these edits do not change until self-host; the run's own `start` is therefore made by the pre-change `start` and takes no digest arguments.

## Constraints

- ADR-0156 D1–D7 fix the verbs, the record location, the no-default rule, the gate digest, the required `start` pins, and the controller rule; widening any of them needs a new ADR.
- RFC-0099 §7: both human gates stay, in order; "parked" means no implementation dispatch for the parked spec.
- `approval-record.v1`, `initial-plan-review.v1`, and the `approvals.jsonl` line are unchanged; `start` keeps passing the whole-file canonical digests to `import_policy`.
- The supervisor pins every file under `scripts/` at `start`, so `_supervisor_gates.py` is pinned with no pin-list edit.
- The supervisor integration lane in `.github/workflows/catalogue-tooling-ci-gates.yml` lists its suites by file; a new integration suite is added to that list.
- A pack test loads skill modules by path under a pack- and skill-unique name (`supervisor_support.load`).

## Construction tests

**Integration tests:** `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`, gated by `WORK_SUPERVISOR_INTEGRATION=1`, plus every existing supervisor integration suite after T4.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale | none — ADR-0156 committed `Accepted` before approval | ADR file | cited in `Constrained by:` |
| Maintainer procedure | T6 | content tests green | suites green at the delivery commit |
| Current architecture | T6 | command-surface row edited | row lists the parser's verbs |
| Operations (state) | T6 | state-schema row added | row present |
| Release history | T7 | version-equality assertion; fragment | release check result recorded |

## Design (LLD)

### Interfaces & contracts

Owned by: T2, T3, T4. Traces to AC-0001, AC-0009, AC-0010, AC-0015, AC-0016.

- `park <spec-dir> --gate spec-approved|plan-approved` → `{"status": "parked"|"current", "gate", "spec_dir", "spec_digest", "plan_digest", "commit"}`, exit 0; refusals use the existing `{"refusal": {"code", "owner", "detail"}}` shape, exit 1. Codes: `gate-uncommitted`, `gate-status-mismatch`, `gate-already-admitted`, `gate-changelog-shape` (owner `controller` for all four).
- `gates` (no positional) → `{"gates": [<entry>, ...]}` sorted by `spec_dir`, exit 0. Entry fields per AC-0009; `state` is `pending`, `stale`, or `invalid`; an `invalid` entry carries `spec_dir` only when the record yields a confined one, else `record` (the file name).
- `start` gains `--approved-spec-digest <64 hex>` and `--approved-plan-digest <64 hex>`, both required by argparse. A value that is not 64 lowercase hex is a usage error. A mismatch raises `Refusal("approval-digest-mismatch", "owner", ...)` before `import_policy` runs.
- Consequence text, fixed per gate, lives as constants in `_supervisor_gates.py`. `spec-approved`: approve → "the spec approver writes Status: Approved and the plan Changelog entry; the controller then parks plan-approved"; reject → "the pair returns to Draft and Drafting and is reviewed again"; no-answer → "the gate stays unapproved; the controller dispatches no implementation work for this spec". `plan-approved`: approve → "the plan approver writes Status: Approved and the Changelog entry; the controller runs start with these two digests"; reject and no-answer as above.

### Data & schema

Owned by: T2, T3. Traces to AC-0001, AC-0006, AC-0013.

- Record path: `<git-dir>/agentbundle-supervisor/gates/<sha256(spec_rel)[:16]>.json`; the `gates` name never matches the run-ID pattern the pin check lists.
- Record body: canonical JSON (sorted keys) of `{"schema_version": 1, "spec_dir", "gate", "spec_digest", "plan_digest", "commit"}`; no other key is written or accepted. A record is read with `read_confined_regular_file`, capped at 4 KiB; a record failing any field check, or whose `spec_dir` fails `_spec_rel` confinement, is `invalid`.
- `park` creates with `confined_create` and replaces with `confined_atomic_replace`; `current` is decided by byte equality of the would-be body.

### Behavior & rules

Owned by: T1. Traces to AC-0007, AC-0008, AC-0025.

- Gate digest: split the text into lines after CRLF/CR → LF; find level-two headings (`## ` at line start) outside fenced code blocks; when `## Changelog` occurs, it must occur once, be the last level-two heading, and every line after it, with HTML comments stripped, must be blank or start with `- `; otherwise raise `GateDigestRefused("gate-changelog-shape")`. Drop the section, then SHA-256 of `_loop_guards.canonical_contract(text, ac_section_only=(name != "plan.md"))`.
- Statuses for AC-0004 come from the existing status parser `_loop_guards` already loads.
- "Clean" for AC-0003: `HardenedGit` `diff --quiet HEAD -- <spec.md> <plan.md>` and `diff --quiet --cached HEAD -- ...` both exit 0, and both files are tracked at `HEAD`.
- "Admitted at `HEAD`" for AC-0005 and AC-0012: `Workspace.approvals("HEAD")` is non-empty.

### Failure, edge cases & resilience

Owned by: T2, T3, T4.

- `gates` with no `gates/` directory prints `{"gates": []}`.
- `park` and `gates` take the same pin preflight as every other verb; `gates` runs it with no spec directory, so only the store-wide checks apply (implementation-discovered: whether `_preflight` needs a no-spec path or `gates` skips it, decided by keeping every existing pin refusal reachable).
- `gates` lists `stale` for an artifact that no longer exists or now fails the Changelog shape.

### Quality attributes (NFRs)

Owned by: T3. `gates` reads each record and two artifacts per record; no Git process is launched per record.

## Tasks

### T1: Gate digest

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py`

**Tests:** TDD — unit, at `_supervisor_gates.gate_digest`
- AC-0007, AC-0008: parametrized edits over one fixture spec and one fixture plan, each asserting digest equality or inequality with the unedited text.
- AC-0025: the three shape violations (two Changelog headings, a later `##` heading, a non-list line) and a `## Changelog` inside a fenced block that is not treated as a heading.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py -q` exits 0.

### T2: `park`

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`, `.github/workflows/catalogue-tooling-ci-gates.yml`

**Tests:** TDD — integration, through `supervisor_harness.run_cli` on `make_repo` repositories
- AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, and the `park` half of AC-0025: one test per criterion; AC-0002 snapshots `git for-each-ref`, `git ls-files -s`, `HEAD`, and the working-tree bytes before and after.

**Done when:** `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py -q -k park` exits 0.

### T3: `gates`

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`

**Tests:** TDD — integration, as T2
- AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, and the `gates` half of AC-0025; AC-0013 plants each bad record kind beside one good record; AC-0014 snapshots the store bytes as well as T2's set.

**Done when:** `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py -q -k gates` exits 0.

### T4: `start` binds to the approved digests

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_admission.py`, `packs/core/tests/skills/work-loop/supervisor_harness.py`, `packs/core/tests/skills/work-loop/test_supervisor_*.py`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`

**Tests:** TDD — integration
- AC-0015, AC-0016, AC-0017, AC-0018, and the `start` half of AC-0025, in `test_supervisor_parked_gates.py`; AC-0018 runs `start` four times from one repository state with the record present, absent, truncated, and rewritten.
- `supervisor_harness.start` computes both digests with `_supervisor_gates.gate_digest`; each direct `start` argv in the other suites gains the two arguments.

**Done when:** every suite in the supervisor integration lane's file list, plus `test_supervisor_parked_gates.py`, exits 0 under `WORK_SUPERVISOR_INTEGRATION=1`, and the pack lane `python3 -m pytest packs/core/tests/skills/work-loop -q` exits 0.

### T5: A parked gate is never approved by default

**Depends on:** T2, T3, T4

**Touches:** `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`

**Tests:** TDD — integration
- AC-0019: one test that parks, runs `gates` three times, re-parks, then runs `start` with no digests, with digests from a `stale` entry after a spec edit, and with digests of the pre-edit revision; after each, `approvals.jsonl` is absent and both `Status:` lines equal their parked values.

**Done when:** `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py -q -k never_default` exits 0.

### T6: Guidance, evals, and docs

**Depends on:** T2, T3, T4

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/references/supervisor.md`, `packs/core/.apm/skills/work-loop/references/session-resumption.md`, `packs/core/.apm/skills/work-loop/references/state-schema.md`, `packs/core/.apm/skills/work-loop/evals/evals.json`, `docs/architecture/work-loop-execution-supervisor.md`, `packs/core/tests/skills/work-loop/test_parked_gates_guidance.py`

**Tests:** goal-based — content test over the shipped files
- AC-0020, AC-0021: substring pins on the verb table rows and the step-12 rules.
- AC-0022: the eval case's id and assertions are present, and the existing eval-schema test over `evals.json` stays green.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_parked_gates_guidance.py -q` exits 0 and the existing work-loop eval tests exit 0.

### T7: Core release

**Depends on:** T1, T2, T3, T4, T5, T6

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/*.md`, adapter projections

**Tests:** no stub (goal-based — release check)
- AC-0023: the version-equality assertion the pack suite carries, and `tools/check-core-release.py`.
- AC-0024: the catalogue commands' exit status and a clean tree after self-host.

**Done when:** `PYTHONPATH=packages/agentbundle python3 -m agentbundle catalogue lint --root . --deep` and `... catalogue verify --root .` exit 0 after `make build-self && make bootstrap-sites`, and `git status --short` is empty.

## Rollout

Ships in the next core patch. Every controller that calls `start` must pass the two digests after upgrading; the refusal is a usage error naming both arguments. A run already admitted is unaffected until its controller next calls `start`, which then needs the digests of the current pair.

## Risks

- A controller can still type digests a human never gave. The pins narrow what `start` admits to a revision someone quoted; they do not authenticate the human, which the authority reference already names.
- Another open change edits the same supervisor scripts; whichever merges second rebases on it and rebuilds the projections.

## Changelog
