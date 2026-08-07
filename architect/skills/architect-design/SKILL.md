---
name: architect-design
description: Use when the user is framing a problem, weighing a technical choice, or designing a system or integration without a diagram as the headline ask. Triggers on "how should we", "we need to", "what's the right way to build X", tech-selection, integration design, NFR trade-offs. Shapes a one-page concept first, then produces a Google-style design doc (TL;DR, context, goals/non-goals, proposal, alternatives, risks, rollout, open questions), 2-5 pages, with Mermaid inline, and converges it against review. Cloud well-architected by construction (AWS/Azure/GCP and primitives providers like Hetzner). Do NOT use when the ask is a diagram (use `architect-diagram`) or a critique (use `architect-review`).
---

# Skill: architect-design

Produce a Google-style design doc that names the problem, proposes a solution,
considers alternatives honestly, and surfaces the risks the proposer least wants
to write down — well-architected by construction, then converged against review.

## Output rendering

Rationale / narrative — Use short ## headings and 2–3 sentence paragraphs. Don't force narrative into a table.
Diagram / flow — For relationships or flow, emit a fenced ```mermaid block (it renders in chat and artifacts). If the surface is terminal-only, fall back to an ASCII box-and-arrow sketch.
Key–value / one record — For a single record's fields, use an aligned key: value list, not a two-row table.

## When to invoke

Before drafting, confirm:

1. The ask is *design*, not *drawing* — if the user wants a picture more than
   a proposal, route to `architect-diagram` (if installed) or tell the user
   to invoke a diagramming skill directly.
2. There is a *real choice* to make. If only one option is on the table and
   the user just wants it written up, the artifact is a project brief, not a
   design doc. Say so and offer to write a shorter brief instead.
3. The *audience* is human — peers, a tech-lead, an architecture review.
   Design docs are read; they are not configuration.

If any check fails, push back rather than proceeding.

## Procedure

1. **Frame the problem.** Ask only what is *genuinely missing* — what we're
   building, who's affected, why now, what would count as success. Skip
   anything the user already said. Three to five questions max; if the
   user can't answer one, flag it as an open question rather than blocking.

2. **Consult available knowledge surfaces.** Before shaping the concept,
   establish what enterprise context you can reach, and **state which surface
   you detected (or "none")** in the concept. **If** you detect an *internal*
   knowledge-retrieval surface this session (an enterprise-knowledge MCP tool,
   an internal CLI, an in-repo doc set — public web search does **not** count),
   load `references/knowledge-surfaces.md`, consult the design-relevant areas,
   and treat a single unconfirmed source as lower-confidence. **If not**, ask
   the user for the missing context and lower the confidence of any proposal
   that leaned on it — as you degrade when `desk-research` is absent. **Either way,
   never fabricate** landscape/standards/in-flight facts.

   **Ground the platform-service contract.** The never-fabricate rule extends to
   the binding contract of any managed service the design depends on. For every
   managed service on a **critical path**, ground its *binding* contract —
   non-configurable limits, scaling floors, cold-start behaviour, network /
   identity requirements — in an authoritative source: a curated platform skill
   for that vendor if one is installed; else the provider's official docs; else
   `desk-research`. Carry **source + confidence** on each load-bearing figure, and
   **lower the confidence and flag** any claim you could not ground. **Never
   assert a service contract from model memory** — a binding limit recalled
   wrong is the design miss that surfaces two days into the build, not at review.
   This is scoped to **load-bearing critical-path claims** (a limit the design
   actually depends on), not every service mention. On an unfamiliar managed
   surface with no platform skill installed, recommend installing one rather
   than guessing the number.

3. **Shape the concept first (Stage 0).** Before the full doc, draft a
   ≤½-page concept from `assets/concept.md` — problem + constraints, 1–2
   candidate shapes, provider / provider-class, top 2–3 prioritized quality
   attributes (rank by business-importance × architectural-risk) — and
   **wait for the user to agree the shape**. This is *shaping* (context +
   constraints + the choice), not the refused "just write the proposal
   section" advocacy (see Anti-patterns). Make it well-architected **by
   construction**: a named provider → `references/well-architected-pillars.md`
   (it routes a Hetzner-class **primitives** provider to
   `references/cloud-primitives.md`'s capability gaps); a **local-first** start
   → `references/local-dev.md`; in all cases name the tradeoff / sensitivity
   points (`references/tradeoffs-and-sensitivity.md`). **No provider** → still
   produce the concept, forcing no provider/pillar scaffolding. **No shipped
   reference fits the domain** → the leading-edge method
   (`references/leading-edge-domains.md`): flag novelty, compose with `desk-research`
   if present (degrade + lower confidence if absent), carry source + confidence.
   Routing has a second, **orthogonal axis — workload class**: when an LLM or
   agent is on the critical path — a **generative or agentic** workload (the
   design generates text on the path, calls tools, takes autonomous action, or
   runs an agent loop) — additionally load `references/lens-genai-agentic.md` and
   shape the concept against the tier(s) that apply. This is *additive to* the
   provider axis, not either/or — an agentic system on a named cloud loads
   **both** the provider pillars and the agentic overlay; a plain generative
   design (RAG/chat that only produces text) loads the overlay at its baseline
   tier only. The overlay itself gates which tiers bite — do not enumerate its
   concerns here.

   **Stage 0 is a valid stopping point — end with a receipt.** After the user
   agrees the shape, they may stop here; a concept does not oblige the full
   doc, and saving one never requires continuing to Stage 1. When the user
   stops (or asks to save the concept), offer to save it using the **same
   path resolution as step 7 below** — `assets/concept.md` written into
   `<output_dir>/<topic-slug>/` — then **emit a Stage-0 completion receipt**,
   exactly one of:
   - **Chat only** — `Result: chat only; no file was created.`
   - **Saved** — the exact absolute path written, plus one line naming what
     it contains (problem + constraints + candidate shape(s) + prioritized
     quality attributes).

4. **Draft inline.** Use the skeleton in `assets/design-doc.md` (load it
   when you start the draft). Sections in order: TL;DR (≤3 sentences),
   Context, Goals and Non-goals, Proposal, Alternatives Considered, Risks,
   Rollout, Open Questions. Embed Mermaid diagrams where structural
   reasoning genuinely needs a picture — not as decoration.

5. **Self-check against the rubric** in `references/design-doc-rubric.md`.
   Walk it line by line; fix what fails before showing the draft.
   Common failures:
   - Non-goals empty or unconvincing → load `references/alternatives.md`.
   - Alternatives are strawmen → load `references/alternatives.md` and
     redraft until each could have been chosen by a reasonable engineer.
   - No cross-cutting concerns named → load `references/nfr-checklist.md`.

6. **Converge against review.** After the full draft, run
   `references/convergence-loop.md`: obtain a review pass (from
   `architect-review` if installed, else your embedded rubric self-check),
   **auto-resolve mechanical findings without asking**, re-review, repeat to
   the pass cap / stasis escape. **Never auto-resolve a judgment finding** —
   surface the tradeoff / risk / low-confidence calls as explicit decisions.

7. **Offer to save — config-driven, per-effort folder.** Resolve where the
   design effort lands, in this order, **in this skill body**. Reading is
   **prompt-only** (Charter Principle 3): this skill reads a file and
   reasons about a path — there is no engine, index, daemon, or watcher
   behind it, and the only code that ever *writes* the layout file is the
   install-time append. See
   [`references/agentbundle-layout.md`](references/agentbundle-layout.md)
   for the `[architecture]` section's full schema.

   **Resolution order:**

   a. **Repo-root config** — read `./agentbundle-layout.toml`
      `[architecture] output_dir`. Repo-scope takes priority so that a
      project or team convention applies when you're in this repo. The
      file is **adopter-owned**, never shipped into a projected path:

      ```toml
      # agentbundle-layout.toml (adopter-created; optional)
      [architecture]
      output_dir = "docs/design"   # a base; per-effort folders are created under it
      ```

   b. **User-profile config** — read `~/.agentbundle/agentbundle-layout.toml`
      `[architecture] output_dir`. User-scope is the fallback — useful for
      a personal vault when no repo convention is set.

   c. **Two-branch elicitation** — when neither config resolves, ask which
      branch fits — never a silent default:
      - **Repo branch** — "Commit to this repo? Suggest: `docs/design/`
        (team-visible, version-controlled). Enter path or press Enter to
        accept:" On accept, write `output_dir = "<path>"` to
        `./agentbundle-layout.toml [architecture]`.
      - **Personal/vault branch** — "Write to a personal workspace (e.g.
        Obsidian vault)? Enter the absolute path. Example:
        `~/Documents/<VaultName>/design/` (no default)." On accept, write
        to `~/.agentbundle/agentbundle-layout.toml [architecture]`.

   **Once the base is resolved**, each design effort gets its own
   **per-effort folder**: `<output_dir>/<topic-slug>/` where `<topic-slug>`
   is a short (~2–5 word) kebab-case slug derived from the design doc's
   title. The design doc, diagrams, and notes all go inside that folder —
   not as a loose file beside it. A Stage-0 concept saved on its own (step 3)
   shares this same effort folder, so a later full doc lands beside it.

   **Anchor `output_dir` by the layout file's own location**, never against
   the ambient cwd: a **repo-root** file's `output_dir` is
   **repo-root-relative** (an absolute value is permitted but warn it as
   non-portable); a **user-profile** file's `output_dir` **must be an
   explicit absolute path** (`~`-anchored is fine), and a *relative* value
   there is an Ask-first deviation, never silently resolved.

   **Resolve, then surface, then write.** After anchoring, resolve `output_dir`
   to its **full absolute path** — `~`-expand it and **realpath-resolve it**
   so any symlink in the path is made visible and never silently followed
   out of the intended root — and **reject any `..` escape**. The `..`
   rejection and the realpath happen **after** anchoring, so a relative
   repo-file value that escapes via `..` (e.g. `output_dir = "../../etc"`)
   is caught regardless of which file supplied it; anchoring never blesses a
   `..`-bearing value as in-tree. Then **surface the resolved absolute path
   to the adopter before creating the effort folder** — the first write is
   always preceded by the path you are about to write under.

   **A repo-root-sourced `output_dir` that resolves outside the repo tree** —
   or whose resolution required following a symlink out of the intended root
   — is **untrusted-origin**: confirm the resolved absolute path with the
   adopter before writing.

   Saving is an offer, never automatic.

8. **Decision-moment prompt.** If the doc captures one or more discrete
   decisions (technology choice, structural commitment, interface
   contract), end with one sentence: *"<N> decision(s) here look
   ADR-worthy — capture them with your ADR skill?"* Don't couple to a
   specific ADR implementation; let the user route.

## Anti-patterns to refuse

- **"Just write the proposal section."** A proposal without context,
  non-goals, or alternatives is advocacy, not a design doc. Either write
  the full doc or write a project brief — name which.
- **Treating the Stage-0 concept as a stripped proposal.** The concept is
  *shaping* — context + constraints + the choice, the opposite of a proposal
  with those removed. Don't let it collapse into partial advocacy.
- **Pre-selected alternative pretending to be a choice.** If the user has
  already decided and wants the doc to look like deliberation, that is an
  ADR with a Context section, not a design doc. Push back.
- **Embedding diagrams the proposal doesn't reason about.** Every Mermaid
  block earns its place by being referenced from the prose. Decorative
  diagrams rot first.
- **Skipping risks because the proposal is "obvious".** No proposal is
  obvious to the person who will operate it in two years. Name at least
  three risks even when the proposer is bored of you.
