# Spec: proof-by-run evidence

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0155, ADR-0154, ADR-0144
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** contracts/delivery/finding-assessment.v1.schema.json, contracts/delivery/evidence-receipt.v1.schema.json, contracts/delivery/finding-disposition.v1.schema.json (all consumed unchanged)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

In a full-mode `work-loop` run, a reviewer finding that carries a command gets a `finding-assessment.v1` record built from the controller's run of that command at the current subject commit, made while the finding's `assess-finding` request is open: a run showing the defect yields `supported`, a run not showing it yields `unsupported-opinion`, and the record's evidence reference is the controller's attestation binding the command, exit status, and output digests to that commit, which the supervisor checks for consistency before it admits the record. A base-versus-change question ("did this change add it, or was it already on the base?") is settled by one run of the built-in `git-history` Evidence gate catalog entry, which computes the change's base itself and refuses any path outside the change.

## What Changes

- A proof-by-run predicate and its consistency check — `packs/core/.apm/skills/work-loop/scripts/_review_assessment.py`.
- The supervisor checks a proof-by-run assessment before admitting it — `packs/core/.apm/skills/work-loop/scripts/_supervisor_readiness.py`.
- A controller CLI with two subcommands, `proof-run` and `git-history`, and the git-history module behind it — `packs/core/.apm/skills/work-loop/scripts/evidence-gate.py`, `packs/core/.apm/skills/work-loop/scripts/_git_history.py`.
- The built-in `git-history` entry joins the Evidence gate catalog — `references/finding-adjudication.md` § Bounded evidence retry.
- FIX step 1 points at the recorded assessment; the supervisor reference's Review section names the predicate — `SKILL.md`, `references/supervisor.md`.
- Eval cases — `packs/core/.apm/skills/work-loop/evals/evals.json`.
- The after-fix run binding is routed to the contract owner as a captured amendment request — `docs/product/captured/`.
- The core version, a core changelog fragment, and the self-hosted projections.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | How an agent records a run and asks a Git fact | `packs/core/.apm/skills/work-loop/SKILL.md` FIX, `references/finding-adjudication.md`, `references/supervisor.md` | core pack maintainers | content tests green | suites green at the delivery commit; projections regenerated |
| Interface compatibility | Records stay in existing contracts | `contracts/delivery/finding-assessment.v1.schema.json`, `contracts/delivery/evidence-receipt.v1.schema.json`, `contracts/delivery/finding-disposition.v1.schema.json`, consumed unchanged | `structured-review-boundary` and `acceptance-authority-and-evidence` contract owners | roster schema-fit test green | schema bytes unchanged against the merge base |
| Decision rationale | The git-history entry is a security-boundary decision | `docs/adr/0155-base-versus-change-questions-get-a-git-history-evidence-entry.md` | eugenelim | ADR Accepted | ADR cited in `Constrained by:` |
| Product direction | The after-fix run has no slot in the contracts | a captured item in `docs/product/captured/` | eugenelim, for the acceptance-centered brief | captured item present | linked from Follow-ons |
| Release history | A non-cosmetic pack change ships under a new version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a core fragment in `docs/product/changelog.d/` | core pack maintainers | version-equality assertion | `tools/check-core-release.py` result recorded in the ledger |

## Agent Rules

### Always do

- Run every Git call of the `git-history` entry through `_supervisor_git.HardenedGit`.
- Keep every sentence an existing test pins in the files this change edits; add text beside it, and keep the FIX rule's meaning: a command that passes before the fix is never recorded as fixed.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together, and regenerate projections with self-host rather than editing them.
- Rebase onto freshly fetched `origin/main` before opening the PR, then rebuild projections.

### Ask first

- Any edit to a `contracts/delivery/` schema; a fact the contracts cannot express is routed to the contract owner as a captured amendment instead.
- Any change to `review-rules.json`, `supervisor-policy.json`, or the reviewer roster.
- Any Git launch in `evidence-gate.py` outside AC-0033's set, or any form of `show` other than `show <oid>:<path>` or of `log` other than `log --no-show-signature --format=%H --max-count=51 <base>..<head> -- <path>`.

### Never do

