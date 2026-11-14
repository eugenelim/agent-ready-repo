# Plan: Platform engineering release evidence collection, admission and focused review

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_handoff.py` (confined reads, `validate_bytes`, `Refusal`, stable issue codes, strict YAML/JSON parse, atomic no-overwrite output, `SafeParser`, UTF-8 stream setup); `packs/release-engineering/.apm/skills/release-loop/assets/image-only-ci-caller/` (valid fixture and trusted policy); `packs/release-engineering/tests/skills/release-loop/test_release_handoff_caller_example.py` (pack-qualified module loading, temp-root fixtures); `packs/release-engineering/.apm/agents/release-lead.md`; `packs/iac-terraform/.apm/skills/generate-iac/scripts/authoring_gate.py` (the review-record derivation style to mirror, not import). `release_admission.py` keeps its own small confinement and parse helpers or loads `release_handoff.py` by file path from its own skill folder; the choice is implementation-discovered and no script is put on `sys.path`.

> **Plan contract:** Tests, Touches and Done when are completion fields.
> Design, Approach, Grounding and Risks are working material. Execution evidence
> belongs in `notes/verification-ledger.md`, not in this plan.

## Approach

Two stdlib scripts carry the mechanical gates so refusals are testable without prose: a collector (new skill) and an admission/review/stage script (in `release-loop`). Procedure prose then references them, two reviewer agents and two canonical checklists replace the borrowed reviewers, and core-absent journeys prove the chain. Script work is TDD and DEEP; prose is content-pinned; journeys are integration. Eight task units, each depending only on earlier evidence.

## Constraints

- [ADR-0071](../../adr/0071-pack-runtime-export-boundary-and-test-placement.md) governs runtime exports, test placement and skill-local evals; [ADR-0101](../../adr/0101-pack-test-isolation-by-default-with-declared-compatibility-classes.md) governs isolated pytest processes.
- No dependency, no cross-pack import, no change to core, hooks, adopter workflow policy or the `pack.toml` dependency tables. `.apm/` content cites no internal records.
- Neither script runs a process, opens a network connection, deploys or fetches.
- Known CI registration traps (run locally before the end): `pytest tests/roster/`, `tools/lint-pack-test-boundary.py`, a changelog fragment, version parity in `pack.toml` and `.claude-plugin/plugin.json`, and the roster tests that pin the pack version and agent counts.

## Construction tests

**Integration tests:** Each suite loads the shipped script with `spec_from_file_location` under `release_engineering_<skill>_<script>`, registers it in `sys.modules`, then calls `exec_module`. A small subprocess layer checks argv, UTF-8, JSON stdout and exit codes. Journeys build candidates in a temporary root from the image-only caller fixture and a new infrastructure-only fixture owned by the release pack's tests; no read from `guides/` and no read from another pack.

**Manual verification:** Run each documented command against the built projection and record command, exit code and JSON in the verification ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Admission, review and stage script | T1 to T4 | Pack suite results | Spec contract and files resolve |
| Collector skill and script | T5 | Pack suite results | Skill and script resolve |
| Reviewers, references, loop and lead procedure | T6 | Content-pin results | One checklist per role |
| Journey proof | T7 | Isolated-root runs | Ledger transcript |
| Guides, evals, version, history | T8 | Link checks, parity, fragment | Destinations current |

## Design (LLD)

### Interfaces & contracts

Owned by: T1 to T5

Traces to AC-0001 through AC-0030. `release_admission.py` has subcommands `admit`, `verify`, `check-review`, `check-stage` and `repair-handoff`; `collect_evidence.py` has `collect`. Both follow `release_handoff.py`'s shape: `SafeParser` that suppresses untrusted argv text, UTF-8 stream setup before the first print, one JSON object on stdout, stable code lists, `main(argv)` returning the exit code. Inputs parse as strictly as a candidate. Confinement opens with no-follow traversal and checks descriptor identity before and after the read. Size is checked from the descriptor before reading; evidence streams under the 536,870,912-byte limit.

### Data & schema

Owned by: T1 to T4

Traces to AC-0007 through AC-0029. The admission record, review record, final summary and repair handoff are internal JSON; no JSON Schema is shipped and the guide documents fields and codes without promising stability. The review derivation mirrors the infrastructure review derivation already shipped in `iac-terraform`, with role area sets and stage binding.

### Skill procedure

Owned by: T5, T6

Traces to AC-0031 through AC-0036. The collector skill is a thin procedure over its script and the existing validator. `release-loop` gains collection, admission, stage and repair sections; its inlined `quality-engineer` brief and `security-reviewer` routing become optional additions after the focused roles.

## Tasks

### T1: Admission pins a validated candidate and verify detects change

**Depends on:** none

**Verification mode:** TDD. Review shape: DEEP, confined to `admit`, `verify` and shared confinement helpers.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_admission.py`

