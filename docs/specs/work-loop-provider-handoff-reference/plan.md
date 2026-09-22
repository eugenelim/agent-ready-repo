# Plan: work-loop provider-handoff reference

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (§ Version bump rule, § Self-hosting
  projection) and `packs/core/AGENTS.md`; analogous implementations
  `4b5c2f4a5` (reviewer-roster relocation) and `2ba77ff8e` (fidelity-ladder
  relocation), whose corresponding control is
  `packs/core/tests/skills/work-loop/test_reference_routing.py`; named
  uncertainty — `tests/roster/` cannot run locally, so AC12 and AC13 close only on
  a CI dispatch.

## Approach

The block moves whole, and the consumer declaration stays behind. Those are two
different obligations on the same text, and separating them is what makes the
change safe: the entrypoint keeps the four literals the
`agent-skill-engineering-consumer-integrations` criteria read, while the rules
an agent must obey once the predicate fires move to the reference. Order is
forced by the suites — relocate first (T1), then repoint the two pack suites
that window the old heading (T2), then teach the roster suite that a new file
exists (T3), then the records and projections (T4). T3 is the riskiest part,
because its assertions are the ones no local gate runs.

## Constraints

- `packs/AGENTS.md` § Version bump rule: pack content changes bump `pack.toml`
  and `.claude-plugin/plugin.json` together. This branch already carries
  `2.26.32`; the second unit extends that version rather than minting another.
- `packs/AGENTS.md` § Self-hosting projection: `.apm/` is source; adapter
  projections are written by self-host, never edited.
- `packs/AGENTS.md` § Shipped pack content carries no internal-governance
  citations: the new reference states its rules directly and cites no
  repository record.
- The `agent-skill-engineering-consumer-integrations` spec is Shipped and
  frozen. Its ticked criteria are neither edited nor overridden: keeping the
  declaration inline satisfies them as written. The owner's direction that a
  Shipped spec does not constrain this change authorised continuing past the
  apparent conflict, and the design that emerged does not rely on it.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none — every criterion has a mechanical check.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Maintainer procedure / `references/skill-engineering-provider.md` | T1, T2 | The two pack suites pass against the reference; `test_reference_routing.py` covers the selection, request-shape and do-not-locate rules they do not reach | Every moved rule is named by a passing assertion |
| Release history / `docs/product/changelog.md` | T4 | Entry under `[core][2.26.32]` | One core heading for the branch |
| Interface compatibility / frozen spec Status line | T4 | Pointer names the reference | Ticked criteria byte-unchanged |
| Decision rationale / commit body | T4 | Commit states the full-mode discriminator | Commit body present |

## Design (LLD)

### Design decisions

- The entrypoint keeps a fail-closed guard, not just a declaration. Naming the
  contract version, task kinds and diagnostic inline satisfies the frozen
  spec's criteria but buys no containment: those literals do not tell an agent
  to treat provider output as data, hold the envelope, or refuse a hostile
  response. So the inline text also forbids resolving, invoking or reading any
  provider before the reference is loaded, which makes the only path to
  provider text run through the file carrying the containment rules. Rejected
  alternative: rely on the declaration alone — an agent that mis-evaluates the
  predicate then reads provider text ungoverned, which is the exact failure the
  relocation must not introduce. Traces to: AC4, AC7, AC8.
- The roster suite's contract-version, task-kind and diagnostic arms are left
  alone. Keeping the declaration inline means they read the same literals from
  the same file as before, so the frozen criteria hold as written and no
  override is exercised. Only the arms that must know a new file exists change:
  bound-surface completeness, projection equality, and the product-name ban,
  which is extended rather than moved so it covers both files and is strictly
  stronger. Traces to: AC10, AC12, AC13.
- `test_reviewer_project_knowledge_boundary` re-expresses its windowed
  containment assertion as the stronger absolute form: no `knowledge-evidence`
  occurrence in `SKILL.md` at all. A window over a section that no longer
  exists cannot fail. Traces to: AC1, AC11.
- Owned by: T1, T2, T3.

### Interfaces & contracts

- The predicate sentence is the interface between entrypoint and reference: it
  is the only thing deciding whether the containment rules are read. It names
  all five task shapes so the predicate's reach is unchanged from the block's
  own opening sentence. Traces to: AC5, AC6.
- Owned by: T1.