- No change to `finding-adjudicator`'s tools, and no new agent, reviewer, review round, dependency, or top-level directory.
- No artifact-derived command, argument, path, or environment value reaches execution in `evidence-gate.py`; the `proof-run` subcommand executes no supplied command and launches only Git through `HardenedGit`.
- No edit to an adapter projection except through self-host, and no citation of this repository's internal records in shipped pack content.
- No edit under `packs/core/.apm/skills/work-loop/scripts/` while a `WORK_SUPERVISOR_INTEGRATION=1` test run is live in this worktree.

## Testing Strategy

- **Proof-by-run predicate (AC-0001, AC-0002, AC-0003, AC-0004):** TDD, in `packs/core/tests/skills/work-loop/test_proof_by_run.py`, calling `_review_assessment` directly. The predicate is a pure mapping with a compressible invariant: observed result and subject binding in, assessment out.
- **Supervisor admission (AC-0005, AC-0006):** TDD, as integration tests in the same file through `supervisor_harness`, gated by `WORK_SUPERVISOR_INTEGRATION=1`, because the check sits on the real `report` path.
- **`proof-run` CLI (AC-0007, AC-0008, AC-0032):** TDD, by calling `evidence-gate.py`'s `main` in a temporary Git repository, with the same launch spy.
- **`git-history` entry and refusals (AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0027, AC-0028, AC-0029, AC-0031, AC-0033, AC-0034, AC-0035):** TDD, in `packs/core/tests/skills/work-loop/test_git_history_evidence.py` (and, for the `proof-run` cases of AC-0013, AC-0031, AC-0033, and AC-0034, `test_proof_by_run.py`), in temporary Git repositories with a bare `origin` remote, with a spy on `_supervisor_git._launch` recording every argument vector. A refusal test asserts the refusal code and that no element of any launched argument vector contains the forbidden value as a substring, so a check that ran Git with the value first and refused after fails.
- **No process launch outside the helper (AC-0030):** goal-based, by an AST scan of `evidence-gate.py` and `_git_history.py` in `test_git_history_evidence.py`.
- **Shipped guidance (AC-0016, AC-0017, AC-0018, AC-0019):** goal-based, by pytest content tests in `test_proof_by_run.py` and `test_git_history_evidence.py`, each reading one bounded section; the merge-base halves of AC-0016 and AC-0019 run once at delivery and are recorded in the ledger.
- **Contract fit (AC-0020):** goal-based, by `tests/roster/test_proof_by_run_contract_fit.py`, validating generated records against the canonical schema with `jsonschema`. A pack test cannot read `contracts/`.
- **Evals (AC-0021):** goal-based shape check in `test_proof_by_run.py`; cases are not run against a model in this delivery.
- **Delivery-time checks (AC-0022, AC-0023, AC-0024, AC-0025, AC-0026):** goal-based, run once against the merge base right before the PR and recorded in the verification ledger, because they compare against a moving base.

## Acceptance Criteria

`<merge-base>` is the merge base of `HEAD` with freshly fetched `origin/main`. "The predicate" is `_review_assessment.proof_by_run_assessment`. A proof-run reference has the form `proof-run:v1:<commit>:<fail|pass>:<sha256>`, where `<commit>` is the full hexadecimal subject commit and `<sha256>` is the SHA-256 of the canonical JSON run envelope holding that commit, the SHA-256 of the command text, the exit status, and the SHA-256 of stdout and of stderr. "The change base" is the merge base of `HEAD` and the commit `refs/remotes/origin/HEAD` names. "Launches no value" means no element of any argument vector passed to `_supervisor_git._launch` contains that value as a substring; the tests choose forbidden values that occur in no fixed argument and no temporary path. "The helper's pinning and config reads" are the launches `_supervisor_git.HardenedGit` makes for itself before any caller form: `version`, the one discovery `rev-parse --path-format=absolute --show-toplevel --absolute-git-dir --git-common-dir`, and `config`.

### Proof-by-run predicate

