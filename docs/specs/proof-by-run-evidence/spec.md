# Spec: proof-by-run evidence

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0155, ADR-0154, ADR-0144
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** contracts/delivery/finding-assessment.v1.schema.json, contracts/delivery/evidence-receipt.v1.schema.json (both consumed unchanged)
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

In a full-mode `work-loop` run, a reviewer finding that carries a command gets a `finding-assessment.v1` record built from the controller's run of that command at the review subject's commit: a run showing the defect yields `supported`, a run not showing it yields `unsupported-opinion`, and the record's evidence reference binds the command, exit status, and output digests to that commit, which the supervisor checks before it admits the record. A base-versus-change question ("did this change add it, or was it already on the base?") is settled by one run of the built-in `git-history` Evidence gate catalog entry, which refuses any value not drawn from the subject's own history and change.

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
| Interface compatibility | Records stay in existing contracts | `contracts/delivery/finding-assessment.v1.schema.json`, `contracts/delivery/evidence-receipt.v1.schema.json`, consumed unchanged | `structured-review-boundary` and `acceptance-authority-and-evidence` contract owners | roster schema-fit test green | schema bytes unchanged against the merge base |
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
- Any Git form in the `git-history` entry beyond the two ADR-0155 names.

### Never do

- No change to `finding-adjudicator`'s tools, and no new agent, reviewer, review round, dependency, or top-level directory.
- No artifact-derived command, argument, path, or environment value reaches execution in `evidence-gate.py`; the `proof-run` subcommand executes nothing.
- No `subprocess` use in `evidence-gate.py` or `_git_history.py`.
- No edit to an adapter projection except through self-host, and no citation of this repository's internal records in shipped pack content.
- No edit under `packs/core/.apm/skills/work-loop/scripts/` while a `WORK_SUPERVISOR_INTEGRATION=1` test run is live in this worktree.

## Testing Strategy

- **Proof-by-run predicate (AC-0001, AC-0002, AC-0003, AC-0004):** TDD, in `packs/core/tests/skills/work-loop/test_proof_by_run.py`, calling `_review_assessment` directly. The predicate is a pure mapping with a compressible invariant: observed result and subject binding in, assessment out.
- **Supervisor admission (AC-0005, AC-0006):** TDD, as integration tests in the same file through `supervisor_harness`, gated by `WORK_SUPERVISOR_INTEGRATION=1`, because the check sits on the real `report` path.
- **`proof-run` CLI (AC-0007, AC-0008):** TDD, by calling `evidence-gate.py`'s `main` in a temporary Git repository.
- **`git-history` entry and refusals (AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015):** TDD, in `packs/core/tests/skills/work-loop/test_git_history_evidence.py`, in temporary Git repositories, with a spy on `_supervisor_git._launch` recording every argument vector. A refusal test asserts both the refusal code and that no launched argument vector holds the forbidden value, so a check that ran Git first and refused after would fail.
- **Shipped guidance (AC-0016, AC-0017, AC-0018, AC-0019):** goal-based, by pytest content tests in `test_proof_by_run.py` and `test_git_history_evidence.py`, each reading one bounded section; the merge-base halves of AC-0016 and AC-0019 run once at delivery and are recorded in the ledger.
- **Contract fit (AC-0020):** goal-based, by `tests/roster/test_proof_by_run_contract_fit.py`, validating generated records against the canonical schemas with `jsonschema`. A pack test cannot read `contracts/`.
- **Evals (AC-0021):** goal-based shape check in `test_proof_by_run.py`; cases are not run against a model in this delivery.
- **Delivery-time checks (AC-0022, AC-0023, AC-0024, AC-0025, AC-0026):** goal-based, run once against the merge base right before the PR and recorded in the verification ledger, because they compare against a moving base.

## Acceptance Criteria

