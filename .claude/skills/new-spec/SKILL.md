---
name: new-spec
description: Use this skill when the user wants to start a new feature with a spec, or wants to write a spec for something they're about to build. Triggers on "new spec", "write a spec for X", "let's spec this out", "start a feature for…". Spec-driven development; the spec drives implementation. Do NOT use for cross-cutting proposals (use `new-rfc`) or recording decisions (use `new-adr`).
---

# Skill: new-spec

Create a new feature spec under `docs/specs/<feature>/` with both `spec.md`
and `plan.md`.

## When to invoke

The spec is the contract; the plan is the strategy. Even a one-day feature
benefits from a one-paragraph spec — it forces the question "what does done
look like?" before any code.

## Procedure

1. Pick a kebab-case feature name from the user's description. Keep it short
   and noun-y: `user-onboarding`, `webhook-retries`, not
   `improve-the-onboarding-experience`.

2. Create the directory and copy this skill's bundled `assets/spec.md`
   and `assets/plan.md` into it as `docs/specs/<feature>/spec.md` and
   `docs/specs/<feature>/plan.md`. (Paths are skill-relative — the
   `assets/` folder lives next to this `SKILL.md` wherever your
   installer placed the skill.)

3. **Surface assumptions before writing any spec body — and run one
   targeted verification check per candidate first.** With the
   directory scaffolded, stop. The load-bearing rule: **one targeted
   check per candidate assumption — a repo read, a web lookup, or a
   read-only probe script — not a sweep.** Then split the result into
   what you confirmed and what still needs the user.

   Draft candidates covering the three categories below, generated
   from this repo's actual context — the template serves multiple
   project types, so don't carry assumptions across features:

   - **Technical** — runtime, data model, persistence, deployment
     target, transport. Canonical sources: package manifests
     (`pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, etc.),
     build / orchestration configs (`docker-compose.yml`, CI
     workflows), and the module the feature touches.
   - **Product** — who this serves and where the feature ends. No
     canonical local source; goes straight to Unverified. Don't
     fabricate confirmation.
   - **Process** — review cadence, who signs off on **Boundaries**
     (especially the `Never do` subsection), how the spec moves Draft
     → Approved. Canonical sources: `docs/CHARTER.md`,
     `docs/CONVENTIONS.md`, recent `docs/specs/<feature>/spec.md` for
     shape precedent, prior ADRs / RFCs that named the rule.

   See the **Source of truth** table in `AGENTS.md` for the full repo
   map. For assumptions about an external library, standard, service,
   or runtime behavior, the right source is a **web search** (cite
   the URL) or a **read-only probe script** (paste the command and
   its output) — e.g. `python -c "import x; print(x.__version__)"`,
   a `GET` on a list endpoint, `git --version`. **Probes must be
   side-effect-free** against any external service: no writes, no
   mutations, no calls that bill or page. If the only way to verify
   is to write, the assumption stays Unverified. **If web search
   isn't available in the harness**, mark the assumption Unverified
   with `(web search unavailable)` — never guess a URL.

   Emit the result **in chat** (not into `spec.md` — the body is
   gated below), under this shape:

   ```
   ASSUMPTIONS I'M MAKING:

   ## Verified
   - <category>: <fact> (<single-line citation: path | URL | command + one-line summary>)
   - …

   ## Unverified
   - <category>: <open item or reason it couldn't be settled>
   - …
   ```

   Each Verified bullet stays single-line. If a probe's output is too
   long to summarise in one line, paste the full transcript in a
   fenced block *above* the `ASSUMPTIONS I'M MAKING:` heading and
   reference it from the bullet (e.g. `(probe #1 above: returned True)`).

   Example Verified entries:
   `Technical: runtime is Python 3.12 (pyproject.toml)`,
   `Technical: HTTP client is undici 6.x (package.json)`,
   `Process: top-level convention changes need an RFC (docs/CONVENTIONS.md §Living-docs)`.

   Three to seven *candidate* assumptions before verification is the
   usual shape; Verified is whatever subset of those candidates passed
   the check — no floor, no separate cap. Coverage check is across
   the three categories (Technical / Product / Process), not the two
   subsections.

   **Surface the Unverified list and wait** for human confirmation or
   correction before writing into `Objective`, `Boundaries`,
   `Testing Strategy`, or `Acceptance Criteria`. If Unverified is
   empty, surface the Verified list with the highest-stakes item
   called out and ask the user to confirm *that one specifically* — a
   vague "looks good" doesn't count when the user may not have read
   the list.

   Only once Unverified has been signed off (or the highest-stakes
   Verified item confirmed, if Unverified was empty):

   - Copy the now-confirmed assumption list into the spec's
     `## Assumptions` section as a flat list — one bullet per item,
     each citing how it was settled. Verified entries keep their
     canonical source (path / URL / probe summary); previously-
     Unverified entries cite `user confirmation YYYY-MM-DD` with
     today's date. The chat block was the working surface; the spec
     section is the audit trail.
   - Write the spec's `Constrained by:` header from any Verified
     items that name an ADR or RFC the feature must cite. The header
     lands before any body section; Verified items don't gate the
     Unverified loop but they do gate `Constrained by:`.

4. Fill in the spec — including the **Testing Strategy** section. Push
   back hard on these failure modes:
   - **Objective is vague.** "It should be fast" is not an objective.
     "Returns within 200ms at p99 for payloads under 1KB" is. Every
     user-visible outcome named in the Objective must be precise
     enough that a test could be derived from it.
   - **Testing Strategy left as the template's mode list.** The
     template shows three modes (TDD, goal-based, manual QA); naming
     them without pairing each user-visible outcome from the Objective
     with a mode and a one-sentence why isn't a strategy.
   - **Boundaries left empty.** The three subsections — `Always do`,
     `Ask first`, `Never do` — keep an implementing agent inside the
     lines. Make the user name at least one entry per subsection, and
     at least one *structural* entry under `Never do` (no new top-level
     dependency, no new module boundary) so the diff can't sprawl into
     hypothetical futures.
   - **No Acceptance Criteria.** Without a checklist, "done" is opinion.

5. Fill in the plan second. The plan should:
   - Cite any ADRs or RFCs it follows from.
   - Break the work into tasks small enough to be a single PR each.
   - Carry **construction tests** per task — `Tests:` before `Approach:`
     in each task, designed up front. "We'll test it" is not a strategy.

   Push back hard on these plan-stage failure modes (mirror of step 4):
   - **Task too big.** "Implement the feature" is not a task; "add the
     validation function for X" is. Each task should fit a single PR
     and a single context window. Split coarse tasks until they do.
   - **`Depends on:` omitted.** Every task must state `Depends on:`
     explicitly — prior task IDs or `none`. Don't let authors lean on
     task order to imply dependency; that hides serial-by-default
     thinking and makes the plan unparseable.
   - **Verification mode unstated.** Every task must declare its mode —
     TDD, goal-based check, or visual / manual QA. Silent defaults
     produce mock-shape tests on config-shape tasks and untested
     invariants on logic-shape tasks.
   - **Tasks without spec mapping.** Each task should reference which
     behavior from the spec's Objective it implements, and the Testing
     Strategy mode for that behavior. Orphan tasks are scope creep in
     disguise; behaviors with no implementing task are gaps.
   - **Specificity miss.** Task descriptions should reference exact
     file paths and function or symbol names where they're known.
     "Update the parser" is too coarse to verify; "add a null-check
     in `parser/lex.ts:Lexer.next`" is the right level.

6. Spec-mode adversarial review. Before announcing the spec in the README,
   select a subagent matching `adversarial-reviewer` and ask it to review
   the freshly drafted `spec.md` + `plan.md` in spec mode — the role
   supports this explicitly. Iterate on findings until the reviewer returns
   `Clean — ready to commit.` Spec-mode reviews should converge in 1-2
   passes; if you can't reach clean in 3, the spec has a structural problem
   — surface to a human rather than grinding. Absence of any subagent
   matching this role is a note in the final summary
   (`adversarial-reviewer: no matching subagent installed; review skipped`),
   not a blocker.

7. Update `docs/specs/README.md` to add the feature to the active list.

8. Remind the user: when implementation diverges from the spec, the spec is
   wrong. Update the spec in the same PR.

## Anti-patterns to refuse

- Drafting a spec for something already half-built without checking against
  the existing code → ask the user to either align the spec with current
  behavior (and note any divergences) or write a new spec for what should
  change.
- Writing a spec that reads like a design doc (full of implementation) → the
  spec is the contract, not the design. Move implementation detail to
  `plan.md`.
- Skipping Boundaries → mandatory section. Each of the three
  subsections needs at least one entry.
- Writing into the spec body before the Unverified list has been
  confirmed → the headers can stay scaffolded; the bodies are the
  commitment and stay empty until the user has signed off on or
  revised the Unverified entries, even if the original prompt sounded
  definitive.
- Classifying a Technical or Process assumption as Unverified
  without recording the one check you attempted (path read, URL
  fetched, or read-only probe command + output) → attempt and cite
  the check. An attempted check that came back ambiguous is fine; a
  skipped check is not. The user's time is the scarce resource;
  burning a round-trip on a fact a single command would have answered
  is a tax on every spec.
- Fabricating a URL when web search isn't available → mark the
  assumption Unverified with `(web search unavailable)` and let the
  user supply the source. Plausible-looking citations the agent
  didn't actually fetch are worse than honest Unverified items.