**Tests:**
- Valid image-only fixture admits with exact digests, policy locator, attempt 1, default `max_attempts` 3, replaces null (AC-0007); each non-valid validator status, stale time and missing check refuses `candidate-invalid` (AC-0008).
- Target, policy-missing and exists refusals leave the existing file unchanged (AC-0009); a candidate whose evidence changed after assembly is refused (AC-0010).
- `verify` current, then one change at a time to candidate, policy (changed and deleted), evidence, target, clock and record (AC-0011).
- Replacement attempt count, inherited `max_attempts`, same-digest refusal, malformed replaced record, `attempt-limit`, and the `--max-attempts` with `--replaces` usage error (AC-0012); byte-identity of every input before and after (AC-0013).
- Every file argument as symlink, hard link, FIFO, escaping, oversized and swapped between open and read; no content or failed path in output (AC-0020 for these commands); UTF-8, one JSON object, exit codes (AC-0030).

**Done when:** `python3 -m pytest packs/release-engineering/tests/skills/release-loop/test_release_admission.py -q` passes and each refusal case fails when its check is removed.

### T2: Review records derive pass, blocked or insufficient-evidence

**Depends on:** T1

**Verification mode:** TDD for the script; goal-based for the two checklists. Review shape: DEEP for `check-review`, bounded prose for the references.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/.apm/skills/release-loop/references/reliability-review.md`, `packs/release-engineering/.apm/skills/release-loop/references/security-review.md`, `packs/release-engineering/tests/skills/release-loop/test_release_review_check.py`

**Tests:**
- Fully covered reliability and security records pass (AC-0014); drop, duplicate, add an outside area, mark a gap, per role (AC-0015).
- Blocker open versus resolved; blocker plus gap (AC-0016); empty, unknown, missing-file, digest-mismatched evidence with and without a `core-agent` reviewer (AC-0017).
- Mutated declared result, subject, target, checklist byte and admitted bytes (AC-0018); malformed-record matrix and reviewer-kind invariance (AC-0019); file-argument confinement and no content echo for this command (AC-0020).
- Each checklist names exactly its role's areas as headings with read targets, blocker criteria and coverage evidence, and no other file defines them (AC-0031).

**Done when:** the isolated suite passes and the checklist pins pass.

### T3: Stage checks refuse skipped, circular, stale and weakened review

**Depends on:** T2

**Verification mode:** TDD. Review shape: DEEP, confined to `check-stage`.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_stage_check.py`

**Tests:**
- Each stage's success progression and `authority_checks_required: true` (AC-0021, AC-0025); healthy `final` without a recovery record, and `recovery` after a blocked post-deploy record (AC-0022).
- Confinement matrix for every `check-stage` input: each review, the admission and `--final` (AC-0020).
- Skipped stage and missing reviewer matrix across stages and roles (AC-0022).
- Circular citation by id, by self and by later stage; runtime evidence missing, at the boundary time, one tick later, older, or shared with pre-deploy (AC-0023).
- Same image digest with a broader `permissions_digest`; changed target and subject; admission no longer current (AC-0024).
- `final` with each missing field and `not-torn-down`; recovery without failure evidence (AC-0025).
- Policy listing no reviews and waiver text in artifact and review change nothing (AC-0026); directive text with recomputed digests changes nothing, and without recomputation only digest refusals appear (AC-0027).

**Done when:** the isolated suite passes and each refusal case fails when its check is removed.

### T4: Repair handoff is bounded and redacted

**Depends on:** T1, T2, T3

