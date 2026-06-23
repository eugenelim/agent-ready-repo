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

> Corrections and scope adjustments to this Accepted RFC discovered during
> implementation. The RFC stays frozen; errata record where the
> decision-as-written diverges from ground truth or where a boundary was drawn
> narrower than intended, **pending Approver sign-off** (the RFC's original
> approver).

### E1 — Detector uses `--output-format stream-json --verbose`, not `--output-format json` (2026-06-21) · ✅ signed off: eugenelim (RFC-0037 Approver), 2026-06-21

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

### E2 — Admit a second, in-harness / agent-dispatch detector mode (Kiro IDE + interactive Claude Code) (2026-06-22) · ✅ signed off: eugenelim (RFC-0037 Approver), 2026-06-22

**Decision 4 (Tier A) and the spec's `§ Never do` draw the boundary
"headless-only — no non-headless / in-editor / GUI execution mode; GUI-only
IDEs (Kiro IDE, Cursor IDE) are out of scope."** That boundary was set to keep
the runner catalogue-internal (Charter Principle 3) and to lean on the one
harness with a parseable activation event (`claude -p` stream-json). In
practice it draws the line **narrower than intended**: it means a maintainer
working in **Kiro IDE** — which has no `claude -p` CLI to shell out to — cannot
run activation evals at all, and there is no way to run them from **within an
interactive Claude Code session** without the headless CLI. Reach to the
agent harnesses people actually author packs in was an unstated goal the
boundary silently foreclosed.

