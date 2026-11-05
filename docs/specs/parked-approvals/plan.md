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

Owned by: T1, T10. Traces to AC-0007, AC-0008, AC-0025.

- Gate digest: decode the bytes as strict UTF-8 and refuse `GateDigestRefused("gate-unsafe-content")` on failure or when a character fails AC-0039 (the hidden-character half calls `is_hidden_char` from `lint-knowledge.py`, loaded by path as a sibling; the Cc, U+2028/U+2029, and U+FFF9 to U+FFFB checks and the invisible budget, length basis 2,000, live in `_supervisor_gates.py`); normalize CRLF/CR to LF; in the approval-entry region after the last line whose `str.rstrip()` form is exactly `## Changelog`, drop every line whose `str.rstrip()` form fully matches the approval-entry pattern `^- [0-9]{4}-[0-9]{2}-[0-9]{2}: (spec|plan|amendment) approved by [A-Za-z0-9][A-Za-z0-9-]{0,38}( \((scope|build strategy|scope and build strategy)\))?\.?$` (compiled with `re.ASCII`); the approval-entry region ends at the first later line whose `lstrip()` form starts with `#`, three backticks, or three tildes; inside the region only, fold each run of blank lines into one and drop blank lines at its end, and keep every line from the region's end on byte for byte; then SHA-256 of `_loop_guards.canonical_contract(text, ac_section_only=(name != "plan.md"))`. No Markdown structure is parsed. AC-0025 is the one statement of the grammar; this pattern implements it.
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
- AC-0039: one case per class (invalid UTF-8, an ESC sequence, a bare CR, DEL, a C1 control, a bidi override, a zero-width space, a tag-character payload, a variation-selector payload, a Mongolian free variation selector, U+2028, U+FFF9), each refusing `gate-unsafe-content`, and a tab and a CRLF, which keep the digest.
- AC-0007, AC-0008: parametrized edits over one fixture spec and one fixture plan, each asserting digest equality or inequality with the unedited text.
- AC-0025: an approval-entry line after the last `## Changelog` line is dropped and keeps the digest; the same line before that heading, a wrapped approval entry, and any other line under `## Changelog` (HTML, a comment, a fence, a heading) change the digest; no input refuses `gate-changelog-shape`.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py -q` exits 0.

### T2: `park`

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`, `packs/core/tests/skills/work-loop/test_supervisor_untrusted_unsafe_host.py`, `.github/workflows/catalogue-tooling-ci-gates.yml`

**Tests:** TDD — integration, through `supervisor_harness.run_cli` on `make_repo` repositories
- AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0029, AC-0030, AC-0032, AC-0038, AC-0039: one test per criterion, each named `test_t2_…`; AC-0002 snapshots `git for-each-ref`, the index file's bytes, `HEAD`, and the bytes of every working-tree file, ignored files included, before and after, on a repository whose index stat data is stale; AC-0005 also parks a spec whose latest pair differs only in envelope fingerprint, only in terminal intent, and only in code trust; AC-0003 includes a CRLF working tree of an LF blob, which parks, and an unmerged index entry, which refuses; AC-0006 re-parks with a different code trust, and after the recorded commit is rewritten away and pruned, and checks the record is replaced each time; AC-0038 parks a spec with no Terminal Intent section and refuses one with two; AC-0029 builds inputs that break two rules at once; AC-0030 edits the spec body after `spec-approved` and commits it with `Status: Approved`.

**Done when:** `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py -q -k t2_` and `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_untrusted_unsafe_host.py -q` exit 0.

