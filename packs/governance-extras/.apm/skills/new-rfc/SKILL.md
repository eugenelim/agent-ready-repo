---
name: new-rfc
description: Use this skill when the user asks to propose, draft, or open an RFC (request for comments). Triggers on "RFC", "propose a change to…", "let's get input on…", "draft a proposal". Do NOT use for already-decided things (use `new-adr`) or single-feature specs (use `new-spec`).
---

# Skill: new-rfc

Open a new RFC in `docs/rfc/` from the template — with a research phase
before drafting, so reviewers don't get handed bare unresolved questions
the author hadn't yet looked into. Modeled on `new-spec`'s assumption
checkpoint, plus a per-question recommendation pass that RFCs need and
specs don't.

## When to invoke

Before invoking, confirm one of:

- The change touches multiple packages or affects external users.
- The change reverses a previous ADR.
- The change adds, removes, or modifies a top-level convention.
- The user explicitly wants discussion before implementation.

If the change fits inside a single package and breaks no public interface,
push back: a normal PR (or a spec, if it's a feature) is enough.

## Procedure

1. Find the next number. The bundled helper prints the next 4-digit
   ordinal — `0001` if no RFCs exist yet, max-plus-one otherwise. It
   parses the full digit prefix, so a `00099-foo.md` correctly yields
   `0100` (not `0010`):

   ```bash
   python3 scripts/next-ordinal.py docs/rfc
   ```

   (The script lives next to this `SKILL.md` under `scripts/`. Python
   is preferred over `ls | grep | sed | sort` so the snippet works the
   same way on native Windows, macOS, and Linux.)

2. Copy this skill's bundled `assets/rfc.md` into `docs/rfc/` and rename
   to `NNNN-<kebab-title>.md`. (Paths are skill-relative — the
   `assets/` folder lives next to this `SKILL.md` wherever your IDE
   installed the skill.)

3. **Research phase — gated checkpoint.** With the file scaffolded, stop.
   Don't write a single body sentence yet. The point of an RFC is to weigh
   a proposal against what's already been tried; bare unresolved questions
   handed to reviewers are research the author should have done first.

   Emit the findings *in chat* (not into the RFC file — the body is gated
   below) under the structure shown. Two sweeps and a synthesis pass:

   - **Repo sweep.** Grep `docs/CHARTER.md`, `docs/CONVENTIONS.md`,
     `docs/adr/`, `docs/rfc/`, `docs/specs/`, and `docs/architecture/`
     for precedent and conflicts — prior decisions the proposal touches,
     related specs, conventions the proposal would alter. Cite each hit
     with file path.
   - **External sweep.** If web search is available (`WebSearch` in
     Claude Code; the equivalent in other harnesses), look up how
     comparable projects, languages, or processes have handled this shape
     of problem (Rust RFCs, PEPs, IETF BCPs, internal RFCs from similar
     orgs — whatever maps). Cite each source as a markdown link. If web
     search isn't available, skip this sweep and say so explicitly under
     the heading rather than producing fabricated citations.
   - **Recommendations on unresolved questions.** For every question the
     user's intent raises (from the conversation that triggered this
     skill — the RFC body is still empty at this stage), surface: the
     question, what repo precedent suggests, what external prior art
     suggests, and a recommended answer with one-sentence reasoning.

   Emit the findings under exactly these three headings:

   ```
   RESEARCH FINDINGS:

   ## Prior art (in repo)
   - …

   ## Prior art (external)
   - …

   ## Recommendations on unresolved questions
   1. **Question.** …
      - Repo precedent: …
      - External prior art: …
      - Recommendation: …
   ```

   Then **wait for human confirmation, rejection, or revision per
   recommendation.** Do not write into *any* body section until the user
   has signed off. The scaffolded headers can stay; the bodies are gated.
   Recommendations the user accepts fold into the body; ones the user
   rejects without an alternative, or genuinely defers, stay in
   `Unresolved questions` — with the author's lean noted. Treat
   unanswered recommendations as deferred (same destination, lean kept).

4. Draft the body, now informed by the research. Route the findings:
   repo precedent lands as citations in `Motivation`; external precedent
   lands in `Prior art`. (The chat block split the two for legibility;
   the body has a single `Prior art` section.) Sections to push hardest
   on:
   - **Motivation.** Cite repo precedent where it argues for or against
     the proposal.
   - **Alternatives considered.** Including "do nothing." If the user
     can't articulate any, the proposal isn't yet honest.
   - **Prior art.** Land the external-sweep citations here. Empty prior
     art is a finding (no one has done anything like this) — surface
     that explicitly rather than leaving the section blank.
   - **Drawbacks.** If they say "none", push back. There are always
     drawbacks.
   - **Unresolved questions.** Each carries the author's lean from the
     research phase, even if the lean is "punt to reviewers."

5. Set status to `Draft` until the user is ready to circulate, then `Open`.

6. Update `docs/rfc/README.md` table (create the file with the standard
   header row if absent).

## After acceptance

When the RFC is accepted, the *follow-on artifacts* section should list
concrete next steps — usually:

- One or more ADRs to record the architectural decisions.
- One or more specs in `docs/specs/` for features.
- Edits to `docs/CONVENTIONS.md` if the RFC changes conventions.

The RFC itself is then "done" and stays as historical record.

## Anti-patterns to refuse

- Writing into the RFC body before the checkpoint clears → see step 3.
- Bare unresolved questions with no author lean → if the question
  hasn't been searched against repo + external prior art, the research
  phase wasn't done. Send it back.
- Empty `Prior art` while web search was available and comparable
  processes plainly exist → the external sweep produces this section;
  "we didn't look" isn't an answer. When web search *wasn't*
  available, the section can be empty — but say so explicitly under
  the heading and never fabricate citations to fill it.