### Failure, edge cases & resilience

- Failure mode the change introduces: an agent mis-evaluates the predicate and
  never loads containment. The guard closes it by ordering rather than by
  detection — no provider is resolved, invoked or read until the reference is
  loaded — so a mis-evaluated predicate yields no provider contact at all
  rather than ungoverned contact. Traces to: AC4.
- Owned by: T1.

## Tasks

### T1: The block is in the reference and the predicate is on the entrypoint

**Depends on:** none
**Touches:** packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/references/skill-engineering-provider.md
**Verification mode:** goal-based check

**Tests:** in `packs/core/tests/skills/work-loop/test_reference_routing.py`,
which already owns pointer-reachability for this skill: `SKILL.md` has zero
`knowledge-evidence` occurrences, asserted as a count compared to 0 rather than
through `grep`'s exit status, which is non-zero on no match and would redden on
the passing case; the inline guard sentence forbidding provider contact before
the reference loads is present and precedes the link; the five task shapes and
the link are present; the routing table has exactly one row naming the
reference; and the reference carries the moved rules the two pack suites do not
already cover — the selection sentence, the no-call-until-selection clause, the
one-call/no-refinement rule, the minimized-request JSON literal, and the
do-not-locate rule. The two pack suites in T2 cover containment ordering, the
envelope literal, refuse-before-citing and the seven-member closed set, so no
assertion is duplicated for those.

**Approach:** drop the block's uniform 4-space indent when writing the
reference; at top level that indent renders the prose as a code block. The
existing suites flatten whitespace, so the dedent is invisible to them.

**Done when:** T1's `Tests:` hold. Covers AC1, AC2, AC3, AC4, AC5, AC6, AC9.

### T2: The two pack suites read the reference

**Depends on:** T1
**Touches:** packs/core/tests/skills/work-loop/test_work_loop_skill_engineering_reference_boundary.py, packs/core/tests/pack/test_reviewer_project_knowledge_boundary.py
**Verification mode:** goal-based check

**Tests:** `python3 -m pytest packs/core/tests/pack packs/core/tests/skills/work-loop -q` passes. The boundary suite's `_section()` reads the whole reference instead of splitting `SKILL.md`; the knowledge-boundary suite asserts `"knowledge-evidence" not in skill` and re-runs its existing containment assertion against the reference.

**Approach:** the second suite's window is replaced, not deleted — deleting it
would drop the containment assertion entirely, and the window is the only thing
that currently carries it.

**Done when:** T2's `Tests:` hold and no assertion was removed without an
equal-or-stronger replacement. Covers AC11.

### T3: The roster suite knows the new reference exists

**Depends on:** T1
**Touches:** tests/roster/test_agent_skill_engineering_consumer_integrations.py
**Verification mode:** goal-based check

**Tests:** `BOUND_SURFACES` names the new reference, so the module-scope
completeness arm stays exhaustive; the projection arm, which today compares
only the work-loop entrypoint, additionally compares the pack reference against
both projected copies — without that, AC13's byte equality has no check and a
stale projected reference ships green; and the product-name ban reads the
reference as well as the body. The contract-version, task-kind and diagnostic
arms are asserted unchanged, and both consumers still pass. Closed by a
`gh workflow run test-roster.yml` dispatch, because `tests/roster/` does not
run locally.

**Approach:** extend the ban rather than repointing it — repointing would move
the guarantee off the entrypoint, where the frozen criteria expect it.

**Done when:** T3's `Tests:` hold on a green roster dispatch. Covers AC7,
AC8, AC10, AC12, AC13.

### T4: The records and projections are consistent

**Depends on:** T1, T2, T3
**Touches:** docs/product/changelog.md, docs/specs/agent-skill-engineering-consumer-integrations/spec.md
**Verification mode:** goal-based check

**Tests:** `python3 -m agentbundle catalogue self-host --root . --write` leaves
`.claude/` and `.agents/` byte-identical to the pack copy for both files;
`python3 -m agentbundle catalogue lint --root . --deep` exits 0 with no ERROR;
`git diff` on the frozen spec touches its Status line only.

**Done when:** T4's `Tests:` hold. Covers AC14 and AC15.

## Changelog

- 2026-09-22 — Drafted.
- 2026-09-22 — Spec approved (scope decision).
- 2026-09-22 — Plan approved (build-strategy decision).
