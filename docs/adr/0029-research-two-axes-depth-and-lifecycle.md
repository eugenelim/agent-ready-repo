# ADR-0029: Research pack structure — two orthogonal axes (depth × lifecycle), with a prompt-only project mode

- **Status:** Accepted
- **Date:** 2026-06-22
- **Areas:** knowledge, packaging
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0039 (the accepted decision this records);
  `docs/rfc/0039-notes/survey-managing-research-projects.md`
  (four-discipline evidence); RFC-0038 (MADR-aligned ADR template)

## Context

The `research` pack scaled along one axis only: **depth** — `quick` / `standard` / `applied` / `deep`, all one-shot, each producing a single `research.md`. That serves a one-shot question well.

A sustained, multi-source investigation is a different kind of object: you gather sources over days or weeks, manage a growing corpus, digest it, and form and revise a working hypothesis toward an actionable verdict. The pack had nowhere for that to live — it jumped `sources → research.md` in one hop, with no middle/digest layer, no corpus management, no stop signal, and one generic filename that collides across investigations.

Constraints in force when deciding:
- **Charter Principle 3 (a habit, not infrastructure).** Pack primitives are prompt-driven file operations. No runtime engine, daemon, or index is permitted.
- **Charter Principle 1 (universal across stacks).** The pack ships to six adapters (Claude Code, Kiro, Codex, Copilot, Cursor, Gemini); it cannot hardcode one project's storage layout.
- **Charter Principle 2 (substantive, not duplicative).** The pack already has seven skills; anything new must add what they don't.
- **Prior art.** A four-discipline survey (PRISMA/Cochrane, Zettelkasten, grounded theory, intelligence-analysis ACH) found all four independently separate raw → working/digest → synthesis with distinct *named* artifacts and a stop signal. llm-wiki-kit v1 (commit `98bfef5`) implemented a comparable research lifecycle as pure prompt-driven phase skills — proving the discipline needs no engine.

## Decision

> We will structure the `research` pack as **two orthogonal axes — depth (one-shot: quick/standard/applied/deep) × lifecycle (episodic vs project)** — and implement "project" research as a **stateful, prompt-only, three-layer discipline** (raw capture → a constructed-column digest layer → a typed synthesis), not as another depth tier and not as a deferral to an external tool.

- **D1:** The `research` pack is structured on two orthogonal axes — depth
  (quick / standard / applied / deep) and lifecycle (episodic vs project).
- **D2:** Episodic output is named `<topic-slug>-<type>.md`, with `research.md`
  retained as a legacy alias.
- **D3:** Project research is a folder, scratch and out-of-repo by default,
  holding `sources/` → `synthesis-matrix.md` + `memos.md` → a typed synthesis
  plus a single-file `<topic-slug>-brief.md` governance handoff.
- **D4:** Raw sources are never overwritten.
- **D5:** Project mode is driven by a four-skill family carrying a passive
  stop-signal.
- **D6:** Implementation is prompt-only — `phase` is a frontmatter string the
  agent reads and writes, and the stop-signal is in-prompt judgment over the
  matrix, with no counter, derived metric, or engine.
- **D7:** The pack's existing seven skills are reused as phase operations, not
  rewritten.

Elaboration and boundaries:
- **Episodic** is today's one-shot behaviour; its output is named by topic + research type (`<topic-slug>-<type>.md`), with `research.md` retained as a legacy alias.
- **Project** is a folder — **scratch / out-of-repo by default** — holding `sources/` (raw, never overwritten) → `synthesis-matrix.md` + `memos.md` (the digest layer) → a typed synthesis + a single-file `<topic-slug>-brief.md` governance handoff, driven by a four-skill family with a **passive** stop-signal.
- **Prompt-only is a hard boundary:** `phase` is a frontmatter string the agent reads/writes; the stop-signal is in-prompt judgment over the matrix — no counter, no derived metric, no engine.
- Scope: this records the pack's *structure*. The existing seven skills are reused as phase operations, not rewritten.

## Decision drivers

