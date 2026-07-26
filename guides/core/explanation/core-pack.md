# The core pack as a system

The other packs in this catalogue are accessories — workflows, doc shapes, credentialed primitives. `core` is the pack you'd lose sleep about losing. It ships the *discipline* that turns "the agent wrote some code" into "the agent shipped code that survived a cold adversarial read." This page explains the parts, how they fit together, and why the result is more productive than vibe-coding or the closest competing approaches (GitHub's Spec Kit and Kiro IDE's spec-driven mode).

## Why loop engineering

The leverage in agent coding has moved off the prompt. A single sharp prompt buys you one good turn; the work that actually ships features lives in the **loop** around it — the thing that plans, makes the change, verifies it, reviews it, and decides what comes next. You stop hand-driving every turn and start designing the loop that drives them.

```text
  design the loop, then let it run:

        ┌────────────────────────── fix ◄─────────────────────┐
        │                                                      │
        ▼                                                      │
      PLAN ───► EXECUTE ───► GATES ───► REVIEW ───► DECIDE ────┘──► ship
      surface   smallest     lint       fresh eyes,  fix or
      assump-   coherent     types      a cold read  finish
      tions     change       tests      of the diff
        │
        └──► spec · plan · state.json · captured learnings
             (on disk — the loop's memory survives the next run)
```

A loop running on its own is also a loop making mistakes on its own, at machine speed — so it has to check its own work harder than you would by hand. Three forces make that non-negotiable, and `core` answers each:

- **The model grades its own homework too kindly.** The agent that just wrote the code is the worst judge of whether it's right. `core` splits the maker from the checker: `adversarial-reviewer` reads the diff cold in a separate context, with no memory of why the code looks the way it does and no sunk cost to defend.
- **The model forgets everything between runs.** Nothing in the agent's head carries to the next session, so the memory lives on disk — the spec, the plan, `state.json`, `AGENTS.md`, `CONVENTIONS.md`, and the learnings captured at the end of every loop. The next run reads the repo, not a transcript.
- **Your attention is the bottleneck, not the tool.** You can spawn more agents than you can meaningfully review, and the gap between what ships and what you actually understand widens every time you wave a change through. `core` keeps you in the judgment seat on purpose: it surfaces assumptions and **stops** before building on them, gates on checks you can trust, and refuses to self-certify past a red gate or a repeated finding.

A loop will happily make you faster on work you understand — or let you skip understanding it at all. The loop can't tell those apart. You can. `core` is built for the first kind of engineer: the one who designs the loop and stays the engineer, not just the person who presses go.

## The parts

The core pack ships six tightly-coupled artifacts plus the documents they all read:

- **`AGENTS.md`** — the project's agent context, loaded first by every skill, every subagent, every reviewer. It carries the non-negotiables ("touch only what you're asked to touch"), the source-of-truth table, the check-before-acting rules. If a subagent skips it, the review is wrong.
- **`docs/CONVENTIONS.md`** — the *why* behind `AGENTS.md`. The verification-mode taxonomy (TDD / goal-based / visual-manual), the loop-iteration cap, the model-selection table, the rationale for every rule. AGENTS.md cites it for anything that needs a paragraph.
- **The `new-spec` skill** — drafts `docs/specs/<feature>/spec.md` + `plan.md`. Mandates assumption-surfacing **before** any spec body is written, mandates a Boundaries section with at least one structural `Never do`, mandates per-task `Tests:` before `Approach:`. The spec is the contract; the plan is the strategy.
- **The `work-loop` skill** — the plan → execute → gates → review → fix loop. Tracks state in `state.json` (gitignored, session-scratch), enforces an iteration cap, detects stasis (same findings twice = stop and surface), and gates EXECUTE on plan-approval after a pre-EXECUTE adversarial review.
- **The reviewer subagents** —
  - **`adversarial-reviewer`** (Opus): reads spec/plan or diff cold, against `AGENTS.md` + `CONVENTIONS.md` + the spec. Returns severity-labeled findings (Blockers / Concerns / Nits). Cannot be skipped.
  - **`security-reviewer`** (Opus): OWASP + STRIDE lens. Conditional — runs when the diff crosses a security boundary.
  - **`quality-engineer`** (Opus): testability, observability, reliability, maintainability. Conditional. Different lens from adversarial; not a duplicate.
  - **`implementer`** (Sonnet): single-task executor for supervisor mode. Not a reviewer.

The reviewers are diff-source-agnostic — the work loop points them at your own working tree, but you can point them at any diff, including a teammate's branch or open PR. See [Review a branch or PR you didn't write](../how-to/review-someone-elses-pr.md).
- **The `session-start.py` + `pre-pr.py` hooks** — wire the loop into the editor lifecycle. `session-start.py` reads the install-marker and nudges into `adapt-to-project` on first session.

