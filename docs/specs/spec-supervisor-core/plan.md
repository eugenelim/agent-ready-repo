# Plan: Spec supervisor core

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/.apm/skills/work-loop/scripts/` supplies the read-only oracle: `review-artifact.py`, `_supervisor_gates.py`, `_loop_guards.py`, `_supervisor_admission.py` and `work-supervisor.py`.

> **Contract:** Touches, Tests and Done when govern completion. Design and approach are working material; spec contract changes require amendment. Execution evidence belongs in `notes/verification-ledger.md`.

## Approach

Build admission, requests and report recovery before protection, review, consent and pins. Derive state from ledger/history; use the work supervisor as an oracle, never a runtime import. Release core before gates.

## Constraints

- eugenelim holds every repository, contract, review and risk owner role.
- ADR-0162 defines commands; ADR-0163 forbids work-loop runtime imports and pin-set changes; ADR-0157 D4 reserves approval for humans.
- Pack rules forbid internal citations and require UTF-8 stdout/stderr, matching version bumps and isolated test imports. No added pack line contains internal record citations.
- Core ships five kinds first; gates adds seven-kind behavior through gates AC-0027. Neither release edits work-loop pins.

## Construction tests

T3 drives real work-supervisor status, park and start beside the core ledger/store, including Approved-pair admission. T6 drives a review-cap park end-to-end. Gates owns manual trials.

## Durable-output map

T1–T7 deliver interface and behavior; T8 delivers release records/projections/eval; T9 aligns page 05. Their Done when checks supply closeout evidence.

## Design (LLD)

### Seam decisions

Core owns consent issuance, marker, identity, park/listing and immutable allowance; gates owns answers, delegation and allowance changes. Extension points are core AC-0002, AC-0004, AC-0005, AC-0010, AC-0013–AC-0017, AC-0029–AC-0032, AC-0034 and AC-0044.

Core consent never completes: report returns no-human-answer even with a purported answer record. Gates adds completion, approve-after-cap/weak binding, delegated-park voiding and answer-driven waits.

After voiding spec-approved consent, AC-0048 blocks review until the named human eugenelim restores Draft and removes the approval entry, through the existing revert-pending wait or human-decision. ADR-0157 D4 reserves Approved writes for that human.

Owned by: T2, T4, T6

### Digest copy and equivalence corpus

Gate digests cover the whole normalized artifact, including Agent Rules; `ac_section_only` limits checkbox normalization only. Pair identity preserves distinctions removed by gate normalization, including checkbox marks and trailing whitespace, while masking the first status token and approval-entry lines.

Copy the full dependency closure of `gate_digest`, `_drop_approval_entries`, `_APPROVAL_ENTRY_RE`, `_unsafe`, `_LINE_SEPARATORS`, `_INVISIBLE_CAP`, `canonical_contract`, `is_hidden_char`, `_RUN_CHARS`, `_MAX_ADJACENT_INVISIBLE`, `invisible_budget`, `_HTML_COMMENT_RE`, `_SECTION_HEADING_RE`, `_STATUS_RE`, and `extract_status_token`.

Corpus: plain input; approval suffixes/period/wrapping; multiple Changelogs; following heading/fence; blank folding/trailing blanks; heading whitespace; status/comment changes; checkbox scope/fences/lowercase criteria; outside-section edits; absent/repeated acceptance headings; CRLF/lone CR/BOM/NUL; NFC/NFD; final newline; invalid UTF-8; hidden/ZWJ runs at/over budget; 200 seeded inputs.

Compare digests and refusals with real modules loaded by unique path, in pack tests, at closeout and in test-corpus.yml. Source: `_supervisor_gates.py` gate_digest hashes all lines returned by `_loop_guards.py` canonical_contract.

Owned by: T6

### Interfaces & contracts

Commands are start/next/report/status/park with spec-dir, report also taking result-file, and gates without it. AC-0005, AC-0010, AC-0046 and AC-0047 own envelopes, facts, payloads and wrappers; results are `{"request_id", "facts"}`; derive facts from reports rather than accepting classifications.

Manifest modes: headless/attach/session for author-spec, review-round, adjudicate and revise; human for consent. Policy contains max_review_rounds, default 3; pinned_files follows AC-0038, including existing new-spec lint scripts.

Owned by: T1, T2, T3, T5

### Data & schema

The admission line also records the run branch ref. Ledger JSON lines contain kind, request/run ids, previous commit, verified facts, report hashes, pair identity, roles and admission pins. Ledger, attempt and store paths are implementation-discovered; store sits beside, never inside, `<git-dir>/agentbundle-supervisor/`, whose preflight rejects malformed run directories.

Report hashes record evidence, not global uniqueness: consumption belongs to request identity. Distinct role/round files may contain identical clean sentinels.

Owned by: T3, T4, T5

### State & control flow

Request ids derive from run id and ledger position, so fresh clones reissue them. State derives from ledger, first-parent history and attempts; no store copy substitutes for the committed anchor.

Report order: confinement, pins, ledger, protected content, request identity, result bounds/facts, allowed differences, kind checks, files/ledger/commit, attempt close. Before-commit recovery accepts only a byte-identical recomputed pending line; after-commit recovery adopts the checked step.

AC-0017 binds identities; AC-0043 prevents mixed-round convergence; AC-0044 voids changed consent/rounds before waiting responses. Gates resolves tip and admission pins from the admission run branch ref; missing/unresolvable refs list invalid. The tip comparison includes identity-only voiding.

Owned by: T2, T3, T4, T5, T6

### Behavior & resilience

Use pre-execute-review ordering and a local classifier behavior-equivalent to review-artifact.py. Clean without footer skips adjudication; other non-invalid reports are adjudicated; every real invalid/indeterminate reason stops the run.

Required roles never shrink; equal author/reviewer profiles mark weakness, while equal reviewer/adjudicator profiles refuse. Each finding reference follows AC-0032; invalid references disappear.

Refusals write nothing. Net pin restoration recovers; first-parent checks accept unrelated commits, while forged valid ledger lines remain an accepted risk.

Owned by: T1, T3, T4, T5

### Quality attributes

Confine paths before pins and open without following links. Disable bytecode loading/writing; run alignment lint from pinned scripts using `-I -B` and a scrubbed environment.

Bound and neutralize every untrusted output under AC-0033. Preserve the security controls and accepted risks in the spec.

Owned by: T1, T3, T6, T7

## Tasks

### T1: Admission and confinement

**Satisfies:** AC-0001, AC-0002, AC-0003

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_admission.py`