`<merge-base>` is the merge base of `HEAD` with freshly fetched `origin/main`. "The predicate" is `_review_assessment.proof_by_run_assessment`. A proof-run reference has the form `proof-run:v1:<commit>:<fail|pass>:<sha256>`, where `<commit>` is the full hexadecimal subject commit and `<sha256>` is the SHA-256 of the canonical JSON run envelope holding that commit, the SHA-256 of the command text, the exit status, and the SHA-256 of stdout and of stderr.

### Proof-by-run predicate

- [ ] **AC-0001.** Given an observed result `fail` and an envelope whose commit equals the current subject commit, the predicate returns a record valid under `_review_contracts.validate_finding_assessment_dict` with `assessment` `supported`, `lineage.predicate_version` `proof-by-run.v1`, `lineage.judgment_authority` equal to the supplied authority, and `evidence_refs` holding exactly one proof-run reference whose kind token is `fail` and whose digest recomputes from the envelope.
- [ ] **AC-0002.** Given an observed result `pass` and a bound envelope, the predicate returns `assessment` `unsupported-opinion` with one proof-run reference whose kind token is `pass`; no input with an observed `pass` yields `supported`.
- [ ] **AC-0003.** Given an envelope whose commit differs from the current subject commit, the predicate returns `assessment` `indeterminate`.
- [ ] **AC-0004.** The predicate refuses, with a named denial code and no record, an observed result other than `fail` or `pass`, a commit that is not 40 or 64 lowercase hexadecimal characters, and an envelope missing any of its five fields.

### Supervisor admission

- [ ] **AC-0005.** An `assess-finding` result whose assessment carries `lineage.predicate_version` `proof-by-run.v1` is refused with code `review-record-refused` and `HEAD` unchanged when it carries no proof-run reference, more than one, a reference whose commit is not the subject's result commit, a `fail` reference with an assessment other than `supported`, or a `pass` reference with an assessment other than `unsupported-opinion`.
- [ ] **AC-0006.** A consistent proof-by-run assessment is admitted as one `review` step, and a `supported` one is followed by a `repair-request` disposition as today; an assessment with any other `predicate_version` is admitted under today's rules unchanged.

### `proof-run` CLI

- [ ] **AC-0007.** `evidence-gate.py proof-run`, given the request's report, finding, assessment, and subject-fingerprint identifiers, an observed result, an exit status, an authority reference, and files holding the command, stdout, and stderr, reads the subject commit from `HEAD` itself, exclusively creates the envelope under `.context/proof-runs/`, prints `{"assessment": {...}}` built by the predicate, and exits 0; it launches no process other than Git through `HardenedGit`.
- [ ] **AC-0008.** `evidence-gate.py proof-run` exits non-zero with a named code and writes no envelope when the tracked working tree differs from `HEAD`, when the envelope path already exists, or when a command, stdout, or stderr file exceeds 1 MiB.

### `git-history` entry

- [ ] **AC-0009.** `evidence-gate.py git-history --base <oid> --path <path>`, with `<oid>` a full commit ID that is an ancestor of `HEAD` and `<path>` a member of the change's path set (`git diff --name-only` from base to `HEAD`, renames off), prints an envelope with gate ID `git-history`, the SHA-256 of each literal argument vector and of the environment, the working directory, the subject commit, isolation `read-only`, network `disabled`, the timeout, the exit status, whether the path exists at the base, the path's base content when it exists, and the commits in `<oid>..HEAD` that touched the path.
- [ ] **AC-0010.** A path that byte-equals no member of the change's path set — including a parent-traversal path, an absolute path, a path under `.context/reviews/`, and a tracked path the change did not touch — refuses with `denied-path-not-in-change`, and no launched argument vector holds that path.
- [ ] **AC-0011.** A base that is a symbolic name, a revision expression, an abbreviated ID, or a value starting with `-` refuses with `denied-ref-form`, and a full commit ID that is not an ancestor of `HEAD` refuses with `denied-ref-outside-subject-history`; in both cases no `show` or `log` argument vector is launched.
- [ ] **AC-0012.** A subcommand, form, or extra argument other than the two ADR-0155 forms refuses with `denied-not-in-catalog` before any Git process launches.
- [ ] **AC-0013.** A repository with an `objects/info/alternates` file, an `extensions.partialClone` setting, or a remote with `promisor` set refuses with `denied-object-source` before any `show` or `log` argument vector is launched.
- [ ] **AC-0014.** A base blob larger than the content cap yields an envelope that omits the content, gives the blob's size and object ID, is marked truncated, and serializes to at most 1 MiB; and every launch the entry makes goes through `_supervisor_git._launch`.
- [ ] **AC-0015.** For a path the change added, the envelope reports it absent at the base and lists the adding commit; for a path present at the base and modified by the change, it reports it present with the base content.

