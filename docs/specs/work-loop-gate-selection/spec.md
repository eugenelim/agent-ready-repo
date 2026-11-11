# Spec: Work-loop gate selection for repository changes

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working material.

## Outcome

An agent planning a task in the core `work-loop` skill is told at PLAN time to name, in the task's `Done when:`, the projection or precheck the repository declares for the paths the task edits. A plan that omits it is caught at review, not discovered in CI.

## What Changes

- PLAN step 7 states that a task whose paths a repository-declared precheck or projection check covers names that check in its `Done when:` — `packs/core/.apm/skills/work-loop/SKILL.md`.
- A "gate selection for a repository change" section, after `## Measurement`, says how to find the declared check and what to do when none exists — `references/verification-modes.md`.
- One eval case covers the PLAN rule — `evals/evals.json`.
- Core's version moves to the next patch above fetched `main` — `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, and the changelog fragment the release check requires.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Agent guidance | Applicable: a skill's PLAN step and reference change | the two work-loop files above | core pack maintainers | pack tests green | text pinned by a pack test |
| Release history | Applicable: `.apm/**` changes | core changelog fragment | core pack maintainers | `check-core-release.py --base origin/main` exits 0 | version is the next patch above fetched `main` |
| Projections | Applicable: `.apm/**` is self-hosted | `.agents/`, `.claude/` copies | the run's regenerate step, or a controller step after terminal | `catalogue self-host --check` exits 0 | no drift |

## Agent Rules

### Always do

- Write the new text as portable guidance: it names no path, command or target that exists only in this repository.
- Keep the added `SKILL.md` text to the fewest lines; the detail lives in `verification-modes.md`.

### Ask first

- Any change to a risk trigger, the finish checklist, or `supervisor-policy.json`.
- Turning the PLAN rule into a refusal in a script.

### Never do

- Edit the work-loop `scripts/`, `supervisor-policy.json` or `review-rules.json` (the files a supervised run pins), or edit work-loop files while another spec's supervised run is open.
- Add a script, a dependency, or a top-level directory.
- Add a `###` heading under `## Verify entries` or a `##` heading beside it: a pack test pins that span.

## Testing Strategy

- **Goal-based (AC-0001, AC-0002, AC-0003):** the PLAN rule, the new section and the portable-text constraint, pinned by a pack test that reads the two sources. The obligation is guidance an agent reads, and a pin is the machine that reds when it is removed.
- **Goal-based (AC-0004):** a structural check that the eval case's `assertions` name the omitted check.
- **Goal-based (AC-0005, AC-0006):** `check-core-release.py --base origin/main` and `self-host --check`.

## Acceptance Criteria

- [x] **AC-0001.** `SKILL.md` PLAN step 7 states that a task whose paths a repository-declared precheck or projection check covers names that check in its `Done when:`.
- [x] **AC-0002.** `references/verification-modes.md` has a `## Gate selection for a repository change` section placed after `## Measurement`, and `SKILL.md` links to it.
- [x] **AC-0003.** Neither new text contains `packs/`, `.apm`, `make precheck` or `self-host`.
- [x] **AC-0004.** `evals/evals.json` holds a case whose prompt is a plan task covering a path with a declared precheck and no check in its `Done when:`, and whose `assertions` include one naming that omission.
- [x] **AC-0005.** `python3 tools/check-core-release.py --base origin/main` exits 0.
- [x] **AC-0006.** `agentbundle catalogue self-host --root . --check` exits 0.

## Follow-ons

none

## Assumptions

- Technical: the PLAN rule is guidance plus a content pin, not a script refusal — what it would change is that an agent ignoring the sentence is caught at review, not at plan time (settled by: owner, see Ask first).
- Technical: `SKILL.md`, `references/` and `evals/` edits do not void a supervised run, because the supervisor pins only `scripts/` and the two policy files — what it would change is that this spec would need controller-only edits (settled by: the first `start`).

## Terminal Intent

`code` — the PLAN rule, the gate-selection section, the eval case and the core version bump are in place and projected.

## Accepted Risk

none
