# RFC-0029: Strengthen the security reviewer — progressive-disclosure, multi-framework, repo-aware, shifted left

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-12
- **Date closed:** 2026-06-12
- **Related:** ADR-0017 (SAST/SCA gate — the motivating evidence); RFC-0025 / ADR-0014 (risk-triggered work-loop modes); `packs/core/.apm/agents/security-reviewer.md`; `packs/core/.apm/agents/adversarial-reviewer.md` (spec-stage precedent); `packs/core/.apm/agents/quality-engineer.md` (multi-mode precedent)

## The ask

- **Recommendation (BLUF):** Strengthen the `security-reviewer` along three axes at once: **(1)** a current, multi-framework checklist (OWASP Top 10:**2025**, ASVS 5.0, API Security Top 10:2023, LLM Top 10:2025, CWE Top 25, LINDDUN) replacing the stale 2021-only list; **(2)** delivered through a new **orchestrator-loaded, progressive-disclosure `security-checklists` skill** so depth never bloats the agent and ships to every adapter; **(3)** **shifted left** — a spec-stage secure-design mode wired into the `work-loop` pre-EXECUTE review on the security-boundary trigger. **No adapter-contract change.**

- **Why now (SCQA):** *Situation* — the security-reviewer is one of three core review lenses. *Complication* — implementing ADR-0017 this session exposed three structural gaps: it is **reactive-only** (it caught a CWE-73 path-confinement gap, an SSRF scheme-guard miss, and a hash disposition only in post-implementation review — three round-trips a design-time pass would have collapsed to one); it runs a **stale awareness list** (OWASP Top 10:**2021**, which predates the two 2025 categories — A03 Supply-Chain and A10 Exceptional-Conditions — that this very PR was *about*); and it has **no depth mechanism** (an awareness list, not a verification standard) and **no design-time mode**, unlike the other two reviewers. *Question* — how do we add design-time, verification-grade, repo-specific depth **without** bloating the agent prompt or breaking cross-adapter portability?

- **Decisions requested:**
  1. **Adopt the layered multi-framework stack** (vs. currency-only bump or do-nothing). Recommended. Decide-by 2026-06-19; default = adopt.
  2. **Deliver via an orchestrator-loaded `security-checklists` skill** (vs. inline-in-agent or subagent-self-discovery). Recommended. Default = adopt.
  3. **Add a spec-stage secure-design mode, wired into `work-loop` pre-EXECUTE** on the security-boundary trigger. Recommended. Default = adopt.
  4. **Adopt the three-bucket delegation + Tier-1 tool-absence behavior** (tool / hybrid / reason; detect-then-degrade-with-disclosure; ecosystem-detected, not Python-assumed). Recommended. Default = adopt.
  5. **Repo-convention awareness via `AGENTS.md` + inference + pack-provided context** — *not* a new `security.md` file. Recommended. Default = adopt.
  6. **Package as: new skill + edits to `security-reviewer.md` + `work-loop` wiring; no adapter-contract change.** Recommended. Default = adopt.

## Problem & goals

**Diagnosis.** The security-reviewer is a strong *reactive* lens (OWASP Top 10:2021 + LLM 2025 + STRIDE, run post-diff). Three structural problems, each independently confirmed:

