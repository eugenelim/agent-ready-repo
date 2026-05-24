# Using `agent-ready-repo`

This template gives a single application, component, microservice, library,
or platform repo the structure it needs to work well with Claude Code (and
other AI coding agents) — without the bureaucracy that sprawling monorepos
require.

This file explains how to bootstrap a real project from the template.
**Read it once before starting.** The whole bootstrap takes 15-30 minutes
depending on how much you customize.

> **Sizing note.** This template targets repos with roughly 1 to 50
> contributors: microservices, single apps, libraries, engines, and
> medium-sized platforms. It is *not* designed for sprawling monorepos
> with hundreds of contributors and SIG-style governance — for that
> scale, look at Kubernetes/CNCF patterns instead. See
> [`docs/CONVENTIONS.md` § Scaling profiles](docs/CONVENTIONS.md#scaling-profiles--how-this-template-adapts-to-different-repo-sizes)
> for the size-by-size breakdown.

---

## Step 0 — Pick your profile

The template's structure is the same at every supported size. What
differs is which folders you populate and which ceremony you keep.

| Profile | Use when |
| --- | --- |
| **A: Microservice / single component** | 1-3 contributors; one service, one purpose. Most folders empty initially. |
| **B: Single library or app** | 4-10 contributors; one cohesive thing, growing. |
| **C: Medium platform / engine** | 10-50 contributors; multiple apps or packages; the design target. |

If you're unsure, start at the smaller profile. Empty folders are fine;
adding ceremony you don't need produces ignored ceremony, which is worse
than no ceremony.

You can move up profiles later — the structure doesn't change, you just
populate more of it.

---

## Step 1 — Create your repo from the template

There are three ways to adopt the template. Pick by what you already have.

### Path A: Bootstrap a fresh repo from the template

The full template — every skill, every reviewer, every doc — wired up
for a new project. Use this when you're starting greenfield, or when
you want the structure as a whole.

**Option A1: GitHub "Use this template" (recommended)**

1. On the template's GitHub page, click **Use this template** → **Create a new repository**.
2. Name your repo, set visibility, click **Create repository from template**.
3. Clone it locally:
   ```bash
   git clone <your-new-repo-url>
   cd <your-new-repo>
   ```

**Option A2: Manual copy**

```bash
# Clone the template
git clone <template-url> my-project
cd my-project

# Drop the template's git history and start fresh
rm -rf .git
git init
```

Then continue with Step 2 below.

### Path B: Drop a single skill into an existing repo

Already have a repo and you just want one skill (say, `bug-fix` or
`work-loop`)? Clone the template anywhere, then run:

```bash
# macOS / Linux:
python3 /path/to/template/tools/install-skill.py <skill-name> /path/to/your-repo

# Windows (PowerShell):
py -3 \path\to\template\tools\install-skill.py <skill-name> \path\to\your-repo
```

The script reads the skill's dependency manifest, walks the closure,
and copies every leaf — sibling agents, templates the skill generates
from, tools it invokes — into your repo at the matching paths. Files
that already exist are left alone; the script reports each one
(`= already present` if it matches the source, `! content differs` if
it doesn't) and moves on. Re-running is safe and shows you the same
inventory.

A few skills depend on sections of `docs/CONVENTIONS.md` or `AGENTS.md`.
Those don't get spliced into your governance docs — the script can't
safely edit prose it didn't write. Instead, it drops the relevant
slice into `docs/CONVENTIONS.fragments/<skill>.md` and prints a note.
Merge by hand, then delete the fragment.

Skip the rest of this guide if Path B was all you needed.

### Path C: have an agent adapt the template

Path C **wraps Paths A and B** — it doesn't replace them. The
installers do the mechanical copying safely (Path B respects existing
files; Path A handles placeholder substitution and profile cleanup).
The agent does the judgment-only work that those scripts intentionally
leave to the adopter: enhancing the project's load-bearing files
(`AGENTS.md`, `README.md`, `docs/CHARTER.md`, `docs/CONVENTIONS.md`)
in place, wiring real commands, picking which skills apply, and
splicing installer fragments into their target files. You review the
agent's diff before committing.

Use Path C when you want that judgment work done for you — typically a
retrofit into an existing repo that already has code and history, or a
fresh project where you'd rather the agent fill the prose-heavy scope
content (charter, architecture overview, roadmap) than write it by
hand after the bootstrap script.

Clone `agent-ready-repo` as a sibling of your target so the agent can
reference it with a relative path:

```bash
# Retrofit case: your existing repo already exists; clone the template
# next to it.
cd /path/to/parent
git clone <template-url> agent-ready-repo
cd /path/to/your-existing-repo   # the agent runs here

# Fresh-project case: follow Path A's "Manual copy" to clone the
# template into your new project directory and reset its history, then
# keep a separate reference clone alongside it for the agent to read.
cd /path/to/parent
git clone <template-url> my-project && cd my-project && rm -rf .git && git init && cd ..
git clone <template-url> agent-ready-repo   # untouched reference copy
cd my-project                                # the agent runs here
```

Keep the sibling `agent-ready-repo` clone in place until Path C
finishes. Prompt 1 references it heavily (installer paths, linter
scripts, doc lookups); Prompt 2 references it for a single
cross-reference back to Step 0 after the local
`USING_THIS_TEMPLATE.md` is removed.

**Prompt 1 — retrofit into an existing repo.** The agent runs the Path
B installer for skills, then enhances the project's existing
load-bearing files in place — preserving their existing content,
merging in the template's patterns, and leaving a clean diff for the
user to review:

> Read `../agent-ready-repo/AGENTS.md`, `../agent-ready-repo/README.md`,
> `../agent-ready-repo/docs/CONVENTIONS.md`, and
> `../agent-ready-repo/USING_THIS_TEMPLATE.md` first.
>
> Install the load-bearing skills using the template's Path B
> installer — it walks each skill's dependency closure and never
> overwrites existing files:
>
> ```
> python3 ../agent-ready-repo/tools/install-skill.py work-loop .
> python3 ../agent-ready-repo/tools/install-skill.py bug-fix .
> ```
>
> `work-loop`'s dependency closure already brings `new-spec`, the three
> reviewers (`adversarial-reviewer`, `security-reviewer`,
> `quality-engineer`), and the `implementer` executor — so the second
> install adds only the `bug-fix` skill itself. Don't port other skills
> (`new-adr`, `new-rfc`, `new-package`, `update-conventions`) without
> asking me first.
>
> If the installer reports `! <path> — exists with different content,
> skipping`, diff the source against the destination and flag the
> divergence in your PR summary — don't silently overwrite, and don't
> silently ignore. (The `= <path> — already present (identical),
> skipping` case is a no-op and needs no action.)
>
> Whenever you draft a file from the template's shape, **only reference
> artifacts that actually exist in this repo**. The template's
> `AGENTS.md` and `docs/CONVENTIONS.md` link to template-only files
> that no installed skill claims as a dependency — for example
> `.claude/skills/README.md`, `docs/architecture/overview.md`,
> `tools/hooks/README.md`, `.claude/skills/new-adr/assets/adr.md`,
> `.claude/skills/new-rfc/assets/rfc.md`. Borrow the section structure, then let the
> docs linter be the authority: for every `broken link →` finding it
> reports against your drafted files, either install the missing
> artifact or remove the link. Don't ignore them.
>
> Then **enhance the load-bearing files in place** — they already
> contain content I care about, so don't replace them; merge the
> template's patterns in alongside what's there. The user will review
> the diff, so keep edits well-scoped and clearly explained in your PR
> summary. If a file is missing, draft it from the template's shape.
> Per-file guidance:
>
> - `AGENTS.md` — the canonical agent context. Keep the project's
>   existing description, commands, and project-specific guidance.
>   Ensure these load-bearing sections are present, in whatever voice
>   matches the existing file: a one-sentence "what this repo is", a
>   "Source of truth" table (or equivalent prose) pointing at `docs/`,
>   references to the `work-loop` skill and the specialist subagents
>   you just installed, real install/test/lint/build commands, and a
>   "Check before acting" list of destructive/cross-cutting actions
>   that need confirmation. Splice content from any
>   `AGENTS.fragments/<skill>.md` file the installer dropped into the
>   relevant section, then delete the fragment. Keep the file under
>   ~200 lines. If `AGENTS.md` doesn't exist, draft one against the
>   template's shape, matching this repo's tech stack.
> - `CLAUDE.md` — must be a symlink to `AGENTS.md` (the docs linter
>   checks this). If `CLAUDE.md` is already a regular file with content
>   the project has been maintaining separately, surface it in your PR
>   summary before swapping; otherwise `rm CLAUDE.md && ln -s AGENTS.md
>   CLAUDE.md`.
> - `README.md` — keep the project's existing pitch and structure. Add
>   one short section pointing agents at `AGENTS.md` and naming the
>   skills/subagents now available, unless an equivalent pointer is
>   already there.
> - `docs/CHARTER.md` — if it exists, keep the mission/scope/principles
>   as written; conform to the template's shape only where it
>   genuinely helps. If it doesn't exist, draft a one-page charter
>   (mission, in-scope/out-of-scope bullets, 5–7 principles) against
>   this repo's actual scope. (Skills outside the current load-bearing
>   set can emit `docs/CHARTER.fragments/<skill>.md` — splice and
>   delete the same way as the AGENTS/CONVENTIONS bullets if you ever
>   see one.)
> - `docs/CONVENTIONS.md` — **required**: installed skills link into
>   anchors inside this file, and the artifact linter resolves those
>   links. If the file doesn't exist, draft it from the template's
>   shape, tailored to this repo's process, before running the linters.
>   Splice content from any `docs/CONVENTIONS.fragments/<skill>.md`
>   file into the matching section without overwriting existing
>   conventions, then delete the fragment.
> - `.gitignore` — append the runtime-state rules the work-loop skill
>   expects: `.ralph/`, `docs/specs/**/state.json`,
>   `docs/specs/**/notes/implementer-*.md`, and `.worktrees/`.
>
> Then run both template linters against this repo:
>
> ```
> bash ../agent-ready-repo/tools/lint-agents-md.py
> bash ../agent-ready-repo/tools/lint-agent-artifacts.py
> ```
>
> The artifact linter validates frontmatter and resolves relative
> markdown links inside the skills and subagents you just installed —
> both must pass. The link check is the other reason `docs/CONVENTIONS.md`
> above is required: installed skill bodies link into anchors there.
> The docs linter is opinionated about full template structure —
> missing Diátaxis subdirectories under `docs/guides/`, a missing
> `CLAUDE.md` symlink, or stale links inside drafted `AGENTS.md` /
> `docs/CONVENTIONS.md` will fail it. List each remaining failure in
> your PR description with a one-line reason ("intentionally skipped",
> "for follow-up").
>
> Cap your PR summary with: what you installed, which files you
> enhanced in place (with a one-line "what changed" for each), what
> you skipped, and which linter failures are intentional. Flag any
> edit you weren't sure about so I can spot-check it.

**Prompt 2 — fill a fresh template clone against a stated scope.** The
honest split: `tools/bootstrap.sh` handles every mechanical edit —
placeholder substitution across `AGENTS.md`, `README.md`,
`docs/CHARTER.md`, `.github/pull_request_template.md`, `LICENSE-MIT`;
date stamping `docs/product/roadmap.md` and `docs/adr/0001-*.md`;
profile-specific deletions with their corresponding link cleanup;
`.ralphrc` creation; self-removal of `USING_THIS_TEMPLATE.md` and the
script itself. The agent's job is the prose-heavy scope content that
the script intentionally leaves blank: a real charter (not just its
one-line description), the architecture overview, the roadmap's themed
bullets, and any project-specific reasoning to append to ADR-0001.

Run the script first, answering its prompts with the scope-specific
values:

```bash
# In the fresh template clone produced by Path A's "Manual copy":
bash tools/bootstrap.sh
```

Then open the agent in the same directory and run:

> This is a freshly bootstrapped clone of `agent-ready-repo` —
> placeholders have been substituted by `tools/bootstrap.sh`, but the
> prose-heavy scope content has not been written yet. Fill it against
> this scope:
>
> - One-line description: `<what it does and for whom>`
> - Tech stack: `<language, framework, datastore, deploy target>`
> - Profile (already chosen at bootstrap): `<A / B / C>` — see Step 0
>   of `../agent-ready-repo/USING_THIS_TEMPLATE.md` if you need a refresher.
>
> Write:
>
> - `docs/CHARTER.md` — full charter: mission (one sentence),
>   in-scope/out-of-scope bullets, 5–7 principles with one example each.
>   The out-of-scope list is the highest-leverage part; don't skip it.
> - `docs/architecture/overview.md` — the project map. For Profile A,
>   one paragraph is enough; for B and C, fill the full structure
>   sections.
> - `docs/product/roadmap.md` — replace every `<theme>` and
>   `<thing we won't do>` placeholder with real content. `Now` and
>   `Not in scope` are the highest-leverage sections; fill those even
>   if `Next` and `Later` stay as `(nothing yet — add as items appear)`.
> - `docs/adr/0001-*.md` — leave the existing rationale alone (it
>   describes adopting AGENTS.md + the doc hierarchy, which this
>   project is also adopting). Append any project-specific bullets
>   under "Consequences" or "Alternatives considered" that the
>   template's generic list doesn't already cover; if nothing
>   project-specific applies, leave the ADR as-is.
>
> You may also refine the files the bootstrap script already filled
> (`AGENTS.md`, `README.md`'s scaffold, `LICENSE-MIT`,
> `.github/pull_request_template.md`, `.ralphrc`) if charter-writing
> turns up scope-specific details worth landing there — for example,
> tightening `AGENTS.md`'s "what this repo is" paragraph against the
> charter you just wrote, or adding project-specific bullets to its
> "Check before acting" list. Don't redo work the script did
> correctly; the user will review the diff. If any of those
> bootstrap-owned files still has a literal `<placeholder>` left in
> it, flag it in your PR summary instead of fixing it yourself —
> that's a bug in the bootstrap script. (The placeholders you wrote
> into the roadmap and elsewhere in the "Write" list above are your
> job to fill, not flag.)
>
> If `tools/bootstrap.sh` or `USING_THIS_TEMPLATE.md` is still present
> in the working tree, note it in your PR summary: usually it means
> the user declined the script's cleanup prompt (fine), but it could
> also mean the script aborted before reaching cleanup (worth a
> closer look).
>
> Then run `python tools/lint-agents-md.py` and
> `python tools/lint-agent-artifacts.py`. Both must pass before you
> declare done.

