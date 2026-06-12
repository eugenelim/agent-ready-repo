# ADR-0018: Shift security review left and deliver its depth via an orchestrator-loaded progressive-disclosure skill

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-12
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0029 (the proposal this records); ADR-0017 (the SAST/SCA gate — the motivating evidence and the "scanners catch syntactic; the reviewer catches reasoning" split); ADR-0014 / RFC-0025 (risk-triggered work-loop modes — the security-boundary trigger this reuses); the implementing spec `docs/specs/security-reviewer-shift-left/`

## Context

The repo ships three core review lenses as subagents — `adversarial-reviewer`,
`security-reviewer`, and `quality-engineer`. Implementing ADR-0017 (the SAST/SCA
gate) this session exercised the `security-reviewer` hard and exposed three
structural gaps, each independently confirmed:

1. **It is the only core reviewer that doesn't shift left.** `adversarial-reviewer`
   has spec-stage checks wired into the work-loop's pre-EXECUTE step;
   `quality-engineer` is multi-mode with a spec-level scope. The
   `security-reviewer`'s contract is explicitly *"use after adversarial-reviewer
   is clean, before merging"* — last lens, never first. Security therefore arrives
   as a *gate*, not as *design guidance*. Concretely, this cost round-trips: a
   CWE-73 path-confinement gap, an SSRF scheme-guard miss, and a hash disposition
   were each caught only in post-implementation review — three round-trips a
   design-time pass would have collapsed to one.

2. **Its checklist is a stale awareness list, used as a verification checklist.**
   The reviewer cites **OWASP Top 10:2021** — which predates the two 2025
   categories central to the very PR that surfaced this (A03 Software Supply Chain
   Failures, A10 Mishandling of Exceptional Conditions). OWASP Top 10 is ~10 coarse
   *awareness* buckets; ASVS is the *verification* standard; API authorization
   (BOLA/BFLA) lives in a *separate* Top 10; STRIDE adds threat-model breadth but
   has a known **privacy blind spot** (LINDDUN's domain).

3. **It has no depth-without-bloat mechanism and no repo-specificity.** You cannot
   paste ASVS's ~350 requirements into an agent prompt, and the highest-value
   real-world finding — *"this code crossed a boundary the repo already has a
   blessed helper for and rolled its own"* (exactly the SSRF and path cases this
   session) — requires repo-convention awareness the reviewer doesn't systematically
   apply.

Four constraints shape any fix:

- **No adapter-contract change is wanted.** The `skill` primitive already projects
  `direct-directory` on every adapter, so a skill's `references/` travel
  everywhere. Bumping the *agent* primitive's contract to give it its own
  `references/` would be an RFC-0022/0026/0027-scale change for no gain.
- **A subagent cannot be forced to load a skill.** Skill invocation is
  model-invoked and adapter-variable, and the `security-reviewer`'s `tools:` does
  not even include a Skill tool. So depth cannot depend on the subagent
  self-discovering a library.
- **Depth must not re-bloat the prompt.** The reviewer's own rule warns against
  forced breadth ("two real Blockers beats ten recycled checklist items"); pasting
  a layered multi-framework checklist inline would dilute findings.
- **This is a reasoning lens above the scanners, not a replacement.** ADR-0017 owns
  Bandit/Semgrep/CodeQL/Snyk; a richer reviewer must actively *confirm scanners are
  wired*, not invite operators to treat the reasoning pass as coverage.

## Decision

**We will strengthen the `security-reviewer` along three axes at once — (1) a
current, multi-framework checklist, (2) delivered through a new
orchestrator-loaded, progressive-disclosure `security-checklists` skill so depth
never bloats the agent, and (3) shifted left via a spec-stage secure-design mode
wired into the work-loop's pre-EXECUTE review on the security-boundary trigger —
with no adapter-contract change.**

The specifics, recorded so the next maintainer need not re-litigate them:

- **Layered, scoped checklist.** Replace the single 2021 list with four tiers,
  scoped to the trust boundaries the change crosses (never a flat march):
  design-time proactive (OWASP Proactive Controls 2024 + ASVS 5.0 V1 + A06
  Insecure Design), awareness breadth (OWASP Top 10:**2025**, API Security
  Top 10:2023, LLM Top 10:2025), verification depth (ASVS 5.0 chapters + CWE
  Top 25), and open-ended threat modeling (STRIDE **+ LINDDUN** for privacy).