**Verification mode:** TDD. Review shape: DEEP, confined to `repair-handoff` and redaction.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`

**Tests:**
- Owner id, `route` present only when recorded, otherwise `human-handoff`; each failure-input refusal writes nothing (AC-0028).
- A shared subprocess and socket prohibition seam runs every case of all five admission subcommands and the collector's suite reuses it (AC-0003).
- 4,096-byte and 20-excerpt bounds with a truncation marker; secret-shaped strings (bearer tokens, `key=value` secrets, long hex and base64 tokens, private-key blocks) never appear in output (AC-0028, AC-0029).
- Confinement and no-echo for the failure and admission arguments (AC-0020).

**Done when:** the isolated suite passes and each redaction case fails when its pattern is removed. The CodeQL clear-text-logging heuristic treats variables named like secrets or tokens as sensitive on printed paths, so redaction helpers avoid those names.

### T5: Collector skill assembles a candidate or reports exact gaps

**Depends on:** T1, T4

**Verification mode:** TDD for the script; goal-based content pins for the skill. Review shape: DEEP for the script, bounded prose for the skill.

**Touches:** `packs/release-engineering/.apm/skills/prepare-release-handoff/SKILL.md`, `packs/release-engineering/.apm/skills/prepare-release-handoff/scripts/collect_evidence.py`, `packs/release-engineering/tests/skills/prepare-release-handoff/test_collect_evidence.py`, `packs/release-engineering/tests/skills/prepare-release-handoff/test_skill_pins.py`

**Tests:**
- Complete request with a trusted policy reaches `ready`, digests match, exit 0 (AC-0001); each gap, including validator issues, with code, path and next action and no output bytes (AC-0002); the subprocess and socket seam fails every case without change (AC-0003).
- Locator confinement matrix and evidence-limit refusal without path echo (AC-0004); never-overwrite, atomic write and request malformed matrix (AC-0005); validator absent, and a missing, unconfined, malformed or request-supplied policy (AC-0006).
- SKILL.md states `ready`, `incomplete`, no implicit build/test/plan, no authority, optional core evidence only after the direct path, and no mandatory core or G4 dependence (AC-0035, AC-0036).

**Done when:** the isolated suites pass.

### T6: Reviewers, loop and lead use the focused roles

**Depends on:** T2, T3, T4, T5

**Verification mode:** Goal-based content pins plus manual read. Review shape: MIXED prose; no script code.

**Touches:** `packs/release-engineering/.apm/agents/release-reliability-reviewer.md`, `packs/release-engineering/.apm/agents/release-security-reviewer.md`, `packs/release-engineering/.apm/agents/release-lead.md`, `packs/release-engineering/.apm/skills/release-loop/SKILL.md`, `packs/release-engineering/.apm/skills/release-loop/references/runbooks.md`, `packs/release-engineering/tests/skills/release-loop/test_release_review_pins.py`

**Tests:**
- Agent frontmatter has no Edit, Write or Bash tool, each loads only its role reference, and each returns the three results and the record shape (AC-0032).
- `release-loop` and `release-lead` route to the focused roles, treat core reviewers as optional additions that cannot replace a local area, and drop the "reuse the reviewers, add none" and three-reviewer-ceiling claims (AC-0033).
- `release-loop` states the stage table, runtime-evidence rule, reassessment triggers, commit-ready-is-not-release-proof and no-authority rule (AC-0034); no mandatory core or G4 step on the new path and no token-saving claim (AC-0036).

**Done when:** the pin suite passes and a human read of both agents and the loop confirms the direct path is complete without core.

### T7: Core-absent journeys and failure cases pass

**Depends on:** T6

**Verification mode:** Integration. Review shape: bounded test unit.

**Touches:** `packs/release-engineering/tests/skills/release-loop/test_release_admission_journey.py`, `packs/release-engineering/tests/skills/release-loop/fixtures/`

**Tests:**
- Application-only chain: `collect` (which validates), `admit`, both reviews, `check-stage` through `pre-deploy` (AC-0037); infrastructure-only chain with a `terraform-plan` component and no image (AC-0038).
- Stale time, wrong subject digest, missing provenance, invalid `not-applicable` basis, missing reviewer role, absent or unreadable admission each fail with their code and stop later steps (AC-0039).
- Skipped `pre-deploy`, circular post-deploy review and post-deploy review reusing pre-deploy evidence are refused (AC-0040).
- The temporary root holds no core pack, no `.claude`, and no work-loop file.

**Done when:** the suite passes.

### T8: Guides, evals, version and gates pass

**Depends on:** T7

**Verification mode:** Goal-based checks. Review shape: MIXED integration wiring.

**Touches:** `packs/release-engineering/pack.toml`, `packs/release-engineering/.claude-plugin/plugin.json`, `packs/release-engineering/README.md`, `packs/release-engineering/JOURNEY.md`, `packs/release-engineering/.apm/skills/*/evals/evals.json`, `guides/release-engineering/**`, changelog fragment, generated self-host projections, roster or pin tests that name the pack version or agent set

**Tests:**
- Version parity 0.3.0 with dependency tables unchanged, fragment via `tools/changelog.py new` (AC-0041); eval cases for collection gaps, admission refusals, review results, stage refusals and the optional-core rule (AC-0042); guide pages and links (AC-0043).
- `make build-self` clean, `make lint-ruff lint-mypy`, `make precheck`, `pytest tests/roster/` and `tools/lint-pack-test-boundary.py` (AC-0044).

**Done when:** the named gates pass and each isolated pack suite folder (`tests/skills/release-loop` and `tests/skills/prepare-release-handoff`, one pytest process per folder) is green.

### T9: Repair credential redaction, unused unsafe evidence refusal and the final-stage guide row

**Depends on:** T8

**Verification mode:** TDD. Review shape: DEEP repair, bounded to redaction, evidence confinement in `check-review`, and one guide row.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `packs/release-engineering/tests/skills/release-loop/test_release_review_check.py`, `packs/release-engineering/tests/skills/release-loop/test_release_stage_check.py`, `guides/release-engineering/reference/release-admission.md`

**Tests:**
- A repair handoff over failure evidence holding an HTTP Basic credential header, a credential-bearing database URL, an AWS access-key-shaped value and a bracketed `password[]=` field never contains those strings, while ordinary text near them survives (AC-0028, AC-0029); each case fails on the pre-repair code.
- A review record holding an otherwise well-shaped evidence entry that no area cites, with an unsafe path (`..`, absolute, symlink), returns the confinement refusal from `check-review` and from `check-stage` rather than `pass` (AC-0020); a cited-and-unresolved entry keeps its existing outcome.
- The guide's final-stage row lists the pre-deploy pair, the post-deploy pair, the final-stage reliability and security records and the final summary, matching the script (AC-0043).

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T10: Redaction is structural and procedure evidence gaps name the right action

**Depends on:** T9

**Verification mode:** TDD. Review shape: DEEP repair, bounded to redaction in `release_admission.py` and one collector gap mapping.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/.apm/skills/prepare-release-handoff/scripts/collect_evidence.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `packs/release-engineering/tests/skills/prepare-release-handoff/test_collect_evidence.py`

**Tests:**
- Repair excerpts never retain the value of a `Cookie`, `Set-Cookie`, `Authorization` or `Proxy-Authorization` header line, a JSON string value whose key names a credential even when the value holds escaped quotes or backslashes, a three-segment JWT-shaped value including short segments and an empty signature, or a value from the existing T9 corpus; a corpus-driven test generates each shape in several surroundings (plain text, JSON, query string, shell export, YAML) and asserts none of the generated sensitive values survives while non-sensitive neighbouring words do (AC-0028, AC-0029); each shape fails on the pre-repair code.
- A phase procedure naming an absent evidence id yields `missing-evidence` with `next_action` `produce-evidence`, like every other unknown cited evidence id (AC-0002); fails on the pre-repair code.

**Done when:** both isolated suites pass and each new case fails on the pre-repair code.

### T11: Repair excerpts fail closed on credential-bearing lines

**Depends on:** T10

**Verification mode:** TDD. Review shape: DEEP repair, bounded to the redaction function in `release_admission.py`.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `guides/release-engineering/reference/release-admission.md`

**Tests:**
- Redaction is line-oriented and fails closed: after normalising each line (lower-casing, decoding JSON `\uXXXX` escapes, removing separators), a line containing a credential-naming word (password, passwd, secret, token, api key, credential, authorization, cookie, bearer, private key, session, signature, and the `-u`/`--user` options of a transfer command) is replaced whole by a redaction marker, and so are the continuation lines it opens (YAML `|` and `>` block scalars by indentation, TOML triple-quoted strings until the closing delimiter, backslash continuations, PEM blocks until their end line). The value-shape patterns from earlier tasks stay as a second layer for lines without such a word (AC-0028, AC-0029).
- Cases: JSON header objects with `Cookie` and `Proxy-Authorization` keys, `curl -u` and `curl --user`, a Unicode-escaped `password` key, YAML `password: |` and `client_secret: >` with indented values, TOML triple-quoted values, env-file backslash continuations, plus every shape from the T9 and T10 corpora; neighbouring benign lines survive and the 4,096-byte and 20-excerpt bounds still hold (AC-0028). Each new case fails on the pre-repair code.
- The guide states that excerpts are redacted line by line, fail closed, and that redaction is a safety net: a human must not rely on it to publish untrusted logs.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

## Rollout

A minor pack release adds a skill, two agents, a script and references and changes the loop procedure. The manifest still requires core until Section 5, so installs behave as before; rollback selects the prior release.

## Risks

- The checks verify structure, digests and evidence resolution, not whether a reviewer read the evidence honestly; the human reviewer carries that judgment.
- Reviewer context size and fault detection are measured at closeout; no saving is claimed until measured.
- A new agent changes the pack's agent roster, which several root tests pin; T8 finds and updates each.

## Changelog
- 2026-11-13: spec approved by eugenelim (scope)
- 2026-11-13: plan approved by eugenelim (build strategy)
