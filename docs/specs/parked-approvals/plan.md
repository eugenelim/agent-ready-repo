# Plan: parked approvals

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, self-host, eval harness, no internal citations, UTF-8 streams, pack-test loader rule); `_supervisor_admission.start` and `_policy_import.import_policy` as the approval seam; `_loop_guards.canonical_contract` as the only canonicalizer; `_confined_mutation.confined_create` / `confined_atomic_replace` as the store-write path; `_file_safety.read_confined_regular_file` as the store-read path; `_supervisor_git.HardenedGit` as the only Git launcher and `_supervisor_commit.GitPort.show` as the commit read; `supervisor_harness.py` and `test_supervisor_admission.py` as the analogous integration tests.

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

- ADR-0157 D1–D7 fix the verbs, the record location, the no-default rule, the gate digest, the required `start` pins, and the controller rule; widening any of them needs a new ADR.
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
| Decision rationale | none — ADR-0157 committed `Accepted` before approval | ADR file | cited in `Constrained by:` |
| Maintainer procedure | T6 | content tests green | suites green at the delivery commit |
| Current architecture | T6 | command-surface row edited | row lists the parser's verbs |
| Operations (state) | T6 | state-schema row added | row present |
| Release history | T7 | version-equality assertion; fragment | release check result recorded |

## Design (LLD)

### Interfaces & contracts

Owned by: T2, T3, T4. Traces to AC-0001, AC-0009, AC-0010, AC-0015, AC-0016.

- `park <spec-dir> --gate spec-approved|plan-approved --intent code|spec-plan --code-trust trusted|untrusted` → `{"status": "parked"|"current", "gate", "spec_dir", "spec_digest", "plan_digest", "intent", "code_trust", "commit"}`; `intent` is the argument, refused `intent-mismatch` when `_supervisor_projector.terminal_intent` of the spec is declared and differs, exactly as `start` refuses it, exit 0; refusals use the existing `{"refusal": {"code", "owner", "detail"}}` shape, exit 1. Codes, checked in AC-0029's order; owner `controller` for all except `intent-mismatch` and `ambiguous-reference`, which keep `start`'s owners.
- `gates` (no positional) → `{"gates": [<entry>, ...]}` sorted by `spec_dir` then `record`, exit 0. Valid entries per AC-0009; invalid entries per AC-0013.
- `start` gains optional argparse arguments `--approved-spec-digest <64 hex>` and `--approved-plan-digest <64 hex>`, format-checked by argparse on every path (AC-0036). In `_main`, before `check_pins` and `run_lock` (both write: the orphan mark and `<spec>/.supervisor/.gitignore`), a read-only pre-check decides whether `start` would record a pair, from the committed `approvals.jsonl` at `HEAD` and the derived envelope, intent, and trust: no pair yet, or a latest pair that differs, means it would. On that path the pre-check reads `spec.md` and `plan.md` once each and refuses in AC-0035's order from those bytes. `admission.start` receives the bytes and the pre-check's decision. Under the lock it makes its own record-or-current decision as today; on the record path it refuses `approval-digest-required` unless it holds pre-checked bytes and the envelope fingerprint, intent, and trust it derives equal the pre-check's (AC-0037). It then passes the whole-file canonical digests of those pre-checked bytes to `import_policy` as `approved_spec_digest` and `approved_plan_digest`, and just before `build_commit` re-reads both files and refuses `approval-digest-mismatch` unless the bytes are identical (AC-0034). On the `current` path the digests are ignored.
- Consequence text, fixed per gate, lives as constants in `_supervisor_gates.py`. `spec-approved`: approve → "the spec approver writes Status: Approved and the plan Changelog entry; the controller then parks plan-approved"; reject → "the pair returns to Draft and Drafting and is reviewed again"; no-answer → "the gate stays unapproved; the controller dispatches no implementation work for this spec". `plan-approved`: approve → "the plan approver writes Status: Approved and the Changelog entry; the controller runs start with the spec digest from the spec approver's own answer and the plan digest from the plan approver's own answer"; reject and no-answer as above.

### Data & schema

Owned by: T2, T3. Traces to AC-0001, AC-0006, AC-0013.