- [ ] **AC-0001.** Given an observed result `fail` and an envelope whose commit equals the current subject commit, the predicate returns a record valid under `_review_contracts.validate_finding_assessment_dict` with `assessment` `supported`, `lineage.predicate_version` `proof-by-run.v1`, `lineage.judgment_authority` equal to the supplied authority, and `evidence_refs` holding exactly one proof-run reference whose kind token is `fail` and whose digest recomputes from the envelope.
- [ ] **AC-0002.** Given an observed result `pass` and a bound envelope, the predicate returns `assessment` `unsupported-opinion` with one proof-run reference whose kind token is `pass`; no input with an observed `pass` yields `supported`.
- [ ] **AC-0003.** Given an envelope whose commit differs from the current subject commit, the predicate refuses with `denied-proof-run-stale` and returns no record.
- [ ] **AC-0004.** The predicate refuses, with a named denial code and no record, an observed result other than `fail` or `pass`, a commit that is not 40 or 64 lowercase hexadecimal characters, and an envelope missing any of its five fields.

### Supervisor admission

- [ ] **AC-0005.** An `assess-finding` result whose assessment carries `lineage.predicate_version` `proof-by-run.v1` is refused with code `review-record-refused` and `HEAD` unchanged when it carries no proof-run reference, more than one, a reference whose commit is not the subject's result commit, a `fail` reference with an assessment other than `supported`, or a `pass` reference with an assessment other than `unsupported-opinion`.
- [ ] **AC-0006.** A consistent proof-by-run assessment is admitted as one `review` step, and a `supported` one is followed by a `repair-request` disposition as today; an assessment with any other `predicate_version` is admitted under today's rules unchanged.

### `proof-run` CLI

- [ ] **AC-0007.** `evidence-gate.py proof-run`, given the request's report, finding, assessment, and subject-fingerprint identifiers, an observed result, an exit status, an authority reference, and paths to the command, stdout, and stderr files, reads the subject commit from `HEAD` itself, creates the envelope at `.context/proof-runs/<sha256 of the assessment id>-<envelope digest>.json` through `_confined_mutation.confined_create`, or leaves an existing file there when its bytes are identical, prints `{"assessment": {...}}` built by the predicate, and exits 0; it executes no supplied command and launches only Git through `HardenedGit`.
- [ ] **AC-0008.** `evidence-gate.py proof-run` exits non-zero with a named code and writes no envelope when AC-0031's config refusal applies (`denied-git-config`); when the tracked working tree differs from `HEAD`; when the envelope path is not a single-link regular file readable through `_file_safety.read_confined_regular_file`, or holds different bytes; when `.context/proof-runs` is a symbolic link; or when an input file is not a single-link regular file confined under the checkout's `.context/` directory outside `.context/reviews/` and `.context/proof-runs/`, or holds more than 1 MiB. Any other refusal — an invalid identifier, an envelope write failure, or a helper Git refusal — also exits non-zero with a named code, prints valid JSON, and writes no envelope. Inputs are read through `_file_safety.read_confined_regular_file` with a 1 MiB bound.
- [ ] **AC-0032.** A second `proof-run` for the same assessment after `HEAD` has moved creates a second envelope and exits 0, and a rerun with identical inputs at the same `HEAD` exits 0 without writing.

### `git-history` entry