1. **It is the only core reviewer that doesn't shift left.** `adversarial-reviewer` has spec-stage checks wired into the work-loop's pre-EXECUTE step; `quality-engineer` is multi-mode with a spec-level scope. The security-reviewer's contract is explicitly *"Use after adversarial-reviewer is clean, before merging"* — last lens, never first. Security therefore arrives as a *gate*, not as *design guidance*, which is why the ADR-0017 findings cost round-trips.
2. **Its checklist is a stale awareness list, used as a verification checklist.** OWASP Top 10 is ~10 coarse risk buckets for *awareness*; ASVS is the *verification* standard; API authz lives in a *separate* Top 10. The reviewer cites the **2021** Top 10 — missing A03 Supply-Chain Failures and A10 Mishandling of Exceptional Conditions (both new in 2025, and both central to the SAST PR). STRIDE adds threat-model breadth but has a known **privacy blind spot** (LINDDUN's domain).
3. **It has no depth-without-bloat mechanism and no repo-specificity.** You can't paste ASVS's ~350 requirements into an agent prompt, and the most actionable real-world finding — *"this code crossed a boundary the repo already has a blessed helper for and rolled its own"* (exactly the SSRF and path cases this session) — requires repo-convention awareness the reviewer doesn't systematically apply.

**Goals.**
- Current, verification-grade coverage scoped to the change under review.
- A design-time (spec-stage) security pass on security-boundary work.
- Depth delivered by progressive disclosure, portable across all adapters, with **no contract change**.
- A graceful, language-agnostic tool-delegation model (defined behavior when a scanner is absent).
- Repo-convention awareness that catches "rolled-its-own-instead-of-the-blessed-helper" without proliferating files.

**Non-goals.**
- **Not** replacing SAST/SCA scanners (Bandit/Semgrep/CodeQL/Snyk) — ADR-0017 owns those; this is the reasoning lens above them.
- **Not** an adapter-contract change — the skill primitive already projects everywhere.
- **Not** a new per-repo `security.md` standard (explicitly rejected — see D5).
- **Not** making CodeQL/Snyk a merge blocker — that's branch-protection config, out of scope.
- **Not** mandating the spec-stage pass on *all* work — only the security-boundary risk trigger (RFC-0025).

## Proposal

### D1 — Layered, scoped, current checklist

Replace the single 2021 list with four tiers, **scoped to the boundaries the change crosses** (never a flat march):

- **Design-time (proactive):** OWASP Proactive Controls 2024 + ASVS 5.0 V1 architecture + A06 Insecure Design — used by the spec-stage mode (D3).
- **Awareness (breadth):** OWASP Top 10:**2025**, OWASP **API Security Top 10:2023**, OWASP **LLM Top 10:2025**.
- **Verification (depth):** ASVS 5.0 chapters + CWE Top 25, pulled *per module* as the depth reference (CWE Top 25 names CWE-22/CWE-73 directly — our exact miss).
- **Threat modeling (open-ended):** STRIDE **+ LINDDUN** (privacy).

**Per D1's refinement:** *universal* method stays in the agent body; *shape-specific depth* moves to the skill (D2). Universal = the three-bucket delegation rule, load-context-first, the always-on **STRIDE + LINDDUN open pass**, the **established-helper-bypass** meta-check, severity rubric, honest-limits footer, output format. Shape-specific = the deep per-domain checklists below.

### D2 — Orchestrator-loaded progressive-disclosure skill

A new core-pack skill `security-checklists` holds the shape-activated modules as `references/<module>.md` (the standard skill progressive-disclosure layout). **The orchestrator — not the subagent — drives loading**, because there is no mechanism to force a subagent to invoke a skill, and subagent skill-discovery is model-invoked and adapter-variable. Concretely, reusing the *existing* work-loop pattern (the loop already loads `references/*.md` on demand):

1. At the security-review step, the work-loop detects which trust boundaries the diff/spec crosses.
2. It loads only the matching modules from `security-checklists` (deterministic boundary→module routing).
3. It **inlines the selected module content into the `security-reviewer` subagent's brief** (today the loop passes the diff + spec *path*; this adds the selected modules' *content*).

The subagent receives a focused ~30-item checklist for *this* change as prompt text — it never loads a skill or resolves an adapter-specific path. Progressive disclosure happens orchestrator-side; auto-discovery by the subagent (where an adapter supports it) is a redundant convenience, never a dependency.

**The 10 shape-modules** (anchored on the OWASP Top 10:2025 category axis + cross-cutting lenses):