Plus a sibling skill that runs alongside the six: **`bug-fix`** ships in `core` too and runs a parallel discipline (reproduce → red test → root vs. symptom → minimum fix → regression test stays) without entering the spec / loop pipeline. It composes with `work-loop` when the fix grows past one file. See [how to fix a bug](../how-to/bug-fix.md).

And a depth skill the loop reaches for by surface: **`frontend-engineering`** is loaded inline by `work-loop` whenever a task's primary output is HTML, CSS, or JS. It carries the design pre-flight (a named aesthetic reference, a seed token block, the six-state matrix), the codified craft rules that govern EXECUTE, and the GATES verification commands (html-validate, pa11y/axe, stylelint) — and it upgrades the design-intent pass from a recommendation to mandatory for that surface. It has no user-prompt activation surface of its own; the loop pulls it in, the way it pulls in `security-checklists` and `operational-safety` for the reviewers.

## How they tie together

A feature lifecycle, end to end, with the parts named:

1. **User asks for X.** "Add webhook retries with exponential backoff."
2. **`new-spec`** runs. The agent scaffolds `docs/specs/webhook-retries/` and **stops** to surface assumptions — technical, product, process — before filling in any spec body. The user signs off (or revises). Bodies fill in: Objective, Boundaries (including a structural `Never do`), Testing Strategy with a verification mode per user-visible outcome, Acceptance Criteria. The plan follows with tasks, each with `Tests:` before `Approach:` and an explicit `Depends on:`.
3. **`adversarial-reviewer`** reads the spec + plan in spec-mode. Findings come back; the spec hardens. Two passes is normal; three means structural problem and the agent surfaces.
4. **`work-loop`** initializes `state.json` via its bundled tool, then gates EXECUTE on `plan_review_status = approved`.
5. **EXECUTE.** The agent implements task by task. For TDD tasks: red, green, refactor. For goal-based: code, then run the one-liner from `Done when:`. The Boundaries section + the PLAN-step's declined-pattern register keep new abstractions from sneaking in.
6. **GATES.** Lint, typecheck, tests. Mechanical termination. Don't edit the gate to make it pass.
7. **REVIEW.** `adversarial-reviewer` reads the diff cold against `AGENTS.md` + `CONVENTIONS.md` + `spec.md`. Findings come back; `loop-cohort review record` fingerprints them; the loop iterates.
8. **Specialist reviewers** (if warranted). `security-reviewer` if the diff touched auth/secrets/I-O; `quality-engineer` for the maintenance lens.
9. **Stasis detection.** If the next iteration's findings fingerprint the same as the previous round's, the loop stops and surfaces. No silent third pass.
10. **Capture learnings.** A loop that finished without writing *something* to a skill, ADR, or pattern note wasted what it learned. The work-loop names where each kind of learning belongs.

The pieces are tightly coupled by design. `adversarial-reviewer` loads `AGENTS.md` first because skipping it makes the review wrong. `new-spec` writes Boundaries because the reviewer measures plans against Boundaries before falling back to the declined-pattern register. The work-loop's prose gates EXECUTE on `plan_review_status = approved`, and that field is set by the reviewer-pass step rather than by the implementing agent — so the discipline holds when the loop is followed and only when it is.

## Why this beats vibe-coding

Vibe-coding is the null alternative: the agent reads the prompt, writes code, declares done. It works for one-line edits and falls over everywhere else. The failure modes are well-known:

| Vibe-coding failure | What core pack does instead |
| --- | --- |
| Agent declares victory when it *feels* done. | Mechanical gates (lint, typecheck, tests) plus a separate-process adversarial reviewer. "Feel" is not a termination criterion. |
| Scope creeps mid-implementation — new abstraction here, defensive wrapper there. | Spec Boundaries + the PLAN-step's declined-pattern register. The reviewer flags any addition not named in either as drift. |
| Edge cases live outside the prompt. | Spec Objective is precise enough to derive tests from; Testing Strategy pairs each user-visible outcome with a verification mode. |
| Agent retries the same broken approach. | Fingerprint-based stasis detection. Same findings twice = stop, surface to a human. |
| Convention drift across PRs. | `AGENTS.md` + `CONVENTIONS.md` loaded first by every subagent. Repo rules can't be forgotten. |
| No second opinion. | Adversarial reviewer reads the diff cold in a separate context, no memory of the implementation rationale, can't be talked out of findings. |

The cost is the overhead of plan-before-code, of surfacing assumptions before bodies fill in, of an extra reviewer pass. The benefit is fewer broken PRs, shorter review cycles, and code that survives next quarter's refactor. For non-trivial work the math is decisive; for one-line edits, skip the loop.

## How it differs from Spec Kit and Kiro IDE

Two well-known spec-driven workflows exist; the core pack overlaps with both but goes further in different directions.

### vs. GitHub's Spec Kit

