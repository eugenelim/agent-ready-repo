# Plan: Work-loop gate selection for repository changes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing
- **Repository anchors:** `packs/core/.apm/skills/work-loop/SKILL.md` PLAN step 7 and its "Confirm the mechanism exists" paragraph; `references/verification-modes.md` (§ Verify entries, § Measurement); `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py`, which pins PLAN step 7 and the Measurement split; `test_verify_entries_contract.py`, which pins the `###` list under `## Verify entries` and its two `##` neighbours; `packs/AGENTS.md` (version bump, portable content, eval harness). Named uncertainty: where the core changelog fragment lives; T2 reads `tools/check-core-release.py` to find it.

## Approach

Add the rule to PLAN step 7 as one sentence beside the existing mechanism paragraph, put the detail in a new section at the end of `verification-modes.md`, pin both with one pack test, add one eval case, then bump core and project. The text is portable, so this spec has no ordering constraint with the precheck spec.

## Constraints

- `SKILL.md` is far over 500 lines; the added text is the fewest lines that carry the rule.
- The supervisor pins `scripts/`, `supervisor-policy.json` and `review-rules.json` (`work-supervisor.py`); this spec edits none of them. A run starts from the installed copy, and no other spec's run is open.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Agent guidance | T1 | pin test green | pack tests green |
| Release history, projections | T2 | release and self-host checks | both exit 0 |

## Design (LLD)

### Design decisions
Traces to: AC-0001, AC-0002, AC-0003. Owned by: T1.
- The rule sits beside the "confirm the mechanism exists" paragraph, which already owns "the mechanism for a task". Rejected: a new PLAN step, which adds lines and a second home.
- The new section goes after `## Measurement`, outside the span `test_verify_entries_contract.py` pins. Where the pin test file lives among the existing `packs/core/tests/skills/work-loop/` files is `implementation-discovered`.

## Tasks

### T1: PLAN rule, section, eval case, and their pin

**Depends on:** none

**Tests:**
- Goal-based, at a pack test that reads the two sources: asserts the AC-0001 rule text, the AC-0002 heading position and the `SKILL.md` link, and the AC-0003 absence of repository-only terms; a structural check of the AC-0004 eval case.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_verify_entries_contract.py packs/core/tests/skills/work-loop/test_evidence_modes_contract.py <the new pin test> -q` passes.

### T2: core version, release check, projections

**Depends on:** T1

**Tests:**
- Goal-based: AC-0005 and AC-0006.

**Approach:**
- Fetch `origin/main` first and bump to the next patch above it in `pack.toml` and `plugin.json`; add the changelog fragment the release check names. Projections come from the run's regenerate step, or from a controller step after terminal.

**Done when:** `python3 tools/check-core-release.py --base origin/main` and `agentbundle catalogue self-host --root . --check` both exit 0.

### T3: repair the review finding on the gate-selection wording

**Depends on:** T2

**Tests:**
- Goal-based, at the existing pin in `packs/core/tests/skills/work-loop/test_gate_selection_contract.py`: the new section names where a repository declares its checks (its agent-guidance files, build files and pipeline definitions) without using the phrase `verification entry`, which the same file reserves as `verify entry`, and says that a check that is not declared is not named as if it were, while the task-zero rule for a missing verification mechanism still applies (AC-0001, AC-0002).
- Goal-based: the changelog highlight limits the rule to a task whose paths a declared check covers, and `python3 tools/check-core-release.py --base origin/main` still exits 0 (AC-0005).

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_gate_selection_contract.py packs/core/tests/skills/work-loop/test_verify_entries_contract.py packs/core/tests/skills/work-loop/test_evidence_modes_contract.py -q` passes and `python3 tools/check-core-release.py --base origin/main` exits 0.

### T4: repair the round-2 review finding on the pin test names and section wording

**Depends on:** T3

**Tests:**
- Goal-based, at `packs/core/tests/skills/work-loop/test_gate_selection_contract.py`: the two tests T3 added carry the identifiers of the criteria they pin (AC-0001, AC-0002) in their names, and no test name claims AC-0005 or AC-0006, which no text pin covers (AC-0001, AC-0002).
- Goal-based: the gate-selection section refers to all three places a repository declares its checks in the plural, skips a kind of file the repository does not have without reporting a gap, and points the missing-mechanism sentence at the SKILL.md rule by its wording (AC-0001, AC-0002).

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_gate_selection_contract.py packs/core/tests/skills/work-loop/test_verify_entries_contract.py packs/core/tests/skills/work-loop/test_evidence_modes_contract.py -q` passes and `python3 tools/check-core-release.py --base origin/main` exits 0.

## Rollout

Reversible by revert. No sequencing with the precheck spec.

## Risks

- A concurrent core bump on `main` invalidates the version; T2 re-fetches before bumping.

## Changelog

- 2026-11-05: spec approved by eugenelim.
- 2026-11-05: plan approved by eugenelim.
