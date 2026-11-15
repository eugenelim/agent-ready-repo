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

### T12: Redaction covers more credential names, bare-key values and encoded keys; review check reports digest refusals only

**Depends on:** T11

**Verification mode:** TDD. Review shape: DEEP repair, bounded to the redaction function and one derivation path in `check-review`.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `packs/release-engineering/tests/skills/release-loop/test_release_review_check.py`, `guides/release-engineering/reference/release-admission.md`

**Tests:**
- Lines naming `passphrase`, `pwd`, `passwd`, `apikey`, `x-api-key`, `auth` or `credentials` as a key are redacted whole (AC-0028, AC-0029).
- A bare credential key whose value starts on the following line (YAML plain or block value, any of LF, CRLF, U+2028 or NEL line ends) redacts that following line too (AC-0029).
- Percent-encoded forms of a credential key (`pass%77ord=...`, fully encoded `password`) are decoded before the keyword test (AC-0029); each case fails on the pre-repair code.
- The guide states that redaction recognises English credential words and common encodings only, and lists no guarantee for other languages, quoted-printable or custom encodings.
- A review record whose cited evidence file changed without a digest update returns `unresolved-evidence` and no additional `result-mismatch`, matching `check-stage` (AC-0027); fails on the pre-repair code.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T13: Redaction drops nested JSON values under a credential key

**Depends on:** T12

