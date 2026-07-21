---
name: new-rfc
description: Use this skill when the user asks to propose, draft, or open an RFC, OR when generating follow-on implementation artifacts (specs, ADRs) for an already-Accepted RFC. Triggers on "RFC", "propose a change to...", "let's get input on...", "draft a proposal", "create the follow-on specs for RFC-NNNN", "generate ADRs for the accepted RFC", "implement the follow-on work from an RFC". Do NOT use for recording a standalone architectural decision outside an RFC context (use `new-adr`), or for authoring a spec with no associated Accepted RFC (use `new-spec` for standalone spec authoring; for RFC follow-on work, invoke this skill first).
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
   to `NNNN-<kebab-title>.md`. **Keep the title short** — it should
   *identify* the proposal in a few words (`RFC-NNNN: Coordinator
   contract`), and the kebab filename follows it; the fuller explanation
   belongs in **The ask**, not the title. A title that carries the whole
   abstract makes the RFC index hard to scan. (Paths are skill-relative — the
   `assets/` folder lives next to this `SKILL.md` wherever your IDE
   installed the skill.) **Optional `NNNN-notes/` companion.** If the
   proposal rests on a sustained investigation, you may create a sibling
   `docs/rfc/NNNN-notes/` folder for the promoted research — a distilled
   brief, evidence, sketches — mirroring the `notes/` folder a spec carries
   (docs/CONVENTIONS.md § 3). It is optional; summarize its conclusions in
   `Evidence & prior art` and link the folder, rather than pasting the corpus
   into the RFC body.

