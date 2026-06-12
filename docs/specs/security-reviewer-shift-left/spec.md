# Spec: security-reviewer-shift-left

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0029](../../rfc/0029-strengthen-security-reviewer.md), [ADR-0018](../../adr/0018-shift-security-review-left-progressive-disclosure.md), [ADR-0017](../../adr/0017-adopt-bandit-pip-audit-semgrep-sast-gate.md), [ADR-0014](../../adr/0014-rigor-scales-with-risk-work-loop-modes.md) / [RFC-0025](../../rfc/0025-work-loop-light-mode-and-risk-based-escalation.md)
- **Brief:** none
- **Contract:** none <!-- no machine-readable interface surface; the artifacts are agent-prompt + skill content. No adapter-contract change (see AC10). -->
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer or agent doing **security-boundary work** in a repo that installed
the core pack gets a security review that is *current*, *shifted left*, and
*deep without prompt bloat*. Concretely, the `security-reviewer` gains a
**spec-stage secure-design mode** (run at the work-loop's pre-EXECUTE step on the
security-boundary trigger, so a control gap is caught as design guidance, not three
post-implementation round-trips later); its checklist is refreshed to a current,
multi-framework stack delivered through a new **orchestrator-loaded,
progressive-disclosure `security-checklists` skill** (the universal method stays in
the agent body; boundary-scoped depth loads from the skill and is inlined into the
subagent's brief); tool-delegation is **language-agnostic and fails honestly** when
a scanner is absent; and the reviewer systematically catches **established-helper
bypass** ("rolled its own instead of the repo's blessed helper") using existing
convention surfaces, with **no adapter-contract change** and **no new mandatory
`security.md` file**. The shipped skill carries the *mechanism* only — never this
repo's specific helper names — so it stays adopter-clean.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Scope every loaded module to the trust boundary the change actually crosses
  (1–3 modules per change, never a flat 10-module march).
- Keep the shipped `security-checklists` skill **adopter-clean**: it carries the
  established-helper-bypass *mechanism*, never this repo's `write_jailed` /
  `credbroker` specifics.
- Preserve the "complements, does not replace SAST/SCA scanners" framing
  (ADR-0017): the `tool`-delegation bucket must actively confirm a scanner is
  wired, and the honest-limits "Not checked" footer stays mandatory.
- Name the standard **and its version** in each module's header (OWASP Top
  10:2025, ASVS 5.0, API Security Top 10:2023, LLM Top 10:2025, CWE Top 25,
  Proactive Controls 2024, STRIDE, LINDDUN).

### Ask first

- Collapsing the module count below 10 (RFC Open Q1 — collapse only on observed
  co-firing redundancy, e.g. `supply-chain` + `config-misconfig`).
- The exact shape of the `AGENTS.md` "blessed security tools/helpers"
  customization point beyond a short list + inference fallback (RFC Open Q2),
  keeping `AGENTS.md` under its ~200-line budget.
- Any edit to the **risk-trigger block** — its wording is byte-identical across
  `AGENTS.md`, `packs/core/seeds/AGENTS.md`, `docs/CONVENTIONS.md`, and the
  `work-loop` skill (a grep-equality acceptance criterion of an existing spec);
  do not disturb it.

### Never do

- Change the adapter contract (`docs/contracts/adapter.toml` / `_data/` twin) —
  the `skill` primitive already projects `direct-directory` everywhere.
- Mint a new mandatory per-repo `security.md` standard file (D5 rejected it);
  convention awareness rides existing surfaces only.
- Add a runtime dependency to any shipped package, or a new top-level directory.
- Make subagent self-discovery of the skill the *load-bearing mechanism* — the
  orchestrator drives loading; auto-discovery is a redundant convenience only.

## Testing Strategy

No behavior here has a compressible code invariant — the deliverables are
agent-prompt and skill **content** plus orchestration **prose**, so there is no
TDD surface. Verification is **goal-based checks** for everything mechanically
inspectable, and **manual / visual QA** for the one behavior that is agent
reasoning rather than a file fact:

ACs are numbered top-to-bottom in the **Acceptance Criteria** list below (AC1 =
the first checkbox … AC13 = the last); the references here resolve against that
order.

- **Skill + module presence and shape** (AC1): goal-based — `ls`/`grep` that the
  10 module files exist, each header names a standard+version, and each carries
  the `tool`/`hybrid`/`reason` tags.
