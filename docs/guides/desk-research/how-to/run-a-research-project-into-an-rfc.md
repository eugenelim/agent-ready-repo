# Run a research project and feed it into an RFC

**Use this when:** A decision needs more than one sitting and you want the research evidence to land in an RFC with citations and confidence tags intact.
**Prerequisites:** `desk-research` pack installed and familiarity with the project lifecycle — walk [your first research project](../tutorials/your-first-research-project.md) first if needed.
**Result:** A self-contained research brief promoted into the RFC's `NNNN-notes/` companion folder, with findings mapped into *Evidence & prior art*.

You have a decision that needs more than one sitting — a framework choice, a
migration, a build-vs-buy — and you want the result to land in an RFC with its
evidence intact. This guide runs the `desk-research` project lifecycle and promotes
its brief into an RFC's `NNNN-notes/` companion and *Evidence & prior art*.

It assumes you already know what the project skills are. If you don't, walk
[your first research project](../tutorials/your-first-research-project.md) once;
if you're unsure a project is even the right tool, read [episodic vs project
research](../explanation/episodic-vs-project-research.md).

## Run the lifecycle

The four skills drive the lifecycle through its phases. Run them in order;
nothing advances on its own. (`-start` opens the `capture` phase, `-check` is a
stop-signal you can run any time, and the `feedback` phase has no skill — it's
where you act on the brief.)

1. **Start** — `start a research project on <question>`. Records the question
   and (optionally) a working hypothesis, scaffolds the folder, sets
   `phase: capture`.
2. **Capture** — fill `sources/` with one file per source. Run a one-off
   `/desk-research` per sub-question and save each result into `sources/`; use
   `/source-map` to find and curate the candidates first (it produces a
   `<topic-slug>-sources.md` list you then capture from). Grade each source's
   `reliability` / `credibility` if you want the extra provenance signal.
3. **Digest** — `digest the sources`. Builds `synthesis-matrix.md` (rows =
   sources, columns built from the material) and `memos.md` (where the
   hypothesis forms and gets revised).
4. **Check** — `is this project saturated?` Reports a qualitative stop-signal.
   Run it whenever you're tempted to stop gathering; believe it when it says the
   matrix structure has stopped changing.
5. **Synthesize** — `synthesize the project`. Writes the typed verdict
   (`<type>.md`) **and** the self-contained `<topic-slug>-brief.md`.

The brief is the artifact you promote. The corpus stays in scratch.

## Promote the brief into an RFC

The brief is built to drop into an RFC with almost no rework — it's answer-first,
self-contained, cited, and it already carries a `## Known unknowns` section that
maps onto an RFC's *Evidence & prior art*.

### 1. Open the RFC

Run `/new-rfc` for the decision. It scaffolds `docs/rfc/NNNN-<title>.md` from the
template and walks you through the body.

### 2. Create the `NNNN-notes/` companion

An RFC may carry a sibling **`docs/rfc/NNNN-notes/`** folder for promoted
research — the same shape as a spec's `notes/`. Use it so the RFC body stays a
proposal, not a lab notebook. Copy the brief in:

```
docs/rfc/
  0041-standardize-python-dep-manager.md
  0041-notes/
    python-dep-manager-brief.md      # the promoted brief
```

`/new-rfc` points you at this companion when you scaffold; the convention is in
`docs/CONVENTIONS.md` § 3. Promote **only the brief** (and, if useful, the typed
verdict) — not the raw `sources/` or the matrix. The brief is self-contained by
design, so it stands alone in the companion folder.

### 3. Map the brief onto *Evidence & prior art*

In the RFC's **Evidence & prior art** section, summarize the brief's findings
and link the companion — don't paste the corpus:

- The brief's **bottom line** → seeds the RFC's `## Proposal` / `The ask`.
- The brief's **cited, confidence-tagged findings** → *Evidence & prior art*
  (carry the `[high]` / `[moderate]` tags through; a reviewer wants to know how
  load-bearing each claim is).
- The brief's **`## Known unknowns`** → the RFC's open risks and *Open
  questions*. A known-unknown is a research lead the RFC still owes; an
  unknowable is a risk to state plainly, not to pretend away.

Link the companion explicitly, e.g. *"Full evidence in
[`0041-notes/python-dep-manager-brief.md`](0041-notes/python-dep-manager-brief.md)."*

## Common variations

- **The matrix is empty when you synthesize.** You skipped the digest.
  `/desk-research-project-synthesize` warns about this — run `/desk-research-project-digest`
  first; a synthesis with no digest is an ungrounded verdict.
- **The decision is small and one-shot.** Don't run a project. A single
  `/desk-research` (standard or applied) produces a `<topic-slug>-survey.md` you can
  cite directly in the RFC's *Evidence & prior art* — no folder, no lifecycle.
  See [episodic vs project research](../explanation/episodic-vs-project-research.md).
- **The investigation is contested, not just broad.** Capture perspective
  columns with `/identify-perspectives`, and let the synthesis lean on
  `/compare-hypotheses` for the adjudication. The brief still promotes the same
  way.
- **You want the reasoning trail to survive.** Scratch is gitignored and
  per-workspace, so it won't outlive the workspace. For a high-stakes decision,
  point `agentbundle-layout.toml`'s `[research]` `parent` at a durable base and link it from the brief —
  but still commit only the brief into the RFC companion.

## See also

- [Your first research project](../tutorials/your-first-research-project.md) —
  the guided walk-through of the lifecycle.
- [Run the research pipelines](research-pipelines.md) — the one-off (episodic)
  recipes, for when a project is more than you need.
- [Desk Research pack reference](../reference/desk-research-pack.md) — the four project
  skills, the folder layout, and the `agentbundle-layout.toml` `[research]` keys.
- [Episodic vs project research](../explanation/episodic-vs-project-research.md)
  — when to reach for which.
