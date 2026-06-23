# Spec: llm-agent-agentic-boundary-extension

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0029 (the `security-checklists` skill + its `llm-agent` module this extends); ADR-0032 (the accepted decision that recorded this module extension as deferred follow-on work); the Shipped `agentic-well-architected-overlay` spec (whose coverage-parity record and deferred AC this closes)
- **Contract:** none <!-- pure-markdown skill reference content; no API/event/RPC surface -->
- **Shape:** mixed — skill reference-content authoring across two packs (`core` module + `architect` lens copies) plus reciprocal governance bookkeeping; no application LLD

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A `security-reviewer` reasoning about an agentic change gets **control-altitude
depth** for three agentic security boundaries — **execution isolation & blast
radius**, **inter-agent identity/privilege propagation**, and **memory
poisoning** — from the `security-checklists` `llm-agent` module, instead of
having to reason from cross-cutting standards (OWASP/STRIDE/LINDDUN) because the
module has no matching text. The module anchors these on the **OWASP Agentic Top
10** (tool misuse, identity/privilege abuse, memory poisoning) and on **OWASP
LLM04** (Data & Model Poisoning) alongside its existing OWASP LLM Top 10:2025
surface (LLM01/02/03/05/06/10). It keeps its established shape — the
`tool`/`hybrid`/`reason` delegation legend, the spec-stage proactive-control
section, the established-helper-bypass section, and the `llm-agent` row in the
`work-loop` boundary→module routing table all stand. As a result, the
`agentic-well-architected-overlay`'s design-altitude route-out for these three
boundaries lands on a **named module check** rather than on a deferred backlog
destination.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep the new checks at **control altitude** — what the reviewer verifies on a
  diff (the containment posture, the privilege-propagation control, the
  memory-integrity control) — complementing the overlay's design-altitude
  *naming* of the same boundaries, never restating it.
- Preserve the module's existing shape: the `tool`/`hybrid`/`reason` delegation
  legend, the **Spec-stage (proactive control)** section, the
  **Established-helper bypass** section, and the `work-loop` boundary→module
  routing-table `llm-agent` row (it must still resolve).
- Tag each new implementation check with a delegation bucket (`reason` /
  `hybrid` / `tool`) per the legend.
- Update the module's **Standards** line and the `security-checklists/SKILL.md`
  module-index anchor and frontmatter to name the added standards family (OWASP
  Agentic Top 10) and LLM04.
- Bump the `core` pack (`pack.toml` `[pack].version` + `.claude-plugin/plugin.json`
  in lockstep), run `make build-self FORCE=1` to refresh the `core` projection
  and `marketplace.json`, and add a `[Unreleased] → Added` changelog entry.
- Soften the overlay lens prose in **both** byte-identical copies
  (`architect-design` and `architect-review` `lens-genai-agentic.md`) so it no
  longer claims these three boundaries "reach beyond the module's current
  checks", and bump the `architect` pack in lockstep.
- Resolve the reciprocal records together: flip the overlay spec's deferred AC
  to `[x]`, remove its `(deferred:)` marker, and remove the
  `llm-agent-module-agentic-boundary-extension` heading from `docs/backlog.md` in
  the same commit (so no dangling marker and no orphan heading is left).

### Ask first

- Adding a new module file, or splitting `llm-agent` into multiple modules — the
  routing table and the reviewer brief assume a single `llm-agent` module.
- Any change to the `work-loop` boundary→module routing table beyond keeping the
  `llm-agent` row resolving unchanged.

### Never do

- Add **design-altitude** prose to the module (provider/topology shaping,
  framework selection) — that is the `architect` overlay's job; do not duplicate
  it here.
- Ship executable tooling, evals, a new reviewer agent, or a new skill (CHARTER
  Principle 3; the ADR-0023 three-reviewer ceiling).
- Edit the frozen RFC-0029 or ADR-0032 bodies.
- Add a new dependency, a new module boundary, or a new top-level directory.

## Testing Strategy

This is a skill reference-content change; verification is **goal-based** and
**manual QA**, with no TDD-mode logic.

- **The module carries the three new control-altitude checks, each
  delegation-tagged, and the standards surface is updated, with the four
  structural sections preserved** — *goal-based*: a `grep` confirms the three
  new check anchors, their `reason`/`hybrid`/`tool` tags, the updated Standards
  line / SKILL.md index / frontmatter, and that the legend, spec-stage,
  established-helper, and routing-table-row anchors are all still present.
