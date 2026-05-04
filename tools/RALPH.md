# Ralph operating manual

> **Read this before running `tools/ralph.sh`.** AFK doesn't mean
> *unconsidered*; it means *pre-considered*.

Ralph is the AFK variant of the [`work-loop`](../.claude/skills/work-loop/SKILL.md)
skill: each iteration is a fresh Claude Code session, with state living in
files. This document covers when Ralph is the right tool, when it isn't, and
the hard limits the harness enforces.

## When to use Ralph

Use Ralph when **all** of the following are true:

1. **The completion criterion is fully mechanical.** Tests pass, a checklist
   in PROMPT.md is fully ticked, a benchmark hits a threshold. If "done" is
   even slightly subjective ("looks good", "feels polished"), Ralph will
   either exit prematurely or never exit. Use the in-session work-loop
   instead.

2. **The task slices into context-window-sized items.** Ralph's superpower
   is fresh context per iteration — but only if each item fits. Tasks like
   "rebuild the API" don't slice cleanly; tasks like "implement the 12 items
   in PROMPT.md, one at a time" do.

3. **Verification is reliable.** Flaky tests turn Ralph into a slot machine
   — green by chance, then red, then green. Fix the flakes first.

4. **You've already done at least one in-session pass on a similar task.**
   Ralph amplifies whatever your conventions are. If those aren't tight,
   Ralph just produces more bad code faster.

5. **You can afford the spend.** Ralph runs many iterations. Each costs
   tokens. Set a budget before starting — see [Hard limits](#hard-limits).

## When NOT to use Ralph

- "Done" is fuzzy or aesthetic.
- The work needs human judgment mid-flight (architectural choices,
  ambiguous requirements, security-sensitive trade-offs).
- The work touches sensitive surfaces (auth, payments, secrets management,
  data deletion). Use in-session with explicit human review at each step.
- You haven't written a PROMPT.md you'd be comfortable handing to a junior
  engineer. If a junior would need clarification, so will Ralph.

## Setup

### 1. Write a `PROMPT.md`

Stable across iterations. Contains the task, constraints, and an explicit
completion criterion.

```markdown
# Task: <one-line summary>

## What to do

<Concrete, scoped task. Reference the spec at docs/specs/<feature>/spec.md
if there is one. Don't paraphrase the spec — link it.>

## Constraints

- Do not modify <files / packages outside scope>.
- Use the conventions in AGENTS.md and docs/CONVENTIONS.md.
- After each completed item, update .ralph/progress.txt with a one-line
  note on what you did and what's left.

## Definition of done

- [ ] <gate-checkable item 1>
- [ ] <gate-checkable item 2>
- [ ] <gate-checkable item 3>
- [ ] All tests pass: <test command>
- [ ] Lint clean: <lint command>

When every checkbox is ticked AND the gates pass, end your output with the
line: RALPH_DONE
```

### 2. Configure gates

Either via `.ralphrc` in the repo root:

```bash
LINT_CMD="<lint command>"
TYPECHECK_CMD="<typecheck command>"
TEST_CMD="<test command>"
MAX_ITERATIONS=20
COMPLETION_PHRASE="RALPH_DONE"
```

Or via env vars on the command line.

**Gates are mandatory.** Ralph without gates is a wish. The harness will
proceed even with no gates configured, but you should not.

### 3. Decide on sandboxing

For overnight or unattended runs, **sandbox the agent**. Options:

- A container with the repo mounted but nothing else (no SSH keys, no
  cloud credentials, no home dir).
- A dedicated branch (Ralph commits to it; you review before merge).
- A worktree separated from your main checkout.

The harness does not enforce sandboxing — that's a per-team decision. But
running Ralph against a directory that contains your home dir's `.ssh/` is
asking for trouble.

## Running

```bash
# First time, with confirmation:
bash tools/ralph.sh

# Skip the confirmation (use only after you've read this file):
bash tools/ralph.sh --yes

# Watch progress in another terminal:
tail -f .ralph/live.log
tail -f .ralph/ralph.log
```

State written to `.ralph/`:

- `ralph.log` — the audit trail (timestamps, gate results, iteration boundaries).
- `live.log` — Claude's stderr stream for the current iteration.
- `last-output.txt` — Claude's stdout from the most recent iteration.
- `progress.txt` — rolling notes Claude writes between iterations. Survives
  across iterations; cross-iteration "memory."

`.ralph/` should be gitignored.

## Hard limits

The harness exits with one of these codes:

| Code | Meaning |
| ---- | ------- |
| 0 | Completion phrase found AND gates green. |
| 2 | `claude` CLI returned non-zero — environment problem. |
| 3 | Same gate failed two iterations in a row — Ralph is stuck. |
| 4 | Hit `MAX_ITERATIONS` without completion. |

**Iteration cap.** Default 20. If a task can't finish in 20 iterations,
something is wrong with the task slicing. Stop, re-plan with the work-loop
skill, then retry — don't just bump the cap.

**Loop detector.** Two consecutive identical gate failures abort the run.
This is the signal that Claude is going in circles — fixing X breaks Y,
fixing Y breaks X. Stop and surface it to a human.

**No cost cap in the harness itself.** Set one externally:
- API key with a billing limit, or
- A wrapper that watches your billing dashboard and SIGINTs the harness.

If you don't have a cost cap, don't run Ralph overnight.

## After Ralph runs

Whether it exits clean (code 0) or stuck (code 3 / 4):

1. **Read `.ralph/ralph.log`.** It's the audit trail. What went green, what
   went red, where it got stuck.
2. **Review the diff.** Even on a clean exit, review every commit. Ralph
   ships work; humans ship trust.
3. **Update `AGENTS.md` or skills with what was learned.** Ralph's biggest
   structural advantage is that lessons from each iteration land in files,
   not in a conversation that disappears. If Ralph kept rediscovering the
   same gotcha, that gotcha goes in the relevant `AGENTS.md` so the next
   loop (Ralph or human) doesn't pay for it again.
4. **If it exited stuck, write a postmortem in `.ralph/postmortem-<date>.md`.**
   What was the loop? What pattern of failure? What would have unstuck it?
   This is how the team learns where Ralph is and isn't appropriate for
   your codebase.

## In-session vs. Ralph — picking the right tool

| Property | In-session work-loop | Ralph |
| --- | --- | --- |
| Context | Single conversation | Fresh per iteration |
| State | Memory + repo | Repo + `.ralph/` only |
| Best for | Tasks needing judgment mid-flight | Mechanical, sliceable work |
| Cost shape | One bursty session | Many small sessions |
| Failure mode | Context drift in long sessions | Cost runaway, plan amnesia |
| Human role | Ambient — review as you go | Pre-flight + post-flight only |

**Default to the in-session work-loop.** Reach for Ralph when the work is
mechanical enough and large enough that supervising it is the bottleneck.
