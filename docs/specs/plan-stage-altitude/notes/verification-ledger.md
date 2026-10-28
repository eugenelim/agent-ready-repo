# Verification ledger — plan-stage-altitude

Execution observations recorded after plan approval. Neither approved artifact is amended by these.

## Scope admitted by the owner during EXECUTE

- `packs/core/tests/skills/work-loop/test_loop_engine.py` — the `deep-nesting` tmp-recovery fixture failed on the base commit: Python 3.14's `json` parses 20,000 levels without `RecursionError`, so the fixture was valid content and was promoted silently. Depth is now 200,000 (about 400 KB, under the 8 MiB reader bound). Observed: 4 of 5 parameters passed before; 5 of 5 after, on Python 3.14.9.
- `packs/core/.apm/skills/work-loop/references/verification-modes.md` and `packs/core/.apm/skills/bug-fix/SKILL.md` (with its `fix-hands-off-to-work-loop` eval) — they came in with the merged `work-loop-evidence-modes` change and still named the retired `no stub (mode)` record and a PLAN materialization rule. Both now match work-loop PLAN step 8 and step 1b, and the roster sweep reads both.

## Merge adaptation

- `origin/main` landed `work-loop-evidence-modes` (core 3.1.27) first. Step 1b now has EXECUTE write the diagnosis regression test in either mode; two `test_evidence_modes_contract.py` pins and two of its eval records follow; its literal-version test became a parity test. Core is 3.1.28.

## Environment

- The local `tests/roster` run shows 25 failures or errors, the same set on a clean `origin/main` checkout (credbroker wheel build, portable-catalogue packaging, and others), so none come from this change. CI evidence is recorded in the pull request.
