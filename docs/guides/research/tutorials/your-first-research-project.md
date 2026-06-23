# Your first research project

In about thirty minutes you'll run a **research project** end to end — start it,
feed it a few sources, build a digest, and synthesize a one-page brief you could
hand to a decision. By the end you'll have a project folder on disk and a
self-contained brief inside it, and you'll know which four skills drive the
lifecycle.

This is project mode — the *lifecycle* axis. It's different from a one-off
`/research` run (the *depth* axis you met in [your first research
session](research-first-session.md)). If you're not sure which one you want,
read [episodic vs project research](../explanation/episodic-vs-project-research.md)
first — then come back. This tutorial assumes you've decided you want a project.

## Prerequisites

- The `research` pack installed at user scope (the [first-session
  tutorial](research-first-session.md) covers the one-time install).
- A throwaway question you actually care about. This tutorial uses *"which
  Python dependency manager should our team standardize on?"* — swap in your own
  if you like; the steps are identical.

## Step 1 — start the project

In your Claude Code session, type:

```
start a research project on which Python dependency manager our team should standardize on
```

The `/research-project-start` skill fires (the phrasing *"start a research
project"* is what triggers it — a casual *"look up X"* would stay a one-off).
It asks where the project should live if it can't resolve a location on its own,
then scaffolds a folder.

You should see a new folder named with today's date and a topic slug, like:

```
2026-06-22-python-dep-manager/
  overview.md
  sources/
```

Open `overview.md`. Its frontmatter records your `question`, a
`working_hypothesis` (empty for now — that's fine, you'll form it as you go), a
`shape`, and `phase: capture`. The project starts in the **capture** phase.

> Where did the folder land? By default, in scratch / out-of-repo space (a
> gitignored `.context/research/` or a user-level path) — a code repo commits
> the *decision*, never the whole corpus. You can point it elsewhere with a
> `research-layout.toml`; the [reference](../reference/research-pack.md) has the
> keys.

## Step 2 — capture a few sources

A project is only as good as its `sources/`. Gather three. The fastest way is to
run a one-off `/research` per sub-question and save each result into `sources/`,
but for this tutorial drop three short notes by hand so the run is quick. Create
three files under `sources/`:

`sources/src-01.md`:

```markdown
---
source: Poetry docs + adoption surveys
reliability: B
credibility: 2
---
Poetry locks dependencies and manages virtualenvs; widely adopted; resolver has
historically been slow on large trees.
```

`sources/src-02.md`:

```markdown
---
source: uv docs + benchmarks
reliability: B
credibility: 2
---
uv is a fast resolver/installer with a lockfile; newer, smaller ecosystem
footprint; rapidly gaining adoption.
```

`sources/src-03.md`:

```markdown
---
source: pip-tools docs
reliability: A
credibility: 2
---
pip-tools is minimal and composable (requirements.in → compiled
requirements.txt); no virtualenv management; very stable.
```

The `reliability` and `credibility` lines are optional Admiralty-style
provenance grades — how much the source has earned trust, and how well its
specific claim is corroborated. You can skip them; they only add signal.

## Step 3 — build the digest

With sources in hand, type:

```
digest the sources for this project
```

`/research-project-digest` reads `sources/*.md` and builds the **middle layer**
the pack gives you here: a `synthesis-matrix.md` and a `memos.md`.

Open `synthesis-matrix.md`. You should see a table whose **rows are your
sources** and whose **columns were built from what the sources actually talk
about** — something like *resolver speed*, *lockfile*, *virtualenv management*,
*maturity*. The columns are discovered from the material, not chosen from a
fixed template; that's the point.

Open `memos.md`. This is where the reasoning lives — and where your
working hypothesis forms. A note like *"speed and maturity pull in opposite
directions; uv leads on speed, pip-tools on stability"* is exactly right.

## Step 4 — check the stop signal

Before you synthesize, ask whether you've gathered enough:

```
is this project saturated?
```

`/research-project-check` reads the matrix and memos **by eye** and reports a
qualitative judgment — is the matrix structure still changing, or are new
sources just confirming existing columns? — plus a recommendation. It changes
nothing except, optionally, a `verdict_status` marker in `overview.md`. It will
**not** move the project forward on its own; that's your call.

You should see a short report ending in a recommendation like *"looks
saturated — move to synthesize"* or *"not yet — the cost dimension is still
single-sourced."* For this tiny corpus, expect the former.

## Step 5 — synthesize the brief

Now produce the output:

```
synthesize the project
```

`/research-project-synthesize` reads the digest and writes **two** files into
the folder:

```
comparison-matrix.md          # the typed verdict (this project's shape is a comparison)
python-dep-manager-brief.md   # the governance brief
```

Open `python-dep-manager-brief.md`. Notice four things:

1. The **bottom line is the first content line** — the recommendation, before any
   supporting detail.
2. It has **no links to the other project files**. Everything it needs is
   inlined; you can copy this one file anywhere and it still makes sense.
3. Every load-bearing claim carries a **citation and a confidence tag**
   (`[high]` / `[moderate]`).
4. It ends with a **`## Known unknowns`** section — the questions a complete
   answer still needs.

That self-contained brief is the durable output of the whole project. The
corpus stays in scratch; the brief is what travels.

## Step 6 — see what you built

List the folder:

```
ls 2026-06-22-python-dep-manager/
```

You should see the full three layers: `overview.md`, a raw `sources/`, the
digest (`synthesis-matrix.md` + `memos.md`), the typed `comparison-matrix.md`,
and `python-dep-manager-brief.md`. That progression — raw → digest → synthesis —
is the shape of every research project.

## Where to go next

- Ready to turn that brief into a decision? [Run a research project and feed it
  into an RFC](../how-to/run-a-research-project-into-an-rfc.md) picks up exactly
  where this tutorial ends.
- Want the full catalogue of the four project skills, their phases, and the
  `research-layout.toml` keys? See the [reference](../reference/research-pack.md).
- Wondering when a project is overkill and a one-off `/research` would do?
  [Episodic vs project research](../explanation/episodic-vs-project-research.md).