Path C is not a shortcut around reviewing the result. Treat the agent's
output like any other PR: read the diff, check that the prose matches
your repo's reality, and edit `AGENTS.md` rather than working around
anything that feels off.

---

## Step 2 — Run the bootstrap helper (optional but recommended)

The template ships with a script that handles the mechanical parts of
bootstrap — placeholder substitution, removing example dirs, initializing
the changelog with today's date.

```bash
bash tools/bootstrap.sh
```

The script will prompt you for:

- **Project name** (used in headers, README, etc.)
- **One-line description** (mission seed)
- **Profile** (A / B / C — see Step 0)
- **Test, lint, typecheck commands** (filled into AGENTS.md and the gates)
- Whether to keep `apps/` and `packages/` (Profile A often deletes both)
- Whether to keep the example package (almost always: no)

It then runs the docs linter to confirm the result is clean. If you'd
rather do it by hand, skip to Step 3.

---

## Step 3 — Customize the load-bearing files

If you skipped the bootstrap script, work through these in order. (If
you ran the script, skim them to verify the result.)

### 3a. `AGENTS.md` (5 minutes)

The single most important file. It's the canonical agent context.

- Replace the "What this repo is" line with one sentence about your
  project.
- Replace `<install command>`, `<test command>`, `<lint command>`,
  `<build command>` placeholders with the real commands for your stack.