- **Both lens copies stay byte-identical after the softening, the now-stale
  claims are gone, and the three boundaries are positively re-routed** —
  *goal-based*: `diff` the two copies (identical modulo the per-skill duplication
  note); a **negative** `grep` on byte-accurate substrings confirms `the module's
  current checks` and `surface catches up` no longer appear (the live source has
  `reach **beyond** the module's current checks` and a line-wrap before `surface
  catches up`, so the substrings — not the full phrases — are what match); and a
  **positive section-scoped read** of the rewritten "Routes into the security
  boundary" section confirms the three boundary names now sit among the concerns
  routed to a named `llm-agent` module check (a bare-token grep won't do — the
  tokens recur in the Tier B/C bullets and the source wraps
  `identity/privilege\npropagation` — so it is a scoped read corroborated by the
  negative grep).
- **The reciprocal records resolve consistently** — *goal-based*: the overlay
  AC's deferral marker for the `llm-agent-module-agentic-boundary-extension`
  anchor is gone, no `#llm-agent-module-agentic-boundary-extension` backlog
  heading remains, the overlay's coverage-parity note maps the three boundaries
  to named module checks, and `.claude/skills/work-loop/scripts/lint-spec-status.py --root .` passes
  (deferral-anchor and
  status invariants hold across the touched specs).
- **The extended module reads as usable control depth to its consumer** —
  *manual QA, exercised end-to-end*: the `security-reviewer` subagent — the
  actual consumer of this content — is run with the `llm-agent` module inlined
  into its brief against a representative **synthetic agentic snippet** (a
  code-execution tool, a delegation chain, a memory write), since this PR's own
  diff is pure prose with no agentic sink. Its report is recorded showing it
  reasons from the three new module checks (not from cross-cutting standards as a
  fallback). A passing grep alone does not satisfy this; the reviewer's verdict on
  the snippet is its own and is not a gate.

## Acceptance Criteria

- [x] **Execution isolation & blast radius is a named module check.** The
  `llm-agent` module's implementation-checks section carries a `reason`-tagged
  check for a tool that runs code or processes untrusted content: the reviewer
  confirms containment along the **three axes** that make the check actionable on
  a diff — **filesystem scope** (what paths the tool can read/write),
  **network egress** (can the sandbox reach internal services or the
  cloud-metadata endpoint — cross-referencing `outbound-ssrf`; this egress facet
  is `hybrid`, a scanner can find the flow but the reviewer judges the
  confinement), and **resource/time bounds** (CPU/memory/wall-clock caps) — and
  that blast radius is thereby bounded. This is *containment* (what a call can
  reach once made), distinct from *authorization* (who may call, LLM06). Anchored
  on **ASI02** (Tool Misuse & Exploitation) and **ASI05** (Unexpected Code
  Execution) of OWASP Top 10 for Agentic Applications:2026.
- [x] **Inter-agent identity/privilege propagation is a named module check.**
  The module carries a `reason`-tagged check that, across a delegation chain, a
  sub-agent does not inherit more authority than the spawning request should
  carry (the multi-agent confused-deputy) — anchored on **ASI03** (Agent Identity
  & Privilege Abuse) of OWASP Top 10 for Agentic Applications:2026.
- [x] **Memory poisoning is a named module check.** The module carries a
  `reason`-tagged check covering **both** ends of the persisted-memory boundary:
  the **write gate** — untrusted retrieved content or an injected past turn is
  attributed / trust-checked / quarantined *before* it is persisted into agent
  memory or a vector store (the place the reviewer actually intervenes) — and the
  **read side** — persisted context that does reach memory cannot silently steer
  later decisions. Anchored on **ASI06** (Memory & Context Poisoning) of OWASP Top
  10 for Agentic Applications:2026 and OWASP **LLM04** (Data & Model Poisoning).
- [x] **The standards surface names the added families.** The module's
  **Standards** line names **OWASP Top 10 for Agentic Applications:2026**
  (ASI02 / ASI03 / ASI05 / ASI06) and **LLM04** (previously omitted) alongside the
  existing LLM01/02/03/05/06/10; the `security-checklists/SKILL.md` module-index
  `llm-agent` anchor cell and the skill frontmatter description are updated to
  match.