- Record path: `<git-dir>/agentbundle-supervisor/gates/<sha256(spec_rel)[:16]>.json`; the `gates` name never matches the run-ID pattern the pin check lists.
- Record body: canonical JSON (sorted keys) of `{"schema_version": 1, "spec_dir", "gate", "intent", "code_trust", "spec_digest", "plan_digest", "commit"}`, field shapes per AC-0031. `gates` lists `gates/` with one `os.scandir` level and classifies each entry by `lstat` on its own: a non-regular entry, a subdirectory, or a file over 4096 bytes is `invalid` without being read; a regular file is read with `_file_safety.read_confined_regular_file(gates_dir, path, max_bytes=4096)` and its `spec_dir` passes both AC-0032 and `_spec_rel` confinement. `list_confined_regular_files` is not used, because one bad entry would fail the whole listing.
- `park` creates `gates/` with the existing `ensure_directory` helper under the Git directory and the record with `_confined_mutation.confined_create`, and replaces it with `confined_atomic_replace`; the run-store helpers (`Attempts._put`, `ensure_store`) are not used, because they accept only run IDs; `current` is decided by byte equality of the would-be body without its `commit`, so gate, digests, intent, and code trust all count, and only while `GitPort.show` still reads both artifacts at the recorded commit with the recorded gate digests; otherwise the record is replaced (AC-0006).
- `park --gate plan-approved` reads the existing record first and requires its `spec_digest` to equal the live spec gate digest (AC-0030); the replacement keeps that value, so the spec approver's digest survives every later `plan-approved` re-park.
- For each valid record, `gates` reads `<commit>:<spec-dir>/spec.md` and `plan.md` through `GitPort.show` (`_supervisor_commit.py`, which runs with `--no-replace-objects` through `HardenedGit`) with the full commit ID and literal path, computes their gate digests, and compares them and the working-tree gate digests with the record (AC-0011).

### Behavior & rules

Owned by: T1. Traces to AC-0007, AC-0008, AC-0025.

- Gate digest: decode the bytes as strict UTF-8 and refuse `GateDigestRefused("gate-unsafe-content")` on failure or when a character fails AC-0039; the hidden-character half calls `is_hidden_char` from `lint-knowledge.py`, loaded by path as a sibling, so one definition serves both; the Cc, U+2028/U+2029, and U+FFF9 to U+FFFB checks are added in `_supervisor_gates.py`; then split the text into lines after CRLF/CR → LF; find level-two headings (`## ` at line start) outside fenced code blocks; when `## Changelog` occurs, it must occur once, be the last level-two heading, and every line after it, with HTML comments stripped, must be blank, start with `- `, or be an indented continuation of a list item; otherwise raise `GateDigestRefused("gate-changelog-shape")`. Drop the section, then SHA-256 of `_loop_guards.canonical_contract(text, ac_section_only=(name != "plan.md"))`.
- Statuses for AC-0004 come from the existing status parser `_loop_guards` already loads.
- "Clean" for AC-0003, without writing the index: `ls-files -s -- <path>` must print exactly one stage-0 entry; its blob must equal `rev-parse HEAD:<path>`; and `hash-object --no-filters --stdin`, fed the bytes `park` already read, must equal that blob either for the raw bytes or for the bytes with CRLF turned into LF. All three run through `HardenedGit` unchanged; none of them takes Git's optional index lock, so no extra environment is passed. No `diff` or `status` runs, because they refresh the index's stat cache.
- "Admitted" for AC-0005 and AC-0012: the latest line of `Workspace.approvals("HEAD")` carries `envelope.envelope_fingerprint` equal to `_acceptance.derive_envelope` of the spec's current references, `terminal_intent` equal to the given intent, and `code_trust` equal to the given trust: the same three values `start` compares.

### Failure, edge cases & resilience

Owned by: T2, T3, T4.

- `gates` with no `gates/` directory prints `{"gates": []}`.
- Entry path: `park` takes the same preflight, `_spec_rel`, `Workspace`, and ref-storage checks as every verb. `gates` takes no spec directory, so `_main` branches on it before `args.spec_dir` is read; it runs no `_preflight` pin check, because it writes nothing and every approval still passes `start`'s own pin check, and it builds a read-only `Workspace` per valid record only to read that spec's `approvals.jsonl` at `HEAD`. The untrusted-unsafe-host check skips `gates`, which writes nothing, and judges `park` as `trusted`: on a host with path-checked writes a racer could redirect `park`'s write, but that lands only a fixed-name file whose body is supervisor-derived and holds no controller free text, and an `unsafe` host refuses the write anyway. `test_supervisor_untrusted_unsafe_host.py`'s three every-verb walks exempt `park` and `gates`, and a separate test runs both, with full argv, on an unsafe host with an untrusted pair at `HEAD` and asserts neither refuses `untrusted-unsafe-host`.
- `gates` lists `stale` for an artifact that no longer exists or has no gate digest (AC-0025, AC-0039).

