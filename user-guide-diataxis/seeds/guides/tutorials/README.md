# Tutorials

> *Learning-oriented.* Lessons that take a beginner from nothing to a
> small, complete success. The reader is on rails — you have a destination
> and you're walking them to it.

## Writing a tutorial

A good tutorial has these properties:

- **Concrete and complete.** Following it produces a real, working result.
- **For beginners.** Assumes nothing. If a reader needs to know X first,
  the tutorial walks them through X (or links to a prior tutorial).
- **One path.** Don't offer choices ("you could do this or that"). Pick
  the best path and walk it.
- **No digression.** Don't explain *why* — link to an explanation page.
  Don't show alternative configurations — link to a reference.
- **Predictable.** The reader sees what you said they'd see. If your
  tutorial is wrong even once, the reader stops trusting it.

## What goes in a tutorial

- A guaranteed-outcome opening: "At the end of this tutorial you'll have
  a running X."
- Prerequisites, listed up front. If installing them is non-trivial, link
  to the install how-to.
- A sequence of small steps. Each step:
  - Says what to do (concrete commands or actions).
  - Shows what to expect (output, screenshot if it helps).
  - Reassures the reader they're on track.
- A clear ending. The reader knows they're done.
- Pointers to next steps — usually how-tos for nearby tasks.

## What does NOT go in a tutorial

- Reference data (config options, full API). Link to `../reference/`.
- Theory. Link to `../explanation/`.
- "Pick your favorite" or other choice-points. Pick one.
- Edge cases, troubleshooting beyond the most common pitfall. Those go
  in how-tos.

## Maintenance

Tutorials rot fastest. They're concrete; small product changes break them.
Run them end-to-end at least once per release, or automate the run in CI.
A tutorial that can't be run automatically should be tested manually on
a schedule — pick one and put it on the calendar.
