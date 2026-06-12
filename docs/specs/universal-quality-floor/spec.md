# Spec: universal-quality-floor

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Contract:** none
- **Shape:** mixed <!-- doctrine/behavior change to shipped skill + agent prose; LLD intentionally thin -->
- **Mode:** full (risk triggers fired: governance surface — CONVENTIONS + AGENTS.local.md; dependent tasks — T3→T2, T5/T6 fan-in)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

When the bundle is installed on a brownfield repo gated by a strict external
static-analysis platform (e.g. a SonarQube "platinum" profile and a CI-only
coverage threshold), agent-authored code currently clears the *local* gate trio
(lint / typecheck / tests) yet fails the *real* merge bar in CI — on code-smell
patterns (complexity, nesting, duplication) and on new-code coverage. We cannot
control or detect what lives in those repos, and client-specific standards are
the adopter's to set in their own files. So we raise the bundle's **default
quality floor by doctrine** — sharper review judgment and a leaner diff — so
output tends to clear a strict gate *regardless of tech stack*, without bundling
any linter, shipping any threshold, or detecting the repo's shape.

Concretely, for the agent doing the work: (a) the `quality-engineer` reviewer
gains a small set of **universal, stack-agnostic code-smell findings** and a
mutation-testing-mindset test headline that together approximate the
maintainability/reliability rating a strict gate enforces; (b) the `work-loop`
gains a **simplify pass** in EXECUTE/REVIEW that shrinks the diff before review,
so there is less code to smell and less to review; and (c) light mode stops
silently dropping the one lens that approximates the gate **when the adopter has
declared** such a gate exists. Mode *mechanics* begin migrating out of
`CONVENTIONS.md` into the `work-loop` skill as their opinionated owner.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit `packs/core/.apm/` sources (`agents/quality-engineer.md`,
  `skills/work-loop/SKILL.md`) and re-project with `make build-self`; never edit
  projected paths (`.claude/...`) directly.
- Keep the four universal-smell bullets **stack-agnostic and threshold-free** —
  describe the smell shape, never a language or a number.
- **Bump the core pack version** (this is a non-cosmetic pack change) and add a
  `docs/product/changelog.md` `[Unreleased]` entry in the same PR for the
  user-visible doctrine change.

### Ask first

- Any change to the **byte-identical risk-trigger block** (synced verbatim
  across `AGENTS.md`, `packs/core/seeds/AGENTS.md`, `docs/CONVENTIONS.md`, and
  the work-loop `SKILL.md`; grep-equality is an AC of the `work-loop-light-mode`
  spec) — out of scope here; confirm before touching.
- Broadening the `CONVENTIONS.md` thinning beyond the Light/full-mode *mechanics
  summary* — full CONVENTIONS retirement is deferred to its own RFC.
- Making the simplify pass a **blocking gate** rather than a doctrine step.

### Never do

- Bundle a linter, ship a per-stack tool table, or ship a numeric
  coverage/complexity threshold (structural: **no new dependency, no new module
  boundary**).
- Make the `work-loop` *depend* on the Claude-Code-only `/simplify` command such
  that Cursor / Gemini / Copilot adapters break — the behavior is harness-agnostic
  doctrine; the native command is an optional accelerant.
- **Detect** the repo's quality gate (no scanning for `sonar-project.properties`
  or coverage configs); the light-mode carve-out is **adopter-declared policy
  only**.
- Edit the risk-trigger block's wording (breaks the grep-equality AC across four
  files).

## Testing Strategy

Doctrine-only change — no runtime logic — so verification is **goal-based
checks** plus the adversarial review, not TDD or visual QA:

- **Prose-presence and prose-absence (goal-based, `grep`).** Each new doctrine
  element is verified by a `grep` over the projected source that it is present;
  each anti-requirement (no language names, no thresholds, no Claude-only
  dependency) by a `grep` that confirms its absence.
- **Projection integrity (goal-based, `make build-self` + `git status`).** The
  working tree is clean after `make build-self` — sources and projections agree,
  no drift.
- **Doctrine-consistency (manual read, recorded in the adversarial pass).** The
  new bullets do not contradict the retained doctrine (#21 rule-of-three, #4
  DAMP-over-DRY, the existing "do not demand 100% coverage" stance). This is a
  judgment check the `adversarial-reviewer` + `quality-engineer` passes record.