- **Prompt-only / habit-not-infrastructure (Principle 3)** — the hard gate; rules out any engine, index, or daemon for corpus management or stop-signalling.
- **Universality (Principle 1)** — rules out hardcoding a storage layout; the layout is config-driven with a scratch default.
- **Fidelity to how sustained research is actually managed** — the convergent three-layer pattern; rules out the one-fat-file shortcut.
- **Substantive, not duplicative (Principle 2)** — the digest middle layer is the genuinely new capability; project skills must add state + lifecycle that episodic cannot.
- **Fit to messy material over up-front opinionation** — drove the folded sub-decision to use **constructed/emergent digest columns over fixed pillars** (see Consequences → revisit).

## Consequences

**Positive:**
- The pack can support its highest-value use case — sustained multi-source decisions — without leaving the prompt-driven model.
- The previously-missing middle layer makes corpus growth tractable: you reason over the digest, not by re-reading every source.
- Typed, topic-named outputs end `research.md` collisions and self-describe.
- Scratch default + the single-file brief give a clean scratch → governance promotion: a code repo commits the *decision*, not the corpus.

**Negative:**
- Four new skills enlarge the pack surface, against the catalogue's bias toward few sharp primitives; `-synthesize`/`-check` are the thinnest and rest on a state-transition justification the spec must defend.
- A folder + lifecycle is more for an adopter to learn than a single file.
- Constructed columns ask more judgment of the agent than a fixed template.

**Neutral / to revisit:**
- **Emergent-vs-fixed columns** is the one call without empirical backing. RFC-0039's Experiment validates it across the first 2–3 real projects; if agents need a fixed scaffold for coherence, that flips via a *superseding* ADR — it is not edited here.
- Whether `-check` may lightly write `verdict_status` (RFC-0039 open question) is settled at spec time.

**Revisit if:** RFC-0039's Experiment finds across the first 2–3 real projects that agents need a fixed digest scaffold for coherence, which flips the constructed-column call behind D3 and D6 — by a superseding ADR, not an edit here.

## Confirmation

- **Mode:** spec acceptance criteria + reviewer-checked.
- **Signal:** the project-mode spec's acceptance criteria encode the three-layer folder (D3) and the prompt-only constraint (D6), and adversarial + quality review checks that no runtime engine creeps in; skill-authoring review confirms the new skills stay prompt-driven file operations (no engine; dependency discipline per the skill-prereq policy); the emergent-columns validation (RFC-0039 § Experiment) is the periodic check on that sub-decision.
- **Owner:** eugenelim.

## Alternatives considered

- **"Project" as another depth tier (a fifth, deepest mode)** — rejected against *fidelity to how sustained research is actually managed*: depth is one-shot, and a lifecycle state machine cannot ride a depth parameter.
- **One fat `research.md` per project** — rejected against *fidelity to how sustained research is actually managed*: no raw/synthesis separation, the exact anti-pattern every surveyed discipline rejects.
- **Flat typed files, no enclosing folder** — rejected against *fidelity to how sustained research is actually managed*: it gives the naming win but no project boundary, phase, or stop-signal for a growing corpus.
- **Defer to an external tool/vault** (Obsidian, llm-wiki-kit) — rejected against *universality (Principle 1)*: it abandons portability and the pack's GRADE/triangulation evidence rail.
- **Fixed pillars for the digest layer** (llm-wiki-kit v1's entities/attributes/mental-model/verdict) — rejected against *fit to messy material over up-front opinionation*: procrustean for causal and prior-art questions, so constructed columns were chosen pending validation.
- **A runtime engine/index** to compute saturation and manage the corpus — rejected against *prompt-only / habit-not-infrastructure (Principle 3)*: that is infrastructure, not a habit.

## References

- RFC-0039 — Research project mode + typed, topic-named artifacts (the accepted decision this ADR records).
- [`docs/rfc/0039-notes/survey-managing-research-projects.md`](../rfc/0039-notes/survey-managing-research-projects.md) — the four-discipline applied survey (PRISMA/Zettelkasten/grounded-theory/ACH) behind the decision.
- llm-wiki-kit v1 — [github.com/eugenelim/llm-wiki-kit](https://github.com/eugenelim/llm-wiki-kit), commit `98bfef5` — prior art proving the lifecycle works as prompt-only phase skills.
- RFC-0038 — MADR-aligned ADR template (this ADR's shape).
