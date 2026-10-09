# Verification ledger: intent navigation — navigator core

Execution observations for slice 1. The spec and plan hold the obligations;
this file holds what execution measured and where it departed from a task
row's literal method.

## Pre-execution

- 2026-10-08, engine run `08208db7-158f-4302-910e-347d55a570c8`: a fresh
  pre-EXECUTE adversarial review ran three rounds over the approved pair.
  Rounds 1 and 2 sustained five findings, all plan wiring; the owner approved
  the revision and re-approved the spec and plan the same day. Round 3 was
  clean.
- The slice branch `eugenelim/intent-navigation-slice-1` was cut from
  `feature/intent-navigation` at `8392ef8d6`, which contains the 2.30.1
  terminality repair merge `aafa2aa1b`; `git merge-base --is-ancestor
  aafa2aa1b HEAD` passed before T1.

## T1

- `python3 -m pytest packs/core/tests/skills/navigate-intents/ -q`: 54
  failed, 24 passed. Every failure is the absent module — 39 on
  `navigate_intents.py`, 15 on `intent_graph.py`. The 24 passes are
  fixture-shape checks over the committed corpora and the test-time builder.
- Interim red, by design: `tools/lint-pack-test-boundary.py` (and its
  self-test, which runs it over the real tree) reports
  `packs/core/tests/skills/navigate-intents` as a suite no runner names. T5
  adds the `Makefile` runner that satisfies it. The slice is one pull request
  whose gates run on its head, and each task's `Done when` runs only its own
  tests, so commits T1 to T4 carry this one finding and the head does not. A
  temporary `_NO_RUNNER` entry was declined because `tools/` is outside T1's
  and T5's pinned `Touches`.

## T2

- Done-when: `test_derivation_contract.py` 45 passed; the copy pin test 3
  passed; `tests/roster/test_intent_delivery_relations_repository.py` 4
  passed; `agentbundle catalogue verify --root .` ok; `make lint-ruff
  lint-mypy` clean.
- Correction inside T2: the first pass returned `dangling` for a spec
  `Discovery:` path or markdown link naming a tombstone. AC-0007 requires
  `retired_target` with the tombstone's `Reissued as:` value. The derivation
  now consults tombstones by path, and three tests prove it over the new
  `fixtures/negative/spec_discovery_retired_target/` corpus.
- `intent_graph.py` first carried internal criterion citations in its
  comments; they were reworded so the canonical shipped-text grep from
  `packs/AGENTS.local.md` returns nothing over the skill and its projections.
- `agentbundle catalogue self-host --root . --write` refuses a dirty tree, so
  it ran with `--force`, which lifts only that guard. It wrote only the two
  `navigate-intents` projections.
