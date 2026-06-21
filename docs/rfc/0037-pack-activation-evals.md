# RFC-0037: Pack-level activation evals — repeatable empirical trigger testing per skill

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental (optional: trial running, results pending — see the Experiment / validation section) -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-21
- **Date closed:** 2026-06-21
- **Related:** RFC-0031 (pack.toml as rich source of truth), ADR-0021 (pack-manifest source of truth), RFC-0036 (markdown→office, shipped first `evals/evals.json`), ADR-0017 (SAST CI gate precedent), ADR-0014 (rigor scales with risk)

## The ask

- **Recommendation (BLUF):** Adopt the agentskills.io **trigger-eval** convention catalogue-wide — a per-skill `evals/eval_queries.json` of `{query, should_trigger}` cases — and add a `tools/run-pack-evals.py` runner that executes a pack's trigger evals through a headless `claude -p` harness, measuring whether each skill *activates* on the prompts it should and stays quiet on the near-misses it shouldn't. `pack.toml` gains a `[pack.evals]` section naming which skills the runner covers. It runs in its own scheduled/dispatch CI workflow, report-only, never on the PR critical path. Scope is **Tier A (activation/selection) only**; output-quality grading (Tier B) is a separate future RFC.

- **Why now (SCQA):** *Situation* — the catalogue has 13 packs whose value rests on skills triggering reliably from their `description:` field. *Complication* — every existing gate is **structural** (frontmatter shape, projection, drift, install mechanics); none empirically verifies that a skill *actually activates* when an agent reads a real prompt. The behavioural assets that exist — 14 skills across 4 packs (`atlassian`, `contracts`, `converters`, `figma`) ship `evals/evals.json` — all test output *quality*, not triggering, and no runner executes any of them. *Question* — what is the repeatable, empirical way to test each pack that the structural gates provably can't?

- **Decisions requested:**
  1. **Adopt the agentskills.io trigger-eval convention** (`evals/eval_queries.json`, flat `[{query, should_trigger}]`) as the catalogue's activation-eval format — *recommended: yes* · decide-by: RFC approval · default if no objection: adopt.
  2. **Extend `pack.toml` with `[pack.evals] skills = [...]`** as the single declarative source of truth for which skills the pack-level runner covers — *recommended: yes* · decide-by: RFC approval · default: adopt.
  3. **Add `tools/run-pack-evals.py`** (headless `claude -p` harness, `trigger_rate` over 3 runs) plus a **scheduled/dispatch, report-only CI workflow** (`pack-evals.yml`); keep `make build-check` structural and fast — *recommended: yes* · decide-by: RFC approval · default: adopt.
  4. **Scope to Tier A only** — defer output-quality grading (Tier B, the `evals/evals.json` with/without-skill comparison) to a future RFC — *recommended: yes* · decide-by: RFC approval · default: adopt.

## Problem & goals

