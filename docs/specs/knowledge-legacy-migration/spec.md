# Spec: knowledge-legacy-migration

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none new. Executes the migration `spec/project-knowledge-foundation`
  AC21 already defines.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Risk trigger: destructive/irreversible — it publishes a new
knowledge store and changes which writer is authoritative. AC21 states the
rollback window, and this change stays inside it. -->

## Objective

`project-knowledge --capture` refused every write, so the work-loop's mandated
learning-capture step had no working path. Finish the migration that refusal was
guarding, so loops stop losing their learnings.

## Acceptance Criteria

- [x] **AC1 — the refusal is diagnosed, not worked around.**
  `_assert_v1_writer_allowed` refuses `staged_dual_writer` when no committed v1
  map exists **and** legacy `patterns.jsonl` is present. That is a deliberate
  dual-writer guard: writing to the v1 store while the legacy store is still
  authoritative would split the corpus in two. The fix is to finish the
  migration, never to weaken the guard.

- [x] **AC2 — the corpus is deduplicated first.** K-0064 (mine, PR#953)
  restated K-0058 (PR#939): both record that a green `make build-check` is not a
  green CI. K-0058 is the more useful — it names the roster test and the exact
  failure — so it absorbed K-0064's crisper instruction and its scope, and K-0064
  was dropped. 65 → 64 entries. Done before migrating, while the corpus was still
  one flat list.

- [x] **AC3 — a latent incompatibility is fixed.** K-0051's body carried literal
  newlines. The legacy linter allowed them; the new store's `_expect_text`
  refuses control characters, so that one row blocked the entire migration with
  `strict_parse` at line 51. Wrapped prose, so the newline and its indent
  collapse to one space — no content lost. **Anyone running this migration would
  have hit it immediately.**

- [x] **AC4 — the staged accounting is verified before publishing.** 64 input
  rows → 60 `active_import`, 4 `needs_review_import`, 0 refused.

- [x] **AC5 — the handshake is followed as specified.** AC21 of
  `project-knowledge-foundation`: stage → publish in one normal Git commit →
  activate. The staged tree is copied byte-for-byte so the activation's
  `staged == committed == worktree` comparison holds; activation then clears the
  stage.

- [x] **AC6 — `patterns.jsonl` is retained, not deleted.** AC21 makes the legacy
  file read-only after activation rather than removing it. The writer guard only
  consults it when no committed v1 map exists, which stops being true here.
  Deleting it would also destroy the rollback window AC21 defines.

- [x] **AC7 — capture is verified working, end to end.** Three real observations
  captured, receipts returned `state: pending` into
  `observations/gotcha/2026-08.jsonl` — the two learnings this session had been
  unable to record, plus AC9's.

- [x] **AC8 — the four `needs_review` topics are recorded as follow-up.** Their
  legacy scopes (`*`, `**/*.py`) were too broad to place automatically, so they
  are preserved but outside the active set. Three of the four are
  security-shaped. Recorded as `knowledge-needs-review-topic-scopes`.

- [x] **AC9 — a false claim I committed is corrected.** PR #972's backlog entry
  said the retired `append-knowledge.py` "exits 0", so callers believe they
  wrote. It exits **2** and prints to stderr. I had measured it as
  `script.py | tail -2`, so `$?` was *tail's* code — the exact anti-pattern the
  work-loop skill documents, committed while auditing gates for that same defect
  class. The entry is removed; the lesson is captured.

## Boundaries

### Never do

- Never weaken the dual-writer guard to make capture work. AC1.
- Never delete `patterns.jsonl`. AC6 — it is the rollback window.
- Never hand-edit a staged topic between staging and activation; the handshake
  compares byte-for-byte.

## Testing Strategy

- **Goal-based**: the migration receipt's accounting, the coherence check
  (`rebuild_map_bytes == topics.index.json`), and a real capture returning a
  receipt. A migration is verified by running it and reading what it produced.