| Module | OWASP 2025 anchor | Reviewer reasons (`reason`) / delegates (`tool`) / `hybrid` |
|---|---|---|
| `access-control` | A01 (+ API BOLA/BFLA) | `reason`: who-can-call, check-before-effect, object/function-level |
| `authn-session` | A07 | `reason`: session rotation, JWT alg/verify, token entropy, lockout |
| `injection` | A05 (+ A08 deserialization) | `hybrid`: SAST taint finds; reviewer judges escaping/parameterization + safe-loader |
| `path-and-file` | A01 / CWE-22,73 | `hybrid`: confinement vs traversal, symlink escape, zip-slip, uploads |
| `secrets-and-crypto` | A04 (+ secrets-in-logs) | `reason` + `tool`: design + KDF; weak-hash/hardcoded → scanner |
| `outbound-ssrf` | A01 (SSRF absorbed) | `hybrid`: scheme/host allowlist, internal-redirect, metadata block |
| `supply-chain` | **A03 (new)** | `tool`: SCA owns CVEs; reviewer reasons typosquat/pinning/build-trust |
| `config-misconfig` | A02 | `tool`: IaC scanners own most; reviewer reasons CORS/IAM/default-creds |
| `exceptional-conditions` | **A10 (new)** (+ A09 logging) | `reason`: fail-open vs fail-closed, error-path leak, unbounded retry |
| `llm-agent` | OWASP LLM Top 10 2025 | `reason`: prompt-injection isolation, excessive agency, output handling |

A06 Insecure-Design is realized by the spec-stage mode (D3), not a runtime module. Privacy (LINDDUN) rides the always-on open pass in the agent body.

### D3 — Shift left: spec-stage secure-design mode