The catalogue's structural gates (`lint-skill-spec.py`, `lint-agent-artifacts.py`, projection/drift checks, install integration tests) verify that a pack **ships and projects correctly**. They are silent on the one property the whole skills mechanism depends on: a skill is loaded only when its `description:` matches the user's task ([agentskills.io progressive disclosure](https://agentskills.io/skill-creation/optimizing-descriptions)). An under-specified description fails to trigger when it should; an over-broad one triggers when it shouldn't. Neither failure is visible to any current check — they are only discoverable by an agent (or a user) hitting the gap in practice. 14 skills across 4 packs (`atlassian`, `contracts`, `converters`, `figma`) ship `evals/evals.json`, but that convention tests *output quality* once a skill is already running, not *whether it runs*, and no runner executes any of them (CI only asserts the files exist with the right keys).

**Goals.**

- A **repeatable, empirical** way to test each pack: same inputs, same harness, a number you can compare across model versions and `description:` edits.
- **Per-skill ownership** that stays inside the agent-skills convention — the eval lives next to the `description:` it tests.
- **Negative controls** (near-miss prompts that must *not* trigger) as first-class, to catch over-broad descriptions.
- A **pack-level aggregator** that runs every covered skill's evals from one declarative list.
- **No new dependency** and **no cost or flakiness on the PR critical path.**

**Non-goals.**

- **Output-quality grading** (does the skill produce a *good* answer once triggered). That is the existing `evals/evals.json` convention and a genuine future tier; bundling it here would double the surface and force an LLM-judge design before activation is even measured.
- **A description-optimization loop** (auto-tuning `description:` against the eval set, train/validation splits). The convention supports it; we are building the regression measurement first, not the optimizer.
- **Shipping a runtime eval service to adopters.** The runner is catalogue-internal dev tooling, like the linters and the SAST gate — not a primitive in any pack (Charter Principle 3).
- **Gating PRs on live-model results** in the first cut. Report first, calibrate, gate later.

## Proposal

### Decision 1 — Trigger evals follow the agentskills.io convention, in their own file

Each covered skill gains `evals/eval_queries.json` — the [agentskills.io trigger-eval format](https://agentskills.io/skill-creation/optimizing-descriptions): a flat JSON array of `{ "query": "...", "should_trigger": true|false }`, ~8–10 should-trigger and ~8–10 should-not-trigger cases. The negatives are **near-misses** — prompts that share keywords or concepts with the skill but need something else — not trivially-irrelevant prompts (those "test nothing").

```json
[
  { "query": "research best practices for rate-limiting a public API, with citations", "should_trigger": true },
  { "query": "we need to pick between Postgres and DynamoDB — what's the right call here?", "should_trigger": false }
]
```

This is deliberately a **separate file** from `evals/evals.json`. The output-quality schema (`{skill_name, evals: [{id, prompt, expected_output, ...}]}`, validated today by `lint-skill-spec.py`) has no activation dimension; adding `should_trigger` to it would contradict that spec. The trigger-eval file is the convention's own answer for activation, so negatives stay **skill-local without forking the quality schema**. The skill that owns a boundary owns the near-misses that test it.

**Path decided here:** `evals/eval_queries.json` — the docs' filename, placed under the repo's already-blessed `evals/` subdir (`BLESSED_SUBDIRS` in `lint-skill-spec.py`) so every eval artifact lives in one place rather than a loose file at the skill root. This is the catalogue's instantiation choice, not an open question.

### Decision 2 — `pack.toml` references the covered skills

```toml
[pack.evals]
# Skills whose evals/eval_queries.json the pack-level runner executes.
skills = ["research", "build-outline", "source-map"]
```

`[pack.evals].skills` is the single declarative source of truth for coverage. It is an explicit allowlist, not auto-discovery, because some skills legitimately ship no trigger evals and the list is a deliberate contract (the same reasoning that made `converters`' carry-over CI gate enumerate its skills by hand). The runner and a lint read `[pack.evals].skills`. This is a **new** trigger-eval coverage list — *not* a replacement for the existing converters carry-over gate, which tests a different contract (presence of *output-quality* `evals/evals.json` for five named skills, plus the negative assertion that `msg-to-markdown` ships none). That gate and its `msg-to-markdown` guard stay; any later consolidation is out of scope here. Extends RFC-0031's "`pack.toml` as the rich superset source of truth."

### Decision 3 — The runner and CI posture

`tools/run-pack-evals.py --pack <name> [--runs 3]`:

1. Reads `packs/<pack>/pack.toml` → `[pack.evals].skills`.
2. Projects the pack into an isolated temp directory (claude-code adapter) with a minimal `.claude/settings.json`, so only that pack's skills are discoverable.
3. For each query in each covered skill's `evals/eval_queries.json`, runs the convention's own detector — `claude -p "<query>" --output-format json --allowed-tools Skill` (with a per-run timeout as the bound) — and parses the result for a `Skill` `tool_use` event, recording **whether it fired** and **which skill** (`.input.skill`) — activation *and* selection. `--allowed-tools Skill` is deliberate: Tier A only needs to **observe** the activation event, not **execute** the skill body (the body's tools, and whether the run succeeds, are Tier B).
4. Runs each query `--runs` times (default 3) and computes a **`trigger_rate`** = fraction of runs that fired the skill.
5. Grades per the convention: a `should_trigger:true` query passes if `trigger_rate > 0.5`; a `should_trigger:false` query passes if `trigger_rate < 0.5`. **Intra-pack exclusivity comes for free** — because the whole pack is projected, the runner can also flag when a *different skill in the same pack* fired, so each positive query doubles as a "this skill and no other (in-pack)" check. Cross-*pack* collisions are out of scope for the per-pack runner.
6. Emits a per-pack JSON summary (trigger rates per query, pass counts) to a gitignored workspace dir.

**No new dependency:** stdlib + `tomllib` + the `claude` CLI (the same binary the repo already runs under). The detector flags are spike-confirmed present on `claude` 2.1.181 — `--print`, `--output-format json`, `--allowed-tools` (the exact form the agentskills.io guide ships). The bound is a wall-clock timeout per run, not a turn cap (`--max-turns` is an SDK option, not a CLI flag on this version); early-exit-once-decided is an optimization the agentskills.io guide notes as client-dependent, not relied on here.

**CI:** a new `.github/workflows/pack-evals.yml`, triggered on **schedule + manual/label dispatch only**, consuming an `ANTHROPIC_API_KEY` repo secret, reporting `trigger_rate` per skill and **never failing the build** in the first cut. `make build-check` stays structural, deterministic, and fast — no live model on the PR path.

### Decision 4 — Tier A only

This RFC delivers **activation/selection** (Tier A). Output-quality grading — running `evals/evals.json` with-skill vs. without-skill, LLM-judged assertions, `pass_rate` deltas, per the [agentskills.io output-quality guide](https://agentskills.io/skill-creation/evaluating-skills) — is **Tier B** and a separate future RFC. Tier A is the cheaper, higher-signal half (the sandbox-eval finding: activation is where accuracy varies; selection is near-perfect once a skill fires) and it tests the load-bearing `description:` directly.

### Code preconditions (co-land with focused tests)

- `lint-skill-spec.py` today **errors** if `evals/` exists without `evals/evals.json`. It must instead accept a skill that ships **only** `evals/eval_queries.json`, and validate that file's schema (array of `{query: non-empty str, should_trigger: bool}`).
- A new check validates that every `[pack.evals].skills` entry names a real skill directory that ships `evals/eval_queries.json`.
- The `converters` carry-over gate in `build-check.yml` migrates to read `[pack.evals].skills` (consolidation; may land as a follow-on PR rather than blocking the harness).

### Rollout

First PR: the runner + lint preconditions + trigger evals for `core` and `converters` (+ their `[pack.evals]` blocks) + the `pack-evals.yml` workflow. Remaining packs backfill their `eval_queries.json` per-pack afterwards — coverage grows without re-touching the harness.

## Options considered

**Axis: where the activation/negative cases live and how they relate to the existing eval convention.** This axis is exhaustive because an activation case must be stored *somewhere* relative to the skill, and the only meaningful distinctions are (a) inside the existing quality file, (b) in the convention's own dedicated file, (c) outside the skill, or (d) not at all.

| Option | Where activation cases live | Prior art | Verdict |
| --- | --- | --- | --- |
| **A. Extend `evals/evals.json`** with a `should_trigger` field | Inside the quality-eval file | None — contradicts the agentskills.io quality schema | Rejected: forks a published spec; the reason this RFC exists is to *not* do this |
| **B. ★ Dedicated `evals/eval_queries.json`** (the trigger-eval convention) | Separate skill-local file | [agentskills.io optimizing-descriptions](https://agentskills.io/skill-creation/optimizing-descriptions); Anthropic `skill-creator`; published skills | **Recommended**: the convention's own answer; skill-local; no schema contradiction |
| **C. Pack-level negative set** (a shared file outside any skill) | One file per pack | Generic test-suite layout | Rejected: introduces a concept outside the agent-skills convention; ownership drifts from the `description:` under test; exclusivity is already free under B |
| **D. Do nothing** | — | Status quo | Rejected below |

**Do-nothing (Option D) and its cost of delay.** Keep only structural gates. Cost: every description regression — a skill that stops triggering after a `description:` edit, or starts grabbing adjacent prompts — ships invisibly and is found only by an agent or user hitting it in the field. As the catalogue grows (13 packs, more per RFC cadence), the surface of un-measured triggering grows with it, and there is no signal to catch a cross-skill collision introduced by a new pack. The structural gates stay green while the product silently degrades — exactly the failure mode the charter's "AGENTS.md vs. reality drift" warning describes, one layer down.

**Secondary axis — harness mechanism** (runner, Decision 3): direct Anthropic API SDK (wrong layer — skills are a Claude Code feature, the SDK wouldn't load them), Daytona/remote sandboxes (heavier infra, sharper Principle-3 tension), or **local/CI `claude -p`** (the convention's own documented detector). The last is recommended and spike-confirmed.

## Risks & what would make this wrong

**Pre-mortem.**

- *Flaky CI erodes trust.* If the eval workflow hard-failed on noisy live-model runs, a red X would mean nothing and people would ignore it. *Mitigation:* report-only first; `trigger_rate` over 3 runs to average out sampling; promote to a gate only after a calibration baseline.
- *Cost creep.* 20 queries × 3 runs × N skills × scheduled cadence adds up. *Mitigation:* a tight per-run wall-clock timeout (early-exit-once-decided where the client supports it); schedule, don't run per-push; the `[pack.evals]` allowlist bounds coverage to skills that warrant it.
- *Convention drift.* agentskills.io could rename/relocate the trigger file. *Mitigation:* the runner reads the path from one place (`evals/eval_queries.json`, pinned in Decision 1); the format is a flat, stable two-field array.
- *`description:`-as-test-oracle is circular.* The eval queries are authored by the same person who wrote the description, risking a test that only re-states the description's keywords. *Mitigation:* the convention's near-miss discipline + (deferred) train/validation split; this is a known agentskills.io concern with a documented answer.

**Key assumptions (falsifiable).**

- Activation is mechanically detectable headless via a parseable `Skill` `tool_use` event. *(Spike-confirmed; see Evidence.)*
- A `trigger_rate` over 3 runs is a stable-enough signal to be worth reporting. *(The convention asserts this; first-cut data will confirm or refute it.)*
- The runner is catalogue-internal tooling, not a shipped primitive, so it doesn't need to clear the four-bar charter test. *(If review disagrees, this becomes a charter question.)*

**Drawbacks.** It adds a maintained surface (per-skill query files someone must keep honest), a live-model dependency in CI (a secret to manage, results that vary run-to-run), and a real authoring cost — good near-miss negatives are hard to write. The payoff is the only empirical signal we'd have that skills trigger as designed; the cost is real and is the reason for the report-only, opt-in, allowlist-bounded posture.

## Evidence & prior art

- **Spike / de-risk.** The assumption that, if false, sinks the proposal: that activation is detectable headless. **Confirmed** — `claude` 2.1.181 is on PATH and exposes `--print`, `--output-format json`, and `--allowed-tools`; the agentskills.io guide ships the exact detector the runner uses (`claude -p "$query" --output-format json | jq 'any(.messages[].content[]; .type=="tool_use" and .name=="Skill" and .input.skill==$skill)'`) and the [sandboxed skill-activation eval](https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals) demonstrates parsing `Skill()` events at scale. (The spike also established that `--max-turns` is *not* a CLI flag on this version — hence the timeout-based bound in Decision 3, not a turn cap.)

- **Repo precedent.** `lint-skill-spec.py` already adopts and validates `evals/evals.json` (`BLESSED_SUBDIRS` includes `evals`); 14 skills across 4 packs (`atlassian`, `contracts`, `converters`, `figma`) ship it. RFC-0031 / ADR-0021 established `pack.toml` as the rich source of truth that `[pack.evals]` extends. ADR-0017 (Bandit/pip-audit/Semgrep) is precedent that **catalogue-internal CI tooling belongs in this repo** (its Principle-3 fit); note it is itself a *blocking* PR gate, so it is *not* precedent for the report-only posture — that comes from ADR-0014 ("rigor scales with risk"), which supports an opt-in, report-only tier over a hard gate. No live-model CI exists today (only Artifactory/PyPI release secrets), so the scheduled workflow is genuinely net-new and rightly isolated.

- **External prior art.**
  - [agentskills.io — Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions): the authoritative trigger-eval convention — `{query, should_trigger}`, ~20 queries (8–10 each way), near-miss negatives, 3 runs, `trigger_rate` with a 0.5 threshold, the `claude -p` detector, and a train/validation split to avoid overfitting.
  - [agentskills.io — Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills): the *separate* output-quality convention (`evals/evals.json`), confirming it carries no activation dimension — which is why Tier A needs its own file.
  - [Anthropic — Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents): deterministic graders before model-based; positive + negative cases; multiple trials; "grade the output, not the path."
  - [OpenAI — Testing agent skills systematically with evals](https://developers.openai.com/blog/eval-skills): the prompt + should-trigger-boolean pattern and negative controls for false positives.

## Open questions

Both questions raised during drafting were **resolved at acceptance to their recommended defaults** (eugenelim, 2026-06-21); they carry into the Tier-A spec as decided constraints, not open items:

1. **When does report-only become a hard-fail gate?** *Resolved:* report-only ships first; the gate turns on only after one calibration cycle establishes a per-skill baseline trigger rate, and it gates on **regression-from-baseline**, not an absolute threshold. The first cut does not hard-fail.
2. **Train/validation split — now or later?** *Resolved:* **deferred.** The split serves description *optimization*, not regression measurement; the first cut measures, and a later description-tuning workflow (not this RFC) can introduce the split. This stays a Non-goal here.

## Follow-on artifacts

When accepted:

- **ADR** recording: trigger evals adopt the agentskills.io `eval_queries.json` convention; `pack.toml` `[pack.evals]` is the coverage source of truth; the runner is catalogue-internal tooling (not a shipped primitive).
- **Spec** `docs/specs/pack-activation-evals/` for the Tier-A runner, lint preconditions, the `core`/`converters` first cut, and `pack-evals.yml`.
- **Future RFC** for Tier B (output-quality grading via `evals/evals.json`, with/without-skill comparison, LLM-judge).

## Errata

> Corrections to this Accepted RFC discovered during implementation. The RFC
> stays frozen; errata record where the decision-as-written diverges from
> ground truth, **pending Approver sign-off** (the RFC's original approver).

### E1 — Detector uses `--output-format stream-json --verbose`, not `--output-format json` (2026-06-21) · ⏳ awaiting Approver sign-off

**Decision 3 and the Evidence section specify `claude -p "<query>"
--output-format json --allowed-tools Skill` and parsing "the result for a
`Skill` `tool_use` event" (the spike's `jq 'any(.messages[].content[]; …)'`).**
Verified empirically on `claude` **2.1.185** (the implementing machine; the
spike ran 2.1.181): `--output-format json` returns a **result-only** envelope —
`{type, subtype, result, usage, permission_denials, …}` with **no `messages`
array and no `tool_use` events**. The activation event the runner must observe
is therefore **not present** in the `json` envelope; the spike's `jq` filter
matched a transcript shape that `--output-format json` does not emit.

**Correction:** the detector uses **`--output-format stream-json --verbose`**.
The activation appears as an `assistant` event whose `message.content[]` holds a
`{"type": "tool_use", "name": "Skill", "input": {"skill": "<name>"}}` block
(`.input.skill` as specified); the stream still terminates with a
`{"type": "result", …, "result": "<text>"}` event, so capturing the parsed
`.result` (the workspace's per-run output) is unchanged. The `--allowed-tools
Skill` observe-don't-execute trust boundary, the wall-clock-timeout bound, the
argv-list invocation, and Tier-A scope are all **unaffected**. The spike's
conclusion — *activation is detectable headless* — **holds**; only the
output-format flag and the parse target are corrected.
