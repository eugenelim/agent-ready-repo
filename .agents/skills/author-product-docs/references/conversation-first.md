# Conversation-first structure

Diátaxis determines where information lives. User intent determines how readers
enter it. These are page-level sequencing rules — they sit above the word-level
checklist in `clear-prose.md` and govern the order of what the reader encounters
before the detail starts.

A reader who does not know any pack or skill names must still be able to begin a
real task from the first screen.

## Rules

1. **Put one observable outcome before the first conceptual explanation.** The
   reader needs to see what they will get before they are asked to understand why
   it works. An observable outcome is a command, a result, a screenshot, or a
   concrete next step — not a category name or a feature list.

2. **Put a realistic user request within the first 120 words.** The request shows
   the reader how to start. It does not have to be the opener; it has to be early
   enough that a reader scanning for "how do I begin?" finds it without scrolling.

3. **Introduce no more than two product-specific terms before that request.** Terms
   introduced before the first example are terms the reader must carry before they
   can act. Two is the ceiling; one is better; zero is possible and often right.

4. **Do not lead with a component, skill, command, or pack inventory.** Leading with
   a list of what the product contains is inventory-first writing. The reader came
   with a goal, not a browse session. The inventory belongs after the first task
   completes.

5. **Use user language first and implementation names second.** "Show me the team's
   open work" before `jira-team-status`. "Create a decision record" before `new-adr`.
   The page can use both; the user term opens the sentence.

6. **Show the next likely request, not only the initial request.** A guide that ends
   with the first task done leaves the reader stranded. Name where they go next —
   a follow-up prompt, a related page, or the decision they face after the first
   result lands.

7. **Separate read-only exploration from remote writes.** State clearly when an
   action reads data vs. when it changes something. A reader deciding whether to
   run a command needs to know which side of that line it falls on. Do not leave
   the read/write boundary implicit.

8. **Put exhaustive options in reference, not in the main procedure.** A how-to
   that enumerates every flag, a tutorial that lists every configuration key — both
   interrupt the reader's task with detail they did not ask for. Link to the
   reference; do not embed it.