### Quality attributes (NFRs)

Owned by: T3. `gates` launches two `git show` reads per valid record and none per invalid record.

## Tasks

### T1: Gate digest

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py`

**Tests:** TDD — unit, at `_supervisor_gates.gate_digest`
- AC-0025 also covers an indented continuation line, which keeps the digest.
- AC-0039: one case per class (invalid UTF-8, an ESC sequence, a bare CR, DEL, a C1 control, a bidi override, a zero-width space, a tag-character payload, a variation-selector payload, a Mongolian free variation selector, U+2028, U+FFF9), each refusing `gate-unsafe-content`, and a tab and a CRLF, which keep the digest.
- AC-0007, AC-0008: parametrized edits over one fixture spec and one fixture plan, each asserting digest equality or inequality with the unedited text.
- AC-0025: the three shape violations (two Changelog headings, a later `##` heading, a non-list line) and a `## Changelog` inside a fenced block that is not treated as a heading.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py -q` exits 0.

### T2: `park`

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`, `packs/core/tests/skills/work-loop/test_supervisor_untrusted_unsafe_host.py`, `.github/workflows/catalogue-tooling-ci-gates.yml`

**Tests:** TDD — integration, through `supervisor_harness.run_cli` on `make_repo` repositories
- AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0026, AC-0029, AC-0030, AC-0032, AC-0038, AC-0039: one test per criterion, each named `test_t2_…`; AC-0002 snapshots `git for-each-ref`, the index file's bytes, `HEAD`, and the bytes of every working-tree file, ignored files included, before and after, on a repository whose index stat data is stale; AC-0005 also parks a spec whose latest pair differs only in envelope fingerprint, only in terminal intent, and only in code trust; AC-0003 includes a CRLF working tree of an LF blob, which parks, and an unmerged index entry, which refuses; AC-0006 re-parks with a different code trust, and after the recorded commit is rewritten away and pruned, and checks the record is replaced each time; AC-0038 parks a spec with no Terminal Intent section and refuses one with two; AC-0029 builds inputs that break two rules at once; AC-0030 edits the spec body after `spec-approved` and commits it with `Status: Approved`.

**Done when:** `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py -q -k t2_` and `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_untrusted_unsafe_host.py -q` exit 0.

### T3: `gates`

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`, `packs/core/tests/skills/work-loop/test_supervisor_untrusted_unsafe_host.py`

**Tests:** TDD — integration, as T2, each test named `test_t3_…`
- AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0031; the three every-verb walks in `test_supervisor_untrusted_unsafe_host.py` exempt `gates`, and the separate full-argv test covers it; AC-0039's `gates` clause lists an entry `stale` after the spec gains a zero-width space; AC-0011 includes a planted well-formed record whose digests are the live ones and whose commit is an older revision, which lists `stale`; AC-0013 and AC-0031 plant each bad record kind, including shell metacharacters in `spec_dir` and a non-hex `commit`, beside one good record; AC-0009 plants a `refs/replace/` entry for the spec blob, `pager.cat-file` and `core.pager` config, and a promisor remote with `core.sshCommand` while the blob is deleted (the command fails and the planted program never runs), checks the listing and digests are unchanged, and runs each `read` command with a pseudo-terminal as stdout and checks its output equals the blob; AC-0011 plants a well-formed record under another name and a `plan-approved` record for a `Draft` spec, both not `pending`; AC-0013 also plants a symlink, a subdirectory, and a 5000-byte padded valid body; AC-0014 snapshots the store bytes as well as T2's set.

**Done when:** `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py -q -k t3_` and `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_untrusted_unsafe_host.py -q` exit 0.

