# Brief: pin every workflow's posture with one shared harness

- **Slug:** `workflow-posture-pinning-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Ready
- **Ready confirmed:** 2026-11-05 by eugenelim, lifecycle owner. Bound to the file as reviewed `Clean` by an independent delivery-brief review at commit `97221f5bb`; the later edits were wording corrections, recorded as nonmaterial by the lifecycle owner. Slice membership and status are the Spec map's; this line does not restate them.
- **Source / provenance:** Mode `repo-origin`; locators [`docs/product/intents/dispatch-workflow-posture-assertions.md`](../intents/dispatch-workflow-posture-assertions.md) and [`docs/product/intents/workflow-posture-harness-consolidation.md`](../intents/workflow-posture-harness-consolidation.md), cut into slices on 2026-11-05 from a read of `tools/`.
- **Parent intent:** intent:dispatch-workflow-posture-assertions

## Outcome

`test-corpus.yml` and `test-roster.yml` carry posture checks, the pages workflow checks run on `tools/posture_harness.py`, and removing `persist-credentials: false` from any checkout fails a gate.

## Success metrics

- A posture check for both dispatch-only workflows fails a seeded widened token, dropped timeout, added trigger, added dispatch input, larger runner, or `secrets.` reference.
- `tools/test-pages-workflow.py` and `tools/test-pages-concurrency.py` report the same mutation count and family coverage as before the move.
- One guard owns zizmor's `artipacked` finding for every workflow.

## Scope / Non-goals

**In scope:** the three slices below, all in stdlib.

**Non-goals:** replacing the regex model in `tools/test-build-check-workflow.py` with a YAML parser, and moving that file onto the shared harness. The owner chose stdlib for the job that wears the required check, and the file's bash differential and shape-stable fixture do not fit the harness; this brief keeps both as they are.

## Proposed slices

Every slice is checked by an agent with no live service, credential, or human reviewer.

| # | Slice | Agent-only verification | Depends on | Gating |
| --- | --- | --- | --- | --- |
| P1 | A posture check for `test-corpus.yml` and `test-roster.yml` built on `tools/posture_harness.py`, with one mutation per assertion family (trigger set, no dispatch inputs, top-level read token with no job key, timeout on every job, exact hosted runner label, `persist-credentials: false` on every checkout, no `secrets.`). Wired through `tools/repo/build_gate_chain.py` and the ordered literal in `tools/test_build_gate_chain.py`. Add both files to the tuple in `tools/check-zizmor-excessive-permissions.py`. | The check passes on both files; each family mutation fails it; the workflow posture test for `ci-security.yml` still passes | none | none |
| P2 | A sibling guard, modelled on `tools/check-zizmor-excessive-permissions.py`, that owns zizmor's `artipacked` ident for all workflows, so the broad gate's high severity floor no longer hides it. Wired as a step in `ci-security.yml` right after the zizmor install, beside the existing `python3 tools/check-zizmor-excessive-permissions.py` run, because it needs zizmor on the path and the build chain does not install it. | Current state, counted 2026-11-05: 48 `actions/checkout` uses under `.github/workflows`, 20 set `persist-credentials: false`, 28 do not (`docs.yml` 10, `build-check-windows.yml` 4, `release-agentbundle.yml` 3, `ci-security.yml` 2, `publish-catalogue.yml` 2, and one each in `codeql.yml`, `iac-release-loop-canary.yml`, `iac-staleness.yml`, `pack-evals.yml`, `pages.yml`, `release-credbroker.yml`, `release-jsonl-otlp-exporter.yml`). The slice also sets `persist-credentials: false` on those 28, or lists a checkout in the guard's named exception list with a reason (for example a release job that pushes). The guard passes on the real tree after that; a seeded checkout without `persist-credentials: false` fails it; the workflow posture test for `ci-security.yml` still passes | none | none |
| P3 | Move `tools/test-pages-workflow.py` and `tools/test-pages-concurrency.py` onto the shared harness, keeping crafted-input predicates and the four-element mutation tuple where they differ. | Mutation count and family list are re-measured at the time of the move (not copied from the intent) and match before and after; both tests pass | none | none |

### Manual or live residue, split off as non-blocking follow-ups

- None. The accepted residual that a dispatched run executes the selected ref's copy of the file stays as recorded in `docs/architecture/remote-verification.md` (accepted residual).

## Decisions

- 2026-11-05, eugenelim: no release or publish workflow checkout may keep persisted credentials unless the job pushes with the checkout token, in which case it is listed in the guard's exception list with that reason. P2 reviews all seven release and publish checkouts in four files (`release-agentbundle.yml` 3, `release-credbroker.yml`, `release-jsonl-otlp-exporter.yml`, `publish-catalogue.yml` 2).

## Constraints / Appetite

Three sessions; P1 medium, P2 medium, P3 small to medium.

## Assumptions / Risks

- Riskiest assumption: a key grammar that fails closed on every unmodelled form can be written for a flat workflow. De-risk in P1 by running each family's mutation list, including duplicate keys, quoted keys, aliases and flow forms, and requiring the check to refuse rather than skip them.
- `test-corpus.yml` is a four-job matrix, so per-job assertions need one mutation per family, not per job. The sharding spec already pins the matrix against `SHARDS=`; P1 does not repeat that.

## Ready gaps (Draft only)

- None open.

## Spec map

| Spec | Status |
| --- | --- |
| dispatch-workflow-posture-check | Draft |

## Provenance

- Parent intent: [`dispatch-workflow-posture-assertions.md`](../intents/dispatch-workflow-posture-assertions.md).
- Also delivered here: [`workflow-posture-harness-consolidation.md`](../intents/workflow-posture-harness-consolidation.md), whose slices are P2 and P3 and whose build-check harness move is a non-goal above.
