# Plan: work-loop script paths

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially, record why in the changelog.

## Approach

Apply one concise path convention at the canonical work-loop source, including
the pinned finish-checklist instruction. Verify the linter's real CLI before
writing its command, compare the pinned prose change with the workspace-status
engine's responsibilities, and update only the finish-window digest when no
engine behavior changes. Retain the existing eval, core release bump, changelog,
and RFC-candidate record, then regenerate every projection through the normal
build chain. Prove the result by running a generated command verbatim from the
repository root before running the repository gates and full-mode reviews.

## Observed starting state

The direct-light pass changed the canonical work-loop path convention, its 43
un-pinned invocations, eval, core release metadata, changelog, generated
projections, and RFC-candidate register before review escalated this work to full
mode. The surviving review Blocker is the pinned finish-checklist sentence,
which still teaches `scripts/lint-spec-status.py`; its hash has not been
updated. This plan describes that observed state and the remaining reconciliation
rather than backfilling a fictional implementation order.

## Constraints

- Canonical edits originate in `packs/core/.apm/skills/work-loop/`; projections
  come from the build chain.
- The active `okf-authoring-projection` spec prevents the cross-pack migration
  from joining this delivery slice.
- Git metadata is read-only in this managed environment; no staging, commits,
  fetches, rebases, or branch updates run.
- The base-freshness command is skipped because it force-updates a remote-tracking
  ref, which the active permission profile forbids.
- Python gates run with `PYTHONDONTWRITEBYTECODE=1`.

## Construction tests

**Integration tests:** run
`python '.agents/skills/work-loop/scripts/loop-engine.py' --help` verbatim from
the repository root after regeneration and require exit 0.

**Manual verification:** compare canonical, Codex, and Claude `SKILL.md` and
eval files byte-for-byte; inspect the finish-window reconciliation against
`workspace_status_engine.py`.

## Design (LLD)

### Design decisions

- One global `<skill-dir>` rule governs every Python example, while each
  command remains copyable after placeholder substitution and cannot widen the
  active runtime's permission profile. Traces to AC1–AC3 and AC5.
- The finish hash changes only after determining that the edited sentence is an
  invocation instruction, not workspace-status behavior. Traces to AC4.
- The other packs remain a registered RFC candidate because one atomic
  catalogue-wide convention crosses active pack ownership. Traces to AC9.

Declined patterns:

- Derive the skill directory in shell snippets: duplicates platform-specific
  mechanics and makes every example longer.
- Use a repository-relative `packs/core/...` path: works only in this source
  checkout, not installed projections.
- Hand-edit projections: violates the repository's source-of-truth contract.
- Re-pin the finish hash without inspecting its engine relationship: defeats the
  drift guard's purpose.

### Dependencies & integration

The pack build consumes canonical work-loop content and emits the Codex and
Claude projections. The workspace-status anchor hashes the canonical
finish-checklist window; its engine consumes spec status semantics but does not
execute the lint command.

## Tasks

### T1: the pinned finish instruction is executable and reconciled

**Depends on:** none · **Verification mode:** goal-based check

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`,
`tools/test_workspace_status.py`

**Tests:**

- The canonical finish checklist contains the exact command specified by AC3.
  Verifies AC3.
- The work-loop contract-anchor test passes with the reconciled finish hash.
  Verifies AC4.
- A source search finds no `python scripts/` in the canonical skill. Verifies
  AC1–AC3.

**Approach:**

- Replace the remaining ambiguous finish-checklist sentence with the explicit
  repository-root command.
- Compare every semantic assertion attached to the pinned window with
  `workspace_status_engine.py`; record why the path-only change requires no
  engine edit.
- Recompute and update only `_WORK_LOOP_FINISH_HASH`.

**Done when:** the explicit command is present and the anchor test passes without
a workspace-status engine change.

### T2: regenerated artifacts publish and exercise the convention

**Depends on:** T1 · **Verification mode:** goal-based check

**Touches:** `packs/core/.apm/skills/work-loop/evals/evals.json`,
`packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`,
`docs/specs/README.md`, `docs/product/changelog.md`,
`docs/product/findings/rfc-candidates.md`,
`.agents/skills/work-loop/**`, `.claude/skills/work-loop/**`,
`web/src/lib/now-highlights.generated.json`

**Tests:**

- Eval JSON parses and includes the repository-root invocation case. Verifies
  AC6.
- Canonical and generated work-loop skill/eval files compare byte-identically.
  Verifies AC7.
- The Active specs table contains `work-loop-script-paths/`. Verifies AC7.
- The generated `loop-engine.py --help` command exits 0 from repository root.
  Verifies AC8.
- The measured remaining roster is 15 skills across seven packs and matches the
  RFC-candidate record. Verifies AC9.

**Approach:**

- Preserve the already-applied eval, patch release, changelog, and candidate
  record where they match the spec.
- Add the reviewed spec to `docs/specs/README.md` before implementation approval.
- Run the dist build, forced self-host regeneration, and final dist build in the
  required order.
- Execute the documented generated command without changing cwd.

**Done when:** projection parity holds and the verbatim root command exits 0.

### T3: repository gates and full-mode reviews close the change

**Depends on:** T2 · **Verification mode:** goal-based check

**Tests:**

- `git diff --check`, focused anchor/eval checks, lint, typecheck, and available
  repository tests pass.
- `PYTHONDONTWRITEBYTECODE=1 make ci` runs to the managed-environment boundary
  with any unrelated infrastructure failures recorded precisely.
- Adversarial, security, and quality reviews return clean after applied findings.

**Approach:**

- Run focused checks before the full gate chain.
- Preserve unrelated worktree changes and do not alter gates to make them pass.
- Resolve in-scope review findings, repeat affected gates, and iterate the
  adversarial, security, and quality reviewers to clean.

**Done when:** all available gates are green, environment-only failures are
evidenced, and required reviewers are clean.

## Rollout

The patch ships in the next core pack release. Regeneration updates the
repository's installed projections. Rollback is the ordinary source revert plus
the same build chain; there is no migration or irreversible state.

## Risks

- A placeholder can remain conceptually correct but non-copyable if quoting or
  repository-root arguments are omitted.
- Updating the hash without semantic reconciliation can conceal workspace-status
  drift.
- A cross-pack sweep can overwrite an active spec's owned surface.

## Changelog

- 2026-08-21: initial full-mode plan created after direct-light review escalation;
  observed prior edits recorded explicitly.