### T4: `start` binds to the approved digests

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_admission.py`, `packs/core/tests/skills/work-loop/supervisor_harness.py`, `packs/core/tests/skills/work-loop/test_supervisor_*.py`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`, `tests/roster/test_t9a_clean_env_fence.py`

**Tests:** TDD — integration, each test named `test_t4_…`
- AC-0015, AC-0016, AC-0017, AC-0018, AC-0027, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037, and AC-0039's `start` clause (owner and no appended line, and first in AC-0035's order) in `test_supervisor_parked_gates.py`; the no-write assertions snapshot the store and every file under the spec directory, ignored files included; AC-0016 asserts no write on both the first-admission and the re-approval path; AC-0018 runs `start` four times from one repository state with the record present, absent, truncated, and rewritten; AC-0033 admits, makes an in-envelope plan edit, and re-runs `start` three ways; AC-0034 patches the seam between `import_policy` and `build_commit` to make a whitespace-only edit to `plan.md`; AC-0037 patches the seam between the pre-check and `run_lock` twice: once so the pre-check answers `current` and the locked decision records, once so a cited record changes while `spec.md` and `plan.md` bytes stay the same.
- `supervisor_harness.start` computes both digests with `_supervisor_gates.gate_digest`; each direct `start` argv in the other suites that records a pair gains the two arguments.

**Done when:** under `WORK_SUPERVISOR_INTEGRATION=1`, every suite in the supervisor integration lane's file list plus `test_supervisor_parked_gates.py`, `test_supervisor_untrusted_unsafe_host.py`, and `test_proof_by_run.py` exits 0; the pack lane `python3 -m pytest packs/core/tests/skills/work-loop -q` exits 0; and `python3 -m pytest tests/roster/test_t9a_clean_env_fence.py -q` exits 0.

### T5: A parked gate is never approved by default

**Depends on:** T2, T3, T4

**Touches:** `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`

**Tests:** TDD — integration, test named `test_t5_…`
- AC-0019: one test that parks, runs `gates` three times, sets `Implementing` and `Executing` with no answer, edits the spec body, commits, and runs `start` with the parked record's digests and with none; after each, `approvals.jsonl` is absent.

**Done when:** `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py -q -k t5_` exits 0.

### T6: Guidance, evals, and docs

**Depends on:** T2, T3, T4

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/references/supervisor.md`, `packs/core/.apm/skills/work-loop/references/session-resumption.md`, `packs/core/.apm/skills/work-loop/references/state-schema.md`, `packs/core/.apm/skills/work-loop/evals/evals.json`, `packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md`, `docs/architecture/work-loop-execution-supervisor.md`, `docs/architecture/loop-infrastructure.md`, `packs/core/tests/skills/work-loop/test_parked_gates_guidance.py`

**Tests:** goal-based — content test over the shipped files
- AC-0020, AC-0021: substring pins on the verb table rows and the step-12 rules.
- AC-0022: the eval case's id and assertions are present, and the existing eval-schema test over `evals.json` stays green.
- Every `start` command line in the Touches files names both digest arguments; the existing `evals.json` case that shows `start` is updated.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_parked_gates_guidance.py -q` exits 0 and the existing work-loop eval tests exit 0.

### T7: Core release

**Depends on:** T1, T2, T3, T4, T5, T6

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/*.md`, adapter projections

**Tests:** no stub (goal-based — release check)
- AC-0023: the version-equality assertion the pack suite carries, and `tools/check-core-release.py`.
- AC-0024: the catalogue commands' exit status and a clean tree after self-host.

**Done when:** `PYTHONPATH=packages/agentbundle python3 -m agentbundle catalogue lint --root . --deep` and `... catalogue verify --root .` exit 0 after `make build-self && make bootstrap-sites`, and `git status --short` is empty.

## Rollout

Ships in the next core patch. Every controller that records an approval with `start` must pass the two digests after upgrading; the refusal `approval-digest-required` names both arguments. A run already admitted answers `current` as before and needs no digests until an amendment asks for re-approval.

## Risks

- A controller can still type digests a human never gave; the spec's Agent Rules state that limit, and the authority references name the humans.
- Another open change edits the same supervisor scripts; whichever merges second rebases on it and rebuilds the projections.

## Changelog

- 2026-11-04: spec approved by eugenelim (scope).
- 2026-11-04: plan approved by eugenelim (build strategy).
