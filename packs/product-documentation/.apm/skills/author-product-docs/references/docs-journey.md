# The documentation journey

A reader meets a product's docs at many points: deciding whether to try it,
getting it running, using it daily, fixing it, and upgrading it. Each point asks
one question, and one kind of page answers it. Use this map to choose an
artifact, and to audit whether a doc set leaves a reader stranded anywhere.

Readers do not arrive in order. Search, a link from an error message, or a
colleague's URL can drop them on any page, so every page must make sense on its
own and link to what comes before and after it. The stages are a coverage map,
not a reading order.

## Stages

| Stage | Reader question | Artifact that answers it |
| --- | --- | --- |
| Discover and evaluate | Is this for me, and what are its limits? | README or docs landing page |
| Install | Can I get it running here? | Installation guide, or the README's install section |
| First success | Can I make it do one real thing quickly? | Quickstart or tutorial |
| Daily tasks | How do I do this specific thing? | How-to guides |
| Look up | What exactly does this accept, return, or default to? | Reference: API, CLI, configuration, or skill |
| Understand | Why does it work this way, and when should I not use it? | Explanation |
| Troubleshoot | It broke. What do I check, and how do I fix it? | Troubleshooting page, and error text that links to it |
| Upgrade | What changed, and what do I have to change? | Changelog and release notes, migration guide |
| Contribute | How do I report a problem, change it, or extend it? | Contributing guide |

Page contracts for each artifact live in [`page-contracts.md`](page-contracts.md).
Which reference artifact the look-up stage needs depends on the product surface;
see [`surface-discovery.md`](surface-discovery.md).

## What each stage needs most

- **Discover and evaluate.** State what the product does, who it is for, and
  what it does not do, before any install step. Show one real example of the
  result. Keep the README short and link out.
- **Install.** List prerequisites with versions before the first command. Give
  one supported path first; put alternatives after it. End with a command that
  proves the install worked.
- **First success.** One path, no choices, and a visible result at every step.
  Every sample works as pasted. Aim for a reader finishing in minutes; split a
  long tutorial into a series.
- **Daily tasks.** Title each how-to by the reader's goal. Assume competence.
  Cover the realistic variations, and link to reference for every option.
- **Look up.** Mirror the product's own structure. Shape sibling entries the
  same way. State every option, including rarely used ones. Generate from the
  source where the repository already does.
- **Understand.** Bound the page by one question. Give the mental model, the
  trade-offs, and when not to use the product. Take a position.
- **Troubleshoot.** Organize by symptom the reader can see. For each: the
  likely cause, how to confirm it, and the fix. Quote exact error text so search
  finds it.
- **Upgrade.** Keep the changelog for humans: newest first, dated, grouped as
  Added, Changed, Deprecated, Removed, Fixed, Security. A changelog may be
  generated per package or published as release notes; treat whichever source
  the project publishes as the changelog, and flag a stale hand-kept file that
  contradicts it. Write a migration guide
  per breaking version pair, as a checklist of what to search for and change.
  Name the replacement for every deprecation.
- **Contribute.** Say how to report a bug, set up a development environment,
  run the tests, and what contributions are welcome. Link it from the README.

## Pages to fold, not create

- **A standalone FAQ.** It duplicates answers that then drift, and it sorts by
  format instead of task. Put each answer on the task or troubleshooting page
  where a reader would look for it. If a short list of real, frequently asked
  questions helps, each item links to that page.
- **`llms.txt` and other machine-reader indexes.** Do not create one by default.
  Plain Markdown sources, descriptive headings, and pages that stand alone serve
  agents and search alike. Add an index only when the user asks for one or the
  repository already publishes one.
- **A page per Diátaxis kind.** Create the artifact the stage needs, not one of
  each kind.

## The journey gap report

Audit and retrofit modes map the existing doc set to the stages before any
other finding. Scope, sampling, and bounds follow Step 15 of the skill.

Produce one row per stage, in table order:

| Stage | Status | Evidence | Next action |
| --- | --- | --- | --- |
| Discover and evaluate | covered / partial / missing / not applicable | file path and line, or the reason | the smallest fix |

- **covered** — a page answers the stage's question for the current release.
- **partial** — a page exists but fails its contract, is stale, or is hard to
  find from the entry page.
- **missing** — no page answers the question.
- **not applicable** — the stage does not apply, with the reason. A library
  with no external contributors may mark Contribute not applicable; nothing
  marks First success not applicable.

Rank the next actions by where readers are lost first: a missing or failing
first success outranks a missing explanation. For retrofit, propose the
smallest set of changes that moves the worst rows to covered, and keep links
between stages so a reader landing anywhere can move forward and back.

## Handoffs

Neighboring skills own adjacent work; the skill's Handoffs section lists them and when to use each.
