# Spec: verify entries

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144
- **Brief:** none
- **Discovery:** docs/product/research/product-run-docs-survey.md
- **Depends on:** none
- **Contract:** contracts/delivery/evidence-receipt.v1.schema.json (consumed unchanged)
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

An agent running `work-loop` in any adopter repository proves a user-facing change by running a saved, repository-owned verify entry for each surface the change touches, and it creates or maps that entry at PLAN when one is missing, then proves the entry runs and can fail. Each run reports one grade that maps onto an `evidence-receipt.v1` record without a schema change, so a reviewer's behavior finding can carry a run wherever an entry covers the surface.

## What Changes

- A "Verify entries" section — `packs/core/.apm/skills/work-loop/references/verification-modes.md`: scope, locating or creating the file, map-first, proving an entry, recording and promoting, drift, fields and rules, grades, receipt mapping, placeholders, and trust.
- One sentence after the task-zero rule in PLAN step 7, and one item under "Verification passed" in the finish checklist — `packs/core/.apm/skills/work-loop/SKILL.md`.
- An entry template — `packs/core/.apm/skills/work-loop/assets/verify-entry.md`.
- Optional seeding of entries — `packs/core/.apm/skills/adapt-to-project/SKILL.md`.
- Eval cases — `work-loop` `evals/evals.json` and `adapt-to-project` `evals/eval_queries.json`.
- The adopter-facing explanation — `guides/core/explanation/core-pack.md`.
- This repository's own entry for the `agentbundle` CLI — `docs/VERIFICATION.md`, routed by a row in root `AGENT_RULES.md`; the roster test that pins root `AGENT_RULES.md` to the seed accepts adopter rows after the seed table.
- Self-host keeps a repository's root `AGENT_RULES.md` (seeded once, then repository-owned) — `EXCLUDED_PATTERNS` in `packages/agentbundle/agentbundle/build/self_host.py`, released as an agentbundle patch.
- The core version, a core changelog fragment, and the self-hosted projections.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | The doctrine an agent follows when it verifies a surface | `packs/core/.apm/skills/work-loop/references/verification-modes.md`, `SKILL.md`, `assets/verify-entry.md`, `packs/core/.apm/skills/adapt-to-project/SKILL.md` | core pack maintainers | `test_verify_entries_contract.py` green | suite green at the delivery commit; projections regenerated |
| Interface compatibility | Verify runs produce records in an existing contract | `contracts/delivery/evidence-receipt.v1.schema.json`, consumed unchanged | `acceptance-authority-and-evidence` contract owners | roster receipt test green; no schema diff | schema bytes unchanged against the merge base |
| User-facing promise | Adopters see `work-loop` propose a new or extended file in their repository | `guides/core/explanation/core-pack.md` | core pack maintainers | roster guide assertion | guide states the behavior |
| Operations | This repository's own way to drive its CLI surface | `docs/VERIFICATION.md`, root `AGENT_RULES.md` row | repository maintainers | live run and failing run in the verification ledger | live run's commit differs from the delivery commit in nothing the entry drives |
| Decision rationale | The default file name and detection order rest on research | `docs/product/research/product-run-docs-survey.md` | repository maintainers | survey retained | survey cited from this spec |
| Release history | A non-cosmetic pack change ships under a new version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a core fragment in `docs/product/changelog.d/` | core pack maintainers | version-equality assertion; `tools/check-core-release.py` exit 0 | release check recorded in the ledger |

## Agent Rules

### Always do

- Keep every sentence an existing test pins in the files this change edits; add text beside it.
- Keep the doctrine in `verification-modes.md`; `SKILL.md`, the template, `adapt-to-project`, and the guide point at it rather than restating it.
- Use placeholders (`<checkout>`, `<scratch>`, `<evidence-dir>`) for every path, host, and user in a recorded command, in the shipped template, in `docs/VERIFICATION.md`, and in the verification ledger.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together, and regenerate projections with self-host rather than editing them.
- Rebase onto freshly fetched `origin/main` before opening the PR, and merge after or before the concurrent run-based finding settlement change, never interleaved; that change owns `work-loop` FIX.

### Ask first