### T3: `gates`

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`, `packs/core/tests/skills/work-loop/test_supervisor_untrusted_unsafe_host.py`

**Tests:** TDD — integration, as T2, each test named `test_t3_…`
- AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0031; the three every-verb walks in `test_supervisor_untrusted_unsafe_host.py` exempt `gates`, and the separate full-argv test covers it; AC-0039's `gates` clause lists an entry `stale` after the spec gains a zero-width space; AC-0011 includes a planted well-formed record whose digests are the live ones and whose commit is an older revision, which lists `stale`; AC-0013 and AC-0031 plant each bad record kind, including shell metacharacters in `spec_dir` and a non-hex `commit`, beside one good record; AC-0009 plants a `refs/replace/` entry for the spec blob and `pager.cat-file` and `core.pager` config and checks the listing and digests are unchanged and `pending`, then adds a promisor remote with `core.sshCommand` while the blob is deleted (the command fails, the planted program never runs, and every entry lists `stale`), and runs each `read` command with a pseudo-terminal as stdout and checks its output equals the blob; AC-0011 plants a well-formed record under another name and a `plan-approved` record for a `Draft` spec, both not `pending`; AC-0013 also plants a symlink, a subdirectory, and a 5000-byte padded valid body; AC-0014 snapshots the store bytes as well as T2's set.

**Done when:** `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py -q -k t3_` and `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_untrusted_unsafe_host.py -q` exit 0.

### T4: `start` binds to the approved digests

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_admission.py`, `packs/core/tests/skills/work-loop/supervisor_harness.py`, `packs/core/tests/skills/work-loop/test_supervisor_*.py`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`, `tests/roster/test_t9a_clean_env_fence.py`

**Tests:** TDD — integration, each test named `test_t4_…`
- AC-0015, AC-0016, AC-0017, AC-0018, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037, and AC-0039's `start` clause (owner and no appended line, and first in AC-0035's order) in `test_supervisor_parked_gates.py`; the no-write assertions snapshot the store and every file under the spec directory, ignored files included; AC-0016 asserts no write on both the first-admission and the re-approval path; AC-0018 runs `start` four times from one repository state with the record present, absent, truncated, and rewritten; AC-0033 admits, makes an in-envelope plan edit, and re-runs `start` three ways; AC-0034 patches the seam between `import_policy` and `build_commit` to make a whitespace-only edit to `plan.md`; AC-0037 patches the seam between the pre-check and `run_lock` twice: once so the pre-check answers `current` and the locked decision records, once so a cited record changes while `spec.md` and `plan.md` bytes stay the same.
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

### T8: Code-review repairs

**Depends on:** T1, T2, T3, T4, T5, T6

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_admission.py`, `packs/core/.apm/skills/work-loop/references/supervisor.md`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`, `packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py`, `packs/core/tests/skills/work-loop/test_supervisor_cutover_source_checks.py`

**Tests:** TDD — unit and integration; every new test named `test_t8_…`
- qe-1 (AC-0015, AC-0035): `start` with no digests on a `Draft` spec refuses `spec-not-approved`, as before; the pre-check runs `start`'s read-only refusals (authority-ref format, intent and code-trust values, untrusted-unsafe-host, Git config, statuses) before any digest refusal.
- sec-2 (AC-0039): a run of three U+FE0F and an alternating U+FE0E/U+FE0F sequence over the knowledge lint's invisible budget refuse `gate-unsafe-content`; one emoji VS16 keeps the digest.
- sec-3 (AC-0009, AC-0011): in a partial clone or with a promisor remote, `park` refuses and `gates` lists `stale` before any record-named commit is read; `park`'s commit read passes `no_lazy_fetch`.
- qe-2 (AC-0014): a failing sibling load under `gates` prints one JSON `internal-error` refusal.
- qe-3 (AC-0020): the cutover source scan collects codes raised through `refuse`, `refusal`, `digest_refusal`, and `GateDigestRefused`, and still finds every row.
- qe-8 (AC-0029): an uncommitted-and-admitted case expects `gate-uncommitted`; an unsafe-path-and-doubled-Terminal-Intent case expects `gate-unsafe-path`.
- qe-9 (AC-0008): byte changes outside the spec's AC section and in a plan body each change the digest.
- qe-11 (AC-0009): the pseudo-terminal read loop has a deadline that kills the child and fails, and the child's stdin is `/dev/null`.
- qe-13 (AC-0036): the malformed-digest cases share one fresh and one admitted repository.
- adv-7, adv-10 (AC-0020): the reference names the exact `git --no-pager --no-replace-objects --no-lazy-fetch cat-file blob` commands, and says no flag may be removed.
- qe-16, sec-6: `is_hidden_char` is typed `Callable[[str], bool]` with no ignore; the park-trusted docstring states the path-checked-host race window and why it is acceptable.

**Done when:** under `WORK_SUPERVISOR_INTEGRATION=1`, `test_supervisor_parked_gates.py`, `test_supervisor_untrusted_unsafe_host.py`, `test_supervisor_admission.py`, and `test_supervisor_cutover_source_checks.py` exit 0; `test_supervisor_gates_digest.py` and `test_parked_gates_guidance.py` exit 0; and `make lint-ruff lint-mypy` exits 0.

### T9: Second code-review repairs

**Depends on:** T8

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`, `packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py`, `packs/core/tests/skills/work-loop/test_supervisor_cutover_source_checks.py`

