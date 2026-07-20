---
name: desk-research-project-start
description: "Start a stateful, multi-week research project — the lifecycle axis, orthogonal to the depth axis the `/research` skill carries. Triggers on explicit project-lifecycle phrasing — \"start a research project\", \"set up a research project on X\", \"begin a sustained investigation\", \"open a research dossier\" — never on a one-shot lookup. Scaffolds the three-layer project folder (overview.md + a raw sources/ layer + the later digest and synthesis), records the question and a possibly-empty working hypothesis, and sets phase to capture. Resolves output_dir: repo-scope agentbundle-layout.toml [research] output_dir first, then user-scope, then two-branch elicitation (repo vs personal workspace) — never a silent .context/ default. Prompt-only: phase is a frontmatter string the agent reads and writes; no engine, index, daemon, or counter. Does not replace /research — episodic quick/standard/applied/deep lookups stay there."
---

# /desk-research-project-start

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
  out of the folder (see `/desk-research-project-synthesize`).

### `overview.md` schema

Front-matter the agent reads and writes by hand — there is no engine behind it:

```markdown
---
question: <the research question, one sentence>
working_hypothesis: <a claim to test — MAY BE EMPTY at start>
shape: <survey | comparison | decision | structural | adjudication | methodology>
phase: capture
stop_signal: not-yet-assessed
# verdict_status: <optional, written only by /desk-research-project-check>
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
`/desk-research-project-digest`) as evidence accumulates. Starting with a strong
prior is fine too; it is held loosely and revised, never defended.

## Where the project lives — config-driven, elicit when not configured

Resolve the project **output directory** in this order, **in this skill body**.
Reading is **prompt-only** (Charter Principle 3): this skill reads a file and
reasons about a path — there is no engine, index, daemon, or watcher behind it,
and the only code that ever *writes* the layout file is the install-time append.
See [`references/agentbundle-layout.md`](references/agentbundle-layout.md) for the
`[research]` section's full schema.

1. **Repo-scope config** — read `./agentbundle-layout.toml` `[research] output_dir`
   if the file exists and the key is present. Repo-scope takes priority so that
   a project or team convention applies when you're working in this repo.

2. **User-scope config** — read `~/.agentbundle/agentbundle-layout.toml` `[research]
   output_dir` if the file exists and the key is present. User-scope is the
   fallback — useful for a personal vault (e.g. Obsidian) or a default output
   path you use across repos when no repo convention is set.

   Both files are **adopter-owned**, never shipped into a projected path (that
   would trip the self-host drift gate). The `output_dir` key is a **base**
   directory under which each project gets its own topic-named folder — never the
   leaf the project lands in:

   ```toml
   # agentbundle-layout.toml (adopter-created; optional)
   [research]
   output_dir = "~/research-projects"   # a base; project folders are created under it
   ```

3. **Two-branch elicitation** — when neither config resolves, ask the user which
   branch fits their situation (never silently default to a path):

   - **Repo branch** — "Commit to this repo? Suggest: `docs/product/research/`
     (team-visible, version-controlled). Enter path or press Enter to accept:"
     On accept, write `output_dir = "<path>"` to `./agentbundle-layout.toml`
     `[research]` so subsequent projects skip elicitation.
   - **Personal branch** — "Write to a personal workspace (e.g. Obsidian vault)?
     Enter the absolute path. Example: `~/Documents/<VaultName>/efforts/research/`
     (no default — Obsidian has no universal vault path). On accept, write
     `output_dir = "<path>"` to `~/.agentbundle/agentbundle-layout.toml`
     `[research]` so subsequent projects skip elicitation.

   Never default to `.context/` — it is gitignored ephemeral scratch and does
   not survive workspace resets or session boundaries.

**Anchor `output_dir` by the layout file's own location**, never against the ambient
cwd: a **repo-root** file's `output_dir` is **repo-root-relative** (an absolute value
is permitted but warn it as non-portable); a **user-profile** file's `output_dir`
**must be an explicit absolute path** (`~`-anchored is fine), and a *relative*
value there is an Ask-first deviation, never silently resolved.

**Resolve, then surface, then write.** After anchoring, resolve `output_dir` to its
**full absolute path** — `~`-expand it and **realpath-resolve it** so any symlink
in the path is made visible and never silently followed out of the intended root
— and **reject any `..` escape**. The `..` rejection and the realpath happen
**after** anchoring, so a relative repo-file value that escapes via `..` (e.g.
`output_dir = "../../etc"`) is caught regardless of which file supplied it; anchoring
never blesses a `..`-bearing value as in-tree. Then **surface the resolved
absolute path to the adopter before creating the project folder** — the first
write is always preceded by the path you are about to write under.

**A repo-root-sourced `output_dir` that resolves outside the repo tree** — or whose
resolution required following a symlink out of the intended root — is
**untrusted-origin**: a cloned, untrusted repo can carry a hostile `output_dir`
(`../../etc`, `~/.ssh`, an out-of-tree symlink). **Confirm the resolved absolute
path with the adopter before writing.** The user-profile file is foot-gun-only
(the adopter authored it), but still surface its resolved path.

**Never create the project inside the committed repo tree** (`docs/`, repo
root) without explicit adopter confirmation — this is the deliberate, configured
exception for product research (when a team commits desk-research output to
`docs/product/research/`). For a high-stakes reasoning trail, configure a
durable-but-separate path and link it from the brief.

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

Once `sources/` has material, run `/desk-research-project-digest` to build the
middle layer. The phases are **human-driven**: this skill never advances `phase`
past `capture`.