**Tests:**

Mode: TDD, real temporary repository.

- Admission produces one committed line with run, run branch ref, roles, pins and identity (AC-0001).
- AC-0002 cases: default/unknown branch, detached HEAD, modified/staged/untracked non-ignored paths, missing/untracked/ignored pair or ledger, repeated start, historical ledger removal with reduced roles/reset allowance/bypassed cap or weak consent, purported answer, policy values 0/-1/"3"/1.5, nonportable script name and manifest mismatch; each writes nothing. Missing policy key admits with 3; value 1 admits.
- Each verb rejects absolute/traversal/dot/backslash/leading-hyphen/git-directory paths, symlink/non-directory components, symlink/non-regular pair or ledger, and a link swapped before open (AC-0003).

**Done when:** the T1 tests pass.

### T2: Manifest, policy file, request shapes and roles

**Satisfies:** AC-0004, AC-0005, AC-0006, AC-0007, AC-0046, AC-0047

**Depends on:** T1, spec:supervisor-manifest-contract/T2

**Touches:** `packs/core/.apm/skills/new-spec/supervisor.toml`, `packs/core/.apm/skills/new-spec/spec-policy.json`, `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_requests.py`

**Tests:**

- Goal-based: manifest validates and lists exactly driven kinds (AC-0004).
- TDD: all kind/stage pairings and invalid enums (AC-0005); author-spec only before any author/review, including human author (AC-0006); adversarial always, security/destructive addition and non-shrinking roles after trigger removal (AC-0007).
- TDD: remove each required payload field in turn; revise contains every sustained finding with only valid references (AC-0046). Assert request/refusal/terminal wrappers, including refusal owner eugenelim; missing wrapper or code/owner/detail fails (AC-0047).

**Done when:** the T2 tests pass.

### T3: Report, ledger, step commits, working tree, resume and coexistence

