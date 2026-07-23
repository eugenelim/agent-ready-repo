# Usability review

Run this checklist before finalizing any guide or pack page. Each "yes" is a
finding to fix. Read the draft cold — the sentences you have to read twice are
the ones that need work.

## Conversation-first checks

1. **Does a first actionable example appear within the first 120 words?**
   Count from the first word of body text (after the title). If the reader
   reaches word 120 without seeing a prompt, a command, or a concrete result,
   the page opens too late.

2. **Can the reader begin a real task without knowing any skill or pack name?**
   Cover the title, the nav, and the first paragraph. If what the reader must
   type to start is a skill name rather than a natural-language goal, the page
   is skill-first, not reader-first.

3. **Is read/write behavior explicit?** The reader should know, before they
   act, whether the agent will only read data or whether it may change something.
   If the page leaves the read/write boundary implicit, name it.

4. **Does the page show at least one realistic follow-up request?** A guide
   that ends when the first task completes leaves the reader without a next
   step. Name the most likely follow-up — a prompt, a decision, or a link.

5. **Does skill/command inventory appear after user outcomes, not before?**
   Scan the page top to bottom. If the first substantive block is a list of
   skills, commands, or flags rather than a goal or an example, the structure
   is inventory-first. Move the inventory below the first task completion.

6. **Does the guide show a visible start AND finish for at least one complete
   task?** A complete task has a first request the reader can copy and a final
   result the reader can verify. If either is missing, the task is incomplete.

## Contract verification

Before declaring the guide ready, confirm the conversation contract fields are
all present and accurate:

- **reader** — who is reading this right now (role + context, not "all users")
- **job** — the specific thing they are trying to accomplish
- **natural_start** — the exact words they would use to begin
- **minimum_scope** — the minimum the agent needs to start (team, board, time horizon, etc.)
- **first_result** — the concrete first thing the reader receives
- **write_boundary** — what the agent reads vs. what it may change
- **next_request** — the most likely follow-up after the first result lands

If any field is empty or vague, the guide cannot meet the reader's real need.
