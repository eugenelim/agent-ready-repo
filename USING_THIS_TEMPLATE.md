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

### Option A: GitHub "Use this template" (recommended)

1. On the template's GitHub page, click **Use this template** → **Create a new repository**.
2. Name your repo, set visibility, click **Create repository from template**.
3. Clone it locally:
   ```bash
   git clone <your-new-repo-url>
   cd <your-new-repo>
   ```

### Option B: Manual copy

```bash
# Clone the template
git clone <template-url> my-project
cd my-project

# Drop the template's git history and start fresh
rm -rf .git
git init
```

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
bash tools/lint-agents-md.sh
bash tools/lint-agent-artifacts.sh
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