**Satisfies:** AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0016, AC-0018, AC-0020, AC-0021, AC-0045

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_ledger.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_resume.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_integration.py`

**Tests:**

Mode: TDD with real commits, except real-script integration.

- One line/commit per step (AC-0008); foreign single-line appends, including open-request forgery, follow AC-0009; two lines, wrong previous and disallowed paths refuse; no-ledger commits remain allowed.
- AC-0010 cases: wrong/consumed id, symlink/non-regular/over-16-MiB/non-UTF-8/duplicate-key/17-level result; extra/repeated/missing facts; invalid 65-character/newline/path agent definition; available/unavailable/missing/unknown outcomes for reviewer and adjudicator. Any consent result refuses no-human-answer, even with a purported answer.
- Supplied classification/count/weakness never determine recorded values (AC-0045). Wrong spec/plan status or failing scrubbed lint refuses author report (AC-0011).
- Edited/removed/reordered/inserted ledger lines refuse on every verb after pins (AC-0012). Exercise each kind's allowed working/index paths, untracked files, protected revise edit and byte-different pending line (AC-0016).
- Kill before commit and after commit; fresh next/repeated report preserve id and exactly one step/commit, using committed history for consumption (AC-0020). Status writes nothing (AC-0021).
- Integration: real installed work-supervisor status/park/start matches behavior without core ledger/store, including Approved-pair admission (AC-0018).

**Done when:** the T3 tests pass.

### T4: Protected content, the approval-edit exception and the reviewed revision

**Satisfies:** AC-0013, AC-0014, AC-0015, AC-0017, AC-0043, AC-0044, AC-0048

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_protected.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_revision.py`

**Tests:**

Mode: TDD with real commits.

- Unrelated foreign commits, including delivery/approvals.jsonl, pass. Combined pin/ledger/protected faults select AC-0013's first code; observable foreign attempt/store mutation refuses; first-parent merges and net pin restoration behave identically.
- Spec token plus spec-entry edits pass from spec-approved issuance through the next ledger commit, including blank-line normalization. Unanswered reverts before park pass; purported answers grant no extra permission; cap/weak has no approval window (AC-0014).
- Before/after-window edits, status prefix/suffix, removed/second status line, wrong entry, wrong Changelog, wrapped entry and other protected changes refuse. Exact early token/entry restoration before another ledger commit clears only that violation; partial restoration, intervening ledger commit or another protected change refuses (AC-0014, AC-0015).
- Converged/cap/weak consent binds the last reviewed identity; allowance-time voiding binds current unreviewed identity; approval-only edits preserve it (AC-0017). Mixed review/adjudication identities, including issue-to-report changes, never converge (AC-0043).
- After allowed spec approval and entry creation, change content to void consent: next refuses approval-revert-pending across restart until both token and entry are reverted; no round opens with either remaining (AC-0048). Only eugenelim writes Approved.
- Risk triggers/Agent Rules/accepted-risk changes exercise open/parked consent and completed-round/pre-consent below/at allowance, plus in-progress rounds. Voiding precedes waiting: further round below allowance, fresh unreviewed cap at allowance, re-run in-progress round; another change reissues the cap (AC-0044).

**Done when:** the T4 tests pass.

### T5: Review rounds, report paths and classification

**Satisfies:** AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_rounds.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_classifier.py`, `packs/core/tests/skills/new-spec/fixtures/`

**Tests:**

Mode: TDD over recorded reports; classifier equivalence is goal-based.

- Required roles/keys and all-role barrier (AC-0022); wrong derived path and unignored reviews directory (AC-0023).
- Link/non-regular/over-1-MiB report refuses. Two clean roles and repeated clean rounds accept identical `Clean — ready to commit.` bytes in distinct request files; second answer to one request refuses request-consumed. Pending identical recovery does not count as consumption (AC-0024, AC-0020).
- Unavailable reviewer/adjudicator and every real invalid/indeterminate reason stop with no next request (AC-0025). Adjudication cases: unreadable, envelope-headings, prose-before-envelope, audit-numbered-finding, indeterminate-present, indeterminate-audit-not-none, sustained-line-shape, legacy-report, finding-unanchored, no-actionable-result.
- Real review-artifact.py agrees on classification/reason/count/footer (AC-0026); clean without footer skips adjudication; findings/footer invokes it; reviewer-equal adjudicator refuses (AC-0027).
- Author-equal reviewer is weak, never converged (AC-0028); sustained findings below allowance revise/review (AC-0029); refuted-only converges (AC-0030).
- Default 3/configured allowance, weak-last-round priority, cap without revise and blocked further rounds after either still-valid consent follow AC-0031/AC-0044.

**Done when:** the T5 tests pass.

### T6: Consent requests, `park`, `gates` and the digest copy

**Satisfies:** AC-0032, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037

**Depends on:** T5

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_consent.py`, `packs/core/tests/skills/new-spec/test_spec_supervisor_digest.py`

**Tests:**

Mode: TDD; digest equivalence is goal-based.