- [x] **The module keeps its established shape, and the existing checks are
  untouched.** The `tool`/`hybrid`/`reason` delegation legend, the **Spec-stage
  (proactive control)** section, and the **Established-helper bypass** section are
  all still present; the three new checks are added to the implementation-checks
  section and each is delegation-tagged. The six existing checks keep their titles
  and delegation tags — LLM01/LLM06/LLM05/LLM02/LLM10 `reason`, LLM03 `tool` (the
  module's only `tool`-bucket check, which the new memory-poisoning provenance
  language must not silently absorb or re-tag) — verified by grep.
- [x] **The spec-stage proactive control covers the three boundaries at design
  altitude.** The module's **Spec-stage (proactive control)** section names the
  containment/isolation, privilege-propagation, and memory-integrity design-time
  questions (so the design-time pass verifies these have a control specified as an
  AC, not only the implementation pass) — extending, not replacing, the existing
  instruction-vs-data / least-privilege-tool-surface / confirmation-criteria
  framing. Grep-verifiable alongside the implementation-check anchors.
- [x] **The depth stays at control altitude.** The new checks describe what the
  reviewer *verifies* (containment, privilege control, memory integrity); they do
  not add design-altitude prose (provider/topology shaping, framework choice) —
  that remains the `architect` overlay's altitude.
- [x] **The `work-loop` boundary→module routing table still resolves.** The
  `llm-agent` row (prompts / model / tool exposure / MCP / model-output handling
  → `llm-agent`) is unchanged and still routes to this single module; no new
  module is added and `llm-agent` is not split.
- [x] **The overlay lens prose is softened in both copies.** Neither
  `architect-design/references/lens-genai-agentic.md` nor
  `architect-review/references/lens-genai-agentic.md` still asserts the three
  boundaries reach `**beyond** the module's current checks` or routes them out
  until the `surface catches up`; both now reflect that control-level verification
  routes to a named `llm-agent` check — verified by a negative grep on the
  byte-accurate substrings (`the module's current checks`, `surface catches up`)
  **and** a positive section-scoped read confirming the three boundary names now
  appear among the routed-to-a-named-check concerns. The design-altitude routing
  statement itself is preserved, and the two copies remain byte-identical (modulo
  the per-skill duplication note).
- [x] **The coverage-parity record is updated.** The
  `agentic-well-architected-overlay` spec's `notes/coverage-parity.md` maps
  execution isolation & blast radius, inter-agent identity/privilege propagation,
  and memory poisoning to **named `llm-agent` module checks** (no longer
  "design-altitude-only → backlog"), and the "Net-new boundaries reconciled"
  section reflects that the module now covers them.
- [x] **The overlay's deferred AC is closed and the backlog entry removed.** The
  `agentic-well-architected-overlay` spec's AC carrying the deferral marker for
  the `llm-agent-module-agentic-boundary-extension` anchor is flipped to `[x]`
  and that marker is removed — the **only** sanctioned edits to that
  Shipped/Frozen spec's AC line; its descriptive prose is **not** reworded
  (the body stays as the frozen record, the checkbox carries the current truth).
  The `### llm-agent-module-agentic-boundary-extension` heading is removed from
  `docs/backlog.md`, and the three `coverage-parity.md` route-out link cells are
  remapped (below) — all in the same commit, leaving no `(deferred:)` marker and
  no open backlog heading for this anchor. The anchor string legitimately
  *remains* in three places, which is correct provenance, not drift: this spec's
  own body and README index row (they name the item they close), and the
  **frozen** `agentic-well-architected-overlay/plan.md` historical prose (a Done
  plan; immutable, and a code-span mention, not a dangling hyperlink).
- [x] **The `core` pack version is bumped and projection refreshed.** `core`
  `pack.toml` `[pack].version` and `.claude-plugin/plugin.json` are bumped in
  lockstep, and `make build-self FORCE=1` refreshes the `core` `.claude/`
  projection and `marketplace.json` with no residual drift on `git status`.
- [x] **The `architect` pack version is bumped.** `architect` `pack.toml` and
  `.claude-plugin/plugin.json` are bumped in lockstep for the lens softening, and
  `marketplace.json` reflects it.
- [x] **A `[Unreleased] → Added` changelog entry** is added in the implementing
  PR (`docs/product/changelog.md`), naming the **`core` 0.4.14** `llm-agent`
  module extension as the primary change (with the `architect` 0.8.1 lens
  softening as the ride-along) — a distinct entry from the existing
  architect-0.8.0 overlay entry.
