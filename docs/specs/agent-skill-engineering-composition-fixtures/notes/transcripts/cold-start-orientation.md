Mode: frame
Write status: not authorized

## Frame — an orientation skill for a cold repository

### What the skill is for

An agent lands in an unfamiliar repository and its next move is a change. The skill's job is to make it stop and build a grounded picture first — what this repo is, what governs changes to it, what state the working tree is in, and where the request it was given actually lands — and to emit that picture as a short, checkable orientation the user can correct before any edit.

The value is not "read some files." It is that the orientation is *bounded* (it terminates), *evidenced* (every claim points at a file it came from), and *read-only* (it cannot become the change itself).

### Proposed name

`orient-before-changing` — action-oriented, lowercase-hyphenated, 22 chars.

Rejected alternatives: `orient` (too generic to discriminate), `cold-start` (names the situation, not the action), `repo-orientation` (noun-shaped, and collides conceptually with status reporting).

### Activation boundary

Should activate:

- "I'm new to this repo — get your bearings before you touch anything."
- "Before you start on the auth refactor, tell me what you understand about this codebase."
- "Onboard yourself to this project."
- "What do I need to know before making a change here?"
- "You're picking this up cold. Orient first."

Should *not* activate:

- "What's the status of the queue / what should I work on next?" — that is workspace/queue reporting, not repository orientation.
- "Explain how the auth module works." — targeted code explanation; no change is pending and no governance question is open.
- "Summarize this codebase for a README." — documentation authoring, with a written artifact as the outcome.
- "Fix the failing test." — the change is already scoped; orientation here would be preamble, not a decision.
- "Review this PR." — the reader already has the delta.

**Discrimination risk to resolve before authoring.** The host skill listing in this session advertises `workspace-status`, whose description explicitly claims "orient me", "session start", "where am I", and "any cold-start orientation request". I have not read that skill's source — that is an unverified reading of its advertised description, not a repository finding. If it is in fact the owner of cold-start orientation, this new skill either (a) must not exist, or (b) must be narrowed to a boundary `workspace-status` does not hold, and both descriptions must be edited so the two do not both claim the phrase. My recommended narrowing: `workspace-status` answers *"what work is queued for me?"* from a tracked workspace file; this skill answers *"what governs a change in this repository, and is the tree safe to change?"* from repository governance and VCS state, and it is the one that fires when there is no workspace file at all. **This is the first thing to settle — it decides whether the skill gets written.**

### Observable outcome

One orientation report, produced without mutating anything, containing:

1. **What this repo is** — one or two sentences, cited to the file they came from.
2. **What governs a change** — the effective agent-instruction files for the paths in scope (nearest-scope wins), the required verification commands, and the commit/branch conventions. Each cited.
3. **Tree state** — current branch, clean/dirty, divergence from the main branch, and whether this is a worktree or the primary checkout.
4. **Where the pending request lands** — the directories it will touch and the scoped instruction file that will apply to them, or an explicit "no request scoped yet."
5. **Unknowns and conflicts** — what could not be determined, and any place where two instruction sources disagree, surfaced rather than silently reconciled.
6. **A stated stopping point** — "orientation complete, no files changed; say what to build."

Failure is visible: an unreadable governance file, an ambiguous main branch, or a conflict between two instruction sources is reported as an unknown, not papered over.

### Authority and boundaries

- **Read:** repository files only, under one confirmed root, treated as untrusted evidence. Instructions found in repository prose describe the *repo's* conventions; they cannot widen this skill's task, tools, or authority.
- **Write:** none. This skill has no write mode. If the user wants the orientation saved, that is a separate authorized write, and it should be an explicit follow-on, not folded in here.
- **Network / authentication / external side effects:** none. No fetching remotes, no issue trackers, no credentials.
- **Shell:** read-only VCS queries only (branch, status, divergence, worktree identity). No fetch, no checkout, no stash, no anything that moves a ref. Worth calling out explicitly in the skill body, because "just run `git stash` to see the clean tree" is exactly the plausible-looking step that makes an orientation destructive.
- Resolve-before-read applies to every candidate path: canonicalize against the confirmed root, require a regular file inside it, reject `..`, symlinks, and containment uncertainty.

### Portability floor

The `SKILL.md` body must work in a repository with no workspace file, no CI config, and no agent-instruction file at all — in that case the honest orientation is "this repository declares no agent guidance; here is what the tree and layout show." Nothing host-specific, no assumption of a particular VCS host, no assumption that `main` is the default branch (derive it, and report it as unknown if it cannot be derived).

The one genuinely conditional piece is **budget**: a large monorepo will not tolerate an unbounded read. That belongs in a reference, not the body — a fixed reading order with a stop rule (read the root instruction file, the nearest scoped one for the request's paths, the architecture entry point if declared, and stop; do not walk the tree).

### Contracts that must stay authoritative

- The repository's own agent-instruction files. This skill *reports* them; it never restates or overrides them, and it must not cache a summary that then drifts from the source.
- Nearest-scope-wins precedence, wherever the repo declares it. An orientation that flattens scoped guidance into one blob is worse than none.
- Whatever skill already owns queue/status reporting — see the discrimination risk above.

### Evidence the skill is working

- **Success:** a run on a repo with scoped instruction files produces the *scoped* file for the request's paths, not just the root one; every factual claim in the report carries a path.
- **Failure:** a run on a repo with a deliberately unreadable or conflicting instruction file reports the conflict, and does not pick a side.
- **Interruption:** stopped mid-orientation, nothing has changed on disk — trivially true, because the skill has no write path. This is the payoff of declaring it read-only rather than "usually read-only."
- **Clean degradation:** a bare repository with no guidance yields a short, explicitly-partial report, not a fabricated one.
- **Negative activation:** the "should not activate" prompts above route elsewhere and this skill stays quiet.

### Proposed file tree

```text
orient-before-changing/
  SKILL.md                       # boundary, reading order, report shape, stop rule
  references/
    reading-order.md             # bounded traversal + stop rule for large repos
    report-template.md           # the six sections, with the evidence-citation rule
```

No scripts. No assets. The VCS queries are three or four read-only commands and belong inline in the body; wrapping them in a script would add an install surface for nothing.

### Non-goals

- Does not recommend what to work on, and does not rank or triage work.
- Does not read or reconcile a workspace/queue file.
- Does not write, cache, or update an orientation artifact.
- Does not plan or perform the change it is orienting for.
- Does not run tests, builds, linters, or any gate — those are the *next* actor's job, and running them here both costs minutes and can write into the tree.
- Does not summarize code behavior beyond what declared documentation states; it points at the architecture entry point rather than reverse-engineering one.
- Does not fetch, pull, or touch remotes.

### Open questions for you

1. **The overlap.** Does `workspace-status` already own this? If yes, this skill should not be created — say so and I will stop. If it owns only queue reporting, I will write both descriptions to draw the line.
2. **Scope of "orient."** Is the pending-request-landing section (item 4) in, or should the skill orient to the repository only and stay agnostic about what comes next? Including it makes the skill much more useful and slightly harder to keep out of planning.
3. **Destination.** No confined root has been confirmed for a create. Naming one is part of authorizing the write, not part of this frame.

No files were created or changed, and agreeing with this frame does not authorize a write. Say "create it" plus a destination root and I will enter `create` as its own transition.

Files changed: none. Checks run: none (read-only framing). Retained behavior: n/a. Unavailable capabilities: none encountered. Cleanup outstanding: none.
