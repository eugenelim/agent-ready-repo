---
name: map-capabilities
description: Step 6 (terminal) of the PE six-step shaping sequence. Translates a committed bet into a Capability Map — L1 domain organisation, Wardley × strategic-criticality annotation, Build/Buy/Partner/Adopt disposition, and a Build-only suggested build sequence anchoring M3–M6 spec-writing. Run after `place-bet`. Triggers on "map our capabilities", "what do we need to build", "what's our build/buy split", "capability areas for this bet". Do NOT use for a single feature (use `frame-intent`) or to author a brief (use `lean-canvas` / `author-brief`).
---

# Skill: map-capabilities

Translate a committed bet into a structured Capability Map — so the team knows
exactly what capabilities the initiative implies, which to build versus
buy/partner/adopt, and in what order to build them.

## Output rendering

Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.

## When to invoke

Confirm scope is initiative or capability level, not a single feature or endpoint.
If clearly feature-scoped, name the altitude mismatch and redirect to `frame-intent`.
If altitude is genuinely ambiguous, ask.

## Procedure

**1. Intake.** Resolve `output_dir` via the three-tier config procedure (repo-scope
`agentbundle-layout.toml [product]` → user-scope → two-branch elicitation).
Realpath-expand; reject `..` escapes and symlink chains that exit the intended root.
Resolve slug from the active shaping queue entry; surface multiple candidates if they
exist; ask when none; never mint.

Check `<output_dir>/shaping/<slug>/bet.md`. If found: surface option, appetite,
and rationale as elicitation context. If absent: offer `place-bet` first; if the
PE declines, proceed on free-form vision — note "reduced traceability" in the
artifact frontmatter.

Check `<output_dir>/shaping/<slug>/situation-framing.md`. If found: carry its
Wardley capability assessments as pre-assessed entries. If absent: proceed on
bet — "proceed on bet" is the branch taken.

**2. Vision.** Elicit or confirm product vision (1–2 sentences naming the outcome
the initiative pursues). Record in `capability-map.md` frontmatter under `vision`.

**3. Domains and capabilities.** Propose candidate L1 domains derived from the
bet and vision; confirm with PE. When the bet is underdetermined, elicit more
context first. When elicitation yields zero capability areas after confirmation,
surface this and ask PE to expand scope — do not emit an empty artifact.

For each domain, elicit capabilities one at a time. Each entry has seven fields:
id (kebab-case stable slug), name, description (one sentence), Wardley stage,
strategic criticality, disposition, and dependencies (other capability ids, or empty).

Wardley stages: *Genesis* (novel/uncertain; explore); *Custom-built* (hand-crafted;
invest to differentiate); *Product* (standardised solutions exist; buy/adopt unless
differentiating); *Commodity* (utility; competing here is waste).

Strategic criticality: *Differentiating* (competitive advantage; prioritise Build);
*Parity* (table stakes; match market, don't over-invest); *Utility* (overhead;
minimise cost).

Disposition: *Build* (own full lifecycle; core to differentiation); *Buy* (commercial
licence; standard function); *Partner* (co-developed; shared governance); *Adopt*
(OSS/open-standard; no licence cost; carries maintenance obligation).

Default depth: L1. Elicit L2 only when the bet explicitly scopes a capability area.

After all entries: scan for Commodity + Differentiating pairs — surface each as a
"strategic tension", describe the mismatch, and require PE acknowledgement before
finalising that entry.

**4. Build sequence.** Collect Build-disposition capabilities. Order dependency-first,
then Wardley-informed (Genesis/Differentiating first; blockers before dependents).
Mark the section "recommendation not mandate". Non-Build capabilities appear in
domain tables only — their disposition is the action (buy / partner / adopt), not
a build task.

**5. Emit.** Write `<output_dir>/shaping/<slug>/capability-map.md` using
`assets/capability-map-template.md`. Surface the resolved absolute path before
writing; confirm before overwriting an existing file. Append "Next step readiness"
when `lean-canvas` / `author-brief` is not detected in available skills.

**6. Suggest workspace.toml transition.** Print the TOML snippet to transition the
slug. Direct PE to `capture-work` or manual edit. Do not write to `workspace.toml`.

## Anti-patterns to refuse

- Never use for a single feature — redirect to `frame-intent`.
- Never write to `workspace.toml` or a literal hardcoded path.
- Never mint a new slug.
- Never include Buy / Partner / Adopt capabilities in the suggested build sequence.
- Never fabricate domains from thin input — elicit more context first.
- Never produce a brief (`lean-canvas` / `author-brief` owns that hand-off).