3. **Guided shape/intake — offer, don't force.** Before researching, get the
   proposal's frame straight. Read the request:

   - **When the ask is already well-specified** (a clear change, a named
     surface, an evident motivation), *infer* the frame and proceed straight to
     research — don't make the author fill in a questionnaire they've already
     answered.
   - **When the intent is vague** (a direction, a complaint, "we should
     probably…"), ask a *small* set of framing questions — what outcome do you
     want · what's in and out of scope · what's the bet/risk — then synthesize a
     short proposal frame and reflect it back for confirmation before you spend
     research effort on the wrong target.

   Either way, **pick the `Decision weight`** (light | standard | heavy) for the
   RFC's header by reading `work-loop`'s risk triggers as a prose heuristic —
   reverses a frozen ADR/RFC, or a governance/charter/security boundary, or a
   one-way door → `heavy`; a reversible, narrow change → `light`; otherwise
   `standard` (the default). The weight right-sizes how much research depth (next
   step) and pre-handoff ceremony (the gate) the RFC carries — it never licenses
   dropping a gate check. Offer the frame; don't block on a form — a half-formed
   ask is normal input.

4. **Research + de-risk checkpoint — gated.** With the file scaffolded, stop.
   Don't write a single body sentence yet. A complex RFC is a tree, not one
   blob: research the *subpoints*, model the options out, and de-risk your own
   riskiest assumption before handing anything to a reviewer. A single shallow
   up-front sweep is the failure this replaces. **Scale the depth to the
   `Decision weight`:** a `light` RFC may need one focused sweep; `standard` and
   `heavy` get the full per-subpoint treatment below.

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
   - **Recommend per decision — and make each one decidable in this message.**
     Present enough per decision that the human can decide *here*, without
     opening a file: the question in plain language; the concrete options with
     their real trade-offs and what accepting each one costs; what repo
     precedent and external prior art suggest; and a recommended answer with
     one- or two-sentence reasoning + owner + decide-by. A bare list of option
     *names* is not decidable — give the trade-offs and the consequence of each.
     Cap genuinely-open questions at ~3.

   Emit the findings under exactly these headings. Each decision is
   self-contained — a reader decides from the block alone:

   ```
   RESEARCH FINDINGS:

   ## Decisions / subpoints
   1. **<subpoint — the decision, as a plain-language question>**
      - Options (MECE along <axis>, prior-art-grounded; always include do-nothing):
        - **<option A>** — <what it is, in plain terms> · trade-off: <what it
          buys vs. costs> · if accepted: <the concrete consequence>
        - **<option B>** — … · trade-off: … · if accepted: …
      - Recommendation: **<option>** — <one or two sentences of why, from the
        evidence below> · owner: … · decide-by: …

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

5. **Draft the body, answer-first.** Set the header fields, including the
   `Decision weight` you picked in step 3. Open with the **Reviewer brief**, then
   **The ask**; then route the findings: repo precedent → `Problem & goals` /
   `Evidence & prior art`; external precedent and the spike result →
   `Evidence & prior art`.

   **Reviewer brief — first-screen orientation, de-duplicated against The ask.**
   Fill the top-of-doc `## Reviewer brief` grid (Decision · Recommended outcome ·
   Change if accepted · Affected surface · Stakes · Review focus · Not in scope).
   It *orients* the reviewer's read; "The ask" *argues* the decision. Don't
   restate the BLUF in it — the two are different jobs. (This in-body brief is a
   distinct artifact from the chat-only `REVIEW READINESS` summary in step 6.)

   **Decisions as a table.** In "The ask", render *Decisions requested* as a
   table — one row per decision — `| ID | Question | Recommendation | Why |
   Decide by | Reviewer action |` — not numbered prose; the `Reviewer action`
   column names what the reviewer must do per decision (confirm X, rule on Y).

   **Body-as-argument split rule.** The RFC body is the *argument* a reviewer
   decides from — not an audit trail of your work. Keep a section in the body
   when it changes the reviewer's decision; when a section mainly demonstrates
   the work was done — full research transcripts, prior-art matrices,
   adversarial-review logs — summarize its conclusion in the body and move the
   detail to the optional `NNNN-notes/` companion (step 2). Default the body to
   the argument and link the proof.

   **Write for a cold reader — define coined terms on first use.** An RFC must be
   readable by someone who has *not* read the related RFCs. Every project-coined
   term, acronym, or back-reference to a sibling RFC gets a plain-language gloss
   the first time it appears in the body — **inline, in a few words, not in a
   separate glossary section**. Don't lean on vocabulary inherited from related
   RFCs as if the reader already holds it: a reviewer arrives at the RFC from the
   index, cold. (The cautionary case: an RFC that has to be hand-patched with
   inline glosses *after* drafting because the draft assumed its siblings' terms;
   the cold-reader check in the gate, step 6, exists to catch this before
   handoff.)

   Sections to push hardest on:
   - **Reviewer brief.** The fixed first-screen orientation grid, above The ask,
     de-duplicated against it (orients, doesn't argue).
   - **The ask.** The decision a reviewer must make, in plain language, on
     top — Recommendation (BLUF) + SCQA framing + the decisions table (one row
     per decision, each with a recommended option + decide-by + reviewer action).
   - **Problem & goals.** Diagnosis before solution; real **Non-goals**
     (could-have-been-goals deliberately dropped), not negated goals.
   - **Options considered.** MECE along a stated axis, each grounded in prior
     art, including do-nothing. If you can't articulate ≥2 genuinely distinct
     options, the proposal isn't honest yet.
   - **Risks & what would make this wrong.** Pre-mortem + falsifiable
     assumptions + drawbacks. If they say "no drawbacks", push back.
   - **Evidence & prior art.** Empty prior art is a finding (no one has done
     this) — surface it; never leave it blank or fabricated. Promoted research
     from a sustained investigation (e.g. a `desk-research`-pack project brief) can
     live in the optional `NNNN-notes/` companion; summarize and link it here.
   - **Open questions.** Each carries a recommended default + owner +
     decide-by; aim for ≤3.
   - **Experiment / validation** (optional). Only if the proposal needs an
     experiment: hypothesis + what you measure + success/failure criteria.
     Route *results* to a linked spike note, not the RFC body; once the RFC
     is circulating and the trial is actually running, it moves to
     `Experimental` while results are pending (a post-circulation state — see
     `docs/CONVENTIONS.md` § RFC lifecycle). Delete the section otherwise.

6. **Pre-handoff gate — mandatory, before status → Open.** Each item is
   *executed and its result recorded, never self-certified*. The `Decision
   weight` right-sizes how much *research and draft* each tier carries, **never
   whether a mandated check below runs**: a `light` RFC runs the full gate over a
   smaller draft (every check still fires — citations still fetched-and-confirmed,
   the `adversarial-reviewer` dispatch still mandatory and re-run until clean);
   `standard` is the full gate as written; `heavy` adds a mandatory de-risk spike
   and explicit Approver sign-off (no silent-default adoption). No tier drops or
   softens a check.
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
   - **Cold-reader readability check.** Dispatch a **generic** subagent in a
     fresh context, given **only the RFC text** and told *not* to read the
     project docs, `CLAUDE.md`/`AGENTS.md`, or sibling RFCs — its sole job is to
     list every term, acronym, or back-reference it cannot resolve from the RFC
     alone. Gloss each flagged item (step 5's cold-reader rule) before handoff.
     This is a *generic* dispatch with a context-denial prompt, **not** a named
     reviewer role, and it runs **in addition to** — never as a substitute for —
     the adversarial pass above (which loads project conventions by design and so
     cannot be the cold-reader instrument). If the harness offers no subagent
     dispatch at all, do the cold read in a fresh pass and note it rather than
     skipping silently.

   **Hand back a reviewer-friendly readiness summary, not a compliance dump.**
   The checks above are run to build the *reviewer's* confidence, so report
   their result as a short summary the reviewer can act on — and **link** the
   heavy proof (citation-fetch detail, the adversarial-review transcript)
   rather than pasting it into the RFC body or the handoff. Emit this **to chat
   at handoff** — it is a handoff artifact, **never an RFC body or template
   section**:

   ```
   REVIEW READINESS:
   - Decision clear: yes/no
   - Options include do-nothing: yes/no
   - Riskiest assumption tested: yes/no (+ link)
   - Citations checked: yes/no
   - Open questions owned: yes/no
   - Adversarial pass: clean | issues linked
   - Cold-reader check: clean | terms glossed | skipped (no subagent)
   ```

7. Set status to `Draft` until the user is ready to circulate, then `Open`.

8. Update `docs/rfc/README.md` table (create the file with the standard
   header row if absent).

## After acceptance

**Session-fragmentation guard.** Before generating any follow-on artifact,
check `workspace.toml` for each `spec/<path>` you are about to create (the
only artifact form the `[work]` queue accepts; ADRs and CONVENTIONS edits are
not checkable and stay in the follow-on artifact list below):

1. If `workspace.toml` is absent → skip this check silently and proceed to
   the prompt.
2. Scan all `status = "active"` initiative sections. For each spec path about
   to be created, check `[work].queue`, `[work].active`, and `[work].shipped`.
   Match both bare-string entries (`"spec/foo"`) and inline-object entries
   (`{path = "spec/foo", ...}`). If more than one initiative is active, the
   existing tie-break (ask which initiative) applies when appending in the
   prompt below (step 5).
3. Collect the absent spec paths — those not found in any of the three arrays.
4. If **all** spec paths are already present → skip this check silently and
   proceed to artifact generation.
5. If **any** spec paths are absent → run the prompt below, offering to queue
   the absent paths.

This guard fires for both the in-session case (RFC just moved to Accepted in
this session) and the follow-on session case (RFC was Accepted in a prior
session and you are now generating follow-on artifacts). Both cases reach the
single shared prompt below — there is no separate in-session trigger. If the
user declines the prompt, paths remain absent; a subsequent same-session
invocation will re-prompt over the still-absent paths.

When the guard fires, offer to queue the missing follow-on implementation work
in `workspace.toml`:

**Prompt the user:** "Add implementation specs to `workspace.toml` queue?"

- **If yes:** check for `workspace.toml` in the working directory.
  - **If present:** read the target initiative section (`["<initiative-slug>"]`).
    If the section is absent, ask the user to confirm the initiative slug and
    offer to create the section with an empty `[work].queue` before appending —
    do not silently skip and do not auto-create. Help the user add entries in
    the `{path = "...", needs = "..."}` inline-object format (see
    `docs/product/workspace-toml-deps.md` for the full entry format and prefix
    notation). If
    `[work].queue` already contains an entry for the same path, surface the
    duplicate and ask whether to add anyway or skip. Stage the file. If
    `workspace.toml` has more than one `status = "active"` initiative section,
    ask which initiative's queue to append to.
  - **If absent:** emit the literal note
    "workspace.toml not found — add the entry manually when Batch 2 lands"
    and continue to the follow-on artifact list. No error or exception.
- **If no:** leave `workspace.toml` unchanged and continue to the
  follow-on artifact list.

Then present the *follow-on artifacts* section — the queue-write step is
additive; the following list runs unchanged:

- One or more ADRs to record the architectural decisions.
- One or more specs in `docs/specs/` for features.
- Edits to `docs/CONVENTIONS.md` if the RFC changes conventions.
- **Phase-slice sequencing (multi-phase RFCs only):** when the RFC covers multiple journey phases, confirm that each phase's roadmap includes its guide(s). Guides ship with the phase that introduces their capability — not in a terminal documentation wave. A phase entry in `workspace.toml` or the RFC's roadmap that ships tooling without a `docs/guides/` artifact is an incomplete slice; name the missing guide in the follow-on spec or as a `workspace.toml` queue entry.

The RFC itself is then "done" and stays as historical record.

## Recording corrections (Errata / Amendments)

An RFC's body freezes, but the proposal can still need a correction after it
publishes — a spec finds a gap, a later RFC reframes a decision. Record the
correction *inside the RFC*, in one of two sections chosen by the RFC's
lifecycle class (the Document-lifecycle table in
`docs/CONVENTIONS.md` § Document lifecycle — Frozen vs. Governance), **never**
by editing the frozen body:

- **`## Errata`** — for a **Frozen** RFC (Accepted or Rejected). The body is
  immutable; corrections are appended here, Approver-signed. This is the common
  case — most corrections are found after acceptance.
- **`## Amendments`** — for an **in-flight** RFC (Open / Governance class) that
  needs to track reconciliations *while still being worked*, without rewriting
  its body. The rare case.

The heading itself signals whether the text beneath it is immutable, so the two
never coexist in one RFC: an Open RFC carrying `## Amendments` renames the
section to `## Errata` if and when it is Accepted (a status-driven edit the
Frozen rule already permits).

### The two-layer structure — optional, threshold-gated

A single one-line erratum stays a plain dated bullet. Split the section into two
layers **only once it crosses the threshold — more than one entry, *or* any
entry supersedes another** — at which point a reader can no longer recover the
present rules without diffing the whole log by hand:

```
## Errata            (or ## Amendments)

### Current state
<an authoritative summary — usually a table — of the corrections in force:
 "read this, not the log", for the present contract>

### History / audit trail
<dated entries explaining how each correction was reached>
```

- The **current-state** layer is the authoritative present contract. **Where it
  disagrees with a historical entry, the current-state layer wins** — say so in
  the section so a reader knows which layer to trust.
- The layer *names* above are illustrative; the contract is the two-layer split
  (authoritative current state over a dated audit trail), not the exact heading
  wording. One worked precedent uses "Current reconciliation state" over an
  "Amendment history / audit trail."

### Append-only and supersession

- Correction sections are **append-only**. A later entry supersedes an earlier
  one simply by being later; the **newest entry plus the current-state layer**
  carry present truth. Earlier entries are never deleted — they *are* the audit
  trail.
- **No per-entry ritual is required.** On a Frozen RFC's `## Errata`, prior
  entries cannot be reworded anyway (immutable body). On an in-flight
  `## Amendments`, an author *may* optionally reword a stale entry in place,
  tagging it `*(Superseded: …)*` — permitted, not required, and **only for
  in-flight Amendments** (a Frozen RFC's entries can't be touched).
- **Whole-RFC replacement is out of scope.** When an entire RFC — not one
  correction within it — is superseded by a later one, record that as an
  **Errata entry naming the superseding RFC** (e.g. an RFC carries an erratum
  recording that its Alternative #7 was superseded by a later RFC). This convention
  governs corrections *within* an RFC; it neither defines nor changes the
  whole-RFC-supersession mechanism.

## Anti-patterns to refuse

- Writing into the RFC body before the checkpoint clears → see step 4.
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
- Padding the RFC body with proof-of-work — full research transcripts,
  prior-art matrices, adversarial-review logs — that belongs in the optional
  `NNNN-notes/` companion → the body is the argument; summarize the conclusion
  and link the detail.
- A title that carries the whole abstract → shorten it to *identify* the
  proposal; the explanation lives in **The ask**, and a scannable RFC index
  depends on it.
- Leaning on vocabulary inherited from sibling RFCs — a coined term, acronym, or
  back-reference the cold reader can't resolve — without glossing it on first use
  → the reviewer arrives from the index, not from the related RFC; define it
  inline (step 5), and let the gate's cold-reader check (step 6) catch what you
  missed.
- Handing the human a decision too terse to decide from — a bare list of option
  *names* with no trade-offs and no consequence-of-each → the research phase
  already produced the trade-offs; put them in the chat handoff so the decision
  can be made in the message, not after opening files (step 4).
