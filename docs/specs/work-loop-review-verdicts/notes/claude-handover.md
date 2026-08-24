# Claude handover — finish AC12

## Current state

- Implementation is complete; spec is `Shipped`, plan is `Done`, and the specs
  index is `Shipped`.
- Fresh final reviews are clean: adversarial, quality, and security.
- The work-loop engine is at `CODE-HUMAN-GATE` for run
  `42579fd8-62b8-4065-8ead-efb5f5807126`.
- Current verdict is `READY_WITH_RESIDUAL_RISK`; see
  [`review-verdict-pending.md`](review-verdict-pending.md).
- Do not repeat research or redesign the reviewer roster/verdict mechanism.
- Preserve all existing worktree changes and review reports. Do not add a
  Co-Authored-By trailer.

## Already verified

- `104 passed, 1 skipped` across core pack, roster projection, and site-routing
  tests.
- `lint-spec-status.py --root .` passed.
- `git diff --check` passed.
- Work-loop and operational-safety `.agents` / `.claude` projections are
  byte-identical to `.apm` sources; Codex agent prompt-body parity was checked.
- `tools/build-site.py` regenerated the released `/now/` highlight for core
  `2.10.6`.
- The code-graph benchmark is registered as non-dispatchable backlog work.

## Remaining AC12 tail

Run these in a runtime that permits bounded directory deletion and atomic
directory rename:

```bash
FORCE=1 PYTHONDONTWRITEBYTECODE=1 make build-self
SKIP_SAST=1 make build-check
make site-build
```

If all pass, then:

1. Change AC12 in `spec.md` from its deferred unchecked form to `[x]` and
   remove the inline deferral marker.
2. Update the specs-index summary from “AC1–AC11 complete; AC12 ... deferred”
   to “12 ACs complete”.
3. Re-run focused tests, spec-status lint, projection parity, and
   `git diff --check`.
4. If an `experience-reviewer` and rendered-browser surface are available, run
   that non-mandatory review against `/now/`; otherwise preserve the named skip.
5. Re-emit `review-verdict.v1`: remove the AC12 deferral; use `READY` only if no
   residual-eligible reviewer skip or blind spot remains, otherwise retain
   `READY_WITH_RESIDUAL_RISK`.
6. Complete the existing human gate only after the user confirms the final
   diff/merge decision.

Do not change build tooling merely to evade an environment policy denial. If a
command fails for a product reason, record the real gate failure and emit
`BLOCKED`; do not relabel it residual risk.
