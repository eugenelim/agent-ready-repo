# Spec: parked approvals

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0157, RFC-0099, ADR-0154
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the `park` and `gates` outputs are supervisor CLI JSON, documented in the work-loop skill's supervisor reference; no `contracts/` schema changes
- **Shape:** service

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

A human approving a full-mode work-loop spec or plan sees every waiting `spec-approved` and `plan-approved` gate in one listing, with the exact digests, the commit to read, and what each answer does, while the controller keeps working on independent specs. The supervisor records an approval only for the digests the controller relays from that human's answer, refuses once either artifact has changed from them, and leaves a gate nobody answers unapproved forever.

## What Changes

- New supervisor verb `park <spec-dir> --gate spec-approved|plan-approved` — `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py` and one new `_supervisor_gates.py` module beside it.
- New read-only supervisor verb `gates` — the same two files.
- The gate digest: the canonical contract digest over the artifact without its `## Changelog` section — `_supervisor_gates.py`, calling the existing canonicalizer in `_loop_guards.py`.
- `start` takes `--approved-spec-digest` and `--approved-plan-digest`, needs both whenever it records an approval pair, and refuses a mismatch before any write — `work-supervisor.py` and `_supervisor_admission.py`.
- Park records live in the checkout's local supervisor store, `<git-dir>/agentbundle-supervisor/gates/`, one per spec.
- Controller procedure for parking, listing, answering, and working other specs while a gate waits — work-loop `SKILL.md` step 12, `references/supervisor.md`, `references/session-resumption.md`, `references/state-schema.md`.
- Eval cases for a parked gate — `packs/core/.apm/skills/work-loop/evals/evals.json`.
- Every existing `start` call site in the core pack tests that records an approval passes the two digests — `packs/core/tests/skills/work-loop/`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | The design choice and its alternatives | `docs/adr/0157-work-loop-approval-gates-park-instead-of-halting.md` | eugenelim | ADR committed `Accepted` before spec approval | Cited in `Constrained by:` |
| Maintainer procedure | Controllers follow the skill, not the code | work-loop `SKILL.md` step 12; `references/supervisor.md`; `references/session-resumption.md` | core pack maintainers | Content tests green | Guidance names `park`, `gates`, both `start` digest arguments, and the no-default rule |
| Current architecture | The supervisor's command surface table lists its verbs | `docs/architecture/work-loop-execution-supervisor.md` command-surface row | core pack maintainers | Row lists `park` and `gates` | Row matches the parser's verb set |
| Operations (state) | A new local record kind | `references/state-schema.md` local-store row | core pack maintainers | Row names `gates/` and its writer | Row present |
| Release history | Core changes content | `docs/product/changelog.d/<uuid>.md`; `packs/core/pack.toml`; `packs/core/.claude-plugin/plugin.json` | core pack maintainers | Release check green | Version is one patch above the merge base's |
| Reusable learning | none — no generalizable practice beyond the ADR is expected | — | — | — | — |

## Agent Rules

### Always do

- Compute every digest the supervisor shows or compares from the files themselves; never take a digest from a controller argument except the two `start` pins.
- Pass `start` the spec digest from the spec approver's own answer and the plan digest from the plan approver's own answer. A digest copied from `park` or `gates` output without that answer is not an approval. The supervisor cannot tell the difference: the pins bind an approval to an exact revision, and the authority references, not the pins, name the humans.
- Fail closed: a missing, malformed, or unreadable park record, a Git read that fails, or an unparseable artifact refuses or lists the gate as not approvable; it never lists a gate as approved.
- Run every Git call through the supervisor's existing hardened Git helper, and every store write through the existing confined-mutation helper.
- Keep `start`'s existing refusals and its single approval-pair commit unchanged apart from the digest check.

### Ask first

- Any change to an existing `approval-record.v1` or `initial-plan-review.v1` field, or to the committed `delivery/approvals.jsonl` line shape.
- Any listing of gates from another worktree or from a remote.
- Any answer other than `approve`, `reject`, and no answer.

### Never do

- Never approve, or record as approved, a gate that no named human answered: no default, timeout, batch rule, flag, or record turns a parked gate into an approval.
- Never let `start` read a park record.
- Never write a commit, a ref, a `Status:` line, or a file in the working tree from `park` or `gates`.
- Never put controller-supplied free text into a park record or the `gates` listing.
- Never add a dependency, a new top-level directory, or a new `contracts/` schema.

## Testing Strategy

