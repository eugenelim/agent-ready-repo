# Spec: reviewer output contract

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** contracts/delivery/review-report.v1.schema.json, contracts/delivery/finding.v1.schema.json (both consumed unchanged)
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

A `work-loop` controller gets findings from `adversarial-reviewer` and `experience-reviewer` that the review classifier parses as written, each anchored to a `path:line` (or, for a non-file design location, a `Where:` location), and, on request, a typed report with the `finding.v1` fields; `experience-reviewer`'s clean `SHIP IT` verdict stays a flagless-classifier signal only. When a report's findings carry no anchor, the classifier refuses it under the reason `finding-unanchored`, not a reason about the clean sentence, so the controller knows which rule to send back.

## What Changes

- The anchor rule and the typed-report evidence anchor — `packs/core/.apm/agents/adversarial-reviewer.md`.
- The anchor rule and a Typed report section — `packs/experience-design/.apm/agents/experience-reviewer.md`.
- The `finding-unanchored` refusal reason in `raw-classify` and in flagless `inspect` (without `--adjudication`) — `packs/core/.apm/skills/work-loop/scripts/review-artifact.py`.
- One eval case — `packs/core/.apm/skills/work-loop/evals/evals.json`.
- Content and behavior tests — `packs/core/tests/pack/test_finding_adjudication_contract.py`, and the cross-pack `tests/roster/test_reviewer_output_contract.py`.
- The core and experience-design versions, one changelog fragment per pack, and the self-hosted projections.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Agent guidance | How each reviewer anchors and shapes a finding | the two agent definitions above | core and experience-design pack maintainers | content tests green | suites green at the delivery commit; projections regenerated |
| Interface compatibility | Typed reports stay in the existing contracts | `contracts/delivery/review-report.v1.schema.json`, `contracts/delivery/finding.v1.schema.json`, consumed unchanged | `structured-review-boundary` contract owner | field names pinned in tests | schema bytes unchanged against the merge base |
| Maintainer procedure | The classifier names the failed rule | `review-artifact.py` stderr refusal vocabulary | core pack maintainers | behavior tests green | suites green at the delivery commit |
| Release history | A non-cosmetic change to two packs ships under new versions | each pack's `pack.toml` and `.claude-plugin/plugin.json`; one fragment per pack in `docs/product/changelog.d/` | pack maintainers | version-equality assertions | `tools/check-core-release.py` result recorded in the ledger |

## Agent Rules

### Always do

- Keep every sentence an existing test pins in the files this change edits; add text beside it.
- Keep the classification each existing report gets; only the named refusal reason changes.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together, and regenerate projections with self-host rather than editing them.
- Rebase onto freshly fetched `origin/main` before each push, re-derive both versions, then rebuild projections.

### Ask first

- Any edit to a `contracts/delivery/` schema.
- Any change to the finding-line grammar the classifier accepts, to `review-rules.json`, or to the reviewer roster.
- Changing `experience-reviewer`'s clean verdict away from `SHIP IT`.

### Never do

- No new agent, reviewer, review round, dependency, module, or top-level directory.
- No experience-design eval-harness change: the owner waived it, because no experience-design harness covers `experience-reviewer`.
- No new key in the `raw-classify` JSON payload; the reason stays on stderr and in the flagless `reason` field.
- No edit to an adapter projection except through self-host, and no citation of this repository's internal records in shipped pack content.
- No edit under `packs/core/.apm/skills/work-loop/scripts/` while a `WORK_SUPERVISOR_INTEGRATION=1` test run is live in this worktree.

## Testing Strategy

- **Refusal reason (AC-0001, AC-0002, AC-0003, AC-0004):** TDD, in `packs/core/tests/pack/test_finding_adjudication_contract.py`, running `review-artifact.py` as a subprocess over fixture reports, the way the suite's existing refusal-code tests do, because the reason is observed on the CLI's stderr and JSON. AC-0004's fingerprint is computed in the test from the stated preimage.
- **adversarial-reviewer guidance (AC-0005, AC-0006):** goal-based. AC-0005 is a content test in `test_finding_adjudication_contract.py` reading the two named sections. AC-0006 is a round trip in `tests/roster/test_reviewer_output_contract.py`, which loads core's classifier.
- **experience-reviewer guidance (AC-0007, AC-0008, AC-0009, AC-0010, AC-0011):** goal-based content tests and round trips in `tests/roster/test_reviewer_output_contract.py`, because they read core's classifier and `contracts/delivery/`, which a pack test may not. AC-0009 reads both sets from the schemas. AC-0010 and AC-0011 assert the stated sentences, not model behavior.
- **Eval (AC-0012):** goal-based shape check in `test_finding_adjudication_contract.py`; the case is not run against a model in this delivery.
- **Delivery-time checks (AC-0013, AC-0014, AC-0015, AC-0016, AC-0017):** goal-based, run once against the merge base right before the PR and recorded in `notes/verification-ledger.md`, because they compare against a moving base.

## Acceptance Criteria