- Any edit to `contracts/delivery/evidence-receipt.v1.schema.json` or any other `contracts/delivery/` schema; a grade or field the contract cannot express is routed to its owners as an amendment instead.
- Any edit to `work-loop` scripts, `review-rules.json`, or `supervisor-policy.json`.
- Changing the `work-loop` FIX step, the risk triggers, or light/full mode selection.

### Never do

- No new skill, agent, script, dependency, or top-level directory; no new evidence-store writer or producer grant.
- No edit to an adapter projection except through self-host.
- No row in the core seed `AGENT_RULES.md`; the seed table ships empty.
- No citation of this repository's internal records (specs, ADRs, acceptance criteria) in shipped pack content.

## Testing Strategy

- **Shipped guidance (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0032, AC-0033, AC-0034, AC-0035):** goal-based, by pytest content tests in `packs/core/tests/skills/work-loop/test_verify_entries_contract.py`, each scoped to the section its rule lives in. A whole-file search would stay green if a rule moved out of the section an agent loads, so each test reads one bounded section.
- **Receipt fit (AC-0022):** goal-based, by a roster test in `tests/roster/test_verify_entry_receipts.py` that builds each receipt from the shipped section's stated fields and validates it against the schema with `jsonschema`. A pack test cannot read `contracts/`.
- **Dogfood entry (AC-0024, AC-0025, AC-0036, AC-0037):** goal-based, by the same roster test reading `docs/VERIFICATION.md`, the verification ledger, and root `AGENT_RULES.md`, and by `tests/roster/test_cognitive_load_repository_contract.py` for the router's shape.
- **Dogfood run (AC-0026, AC-0027):** visual / manual QA. The entry is driven live end to end against the real built CLI, then driven once against a mutated install, and both runs are recorded in the verification ledger; the roster test validates the recorded receipt against the schema.
- **Delivery-time checks (AC-0023, AC-0038, and the merge-base or post-rebase halves of the dogfood-run, regression, and projection criteria):** goal-based, run once against the merge base right before the PR and recorded in the verification ledger. They compare against a moving base, so they are not standing tests.
- **Guide (AC-0028):** goal-based, in `tests/roster/test_core_onboarding_documentation.py`, because a pack test may not read `guides/`.
- **Regression (AC-0029):** goal-based. The named suites pass; their unedited-files diff is a delivery-time check.
- **Release and projection (AC-0030, AC-0031):** goal-based, by a version-equality assertion and by the catalogue commands' exit status, with self-host rerun on the rebased tree as a delivery-time check.

## Acceptance Criteria

Unless a criterion names another region, "the section" is the text of `packs/core/.apm/skills/work-loop/references/verification-modes.md` from the heading `## Verify entries` to the next `## ` heading. `<merge-base>` is the merge base of `HEAD` with freshly fetched `origin/main`.

### Scope and location

- [ ] **AC-0001.** The section states that at PLAN a task whose verification mode is visual / manual QA, behavior pin, or measurement looks for a verify entry for each surface the task changes or must drive to prove its outcome, and that a missing entry makes creating it the task's first step.
- [ ] **AC-0002.** The section states that a surface the change neither touches nor must drive is recorded as uncovered and is not mapped, drafted, or fixed.
- [ ] **AC-0003.** The section lists, in this order, where an agent looks before creating a file: a verify file an `AGENT_RULES.md` row already routes to; `CONTRIBUTING.md` in `.github/`, the root, or `docs/`, and the guides it links to; developer guides, naming `DEVELOPMENT.md`, `docs/DEVELOPMENT.md`, `docs/development/`, `contribute/`, `BUILD.md`, `BUILDING.md`, `TESTING.md`, `HACKING.md`, and `VERIFICATION.md`; README sections on running or building locally; agent instruction files and host skills, naming `AGENTS.md`, `.github/copilot-instructions.md`, `GEMINI.md`, and `.claude/skills/verify/`.
- [ ] **AC-0004.** The section states that when an existing human-facing file covers the surface the agent offers to add the entry there; that agent instruction files and host skills are read for commands to map into an entry but never hold one; that `docs/VERIFICATION.md` is created only when no human-facing file covers the surface or the adopter declines; and that an unanswered or ambiguous offer writes nothing. A human-facing file is any place AC-0003 lists other than agent instruction files and host skills.
- [ ] **AC-0032.** The section states that while an offer is unanswered the surface's grade is `blocked`, the run names the pending offer and records no receipt, because no command ran, and the task does not claim its mode.
- [ ] **AC-0005.** The section states that after writing an entry in a file no `AGENT_RULES.md` row routes to, the agent adds one row under the same adopter acceptance as the entry, whose `read` cell is that file's repository-relative path and whose `when` is limited to verifying the surfaces that file covers.
- [ ] **AC-0006.** The section states that `RUNBOOK.md` and `docs/runbooks/` are not extended with launch steps.

