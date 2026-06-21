---
name: new-adr
description: Use this skill when the user asks to create, write, draft, or open a new ADR (architecture decision record). Triggers on phrases like "new ADR", "write an ADR for...", "record this decision", "let's ADR this". Do NOT use for RFCs (use `new-rfc`) or feature specs (use `new-spec`).
---

# Skill: new-adr

Create a new ADR in `docs/adr/` from the template, with the next sequential
number.

## When to invoke

Before invoking, confirm:

1. The decision is about *architecture or shared infrastructure*, not a
   single feature's internals (that's a spec).
2. The decision has been *made or is being formally proposed*. ADRs are not
   a venue for open-ended discussion — that's an RFC.
3. There is a *concrete tradeoff* — at least one viable alternative was
   considered. If there's only one option, you don't need an ADR.

If any of these checks fail, push back rather than proceeding.

## Procedure

1. Find the next number. The bundled helper prints the next 4-digit
   ordinal — `0001` if no ADRs exist yet, max-plus-one otherwise. It
   parses the full digit prefix, so a `00099-foo.md` correctly yields
   `0100` (not `0010`):

   ```bash
   python3 scripts/next-ordinal.py docs/adr
   ```

   (The script lives next to this `SKILL.md` under `scripts/`. Python
   is preferred over `ls | grep | sed | sort` so the snippet works the
   same way on native Windows, macOS, and Linux.)

2. Pick a kebab-case filename title from the user's description. Keep it
   short and declarative — `0007-primary-store-postgres-over-dynamodb.md`,
   not `0007-decision-about-the-database.md`. The H1 title inside the file
   names the problem *and* the chosen solution together — "Primary store
   for user activity: Postgres over DynamoDB" — so the decision is legible
   from the index alone; keep the `ADR-NNNN` ordinal prefix on it.

3. Copy this skill's bundled `assets/adr.md` into `docs/adr/` and
   rename to `NNNN-<title>.md`. (Paths are skill-relative — the
   `assets/` folder lives next to this `SKILL.md` wherever your IDE
   installed the skill.)

4. Fill in the frontmatter: status `Proposed`, today's date, the
   `Decision-makers` who own the call, and — when the decision was run past
   others — the `Consulted` (whose input was sought, two-way) and `Informed`
   (who is kept up to date, one-way). Delete the `Consulted`/`Informed` lines
   if neither applies.

5. Help the user draft the sections. Push back if any is empty or hand-wavy:
   - Context with no constraints listed → ask what's actually constraining
     this choice.
   - Decision without a single declarative sentence at the top → write one.
   - Consequences without honest negatives → ask what we're giving up.
   - Alternatives without rejection reasons → ask why each was rejected.

   Two sections are optional — include them when they earn their place,
   delete them otherwise:
   - **Decision drivers** — the criteria the choice was judged against. Add it
     when more than one option was viable, so each alternative is rejected
     against a *stated* criterion rather than an ad-hoc reason.
   - **Confirmation** — how conformance with the decision will be verified (a
     design review, an architecture fitness test, a lint or CI check, a
     periodic audit). Add it when the decision is the kind that erodes
     silently if no one checks.

6. Update `docs/adr/README.md` to add the new ADR to the table.

7. Leave the status `Proposed`. Once the decision-makers sign off, mark it
   `Accepted`; if they decline it, mark it `Rejected` and keep the file — a
   recorded rejection stops the same option being re-proposed later. After
   `Accepted`, the body is frozen (see Lifecycle below).

## Lifecycle after acceptance

- **Reversing a decision.** Don't edit an accepted ADR. Write a *new* ADR for
  the new decision, set its `Supersedes:` to the old ADR's number, and flip the
  old ADR's status to `Superseded by ADR-NNNN` — status line only, the old body
  stays as history. The cross-reference points both ways.
- **Deprecated vs Superseded.** Mark an ADR `Deprecated` when the decision no
  longer applies and nothing replaces it; `Superseded by ADR-NNNN` when a
  specific later ADR replaces it.
- **Backfilling.** Recording a decision made months ago is fine — reconstruct
  the Context from memory and history, list the people who actually decided as
  `Decision-makers`, and note in References that it's a backfill.

## Anti-patterns to refuse

- "Make this ADR say we're definitely using X" before discussion has happened →
  that's an RFC, not an ADR. An ADR records a decision already made; an open
  debate is an RFC, and the accepted RFC then produces the ADR. Suggest opening
  one instead.
- Editing an accepted ADR's body → ADRs are immutable. A reversal is a *new*
  ADR that supersedes the old one (see Lifecycle above), never an edit.
