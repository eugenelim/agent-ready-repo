---
name: research-project-start
description: "Start a stateful, multi-week research project — the lifecycle axis, orthogonal to the depth axis the `/research` skill carries. Triggers on explicit project-lifecycle phrasing — \"start a research project\", \"set up a research project on X\", \"begin a sustained investigation\", \"open a research dossier\" — never on a one-shot lookup. Scaffolds the three-layer project folder (overview.md + a raw sources/ layer + the later digest and synthesis), records the question and a possibly-empty working hypothesis, and sets phase to capture. Resolves the project parent from the [research] table of an adopter-created agentbundle-layout.toml, else a scratch .context/research default, else by eliciting — never the committed repo tree. Prompt-only: phase is a frontmatter string the agent reads and writes; no engine, index, daemon, or counter. Does not replace /research — episodic quick/standard/applied/deep lookups stay there."
---

# /research-project-start

The entry point for **project mode** — a sustained, multi-week investigation
that accumulates a corpus, as opposed to the one-shot episodic research the
`/research` skill drives. Project mode is the **lifecycle axis**; depth (quick /
standard / applied / deep) is the orthogonal axis and stays with `/research`.

This skill scaffolds the project folder, records the question and a (possibly
empty) working hypothesis, and sets the project to its first phase. It writes no
findings — it sets up the place the rest of the lifecycle works in.

## When to invoke

Explicit project-lifecycle phrasing only: *"start a research project on X"*,
*"set up a research project"*, *"begin a sustained investigation"*, *"open a
research dossier"*. A casual *"look up X"* or *"research with citations: Y"* is
**not** a project — that stays with `/research` (the depth axis is the default
front door; project mode never displaces it).

## What it creates

A three-layer project folder:

```
<parent>/<YYYY-MM-DD>-<topic-slug>/
  overview.md          # question · working hypothesis · shape · phase · stop-signal
  sources/             # raw layer — one file per source, never overwritten
  # (digest + synthesis files are added by later phases)
```

- `<YYYY-MM-DD>` is the project's start date; `<topic-slug>` is the short
  (~2–5 word) kebab-case slug derived from the question, per the
  `/research` skill's topic-slug rule (§ Typed, topic-named artifacts). The
  date-plus-slug folder name namespaces the project, so working files **inside**
  the folder are bare-named (the folder already carries the topic) — the single
  exception is `<topic-slug>-brief.md`, which is topic-named because it travels
  out of the folder (see `/research-project-synthesize`).

### `overview.md` schema

Front-matter the agent reads and writes by hand — there is no engine behind it:

```markdown
---
question: <the research question, one sentence>
working_hypothesis: <a claim to test — MAY BE EMPTY at start>
shape: <survey | comparison | decision | structural | adjudication>
phase: capture
stop_signal: not-yet-assessed
# verdict_status: <optional, written only by /research-project-check>
---

# <topic> — project overview

## Question
<the question, expanded>

## Working hypothesis
<the current best guess, or "(none yet — to be formed in memos as evidence
accumulates)">

## Phases
- capture → digest → synthesize → feedback (human-driven; no skill auto-advances)
```

`phase` is a **string the agent reads and writes** — `capture` at start, advanced
by hand as the human moves the project on. There is no counter, index, or
state engine; the lifecycle is a prompt-driven habit (Charter Principle 3).

## Soft, revisable working hypothesis

`working_hypothesis` **may be empty at start** — there is no
refuse-without-a-claim gate. A project often begins as an open question; the
hypothesis is *formed and revised in `memos.md`* (see
`/research-project-digest`) as evidence accumulates. Starting with a strong
prior is fine too; it is held loosely and revised, never defended.

## Where the project lives — config-driven, scratch by default

Resolve the project **parent** directory in this order, **in this skill body**.
Reading is **prompt-only** (Charter Principle 3): this skill reads a file and
reasons about a path — there is no engine, index, daemon, or watcher behind it,
and the only code that ever *writes* the layout file is the install-time append.
See [`references/agentbundle-layout.md`](references/agentbundle-layout.md) for the
`[research]` section's full schema.

1. **Read `agentbundle-layout.toml`'s `[research]` table** if the adopter created
   one. Two locations, **repo-root overrides user-profile per table**: the
   repo-root `./agentbundle-layout.toml` `[research]` table if present, else the
   user-profile `~/.agentbundle/agentbundle-layout.toml` `[research]` table. The
   file is **adopter-owned**, never shipped into a projected path (that would trip
   the self-host drift gate). Its `parent` key is a **base** directory under which
   each project gets its own topic-named folder — never the leaf the project lands
   in:

   ```toml
   # agentbundle-layout.toml (adopter-created; optional)
   [research]
   parent = "~/research-projects"   # a base; project folders are created under it
   ```