### Building and proving an entry

- [ ] **AC-0007.** The section states that an entry for a surface with existing tooling points at that tooling and records only what it lacks: the exact invocation, the ready signal, which output is the evidence, and cleanup; and that new commands are drafted from the repository's manifests, scripts, CI, and docs only where no tooling covers the surface.
- [ ] **AC-0008.** The section states that an entry is a draft until it has run once from start to finish; that it also needs one recorded failing run whose `mutation-proof.md` record names the entry's evidence check as its catching test and one deliberate break of the driven subject as its exact mutation, the break standing in for that reference's revert to the pre-fix implementation; and that the task does not claim its mode before both exist.
- [ ] **AC-0009.** The section states that drive commands are recorded in the verification ledger, and that when a second run drives the same surface by hand its commands move into the verify file, a test, or the repository's own tooling.
- [ ] **AC-0010.** The section states that an in-scope entry failing at run start is classified as doc drift, a harness gap, or a product bug; that a harness gap in mapped tooling is fixed in that tooling; and that a product bug is reported and never written into the entry as expected behavior.

### Entry contents

- [ ] **AC-0011.** The section names these twelve fields, each with what it holds: Surface, Launch, Ready, Doctor, Isolation, Drive, Features, Evidence, Proof limits, Cleanup, Helpers, Stand-in gap; and states that Doctor is one read-only check.
- [ ] **AC-0012.** The section states each of these rules: ready means usable, not that the process answers; never drive an instance this run did not start; drive by stable handles such as roles, labels, and prompt strings, never coordinates; evidence survives cleanup and the run checks that it did; test-only endpoints and internal setters are not proof; a dry-run is checked by observing what it skips.
- [ ] **AC-0033.** The section states that cleanup stops or removes only processes, containers, and directories this run started or created, identified by the handle the run recorded and never by process name or pattern.
- [ ] **AC-0013.** `packs/core/.apm/skills/work-loop/assets/verify-entry.md` holds one heading per field AC-0011 names, in that order, and every value in it is an angle-bracket placeholder.

### Grades and receipts

- [ ] **AC-0014.** The section names exactly five grades — `live-verified`, `test-verified`, `build-only`, `blocked`, `failed` — states that each run other than the failing proof run reports one, and states that a grade its recorded commands and output do not support is reported as `blocked`.
- [ ] **AC-0015.** The section holds a table mapping each of the five grades to an `observation.type` from `command-result` and `test-result` and to an `outcome` equal to the grade, and states the receipt's `schema_version` `1`, its `receipt_id` form `verify:<surface>:<run-id>`, its `freshness_mode` `exact-subject`, and its producer class `verify-entry` with the identity `verify:<surface>`.
- [ ] **AC-0016.** The section states that which criterion a run proves comes from the task and the criterion's approved evidence policy, never from the verify entry.

### Safety

- [ ] **AC-0017.** The section states that recorded commands, and any output copied into the verification ledger or another committed record, use placeholders for paths, hostnames, and usernames, never include a credential value, and name a credential only by its environment variable.
- [ ] **AC-0018.** The section states that a verify entry is agent guidance whose edits change a tool surface, that its commands run only under the host's permission mode, and that an entry never widens network, credential, or write scope beyond what the task's verification needs.

### Routing, seeding, evals