- [ ] **AC-0009.** `evidence-gate.py git-history --path <path>`, with `<path>` a member of the change's path set (`git diff --name-only -z --no-renames` from the change base to `HEAD`), prints an envelope with gate ID `git-history`, the SHA-256 of each literal argument vector, an `environment_sha256` that is the SHA-256 of the canonical JSON (sorted keys, `,` and `:` separators, ASCII) of the one environment mapping every `HardenedGit.run` launch of that invocation receives, the working directory, the subject commit, the change base, `isolation` `git-object-store`, `network` `no-remote-objects`, the timeout, the exit status, whether the path is a blob at the change base, its base content when present and within the content cap, and up to 50 commits in `<base>..HEAD` that touched the path, from a log launched with `--no-show-signature --format=%H --max-count=51`, with `log_truncated` true when a 51st commit is returned.
- [ ] **AC-0010.** A path that byte-equals no member of the change's path set — including a parent-traversal path, an absolute path, and a tracked path the change did not touch — refuses with `denied-path-not-in-change` and launches no value of the path.
- [ ] **AC-0027.** A path under `.context/` refuses with `denied-artifact-path` even when it is a committed member of the change's path set, and no `cat-file`, `show`, or `log` argument vector is launched for it.
- [ ] **AC-0011.** A `--base` that is a symbolic name, an abbreviated ID, a value starting with `-`, or a full commit ID followed by `^`, `~1`, `..HEAD`, `:x`, `^{}`, or a newline refuses with `denied-ref-form`; a full commit ID that is not the change base — a commit outside `HEAD`'s history, or an ancestor older than the change base — refuses with `denied-ref-outside-subject-history`; in every case the entry launches no value of the supplied base.
- [ ] **AC-0028.** A repository where `refs/remotes/origin/HEAD` is absent refuses with `denied-no-change-base` before any `diff`, `cat-file`, `show`, or `log` argument vector is launched.
- [ ] **AC-0012.** Under `git-history`, any argument other than one `--path` and at most one `--base` refuses with `denied-not-in-catalog` before any Git process launches; `evidence-gate.py`'s subcommands are exactly `proof-run` and `git-history`.
- [ ] **AC-0013.** Under `git-history` and `proof-run` alike, a repository with an `objects/info/alternates` file, any `extensions.partialClone` entry whatever its value, empty included, or a remote Git treats as a promisor (`promisor` set to a true value, or any `partialclonefilter` entry whatever its value, empty included) refuses with `denied-object-source` before any Git process other than the helper's pinning and config reads is launched.
- [ ] **AC-0031.** Under `git-history` and `proof-run` alike, a repository or worktree config entry that `_supervisor_git.code_running_keys` returns, such as `gpg.program`, refuses with `denied-git-config` before any Git process other than the helper's pinning and config reads is launched.
- [ ] **AC-0034.** Every Git process `evidence-gate.py` launches through `HardenedGit.run` carries `GIT_NO_LAZY_FETCH=1` in its environment, so no missing object is fetched whatever the repository config says, The Git version is read once, from the helper's own single `version` launch, which the invocation makes exactly once; a Git older than 2.44, which does not honour the variable, refuses with `denied-git-version` (a Git older than 2.32, which the helper itself refuses, is reported with the same code) before any Git process other than the helper's pinning and config reads is launched.
- [ ] **AC-0035.** With `log.showSignature=true` in repository config and a commit in the change range that touches the queried path and carries an OpenPGP, X.509, or SSH signature (with `gpg.ssh.allowedSignersFile` set for SSH), `git-history` launches no signature-verification program: the `gpg`, `gpgsm`, or `ssh-keygen` stub placed first on `PATH` writes no marker, while the same fixture's `log` without `--no-show-signature` does write it.
- [ ] **AC-0033.** In every test that drives `evidence-gate.py` for AC-0007, AC-0008, AC-0009 to AC-0015, AC-0027 to AC-0029, AC-0031, AC-0032, AC-0034, and AC-0035, the test records at least one launch, except that each test of a refusal the entry makes before its first Git launch records no launch at all — the AC-0012 refusals, the `denied-ref-form` cases of AC-0011, AC-0027, and a `proof-run` argument list refused with `denied-not-in-catalog` — and each argument vector passed to `_supervisor_git._launch`, other than the helper's pinning and config reads, names a Git subcommand in `rev-parse`, `symbolic-ref`, `merge-base`, `diff` (only with `--name-only -z --no-renames`), `cat-file`, `show`, `log`, or `status`, and only `proof-run` launches `status`.
- [ ] **AC-0014.** A base blob whose `cat-file -s` size exceeds the content cap yields an envelope that omits the content, gives the blob's size and its object ID from `rev-parse --verify`, is marked truncated, and serializes to at most 1 MiB, and no `show` argument vector is launched for it.
- [ ] **AC-0029.** For a changed path that starts with `-` and one that holds pathspec magic (`:(glob)*`), every launched `log` vector carries `--literal-pathspecs` and the path only after a `--` element, every `show` and `cat-file` vector carries it only inside one `<oid>:<path>` element, and the run writes no file in the checkout.
- [ ] **AC-0015.** For a path the change added, the envelope reports it absent at the change base and lists the adding commit; for a path present at the change base and modified by the change, it reports it present with the base content.
- [ ] **AC-0030.** Neither `evidence-gate.py` nor `_git_history.py` imports `subprocess`, `pty`, `asyncio`, `multiprocessing`, or `ctypes`; calls `os.system`, `os.popen`, an `os.exec*`, `os.spawn*`, `os.posix_spawn*`, or `os.fork*` function; or calls `importlib.import_module` or `__import__`.