2. **Fall back to the pack's own default** — a gitignored `.context/research/`
   under the repo. The default is **scratch**: a code repo commits the *decision*
   (the brief), never the corpus.
3. **Elicit** if neither resolves — ask the user where the project should live.

**Anchor `parent` by the layout file's own location**, never against the ambient
cwd: a **repo-root** file's `parent` is **repo-root-relative** (an absolute value
is permitted but warn it as non-portable); a **user-profile** file's `parent`
**must be an explicit absolute path** (`~`-anchored is fine), and a *relative*
value there is an Ask-first deviation, never silently resolved.

**Resolve, then surface, then write.** After anchoring, resolve `parent` to its
**full absolute path** — `~`-expand it and **realpath-resolve it** so any symlink
in the path is made visible and never silently followed out of the intended root
— and **reject any `..` escape**. The `..` rejection and the realpath happen
**after** anchoring, so a relative repo-file value that escapes via `..` (e.g.
`parent = "../../etc"`) is caught regardless of which file supplied it; anchoring
never blesses a `..`-bearing value as in-tree. Then **surface the resolved
absolute path to the adopter before creating the project folder** — the first
write is always preceded by the path you are about to write under.

**A repo-root-sourced `parent` that resolves outside the repo tree** — or whose
resolution required following a symlink out of the intended root — is
**untrusted-origin**: a cloned, untrusted repo can carry a hostile `parent`
(`../../etc`, `~/.ssh`, an out-of-tree symlink). **Confirm the resolved absolute
path with the adopter before writing.** The user-profile file is foot-gun-only
(the adopter authored it), but still surface its resolved path.

**Never create the project inside the committed repo tree** (`docs/`, repo
root). Pointing the layout at a durable vault or the committed tree is an
*Ask-first* deviation (the default is scratch; a vault is the deliberate,
configured exception for product research). `.context/` is per-workspace and
gitignored, so a scratch corpus does not survive the workspace — for a
high-stakes reasoning trail, configure a durable-but-separate parent and link it
from the brief.

This generalises the read `research-project-mode` shipped via the old
`research-layout.toml` into the shared `agentbundle-layout.toml` `[research]`
table — a **clean rename, no alias** (the old file was undistributed, so nothing
in the wild holds the old name). RFC-0038's forward-only migration alias was
considered and found not to apply.

## Source provenance — optional, additive axes

When sources are captured into `sources/` (by `/source-map` or by hand), each
source file's frontmatter MAY carry two **optional, independent** grading axes,
modelled on the Admiralty/NATO scale:

- `reliability` — the source's track record (A–F: how much the *source* has
  earned trust over time).
- `credibility` — corroboration of the *specific claim* this source makes
  (1–6: how well that claim is independently confirmed).

These **inform** the existing rail; they do not replace it. The claim-level rail
stays **GRADE confidence + ≥3-source triangulation** (per the `/research`
confidence schema). wiki-kit's binary Two-Source Rule is folded into
triangulation, not shipped as a separate gate. Both axes are optional — a
project that ignores them loses nothing but the extra provenance signal.

## Existing skills reused as phase operations

Project mode **reuses the pack's seven existing skills** in phase roles — it
does not rewrite them and injects no project-phase logic into their bodies. The
mapping:

| Existing skill | Role in the project lifecycle |
|---|---|
| `/research` | per-source episodic retrieval — a `standard`/`applied`/`deep` run that fills `sources/` with a cited finding-set for one source or sub-question |
| `/source-map` | populates `sources/` — curates and grades candidate sources by primacy |
| `/build-outline` | seeds the **initial** `synthesis-matrix.md` columns from the question's sub-questions (the emergent coding then overrides them) |
| `/identify-perspectives` | supplies **perspective columns** for a contested topic — one lens per camp |
| `/compare-hypotheses` | **is** the `hypotheses.md` synthesis for the adjudication shape — not re-derived |
| `/devils-advocate` | runs at synthesis against the typed verdict — the per-finding counter-pass |
| `/decision-archaeology` | **stays standalone** — self-contained rationale reconstruction, not part of the project lifecycle |

The four `research-project-*` skills orchestrate these; they add the lifecycle
(folder, phases, digest, brief), not new retrieval or synthesis primitives.

## What this skill is not

- Not `/research` — that is the episodic depth axis; this is the project
  lifecycle axis.
- Not a synthesis step — it writes no findings, only the scaffold.
- Not an engine — `phase` and `stop_signal` are frontmatter strings; nothing
  computes or advances them automatically.

## Next

Once `sources/` has material, run `/research-project-digest` to build the
middle layer. The phases are **human-driven**: this skill never advances `phase`
past `capture`.