**Verification mode:** TDD. Review shape: DEEP repair, bounded to the redaction continuation logic.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`

**Tests:**
- A credential-naming line that opens a JSON object or array (the line ends in `{` or `[`, or the value starts one that stays open) drops every following line until the matching close, counting brackets while ignoring brackets inside strings, including nested objects, arrays of objects and a value that spans several lines; neighbouring benign lines survive and a malformed or unclosed structure drops to the end of the excerpt (AC-0029); each case fails on the pre-repair code.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T14: Redaction drops the value that follows a bare credential key in any layout

**Depends on:** T13

**Verification mode:** TDD. Review shape: DEEP repair, bounded to the redaction continuation logic.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`

**Tests:**
- A credential key with no inline value (the line ends after the key, its colon or its equals sign) drops the next non-blank line whatever its indentation, and keeps dropping while the structure it opens continues: a YAML sequence whose `-` items sit at the key's own indentation, an indented block, or a JSON object or array whose opening bracket is on the next line, balanced as in the same-line case (AC-0029); neighbouring benign keys and lines survive; each case fails on the pre-repair code.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T15: Redaction handles YAML anchors and tags, and the repair route is sanitised

**Depends on:** T14

**Verification mode:** TDD. Review shape: DEEP repair, bounded to redaction and the `route` output.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `guides/release-engineering/reference/release-admission.md`

**Tests:**
- A credential key line whose remainder, after stripping YAML anchors (`&name`), tags (`!!str`, `!tag`) and aliases, is empty, a block indicator (`|`, `>`, with chomping or indentation marks) or an opening bracket opens a continuation exactly as the bare form does, so anchored and tagged block scalars and sequences are dropped (AC-0029); each case fails on the pre-repair code.
- The `route` copied from the candidate into the handoff is passed through the same redaction, and a URL userinfo section (`scheme://user:value@host`) or credential-named query parameter is replaced by a redaction marker; a benign route is unchanged (AC-0028, AC-0029); fails on the pre-repair code.
- The guide states that the route is sanitised in the same way.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T16: Redaction covers multi-line YAML scalars and aliases, and the handoff declares best-effort

**Depends on:** T15

**Verification mode:** TDD. Review shape: DEEP repair, bounded to redaction and one output field.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `guides/release-engineering/reference/release-admission.md`, `packs/release-engineering/.apm/skills/release-loop/SKILL.md`

**Tests:**
- A credential key whose value is a multi-line double-quoted, single-quoted or plain YAML scalar (continuation lines until the closing quote, or until indentation returns for a plain scalar) and the explicit `? key` / `: value` layout drop the value lines, in excerpts and in the route (AC-0029).
- A credential key whose value is an alias (`*name`) also drops the line that defines the anchor `&name`, including the continuation lines of a multi-line anchored value (for example `shared: &a |` with an indented value under a non-credential key), and any other line using that alias; the complete referenced value is absent from the handoff (AC-0029); each case fails on the pre-repair code.
- The handoff carries `redaction: "best-effort"`; the guide lists the documented forms and the forms outside the guarantee; the loop procedure says a handoff must be reviewed by a human before it leaves the team (AC-0028).

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T17: Alias redaction covers anchored sequence items and the whole evidence

**Depends on:** T16

**Verification mode:** TDD. Review shape: DEEP repair, bounded to alias handling in redaction.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`

**Tests:**
- An anchor on a sequence item (`- &a |-` with indented continuation lines, quoted and plain multi-line variants, and a single-line `- &a value`) is dropped, with its continuation lines, when a credential key aliases it (AC-0029); each case fails on the pre-repair code.
- Alias analysis reads the whole evidence file within the existing evidence size limit rather than a fixed 8,192-byte prefix: an anchor defined near the start with the credential alias after 800 or more further entries is still redacted, while the excerpt and its 4,096-byte bound stay unchanged (AC-0029); fails on the pre-repair code.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T18: Circular-review detection ignores evidence ids, and redaction handles comments and continued options

**Depends on:** T17

**Verification mode:** TDD. Review shape: DEEP repair, bounded to circular-review detection and two redaction paths.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_stage_check.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`

**Tests:**
- A passing reliability and security pair whose evidence ids equal a review file's name stem (for example `pre-deploy-reliability`) is still accepted by `check-stage`; a record that genuinely cites a review record as evidence, by evidence path or digest of a supplied review record, is still refused `circular-review` (AC-0021, AC-0023); each case fails on the pre-repair code.
- YAML comment lines (and blank lines) between a credential key and its value or alias do not clear alias or continuation context, for scalar, sequence and multi-line anchored forms and in the route (AC-0029).
- A `-u`, `--user` or `--header` authentication option on a continuation line of a backslash-continued command, and a transfer command other than `curl` (`wget --user`, `http --auth`), drops the option's value (AC-0029); each case fails on the pre-repair code.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T19: Credential options are redacted wherever they appear

**Depends on:** T18

**Verification mode:** TDD. Review shape: DEEP repair, bounded to option redaction.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`

**Tests:**
- A `-u` or `--user` option with a `user:value` or bare value drops the value on any line, with or without a transfer command on that line or an earlier one, including at the start of a line, after a pipe or in a quoted argument list (AC-0029); a benign `-u` flag with no value-shaped argument (for example `-u` before another option) keeps the line; each case fails on the pre-repair code.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T20: Review check reports result-mismatch again, and the loop's final-stage row names the final pair

**Depends on:** T19

**Verification mode:** TDD. Review shape: DEEP repair, bounded to one derivation path and one table row.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_review_check.py`, `packs/release-engineering/.apm/skills/release-loop/SKILL.md`, `packs/release-engineering/tests/skills/release-loop/test_release_review_pins.py`

**Tests:**
- A valid review whose declared result is `pass` and whose cited evidence id is unknown, or whose evidence digest changed, returns `unresolved-evidence` together with `result-mismatch` and derives `insufficient-evidence` (AC-0018, AC-0027); fails on the pre-repair code. A directive-bearing evidence fixture with digests recomputed returns the same codes as without it (AC-0027).
- The `release-loop` stage table names the final-stage reliability and security records in the `final` row, and a pin asserts it (AC-0034).

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T21: A credential option whose value is on the next continued line is redacted

**Depends on:** T20

**Verification mode:** TDD. Review shape: DEEP repair, bounded to option continuation handling.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`

**Tests:**
- A `-u` or `--user` option that ends its line (or ends it with a backslash continuation) drops the next line that carries its value, for `curl`, `wget`, `http` and no-command layouts, with LF and CRLF line ends; a benign `-u` flag followed by another option keeps the following line (AC-0029); each case fails on the pre-repair code.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T22: Review findings repair: review binds the verified admission, collector refuses overlong integers, evidence labels are not citations, redaction closes six layouts

**Depends on:** T21

**Verification mode:** TDD. Review shape: DEEP repair, bounded to the named paths.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/.apm/skills/prepare-release-handoff/scripts/collect_evidence.py`, `packs/release-engineering/tests/skills/release-loop/test_release_review_check.py`, `packs/release-engineering/tests/skills/release-loop/test_release_stage_check.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `packs/release-engineering/tests/skills/prepare-release-handoff/test_collect_evidence.py`

**Tests:**
- `check-review` and `check-stage` bind to the admission bytes that `verify` actually checked: an admission file replaced between verification and use is refused (an injected seam swaps it), never used for target or subject binding (AC-0018, AC-0020).
- A collection request holding an integer over 4,300 digits, or any value the JSON copy cannot serialise, returns the structured error result with exit 2 and no traceback on either stream (AC-0005).
- `check-stage` accepts independent post-deploy runtime evidence whose record-local evidence id repeats a pre-deploy id when path and digest differ and the observation is later; it still refuses evidence reused by path or digest (AC-0023).
- Redaction: an alias reaching a credential through a nested alias in an anchored value is removed with every referenced anchor value; an anchor whose properties sit on a separate line from the key (`shared:` newline `&a |` newline value) and its value lines are removed when aliased by a credential key; a continued `--user=` value on the next line is removed; a JWT whose first segment is any base64url encoding of a JSON object (not only `eyJ`) with up to three segments is removed (AC-0029); each case fails on the pre-repair code.

**Done when:** the isolated suites pass and each new case fails on the pre-repair code.

### T23: Every command that verifies an admission uses the verified bytes

**Depends on:** T22

**Verification mode:** TDD. Review shape: DEEP repair, bounded to admission loading in `release_admission.py`.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `packs/release-engineering/tests/skills/release-loop/test_release_admission.py`

**Tests:**
- `repair-handoff` binds to the admission bytes that `verify` checked: an admission replaced between verification and use (an injected seam swaps it) is refused and never used for target, subject or owner binding (AC-0020, AC-0028); every other command that loads an admission after verifying it (`check-review`, `check-stage`, `repair-handoff`) shares one load-and-verify path, and a test swaps the file at that seam for each command; each case fails on the pre-repair code.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T24: Redaction fails closed on anchors and credential options, and runtime evidence times compare at full precision

**Depends on:** T23

**Verification mode:** TDD. Review shape: DEEP repair, bounded to redaction policy and timestamp comparison.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `packs/release-engineering/tests/skills/release-loop/test_release_stage_check.py`, `guides/release-engineering/reference/release-admission.md`

**Tests:**
- When an excerpt's text contains YAML anchor or alias syntax (`&name`, `*name` used as YAML properties) and any credential-named line, the whole excerpt is replaced by a single redaction marker instead of tracing individual values; tagged separate-line anchors, nested aliases through sequences at the parent's indentation, and multi-line flow sequences are all covered by that rule, and an excerpt with anchors but no credential-named line is unchanged (AC-0029); each case fails on the pre-repair code.
- A credential option (`-u`, `--user`, `--user=`) drops its value and every following line of the same continued command, however many continuation or blank lines intervene, and attached values that begin with a hyphen (`--user=-name:value`) are dropped; a benign separate option is kept (AC-0029); each case fails on the pre-repair code.
- Runtime-evidence freshness compares RFC 3339 times at nanosecond precision, so a post-deploy time one nanosecond later than the latest pre-deploy time is accepted and an equal time is refused (AC-0023); fails on the pre-repair code.
- The guide states the whole-excerpt rule for anchors beside credential lines and the continued-command rule.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T25: Redaction is document-level fail-closed and linear in time

**Depends on:** T24

**Verification mode:** TDD. Review shape: DEEP repair, bounded to the redaction policy.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `guides/release-engineering/reference/release-admission.md`

**Tests:**
- The redaction decision is made on the whole evidence text, not per line: when any credential word of the documented list, any credential option (`-u`, `--user`, `--user=`, quoted or attached in any form), any HTTP authentication or cookie header, URL userinfo, or any anchor or alias beside such content appears anywhere in the evidence, the excerpt text is replaced by a single redaction marker that states only that credential-like content was withheld; text with none of these is passed through after value-shape redaction of JWT, AWS access-key and PEM shapes (AC-0028, AC-0029). The earlier per-line and layout cases (quoted continued options, split JSON keys, hyphen-leading attached values, anchors and aliases, multi-line scalars, next-line values) all produce the marker; each fails on code before T25 where it leaked.
- A benign evidence file with no credential word is returned unchanged within the bounds and keeps `redaction: "best-effort"` (AC-0028).
- Redaction takes time linear in the evidence size: inputs of 64 KiB, 512 KiB and 4 MiB of plain `a` and of credential-word-free log lines complete within a bounded multiple of the 64 KiB time, with no pattern that rescans the remaining input per match (AC-0029); fails on the pre-repair code at 64 KiB.
- The guide states the document-level rule and its cost: evidence mentioning credential words is withheld and the repair owner opens it from the protected store.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T26: Handoff metadata, sensitive plan evidence, encoded userinfo and adjacent JWTs

**Depends on:** T25

**Verification mode:** TDD. Review shape: DEEP repair, bounded to `repair-handoff` output construction.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `guides/release-engineering/reference/release-admission.md`

**Tests:**
- Every string the handoff copies from the evidence or the failure record, including evidence ids and the check id, passes the same document-level decision as excerpt text: a credential-shaped id is replaced by a neutral positional label (`evidence-1`) and is never printed (AC-0029).
- The handoff never carries sensitive plan bytes: an evidence entry whose `kind` names a plan or state artifact, or whose parsed content holds Terraform plan or state structure (`planned_values`, `resource_changes`, `prior_state`, `terraform_version` with `configuration`, or `sensitive_values`), has its excerpt withheld with the marker `withheld: sensitive-plan` while id, digest and size remain (AC-0028, AC-0029); each case fails on the pre-repair code.
- URL userinfo is detected before and after percent-decoding (`%2F`, `%20`, `%40` and similar inside the userinfo): any `://` followed by non-slash characters and `@` before the next slash withholds the excerpt (AC-0029).
- A JWT-shaped value (two or three base64url segments whose first segment decodes to a JSON object) is detected wherever it appears, including when followed by punctuation or an ellipsis, and withholds the excerpt (AC-0029); each case fails on the pre-repair code.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T27: Redaction normalises escapes and quoting first, circularity binds verified bytes, plan withholding follows digest

**Depends on:** T26

**Verification mode:** TDD. Review shape: DEEP repair, bounded to redaction normalisation, circular-review byte binding and sensitive-plan classification.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `packs/release-engineering/tests/skills/release-loop/test_release_stage_check.py`, `guides/release-engineering/reference/release-admission.md`

**Tests:**
- Before the document-level decision, the text is normalised in one linear pass that decodes JSON escapes (`\/`, `\uXXXX`), YAML escapes (`\xNN`, `\uXXXX`, `\UXXXXXXXX`) and percent-encoding, and removes shell quote characters and backslash-newline joins, so `"pass\x77ord"`, `https:\/\/user:value@host`, and `--us'er'=value` are decided as their plain forms and withhold the excerpt (AC-0029); each case fails on the pre-repair code.
- `check-stage` decides circular citation from the same evidence bytes it verified: evidence replaced between hashing and the circularity inspection (an injected seam) is refused and never changes a `circular-review` refusal into progression (AC-0023, AC-0020).
- Sensitive-plan withholding follows content: evidence whose bytes equal an admitted plan component's bytes (by SHA-256) is withheld wherever it is located and whether or not a `kind` is given (AC-0028, AC-0029); fails on the pre-repair code.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T28: Normalisation reaches a bounded fixpoint and every check runs on the normalised text

**Depends on:** T27

**Verification mode:** TDD. Review shape: DEEP repair, bounded to the redaction normaliser.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `guides/release-engineering/reference/release-admission.md`

**Tests:**
- Normalisation (JSON, YAML and percent decoding, shell quote removal, backslash-newline joins) repeats until the text stops changing or four passes have run, each pass linear in the text; the credential-word, option, header, URL userinfo, anchor, JWT, AWS access-key and PEM checks run on the original text and on every normalised form, so combined encodings (`https:\/\/user%2Fname:value@host`, a JSON `\u0041` inside an AWS key shape, escapes inside percent-encoding) withhold the excerpt (AC-0029); each case fails on the pre-repair code.
- A text that still changes after four passes is withheld whole; benign text unchanged by normalisation is returned within the bounds; the 64 KiB, 512 KiB and 4 MiB timing bound from the earlier linear-time test still holds with the repeated passes (AC-0029).

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T29: Backslash-quoted options are normalised, and admission and reader share one target limit

**Depends on:** T28

**Verification mode:** TDD. Review shape: DEEP repair, bounded to the redaction normaliser and admission target limits.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `packs/release-engineering/tests/skills/release-loop/test_release_admission.py`

**Tests:**
- A shell backslash before an ordinary character is removed by the normaliser (`--us\er=value`, `-\u value`), so the options are decided as `--user` and `-u` and withhold the excerpt (AC-0029); each case fails on the pre-repair code.
- `admit` refuses (`candidate-invalid` or a dedicated refusal) a candidate whose target environment or account is longer than the length the admission reader accepts, or the reader accepts what validation accepts: a copied fixture with a 4,097-character environment either fails at admission or verifies `current`, never admits and then fails `verify` (AC-0007, AC-0011); fails on the pre-repair code.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T30: Command invocations are withheld whole, control characters are normalised, and admission matches its reader

**Depends on:** T29

**Verification mode:** TDD. Review shape: DEEP repair, bounded to redaction policy, normalisation and admission record limits.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `packs/release-engineering/tests/skills/release-loop/test_release_admission.py`, `guides/release-engineering/reference/release-admission.md`

**Tests:**
- An excerpt whose text holds an invocation of a transfer, authentication or client command (`curl`, `wget`, `http`, `https`, `ssh`, `scp`, `sftp`, `docker login`, `psql`, `mysql`, `aws`, `gcloud`, `kubectl`, `helm`, `git` with a URL) is withheld whole, whatever its options (grouped `-vu`, `-su`, `$'..'` quoting, `\u` escapes inside option names, attached values) (AC-0029); each case fails on the pre-repair code.
- URL userinfo is detected when percent-decoding introduces control characters, including `%0A` and `%0D` before the `@` (AC-0029).
- `admit` and the admission reader share one validation: a timestamp with a very long fractional part is refused or accepted identically by both, and an uncited external evidence entry with a supplied digest is admitted when the validator reports `valid`, with its digest recorded and not read as a local file, and verifies `current` (AC-0007, AC-0011); each case fails on the pre-repair code.
- The guide states the command-invocation rule.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T31: Client commands are detected as substrings of de-quoted text

**Depends on:** T30

**Verification mode:** TDD. Review shape: DEEP repair, bounded to client-command detection.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `guides/release-engineering/reference/release-admission.md`

**Tests:**
- Client-command detection is a case-insensitive substring search over the normalised text after every shell quoting and expansion character (`$`, quotes, backslashes, backticks, braces, parentheses, control characters) is removed, with no word-boundary or whitespace requirement, so `curl</dev/null -vu x:y`, `mysql</dev/null -pvalue`, `cu$'rl' -vu x:y`, JSON argument arrays (`["curl","-u","x:y"]`), `c""url` and `CURL` all withhold the excerpt; client names include `curl`, `wget`, `http`, `ssh`, `scp`, `sftp`, `psql`, `mysql`, `aws`, `gcloud`, `kubectl`, `helm` and `docker login` (AC-0029); each case fails on the pre-repair code.
- Benign text without any listed name is returned unchanged within the bounds (AC-0028); the guide states that detection is a substring match and may withhold harmless text.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T32: The repair route keeps its own sanitising rule, and a supplied recovery security refusal stops recovery

**Depends on:** T31

**Verification mode:** TDD. Review shape: DEEP repair, bounded to route sanitising and the recovery stage check.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `packs/release-engineering/tests/skills/release-loop/test_release_stage_check.py`

**Tests:**
- The `route` is sanitised only for URL userinfo and credential-named query parameters, not by the client-command substring rule: `https://example.invalid/repair` and a `mailto:` or chat-hook route that holds no userinfo are returned unchanged and the handoff reports `handoff`; a route with userinfo or a credential query value is replaced and the handoff reports `human-handoff` because the recorded route is unusable (AC-0028); each case fails on the pre-repair code.
- `check-stage --stage recovery` refuses when a supplied same-stage security record is `blocked` or `insufficient-evidence` or holds an open blocker, while a missing security record at recovery stays allowed and a failed post-deploy review stays allowed as recovery's input (AC-0022, AC-0025); fails on the pre-repair code.

**Done when:** the isolated release-loop suite passes and each new case fails on the pre-repair code.

### T33: Route credentials anywhere, target extensions, host-neutral reviewer paths, and current published docs

**Depends on:** T32

**Verification mode:** TDD for the scripts; goal-based pins for prose. Review shape: DEEP for the script repairs, bounded prose for the docs.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `packs/release-engineering/tests/skills/release-loop/test_release_admission.py`, `packs/release-engineering/.apm/agents/release-reliability-reviewer.md`, `packs/release-engineering/.apm/agents/release-security-reviewer.md`, `packs/release-engineering/tests/skills/release-loop/test_release_review_pins.py`, `guides/release-engineering/explanation/the-release-loop.md`, `guides/release-engineering/reference/release-admission.md`, `packs/release-engineering/README.md`, `packs/release-engineering/JOURNEY.md`, `packs/release-engineering/.apm/skills/release-loop/references/runbooks.md`

**Tests:**
- A route holding a credential word or a value in its fragment, path or query (`#password=...`, `/token/...`) is replaced and the handoff reports `human-handoff`; the userinfo and credential-query rules stay (AC-0028, AC-0029); each case fails on the pre-repair code.
- `admit` accepts a candidate whose `target` carries schema-supported `extensions` beside `environment` and `account`; the admission record keeps only environment and account, and `verify` returns `current` (AC-0007, AC-0011); fails on the pre-repair code.
- Both reviewer agents name their checklist by skill and file (`the release-loop skill's references/reliability-review.md`) and say to find it in the host's installed `release-loop` skill folder, with no relative `../skills` path that depends on one host's layout; a pin asserts no `../` in either agent (AC-0032).
- The published explanation, the readiness template wording and the pack README and journey describe the focused reliability and security reviewers, their records and the stage check, and no longer say that the pack ships no reviewers or that readiness consumes core reviewers' verdicts as its only source (AC-0033, AC-0043).

**Done when:** the isolated release-loop suite passes, each new script case fails on the pre-repair code, and the named docs are current.

### T34: Collector ids do not collide, docker global options are caught, and the remaining published pages and generated journey are current

**Depends on:** T33

**Verification mode:** TDD for the scripts; goal-based for prose and generated output. Review shape: DEEP for the script repairs, bounded prose for the docs.

**Touches:** `packs/release-engineering/.apm/skills/prepare-release-handoff/scripts/collect_evidence.py`, `packs/release-engineering/tests/skills/prepare-release-handoff/test_collect_evidence.py`, `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py`, `packs/release-engineering/tests/skills/release-loop/test_release_repair_handoff.py`, `guides/release-engineering/tutorials/your-first-release.md`, `guides/release-engineering/reference/release-readiness-record.md`, `web/src/content/journeys/release-engineering.md`

**Tests:**
- A collection request whose component id equals an evidence id, or two components share a digest, no longer lets one entry overwrite another's digest: components and evidence ids live in separate lookups, a component id equal to an evidence id is accepted when the references still resolve and refused with a stable gap code when they are ambiguous, and every digest in the written candidate equals its file's SHA-256 (AC-0001, AC-0002); each case fails on the pre-repair code.
- A client-command withhold covers `docker` with any global options before `login` (`docker --config cfg login -p value registry`): the substring `docker` together with `login` anywhere in the normalised text withholds the excerpt (AC-0029); fails on the pre-repair code.
- The tutorial and the readiness-record reference describe the reliability and security reviewer records, the stage check results and the human decision as the readiness inputs, and name `quality-engineer` and `security-reviewer` only as optional additional reviewers (AC-0033, AC-0043).
- The generated journey page equals the output of the repository's journey build from the current `JOURNEY.md` (AC-0044); regenerate it with the repository's own build step and do not edit generated text by hand.

**Done when:** the isolated suites pass, each new script case fails on the pre-repair code, and `pytest tests/roster/test_registry_upgrade_notes.py` reports the journey build unchanged.

### T35: The collector decides missing cited evidence itself, accepts large integers in extensions and refuses credentialed routes

**Depends on:** T34

**Verification mode:** TDD. Review shape: DEEP repair, bounded to `collect_evidence.py` and one guide sentence.

**Touches:** `packs/release-engineering/.apm/skills/prepare-release-handoff/scripts/collect_evidence.py`, `packs/release-engineering/tests/skills/prepare-release-handoff/test_collect_evidence.py`, `guides/release-engineering/reference/release-admission.md`

**Tests:**
- Every evidence id cited anywhere in the request (components, provenance, checks, and phase procedures) is resolved by the collector before the validator runs, and an unknown id is the gap `missing-evidence` with `next_action` `produce-evidence`; validator issues for any other cause keep `fix-candidate`; the guide states exactly that split (AC-0002, AC-0043); the phase-procedure case fails on the pre-repair code as a collector-originated gap.
- An integer over 4,300 digits inside permitted `extensions` is kept as inert text and does not stop collection, while the same integer in a normative field is still refused (AC-0001, AC-0005); fails on the pre-repair code.
- A `repair_owner.route` holding URL userinfo, a credential-named query parameter, or a credential word anywhere in the route is a gap `unsafe-route` with `next_action` `supply-route` and no candidate is written (AC-0002); a plain `https://` route is accepted unchanged; fails on the pre-repair code.

**Done when:** the isolated suites pass and each new case fails on the pre-repair code.

## Rollout

A minor pack release adds a skill, two agents, a script and references and changes the loop procedure. The manifest still requires core until Section 5, so installs behave as before; rollback selects the prior release.

## Risks

- The checks verify structure, digests and evidence resolution, not whether a reviewer read the evidence honestly; the human reviewer carries that judgment.
- Reviewer context size and fault detection are measured at closeout; no saving is claimed until measured.
- A new agent changes the pack's agent roster, which several root tests pin; T8 finds and updates each.

## Changelog
- 2026-11-13: spec approved by eugenelim (scope)
- 2026-11-13: plan approved by eugenelim (build strategy)
- 2026-11-13: amendment approved by eugenelim (scope)
- 2026-11-13: amendment approved by eugenelim (build strategy)
- 2026-11-14: amendment approved by eugenelim (scope)
- 2026-11-14: amendment approved by eugenelim (build strategy)
