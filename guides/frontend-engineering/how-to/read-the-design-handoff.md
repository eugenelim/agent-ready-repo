---
title: Read the design handoff
summary: What the frontend pre-flight reads from your design directory, what it ignores, what each skip and refusal means, and the limits of every control on this page.
pack: frontend-engineering
kind: how-to
---

# Read the design handoff

Use this when your team already has design work — an aesthetic direction, screen
briefs, a token taxonomy — and you want the frontend build to honour it instead of
inventing a look of its own.

You do not run anything. The pre-flight does this before it writes code. This page
tells you what it will and will not do, so you can tell a correct run from a
wrong one.

## What it reads

Set `output_dir` in the `[design]` section of your `agentbundle-layout.toml`. The
repository file is read first; a user-profile file is read when the repository one
is absent or has no `[design]` key.

Under that directory, three paths, where `<slug>` is the surface or product name
you give:

| What | Where | Must declare |
|---|---|---|
| Aesthetic direction | `direction/<slug>.md` | `type: creative-direction` |
| Per-screen brief | `screens/<slug>/<screen>.md` | `type: screen-flow-brief` |
| Token taxonomy | `tokens/<slug>.md` | `type: token-taxonomy` |

From each file it takes the first `# ` heading, the frontmatter as it finds it,
and the body as one block.

## What it ignores

**Section names.** It keys on no heading inside your files. Design templates are
scaffolds people edit — a real direction doc often shares no section name with the
template it started from — so a reader that looked for named sections would find
nothing in most real artifacts.

**HTML comments.** Commented-out content is removed before anything is used or
shown you. The screen-brief template ships with commented sections, and text that
renders invisibly should not reach the build.

**Instructions inside your files.** Content describes design intent. If a brief
contains a sentence shaped like a command, it is read as content, not followed. A
path inside a file is text, not something to open — the pre-flight reads three
files and no fourth.

**Files that are not these artifacts.** A file matching a read path whose `type:`
is missing or different is skipped, and the scan continues. Design directories
hold many kinds of document; that is expected, not an error.

## What "skipped" means

A skip means nothing was there to read. The build falls back to its own canonical
reference set for whatever is missing, and carries on.

- **No `[design]` section configured** — neither layout file names one. Nothing is
  read; the canonical set supplies the aesthetic reference.
- **No conforming artifact** — the directory resolved, but nothing in it matches a
  read path with the right `type:`. Same fallback.
- **One slot empty** — say you have a token taxonomy but no direction doc. The
  taxonomy is used, and the canonical set fills the direction slot only.

## What "refused" means

A refusal means something was wrong. The whole handoff read stops, the build halts
in a named state, and it waits for you. It does not quietly fall back, pick a
different file, or fix the problem itself. There are six:

- **Reserved tree.** The directory resolves into the agent's own source or
  installed-skill directories. Never confirmable — change the configured path.
- **Outside the approved root.** A file or folder resolves somewhere the approved
  directory does not contain, usually through a symlink. The refusal reports the
  resolved path so you can see where the read would have gone.
- **Bad slug.** The slug must be lowercase letters, digits and single hyphens, at
  most 64 characters. A slug that does not fit is refused before any path is
  built, and it is **not** repaired into a tidy one — you are asked for a
  conforming name. A silently corrected slug would read a different product's
  files while reporting success.
- **Confirmation declined.** See below.
- **A bound exceeded.** At most 12 matching files, 128 KiB per file, 2 directory
  levels, 200 entries per directory. The refusal names which one.
- **Something could not be read.** An unparseable layout file, an `output_dir`
  that is missing or not a string, a file that cannot be opened, a symlink loop.

## When it asks you to confirm

If the approved directory is a personal vault, or anywhere outside this
repository, the pre-flight asks you about **each** artifact before using it. It
shows you the approved root, which configuration file named it, the file's path
relative to that root, its first heading, and its frontmatter.

It asks because nothing in these files says which product they belong to. `slug`
names the surface *or* the product. The screen brief has no `slug` at all. A
heading may say either. A shared vault holding two products' work will hand you a
same-named file from the wrong one and nothing in it will look wrong.

So the confirmation is the whole check. It is never reported as "belonging
confirmed" — you confirmed it, not a test. Declining is a refusal, not a skip.

## The limits of all of this

Worth knowing before you rely on it.

**These are instructions, not a guarantee.** Everything here is guidance the agent
follows. No gate enforces it, and a skipped check leaves no trace — the read
succeeds and looks ordinary. If you need a guarantee rather than a strong default,
enforce it outside the agent: in filesystem permissions, or a tool that refuses
the read.

**A refusal cannot unread a file.** By the time a check on content can fire, the
file has been read. A refusal bounds what is shown, recorded and written into your
code; it does not remove what was already loaded. If some content must never reach
the agent at all, keep it out of the configured directory.

**Content is not inspected.** This release reads your files and treats them as
data, but does not normalise unusual characters in them, strip paths out of them,
or limit how much of one is shown at a confirmation prompt. Those need an
executable reader and are not in this release.

**Go deeper:** the full contract, including exactly what is taken from each
artifact, is in the pack's `references/design-handoff.md`.
