---
name: architect-review
description: Use this skill when the user pastes a design doc, diagram, or other architecture artifact and asks for a critique. Triggers on "review this", "what's wrong with…", "is this any good", or any artifact-shaped paste with a question attached. Produces a one-line verdict (SHIP IT / SHIP WITH CHANGES / MAJOR REWRITE / WRONG ARTIFACT), a 3-sentence executive summary, severity-tagged findings (🟥 / 🟧 / 🟨 / ⚪), and a closing "what's working" section. Inline only — no file write. Do NOT use to *produce* a design doc or diagram (use `architect-design` or `architect-diagram`); use this when the artifact already exists.
---

# Skill: architect-review

Critique an existing architecture artifact. Severity-tagged findings,
genre-aware rubric routing, no file write — reviews are throwaway
artifacts.

## When to invoke

Before reviewing, confirm:

1. There is an *artifact in scope* — pasted into the conversation,
   linked, or named at a known path. "Review our architecture" with
   nothing concrete attached is a design conversation, not a review.
2. The artifact is *finished enough to critique*. A two-bullet
   outline is a discussion; a draft with all the sections at least
   started is a review. Don't critique tumbleweeds.
3. The user wants *severity-tagged findings*, not a discussion. If
   they want a conversation, route to `architect-design` (if installed)
   or tell the user to switch to a design-conversation surface.

If any check fails, push back rather than reviewing.

## Procedure

1. **Identify the artifact type.** Read the paste; pick one:
   - Design doc (Google-style or close to it) → `references/rubric-design-doc.md`
   - C4 Container / Context diagram → `references/rubric-c4-diagram.md`
   - Sequence diagram → `references/rubric-sequence-diagram.md`
   - State diagram → `references/rubric-state-diagram.md`
   - ER diagram → `references/rubric-er-diagram.md`
   - Something else, or unclear → `references/rubric-generic.md`

   If the artifact is the *wrong shape for the question* — a sequence
   diagram when the user wanted topology, an ADR when the user wanted
   a design doc — flag it with the **WRONG ARTIFACT** verdict and
   route to the right skill.

2. **Walk the rubric.** Read every check; note the failures. Do not
   start writing findings yet — finish the rubric pass first so the
   findings can be ordered by severity, not by discovery order.

3. **Decide the verdict** before writing the findings:
   - **SHIP IT.** Zero blockers, ≤2 minors. Rare and worth saying so.
   - **SHIP WITH CHANGES.** Blockers absent or trivially fixable;
     majors exist but the artifact's shape is right.
   - **MAJOR REWRITE.** Two or more blockers, or one blocker that
     invalidates the artifact's structure.
   - **WRONG ARTIFACT.** The artifact answers a question the user
     didn't ask. Name the right artifact and route.

4. **Write the review** using the shape in `assets/critique.md`:
   - Verdict (one line).
   - Executive summary (≤3 sentences).
   - Findings, ordered by severity, each with: **where** (5–10 words
     quoted verbatim, or section + paragraph), **what's wrong** (one
     sentence naming the failed rubric check), **suggested fix**
     (concrete, paste-able where possible).
   - **What's working** (2–4 specific reusable strengths). Not
     flattery. Things the author should *keep* during a rewrite.

5. **No file write.** Render inline. If the user explicitly asks to
   save the review, write to a path they choose with a kebab-case
   slug — but the default is throwaway.

## Severity glossary

| Tag | Meaning | Example |
| --- | --- | --- |
| 🟥 blocker | Ship-stopping. Wrong, misleading, or unsafe to act on as-is. | TL;DR contradicts proposal; trust boundary unlabeled; alternatives are strawmen. |
| 🟧 major | Not ship-stopping but materially weakens the artifact. | NFRs missing; one alternative is a strawman; technology label missing on a Container. |
| 🟨 minor | Author should fix; reviewer won't block on. | Edge labels inconsistent; non-goal phrasing weak. |
| ⚪ nit | Style / formatting. Optional. | Capitalization, indentation, oxford-comma. |

## Anti-patterns to refuse

- **Reviewing your own draft from the same session.** If the user
  asked you to produce the artifact, reviewing it back yourself is
  marking your own homework. Push back and ask the user (or another
  agent) to drive the critique.
- **Writing a critique without a rubric.** Reviews without explicit
  rubric anchors read as opinion. Always cite the rubric check that
  failed.
- **Padding "what's working" with flattery.** "Clear writing" and
  "good structure" alone are filler. Name specific things the
  author should preserve.
- **Burying the verdict.** Verdict goes first. The reader should not
  have to scroll past 12 findings to learn the artifact is broken.