**Tests:** TDD — unit and integration; every new test named `test_t9_…`
- adv2-1 (AC-0015): with an open attempt carrying residue, `start` with or without digests writes no `.refused.json` and no security event before the locked path, and gives the non-standing `attempt-residue` detail; the pre-check uses `Attempts.standing_refusal()`, never `guard`.
- sec2-3 (AC-0039): `invisible_budget` takes a fixed per-artifact cap; a padded artifact with many interleaved VS16 refuses `gate-unsafe-content`, and one emoji VS16 keeps the digest.
- qe2-1 (AC-0020): the cutover scan's sentinel requires `gate-unsafe-path`, `gate-unsafe-content`, and `approval-digest-required`.
- qe2-2 (AC-0015): `start` without digests on a repository with a code-running Git config key refuses `unsupported-git-config`.
- qe2-3 (AC-0009, AC-0011): under the replace ref and pager settings alone, `gates` equals the baseline listing with state `pending`; after the partial-clone settings every entry lists `stale`.

**Done when:** under `WORK_SUPERVISOR_INTEGRATION=1`, `test_supervisor_parked_gates.py`, `test_supervisor_untrusted_unsafe_host.py`, `test_supervisor_admission.py`, `test_supervisor_attempt.py`, and `test_supervisor_cutover_source_checks.py` exit 0; `test_supervisor_gates_digest.py` and `test_parked_gates_guidance.py` exit 0; and `make lint-ruff lint-mypy` exits 0.

### T10: Approval-entry grammar

**Depends on:** T9

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py`

**Tests:** TDD — unit, at `_supervisor_gates.gate_digest`; every test named `test_t10_…`
- AC-0025: the template form `- 2026-11-04: spec approved by example-owner`, the same with ` (scope).`, a plan entry with ` (build strategy)`, and an amendment entry with ` (scope and build strategy).` each keep the digest when added after the last `## Changelog` line, also with trailing spaces or a trailing U+00A0; a handle of 40 characters, a handle with `_`, a reason outside the set, non-ASCII digits in the date, and any extra text each change the digest.
- AC-0007: adding a first approval entry with a separating blank line, and adding a second after an existing one, keep the digest; a run of extra blank lines folds to one.
- AC-0008: removing a blank line between two paragraphs changes the digest.
- AC-0039: the invisible budget's length basis is 2,000 characters; 40 emoji presentation selectors in one artifact keep the digest and 41 refuse.

**Done when:** `test_supervisor_gates_digest.py` exits 0 and `make lint-ruff lint-mypy` exits 0.

### T11: Approver surfaces and review must-fixes

**Depends on:** T10

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/.apm/skills/work-loop/references/supervisor.md`, `packs/core/.apm/skills/work-loop/references/pre-execute-review.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/new-spec/assets/plan.md`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`, `packs/core/tests/skills/work-loop/test_parked_gates_guidance.py`, `packs/core/tests/skills/work-loop/test_supervisor_cutover_source_checks.py`, `packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py`

**Tests:** TDD — goal-based content tests and integration; every new test named `test_t11_…`
- AC-0021, AC-0020: the new-spec plan template, `SKILL.md`, `supervisor.md`, `pre-execute-review.md`, and the `gates` answer text each state the approval-entry form or point to the supervisor reference's one statement of it; the reference has no `gate-changelog-shape` row and every remaining refusal code has one.
- AC-0029: an input that is both unsafe-content and spec-changed under `park --gate plan-approved` refuses `gate-unsafe-content`.
- AC-0035: a `start` input with unsafe content and no digests refuses `gate-unsafe-content`.
- AC-0039: every `gate-unsafe-content` refusal detail names the artifact and the first offending line number, and the budget comment states the 40-character bound.
- Test fixtures use a generic placeholder handle, never a real account name.

**Done when:** `test_supervisor_gates_digest.py` and `test_parked_gates_guidance.py` exit 0; under `WORK_SUPERVISOR_INTEGRATION=1`, `test_supervisor_parked_gates.py`, `test_supervisor_untrusted_unsafe_host.py`, `test_supervisor_admission.py`, and `test_supervisor_cutover_source_checks.py` exit 0; and `make lint-ruff lint-mypy` exits 0.