- **Gate digest (AC-0007, AC-0008, AC-0025): TDD, unit.** A pure function of the artifact text, so each normalization and each shape violation is one small case.
- **`park` and `gates` behaviour (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0026, AC-0029, AC-0030, AC-0031, AC-0032, AC-0038, AC-0039): TDD, integration** through the supervisor CLI on a real Git repository built by the existing supervisor test harness, because each criterion is about what lands in Git and the store.
- **`start` digest binding and the no-default rule (AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0027, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037): TDD, integration** through the CLI, gated like the other supervisor integration suites, because the property is that no Git state changes.
- **Guidance and evals (AC-0020, AC-0021, AC-0022): goal-based**, a content test over the shipped skill files plus the eval harness's own schema check.
- **Release (AC-0023, AC-0024): goal-based**, the release and catalogue checks.

## Acceptance Criteria

### `park`

- [ ] **AC-0001.** Given a committed, clean spec directory whose spec is `Draft`, `park <spec-dir> --gate spec-approved --intent code|spec-plan --code-trust trusted|untrusted` exits 0, prints JSON with `status` `parked`, `gate`, `spec_dir`, `spec_digest`, `plan_digest`, `intent`, `code_trust`, and `commit` equal to `HEAD`, and writes exactly one file under `<git-dir>/agentbundle-supervisor/gates/`.
- [ ] **AC-0002.** After any `park` run, `HEAD`, every ref, the index file, and every working-tree file, ignored files included, are byte-identical to before.
- [ ] **AC-0003.** `park` refuses with code `gate-uncommitted` and writes no record when `spec.md` or `plan.md` has no single stage-0 index entry, or its blob differs between the index and `HEAD`, or neither its working-tree bytes nor those bytes with each CRLF turned into LF hash to that blob.
- [ ] **AC-0004.** `park --gate spec-approved` refuses with `gate-status-mismatch` unless the spec is `Draft`; `park --gate plan-approved` refuses with `gate-status-mismatch` unless the spec is `Approved` and the plan is `Drafting`.
- [ ] **AC-0005.** `park` refuses with `gate-already-admitted` exactly when `start` with the same intent and code trust would answer `current`: the latest approval pair in `<spec-dir>/delivery/approvals.jsonl` at `HEAD` carries the envelope fingerprint the spec derives now, the `--intent` given to `park`, and the `--code-trust` given to `park`. A spec whose latest pair differs in any of the three parks like a spec with no pair.
- [ ] **AC-0006.** A second `park` with the same gate, the same digests, the same intent, and the same code trust prints `status` `current` and leaves the record byte-identical, provided the recorded commit can still be read and holds the recorded digests; a successful `park` for the same spec that differs in any of them, or whose recorded commit fails that condition, replaces the record, so the spec has one record.
- [ ] **AC-0029.** When an input meets more than one `park` refusal, `park` returns the first that applies in this order: `gate-unsafe-path`, `ambiguous-reference`, `intent-mismatch`, `gate-uncommitted`, `gate-already-admitted`, `gate-status-mismatch`, `gate-unsafe-content`, `gate-changelog-shape`, `gate-spec-changed`.
- [ ] **AC-0038.** `park` refuses with `intent-mismatch` and owner `owner`, writing no record, when the spec declares a Terminal Intent that differs from `--intent`, and with `ambiguous-reference` when the spec has more than one `## Terminal Intent` section, the same refusals `start` gives; a spec that declares none parks with the given intent.
- [ ] **AC-0030.** `park --gate plan-approved` refuses with `gate-spec-changed` and writes no record when the spec has no valid park record (AC-0031) or its record holds a `spec_digest` other than the current gate digest of `spec.md`; on success, the record it writes holds that same `spec_digest`.
- [ ] **AC-0032.** A safe spec path is a repository-relative path with no leading `/`, whose segments are non-empty, are not `.` or `..`, do not start with `-`, and hold only `A-Z`, `a-z`, `0-9`, `.`, `_`, and `-`. Among paths the supervisor's shared spec-directory check accepts, `park` refuses every unsafe one with `gate-unsafe-path`; a path the shared check rejects exits 2 with a usage error before any verb runs.
- [ ] **AC-0039.** An artifact that is not valid UTF-8, or that holds a character in Unicode category Cc other than tab, LF, or a CR immediately before LF, a character in category Cf, a Default_Ignorable_Code_Point (the work-loop knowledge lint's one hidden-character definition), U+2028, U+2029, or U+FFF9 to U+FFFB, has no gate digest: `park` refuses it with `gate-unsafe-content`, `gates` lists its entry as `stale`, and `start` that would record a pair refuses with `gate-unsafe-content` and owner `controller` and appends no line.
- [ ] **AC-0026.** `park` refuses with `gate-changelog-shape` and writes no record when either artifact has no gate digest under AC-0025.

### Gate digest

- [ ] **AC-0007.** The gate digest of an artifact is unchanged when only its `Status:` token changes, when lines are added to or removed from its `## Changelog` section, or when line endings or trailing whitespace change.
- [ ] **AC-0008.** The gate digest of an artifact changes when any byte outside its status token, its `## Changelog` section, line endings, trailing whitespace, and checkbox contents changes.
- [ ] **AC-0025.** An artifact has no gate digest when, counting only lines outside fenced code blocks, its `## Changelog` heading occurs more than once, is not its last level-two heading, or heads a section holding, outside HTML comments, any line other than a blank line, a `- ` list item, or an indented continuation line of a list item.

### `gates`

- [ ] **AC-0009.** `gates` prints one entry per valid park record (AC-0031) with exactly the fields `spec_dir`, `gate`, `spec_digest`, `plan_digest`, `intent`, `code_trust`, `commit`, `read`, `answers`, and `state`, where `read` is the two commands `git --no-pager --no-replace-objects --no-lazy-fetch cat-file blob <commit>:<spec-dir>/spec.md` and `git --no-pager --no-replace-objects --no-lazy-fetch cat-file blob <commit>:<spec-dir>/plan.md`, which print the stored bytes the digests came from and nothing else, whatever replace refs, textconv, filters, pager, or promisor remote the repository configures, and which fail rather than fetch a missing object.
- [ ] **AC-0010.** Each entry's `answers` maps exactly `approve`, `reject`, and `no-answer` to the supervisor's fixed consequence text for that gate, and the `no-answer` text states that the gate stays unapproved.
- [ ] **AC-0011.** For a valid park record (AC-0031), the entry's `state` is `pending` only when the record's file name is the one `park` derives from its `spec_dir`, its `gate` fits the AC-0004 statuses of the artifacts at the recorded commit, and the recorded digests equal both the gate digests of the two artifacts at the recorded commit and the gate digests of the two working-tree artifacts; it is `stale` in every other case, including an artifact that is missing or has no gate digest at either revision and a commit that cannot be read.
- [ ] **AC-0012.** `gates` omits a valid park record (AC-0031) for which `park` with the record's `intent` and `code_trust` would refuse `gate-already-admitted` (AC-0005).
- [ ] **AC-0013.** Every entry under the store's `gates/` directory that is not a valid park record is listed with `state` `invalid` and no other field except `spec_dir`, present only when the record holds a safe spec path (AC-0032), and `record`, present only when the entry's name is 16 lowercase hexadecimal characters followed by `.json`; such an entry never lists as `pending`, and `gates` still exits 0 with the other records listed.
- [ ] **AC-0031.** A valid park record is a regular file of at most 4096 bytes holding a JSON object with exactly the keys `schema_version` (the integer 1), `spec_dir` (a safe spec path, AC-0032, every part of which is an existing plain directory, not a symbolic link), `gate` (`spec-approved` or `plan-approved`), `intent` (`code` or `spec-plan`), `code_trust` (`trusted` or `untrusted`), `spec_digest` and `plan_digest` (64 lowercase hexadecimal characters each), and `commit` (40 or 64 lowercase hexadecimal characters).
- [ ] **AC-0014.** After any `gates` run, the store, `HEAD`, every ref, the index, and every working-tree file are byte-identical to before.

### `start` binding

- [ ] **AC-0015.** `start` that would record an approval pair refuses with code `approval-digest-required` and owner `owner` when `--approved-spec-digest` or `--approved-plan-digest` is absent, and writes nothing to Git, the store, or the working tree, ignored files included.
- [ ] **AC-0036.** On every `start` path, a `--approved-spec-digest` or `--approved-plan-digest` value that is not 64 lowercase hexadecimal characters exits 2 with a usage error and writes nothing.
- [ ] **AC-0016.** `start` that would record an approval pair refuses with code `approval-digest-mismatch` and owner `owner`, exits 1, and writes nothing to Git, the store, or the working tree, ignored files included, when either digest differs from the current gate digest of that artifact.
- [ ] **AC-0017.** `start` that would record an approval pair, with both digests equal to the current gate digests answers `admitted` for `--intent code` and `terminal` for `--intent spec-plan`, and appends exactly one `approvals.jsonl` line in one commit.
- [ ] **AC-0033.** `start` on an admitted run whose envelope, intent, and code trust are unchanged answers `current` whether well-formed digests are absent, equal to the current gate digests, or different from them, including after an in-envelope plan edit.
- [ ] **AC-0034.** The whole-file digests in a recorded approval pair come from the same bytes of `spec.md` and `plan.md` whose gate digests matched the pins; when either file's bytes change between the digest check and the last read before the approval commit, `start` refuses with `approval-digest-mismatch` and owner `owner` and appends no line.
- [ ] **AC-0037.** `start` records an approval pair only from bytes its digest check verified: when the read-only decision before its first write answers `current` but the decision under the run lock would record a pair, or the envelope fingerprint, intent, or code trust derived under the lock differs from the one the digest check used, `start` refuses with `approval-digest-required` and owner `owner` and appends no line.
- [ ] **AC-0027.** `start` that would record an approval pair refuses with `gate-changelog-shape` and owner `controller`, writing nothing to Git, the store, or the working tree, ignored files included, when either artifact has no gate digest under AC-0025.
- [ ] **AC-0035.** When an input meets more than one `start` digest refusal, `start` returns the first that applies in this order: `gate-unsafe-content`, `gate-changelog-shape`, `approval-digest-required`, `approval-digest-mismatch`.
- [ ] **AC-0018.** For the same arguments, `start`'s exit code and output are the same whether the spec's park record is present, absent, malformed, or rewritten to hold other digests.

### Never approved by default

- [ ] **AC-0019.** Given a parked gate, both statuses then set to `Implementing` and `Executing` with no human answer, and a spec edit outside `## Changelog`, `start` with the digests from the parked record refuses `approval-digest-mismatch` and `start` with no digests refuses `approval-digest-required`, and `approvals.jsonl` stays absent after each.

### Guidance and evals

- [ ] **AC-0020.** The work-loop supervisor reference's verb table lists `park` and `gates`, and its `start` row names `--approved-spec-digest` and `--approved-plan-digest`.
- [ ] **AC-0021.** The work-loop `SKILL.md` approval step tells the controller to park each gate, to pass `start` the spec digest from the spec approver's answer and the plan digest from the plan approver's answer, to dispatch no implementation work for a parked spec, and never to treat a parked gate as approved.
- [ ] **AC-0022.** `evals.json` carries a case in which a gate is parked with no answer and another independent spec is ready, whose assertions require the controller to work the other spec, not run `start` for the parked one, and not report the gate approved.

### Release

- [ ] **AC-0023.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version, one patch above `packs/core/pack.toml` at the merge base with freshly fetched `origin/main`, and a `docs/product/changelog.d/` fragment names the change.
- [ ] **AC-0024.** After self-host, `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` exit 0 and the tree is clean.

## Retired identifiers

- AC-0028

## Terminal Intent

`code` — ship `park`, `gates`, the gate digest, the `start` digest binding, the guidance and eval cases, and the core release with its projections.

## Follow-ons

none

## Assumptions

- Security: who may run `park`, `gates`, and `start`, or write under the Git directory, is the host's tool separation, which this delivery does not change — a controller or worker that can do all three can still relay digests no human gave (settled by: the host's permission model; the Agent Rules state the relay limit).
- Security: lookalike letters and right-to-left letters that need no format character can still mislead a reader of `read` output — AC-0039 covers only characters that render as nothing or reorder text (settled by: a later review if this proves exploitable).
- Security: the approver's own Git environment (`GIT_DIR`, `GIT_CONFIG_*`, global config) is trusted — the `read` commands neutralize only repository-controlled behaviour.
- Security: `start`'s `--intent` and `--code-trust` are not pinned to the parked entry; only the two digests are — a controller can start with a different trust from the one the approver saw (settled by: the authority references and review of the start command; a later delivery may pin them).
- Operations: the `read` commands need Git 2.44 or later for `--no-lazy-fetch`; an older Git fails the command rather than fetching — whether CI runners and adopters meet that floor is checked at code stage.
- Testing: `test_supervisor_parked_gates.py`, including its pseudo-terminal test, does not run on Windows CI — Windows behaviour of `park` and `gates` is untested.
- Review: the final narrow-check edit (AC-0003, AC-0006, AC-0009, AC-0038, AC-0039 wording and the matching plan lines) had no spec-stage reviewer pass — the code-stage security, adversarial, and quality passes cover it.