- Skim the "Skills available to you" list — remove any that don't fit
  your project (e.g., `new-package` if you're not a monorepo).
- Skim "Things you should not do without asking" — keep what applies.

Keep the file under ~200 lines. Detail belongs in `docs/`, not here.

### 3b. `docs/CHARTER.md` (10 minutes)

One page: mission (one sentence), scope (in-scope and out-of-scope
bullets), principles (5-7 with examples).

The out-of-scope list is the most valuable part — it's what tells
contributors and agents when a request is out of bounds. Don't skip it.

### 3c. `docs/architecture/overview.md` (5 minutes)

The map of your repo. For Profile A, this is one paragraph. For Profile
C, it's a real document.

### 3d. `docs/product/roadmap.md` (5 minutes)

Set today's date and at least the **Now** section. The other sections
can stay empty until they have content.

### 3e. `docs/product/changelog.md` (1 minute)

The bootstrap script populates this; otherwise leave the `[Unreleased]`
section in place and add real entries as features ship.

### 3f. `docs/adr/0001-*.md` (2 minutes)

This is the meta-ADR that records "we adopted this template." Set the
date and the deciders. Edit any tradeoffs to match your project.

### 3g. `README.md` (5 minutes)

Replace the placeholder header (the bootstrap script does this for you)
and the project name, description, install/run commands. Delete the
`<!-- IF YOU ARE READING THIS ON THE TEMPLATE REPO -->` comment block.

### 3h. Profile-specific cleanup

**Profile A (microservice):**
- Delete `apps/` and `packages/` entirely (your code goes in the repo
  root, or in `src/`).
- Delete `.claude/skills/new-package/` (no packages).
- Delete `.claude/agents/adversarial-reviewer.md` if you're a one-person
  team (use the in-code review pass in the work-loop skill instead).
- Trim `docs/CONVENTIONS.md` aggressively — sections on RFCs and
  per-package AGENTS.md don't apply.

**Profile B (single library/app):**
- Delete either `apps/` or `packages/` (whichever doesn't apply).
- Delete `packages/_example/`.

**Profile C (platform):**
- Delete `packages/_example/` once you have real packages.
- Otherwise, keep everything.

### 3i. Decide on the license

The template ships with **dual MIT + Apache-2.0** — the same scheme
Rust uses. Two LICENSE files (`LICENSE-MIT`, `LICENSE-APACHE`) and a
section in README.md that lets users pick either.

For most projects, keep the dual license — it gives consumers maximum
flexibility (MIT for simplicity, Apache for the explicit patent grant).
If your project requires something else:

- **Single MIT or single Apache.** Delete the file you don't want and
  trim the README's license section to one option.
- **GPL or similar copyleft.** Replace both files with the new license
  text and update README. Note this changes what downstream users can do
  with code generated from the template.
- **Proprietary / all rights reserved.** Delete both LICENSE files and
  replace with your own. Consider whether contributors need a CLA.

Whatever you pick, **fill in the year and copyright holder** in
`LICENSE-MIT` (the placeholders read `<year>` and `<copyright holders>`).

### 3j. Remove this file

Once you're bootstrapped, `USING_THIS_TEMPLATE.md` is no longer relevant
to your project — it's about the template, not your repo. Delete it:

```bash
rm USING_THIS_TEMPLATE.md
```

---

## Step 4 — Verify

```bash
python tools/lint-agents-md.py
python tools/lint-agent-artifacts.py
```

Expected output for each: all green checks, "passed."

If anything is red, fix it before your first commit. The linter is
checking the contracts the rest of the template relies on (AGENTS.md
exists, CLAUDE.md is a symlink, no legacy folders, Diátaxis structure
intact).

---

## Step 5 — First commit

```bash
git add -A
git commit -m "chore: bootstrap from agent-ready-repo"
```

You're done. Open the repo in Claude Code and try a small task — Claude
will read `AGENTS.md` automatically. If something feels wrong about
how Claude is interpreting the project, **edit `AGENTS.md`** rather
than working around it. The template gets sharper with every project
that uses it.

---

## What to do next

A few high-leverage moves for the first week:

1. **Write your first real ADR.** Pick a non-obvious decision you've
   already made (database choice, framework choice, deploy target,
   anything where there was a real tradeoff) and record it. This is
   how you learn the ADR habit before you've forgotten the reasoning.
2. **Write your first spec.** Even for a small feature. The spec
   discipline pays off most when you build it before you need it.
3. **Try the `work-loop` skill** on a non-trivial change. It's the
   default workflow for any feature, fix, or refactor.
4. **Don't run Ralph yet.** Get a feel for the in-session loop first.
   Ralph amplifies whatever your conventions are; let those settle.
5. **Adapting one pattern into an existing repo?** Use
   `tools/install-skill.py` (Path B in Step 1) for an automated copy, or
   read the skill's `SKILL.md` plus its `dependencies:` closure and port
   the pattern by hand. README.md plus this file are enough to get the
   shape; the dependency closure carries the runtime contract.

---

## Common questions

**Do I have to use all of this?**
No. The template is opinionated, but the *structure* is the load-bearing
part. Skipping a layer is fine — leaving a folder empty is fine.
Replacing a layer with your own equivalent is fine. The only thing that
breaks is removing the agent context (`AGENTS.md` + `CLAUDE.md` symlink)
or the convention boundary between living and frozen docs.

**Can I rename the folders?**
You can, but you'll need to update the linter and references. Not
recommended unless you have a strong reason.

**What if my project grows past 50 contributors?**
Read [`docs/CONVENTIONS.md` § Scaling profiles](docs/CONVENTIONS.md#scaling-profiles--how-this-template-adapts-to-different-repo-sizes)
for what to add: GOVERNANCE.md, formal RFC process, sub-team boundaries,
CODEOWNERS-driven review routing. The template doesn't get in the way of
those — it just doesn't ship them.

**What if I disagree with a convention?**
Open an RFC against the convention in your own repo. The template's
opinions are starting points, not commandments.