- **Agent-body edits** (AC2, AC3): goal-based — `grep` that `security-reviewer.md`
  carries the spec-stage secure-design mode heading (AC2), cites OWASP Top
  10:**2025** (and no longer **2021** as its awareness anchor), keeps the universal
  method (the always-on STRIDE+LINDDUN pass, the established-helper-bypass
  meta-check), and that the deep per-domain checklists were removed from the body
  (AC3).
- **Three-bucket delegation** (AC7): goal-based — `grep` that the agent body
  carries the three-bucket rule *and* the language-agnostic scanner-detection list
  (`npm audit` / `pip-audit` / `govulncheck` / `cargo audit` / Snyk / Semgrep /
  CodeQL) *and* the tool-absence tokens (`degraded: no scanner` / an explicit-gap
  statement). The rule's *presence* is necessary but not sufficient — the grep must
  hit the detection list and the absence behavior, the verifiable core of AC7.
- **work-loop wiring** (AC4, AC5, AC6): goal-based — `grep` that the pre-EXECUTE
  step names `security-reviewer` on the security-boundary trigger as net-new (AC4),
  that the security-review step loads matching modules and inlines their content
  (AC5), and that a deterministic boundary→module routing table is present (AC6).
- **Repo-convention awareness** (AC8): goal-based — `grep` that `AGENTS.md` carries
  a light "blessed security tools/helpers" point and that the agent's existing
  `docs/architecture/security.md` / `docs/guides/reference/security.md` reads are
  retained; assert no new mandatory `security.md` standard file was added.
- **Adopter-clean + no-contract-change + projection** (AC9, AC10, AC11): goal-based —
  a grep that the shipped skill names no repo-specific helper (AC9); an assertion
  that the adapter contract `version` is unchanged and `skill` stays
  `direct-directory` (AC10); and `make build-self` produces no drift with the core
  pack version bumped (AC11).
- **CONVENTIONS touch** (AC12): goal-based — `grep` the landed note (in its decided
  home) and confirm it ships in the same PR as the AC4 wiring, so it is not a
  forward-claim.
- **No new top-level dir / no new dependency** (AC13): goal-based — assert against
  `origin/main` that no new top-level directory and no new runtime dependency were
  introduced.
- **Orchestrator loads the right depth into the brief** (AC5 behavior): manual /
  visual QA — on a sample security-boundary diff (e.g. an outbound-HTTP change),
  walk the work-loop security-review step and confirm only the matching module(s)
  (`outbound-ssrf`) are inlined into the subagent brief, recorded in the PR.
- **Spec-mode + implementation adversarial review**: the loop's own gate, not an
  AC artifact.

## Acceptance Criteria

- [ ] A new core-pack skill `security-checklists` exists with a `SKILL.md` and ten
  `references/<module>.md` modules — `access-control`, `authn-session`,
  `injection`, `path-and-file`, `secrets-and-crypto`, `outbound-ssrf`,
  `supply-chain`, `config-misconfig`, `exceptional-conditions`, `llm-agent` — each
  module naming its standard+version in its header and tagging every check
  `tool` / `hybrid` / `reason`.