A finding-marker line, below, is a line whose leading-whitespace-stripped form starts with `**<digits>.`; an unanchored line is a finding-marker line from which no finding parses. Flagless `inspect`, below, is `review-artifact.py inspect --run-id <id> --root <dir> --report <path> --json` without `--adjudication`, over a run with no prior records.

- [x] **AC-0001.** For a report from which no finding parses, which holds no `Clean — ready to commit.` line, no `## Not checked` line, and at least one unanchored line, `review-artifact.py raw-classify --json` exits 0, prints `{"classification": "invalid", "finding_count": 0, "not_checked_present": false}`, and writes `review-artifact: raw report refused (finding-unanchored)` to stderr.
- [x] **AC-0002.** For a report with no adjudication heading, no `Clean — ready to commit.` substring, no `SHIP IT` line, no parsed finding, and at least one unanchored line, flagless `inspect` exits 0 with `"classification": "invalid"` and `"reason": "finding-unanchored"`, and stderr carries `finding-unanchored`.
- [x] **AC-0003.** These reports keep their current result: prose with no unanchored line (`raw-classify` reason `sentinel-absent`; flagless `inspect` reason `no-actionable-result`); an unanchored line followed by the sentinel line (`raw-classify` reason `content-before-sentinel`); an unanchored line plus a `SHIP IT` line (flagless `inspect` classification `clean`); and a three-section adjudication envelope whose main-loop line is unanchored (flagless `inspect` reason `sustained-line-shape`).
- [x] **AC-0004.** A report holding one anchored finding `` **1. Missing guard.** `src/loader.py:42`. The loader skips validation. Fix: validate the input. `` and one unanchored line gives `raw-classify` classification `findings` with `finding_count` 1, and flagless `inspect` classification `findings` with exactly the fingerprint `sha256("src/loader.py|42|**1. Missing guard.**")`.
- [x] **AC-0005.** `adversarial-reviewer.md`'s `## Report numbered findings` section states that the first element after a finding's bold title is a backticked repository-relative `path:line` or `path:start-end`, that a finding about something absent cites the line where it belongs, and that a report whose numbered findings carry no anchor is refused as `finding-unanchored`; its `## Typed report` section states that `evidence_refs` starts with that anchor.
- [x] **AC-0006.** `adversarial-reviewer.md` carries at least one finding-marker line holding no `<`, and each such line parses as exactly one finding and matches the strict sustained-line shape.
- [x] **AC-0007.** `experience-reviewer.md`'s output section states that a finding in a file takes a backticked `path:line` right after its bold title, that any other finding takes `Where: <screen/stage/brief>` with no period inside the location, and that a report whose numbered findings carry no anchor is refused as `finding-unanchored`.
- [x] **AC-0008.** `experience-reviewer.md` carries a finding-marker line holding no `<` in each form (backticked `path:line` and `Where:`), and each such line parses as exactly one finding and matches the strict sustained-line shape.
- [x] **AC-0009.** `experience-reviewer.md` has a `## Typed report` section that names every member of `required` in `contracts/delivery/finding.v1.schema.json` and every member of the `terminal_status` `enum` in `contracts/delivery/review-report.v1.schema.json`.
- [x] **AC-0010.** That section states that a typed report carries only material findings, defines material as a Blocker or Major whose defect something outside the finding establishes, and states that the result is `indeterminate` with no findings when the request names no spec or a material finding has no criterion identifier in it.
- [x] **AC-0011.** That section states that, without a typed-report request, the output block above, unchanged, is the whole output.
- [x] **AC-0012.** `packs/core/.apm/skills/work-loop/evals/evals.json` holds a case whose expected output contains both `finding-unanchored` and `` `path:line` ``.
- [x] **AC-0013.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry one equal version, one patch above `packs/core/pack.toml` at the merge base with freshly fetched `origin/main`; `packs/experience-design/pack.toml` and its `plugin.json` carry one equal version, one patch above `packs/experience-design/pack.toml` at that merge base.
- [x] **AC-0014.** `docs/product/changelog.d/` holds one new fragment per pack, each naming its pack at the version AC-0013 sets and carrying a `## Highlights` section with at least one bullet.
- [x] **AC-0015.** `python3 tools/check-core-release.py --base <merge-base>` exits 0.
- [x] **AC-0016.** `contracts/delivery/review-report.v1.schema.json` and `contracts/delivery/finding.v1.schema.json` are byte-identical to the merge base.
- [x] **AC-0017.** `agentbundle catalogue self-host --root . --write` leaves no diff after the delivery commit.

## Terminal Intent

`code` — ship the `finding-unanchored` refusal reason, the anchor rule and findings shape in both reviewer definitions with the experience Typed report section, the eval case, the tests, and the core and experience-design releases with their projections.

## Follow-ons

none

## Assumptions

- Technical: in a report where some findings parse, an unanchored finding gets no fingerprint and no refusal — the adjudicator still reads the whole body, but recurrence tracking misses it (named gap; this delivery keeps that classification by design).
