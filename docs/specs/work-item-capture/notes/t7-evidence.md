# T7 completion evidence

**Task:** a close accounts for every declined item and fails closed when
validation cannot run.
**Completed:** 2026-09-20. Carries the three criteria amendment 005 moved in
from T5 — the instruction-shape refusal (`AC-0035`), the necessity razor's
refusal (`AC-0044`), and the shape-threshold judgement (`AC-0045`) — all
asserted against the dispatch this task builds.

## What shipped

- `project_knowledge.py` gains the close's per-item reasoning dispatch: the
  declined-set cap (`enforce_declined_set_cap`, `AC-0040`), the pre-dispatch
  instruction-shape gate (`refuse_instruction_shaped_work_item`, `AC-0035`),
  the enumerated, total-by-construction dispatch parameter domain
  (`reasoning_dispatch_parameter_bins`, `build_reasoning_dispatch_payload`,
  `AC-0069`, `AC-0041`), the data-delimited message renderer
  (`render_reasoning_dispatch_message`, `AC-0036`), the fail-closed dispatch
  call (`dispatch_reasoning_check`, all six drives), and the write-path floor
  (`admit_work_item_capture`, `AC-0068`) that refuses any `work-item`
  submission without a recognized verdict matched to that exact item by a
  content-and-ordinal correlation key, not a count.
- The close's declined-item accounting: `DeclinedItemOutcome`,
  `CloseLedger` (one correction per ordinal, a second refusal ends the close
  — `AC-0038`/`AC-0039`), and `render_close_output` (`AC-0014`'s printed
  rationale).
- `work-loop/SKILL.md` gains three lines pointing at the new
  [reasoning check](../../../../packs/core/.apm/skills/work-loop/references/work-item-capture.md#the-reasoning-check)
  reference section; the enforceable rule lives in `project_knowledge.py`,
  never in skill prose, per the plan's own warning that a source-text
  assertion over a reference is the hand-written list `AC-0069` names as
  catching nothing.
- Self-hosted the pack: `.claude/skills/` and `.agents/skills/` mirrors were
  stale from an earlier task (T4's kind-vocabulary widening had never been
  projected); `agentbundle catalogue self-host --write --force` caught both
  that backlog and this task's own delta up in one pass, and
  `check_contract_parity.py` still reports all 18 contract files synced.

## Verification, checked by the implementer

- Project-knowledge suite: **322 passed, 0 failed**, against a 300 baseline
  (22 new tests, all T7's).
- Work-loop suite: **1230 passed, 5 skipped, 68 subtests passed**, matching
  the 1230 baseline exactly — T7 added no new work-loop test file; every new
  assertion lives in `test_contracts.py`, per the plan's own Touches split.
- `make lint-ruff lint-mypy`: clean.
- `agentbundle catalogue lint --root . --deep`: `work-loop/SKILL.md` body is
  983 lines (WARN threshold is 500; the ERROR threshold this task had to
  stay under is 1000) — no error-severity finding.
- `python3 tools/catalogue/check_contract_parity.py`: 18 files synced.
- Manual QA (`Done when`): a real close, using the shipped functions
  end-to-end (no test doubles besides the dispatch stand-in a sandboxed run
  cannot avoid), declining one item of each shape — `defect`, `question`,
  `decision` — captured all three, printed each one's `necessity_rationale`
  beside it, and derived a real capture id per item. A second run wrote a
  captured item through the real store (`observations/work-item/2026-09.jsonl`)
  and then refused a razor-failing item with `work_item_unnecessary`,
  leaving the store's file set unchanged.
- The floor refuses in all six drives (`dispatch_reasoning_check`, obligation
  4): tier not configured (`dispatch=None`), endpoint unreachable
  (`ConnectionError`), a raised exception of a different shape
  (`TypeError`), a well-formed response outside the recognized set
  (`"maybe"`), expiry (a 0.25s responder against a 0.02s bound), and the
  positive direction (a recognized `"admit"` verdict) — each driven
  separately in `test_dispatch_reasoning_check_fails_closed_for_every_drive`.
- The write-path floor's four `AC-0068` cases and the positive
  correspondence-not-count spy are each their own test: absent, outside the
  recognized set, a verdict computed for a different item (dispatching one
  item twice and writing a second, undispatched item — which a call-count
  check would pass), and a corrected re-submission reusing its
  pre-correction verdict.

## Deviations from the task body

- The plan's Touches list did not name a new script under
  `.apm/skills/work-loop/scripts/`; the dispatch, its enumeration, and the
  write-path floor all live in `project_knowledge.py` (the one script T7's
  Touches does name), and `SKILL.md`/the reference stay documentation —
  consistent with the task's own warning against enforcing this in skill
  prose.
- `WORK_ITEM_REASONING_VERDICTS`'s `work_item_unnecessary` doubles as the
  floor's generic "no recognized verdict" refusal code (absent, malformed,
  or mismatched cases) — no twelfth catalog code was added, and D4 already
  closes that catalog at eleven additions.

## Out of scope observed

`packs/core/tests/pack/test_ride_along_admission_test.py::test_capture_section_routing_bullet`
fails on the pristine, already-committed baseline (verified by stashing this
task's edits and re-running it against T6's landed state) — a prior task's
rewrite of the `## Capture` section's routing prose broke a byte-pinned
quote (`C4`) an unrelated RFC-0090 feature's suite carries. Not caused by
this task, not in T7's declared gate list, and not fixed here.
