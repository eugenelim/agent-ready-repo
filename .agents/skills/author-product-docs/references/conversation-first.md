# Conversation-first structure

Diátaxis determines where information lives. User intent determines how readers
enter it. These are page-level sequencing rules — they sit above the word-level
checklist in `clear-prose.md` and govern the order of what the reader encounters
before the detail starts.

A reader who does not know any of the product's internal names must still be
able to begin a real task from the first screen.

## Rules

1. **Put one observable outcome before the first conceptual explanation.** The
   reader needs to see what they will get before they are asked to understand why
   it works. An observable outcome is a command, a result, a screenshot, or a
   concrete next step — not a category name or a feature list.

2. **Put a first runnable action within the first 120 words of the page body,
   counted after the title and any front matter.** The action is a request, a
   command, or a code sample. It shows the reader how to start. It does not have
   to be the opener; it has to be early enough that a reader scanning for "how do
   I begin?" finds it without scrolling. Examples: an agent request ("Show me the
   team's open work"), a CLI command (`tool init --template web`), or a library
   call (`client.fetch(id)`).

3. **Introduce no more than two product-specific terms before that action.** Terms
   introduced before the first example are terms the reader must carry before they
   can act. Two is the ceiling; one is better; zero is possible and often right.

4. **Do not lead with a component, command, flag, endpoint, skill, or pack inventory.** Leading with
   a list of what the product contains is inventory-first writing. The reader came
   with a goal, not a browse session. The inventory belongs after the first task
   completes.

5. **Use user language first and implementation names second.** "Show me the team's
   open work" before `jira-team-status`. "Create a decision record" before `new-adr`.
   The page can use both; the user term opens the sentence.

6. **Show the next likely action, not only the initial one.** A guide that ends
   with the first task done leaves the reader stranded. Name where they go next —
   a follow-up command or prompt, a related page, or the decision they face after the first
   result lands.

7. **Separate read-only exploration from remote writes.** State clearly when an
   action reads data vs. when it changes something. A reader deciding whether to
   run a command needs to know which side of that line it falls on. Do not leave
   the read/write boundary implicit.

8. **Put exhaustive options in reference, not in the main procedure.** A how-to
   that enumerates every flag, a tutorial that lists every configuration key — both
   interrupt the reader's task with detail they did not ask for. Link to the
   reference; do not embed it.

9. **Label who acts.** For each step, say whether the reader says something, the
   agent or product does something, or the reader runs something in a terminal.
   Never show a command the agent runs as if the reader must type it.

10. **Say where the result lands and how to open it.** Name the location of any
    file or output and the way to open it. Do not assume a terminal, git, or a
    repository. State what must be installed and who can install it. When the
    source does not show where output lands, do not invent a location: leave the
    claim out of the page and list it as an open question for the owner in your
    report.

11. **Name the non-terminal route when one exists, and what it lacks.** If the
    task can be done through a menu or another interface, give that route first
    for readers who do not use a terminal, and say what it cannot do. When the
    audience does not use a terminal and you find no such route, ask the owner
    once whether one exists, and write the page without claiming that none does
    until they answer.

12. **Say what the product does not do.** One plain line in the page's scope,
    where a reader would otherwise assume the capability.
