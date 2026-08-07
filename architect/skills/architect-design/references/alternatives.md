# Alternatives — surfacing real options, not strawmen

The most common failure mode in a design doc's Alternatives section is
the *false foil*: an option set up to lose. Reviewers spot it
immediately and the whole doc loses credibility — if Alternatives is
fake, what else is?

## The test for a real alternative

Each option in *Alternatives Considered* must pass all three:

1. **A reasonable engineer could have chosen it.** Not "in some
   universe", but in *this one*, knowing what we know now.
2. **Its rejection reason is specific.** Not "doesn't fit our
   architecture" — *which property of the architecture*, and what
   would have to change to make it fit.
3. **The reader could imagine the alternate timeline.** If we'd
   picked option B, what would the system look like in six months?
   If you can't sketch that, the option isn't real enough.

## Common strawmen and how to repair them

| Strawman | What's wrong | Repair |
| --- | --- | --- |
| "Do nothing." | Almost never a real option once a problem statement exists. | Drop it unless *staying with the status quo* is genuinely defensible — then name what staying costs. |
| "Build it from scratch." | Lazy foil when the proposal is to adopt a library. | Replace with the *specific* in-house build you'd actually have considered: which abstractions, which trade-offs. |
| "Use $popular_thing." | If the rejection is one sentence, you didn't consider it. | Either deepen the consideration or drop the option. |
| "Outsource it." | Used to make the proposal look like the only adult choice. | Drop unless outsourcing was an actual option on the table. |

## Where alternatives come from

Look in three places when generating alternatives:

1. **Across the boundary.** If the proposal is a service, the
   alternative might be a library. If it's a library, the alternative
   might be a service. If it's synchronous, the alternative might be
   asynchronous.
2. **From the team's recent history.** What did the team build last
   time a similar problem came up? Naming it forces honesty about why
   *this time* is different.
3. **From the industry's recent history.** If three peer companies
   have published about this problem, at least one of their answers
   is an alternative — engage with it specifically.

## Pattern: "what we're not doing"

Non-goals and alternatives overlap. If something is *not in scope* but
a reasonable reader would assume it is, name it as a Non-goal *and*,
where the choice is load-bearing, as an Alternative with rejection
reasoning. Do not duplicate without purpose — the two sections answer
different reader questions ("what won't this do?" vs. "what else did
you consider?").
