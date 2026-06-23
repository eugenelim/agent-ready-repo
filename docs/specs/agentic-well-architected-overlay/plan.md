# Plan: agentic-well-architected-overlay

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change has two halves that meet at one shared file. **First, author the canonical expanded lens** (`lens-genai-agentic.md`) — reorganise the five shipped concerns into the progressive Tier A/B/C taxonomy and add the missing concerns (the Tier-B trust triad, output handling, execution isolation, reliability-under-non-determinism; the Tier-C memory/provenance/coordination set), keeping the route-to-`security-reviewer` boundary and the apply-what-bites instruction. **Second, wire it in at design time** — add the workload-class routing branch to `architect-design` Stage 0 so the (today dead) lens copy becomes live. The lens is duplicated per skill, so the canonical content is written once and mirrored byte-for-byte into both copies (modulo each copy's duplication note). The review side already routes to the lens, so it picks up the expansion for free; the only review-side task is a no-regression check.

The riskiest part is **content parity and altitude**: the security-boundary concerns must cover the `llm-agent` module's surface without sliding into control-level prescriptions the pack shouldn't own. That is the focus of the coverage-parity task and the security-reviewer pass. The routing branch itself is a small, well-bounded SKILL.md edit. Order: author the lens (T1), mirror it (T2), wire design-time routing (T3), then the parity/no-regression/version/dogfood checks (T4–T7).

This plan describes the **implementing PR**; the governance PR that introduces ADR-0032 and this spec/plan does not execute it.

## Constraints

- **ADR-0032** — the load-bearing decisions: design-and-review one-shared-file, workload-class as an orthogonal routing axis, progressive A/B/C taxonomy, graduated autonomy as engineering judgment, no new primitive, prose only.
- **RFC-0042** — D1–D5 and the open-question defaults (OQ1 OTel-with-caveat, OQ2 Tier-C gate split).
- **CHARTER Principles 2 & 3** — no duplication (no new skill), habit not infrastructure (no executable tooling/evals).
- **ADR-0023** — the three-reviewer ceiling (no fourth reviewer).
- **The pack's per-skill duplication shape** — both lens copies stand alone, each with a duplication note (`architect/README.md:54-57`).

## Construction tests

Most verification is per-task below. Cross-cutting checks that span tasks:

**Integration / cross-cutting checks:**
- **Both-copies-identical:** `diff` the two `lens-genai-agentic.md` files with their duplication-note lines normalised — they are otherwise byte-identical.
- **Coverage parity:** a reviewer-checkable mapping from each overlay security-boundary concern to a `security-checklists/references/llm-agent.md` item; no overlay security concern is unmapped, and the `llm-agent` surface is fully covered by the overlay's concern set.
- **No SKILL.md taxonomy inlining:** `grep` confirms `architect-design/SKILL.md` references the lens file but does not enumerate the Tier A/B/C concern list.

**Manual verification:**
- Dogfood `architect-design` end-to-end on one agentic concept and one plain-RAG concept; record what the skill loads and produces (T7).

## Tasks

### T1: Author the expanded progressive lens (canonical content)

**Depends on:** none

**Tests:**
- `grep` confirms the three tier headings (Tier A / Tier B / Tier C) and their gating instructions are present (AC: progressive taxonomy).
- `grep` confirms each named concern from the spec's Tier A/B/C ACs is present (injection, egress/disclosure, evaluation, token cost, observability; tool-authz+bounded-autonomy+intent-verification, tool/MCP source provenance, output handling, execution isolation, human oversight, auditability, reliability; memory integrity, sub-agent provenance, multi-agent/identity-propagation).
- `grep` confirms the Tier-C gate split is written as **distinct** triggers — memory & context integrity on *stateful*, sub-agent provenance + coordination/identity-propagation on *multi-agent*, tool/MCP source provenance on *Tier B* — not collapsed into one gate (AC: Tier-C gate split; tool/MCP provenance on Tier B).
- `grep`/read confirms each trust-triad item (human oversight/HITL, intent verification, auditable action trails) is its **own** named concern entry, not a sub-clause of the tool-authz or observability bullets (AC: trust triad first-class).
- `grep`/read confirms the Tier-B authz concern forces the explicit "tool allowlist + which actions require confirmation" question (AC: Tier B authz, the named design-time miss).
- `grep` confirms the Tier-C memory/poisoning concern carries the **LLM04** anchor, the Tier-A retrieved-content/embedding surface carries the **LLM08** anchor, and the Tier-A token-cost + Tier-B loop-cap concerns carry the **LLM10** anchor (AC: OWASP anchors; bidirectional parity direction (a) for LLM10).
- `grep` confirms the graduated-autonomy text names the irreversibility/blast-radius cap (incl. the partially-reversible default-to-gated case) and contains no "a standard requires/prescribes" claim about threshold-gated checkpoint removal (AC: engineering-judgment framing).
- `grep` confirms OTel GenAI conventions are named with a maturity caveat (AC: OQ1).
- `grep` confirms the route-to-`security-reviewer` / `llm-agent` block and the apply-what-bites instruction are retained (AC: altitude).

**Approach:**
- Start from the shipped `lens-genai-agentic.md`; regroup its five concerns under Tier A/B and add the missing concerns per the spec's Tier A/B/C ACs.
- Write the per-tier gating instruction (Tier A always; Tier B once the system acts; Tier C split — memory on *stateful*, provenance/coordination on *multi-agent*).
- Keep the "Distinct from the managed-platform diagram refs", "Routes into the security boundary", and "Use, don't recite" sections; extend the security-boundary section to enumerate the full Tier A/B/C security-boundary concern set that routes out.

**Done when:** the canonical lens text exists and all T1 greps pass against it.

### T2: Mirror the lens into both skill copies identically

**Depends on:** T1

**Tests:**
- `diff` of the two `lens-genai-agentic.md` copies (duplication-note lines normalised) is empty (AC: both copies identical).
- `grep` confirms each copy retains its own one-line duplication note pointing at the sibling skill (AC: per-skill duplication preserved).

**Approach:**
- Write the canonical content into `architect-design/references/lens-genai-agentic.md` and `architect-review/references/lens-genai-agentic.md`, preserving each file's existing duplication-note line.

**Done when:** the both-copies-identical cross-cutting check passes.

### T3: Add the workload-class routing branch to `architect-design` Stage 0

**Depends on:** T2

**Tests:**
- `grep` confirms Stage 0 (`SKILL.md:45-60` region) now references `references/lens-genai-agentic.md` behind an agentic-workload trigger (names tool-use / autonomous action / agent loop) (AC: routing axis exists).
- `grep` confirms the branch is additive to provider routing (the provider routing text is unchanged and the agentic branch loads alongside it) (AC: orthogonal axes).
- `grep` confirms the Tier A/B/C concern list is **not** inlined into `SKILL.md` (AC: routing branch is the only SKILL.md addition) — cross-cutting "no taxonomy inlining" check.

**Approach:**
- In the Stage 0 step, add a workload-class sentence parallel to the provider sentence: when the concept's workload is agentic, load `references/lens-genai-agentic.md` and shape against the applicable tier(s); the two axes are orthogonal.
- Keep the addition to one routing branch — no concern enumeration in the skill body.

**Done when:** the three T3 greps pass and the dead lens copy is now reachable from the procedure.

### T4: Bidirectional coverage parity with the `llm-agent` control module

**Depends on:** T1

**Tests:**
- The **bidirectional** parity mapping (cross-cutting check) holds: (a) every `llm-agent` control item (LLM01/02/03/05/06/10 + spec-stage proactive control) maps to an overlay concern, **and** (b) every overlay security-boundary concern resolves to a named `llm-agent` check **or** an explicit design-altitude-only status (AC: bidirectional coverage parity).
- The three net-new agentic boundaries (execution isolation, inter-agent identity/privilege propagation, memory poisoning) are each named at design altitude **and** carry the deferred backlog pointer `llm-agent-module-agentic-boundary-extension` (AC: net-new boundaries reconciled).

**Approach:**
- Build the concern↔module mapping both ways; for each overlay security concern with no `llm-agent` check, mark it design-altitude-only and confirm the deferred backlog entry covers the module extension.
- Confirm the lens routes control-level verification out (names the boundary only), not control prescriptions.

**Done when:** the bidirectional mapping is complete — no `llm-agent` control unmapped, and every overlay security concern resolves to a check or a recorded design-altitude-only status with a backlog pointer.

### T5: Confirm `architect-review` WA-mode routing is unregressed

**Depends on:** T2

**Tests:**
- `grep` confirms `rubric-well-architected.md` still selects `lens-genai-agentic.md` for the GenAI/agentic workload class, with its concern-lens × workload-class axes intact (AC: review-side route preserved).
- `grep` confirms the rubric's ML / SaaS / serverless workload-class entries are **unchanged** — still named, still unbacked (AC: ML/SaaS/serverless remain named-but-unbacked, the status-quo half).

**Approach:**
- Read `rubric-well-architected.md`'s lens-selection section; verify the GenAI/agentic route is unchanged and now resolves to the expanded shared file, and that ML/SaaS/serverless are still named without backing files.

**Done when:** the rubric routes to the expanded lens with no edit required (or a one-line pointer fix if the route drifted), and ML/SaaS/serverless are confirmed unchanged.

### T6: Bump the `architect` pack version and refresh projection

**Depends on:** T1-T5

**Tests:**
- `grep`/build confirms `pack.toml` `[pack].version` and `plugin.json` are bumped in lockstep and the projection (`.claude/skills/architect-*`, marketplace aggregation) is regenerated and drift-clean (AC: version bump).

**Approach:**
- Bump `packs/architect/pack.toml` and the pack's `plugin.json`; run the pack build/projection; confirm the build-check drift gate is clean.
- Add the `[Unreleased] → Added` changelog entry (AC: changelog).

**Done when:** the version is bumped in both files, projection is drift-clean, and the changelog carries the entry.

### T7: Dogfood the overlay end-to-end

**Depends on:** T3, T6

**Tests:**
- Manual QA: run `architect-design` on an agentic concept (tool-using) — record that the workload-class branch fires, the lens loads, and the applicable tier(s) gate as intended.
- Manual QA: run `architect-design` on a plain-RAG concept — record that only Tier A applies (the branch does not drag in Tier B/C).

**Approach:**
- Exercise the built skill the way a user would; capture the observed behaviour (what loaded, what tiers applied) in the PR description.

**Done when:** both runs are recorded and show the routing fires for the agentic concept and stays Tier A for the RAG concept.

## Rollout

Pure skill-prose / reference-content change. **Delivery:** ships with the next `architect` pack release (version bumped in T6); reversible by reverting the routing branch and lens edits. No infrastructure, no external-system integration, no deployment sequencing. **Irreversible:** none. Adopters pick up the expanded overlay on pack upgrade.

## Risks

- **Coverage parity drifts as OWASP moves.** The overlay and the `llm-agent` module can diverge over time. Mitigation: the parity criterion is an AC and a reviewer-checked mapping; the route-out boundary means the module stays the control source of truth.
- **Routing over-fires**, tagging every LLM feature "agentic." Mitigation: the trigger is the system *acting*; Tier A is the explicit non-acting baseline, so over-firing costs at most Tier A. Exercised in the T7 RAG dogfood.
- **Altitude creep** — the expanded security-boundary content slides into control-level prescriptions. Mitigation: the security-reviewer pass and the Always-do/Never-do boundaries; the lens names boundaries and routes controls out.
- **The two copies drift** during authoring. Mitigation: the both-copies-identical cross-cutting check; a possible follow-up governance lint (noted in ADR-0032, not required here).

## Changelog

- 2026-06-23: initial plan (governance PR — ADR-0032 + this spec/plan). Implementation deferred to a separate PR.
