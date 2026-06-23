---
name: new-rfc
description: Use this skill when the user asks to propose, draft, or open an RFC (request for comments). Triggers on "RFC", "propose a change to...", "let's get input on...", "draft a proposal". Do NOT use for already-decided things (use `new-adr`) or single-feature specs (use `new-spec`).
---

# Skill: new-rfc

Open a new RFC in `docs/rfc/` from the template — **answer-first** (lead with
"The ask"), with a per-subpoint research-and-de-risk phase before drafting and
a mandatory self-review gate before handoff. The point: a reviewer gets a
steerable proposal with the decision on top and its options modelled out and
backed by research — not a pile of un-researched questions to rescue. Modeled
on `new-spec`'s assumption checkpoint, plus the per-decision recommendation
pass RFCs need and specs don't.

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
   installed the skill.) **Optional `NNNN-notes/` companion.** If the
   proposal rests on a sustained investigation, you may create a sibling
   `docs/rfc/NNNN-notes/` folder for the promoted research — a distilled
   brief, evidence, sketches — mirroring the `notes/` folder a spec carries
   (docs/CONVENTIONS.md § 3). It is optional; summarize its conclusions in
   `Evidence & prior art` and link the folder, rather than pasting the corpus
   into the RFC body.

3. **Research + de-risk checkpoint — gated.** With the file scaffolded, stop.
   Don't write a single body sentence yet. A complex RFC is a tree, not one
   blob: research the *subpoints*, model the options out, and de-risk your own
   riskiest assumption before handing anything to a reviewer. A single shallow
   up-front sweep is the failure this replaces.

   Work the proposal as decisions/subpoints, emitting findings *in chat* (not
   into the gated body):

   - **Decompose first.** Break the proposal into its decisions/subpoints. The
     research unit is the subpoint, not the whole RFC.
   - **Research each subpoint independently:**
     - *Repo sweep.* Grep `docs/CHARTER.md`, `docs/CONVENTIONS.md`,
       `docs/adr/`, `docs/rfc/`, `docs/specs/`, and `docs/architecture/` for
       precedent and conflicts the subpoint touches. Cite each hit with file
       path.
     - *External sweep.* If web search is available (`WebSearch` in Claude
       Code; the equivalent elsewhere), look up how comparable projects,
       languages, or processes handled this shape of problem (Rust RFCs, PEPs,
       IETF BCPs, internal RFCs from similar orgs). Cite each as a markdown
       link. If web search isn't available, say so explicitly rather than
       fabricating citations.
   - **Enumerate each option/scenario space to be collectively exhaustive
     (MECE) along a stated axis**, and **ground every option in prior art**
     (how have others taxonomised this?) rather than inventing categories. A
     small round count (e.g. exactly 3) with no exhaustiveness argument or
     sources is a smell to challenge, not a finish line. Always include
     do-nothing.
   - **Self-Ask.** Resolve research-answerable questions yourself and fold the
     answers into the findings — they should not reach the human as open
     questions.
   - **Spike the riskiest assumption.** Identify the one assumption that, if
     false, sinks the proposal; run a small/timeboxed check and report the
     result — or state explicitly why no spike is needed. Do your own
     experimentation; don't hand the reviewer an untested guess.
   - **Cite as you go.** When a sweep (or a research subagent) surfaces a
     source, fetch it and confirm it resolves *and* contains the borrowed
     claim before that claim enters the findings. Never pass an unverified
     citation through.
   - **Recommend per decision.** For each decision/subpoint: the question,
     what repo precedent suggests, what external prior art suggests, and a
     recommended answer with one-sentence reasoning + owner + decide-by. Cap
     genuinely-open questions at ~3.

   Emit the findings under exactly these headings:

   ```
   RESEARCH FINDINGS:

   ## Decisions / subpoints
   1. **<subpoint>** — options (MECE along <axis>, prior-art-grounded): …
      · recommendation: … · owner: … · decide-by: …

   ## Prior art (in repo)
   - …

   ## Prior art (external)
   - …

   ## De-risk
   - Riskiest assumption: … · spike result (or why none needed): …
   ```

   Then **wait for human confirmation, rejection, or revision per
   recommendation.** Do not write into *any* body section until the user has
   signed off. Accepted recommendations fold into the body; ones rejected
   without an alternative, or genuinely deferred, stay in `Open questions` —
   with a recommended default + owner + decide-by, never bare.