- Reviewed/unreviewed cap/weak prompts match AC-0032, including marker, consequence text and only two unreviewed answers. References cover absolute/traversal/hidden/escape/symlink/non-regular paths and lines 0/1/2147483647/2147483648; only confined valid references survive.
- Consent uses fixed fields; every other output surface, including stdout/stderr and lint output, neutralizes the full is_hidden_char/_unsafe corpus, marks untrusted and bounds 512/513-character input (AC-0033).
- Unchanged open consent repeats without writes; parked consent refuses parked across restart; changed identity voids before waiting; no purported answer completes core consent (AC-0034).
- Park records AC-0035 fields, clock time and marker without commit/tracked changes.
- Admission records its run branch ref; listing uses that ref even from another checkout branch and lists invalid for a missing/unresolvable ref (AC-0001, AC-0035, AC-0036).
- Listing is pending initially, stale after a content commit at the run branch tip (including identity-only voiding), unchanged by working-tree-only edits, invalid after malformed records, read-only and free of reviewer/human text (AC-0036).
- Full Design corpus matches real gate_digest results/refusals, in pack tests, closeout and corpus suite (AC-0037).

**Done when:** the T6 tests pass and the end-to-end integration test passes.

### T7: Pins

**Satisfies:** AC-0038, AC-0039, AC-0040

**Depends on:** T6

**Touches:** `packs/core/.apm/skills/new-spec/scripts/spec-supervisor.py`, `packs/core/.apm/skills/new-spec/supervisor.toml`, `packs/core/tests/skills/new-spec/test_spec_supervisor_pins.py`

**Tests:**

- Goal-based: admission/manifest pins cover every portable script at every depth except __pycache__, plus manifest/policy (AC-0038).
- TDD: each admission-reading verb rejects modified/added/removed scripts, manifest/policy changes and later dot-files. Start/gates use their specified sources; gates takes admission pins from the recorded run branch ref even when another branch is checked out; missing/unresolvable refs list invalid; planted bytecode never runs; __pycache__ is excluded (AC-0039).
- Combined faults put confinement first, pins second, remaining checks last; restored pins pass by net comparison. Recorded trees match real work-supervisor pin digests except core's declared refusals (AC-0039, AC-0040).

**Done when:** the T7 tests pass.

### T8: Release records, projections, eval and closeout evidence

**Satisfies:** AC-0019, AC-0041, AC-0042, AC-0049

**Depends on:** T7

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `packs/core/.apm/skills/new-spec/evals/`, `.claude/skills/new-spec/`, `.agents/skills/new-spec/`

**Tests:**

Mode: goal-based closeout.

- Core-release eval drives the supervisor path and expects consent to remain incomplete (AC-0049); this non-cosmetic release updates the eval harness independently of gates T8.
- Matching versions one patch above main, changelog validation, committed clean projections after build-self (AC-0041).
- Added-line-only citation scan under packs against origin/main (AC-0042); no work-loop pin-set path or rewritten projection (AC-0019).
- Record targeted pack tests, `make precheck PRECHECK_ARGS="--with-tests --base origin/main"` and one test-corpus.yml dispatch covering AC-0037.

**Done when:** the T8 checks pass and the closeout runs are recorded in the verification ledger.

### T9: Page 05 update

**Satisfies:** none — Durable Outputs architecture alignment

**Depends on:** T8

**Touches:** `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`

**Tests:**

Mode: goal-based page read. Align these page-05 points:

1. Section 5: start creates ledger; steps are never reverted; ledger removal does not bypass historical restrictions even with purported answers; partial migration resumes from ledger/history.
2. Sections 3/4: protected-content checks accept unrelated commits; known-commits remains provisional.
3. Sections 2/3: five core kinds, six stages, three consent gates and fixed answer prompts; core consent never completes.
4. Section 3: own park fields, branch-tip listing states, terminal reasons, identity/voiding, non-shrinking roles and destructive security review.
5. Sections 3/7: self-reported profiles do not prove independent review.
6. Section 8: bytecode exclusion, portable names, pin restoration and historical admission limits.
7. Section 3: core approval/revert exception and accepted forgery risks; gates adds answer-driven transitions.

**Done when:** the page read finds no contradiction with this spec.

## Rollout

Delivery is one change set with no flag. Rollback removes the new files, since nothing calls the supervisor until `spec-supervisor-gates` and the `work-loop` driver line land.

A core pack release carries it to adopters, ahead of the gates release. `work-supervisor.py` and its pin set are unchanged, so its pin is unaffected. No infrastructure or external system is involved.

## Risks

The spec owns accepted risks. T3 checks coexistence and recovery; T4 checks protected edits/identity; T5 checks request-local replay; T6/T7 compare copied behavior with real oracles. Gates alone owns answer-driven completion.

## Changelog
