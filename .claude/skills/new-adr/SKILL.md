---
name: new-adr
description: Use this skill when the user asks to create, write, draft, or open a new ADR (architecture decision record). Triggers on phrases like "new ADR", "write an ADR for…", "record this decision", "let's ADR this". Do NOT use for RFCs (use `new-rfc`) or feature specs (use `new-spec`).
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

2. Pick a kebab-case title from the user's description. Keep it short and
   declarative — `0007-use-postgres-for-primary-store.md`, not
   `0007-decision-about-the-database.md`.

3. Copy this skill's bundled `assets/adr.md` into `docs/adr/` and
   rename to `NNNN-<title>.md`. (Paths are skill-relative — the
   `assets/` folder lives next to this `SKILL.md` wherever your IDE
   installed the skill.)

4. Fill in the frontmatter (status `Proposed`, today's date, deciders).

5. Help the user draft the four sections (Context, Decision, Consequences,
   Alternatives). Push back if any section is empty or hand-wavy:
   - Context with no constraints listed → ask what's actually constraining
     this choice.
   - Decision without a single declarative sentence at the top → write one.
   - Consequences without honest negatives → ask what we're giving up.
   - Alternatives without rejection reasons → ask why each was rejected.

6. Update `docs/adr/README.md` to add the new ADR to the table.

7. Tell the user to mark the ADR `Accepted` (and commit) once the relevant
   reviewers have signed off.

## Anti-patterns to refuse

- "Make this ADR say we're definitely using X" before discussion has happened →
  that's an RFC, not an ADR. Suggest opening one instead.
- Editing an existing accepted ADR → ADRs are immutable. If a decision is being
  reversed, write a *new* ADR that supersedes it, and update the old ADR's
  status to `Superseded by ADR-NNNN` (status only — leave the body untouched).