[Spec Kit](https://github.com/github/spec-kit) ships spec templates (`constitution.md`, `spec.md`, `plan.md`, `tasks.md`) plus slash commands that drive a `/specify` → `/plan` → `/tasks` → `/implement` flow (and additional commands like `/clarify` and `/analyze` for hardening intermediate artifacts). It's a strong workflow scaffold and the closest thing to a peer; the comparison below holds as of the catalogue's last sync with Spec Kit's README — re-check the source if you're choosing today.

| Capability | Spec Kit | Core pack |
| --- | --- | --- |
| Spec template with sections | ✓ | ✓ (plus mandatory assumption-surfacing before bodies, structural `Never do` enforced) |
| User-driven flow with explicit commands | ✓ (slash commands) | ✓ (skills auto-invoked by the agent; not literal slash commands today) |
| Adversarial reviewer reading the diff cold | — | ✓ (`adversarial-reviewer`, separate-process, separate model context) |
| State-machine discipline with iteration cap and stasis detection | — | ✓ (`state.json` + `loop-cohort` tool) |
| Specialist review lenses (security, quality) | — | ✓ |
| Supervisor-mode parallelism for independent tasks | — | ✓ |
| Cross-harness reach | partial (multiple agent harnesses supported) | ✓ (four adapters: Claude Code, Codex, Copilot, Kiro — plus broader IDE coverage via APM's `HookIntegrator`) |

Spec Kit's spec-driven loop terminates at `/implement` — there's no state-machine loop around it that re-fires until an adversarial reviewer returns clean. The core pack treats `/implement` as step 5 of 10. The extra five steps — gates, adversarial review, fingerprint stasis, specialist reviewers, learning capture — are the ones that catch the failures spec-shape alone can't.

### vs. Kiro IDE's spec-driven mode

[Kiro IDE](https://kiro.dev/) generates a `requirements.md`, `design.md`, and `tasks.md` from the user prompt in a planning panel, then iterates by re-prompting in "do" mode.

| Capability | Kiro spec-driven | Core pack |
| --- | --- | --- |
| Spec generated from prompt | ✓ | ✓ (but assumptions are surfaced *before* spec bodies, then user signs off) |
| Test design before code | partial | ✓ mandated (Testing Strategy in spec; `Tests:` per plan task) |
| Adversarial review of the diff against the spec | — | ✓ |
| Iteration cap and stasis detection | — | ✓ |
| Works outside Kiro | — (IDE-coupled) | ✓ (every supported harness) |
| Boundaries-driven scope control | — | ✓ (structural `Never do` + declined-pattern register) |
| Hook into editor lifecycle events | ✓ (native to Kiro) | designed in [RFC-0005](../../../rfc/0005-user-scope-hook-support.md) as `kiro-ide-hook`; the primitive isn't declared in `adapter.toml` v0.5 yet |

Kiro's "do" mode is one-shot per task: if the generated code is wrong, the user re-prompts. The core pack's loop iterates *within* the task — failing gates send you back to FIX, reviewer findings send you back to FIX, fingerprint stasis sends you to a human. The user isn't the retry loop; the tool is.

Kiro is also IDE-coupled — the spec-driven mode only fires inside Kiro's planning panel. The core pack ships through the adapter contract today (the Claude Code, Codex, Copilot, and Kiro adapters) plus APM's `HookIntegrator` for IDEs that consume the APM compile target (Cursor, Gemini, and others); install it once and the same loop runs wherever the install route reaches.

## When the overhead isn't worth it

The loop has cost. It pays back on non-trivial work and is friction on:

- One-line edits, typo fixes, config tweaks.
- Throwaway exploration and spikes (the work-loop skill explicitly excludes these).
- Genuine one-off scripts that won't be maintained.

For everything else — features, multi-file bug fixes, refactors, migrations, schema changes — the math is decisive. The [`work-loop` skill](../../../../packs/core/.apm/skills/work-loop/SKILL.md) itself enumerates its scope of application; the discipline applies forward-looking, not retroactively.

## Where to read next

- [The pack catalogue](../../_shared/explanation/pack-catalogue.md) — why `core` is the load-bearing pack and how the other packs compose against it.
- [Install routes](../../_shared/explanation/install-routes.md) — the four ways to install `core` and the install→adapt chain that closes on first session.
- [`docs/CONVENTIONS.md` § How we do non-trivial work](../../../CONVENTIONS.md#how-we-do-non-trivial-work) — the contributor-side rationale, deeper than this page.
- [The token economy of the loop](token-economy.md) — what the loop wastes, what it spends on purpose, and why the cold reviewer is worth its cost.
- [The `work-loop` skill itself](../../../../packs/core/.apm/skills/work-loop/SKILL.md) — the authoritative procedure. Loaded by the agent when a non-trivial task starts.