**Adjustment:** a **second detector mode** is admitted **behind the existing
detector seam (AC18)** — an **in-harness / agent-dispatch detector**: the host
harness's own agent (Claude Code's `Agent`/subagent tool; Kiro IDE's
agent-spawn) runs each `eval_queries.json` query in a fresh sub-context
(supplied the candidate skills' descriptions) and **reports** which skill it
would activate — a description-match judgement, **not** a pack-isolated router
observation (see the Activation-signal paragraph below). The shared abstraction —
*"the host harness's agent is the detector"* — is what makes the same mode
serve both Claude Code and Kiro IDE. The seam was built additive (AC18) for
exactly this; headless is no longer the *only* mode, but it **remains the
reference mode**.

**Activation signal (recommended default; ratify on sign-off).** The in-harness
mode records **reported** activation — the dispatched agent names the skill it
activated — accepting **lower fidelity** than headless's **observed** `Skill`
`tool_use` event. Headless `claude -p --output-format stream-json --verbose`
stays the **high-fidelity calibration reference**; the in-harness mode is the
**portable** path that extends reach to Kiro IDE + interactive use. Both modes
write the same `eval_queries.json` / `summary.json` / eval-workspace contract,
and the summary must label which mode (and thus which fidelity) produced each
result. *Truly-observed* in-harness activation (reading the host agent's real
`Skill` invocation) is left open as a future refinement — it is not reliably
exposed by either harness's subagent surface today.

**New trust boundary to carry into the spec.** The headless mode's
`--allowed-tools Skill` observe-don't-execute sandbox does **not** transfer:
dispatching author-influenced query strings into the **host** agent (which holds
the full project's tools) is a different, larger risk surface. The in-harness
mode must constrain the dispatched sub-context so it cannot execute skill bodies
or project tools against those strings — the spec's security pass must specify
this control as an acceptance criterion, not inherit the headless one.

**Unchanged:** Tier-A scope, the `[pack.evals]` coverage model, the
`eval_queries.json` schema, the report-only posture, and the headless mode's
`--allowed-tools Skill` boundary.

**Follow-on artifacts (after sign-off):** narrow the spec's `§ Never do`
("headless is the reference; an in-harness agent-dispatch mode is admitted
behind the seam") and add Kiro IDE to scope; extend AC18 and add a new AC for
the in-harness detector, its fidelity caveat, and its trust boundary; a
companion correction note on **ADR-0028**; a new plan task; the runner gains the
second `Detector`; the authoring docs gain the in-harness run path.

### E3 — Admit a *lightweight* in-harness behavior/output check (a bounded slice of Tier B) (2026-06-22) · ✅ signed off: eugenelim (RFC-0037 Approver), 2026-06-22

**Decision 4 scoped this RFC to Tier A (activation/selection) only and deferred
all of Tier B (output quality) to a separate future RFC.** That left a gap a
maintainer hits in practice: once a skill activates, *does it do the job* — run
the right script, produce the expected artifact, avoid the documented
anti-action? The **full** Tier-B apparatus (LLM-judge grading, `benchmark.json`
pass-rate deltas, with/without-skill comparison, the train/validation split)
stays out of scope and remains the future RFC. But a **lightweight** check —
run the skill and validate its behavior + outputs against deterministic
post-conditions — is cheap, high-value, and belongs in this RFC's in-harness
mode (E2).

**Adjustment:** the in-harness mode gains a second sub-mode — a **behavior/output
check** that, for each eval in a skill's existing `evals/evals.json`, has the
host agent **run the skill** on the eval's `prompt` in an **isolated, ephemeral
workspace** and grades the result by:
- **deterministic post-conditions (the backbone):** the eval carries an optional
  `expect` block (`{produces, output_contains, output_excludes}`); the runner
  **re-derives** these from the per-eval working dir — `expect.produces` files
  exist, `output_contains`/`output_excludes` hold against the captured output —
  mechanical, reliable, never trusting operator-supplied result booleans;
- **the host agent's per-`assertion` pass/fail self-attestation** for the
  semantic assertions a string check can't cover ("did NOT hand-write the
  .docx"). No separate judge model.

It reuses the existing `evals/evals.json` source (no new file; the file the RFC
already says authors write now becomes *lightly runnable*). It produces a
pass/fail per eval + counts, written to the same eval-workspace and labelled a
distinct tier (e.g. `mode: in-harness`, `tier: B-lite`) so it is never confused
with the Tier-A activation number **or** with the full Tier-B grade.

**Fidelity.** Unlike Tier-A in-harness (a *reported* description-match — the
router can't be isolated), the behavior check **runs the skill for real and
inspects real artifacts**, so the deterministic post-conditions are *observed*;
only the semantic-`assertion` verdicts are *self-attested* (lightweight, not an
independent judge). Honest label: observed outputs + attested assertions.

**Security — this REVERSES E2's containment control.** E2 forbade the dispatched
sub-context from executing skill bodies (the `--allowed-tools Skill` sandbox
"does not transfer"); the behavior check **must** execute the skill body, which
is the whole point. **The spec-stage `security-reviewer` pass (2026-06-22)
established that a host agent running the skill keeps its full tool surface,
cwd, inherited environment, and network — so a temp working directory is *not* a
mechanical sandbox** (the same cwd-isn't-confinement truth as Phase-2 activation).
The control is therefore honestly a **procedure + scope-gate**, not a sandbox
guarantee: (1) a **scope gate** — only author-opted skills whose run is
**non-destructive and needs no network/credentials** are eligible for B-lite (a
destructive/egressing body waits for a real OS-level sandbox); (2) a **documented
procedure** — run in an OS-temp working dir (`tempfile.mkdtemp`), confine writes
to it, teardown in `finally` under a max-runtime; (3) **enforceable slices** —
fixture-copy path-confinement (`followlinks=False`), and a **scrubbed,
network-denied environment whenever the runner itself spawns a skill script**.
The follow-on spec specifies these as acceptance criteria; a future real sandbox
(container / separate user / netns) would lift the scope gate.

**Pre-test setup & backend skills (repeatability).** The behavior check **never
installs deps itself** — it leans on each skill's existing Tier-1
`## Prerequisites` + detection contract (detect-or-guide; the adopter installs
once via the skill's *own* documented command, then runs are repeatable;
`node_modules/` is gitignored so in-place installs don't pollute git). Skills
that integrate a **logged-in backend** (credentialed skills on the `auth: cli` /
credential-broker contract) are **out of B-lite scope** by the same scope gate —
they need live auth + a real backend and may mutate remote state, so they get
**activation-only** coverage and the harness never injects real credentials;
their behavior testing (recorded cassettes / a disposable test backend) is
future-Tier-B work (`docs/backlog.md`).

**Unchanged / still out of scope:** Tier-A activation (headless + in-harness),
the `[pack.evals]` model, the report-only posture, and — explicitly — the
**full** Tier-B grading (LLM-judge, benchmark deltas, with/without, train/val),
which remains the separate future RFC. E3 is the *lightweight* slice only.

**Follow-on artifacts (after sign-off):** spec — a new AC for the lightweight
behavior/output check (run-the-skill + deterministic post-conditions + attested
assertions, `tier: B-lite` label) and a new AC for the **sandbox containment
control** (ephemeral workspace, fixtures-only, no secret/network/real-repo
access, cleanup); ADR-0028 companion note; plan tasks (a sandbox helper +
`grade_behavior` model-free grader + the driver-procedure extension + live
validation); the runner + the authoring guide gain the behavior-check path; a
spec-stage `security-reviewer` pass on the sandbox.

### E4 — Admit a report-only LLM-judge for the quality layer, behind a multi-adapter judge seam (2026-06-22) · ✅ signed off: eugenelim (RFC-0037 Approver), 2026-06-22

**E3's deterministic B-lite check covers the *validity/shape* layer (artifacts
exist, substrings, validators) but not output *quality* — "is the contract
well-designed? is this the right diagram abstraction? is the verdict correct?"**
That layer has no ground truth, so it needs a model. E4 admits a **report-only
LLM-judge** for it, behind a **swappable judge backend seam** parallel to the
detector seam.

**Adjustment.** `run-pack-evals.py --mode judge --judge-adapter {claude-code,codex}`
grades a skill's produced artifact against the eval's rubric. Key shapes:
- **The lens is the rubric we already author** — the eval's `expected_output` +
  `assertions`. The judge prompt inlines the artifact + the rubric and requests a
  **strict-JSON verdict** (`{verdict: PASS|FAIL, assertions:[…], rationale}`),
  parsed deterministically; an unparseable verdict **fails closed** (ERROR, never
  a silent PASS). The repo's own review skills (`architect-review`, the reviewer
  subagents) are natural lenses.
- **Config-driven, multi-adapter, model-selectable, cross-model preferred.**
  Backends are **declarative command templates**, not hardcoded classes:
  `[judge.<name>]` = `{command (with a `{prompt}` argv token), model-flag,
  extract (`json:<field>`|`stdout`)}`. Built-ins ship `claude-code` (same model,
  `claude -p` → `.result`) and `codex` (independent model/IDE, `codex exec -s
  read-only`); an **adopter adds their own — e.g. a `kiro-cli` headless judge —
  by a config entry, no code change** (`--judge-config <toml>`), and picks the
  **model** with `--model` (passed via the backend's model-flag). A **cross-model**
  judge (codex/kiro judging a claude-run skill) is preferred — it can't
  self-grade. `{prompt}` substitutes as a discrete argv element (no shell), so a
  config entry can't inject. Both built-ins validated live (each returned a
  structured PASS on a good design doc).
- **Containment.** The judge is **judgment-only**: claude is granted no tools
  (the artifact is inlined); codex runs `-s read-only` so any model-generated
  command can't mutate. It reads an operator-supplied artifact path + calls a
  model — report-only, no gating.
- **Honest limits.** A judge **wobbles** (mitigate: structured per-assertion
  verdict, multiple runs, report-only) and needs periodic **human calibration**
  (does the judge agree with a human on a sample — the agentskills.io
  `feedback.json` loop). It is a quality *signal*, not a gate.

**Still the separate future RFC (full Tier-B):** `benchmark.json` pass-rate
**deltas**, the **with/without-skill** comparison, the **train/validation split**,
and the formal **human-feedback** loop. E4 ships only the judge *mechanism* +
the multi-adapter seam.

**Follow-on artifacts:** spec — a new AC for the judge mode (lens=rubric,
multi-adapter, JSON verdict, fail-closed, report-only) + the judge containment
note; ADR-0028 companion note; the runner's judge seam (`get_judge`,
`build_judge_prompt`, `parse_judge_verdict`, `grade_judge`) + tests; backlog —
narrow the full-Tier-B entry to deltas/with-without/train-val/human-feedback.