### Shipped guidance

- [ ] **AC-0016.** In `finding-adjudication.md`, the text from `## Bounded evidence retry` to the next `## ` heading names the built-in `git-history` entry, its measured fact, its two forms, that the base must be an ancestor of the subject and the path a member of the change's path set, and that the controller runs it with `evidence-gate.py git-history` and supplies the envelope; every sentence that section holds at `<merge-base>` is still present.
- [ ] **AC-0017.** In `SKILL.md`, the text from `## FIX` to the next `## ` heading states that in full mode the before-fix run is recorded as the finding's assessment by `evidence-gate.py proof-run`, links `references/supervisor.md`, and keeps the statements that a command passing before the fix is Surfaced instead of fixed and what failing and passing mean.
- [ ] **AC-0018.** In `references/supervisor.md`, the text from `### Review` to the next `### ` heading names the `proof-by-run.v1` predicate, its three outcomes, and that the supervisor refuses an inconsistent proof-by-run assessment.
- [ ] **AC-0019.** `packs/core/.apm/agents/finding-adjudicator.md` declares `tools: Read, Grep`, and at delivery `git diff --exit-code <merge-base> HEAD -- packs/core/.apm/agents/finding-adjudicator.md` exits 0.

### Contract fit and evals

- [ ] **AC-0020.** A record the predicate returns for each of AC-0001, AC-0002, and AC-0003 validates against `contracts/delivery/finding-assessment.v1.schema.json` with `jsonschema`'s `Draft202012Validator`.
- [ ] **AC-0021.** `work-loop`'s `evals/evals.json` holds one case each for a command that passes before the fix (expecting `unsupported-opinion`, not fixed), a base-versus-change indeterminate settled with `git-history`, and a request to give `finding-adjudicator` a Git tool (expecting refusal), and each case carries `id`, `prompt`, `expected_output`, and a non-empty `assertions` list.

### Delivery-time checks

- [ ] **AC-0022.** At delivery, `git diff --exit-code <merge-base> HEAD -- contracts/delivery/finding-assessment.v1.schema.json contracts/delivery/evidence-receipt.v1.schema.json packs/core/.apm/skills/work-loop/review-rules.json` exits 0, and the ledger records it.
- [ ] **AC-0023.** A captured item under `docs/product/captured/` names the after-fix run gap, the contracts that cannot hold it, and a proposed amendment for the acceptance-centered brief's owner, and this spec's Follow-ons links it.
- [ ] **AC-0024.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version, one patch above `packs/core/pack.toml` at `<merge-base>`.
- [ ] **AC-0025.** At delivery, `python3 tools/check-core-release.py --base <merge-base>` is run and its exit status recorded in the ledger.
- [ ] **AC-0026.** `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` exit 0, and `agentbundle catalogue self-host --root . --write` leaves no tracked change after the delivery commit.

## Terminal Intent

`code` — ship the proof-by-run predicate with its supervisor check and CLI, the `git-history` catalog entry with its refusals, the guidance and eval cases, the captured amendment request, and the core release with its projections.

## Follow-ons

- eugenelim: the after-fix run at the replacement subject has no record slot — routed to the acceptance-centered brief's owner as a captured amendment request (AC-0023; link added at delivery).

## Assumptions

none