- [ ] `security-reviewer.md` carries a **spec-stage secure-design mode** distinct
  from its implementation mode (mirroring `adversarial-reviewer`'s spec-stage
  structure): in this mode it reads the *spec* and asks, per trust boundary the
  feature crosses, whether the control is specified as an acceptance criterion at
  the right depth (confinement not just traversal; scheme allowlist not "validate
  the URL"; broker-mediated secrets not ad-hoc reads).
- [ ] `security-reviewer.md`'s awareness checklist cites **OWASP Top 10:2025**
  (replacing the 2021 list), and its **deep per-domain checklists are trimmed** to
  the universal method (delegation rule, load-context-first, always-on
  STRIDE + LINDDUN open pass, established-helper-bypass meta-check, severity rubric,
  honest-limits footer, output format) — the shape-specific depth now lives in the
  skill modules, not the agent body.
- [ ] The `work-loop` SKILL.md **pre-EXECUTE review step dispatches
  `security-reviewer` (spec-stage mode) when the security-boundary trigger is
  present** — net-new wiring alongside the existing adversarial-only firing, named
  as net-new (not a re-use) per RFC D3.
- [ ] The `work-loop` SKILL.md **security-review step loads only the
  boundary-matching `security-checklists` modules and inlines their content into the
  `security-reviewer` subagent's brief**, reusing the existing on-demand
  `references/*.md` loading pattern.
- [ ] A **deterministic boundary→module routing table** is documented (which trust
  boundaries load which module(s)), so loading is orchestrator-driven and not
  model-relevance-judged.
- [ ] The **three-bucket delegation** is specified with **language-agnostic scanner
  detection** (`npm audit` / `pip-audit` / `govulncheck` / `cargo audit` / Snyk /
  Semgrep / CodeQL — not Python-assumed) and **defined tool-absence behavior**
  (Tier-1 declare/detect/fail-clean: reason best-effort with a `degraded: no
  scanner` flag, or state the gap explicitly — never silently skip).
- [ ] **Repo-convention awareness without a new file**: `AGENTS.md` gains a light
  "blessed security tools/helpers" customization point (a short list + inference
  fallback), and the agent's existing read of
  `docs/architecture/security.md` / `docs/guides/reference/security.md` is retained;
  no new mandatory `security.md` standard file is introduced.
- [ ] **Adopter-clean**: the shipped `security-checklists` skill names no
  repo-specific helper (`write_jailed`, `credbroker`, …) — it carries the
  established-helper-bypass *mechanism* only (grep-gated).
- [ ] **No adapter-contract change**: `docs/contracts/adapter.toml` (and its
  `_data/` twin) `version` is unchanged, and `skill` stays `direct-directory` for
  every adapter.
- [ ] The new skill + agent edits + work-loop edits **project via `make build-self`
  with no drift**, and the **core pack version is bumped** (non-cosmetic pack update
  per the `AGENTS.local.md` rule).
- [ ] The RFC-0029 **CONVENTIONS touch lands in this implementing PR**, in its
  decided home (`docs/CONVENTIONS.md` how-we-work *or* the `work-loop` skill as the
  canonical "how"), describing that security review runs at spec stage on
  security-boundary work — landing **atomically with the AC4 wiring** so it is not a
  forward-claim.
- [ ] **No new top-level directory and no new dependency** are introduced.

## Assumptions

<!-- Audit trail for the assumption-surfacing checkpoint (new-spec step 3). Each
item was verified by direct repo read or against RFC-0029, which is Accepted. -->

- Technical: the `skill` primitive projects `direct-directory` on every adapter, so
  `references/` travel everywhere with no contract change (source:
  `docs/contracts/adapter.toml`; RFC-0029 § Evidence "contract grep").
- Technical: the work-loop already loads `references/*.md` on demand and dispatches
  reviewers with a constructed brief, so orchestrator-side module-inlining reuses an
  existing mechanism (source: `packs/core/.apm/skills/work-loop/SKILL.md` §§ PLAN
  "Pre-EXECUTE adversarial review" / REVIEW, read 2026-06-12).
- Technical: the pre-EXECUTE review fires today only for spec-amendment /
  structural-change and dispatches only `adversarial-reviewer`; the security-boundary
  trigger exists only for light→full escalation — so spec-stage security dispatch is
  **net-new wiring** (source: `work-loop/SKILL.md` §§ PLAN + Modes, read 2026-06-12;
  RFC-0029 D3).
- Technical: `security-reviewer.md` already reads
  `docs/architecture/security.md` / `docs/guides/reference/security.md` and cites
  OWASP Top 10:**2021** as its web lens — both confirmed (source:
  `packs/core/.apm/agents/security-reviewer.md:42,62`, read 2026-06-12).
- Technical: `docs/CONVENTIONS.md` is projected from the seed
  `packs/core/seeds/docs/CONVENTIONS.md` (byte-identical today), so a CONVENTIONS
  edit means editing the seed + `make build-self`, and is a core-pack content change
  (source: repo read + memory `self-host projection`; core `pack.toml` version
  `0.2.0`, read 2026-06-12).
- Process: this is a follow-on to an **Accepted** RFC (RFC-0029) and is recorded by
  **ADR-0018** (Accepted), so the decision is made; this spec is the implementation
  contract (source: `docs/rfc/0029-strengthen-security-reviewer.md` § Follow-on
  artifacts; `docs/adr/0018-...md`).
- Process: the risk-trigger block is byte-identical across four files and must not be
  disturbed (source: `work-loop/SKILL.md` risk-triggers comment; memory
  `quality-floor` note).
- Product: the consumer is a maintainer/agent doing security-boundary work in a
  core-pack-installed repo; the value is collapsing post-implementation security
  round-trips into a design-time pass (source: RFC-0029 § Problem; user direction
  2026-06-12).
