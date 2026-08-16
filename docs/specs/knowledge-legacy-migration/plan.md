# Plan: knowledge-legacy-migration

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `docs/knowledge/patterns.jsonl` (dedup + one control-character fix; retained).
- `docs/knowledge/topics/` + `topics.index.json` (new, published from the stage).
- `docs/knowledge/observations/` (created by the first real captures).
- `workspace.toml`.

**What demonstrates done**
- `--capture` returns a receipt instead of `staged_dual_writer`.

**What I am NOT changing**
- The dual-writer guard, or any store contract.
- `patterns.jsonl`'s retained content beyond AC2/AC3.
- The retired shim — it already fails correctly (AC9).

## Declined patterns

- **Tempted:** delete `patterns.jsonl` for tidiness once the v1 store was live.
  **Declined:** AC21 keeps it read-only, and it is the rollback window — before
  any v1 observation is persisted, reverting the activation commit restores the
  legacy-only path. Deleting it converts a reversible migration into a one-way door.
- **Tempted:** relax `_expect_text` to tolerate the newline in K-0051, since the
  legacy linter allowed it. **Declined:** the new contract is the stricter one on
  purpose; the row is wrapped prose and normalising it loses nothing.
- **Tempted:** hand-place the four `needs_review` topics into plausible scopes
  while migrating. **Declined:** the migrator declined to guess for good reason —
  `*` and `**/*.py` match the whole repo. Guessing a scope silently narrows where
  a lesson surfaces.

## Verification log

- **AC1** traced to `knowledge_store.py` `_assert_v1_writer_allowed`.
- **AC2** 65 -> 64 entries; legacy lint clean.
- **AC3** `strict_parse` at line 51 before, 0 refusable rows after.
- **AC4** receipt: `{"active_import": 60, "input_rows": 64, "needs_review_import": 4, "refused": 0}`.
- **AC5** published 64 topics + map; `rebuild_map_bytes == topics.index.json`;
  activation returned `state: activated` and cleared the stage.
- **AC7** three captures, each returning a `pending` receipt.
- **AC9** re-measured unpiped: exit 2 from both the source and projected copies.
- **REVIEW** `adversarial-reviewer` = named skip (session instruction prohibits
  subagent dispatch). Self-reviewed against the spec-less checklist.
