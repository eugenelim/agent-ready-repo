# Verification ledger: default reversible assumptions

Execution observations for this delivery. The supervised run's full history, including its `delivery/` records, is kept on the branch `feat/default-reversible-assumptions-evidence`. The pull-request branch holds one squashed commit without `delivery/`.

## Supervised run

- **Run:** `run-ab6ecaa96b36e9dc`, intent `code`, code trust `trusted`.
- **Approval pair:** 1, approved by the owner on 2026-11-04.
- **Tasks:** all 5 complete (T1 to T5). T5 was a working-plan repair task added after code review; it needed no approval.
- **Terminal readiness:** `work-supervisor.py status --check` exits 0. All 25 criteria are `pass` at the gates, run twice (before and after the T5 repair).
- **Reviewers:** adversarial-reviewer and security-reviewer. quality-engineer was omitted: the change is not high-risk (no operational-safety module, nothing structural, no human request).

## Code review

| Round | Role | Result |
| --- | --- | --- |
| 1 | adversarial-reviewer | 5 findings. adv-1-1 supported (an eval prompt said nobody stated a default). adv-1-2 supported by an owner decision. adv-1-3, adv-1-4 and adv-1-5 refuted by the finding adjudicator: existing handling and consequence. |
| 1 | security-reviewer | Clean. |
| 2 | adversarial-reviewer | Clean, bounded to the T5 repair. |
| 2 | security-reviewer | Clean, bounded to the T5 repair, including the owner's new sentence. |

**Owner decision on adv-1-2 (2026-11-04).** A default the authoring agent proposes counts as stated once it is named in the chat block. Step 3 carries the sentence "A default you propose counts as stated once you name it; an item for which you cannot name one waits."

## Gate evidence

These ran against merge base `2fe8d651268bfc1052112337c30f621a29877b1e` with freshly fetched `origin/main`.

| Criterion | Check | Result |
| --- | --- | --- |
| AC-0001 to AC-0017, AC-0020, AC-0025 | `python3 -m pytest packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py -q` | 21 passed, exit 0 |
| AC-0018 | `python3 -m pytest packs/core/tests/skills/new-spec -q` | 307 passed, 82 subtests passed, exit 0 (286 at baseline) |
| AC-0019 | `git diff --name-status <merge-base> HEAD -- packs/core/tests/skills/new-spec` | only `A test_default_reversible_assumptions.py`; no existing assertion changed |
| AC-0021 | the how-to's `### What to expect` section holds `## Defaulted` and `Defaulted:` and not `each needing your input` | true, exit 0 |
| AC-0022 | `! grep -q "stops\*\* before building on them" guides/core/explanation/core-pack.md` | exit 0 |
| AC-0023 | `pack.toml` and `plugin.json` versions | both `4.0.12`; `4.0.11` at the merge base |
| AC-0024 | `python3 tools/check-core-release.py --base <merge-base>` | `release is consistent`, exit 0 |
| Local gate | `make lint-ruff lint-mypy` | exit 0 |
