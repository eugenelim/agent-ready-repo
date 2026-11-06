# Spec: Risk-trigger record on the spec header

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** mixed
- **Risk triggers:** structural-interface

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working material.

## Outcome

A maintainer measuring the work-loop's mode decisions reads which risk triggers
fired for each persisted spec from one header line with a closed vocabulary, so
a question such as "how often was Unfamiliar the only trigger" is a `git grep`
count rather than a prose search. The spec-status lint refuses a malformed
value, and a short note names when to re-measure the Unfamiliar-alone share,
RFC-0111's effect on full-mode runs, and the share of code-stage findings that
carry a run.

## What Changes

- A `- **Risk triggers:**` header line, its closed token vocabulary, and the
  token-to-trigger table — `new-spec` `references/spec-and-plan-contract.md`
  § Spec metadata contract, and the `assets/spec.md` template header.
- PLAN step 2 tells the agent to record the mode decision on that line —
  `work-loop` `SKILL.md`.
- Invariant (vii) validates the line — `work-loop` `scripts/lint-spec-status.py`.
- One eval case per skill covers the obligation — `new-spec` and `work-loop`
  `evals/evals.json`.
- One how-to sentence names the line — `guides/core/how-to/plan-and-execute-non-trivial-work.md`.
- A re-measure note — `docs/product/research/mode-decision-re-measure.md`.
- Core's version moves one patch above `packs/core/pack.toml` at the merge base
  with freshly fetched `origin/main`, with its changelog fragment.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Published schema | Applicable: a new spec header field adopters write and a lint parses | `spec-and-plan-contract.md` § Spec metadata contract | core pack maintainers | pack test pins the table against the lint and the risk-trigger block | test green |
| Agent guidance | Applicable: PLAN step 2 and the spec template change | work-loop `SKILL.md`, new-spec `assets/spec.md` | core pack maintainers | pack test pins the sentence and template line | test green |
| User documentation | Applicable: adopters choose the mode | the how-to above | core pack maintainers | one sentence naming the header | sentence present |
| Measurement plan | Applicable: the reason for the record | `docs/product/research/mode-decision-re-measure.md` | owner | the note names each trigger condition with a date or count | note present |
| Release history | Applicable: `.apm/**` changes | core changelog fragment | core pack maintainers | `check-core-release.py --base origin/main` exits 0 | version is one patch above the merge base |
| Projections | Applicable: `.apm/**` is self-hosted | `.agents/`, `.claude/` copies | the run's regenerate step | `catalogue self-host --check` exits 0 | no drift |

## Agent Rules

### Always do

- Keep the vocabulary's single owner the spec metadata contract table; the lint
  holds only the token set, and the test proves the two agree.

### Ask first

- Making an absent `Risk triggers:` line a hard violation.
- Adding the field to `review-verdict.v1`, the supervisor's records, or any
  other record.

### Never do

- List the tokens anywhere in pack content other than the contract table and
  the lint's token set.
- Edit the text between the `risk-triggers:start` and `risk-triggers:end`
  markers in `work-loop` `SKILL.md`.
- Add a script, a dependency, or a top-level directory.
- Backfill the line into any spec other than this one.

## Testing Strategy

- **TDD (AC-0003 to AC-0007):** invariant (vii) is pure parsing with a closed
  grammar; each case is a fixture spec run through the lint's `check`.
- **Goal-based (AC-0001, AC-0002, AC-0008, AC-0009):** content pins in a pack
  test read the contract table, the lint's token set, the template, `SKILL.md`,
  and the eval files.
  The obligations are guidance an agent reads, and a pin is the machine that
  reds when one is removed.
- **Goal-based (AC-0010, AC-0011):** a `grep` over the how-to and the note,
  recorded in the verification ledger. Pack tests do not read repository docs,
  so these two are checked at closeout rather than pinned.
- **Goal-based (AC-0012, AC-0013):** `check-core-release.py --base origin/main`
  and `agentbundle catalogue self-host --root . --check`.

## Acceptance Criteria

- [x] **AC-0001.** The spec metadata contract has a `Risk triggers` bullet with
  a token-to-trigger table whose trigger column, read top to bottom, is the same
  ordered sequence as the bold labels of the bullets between the
  `risk-triggers:start` and `risk-triggers:end` markers of `work-loop`
  `SKILL.md`, with no extra entry on either side.
- [x] **AC-0002.** The lint's token set equals the table's token set, plus `none`.
- [x] **AC-0003.** Invariant (vii) reports a hard violation for a spec in scope
  whose `Risk triggers:` line's value contains an unknown token, a repeated
  token, an empty item (leading, trailing, or between commas), or `none` beside
  another token. Tokens match exactly and case-sensitively after the spaces
  AC-0006 allows are trimmed, so a backticked or differently cased token is
  unknown.
- [x] **AC-0004.** Invariant (vii) reports a hard violation for a spec in scope
  with more than one `Risk triggers:` line in its preamble.
- [x] **AC-0005.** Invariant (vii) reports a warn-only finding, and no hard
  violation, for a `Draft` spec added since the base ref that has no
  `Risk triggers:` line.
- [x] **AC-0006.** Invariant (vii) reports nothing for a spec whose value is
  `none` or one or more distinct tokens separated by commas, with any spaces
  around each comma and at the start or end of the value. It also reports
  nothing for a spec without a line when that spec is present at the base ref,
  is not `Draft`, or no base ref resolves.
- [x] **AC-0007.** A `Risk triggers:` line is a line that starts
  `- **Risk triggers:**`, sits in the preamble outside any HTML comment or code
  fence, and has a value that is not empty once HTML comments are hidden. Any
  other line naming the field — bare, commented out, in the body, or empty — is
  no line, so invariant (vii) gives it no hard violation in any of AC-0003 to
  AC-0006.
- [x] **AC-0008.** `work-loop` `SKILL.md` PLAN step 2 states that the
  `Risk triggers:` line holds the tokens that fired, or `none`; that it is
  written or rewritten only while the spec is `Draft`, so it records the mode
  decision the spec was approved under; and that a spec past `Draft` is not
  edited to add or change it.
- [x] **AC-0009.** `assets/spec.md` carries exactly one `- **Risk triggers:**`
  header line, and each of `new-spec` and `work-loop` `evals/evals.json` holds a
  case whose assertions name the line.
- [x] **AC-0010.** `guides/core/how-to/plan-and-execute-non-trivial-work.md`
  names the `Risk triggers:` header as where a spec records the triggers that
  fired.
- [x] **AC-0011.** `docs/product/research/mode-decision-re-measure.md` names, for each of the Unfamiliar-alone
  share, RFC-0111's effect on full-mode runs, and the share of code-stage
  findings that carry a run, its baseline, a trigger condition stated as a count
  or a UTC date, and the rule or command that measures it.
- [x] **AC-0012.** `python3 tools/check-core-release.py --base origin/main`
  exits 0.
- [x] **AC-0013.** `agentbundle catalogue self-host --root . --check` exits 0.

## Follow-ons

none

## Assumptions

- Defaulted: Technical: a new `Draft` spec with no line (AC-0005) warns rather than fails — default: warn-only, so in-flight branches that add a spec from the older template still pass; if wrong: (vii) gains one hard branch and AC-0005 flips (settled by: owner).
- Product: direct-light work creates no spec — its decisions are not recorded, so the record counts full-mode and persisted light-mode decisions only, each as approved; a spec approved without the line is outside the count.

## Terminal Intent

`code` — the header field, its lint invariant, the PLAN sentence, the template
line, the eval cases, the how-to sentence, the re-measure note and the core
version bump are in place and projected.

## Accepted Risk

none
