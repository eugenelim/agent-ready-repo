# Spec: knowledge-zero-row-migration

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0081](../../adr/0081-canonical-project-knowledge-uses-per-topic-json.md) and [ADR-0082](../../adr/0082-project-knowledge-modes-separate-authority.md) (Accepted)
- **Brief:** none
- **Discovery:** none
- **Contract:** none new. The staged artifact is the existing `knowledge-topic-map.v1` map.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> change must match it or update it through the same review workflow.

<!-- Mode: full. Risk trigger: persistent representation — this is the legacy
import path, and the change makes it write a durable staged artifact where it
previously wrote nothing. -->

## Objective

A repository whose knowledge base is legacy-only can activate the v1 knowledge
store even when the migration has nothing to import. `docs/knowledge/README.md`
tells that repository's maintainer that capture stays unavailable "until a
reviewed migration activates that v1 snapshot", and `project-knowledge
--migrate-legacy` is the first command they run. When their
`docs/knowledge/patterns.jsonl` is empty, or when every row in it is refused,
staging produces the canonical empty topic map and the maintainer can carry it
through to an activated store. The migration lifecycle is also legible from the
shipped documentation alone: a maintainer reaching `--activate-staged` knows
that the staged map must first be promoted into `docs/knowledge/` and committed.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — the migration lifecycle is a documented user journey with an undocumented mandatory step | `packs/core/.apm/skills/project-knowledge/SKILL.md` and `packs/core/seeds/docs/knowledge/README.md` | Pack maintainer | AC6's order-aware section check green | Both surfaces carry the four-step sequence and the check runs in the pack's pytest suite |
| Current product truth | Applicable — the same journey text ships into every adopter repository as a seed | `packs/core/seeds/docs/knowledge/README.md` | Pack maintainer | Seed diff reviewed alongside the skill body | Seed and skill body agree on the four-step sequence |
| Release history | Applicable — a `.apm/**` change is a pack release | `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` | Pack maintainer | Both files read 2.25.19 | Versions match and the PR description names 2.25.19 for the adopter to pin |
| Decision rationale | Not applicable — ADR-0081 and ADR-0082 already own the migration lifecycle's authority model, and this change alters no decision | — | — | — | — |
| Interface compatibility | Not applicable — no CLI flag, helper signature, or contract schema changes | — | — | — | — |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit `packs/core/.apm/` as the source of truth, then regenerate the `.claude/`
  and `.agents/` projections with `agentbundle catalogue self-host --root . --write`.
- Bump `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  together to 2.25.19.

### Ask first

- Any edit to `knowledge_store.py` beyond the single `mkdir` statement.
- Any new mode, flag, or helper on the `project_knowledge.py` command surface.
- Any change to the `knowledge-topic-map.v1` map bytes or to the four-way
  snapshot comparison in `activate_staged_migration`.

### Never do

- Place the stage-root creation outside the existing `try`, which would let a
  failed staging run leave a stage directory behind.
- Add a module, a top-level directory, or a dependency.
- Cite this repository's internal governance records, acceptance criteria, or
  repository-only paths in shipped `packs/` prose.
- Weaken, skip, or delete an existing migration test so a new one passes.

## Testing Strategy

- Zero-row staging's return value and staged bytes: **TDD**, unit surface. The
  invariant compresses to one function's returned counts and one file's exact
  content, so a test can state it completely before the code exists.
- All-refused staging: **TDD**, unit surface. Same invariant over a different
  input partition — a non-empty source file that still yields no importable
  topic — which is the second way the empty-loop path is reached.
- Zero-row stage, promote, commit, activate: **TDD**, integration surface. It
  proves out only across the git boundary, because `committed_knowledge_snapshot`
  reads `HEAD` rather than the worktree.
- The zero-row coverage's discriminating power: **goal-based check**. Restore
  the 2.25.18 staging behaviour, run the zero-row case, observe the named
  failure, restore by editing. Coverage that passes against the defect it was
  written for is not coverage.
- The failure-residue, four-way-snapshot, and staged-map-exists controls this
  change must not disturb: **goal-based check**. They already have owning tests;
  the check is that `test_migration.py` runs green unchanged.
- The documented promotion sequence: **TDD**, unit surface, as an order-aware
  check over each surface's migration section. Prose that no check reads is
  prose that rots silently, and a check that only finds scattered tokens passes
  while the sequence is gone.

## Acceptance Criteria

- [x] **AC1 — an empty legacy corpus stages instead of crashing.** With
  `docs/knowledge/patterns.jsonl` present and zero bytes long,
  `stage_legacy_migration` returns `counts` equal to
  `{"input_rows": 0, "active_import": 0, "needs_review_import": 0, "refused": 0}`
  and `diagnostics` equal to `[]`.
- [x] **AC2 — the zero-row staged result is the canonical empty map, not an
  empty directory.** After AC1's run, exactly one file exists anywhere under
  `docs/knowledge/.migration-stage/`: the map at
  `docs/knowledge/.migration-stage/docs/knowledge/topics.index.json`, whose
  content is these 66 bytes exactly, including the trailing newline —
  `{\n  "entries": [],\n  "schema_version": "knowledge-topic-map.v1"\n}\n`.
- [x] **AC3 — a corpus whose every row is refused stages the same shape.** With
  a `patterns.jsonl` of *n* rows, *n* at least 1, that each receive the
  `refused` disposition, staging returns `counts` equal to
  `{"input_rows": n, "active_import": 0, "needs_review_import": 0, "refused": n}`
  and leaves the same single staged map, byte for byte, that AC2 names.
- [x] **AC4 — the zero-row migration activates end to end.** After AC1's run,
  with the staged map copied into `docs/knowledge/` and committed,
  `activate_staged_migration` returns `state` equal to `"activated"` and the
  directory `docs/knowledge/.migration-stage/` no longer exists.
- [x] **AC5 — the zero-row coverage discriminates.** Run against the staging
  behaviour this repository shipped in 2.25.18, where the stage root exists only
  as a side effect of writing a topic, the test covering AC1 fails with an
  unhandled `FileNotFoundError` naming `topics.index.json`.
- [x] **AC6 — both shipped surfaces state the promotion sequence.** The
  `project-knowledge` skill body and the `docs/knowledge/README.md` seed each
  carry a migration section giving, in this order: run `--migrate-legacy`, copy
  the staged `docs/knowledge/` tree into `docs/knowledge/`, commit it, then run
  `--activate-staged`.

## Follow-ons

- Pack maintainer: the adopter repository's temporary in-repo divergence
  (the one-line fix applied to both projections with re-pinned
  `.agentbundle-state.toml` SHAs) is dropped and the projections restored to
  upstream once 2.25.19 is released. Tracked outside this repository.

## Assumptions

- Technical: the defect is live at HEAD in both reachable cases and raises a raw
  `FileNotFoundError` at `knowledge_store.py:2920` rather than a typed
  `knowledge-diagnostic.v1` refusal (source: probe, both cases raised with
  `staged_migration_files() == []`).
- Technical: creating the stage root inside the existing `try` is a complete
  fix — staging returns the specified counts, writes the 66-byte canonical map
  as its only file, and the full lifecycle activates and clears the stage
  (source: probe against a patched scratch copy; user confirmation 2026-09-13).
- Technical: `packs/core/.apm/` is the source of truth and `.claude/` and
  `.agents/` are self-host projections (source:
  `packs/AGENTS.md` § Self-hosting projection).
- Technical: the migration harness is
  `packs/core/tests/skills/project-knowledge/test_migration.py`, which loads the
  module under a unique name through `knowledge_test_support`, and whose
  `_commit_staged_activation` helper cannot serve a zero-row case because it
  copies a `topics` directory that zero-row never creates (source:
  `test_migration.py:45`).
- Process: a `.apm/**` content change bumps `pack.toml` and
  `.claude-plugin/plugin.json` by a patch level; both read 2.25.18, so this
  ships as 2.25.19 (source: `packs/AGENTS.md` § Version bump rule).
- Process: packs keep no `CHANGELOG.md` — only published packages do — so no
  changelog surface is in scope (source: `docs/CONVENTIONS.md:720`).
- Process: no content pin blocks this change. The `project-knowledge` skill body
  is 47 lines against the `CAT-S003` 500-line advisory, and the shared-test
  deduplication guard pins no project-knowledge node ID (source: line count and
  a search of `tools/test_local_ci_shared_test_deduplication.py`).
- Product: the stage-to-activate gap closes by documenting the manual promotion
  step rather than by adding a `--promote-staged` mode, so the git commit stays
  the human review boundary the lifecycle is built around (source: user
  confirmation 2026-09-13).