- [ ] **AC-0019.** In `work-loop` SKILL.md, PLAN step 7's paragraph beginning `**Confirm the mechanism exists before claiming the mode` links `references/verification-modes.md#verify-entries`.
- [ ] **AC-0034.** In `work-loop` SKILL.md, the finish checklist's "Verification passed" item asks whether the run drove a surface or feature its verify entry does not cover.
- [ ] **AC-0020.** `adapt-to-project` SKILL.md states that it may seed verify entries in the format `work-loop` uses, and that `work-loop` does not depend on it having run.
- [ ] **AC-0021.** `work-loop`'s `evals/evals.json` holds one case each for a missing entry becoming task zero, an existing contribution guide offered for extension, and a product bug found at run start, and each carries `id`, `prompt`, `expected_output`, and a non-empty `assertions` list.
- [ ] **AC-0035.** `adapt-to-project`'s `evals/eval_queries.json` holds one `should_trigger: true` query about seeding verify entries.

### Contract fit

- [ ] **AC-0022.** For each row of AC-0015's table, a receipt whose `observation.type` and `outcome` come from that row, whose `schema_version`, `receipt_id`, `freshness_mode`, and `producer` come from the section's stated forms with `<surface>` and `<run-id>` filled, and whose lineage, selector, and fingerprint are placeholders, validates against `contracts/delivery/evidence-receipt.v1.schema.json`.
- [ ] **AC-0023.** At delivery, `git diff --exit-code <merge-base> HEAD -- contracts/delivery/evidence-receipt.v1.schema.json` exits 0, and the ledger records the command and its exit status.

### This repository's entry

- [ ] **AC-0024.** `docs/VERIFICATION.md` holds one `agentbundle` CLI entry with a heading for every field AC-0011 names.
- [ ] **AC-0036.** That entry's Drive renders the core pack with `agentbundle render`, installs it into a scratch Git repository with `agentbundle install` and `--adapter codex`, and verifies it with `agentbundle diff`.
- [ ] **AC-0037.** Neither `docs/VERIFICATION.md` nor `docs/specs/verify-entries/notes/verification-ledger.md` contains a `/Users/`, `/home/`, `/private/var/`, `/var/folders/`, or `C:\Users` path, or an email address.
- [ ] **AC-0025.** Root `AGENT_RULES.md` is the seed `AGENT_RULES.md` followed by table rows only, one of which has the `read` cell `` `docs/VERIFICATION.md` ``.
- [ ] **AC-0026.** The verification ledger records one run of the entry graded `live-verified`, with each command, its exit status, and its output, and one receipt for it whose `acceptance_fingerprint` is `git:<commit>` of the commit driven and which validates against the schema; at delivery, `git diff --quiet <commit> HEAD -- . ':(exclude)docs/specs/verify-entries'` exits 0 and the ledger records it.
- [ ] **AC-0027.** The ledger records one failing run as a mutation proof naming: the invariant (the install matches a fresh render); the catching check (`agentbundle diff`); the exact mutation (one line appended to one installed file in the scratch repository); and the expected and observed failure (`agentbundle diff` exiting 1 and naming that file).

### Guide, regression, release

- [ ] **AC-0028.** `guides/core/explanation/core-pack.md` states that `work-loop` looks for an existing file covering a surface before proposing `docs/VERIFICATION.md`, and that the adopter owns the file.
- [ ] **AC-0029.** `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py`, `tests/roster/test_tdd_stub_lifecycle_contract.py`, and `packs/core/tests/skills/adapt-to-project/test_adapt_skill_body.py` pass, and at delivery `git diff --exit-code <merge-base> HEAD --` over those three files exits 0, and the ledger records it.
- [ ] **AC-0030.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version.
- [ ] **AC-0038.** At delivery, `python3 tools/check-core-release.py --base <merge-base>` exits 0, and the tool owns the release facts it checks; the ledger records the command and its exit status.
- [ ] **AC-0031.** `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` exit 0, and `agentbundle catalogue self-host --root . --write` leaves no tracked change after the delivery commit.

## Terminal Intent

`code` — ship the verify-entry doctrine, its routing, template, seeding note, eval cases, and guide; this repository's `agentbundle` CLI entry proven live and failing; and the core release with its projections.

## Follow-ons

- eugenelim: none filed — admitting `verify-entry` receipts into the supervisor's evidence store needs a producer grant and an append path; it is separate work if the owner asks for it.

## Assumptions

- Product: the default name `docs/VERIFICATION.md` is a chosen default, not an observed convention — what it would change: AC-0004 and AC-0024 (settled by: the owner, at spec approval).
- Product: eval cases are added but not run against a model in this delivery — the routing behavior they assert is checked only by shape.
