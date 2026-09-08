# Brief: Measure pack behavior on Claude Code and Codex

- **Slug:** `multi-adapter-eval-runner`
- **Received:** 2026-09-03
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** Repository-origin capability 5 from [`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md), accepted at the current checkout by owner decision.
- **Parent intent:** [`cross-adapter-behavior-enforcement`](../intents/cross-adapter-behavior-enforcement.md)

## Outcome

Pack authors can opt into the existing `agentbundle pack evals run --adapter`
surface to measure the same pack on `claude-code` and `codex`, with the host,
model, CLI version, and inference configuration recorded for each result. The
default remains `claude-code`; the scheduled workflow remains Claude Code-only
and report-only. This supplies capability 5 within the parent intent's
[three-layer shape and lifecycle allocation](../intents/cross-adapter-behavior-enforcement.md#where-the-lifecycle-holds-and-where-it-breaks)
without changing either.

## Success metrics

- A local `--adapter codex` run measures every selected Tier-A query and emits a
  bounded summary whose `adapter` is `codex`; a failed or unparseable host run is
  reported as a harness error, not a clean non-activation.
- The same case set can be run on `claude-code` and `codex`, with each result
  bound to the qualification tuple required by
  [`cross-model-steering-survey.md`](../research/cross-model-steering-survey.md):
  pack version, host adapter version, model snapshot, and inference/tool
  configuration.
- An invocation that omits `--adapter` still selects `claude-code` and preserves
  its current report contract.
- The weekly schedule in [`.github/workflows/pack-evals.yml`](../../../.github/workflows/pack-evals.yml)
  still runs only the pinned `@anthropic-ai/claude-code@2.1.185` CLI, uses only
  `ANTHROPIC_API_KEY`, and remains report-only.
- No live pack eval enters `make ci`, `make pre-pr`, or the pre-PR aggregator.
  Their existing runner self-test and workflow-posture test remain gates.
- `get_judge(adapter, model, config)` remains independently selectable and every
  judged summary continues to record `judge_adapter`; a Codex-authored artifact
  can therefore use the existing Claude Code judge, and the reverse.

## Current state

**Measured — one exact detector assignment.** The exact text
`adapter = "claude-code"` occurs once, at
[`pack_evals.py:159`](../../../packages/agentbundle/agentbundle/commands/pack_evals.py):

```text
rg -n -F 'adapter = "claude-code"' packages/agentbundle/agentbundle/commands/pack_evals.py
# 159:    adapter = "claude-code"
```

Three separate summary dictionaries still write the literal
`"adapter": "claude-code"` at lines 696, 843, and 969. The headless summary at
line 586 instead reads `detector.adapter` but falls back to `claude-code`.

```text
rg -n -F '"adapter": "claude-code"' packages/agentbundle/agentbundle/commands/pack_evals.py
# 696, 843, 969 — 3 occurrences
```

**Measured — the detector seam exists but has one implementation.** The CLI
already exposes `--adapter` with a `claude-code` default at
[`pack_evals.py:1104`](../../../packages/agentbundle/agentbundle/commands/pack_evals.py),
while `_DETECTORS` contains only `ClaudeCodeDetector` at line 223. The runner
needs a second detector behind the existing parameter, not a second public
flag. This corrects a wording conflict with the parent intent, which says the
capability adds the parameter.

**Measured — judging is already cross-family.** Built-in declarative judge
backends name `claude-code` and `codex` at
[`pack_evals.py:318`](../../../packages/agentbundle/agentbundle/commands/pack_evals.py).
`get_judge(adapter, model, config)` selects either built-in or configured
backend at line 374, and `grade_judge` records `judge_adapter` at line 972.
Detector work must not duplicate or couple this judge seam. The repository
inventory reaches the same finding in
[`behavior-controls-inventory.md`](../research/behavior-controls-inventory.md).

**Measured — the scheduled boundary is narrow.** The current
[`pack-evals.yml`](../../../.github/workflows/pack-evals.yml) has only `schedule`
and `workflow_dispatch` triggers at lines 17–26; the dispatch input `packs` is
already present at lines 22–26. It installs only
`@anthropic-ai/claude-code@2.1.185` at line 52, binds only
`ANTHROPIC_API_KEY` at line 59, and makes the eval step report-only with
`continue-on-error: true` at line 56.

[`tools/test-pack-evals-workflow.py`](../../../tools/test-pack-evals-workflow.py)
currently asserts: the file exists and parses; triggers are exactly schedule
plus dispatch; top-level permissions are `contents: read` with no job override;
the Anthropic secret comes from `secrets`, reaches only the eval step, and the
eval step is report-only; and uploads contain bounded `summary.json` files but
not model outputs. Its mutation matrix proves each assertion family. It does
not assert the CLI version pin, Claude-only default, or `packs` input.

**Measured — local gates test the runner but never run a live eval.** This
search returns no matches:

```text
rg -n 'agentbundle pack evals run|run-pack-evals\.py --pack' \
  Makefile tools/catalogue/pre_pr_catalogue.py \
  tools/repo/build_gate_chain.py tools/hooks/pre-pr.py
```

The pre-PR aggregator runs only `tools/test-run-pack-evals.py` and
`tools/test-pack-evals-workflow.py` at
[`pre_pr_catalogue.py:137`](../../../tools/catalogue/pre_pr_catalogue.py). This
matches the report-only boundary recorded in
[`behavior-controls-inventory.md`](../research/behavior-controls-inventory.md).

## Scope / Non-goals

**In scope:**

- A headless `codex` detector behind the existing `--adapter` registry, with
  Codex projection, invocation, parsing, error classification, and truthful
  result provenance.
- Contract tests for both detector families, including default preservation,
  adapter-specific event parsing, non-zero exits, timeouts, malformed streams,
  missing terminal events, and summary labelling.
- Local opt-in instructions for pack authors in
  `guides/_shared/how-to/author-a-skill.md`.
- A conditional, manual-only Codex workflow lane if the owner confirms that
  slice after its secret, CLI pin, and posture contract are known.
- `claude-code` and `codex` only. Evidence for one must never be presented as
  evidence for another host.

**Non-goals:**

- Changing the default adapter, the weekly schedule, its Claude Code-only
  execution, its named CLI pin, or its report-only behavior.
- Adding a live pack eval to the Makefile, `make ci`, `make pre-pr`, or the
  pre-PR chain.
- Adding Copilot, Cursor, Gemini CLI, Kiro, or any other host before a later
  host-specific probe establishes its contract.
- Rebuilding the existing judge backend seam or treating judge support as
  proof that live activation support exists.
- Claiming portability beyond the exact measured qualification tuple.
- Turning policy evaluation into a blanket blocking gate. The parent intent
  owns where enforcement applies.

## Constraints / Appetite

- Keep this to one local detector slice and, only if confirmed, one manual
  workflow slice. Reuse the existing CLI, detector registry, summary shape,
  eval corpus, and judge seam.
- The default and scheduled workflow do not change. Every additional workflow
  adapter is opt-in, vendor-secret-bearing, manual-only, report-only, and pinned
  to a named host CLI version.
- Treat the workflow as a security boundary. Any manual Codex lane must retain
  schedule-plus-dispatch-only triggers, `contents: read`, step-local secret
  binding, bounded summary uploads, and no uploaded model outputs.
- A policy family ships precise or advisory, never between the two. The cited
  measurement in the [parent intent](../intents/cross-adapter-behavior-enforcement.md#de-risk)
  found that a stylistic predicate blocked 405 of 1,477 governed files, 27.4%,
  against a 0.4% per-family budget. Precise families may block; stylistic
  families remain advisory. The calibration basis is in
  [`agent-behavior-oracle-patterns-survey.md`](../research/agent-behavior-oracle-patterns-survey.md).
- Never impose a hard per-criterion word budget. This is already rejected by
  `new-spec`, RFC-0099, and the ticked Shipped criterion in
  `docs/specs/shaping-review-contracts/spec.md`.

## Proposed slices

**E1 is the sole delivery slice.** Rejected: a conditional workflow lane adding
Codex to CI. Each added adapter puts a vendor secret into a security-load-bearing
workflow and needs every host CLI pinned on the runner, so additional adapters
stay local and on-demand while the default adapter and the scheduled workflow are
unchanged.

None is confirmed and no spec is authored. Each acceptance-criteria number is
a ceiling and a stall threshold, never a floor; a smaller complete contract
ships with fewer criteria.

| # | Slice | Owning surface | Verification | Guide | AC ceiling | Gating |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | Local Codex Tier-A activation measurement through the existing adapter seam, including truthful provenance | `packages/agentbundle/agentbundle/commands/pack_evals.py` | `tools/test-run-pack-evals.py` covers the Codex projection/invocation/parser contract, failure modes, default preservation, and adapter-labelled summaries without calling a live model | update `guides/_shared/how-to/author-a-skill.md` because `--adapter codex` is adopter-visible | 8 | after the Codex CLI activation contract, version pin, and result tuple are resolved |

E1 is independently shippable as a local capability. A CI lane is not required to
claim local `claude-code`/`codex` measurement and disappears if the owner keeps
the second adapter local-only.

## Assumptions / Risks

- **Assumption — inferred:** Codex exposes a headless, machine-readable event
  contract from which actual skill activation can be distinguished from model
  text. The repository proves this only for Claude Code today.
- **Risk — cited:** A measurement on one adapter/model/configuration tuple will
  be mistaken for portable behavior. The qualification and paired-evaluation
  discipline live in
  [`cross-model-steering-survey.md`](../research/cross-model-steering-survey.md).
- **Risk — measured:** Reusing the three hard-coded in-harness/judge summary
  literals could mislabel Codex-produced artifacts as `claude-code` even after
  a detector lands.
- **Risk — inferred:** A shared parser could normalize away host-specific
  event differences and turn an unmeasured Codex run into a false miss. Each
  adapter needs fixtures from its pinned CLI contract.
- **Risk — measured:** The workflow posture test does not yet pin the CLI
  version, scheduled adapter, or `packs` input, so an on-demand extension could
  regress an owner constraint while leaving the current test green.
- **Risk — cited:** A cross-family judge reduces self-preference but does not
  establish truth; calibration and abstention rules remain those of
  [`agent-behavior-oracle-patterns-survey.md`](../research/agent-behavior-oracle-patterns-survey.md).

## Ready gaps (Draft only)

- **Open — reconcile the parent wording.** The parent says this capability adds
  an opt-in adapter parameter, but `pack_evals.py:1104–1108` already exposes
  `--adapter`; only the Codex detector is absent. Search:
  `rg -n -- '--adapter|_DETECTORS|get_detector' packages/agentbundle/agentbundle/commands/pack_evals.py`.
  The parent remains authoritative and needs an owner-approved wording fix
  before this brief is Ready.
- **Open — acquire the pinned Codex activation contract.** No repository source
  defines a `CodexDetector`, Codex activation event parser, or Codex JSON/JSONL
  activation invocation. Search:
  `rg -n 'CodexDetector|parse_codex|codex.*activation|codex exec.*(--json|jsonl)' packages/agentbundle/agentbundle/commands/pack_evals.py tools/test-run-pack-evals.py guides/_shared/how-to/author-a-skill.md`
  returned no matches. A later contract-acquisition step must record the exact
  supported CLI version, argv, output fixtures, terminal-event rule, exit
  behavior, skill-activation signal, model selector, and non-interactive auth
  behavior before E1 can be specified.
- **Open — name the first paired result tuple.** The repository does not select
  the Codex model snapshot or inference/tool configuration that will pair with
  the pinned Claude Code run. Record both sides of the tuple before comparison;
  do not rely on either CLI's moving default.
- Ready also requires a revision-bound clean shaping review and the owner's
  explicit confirmation. Neither has happened.

## Rabbit holes

- Rejected: a second eval command because the public `--adapter` seam already
  exists and owns detector selection.
- Rejected: changing the scheduled job to a matrix because that changes the
  owner-pinned Claude Code schedule and widens the managed-secret boundary.
- Rejected: treating `get_judge("codex", ...)` as Codex activation support
  because judging consumes an artifact while activation must observe the host
  routing event.
- Rejected: a generic multi-host parser because no untested host contract may
  be inferred from Claude Code or Codex.
- Rejected: a hard per-criterion word budget because semantic atomicity and
  testability, not length, determine an acceptance criterion.

## Spec map

| Spec | Status |
| --- | --- |

## Provenance

This brief is capability 5, `multi-adapter-eval-runner`, from
[`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md).
Its delivery boundary uses the parent's lifecycle and three-layer shape without
restating them. Repository research remains at
[`cross-model-steering-survey.md`](../research/cross-model-steering-survey.md),
[`behavior-controls-inventory.md`](../research/behavior-controls-inventory.md),
[`agent-behavior-oracle-patterns-survey.md`](../research/agent-behavior-oracle-patterns-survey.md),
and [`phase-scoped-policy-delivery.md`](../research/phase-scoped-policy-delivery.md).