4. **Draft the body, answer-first.** Lead with **The ask**; then route the
   findings: repo precedent → `Problem & goals` / `Evidence & prior art`;
   external precedent and the spike result → `Evidence & prior art`. Sections
   to push hardest on:
   - **The ask.** The decision a reviewer must make, in plain language, on
     top — Recommendation (BLUF) + SCQA framing + numbered decisions, each
     with a recommended option + decide-by.
   - **Problem & goals.** Diagnosis before solution; real **Non-goals**
     (could-have-been-goals deliberately dropped), not negated goals.
   - **Options considered.** MECE along a stated axis, each grounded in prior
     art, including do-nothing. If you can't articulate ≥2 genuinely distinct
     options, the proposal isn't honest yet.
   - **Risks & what would make this wrong.** Pre-mortem + falsifiable
     assumptions + drawbacks. If they say "no drawbacks", push back.
   - **Evidence & prior art.** Empty prior art is a finding (no one has done
     this) — surface it; never leave it blank or fabricated. Promoted research
     from a sustained investigation (e.g. a `research`-pack project brief) can
     live in the optional `NNNN-notes/` companion; summarize and link it here.
   - **Open questions.** Each carries a recommended default + owner +
     decide-by; aim for ≤3.
   - **Experiment / validation** (optional). Only if the proposal needs an
     experiment: hypothesis + what you measure + success/failure criteria.
     Route *results* to a linked spike note, not the RFC body; once the RFC
     is circulating and the trial is actually running, it moves to
     `Experimental` while results are pending (a post-circulation state — see
     `docs/CONVENTIONS.md` § RFC lifecycle). Delete the section otherwise.

5. **Pre-handoff gate — mandatory, before status → Open.** Each item is
   *executed and its result recorded, never self-certified*:
   - **Citation-integrity protocol.** Every reference is fetched; it must both
     resolve and actually contain the claim or statistic it is cited for (a
     link that merely loads is not enough). Citations surfaced by a research
     subagent get the same treatment. If a claim can't be confirmed, downgrade
     or drop it. The rule is symmetric: *challenge* a citation by fetching it
     too — never by judging whether an identifier "looks real".
   - **Verify-before-you-assert.** Every checkable claim the RFC makes about
     *itself* (section/field counts, "lighter", "readable") is checked against
     the artifact, not asserted.
   - **Per-subpoint backing.** Each decision/subpoint is independently backed
     by research; each enumeration is MECE along a stated axis and prior-art-
     grounded, not invented.
   - **Completeness checklist (YES/NO).** Approver named? every decision
     carries a recommendation? do-nothing present? ≤3 owned open questions? no
     item is simultaneously a decided default *and* an open question? all
     internal cross-references resolve?
   - **Different-lens review.** Dispatch a subagent matching
     `adversarial-reviewer` (fresh context) — **mandatory**, re-run until it
     reports clean; add `security-reviewer` if the RFC touches a security
     boundary. If no such subagent is installed, note it in the summary
     rather than skipping silently.

6. Set status to `Draft` until the user is ready to circulate, then `Open`.

7. Update `docs/rfc/README.md` table (create the file with the standard
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
- A single shallow up-front sweep standing in for per-subpoint research on a
  multi-decision RFC → decompose and back each subpoint.
- Enumerating an option/scenario space by inventing a small round number of
  categories (e.g. exactly 3) with no exhaustiveness argument or prior-art
  grounding → make it MECE along a stated axis, and source it.
- Bare open questions with no recommended default + owner → if the question
  hasn't been searched against repo + external prior art, the research phase
  wasn't done. Send it back.
- Passing any citation — especially one surfaced by a subagent — into the
  draft without fetching the source and confirming the borrowed claim is in
  it (a link that resolves is not enough; this is the single most-documented
  LLM-drafting failure). Challenge a citation the same way — by fetching —
  never by judging whether an identifier "looks real".
- Asserting any self-claim or a "gate passed" status without having run the
  check.
- Empty `Evidence & prior art` while web search was available and comparable
  processes plainly exist → "we didn't look" isn't an answer. When web search
  *wasn't* available, say so explicitly under the heading and never fabricate
  citations to fill it.