No contract surface (not an API), no UI, no new tests of runtime behavior — the
artifacts under change *are* review doctrine.

## Acceptance Criteria

- [ ] `quality-engineer.md` Maintainability section adds four universal-smell findings: (a) **bounded complexity** — *split* high cognitive/cyclomatic complexity that is **reducible structural** complexity, explicitly distinguished from existing #23 (which *comments* irreducible, non-obvious complexity — the two are complementary, not rival remedies); (b) **nesting depth** — reduce via idiom-appropriate techniques (guard clauses / pattern matching / early returns), explicitly *not* mandating early-`return`; (c) **duplicated production blocks past the rule-of-three**; (d) **magic literals of non-obvious origin → named constants, and function/parameter bloat**, judgment-based and threshold-free — scoped to align with `adversarial-reviewer`'s existing threshold-suppression carve-out (a self-evident tunable like `MAX_RETRIES = 3` is **not** a finding; a spec-derived / regulatory / calibrated literal is), never the opposite of it.
- [ ] The Maintainability section is reframed so the lens explicitly states it **approximates the maintainability/reliability rating a strict static-analysis gate enforces, applied whether or not such a gate is wired** — i.e. by default, without detection.
- [ ] The four bullets name **no programming language as a requirement and no numeric threshold** (verified by absence-grep); the project owns the numbers when a linter is wired.
- [ ] `quality-engineer.md` Test Design gains a **one-line preface above the numbered list** stating the mutation-testing mindset — *"a test must be able to fail: if you can break the behaviour and nothing goes red, the test is theatre"* — as the Goodhart-safe stand-in for chasing a coverage number; the existing #1–#8 numbering is left intact and the existing "do not demand 100% coverage" stance is retained, not contradicted.
- [ ] No new bullet contradicts retained doctrine: the duplication bullet **explicitly exempts test code** (tests stay DAMP per existing #4); abstraction still defers to the **rule-of-three** (existing #21); the complexity bullet disambiguates from **#23**; and the magic-literal bullet aligns with **`adversarial-reviewer`'s threshold carve-out** — a read-check confirms all four alignments.
- [ ] `work-loop` `SKILL.md` adds a **simplify pass** to EXECUTE/REVIEW: after a task's gates are green, a deliberate reduce-the-diff step (inline single-use, delete dead code, collapse needless indirection) **scoped to the new code only**, leaving tests DAMP and not touching adjacent untouched code.
- [ ] The simplify pass is **harness-agnostic doctrine** and notes that Claude Code's native `/simplify` performs the pass, **without making the loop depend on it** (graceful for adapters that lack it).
- [ ] `work-loop` light mode **carries prose retaining the `quality-engineer` pass when the adopter declares (in their AGENTS.md) that the repo is judged by a strict external quality gate the local loop can't run**; absent that declaration, light mode is unchanged (still drops it by default). *Verification is prose-presence (grep) — the behavioral half (the agent reading an adopter declaration and acting on it) is non-harnessable LLM doctrine, consistent with Testing Strategy.*
- [ ] The light-mode carve-out is **policy-driven (adopter declaration), not repo detection** — no scanning logic, no per-stack table (verified by reading the added prose).
- [ ] The **seed** `packs/core/seeds/docs/CONVENTIONS.md` (which projects to `docs/CONVENTIONS.md` — AGENTS.local.md:146) has § *Light and full modes* **thinned**: the duplicated mechanics summary ("a lean inline spec … no default `quality-engineer` pass") is removed, leaving the principle (rigor scales with risk) + an explicit pointer to the `work-loop` skill as the sole owner of mode mechanics. The **risk-trigger block stays byte-identical across all four copies** — `AGENTS.md`, `packs/core/seeds/AGENTS.md`, the seed CONVENTIONS, and `work-loop/SKILL.md` — verified by a four-file `diff` of the extracted block after `make build-self` (grep-equality AC of `work-loop-light-mode` preserved).
- [ ] A **governance note** records the `CONVENTIONS.md` edit as owner-directed in lieu of a separate RFC (this conversation), per the repo's convention for substantive CONVENTIONS edits.
- [ ] The **core pack version is bumped** `0.2.0` → `0.3.0` (minor — this is a `feat`-grade doctrine addition) in **both** the `[pack]` `version` key of `packs/core/pack.toml` (**not** the `[contract]` `version` key, which stays `0.12`) and the `version` in `packs/core/.claude-plugin/plugin.json`; `make build-self` re-aggregates `marketplace.json` and any version-assertion sweep stays green.
- [ ] `AGENTS.local.md` gains a standing rule: **a non-cosmetic update to any `packs/<pack>/` content must bump that pack's version** (`pack.toml` `[pack]` version + `.claude-plugin/plugin.json`); cosmetic-only changes (typos, formatting, comment reflow) need no bump.
- [ ] All edits are made in `packs/core/.apm/` sources and projected via `make build-self`; `git status` is clean afterward (no drift), and the projected `.claude/agents/quality-engineer.md` + `.claude/skills/work-loop/SKILL.md` reflect the sources.
- [ ] `docs/product/changelog.md` `[Unreleased]` carries an entry describing the user-visible doctrine changes.

## Assumptions

- Technical: `quality-engineer` source is `packs/core/.apm/agents/quality-engineer.md`; Maintainability = findings #20–23, Test Design = #1–8, and the "do not demand 100% coverage" stance is already present (source: file read 2026-06-12)
- Technical: `work-loop` light mode currently states "No default `quality-engineer` pass" in `packs/core/.apm/skills/work-loop/SKILL.md` § Modes (source: file read 2026-06-12)
- Technical: the risk-trigger list is byte-identical across `AGENTS.md`, `packs/core/seeds/AGENTS.md`, `docs/CONVENTIONS.md`, and the work-loop `SKILL.md`; grep-equality is an AC of `work-loop-light-mode` (source: `risk-triggers:start` comment, `docs/CONVENTIONS.md:653`)
- Technical: `CONVENTIONS.md:643` § Light/full modes names "no default `quality-engineer` pass" but `:678` already delegates trim *mechanics* to the work-loop skill (source: file read 2026-06-12)
- Technical: self-host projection is `make build-self` (`Makefile:38`), editing `packs/core/.apm/` sources; `docs/product/changelog.md` has an `[Unreleased]` section at line 18 (source: file reads 2026-06-12)
- Technical: core pack version is `0.2.0` in `packs/core/pack.toml:3` (`[pack]`) and `packs/core/.claude-plugin/plugin.json:3`; the `version = "0.12"` at `pack.toml:18` is the separate `[contract]` version and is out of scope (source: file reads 2026-06-12)
- Process: a non-cosmetic pack update must bump the pack version; this spec both follows that rule (bumping core) and codifies it in `AGENTS.local.md` (source: user confirmation 2026-06-12)
- Reference: bullets 1–3 (complexity / nesting / duplication) map to real lint rules across the 9 stacks — confirmed that detekt's `ComplexMethod` and the SonarJS ESLint plugin both use SonarSource's cognitive-complexity metric, ESLint ships `complexity`/`max-depth`, gocognit covers Go, RuboCop `Metrics/CyclomaticComplexity`, pylint `duplicate-code (R0801)` (sources: [detekt complexity rules](https://detekt.dev/docs/rules/complexity/), [ESLint complexity](https://eslint.org/docs/latest/rules/complexity), [gocognit](https://github.com/uudashr/gocognit), [pylint R0801](https://pylint.readthedocs.io/en/stable/user_guide/messages/refactor/duplicate-code.html), web search 2026-06-12). Bullet (d) magic-literals is threshold-variable and weaker-by-default in Go/Ruby/Rust, so it ships judgment-based and threshold-free (source: pressure-test table, this conversation)
- Process: the `CONVENTIONS.md` thinning + light-mode carve-out land in this single spec as an owner-approved PR with a governance note, in lieu of a separate `update-conventions` RFC; full CONVENTIONS retirement is deferred to its own RFC (source: user confirmation 2026-06-12)
- Product: the adopter declares "this repo is judged by a strict external quality gate" as a free-text instruction in their own `AGENTS.md`, read by the agent — no new structured field (source: user confirmation 2026-06-12)