Add a second mode to the agent (mirroring `adversarial-reviewer`'s spec-stage checks). Two distinct work-loop gates are involved and must not be conflated: RFC-0025's **security-boundary trigger already exists** but only for *light→full mode escalation* (`work-loop/SKILL.md:67`); the **pre-EXECUTE review step** fires today only on *spec-amendment* or *structural-change* and dispatches only `adversarial-reviewer` (`work-loop/SKILL.md:191-216`). So this RFC's D6 must **add new wiring**: extend the pre-EXECUTE review to also dispatch the `security-reviewer` spec-stage mode when the security-boundary trigger is present. That is net-new, not a re-use of existing firing. In this mode the reviewer reads the *spec*, not code, and asks: for each trust boundary the feature crosses, is the **control specified as an acceptance criterion at the right depth** — confinement (CWE-73) not just traversal (CWE-22); scheme allowlist not "validate the URL"; broker-mediated secrets not ad-hoc reads. The same `security-checklists` modules back it, in their proactive-control framing.

### D4 — Three-bucket delegation + Tier-1 tool-absence

Every loaded check is tagged **`tool`** (scanner-owned — confirm it's wired, don't re-check), **`hybrid`** (scanner finds the flow; reviewer judges the fix — the CWE-73 class), or **`reason`** (reviewer-only — logic-flaw authz, fail-open, privacy). Tool-delegation **detects the ecosystem's** scanner (`npm audit` / `pip-audit` / `govulncheck` / `cargo audit` / Snyk / Semgrep / CodeQL), never assumes Python. When a delegated scanner is **absent**, the reviewer does **not** silently skip (Tier-1 declare/detect/fail-clean): it either reasons the class best-effort with a `degraded: no scanner` flag, or emits "class X is normally scanner-owned; none detected → wire one or accept the gap."

### D5 — Repo-convention awareness without new files

The highest-value repo-aware check is **established-helper bypass**: for each boundary the change crosses, find the repo's blessed helper and flag code that rolled its own. Convention source, in precedence: **`AGENTS.md`** (the canonical universal file every adapter already reads — recommend a light "blessed security tools/helpers" customization point there, *not* a new `security.md`) → `CONVENTIONS.md` and **any context other packs install** (Kiro steering files, etc. — the reviewer consumes the established context surface, not a hardcoded filename) → **inference fallback** (grep the codebase for the de-facto helper). The shipped skill carries the **mechanism**, never this repo's specifics (`write_jailed`/`credbroker`) — keeping the primitive adopter-clean. **Backward-compat:** the agent today already reads `docs/architecture/security.md` / `docs/guides/reference/security.md` (`security-reviewer.md:42`); that read is **retained** — it fits the "any context the repo provides" tier. What D5 rejects is *minting a new mandatory standard file*, not reading one an adopter already keeps.

### D6 — Packaging

New `security-checklists` skill (core pack) + edits to `security-reviewer.md` (add spec-stage mode; trim per-domain checklists to the universal method; add the three-bucket rule) + `work-loop/SKILL.md` wiring (load modules → inline into brief; add security-reviewer to the security-boundary pre-EXECUTE pass). **No adapter-contract change** — the `skill` primitive already projects `direct-directory` on every adapter.

## Options considered

**Axis: how much the proposal changes, from nothing to a contract-level overhaul.** This axis is collectively exhaustive — any proposal is somewhere between "change nothing" and "change the primitive contract," and the middle points are the meaningful design forks. Each option below is grounded in how the repo's *other* reviewers and the broader ecosystem already work.

| Option | What | Trade-off | Verdict |
|---|---|---|---|
| **0. Do-nothing** | Keep 2021 + LLM + STRIDE, post-diff only | Zero cost now; but the gaps that cost round-trips this session persist, and the awareness list is provably stale | Rejected — cost-of-delay is recurring late findings |
| **1. Currency-only** | Bump 2021→2025, nothing else | Cheap; closes the staleness | Rejected — leaves the *structural* gaps (no depth, no shift-left, no repo-awareness) |
| **2. Inline everything in the agent** | Paste the layered checklist into `security-reviewer.md` | No new primitive; but bloats the prompt, dilutes findings ("forced breadth"), and still no shift-left | Rejected — the agent's own rule warns against forced breadth |
| **3. Subagent self-discovers a skill** | Agent loads `security-checklists` itself | Works on Claude Code; but model-invoked + adapter-variable, and our agent's `tools:` excludes the Skill tool | Rejected as the *mechanism* — fine as a redundant convenience |
| **★ 4. Skill + orchestrator-loaded + shift-left (this RFC)** | Progressive-disclosure skill, orchestrator inlines modules, spec-stage mode, no contract change | More moving parts (skill + agent + loop wiring); but reuses the existing reference-loading pattern and ships everywhere | **Recommended** |
| **5. + adapter-contract change** | Give the *agent* primitive its own `references/` | Most general; but expensive contract bump (RFC-0022/0026/0027 scale) for no gain — skills already carry references | Rejected — unnecessary |

Prior art for option 4: `adversarial-reviewer` (spec-stage mode wired into pre-EXECUTE), `quality-engineer` (multi-mode), and the work-loop's own on-demand `references/` loading — this is the established shape, not a new invention.

## Risks & what would make this wrong

**Pre-mortem.**
- *The orchestrator forgets to load the modules.* → Once D6's wiring lands, the work-loop step is **deterministic** (the loop instructs it), not model-relevance-judged. Note the firing is **new wiring** (the pre-EXECUTE review must be extended to dispatch security-reviewer on the security-boundary trigger — it does not fire there today), so the cost is real, not free. Mitigation: name the modules in the loop step explicitly.
- *The layered checklist re-bloats review.* → Modules are **scoped by boundary** (1–3 load per change, not 10); the universal agent body stays lean. Mitigation: the routing table caps what loads.
- *Maintenance drift as standards update annually.* → Modules are small and version-pinned in their headers; a yearly currency review is cheaper than a stale single list. Mitigation: name the standard+version in each module.
- *Spec-stage mode adds a pre-EXECUTE round on security work.* → Gated by the risk trigger (only security-boundary work); trades 3 cheap design sentences for the round-trips we measured. Accepted cost.
- *Checklist theater / displacement.* A richer, multi-framework, shift-left lens can invite operators to treat the *reasoning* pass as *coverage* — under-investing in the actual scanners (ADR-0017) or human review. → Mitigation: the "complements, does not replace scanners" non-goal, the three-bucket `tool`-delegation (which actively confirms scanners are wired), and the mandatory honest-limits "Not checked" footer all push against false confidence; this risk is named explicitly so the framing stays "reasoning above the tools," not "the tools."

**Key assumptions (falsifiable).**
- *Skills + `references/` project to every adapter.* — Verified: every adapter uses `mode = direct-directory` for skills (contract).
- *The orchestrator can load modules and inline them into a subagent brief.* — Verified: the work-loop already loads `references/*.md` on demand and dispatches reviewers with a constructed brief.
- *`AGENTS.md` is a universal convention source.* — Verified: it is the canonical file, read by Cursor/Codex/Copilot and bridged for Gemini.
- *Adapters with subagents also have auto-discoverable skills (the redundant convenience holds).* — Verified across Claude Code, Cursor, Copilot, Gemini, Codex, Kiro (agentskills.io open standard).

**Drawbacks.** Real cognitive + maintenance surface (a new skill + a second agent mode + loop wiring); a second review mode is a judgment call the model can mis-route; and the gate's fidelity to a given org's actual Snyk/scanner config can't be proven from source — it's a high-fidelity proxy, not the same engine.

## Evidence & prior art

**Spike / de-risk (done).** Riskiest assumption: the skill-library + orchestrator-routing actually ships and loads across all adapters. Spike: (1) contract grep — **every** adapter projects `skill` as `direct-directory` → `references/` travel everywhere; (2) web research — all six adapter *families* (Claude Code, Cursor, Copilot, Gemini, Codex, Kiro — Kiro ships as `kiro-ide` + `kiro-cli` sharing one skill projection) have subagents **and** auto-discoverable `SKILL.md` skills on the agentskills.io open standard; (3) residual risk — skill invocation is model-invoked → **mitigated** by orchestrator-driven deterministic selection (D2). Assumption holds.

**Repo precedent.**
- ADR-0017 (`docs/adr/0017-…`) — the SAST/SCA gate and the "scanners catch syntactic; the reviewer catches reasoning" split; the three findings that motivated this RFC landed under it.
- RFC-0025 / ADR-0014 — risk-triggered work-loop modes; the security-boundary trigger D3 reuses.
- `packs/core/.apm/agents/adversarial-reviewer.md` — spec-stage checks wired into pre-EXECUTE: the direct template.
- `packs/core/.apm/agents/quality-engineer.md` — multi-mode reviewer: precedent for adding a mode.
- `packs/core/.apm/skills/work-loop/SKILL.md` — on-demand `references/*.md` loading + reviewer dispatch: the exact mechanism D2 reuses.
- The Tier-1 declare/detect/fail-clean skill-prereq policy — the model for D4 tool-absence.

**External prior art** (each fetched/confirmed):
- [OWASP Top 10:2025](https://owasp.org/Top10/2025/) — A01–A10 incl. **A03 Software Supply Chain Failures**, **A10 Mishandling of Exceptional Conditions** (fetched; category list confirmed).
- [OWASP ASVS 5.0.0](https://owasp.org/www-project-application-security-verification-standard/) (released May 30 2025) — the verification standard (depth beyond the awareness list).
- [OWASP API Security Top 10:2023](https://owasp.org/www-project-api-security/) — BOLA/BFLA, the authz classes the web Top 10 underweights.
- [OWASP Proactive Controls 2024](https://top10proactive.owasp.org/archive/2024/the-top-10/) — C1–C10, the design-time control set for the spec-stage mode.
- `SKILL.md` as an open standard with subagents + auto-discovery on every target: [Cursor 2.4](https://cursor.com/changelog/2-4), [Copilot](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills), [Gemini CLI](https://geminicli.com/docs/core/subagents/), [Codex](https://developers.openai.com/codex/skills), [Kiro](https://kiro.dev/docs/cli/skills/).

## Open questions

1. **Module granularity** — the proposal consolidates to 10 modules (merging deserialization→injection, secrets-logging→split). If implementation finds two that always co-fire (e.g. `supply-chain` + `config-misconfig`), collapse them. Default: ship 10; consolidate only on observed redundancy. · owner: eugenelim · decide-by: implementation.
2. **`AGENTS.md` customization shape** — exactly how light the "blessed security tools/helpers" customization point is (a short list vs. a per-boundary table). Default: a short list + inference fallback, keeping `AGENTS.md` under its ~200-line budget. · owner: eugenelim · decide-by: implementation spec.

## Follow-on artifacts

On acceptance:
- **ADR** — record the decision to make security review progressive-disclosure + shift-left (a methodology decision worth an immutable record).
- **Spec** — `docs/specs/security-reviewer-shift-left/` (the new `security-checklists` skill + its 10 modules; the `security-reviewer.md` spec-stage mode + trim; the `work-loop` wiring; the `AGENTS.md` customization guidance).
- **Convention touch** — a light note in `docs/CONVENTIONS.md` (how-we-work) that security review runs at spec stage on security-boundary work, mirroring the adversarial spec-stage entry.