- **Universal method stays in the agent body; shape-specific depth moves to the
  skill.** Universal = the delegation rule, load-context-first, the always-on
  STRIDE + LINDDUN open pass, the established-helper-bypass meta-check, severity
  rubric, honest-limits footer, output format. Shape-specific = ten boundary-keyed
  modules (`access-control`, `authn-session`, `injection`, `path-and-file`,
  `secrets-and-crypto`, `outbound-ssrf`, `supply-chain`, `config-misconfig`,
  `exceptional-conditions`, `llm-agent`) as `references/<module>.md`.
- **The orchestrator drives loading, not the subagent.** At the security-review
  step the work-loop detects which boundaries the diff/spec crosses, loads only the
  matching modules (deterministic boundary→module routing), and **inlines the
  selected module content into the subagent's brief** — reusing the work-loop's
  existing on-demand `references/*.md` loading. The subagent receives a focused
  ~30-item checklist as prompt text; it never resolves an adapter-specific path.
  Subagent auto-discovery (where supported) is a redundant convenience, never a
  dependency.
- **Three-bucket delegation with defined tool-absence behavior.** Every loaded
  check is tagged `tool` (scanner-owned — confirm it's wired), `hybrid` (scanner
  finds the flow, reviewer judges the fix), or `reason` (reviewer-only). Delegation
  **detects the ecosystem's** scanner (`npm audit` / `pip-audit` / `govulncheck` /
  `cargo audit` / Snyk / Semgrep / CodeQL) rather than assuming Python; when a
  delegated scanner is **absent**, the reviewer does not silently skip
  (Tier-1 declare/detect/fail-clean) — it reasons the class best-effort with a
  `degraded: no scanner` flag, or states the gap explicitly.
- **Repo-convention awareness without a new mandatory file.** The highest-value
  repo-aware check is **established-helper bypass**. Convention source, in
  precedence: `AGENTS.md` (a light "blessed security tools/helpers" customization
  point, *not* a new `security.md`) → `CONVENTIONS.md` and any context other packs
  install → inference fallback (grep for the de-facto helper). The agent's existing
  read of `docs/architecture/security.md` / `docs/guides/reference/security.md` is
  **retained** (it fits the "any context the repo provides" tier). What is rejected
  is *minting a new mandatory standard file*, not reading one an adopter keeps.
- **Packaging.** New `security-checklists` skill (core pack) + edits to
  `security-reviewer.md` (add the spec-stage mode; trim the per-domain checklists
  to the universal method; add the three-bucket rule) + `work-loop/SKILL.md` wiring
  (load modules → inline into brief; add `security-reviewer` to the
  security-boundary pre-EXECUTE pass — **net-new wiring**, not a reuse of the
  existing adversarial-only firing).

Boundaries on the decision:

- **No adapter-contract change.** The `skill` primitive already projects everywhere.
- **Not a replacement for SAST/SCA scanners.** ADR-0017 owns those; this is the
  reasoning lens above them, and the three-bucket delegation actively confirms they
  are wired.
- **Not a new per-repo `security.md` standard.** Convention awareness rides existing
  surfaces.
- **The spec-stage pass is gated to the security-boundary risk trigger** (ADR-0014 /
  RFC-0025), not mandated on all work.

## Consequences

**Positive:**
- Security review becomes design guidance, not only a late gate — the round-trips
  the ADR-0017 work measured collapse toward one design-time pass.
- The awareness list is current (2025 categories) and the depth reference is
  verification-grade (ASVS + CWE Top 25 name CWE-22/CWE-73 directly — our exact
  miss), without bloating the agent prompt.
- Depth ships to **every** adapter with no contract change — the skill primitive
  already projects, and orchestrator-driven loading removes the dependency on
  model-invoked subagent skill-discovery.
- The established-helper-bypass check catches the most actionable real finding
  (rolled-its-own instead of the blessed helper) while keeping the shipped skill
  adopter-clean (it carries the *mechanism*, never this repo's `write_jailed` /
  `credbroker` specifics).
- Tool-delegation is language-agnostic and fails honestly when a scanner is absent,
  so the lens degrades visibly rather than silently.

**Negative:**
- Real cognitive and maintenance surface: a new skill, a second agent mode, and
  work-loop wiring — three places to keep coherent.
