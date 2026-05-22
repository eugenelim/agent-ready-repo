---
name: new-rfc
description: Use this skill when the user asks to propose, draft, or open an RFC (request for comments). Triggers on "RFC", "propose a change to…", "let's get input on…", "draft a proposal". Do NOT use for already-decided things (use `new-adr`) or single-feature specs (use `new-spec`).
dependencies:
  - docs/_templates/rfc.md
---

# Skill: new-rfc

Open a new RFC in `docs/rfc/` from the template.

## When to invoke

Before invoking, confirm one of:

- The change touches multiple packages or affects external users.
- The change reverses a previous ADR.
- The change adds, removes, or modifies a top-level convention.
- The user explicitly wants discussion before implementation.

If the change fits inside a single package and breaks no public interface,
push back: a normal PR (or a spec, if it's a feature) is enough.

## Procedure

1. Find the next number:

   ```bash
   ls docs/rfc/ 2>/dev/null | grep -E '^[0-9]{4}' | sed 's/-.*//' | sort -n | tail -1
   ```

   Add 1, zero-pad to 4 digits. (If no RFCs exist, start at `0001`.)

2. Copy the template:

   ```bash
   cp docs/_templates/rfc.md docs/rfc/NNNN-<kebab-title>.md
   ```

3. Help the user draft the sections. The two sections most often
   under-developed are:
   - **Alternatives considered.** Including "do nothing." If the user can't
     articulate any, the proposal isn't yet honest.
   - **Drawbacks.** If they say "none", push back. There are always drawbacks.

4. Set status to `Draft` until the user is ready to circulate, then `Open`.

5. Update `docs/rfc/README.md` table.

## After acceptance

When the RFC is accepted, the *follow-on artifacts* section should list
concrete next steps — usually:

- One or more ADRs to record the architectural decisions.
- One or more specs in `docs/specs/` for features.
- Edits to `docs/CONVENTIONS.md` if the RFC changes conventions.

The RFC itself is then "done" and stays as historical record.
