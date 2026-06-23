# ADR-0028: Pack-level activation evals adopt the agentskills.io trigger-eval convention; coverage in `pack.toml`; runner is catalogue-internal tooling

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-21
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0037 (the proposal this records), RFC-0031 / ADR-0021 (`pack.toml` as the rich source of truth), RFC-0036 (`converters`, first `evals/evals.json`), ADR-0017 (SAST CI gate — catalogue-internal tooling belongs in-repo), ADR-0014 (rigor scales with risk — report-only over a hard gate)

> **Correction (2026-06-21, ✅ signed off by eugenelim — RFC-0037 Approver; see RFC-0037 § Errata E1):**
> Decision 3 below records the detector as `claude -p "<query>" --output-format
> json --allowed-tools Skill`, parsing "the result for a `Skill` `tool_use`
> event". Verified empirically on `claude` 2.1.185, `--output-format json`
> returns a **result-only** envelope with **no `tool_use` events**; the runner
> uses **`--output-format stream-json --verbose`** to observe the activation
> event (`assistant` event → `message.content[]` → `Skill` `tool_use` →
> `.input.skill`). The `.result` capture, the `--allowed-tools Skill` trust
> boundary, the timeout bound, and Tier-A scope are unchanged.

> **Scope adjustment (2026-06-22, ✅ signed off by eugenelim — RFC-0037 Approver; see RFC-0037 § Errata E2):**
> The "headless-only / runner is catalogue-internal" decision below was drawn
> narrower than intended — it foreclosed running activation evals in **Kiro
> IDE** (no `claude -p` CLI) and in interactive Claude Code. E2 admits a second
> **in-harness / agent-dispatch** detector behind the seam: the host harness's
> agent runs each query in a fresh sub-context (with the candidate skills'
> descriptions) and **reports** activation. Headless stays the high-fidelity
> reference; in-harness is **reported, lower-fidelity** (a dispatched
> sub-context can't be skill-isolated, so it's a description-match judgement,
> not the real router event) and every result is labelled by mode. A **new
> containment control** applies (the dispatched context must not execute skill
> bodies / project tools against author strings — the `--allowed-tools Skill`
> sandbox doesn't transfer), and the driver stays catalogue-internal
> (repo-owned, not a projected primitive) so Principle 3 holds. Tier-A scope,
> the `[pack.evals]` model, the `eval_queries.json` schema, and the report-only
> posture are unchanged.

> **Scope adjustment (2026-06-22, ✅ signed off by eugenelim — RFC-0037 Approver; see RFC-0037 § Errata E3):**
> Decision 4's "Tier A only" is extended with a **lightweight** in-harness
> behavior/output check (a bounded slice of Tier B): for each eval in a skill's
> existing `evals/evals.json`, the host agent **runs the skill** on the
> `prompt` and grades by deterministic post-conditions (artifacts exist;
> expected/forbidden substrings) plus the agent's per-`assertion` self-
> attestation — no LLM-judge, no `benchmark.json` deltas, no with/without-skill
> baseline (those stay the separate future Tier-B RFC). Labelled `tier: B-lite`;
> the deterministic checks are **observed**, the assertion verdicts
> **self-attested**. **Security:** this **reverses E2's "no execution" control**
> — the skill body now runs, confined to an **ephemeral, fixtures-only sandbox**
> (no real-repo / secrets / network access, gitignored, torn down); a
> `security-reviewer` spec-stage pass signs off the sandbox before execution
> code ships.

> **Scope adjustment (2026-06-22, ✅ signed off by eugenelim — RFC-0037 Approver; see RFC-0037 § Errata E4):**
> Adds a **report-only LLM-judge** for the *quality* layer (which deterministic
> checks can't reach), behind a **config-driven, multi-adapter judge seam**: the
> lens is the eval's rubric (`expected_output` + `assertions`); backends are
> declarative command templates (built-in `claude-code` same-model + `codex`
> independent; adopters add their own — e.g. `kiro-cli` — and pick the model via
> config, no code). Judgment-only + report-only; an unparseable verdict fails
> closed. The **full** Tier-B grading (benchmark deltas, with/without-skill,
> train/validation, human-feedback loop) remains the separate future RFC.

## Context

Every gate the catalogue runs today is **structural**: `lint-skill-spec.py` and
`lint-agent-artifacts.py` check frontmatter shape, the projection/drift checks
verify packs build and project correctly, and the install integration tests
verify install mechanics. None of them verifies the one property the whole
skills mechanism depends on — that a skill is loaded only when its
`description:` matches the user's task. An under-specified description fails to
trigger when it should; an over-broad one triggers when it shouldn't. Neither
failure is visible to any current check; both are discoverable only by an agent
(or a user) hitting the gap in practice.

Behavioural assets already exist but test a different thing: 14 skills across 4
packs (`atlassian`, `contracts`, `converters`, `figma`) ship `evals/evals.json`,
which measures **output quality** once a skill is already running — not **whether
it runs**. No runner executes any of them; CI only asserts the files exist with
the right keys.

The catalogue has 13 packs whose value rests on skills triggering reliably, and
the surface of un-measured triggering grows with every new pack. RFC-0037 was
opened and **Accepted** (2026-06-21) to add a repeatable, empirical activation
measurement; both of its open questions were resolved to their recommended
defaults at acceptance. This ADR records the architectural decisions that
follow-on artifact list calls for, so they are durable independent of the RFC's
proposal narrative.

Constraints in play at the time of this decision:

- The `claude` CLI is the only thing that can actually load and activate a
  skill — the Anthropic API SDK operates at the wrong layer and would not load
  skills at all. `claude` 2.1.181 (on PATH) exposes `-p`/`--print`,
  `--output-format json`, and `--allowed-tools`; it has **no** `--max-turns`
  CLI flag, so a per-run bound must be a wall-clock timeout.
- No live-model CI workflow exists today — the only secrets in CI are
  release-time Artifactory/PyPI credentials — so any live-model job is genuinely
  net-new and must be isolated from the deterministic PR path.
- `pack.toml`'s schema (`docs/contracts/pack.schema.json`) sets no
  `additionalProperties: false` on the `pack` object, so a new `[pack.evals]`
  subsection is admissible without a schema migration.

## Decision

> We adopt the agentskills.io **trigger-eval convention** — the *methodology*
> from its [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
> page (a flat array of `{query, should_trigger}` cases, near-miss negatives, the
> `claude -p` detector, `trigger_rate` over runs, 0.5 threshold) — as the
> catalogue's per-skill activation-eval format, stored at `evals/eval_queries.json`;
> we make `pack.toml`'s `[pack.evals].skills` the single declarative source of
> truth for which skills a pack-level runner covers; and we build that runner
> (`tools/run-pack-evals.py`) plus its scheduled, report-only CI workflow as
> **catalogue-internal dev tooling — not a shipped pack primitive**.
>
> *Attribution precision:* the **convention/methodology** is agentskills.io's; the
> **`evals/eval_queries.json` path is the catalogue's instantiation** — agentskills.io
> illustrates the file only as a bare `eval_queries.json` and its script takes a
> generic `<queries.json>`, never mandating the `evals/` subdirectory. Placing it
> under our already-blessed `evals/` subdir (alongside the output-quality
> `evals/evals.json`) is our choice, not theirs.

Elaboration of the three decisions and their scope:

1. **Convention & file.** Each covered skill gains
   `evals/eval_queries.json` — a flat JSON array of
   `{ "query": "...", "should_trigger": true|false }`, with near-miss
   negatives (prompts that share keywords or concepts with the skill but need
   something else) as first-class. It is a **separate file** from
   `evals/evals.json`: the output-quality schema has no activation dimension,
   and adding `should_trigger` to it would fork a published spec. The file lives
   under the already-blessed `evals/` subdir so every eval artifact has one home.

2. **Coverage source of truth.** `pack.toml` gains
   `[pack.evals].skills = [...]`, an **explicit allowlist** (not auto-discovery)
   of the skills the pack-level runner covers. Some skills legitimately ship no
   trigger evals, and the list is a deliberate contract — the same reasoning that
   made the `converters` carry-over gate enumerate its skills by hand. This
   extends RFC-0031's "`pack.toml` as the rich superset source of truth". It is a
   **new** coverage list, not a replacement for the existing `converters`
   `evals/evals.json` carry-over gate, which tests a different contract.

3. **Runner & CI posture; Tier A only.** `tools/run-pack-evals.py` projects a
   pack in isolation, runs each covered skill's queries through the convention's
   own detector — `claude -p "<query>" --output-format json --allowed-tools
   Skill` — parses the result for a `Skill` `tool_use` event (recording
   activation **and** which skill fired, `.input.skill`), and grades a
   `trigger_rate` over N runs against the convention's 0.5 threshold. It uses
   only stdlib + `tomllib` + the `claude` CLI — **no new dependency**. It runs in
   a new `.github/workflows/pack-evals.yml` on **schedule + manual/label dispatch
   only**, **report-only** (never fails the build in the first cut);
   `make build-check` stays structural, deterministic, and fast. The runner is
   catalogue-internal tooling — it lives in `tools/`, is never projected into any
   pack, and clears no charter four-bar test because it is not a shipped
   primitive (Charter Principle 3), exactly like the linters and the SAST gate.
   It writes into a gitignored, **iteration-numbered eval-workspace** that adopts
   the agentskills.io evaluating-skills layout *now* — `iteration-<N>/` per pass,
   per-eval `outputs/` capturing the actual run output — and **reserves the
   grading slots** (`without_skill/`, `timing.json`, `grading.json`,
   `benchmark.json`) so a future grading RFC fills them without restructuring.
   Scope is **Tier A (activation/selection) only**; output-quality *grading*
   (Tier B) is a separate future RFC.

4. **Reference-harness proxy; headless-only.** Activation is measured on
   **claude-code as the reference harness**, and **only headlessly**. Every
   adapter projects skills as native `direct-directory` primitives with the
   `description:` projected **byte-identical**, so the variable a trigger-eval
   tests is constant across adapters and measuring the reference harness is a
   sound proxy for the description-quality regression any adapter would share.
   **GUI-only IDEs (Kiro IDE, Cursor IDE) are out of scope** — they expose no
   headless prompt surface, and an in-editor eval driver (e.g. a `userTriggered`
   `.kiro.hook`) was rejected as runtime infra, not catalogue dev tooling
   (Principle 3). The other headless CLIs (codex, copilot, cursor-agent, gemini)
   become **additive headless detectors later** behind a small `Detector` seam;
   the first cut ships the `claude-code` detector only.

## Consequences

**Positive:**

- The only empirical signal the catalogue has that skills trigger as designed —
  a number comparable across model versions and `description:` edits.
- Per-skill ownership stays inside the agent-skills convention: the eval lives
  next to the `description:` it tests.
- Near-miss negatives are first-class, catching over-broad descriptions; because
  the whole pack is projected, **intra-pack exclusivity comes for free** (a
  positive query doubles as a "this skill and no other in-pack" check).
- No new dependency, and no cost or flakiness on the PR critical path.

**Negative:**

- A maintained surface — per-skill query files someone must keep honest, and
  good near-miss negatives are genuinely hard to write.
- A live-model dependency in CI — a new `ANTHROPIC_API_KEY` repo secret to
  manage, and results that vary run-to-run.
- Report-only means **no enforcement** until a calibration baseline exists; a
  regression can ship between the eval landing and the gate turning on.

**Neutral / to revisit:**

- **Report-only → hard-fail gate** turns on only after one calibration cycle
  establishes a per-skill baseline, and gates on **regression-from-baseline**,
  not an absolute threshold (RFC-0037 Open Q1, resolved).
- **Train/validation split** of the eval sets is deferred — it serves
  description *optimization*, not regression *measurement* (RFC-0037 Open Q2,
  resolved).
- **Tier B — the entire [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills)
  page — is out of scope here** (a separate future RFC). We adopt that page's
  *workspace structure* now (`iteration-N/` + per-eval `outputs/`; see Decision 3)
  as a forward-compatible convention, but its **grading/execution machinery is
  what we do not build**: with-skill-vs-without-skill (or vs-previous-version)
  baseline runs, assertions, LLM-judge or script grading (`grading.json`), blind
  comparison, `benchmark.json` (`pass_rate`/`stddev`/`delta`/timing/tokens),
  pattern analysis, the human-review `feedback.json` step, and the SKILL.md
  improvement loop. (Note: 14 skills across 4 packs already *author*
  `evals/evals.json` by hand, but nothing executes them — that execution is
  exactly the deferred Tier B.) **Also excluded from the triggering page itself:**
  the train/validation split and the description-*optimization* loop (we measure
  activation for regression, we don't auto-tune `description:`) — RFC-0037 Open
  Q2 / Non-goals.
- The `converters` `evals/evals.json` carry-over gate **may** later consolidate
  onto `[pack.evals].skills`; out of scope here and may land as a follow-on.

## Alternatives considered

- **Extend `evals/evals.json` with a `should_trigger` field.** Rejected: it
  forks the published agentskills.io quality schema — the very thing this
  decision exists to avoid.
- **A pack-level shared negative set** (one file outside any skill). Rejected:
  it introduces a concept outside the agent-skills convention and drifts
  ownership away from the `description:` under test; intra-pack exclusivity is
  already free under the chosen file-per-skill model.
- **Do nothing** (keep only structural gates). Rejected: every description
  regression ships invisibly and is found only in the field, and the un-measured
  surface grows with the catalogue — the charter's "AGENTS.md vs. reality drift"
  failure mode, one layer down.
- **Harness mechanism — direct Anthropic API SDK.** Rejected: wrong layer; the
  SDK would not load Claude Code skills, so it cannot observe activation.
- **Harness mechanism — Daytona / remote sandboxes.** Rejected: heavier infra
  and a sharper Charter Principle-3 tension than the convention's own
  documented local/CI `claude -p` detector.

## References

- RFC-0037 — Pack-level activation evals (Accepted 2026-06-21).
- [agentskills.io — Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) (the trigger-eval convention).
- [agentskills.io — Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills) (the separate Tier-B quality convention).
- [Anthropic — Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