- A second review mode is a judgment call the model can mis-route.
- Standards update annually; the modules carry a yearly currency-review cost (small
  and version-pinned per module, but real).
- The gate's fidelity to a given org's actual scanner config (Snyk, etc.) cannot be
  proven from source — it is a high-fidelity proxy, not the same engine.
- **Checklist theater risk:** a richer, shift-left lens can invite treating the
  *reasoning* pass as *coverage*. Mitigated by the "complements, does not replace
  scanners" boundary, the `tool`-delegation that confirms scanners are wired, and
  the mandatory honest-limits footer — named here so the framing stays "reasoning
  above the tools," not "the tools."

**Neutral / to revisit:**
- **Module granularity.** We ship 10 modules; if two always co-fire in practice
  (e.g. `supply-chain` + `config-misconfig`), collapse them. Decide on observed
  redundancy, in the implementing spec.
- **`AGENTS.md` customization shape** — exactly how light the "blessed security
  tools/helpers" point is (a short list vs. a per-boundary table) — is settled in
  the implementing spec, keeping `AGENTS.md` under its ~200-line budget.
- **CONVENTIONS touch timing.** RFC-0029 named a light how-we-work note that
  security review runs at spec stage on security-boundary work. Because that note
  describes the work-loop wiring this decision authorizes but does not yet build, it
  lands *with* the wiring (an implementing-spec acceptance criterion), not ahead of
  it — and whether it belongs in `CONVENTIONS.md` or in the `work-loop` skill (the
  canonical "how") is settled there, consistent with the ongoing move of mode
  mechanics out of `CONVENTIONS.md`.

## Alternatives considered

Grounded in how the repo's *other* reviewers already work, along the axis of "how
much the proposal changes," from nothing to a contract-level overhaul (collectively
exhaustive — any proposal sits somewhere on it):

- **Do nothing** (keep 2021 + LLM + STRIDE, post-diff only). Rejected — the gaps
  that cost round-trips this session persist and the awareness list is provably
  stale; the cost of delay is recurring late findings.
- **Currency-only** (bump 2021→2025, nothing else). Rejected — closes the staleness
  but leaves the *structural* gaps (no depth, no shift-left, no repo-awareness).
- **Inline everything in the agent** (paste the layered checklist into
  `security-reviewer.md`). Rejected — no new primitive, but bloats the prompt,
  dilutes findings (the agent's own rule warns against forced breadth), and still
  doesn't shift left.
- **Subagent self-discovers a skill** (agent loads `security-checklists` itself).
  Rejected as the *mechanism* — works on some adapters but is model-invoked and
  adapter-variable, and the agent's `tools:` excludes a Skill tool. Fine as a
  redundant convenience layered on top of orchestrator-driven loading.
- **★ Skill + orchestrator-loaded + shift-left (chosen).** More moving parts, but
  reuses the established shape — `adversarial-reviewer`'s spec-stage mode,
  `quality-engineer`'s multi-mode design, and the work-loop's own on-demand
  `references/` loading — and ships everywhere with no contract change.
- **Add an adapter-contract change** (give the *agent* primitive its own
  `references/`). Rejected — most general, but an expensive contract bump for no
  gain when skills already carry references.

## References

- Proposal: RFC-0029 (`docs/rfc/0029-strengthen-security-reviewer.md`).
- Implementing spec: `docs/specs/security-reviewer-shift-left/spec.md`.
- ADR-0017 (`docs/adr/0017-adopt-bandit-pip-audit-semgrep-sast-gate.md`) — the
  scanner gate and the reasoning-vs-syntactic split.
- `packs/core/.apm/agents/adversarial-reviewer.md` — the spec-stage-mode template.
- `packs/core/.apm/agents/quality-engineer.md` — the multi-mode precedent.
- `packs/core/.apm/skills/work-loop/SKILL.md` — the on-demand `references/` loading
  and reviewer-dispatch mechanism the orchestrator-loading reuses.
- OWASP Top 10:2025 <https://owasp.org/Top10/2025/>; ASVS 5.0
  <https://owasp.org/www-project-application-security-verification-standard/>; API
  Security Top 10:2023 <https://owasp.org/www-project-api-security/>; Proactive
  Controls 2024 <https://top10proactive.owasp.org/archive/2024/the-top-10/>.
