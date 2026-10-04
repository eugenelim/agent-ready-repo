# Verification ledger: silent-domain-gap

Execution observations recorded after the plan baseline was pinned on
2026-10-04. The approved spec and plan are unchanged.

## Proof obligations

- **T2 — the silent-domain walk reds without the third source.** With the
  third source removed from the `gap-sources` cell of
  `references/visual-observation.md` (all other text unchanged), and both packs
  re-installed by the roster module, `test_a_silent_needed_domain_is_held`
  failed (1 failed). The cell was restored and the test passes.
- **T3 — the eval assertions red on the earlier `evals.json`.** With
  `evals.json` replaced by its `origin/main` copy (frontend-engineering
  0.4.3), `test_the_silent_domain_eval_grades_the_hold` and
  `test_golden_prompts_state_type_shape_and_layout_values` both failed
  (2 failed). The current file was restored and both pass.

## Observations

- **T1–T4 — implemented by the controller.** The owner directed controller
  implementation on 2026-10-04; each dispatch receipt records
  `human-directed`.
- **Post-gates review round 1.** Sustained: the guide routing sentence is now
  pinned by its own test; the golden-prompt check reads every value-bearing
  Shape and containment and Spatial structure commitment, and both golden
  prompts state the alignment commitment; the confirmed golden implementation
  consumes the taxonomy's typography, control border and square corners; the
  no-third-operation-kind check reads every backticked token in the cell.
- **Local-only lint interaction.** `tools/lint-agents-md.py` walks
  `.context/`, so the gitignored codex-eval scratch copies of the frontend pack
  failed it locally. The copies were removed and the scratch driver now builds
  its catalogue outside the repository; CI never saw them.