### Shipped guidance

- [ ] **AC-0016.** In `finding-adjudication.md`, the text from `## Bounded evidence retry` to the next `## ` heading names the built-in `git-history` entry, its measured fact, its two forms, that the entry computes the change base itself and accepts only a path in the change's path set outside `.context/`, that the entry is a scoped exception to the process-level read allowlist and network isolation whose replacement controls are committed objects only, the object-source refusals, and `HardenedGit`, that every Git call it makes through the hardened helper carries `GIT_NO_LAZY_FETCH=1` and that it needs Git 2.44 or later, and that the controller runs it with `evidence-gate.py git-history` and supplies the envelope; every sentence that section holds at `<merge-base>` is still present.
- [ ] **AC-0017.** In `SKILL.md`, the text from `## FIX` to the next `## ` heading states that in full mode the before-fix run is already recorded as the finding's assessment, links `references/supervisor.md`, and keeps the statements that a command passing before the fix is Surfaced instead of fixed and what failing and passing mean.
- [ ] **AC-0018.** In `references/supervisor.md`, the text from `### Review` to the next `### ` heading names the `proof-by-run.v1` predicate and its two outcomes, states that the controller runs the finding's command and `evidence-gate.py proof-run` after that finding's `assess-finding` request is issued and before it is reported, states that the reference is the controller's attestation which the supervisor checks only for consistency and the current commit, and states that the supervisor refuses an inconsistent proof-by-run assessment.
- [ ] **AC-0019.** `packs/core/.apm/agents/finding-adjudicator.md` declares `tools: Read, Grep`, and at delivery `git diff --exit-code <merge-base> HEAD -- packs/core/.apm/agents/finding-adjudicator.md` exits 0.

### Contract fit and evals

- [ ] **AC-0020.** A record the predicate returns for each of AC-0001 and AC-0002 validates against `contracts/delivery/finding-assessment.v1.schema.json` with `jsonschema`'s `Draft202012Validator`.
- [ ] **AC-0021.** `work-loop`'s `evals/evals.json` holds one case each for a command that passes before the fix (expecting `unsupported-opinion`, not fixed), a base-versus-change indeterminate settled with `git-history`, and a request to give `finding-adjudicator` a Git tool (expecting refusal), and each case carries `id`, `prompt`, `expected_output`, and a non-empty `assertions` list.

### Delivery-time checks

- [ ] **AC-0022.** At delivery, `git diff --exit-code <merge-base> HEAD -- contracts/delivery/finding-assessment.v1.schema.json contracts/delivery/evidence-receipt.v1.schema.json contracts/delivery/finding-disposition.v1.schema.json packs/core/.apm/skills/work-loop/review-rules.json` exits 0, and the ledger records it.
- [ ] **AC-0023.** A captured item under `docs/product/captured/` names the after-fix run gap, the contracts that cannot hold it, and a proposed amendment for the acceptance-centered brief's owner, and this spec's Follow-ons links it.
- [ ] **AC-0024.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version, one patch above `packs/core/pack.toml` at `<merge-base>`.
- [ ] **AC-0025.** At delivery, `python3 tools/check-core-release.py --base <merge-base>` exits 0, and the ledger records it.
- [ ] **AC-0026.** `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` exit 0, and `agentbundle catalogue self-host --root . --write` leaves no tracked change after the delivery commit.

## Terminal Intent

`code` — ship the proof-by-run predicate with its supervisor check and CLI, the `git-history` catalog entry with its refusals, the guidance and eval cases, the captured amendment request, and the core release with its projections.

## Follow-ons

- eugenelim: the after-fix run at the replacement subject has no record slot — routed to the acceptance-centered brief's owner as a captured amendment request: [`docs/product/captured/proof-by-run-after-fix-run-binding.md`](../../product/captured/proof-by-run-after-fix-run-binding.md).

## Assumptions

none