- [x] **The security-reviewer reasons from the new module checks.** With the
  extended `llm-agent` module inlined into its brief, the `security-reviewer`
  subagent is run against a representative **synthetic agentic snippet** (a
  code-execution tool, a sub-agent delegation chain, and a write into persisted
  memory) — since this PR's own diff is pure prose with no agentic sink to reason
  against — and its report is recorded (manual QA) demonstrating it reasons from
  the three new module checks (containment axes, privilege propagation, the memory
  write gate) rather than falling back to cross-cutting standards. The pass
  condition is that the report **cites the three new checks as the control depth**
  — not that the reviewer returns a particular verdict on the snippet (its verdict
  is its own judgment and is not gated here).

## Assumptions

- Technical: `llm-agent.md` anchors only on OWASP LLM Top 10:2025
  (LLM01/02/03/05/06/10) with no Agentic-Top-10 or LLM04 content; its shape is
  the Standards header + delegation legend + Spec-stage section + six
  implementation checks + Established-helper-bypass section (source:
  `packs/core/.apm/skills/security-checklists/references/llm-agent.md`, read
  2026-06-23).
- Technical: the module is loaded orchestrator-driven and inlined into the
  `security-reviewer` brief; the subagent has no Skill tool; the `llm-agent` row
  lives in the `work-loop` boundary→module routing table (source:
  `security-checklists/SKILL.md`; `work-loop/SKILL.md` routing table, read
  2026-06-23).
- Technical: `security-checklists/SKILL.md` names the module's anchor standard in
  both the frontmatter description and the module-index table row, so the
  standards update must touch both (source: `SKILL.md:3`, `:90`, read
  2026-06-23).
- Technical: the `architect` pack is **not** projected to this repo's working
  tree (user-scope-default); a version bump refreshes only `marketplace.json`
  aggregation, not a `.claude/` projection (source: `ls .claude/skills` shows no
  architect; self-host pack-scope precedent, confirmed 2026-06-23).
- Technical: `lens-genai-agentic.md` exists as two copies
  (`architect-design`, `architect-review`) that are identical modulo their
  one-line per-skill duplication note; the Tier B / Tier C bullets name the three
  boundaries at design altitude and the "Routes into the security boundary"
  section routes them out as reaching "beyond the module's current checks ...
  until the security module's agentic surface catches up" (source: lens files,
  read 2026-06-23; cited by section heading, not line range, since Draft-spec line
  numbers rot).
- Technical: the OWASP Top 10 for Agentic Applications:2026 is a released,
  peer-reviewed list (Dec 2025); execution isolation maps to ASI02 (Tool Misuse &
  Exploitation) + ASI05 (Unexpected Code Execution), inter-agent
  identity/privilege to ASI03 (Agent Identity & Privilege Abuse), memory poisoning
  to ASI06 (Memory & Context Poisoning) (source: OWASP Top 10 for Agentic
  Applications 2026, verified 2026-06-23). The ADR-0032 "still settling" caveat is
  correspondingly tightened — the list has shipped a v1.
- Process: the `agentic-well-architected-overlay` spec is Shipped/Frozen, so the
  **only** sanctioned edits to its deferred AC line are the checkbox flip
  (`[ ]`→`[x]`) and removal of the now-inapplicable `(deferred: …)` marker; the
  AC's descriptive prose is left as the frozen record (the checkbox carries
  current truth). This is the close-the-deferral gesture the deferral convention
  designs for, not a body rewrite (source: `CONVENTIONS.md` § Document lifecycle
  Frozen row + § 4 deferral token; adversarial-reviewer spec-stage finding
  2026-06-23).
- Process: the governance vehicle is a **plain spec** (no new RFC/ADR) — the
  decision to extend the module was already taken and recorded in Accepted
  RFC-0042 / ADR-0032; this spec executes the deferred backlog item those
  produced (source: `CONVENTIONS.md` §§ 2-3 lifecycle; ADR-0032 § Decision; user
  confirmation 2026-06-23).
- Process: the overlay lens prose is softened in this PR (the cross-pack
  expansion) and the Shipped overlay spec's deferred AC is flipped here, both
  user-approved (source: user confirmation 2026-06-23).
- Process: closed backlog items leave the backlog register; deferred markers and
  their backlog headings are removed together to keep `lint-spec-status.py`
  invariant (iv) satisfied (source: `docs/backlog.md` § maintenance rule;
  `CONVENTIONS.md` § 4 Spec metadata contract).
