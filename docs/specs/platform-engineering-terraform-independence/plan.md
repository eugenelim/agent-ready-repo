# Plan: Platform engineering Terraform workflows independent of core and our ADR format

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/iac-terraform/.apm/skills/generate-iac/SKILL.md` Stage 0 and reviewers; `packs/iac-terraform/.apm/skills/generate-iac/scripts/plan_bundle.py` (confined reads, stable issue codes, SafeParser, UTF-8 stream setup, the closed-record validator style); `packs/iac-terraform/tests/skills/generate-iac/test_plan_bundle_caller_example.py` (pack-qualified module loading, temp-root fixtures); `packs/iac-terraform/.apm/skills/reconcile-iac/SKILL.md`. `plan_bundle.py` keeps its own confinement helpers and a sibling script may not import it by bare name; whether `authoring_gate.py` duplicates the small helpers or loads them by file path is implementation-discovered.

> **Plan contract:** Tests, Touches and Done when are completion fields.
> Design, Approach, Grounding and Risks are working material. Execution evidence
> belongs in `notes/verification-ledger.md`, not in this plan. Both human approval
> gates remain pending; this draft dispatches no implementation.

## Approach

One new stdlib script carries the two mechanical gates (governance summary, review record) so stop conditions are testable without prose. The skills then reference it, and a Terraform-only integration fixture proves the whole chain with a real built-in provider. Script work is TDD and DEEP; skill prose is content-pinned; the journey is integration. Five task units, ordered so each depends only on earlier evidence.

## Constraints

- [ADR-0071](../../adr/0071-pack-runtime-export-boundary-and-test-placement.md) governs runtime exports, test placement and skill-local evals; [ADR-0101](../../adr/0101-pack-test-isolation-by-default-with-declared-compatibility-classes.md) governs isolated pytest processes.
- No dependency, no cross-pack import, no change to core, hooks, adopter workflow policy or the `pack.toml` dependency tables. `.apm/` content cites no internal records.
- The script never runs Terraform, never fetches, never prints input content. Terraform runs only in the integration test's own subprocess calls.

## Construction tests

**Integration tests:** Each suite loads the shipped script with `spec_from_file_location` under `iac_terraform_generate_iac_authoring_gate`, registers it in `sys.modules`, then calls `exec_module`; `scripts/` is never put on `sys.path`. A small subprocess layer checks argv, UTF-8, JSON stdout and exit codes. The journey suite uses `shutil.which("terraform")`, `skipif` with a stated reason, `terraform init -backend=false` in a temporary repository, and the built-in `terraform_data` resource so no network or cloud account is needed.

**Manual verification:** Run each documented command against the built projection and record command, exit code and JSON in the verification ledger, together with one local run of the Terraform-only journey with the binary present.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Gate script and canonical checklist | T1, T2 | Pack suite results | Spec contract and files resolve |
| Skill procedure | T3 | Content-pin results | Both skills cite one checklist |
| Journey proof | T4 | Fixture run with real engine | Ledger transcript |
| Guides, evals, version, history | T5 | Link checks, version parity, fragment | Destinations current |

## Design (LLD)

### Interfaces & contracts

Owned by: T1, T2, T3

Traces to AC-0001 through AC-0017, AC-0034 through AC-0039 and AC-0041. `authoring_gate.py` follows `plan_bundle.py`'s shape: an argparse `SafeParser` that suppresses untrusted argv text, UTF-8 stream setup before the first print, one JSON object on stdout, a stable issue-code list, and `main(argv)` returning the exit code. Subcommands are `discover`, `check-summary` and `check-review`. The inputs are parsed with the same strictness as plan bundles (duplicate keys, non-finite numbers and over-size input refused before semantic checks); the exact reuse or small duplication of those helpers is implementation-discovered. Confinement opens files with no-follow traversal and checks descriptor identity before and after the read; it refuses on uncertainty. Source-too-large is checked from the descriptor's stat size before reading the bytes, and reads are capped.

### Data & schema

Owned by: T1, T2

Traces to AC-0001 through AC-0016. The summary and review record are internal; no JSON Schema file is shipped for them, and the guides document fields and codes without promising stability. The conflict rule compares `topic` and exact `requirement` strings from distinct source ids; semantic conflict between differently worded requirements is the agent's judgment recorded as an `unresolved` entry or two constraints, never detected by the script.

### Skill procedure

Owned by: T3

Traces to AC-0018 through AC-0023. Stage 0 becomes "Governance gate": collect sources, write the summary, run `check-summary`, stop on `stop`. The bootstrap offer, `work-intake`, `new-adr` and governance-index language move to a clearly optional integrations subsection that runs after the direct path. Core agents and modules are listed as optional additional reviewers. `reconcile-iac` Trigger 3 and step 1 use the same summary.

## Tasks

### T1: Governance summary discovery and check stop correctly

**Depends on:** none

**Verification mode:** TDD. Review shape: DEEP, confined to one script's first two subcommands.

**Touches:** `packs/iac-terraform/.apm/skills/generate-iac/scripts/authoring_gate.py`, `packs/iac-terraform/tests/skills/generate-iac/test_authoring_gate_summary.py`

**Tests:**
- Starting from a valid ready summary over a temporary repository with native ADRs and an instruction file, mutate one fact at a time to reach each stop code and assert code, exit status and absence of input text in both streams (AC-0001 through AC-0011, AC-0017).
- Build `discover` fixtures at 499, 500 and 501 files, a symlinked decision file, an oversized file and a directory outside the conventional set (AC-0012).
- `discover --target` chain cases: root only, nested scoped file, unrelated directory, escaping target (AC-0034); verbatim, missing and non-accepted `status_line` (AC-0035).
- Every file argument as symlink, hard link, FIFO, escaping path, oversized and swapped between open and read via an injected seam (AC-0038); a hostile directive fixture changes no result (AC-0039).
- Duplicate source ids with contradictory constraints (AC-0041); the native example's `* Status: accepted` line passes and a planned non-existent target is accepted for chain selection (AC-0034, AC-0035).
- Subprocess smoke for argv errors, UTF-8 and exit codes.

**Done when:** `python3 -m pytest packs/iac-terraform/tests/skills/generate-iac/test_authoring_gate_summary.py -q` passes and each stop-code case fails when its check is removed.

### T2: Review record check and canonical checklist

**Depends on:** T1

**Verification mode:** TDD for the script; goal-based for the checklist. Review shape: DEEP for `check-review`, bounded prose for the reference.

**Touches:** `packs/iac-terraform/.apm/skills/generate-iac/scripts/authoring_gate.py`, `packs/iac-terraform/.apm/skills/generate-iac/references/infrastructure-review.md`, `packs/iac-terraform/tests/skills/generate-iac/test_authoring_gate_review.py`

**Tests:**
- A fully covered record with matching digests returns pass (AC-0013); drop each of the seven areas in turn, then mark each `gap` in turn (AC-0014).
- An open blocker versus the same blocker resolved; blocker plus a gap derives insufficient-evidence (AC-0015).
- Mutated declared result, saved-plan byte and checklist byte (AC-0016); a `core-agent` reviewer entry changes no derived result; output contains no input content (AC-0017).
- Empty, unknown, missing-file and digest-mismatched evidence under a declared `pass` and with a `core-agent` reviewer (AC-0036); duplicate keys, areas and ids, unknown fields, bad enums, NaN, depth 33 and oversize input (AC-0037).
- The checklist file names exactly the seven areas as headings and each states read-targets, blocker criteria and coverage evidence (AC-0022 half).

**Done when:** the isolated `test_authoring_gate_*.py` suites pass and the checklist pin test passes.

### T3: Skills describe the direct governance, grounding and review path

**Depends on:** T1, T2

**Verification mode:** Goal-based content pins plus manual read. Review shape: MIXED prose; no script code.

**Touches:** `packs/iac-terraform/.apm/skills/generate-iac/SKILL.md`, `packs/iac-terraform/.apm/skills/generate-iac/references/{spec-plan-tasks-shape,bootstrap-sequence,terraform-verify-and-iterate,security-iam-standard,terraform-standard,provider-contract,release-loop-integration}.md`, `packs/iac-terraform/.apm/skills/reconcile-iac/SKILL.md`, `packs/iac-terraform/tests/skills/generate-iac/test_skill_independence.py`

**Tests:**
- Parse both SKILL.md bodies; assert no mandatory-step line requires core, repo-governance, `work-intake`, `new-adr`, a governance index or a bootstrap outside the optional integrations section (AC-0018).
- Assert the stop-on-refusal / no-weaker-fallback sentence in both skills and the Stage 2 input list and snapshot wording (AC-0019, AC-0020); the grounding and gated-chain wording (AC-0021).
- Assert `release-loop-integration.md` marks G4 artifacts, apply evidence, smoke results and core modules optional-release-only (AC-0040).
- Assert only `infrastructure-review.md` defines the seven area checklists and the other references link to it (AC-0022); `reconcile-iac` uses the summary and states the managed-only limit (AC-0023).

**Done when:** the pin suite passes, and a human read of both skills confirms the direct path is complete without any optional section.

### T4: Terraform-only journey and stop cases pass with a real engine

**Depends on:** T3

**Verification mode:** Integration plus recorded manual run. Review shape: bounded test unit.

**Touches:** `packs/iac-terraform/tests/skills/generate-iac/test_terraform_only_journey.py`

**Tests:**
- Positive journey in a temporary repository (AC-0024): ADRs and instruction file, summary, `check-summary` ready, `terraform init -backend=false`, `providers schema -json` asserted to contain each used resource type, `validate`, `plan -out`, `show -json`, digests, review record, `check-review` pass, then a plan bundle assembled from the real artifacts that `plan_bundle.py validate` accepts with a caller policy.
- Conflicting ADR constraints stop with no saved plan (AC-0025); symlinked ADR stops at `discover` with no `.tf` written (AC-0026); an invented resource type fails the gated chain with no saved plan (AC-0027).
- Review gap yields no bundle; adding a `used` integration and a `core-agent` reviewer leaves each earlier outcome identical (AC-0028).
- The suite skips with a stated reason when `terraform` is absent.

**Done when:** the suite passes locally with `terraform` present (transcript in the ledger) and skips cleanly without it.

### T5: Guides, evals, version and gates pass

**Depends on:** T4

**Verification mode:** Goal-based checks. Review shape: MIXED integration wiring.

**Touches:** `packs/iac-terraform/pack.toml`, `packs/iac-terraform/.claude-plugin/plugin.json`, `packs/iac-terraform/README.md`, `packs/iac-terraform/JOURNEY.md`, `packs/iac-terraform/.apm/skills/*/evals/evals.json`, `guides/iac-terraform/**`, changelog fragment, generated self-host projections

**Tests:**
- Version parity 0.4.0 in manifest and plugin with the dependency tables unchanged (AC-0029); fragment via `tools/changelog.py new` (AC-0030).
- Eval cases for direct governance, each stop outcome and the optional-integration rule in both skills (AC-0031); guide pages and links (AC-0032).
- `make build-self` clean, `make lint-ruff lint-mypy`, `make precheck` (AC-0033).

**Done when:** the named gates pass and the pack suite `python3 -m pytest packs/iac-terraform/tests/skills/generate-iac/ -q` is green.

### T6: Stop output hides discovered names and every cited evidence id must resolve

**Depends on:** T5

**Verification mode:** TDD. Review shape: DEEP repair, bounded to two checks in `authoring_gate.py`.

**Touches:** `packs/iac-terraform/.apm/skills/generate-iac/scripts/authoring_gate.py`, `packs/iac-terraform/tests/skills/generate-iac/test_authoring_gate_summary.py`, `packs/iac-terraform/tests/skills/generate-iac/test_authoring_gate_review.py`, `packs/iac-terraform/.apm/skills/generate-iac/references/infrastructure-review.md`, `guides/iac-terraform/reference/authoring-gate.md`

**Tests:**
- A `discover` run that hits the file limit, with a discovered file name containing a credential-like token, returns the `file-limit` code and exit status with no discovered file name on stdout or stderr (AC-0017).
- A `covered` area citing one resolving evidence id plus an unknown id, a missing file or a changed digest derives `insufficient-evidence` with `unresolved-evidence`, with and without a `core-agent` reviewer (AC-0036); each case fails on the pre-repair code.

**Done when:** the isolated pack suite passes, each new case fails on the pre-repair code, and the checklist and guide state that every cited evidence id must resolve.

### T7: Review checks accept real-sized saved plans and the evals match the stop output

**Depends on:** T6

**Verification mode:** TDD. Review shape: DEEP repair, bounded to the review-check read path and two eval expectations.

**Touches:** `packs/iac-terraform/.apm/skills/generate-iac/scripts/authoring_gate.py`, `packs/iac-terraform/tests/skills/generate-iac/test_authoring_gate_review.py`, `packs/iac-terraform/.apm/skills/generate-iac/evals/evals.json`, `packs/iac-terraform/.apm/skills/reconcile-iac/evals/evals.json`, `guides/iac-terraform/reference/authoring-gate.md`

**Tests:**
- `check-review` returns `pass` for a correctly bound saved plan and evidence file larger than 262,144 bytes (for example 700,000 bytes), hashing them by streaming under the 536,870,912-byte evidence limit used by plan-bundle validation, and still returns `source-too-large` above that limit; the checklist and summary sources keep their 262,144-byte limit (AC-0013); the case fails on the pre-repair code.
- Both eval expectations for the `file-limit` stop state the empty `sources` list and the code only (AC-0031); the guide states the two limits.

**Done when:** the isolated pack suite passes and the first case fails on the pre-repair code.

## Rollout

A minor pack release adds the script and checklist and changes procedure. The manifest still requires core and repo-governance until Section 5, so installs behave as before; rollback selects the prior release.

## Risks

- Bounded discovery can miss a repository's real convention directory; the caller names it explicitly and the summary records it, so the miss is a stop or an explicit input, never a silent pass.
- The script checks digests and structure, not whether the agent read a source faithfully; the review record's evidence ids and the human reviewer carry that judgment.
- Journey tests prove behavior only where the binary is installed; CI skips them until the owner adds a Terraform step.

## Changelog

- 2026-11-13: spec approved by eugenelim (scope)
- 2026-11-13: plan approved by eugenelim (build strategy)