### T12: Third code-review repairs

**Depends on:** T11

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/.apm/skills/work-loop/references/supervisor.md`, `packs/core/.apm/skills/work-loop/references/pre-execute-review.md`, `packs/core/.apm/skills/new-spec/assets/plan.md`, `packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py`, `packs/core/tests/skills/work-loop/test_parked_gates_guidance.py`, `packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py`

**Tests:** TDD — unit and goal-based; every new test named `test_t12_…`
- AC-0007, AC-0025 (adv5-2, sec5-1): a trailing space on the real `## Changelog` line keeps the digest with an entry present; an earlier exact `## Changelog` inside a fenced example does not become the boundary when the real heading gains a trailing space.
- AC-0007, AC-0008 (sec5-2): extra blank lines after the last `## Changelog` line keep the digest; a changed blank-line count before it, including inside a fenced stub, changes the digest.
- AC-0025 (qe5-1): with two `## Changelog` lines, an entry after the first but before the last changes the digest, and each placement case compares texts that differ only by the entry.
- AC-0007 (qe5-2): a file with no final newline and the same file with trailing blank lines after the heading have the same digest.
- AC-0025 (qe5-4): a 39-character handle and handles starting with an uppercase letter or a digit keep the digest.
- AC-0039 (qe5-3, qe5-5): refusal details assert literal line numbers, including a budget-overrun refusal.
- AC-0021 (adv5-1, adv5-3, adv5-5, qe5-8): `pre-execute-review.md` and the new-spec plan template state AC-0021's rules or point to the supervisor reference for them; every surface that paraphrases the entry form quotes the reason set (`scope`, `build strategy`, `scope and build strategy`), the optional final period, and the `amendment` kind exactly; the `gates` answer text is asserted through `ANSWERS`, and the docstring cites AC-0021.
- qe5-6, qe5-7: `park` picks the first refusal as `start` does; the lone-CR comment describes only the CRLF case.

**Done when:** `test_supervisor_gates_digest.py` and `test_parked_gates_guidance.py` exit 0; under `WORK_SUPERVISOR_INTEGRATION=1`, `test_supervisor_parked_gates.py` exits 0; the new-spec tests exit 0; and `make lint-ruff lint-mypy` exits 0.

### T13: Approval-entry region end and budget test

**Depends on:** T12

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/.apm/skills/work-loop/references/supervisor.md`, `packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py`

**Tests:** TDD — unit; every new test named `test_t13_…`
- AC-0025, AC-0008 (sec6-1): with a `### T<n>` task and a stub fence placed directly after the last `## Changelog` line, a blank-line change inside the stub and an approval-shaped line inside the stub each change the digest; a fence opener (backticks or tildes, indented up to any depth) also ends the region.
- AC-0007, AC-0025: an amendment approval entry added after history lines inside the region keeps the digest; a non-approval history line added there changes it.
- AC-0039 (qe6-1): the budget-overrun unit test spreads the selectors over several lines and asserts the literal line of the first one.
- The supervisor reference's statement of the entry form says where the region ends.

**Done when:** `test_supervisor_gates_digest.py` and `test_parked_gates_guidance.py` exit 0; under `WORK_SUPERVISOR_INTEGRATION=1`, `test_supervisor_parked_gates.py` exits 0; and `make lint-ruff lint-mypy` exits 0.

### T14: Region-end test gaps

**Depends on:** T13

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_gates.py`, `packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py`

**Tests:** TDD — unit; every new test named `test_t14_…`
- AC-0007 (qe7-1): an approval entry plus a trailing blank line placed directly before a later heading, and the same before a fence, keep the digest; the test reds when blank lines at the region end are no longer dropped.
- AC-0025 (qe7-2): the fence-opener test's second assertion changes only blank lines after the fence, so it reds when folding reaches past the region end.
- adv7-2: the region-join docstring states the condition the code applies.

**Done when:** `test_supervisor_gates_digest.py` exits 0 and `make lint-ruff lint-mypy` exits 0.

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
- 2026-11-04: amendment approved by eugenelim (scope and build strategy).
- 2026-11-04: amendment approved by eugenelim (scope and build strategy).
- 2026-11-04: amendment approved by eugenelim (scope and build strategy).
