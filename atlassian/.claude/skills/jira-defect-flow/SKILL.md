---
name: jira-defect-flow
description: Use this skill when the user points at a Jira defect and asks you to handle it end-to-end -- "fix PROJ-123", "work this bug ticket", "diagnose and ship a fix for this defect". The skill pulls the ticket via the `jira` skill, hands the actual fix to the `bug-fix` skill (reproduction-first, root-cause, minimum-diff, regression-test), opens a PR whose body links back to Jira, and comments + transitions the ticket. By default it stops at PR-opened; runs a dev-deploy step only if the consumer repo provides one. Do NOT use for stories, tasks, or feature work -- those go through `new-spec`.
metadata:
  version: "1.0"
---

# Skill: jira-defect-flow

This is choreography, not invention. It composes three things that already
exist:

- **`jira` skill** (sibling in this pack) — all Jira reads, comments,
  transitions, attachments. You never write a raw Jira REST call here.
- **`bug-fix` skill** (shipped by the host repo; resolved by name
  through the harness) —
  reproduction, failing test, root-cause identification, minimum fix,
  regression test, commit-body-explains-why, and tracker loopback. This
  skill does **not** re-explain that discipline; invoke `bug-fix` and
  follow it. **Stages 6–7 below are the Jira-specific mechanism for
  `bug-fix` step 9** ("loop back to the tracker") — not a separate
  obligation.
- **Reviewer subagents** (`adversarial-reviewer`, plus `security-reviewer`
  / `quality-engineer` when the diff warrants) — already wired into the
  consumer repo's work-loop.

If you find yourself writing a Jira REST call, a reproduction recipe, or
a root-cause checklist inside this skill, stop — the right place is one
of the three above.

## Cross-skill invocation — name, not path

This skill names sibling skills (`jira`, `bug-fix`) and subagents
(`adversarial-reviewer`, `security-reviewer`, `quality-engineer`) **by
their `name:` field, never by path**. Install locations vary by IDE
and scope, and skills can be renamed at install time. Path coupling
silently breaks every alternative layout.

The contract: when this skill says *"via the `jira` skill: `get-issue
$KEY ...`"*, the agent uses its native skill-dispatch mechanism to invoke
the skill registered under that name with those arguments. In Claude
Code that's the Skill tool (`/<skill-name>` or programmatic dispatch);
in other IDEs it's the equivalent. **If you find yourself writing
`~/.claude/skills/jira/...` or any other hardcoded path here, stop —
look up the skill by name instead.**

Install guidance for the named dependencies lives in `manifest.json`
under `deps.skills` and `deps.agents` — that's a *where to get them*
hint, not a runtime path.

## Prerequisites

Before stage 1, confirm:

1. The `jira` skill is installed and works in this environment. Invoke
   it: `jira: check`. Exit 0 → proceed. Exit 2 → tell the user to run
   the jira skill's `setup_credentials.sh` themselves; do not try to
   authenticate for them.
2. The `bug-fix` skill is installed (from `agent-ready-repo` or wherever
   the consumer keeps it). If not, surface the gap and stop — don't
   substitute a free-form fix.
3. `gh auth status` is green (PR opening uses it).
4. `git config user.email` looks right for this repo. If the user has a
   per-repo identity convention, do not override it.

## Lifecycle

### Stage 1 — Intake

Fetch the ticket with the fields a defect needs, via the `jira` skill:

```
get-issue $KEY --expand renderedFields,attachments,changelog,transitions
```

Check for the **three intake requirements** of a defect:

| Requirement | Where it usually lives |
|---|---|
| Environment (version, OS, browser, tenant) | `environment`, `description`, custom fields |
| Reproduction steps | `description` |
| Expected vs actual behavior | `description`, attachments |

If any are missing or unclear, **do not start work**. Via the `jira`
skill, comment on the ticket asking for the missing piece and stop:

```
comment $KEY --body "Before picking this up I need: <list>. Once those are in I'll start."
```

Do not invent reproduction steps. Do not guess the environment.

### Stage 2 — Triage & start

When intake is clean, write a short triage brief to
`.context/defects/$KEY.md`. Include: severity (your read, with reasoning),
defect class (regression / data / perf / UI / integration / other),
candidate impacted areas (file paths or modules you suspect — no fix
yet, just suspects), and any open questions.

Then **ask the user to confirm before transitioning**. The "In Progress"
move is visible to the whole team and may reassign the ticket.

Via the `jira` skill:

```
# Discover available transitions for this issue's current state:
list-transitions $KEY

# Then apply the user-chosen "start work" transition by name:
transition $KEY --to "In Progress"
```

Use `list-transitions` rather than guessing names — workflow state names
vary per project (see `references/transitions.md` for common shapes).

### Stage 3 — Hand off to `bug-fix`

Invoke the `bug-fix` skill with the triage brief and the ticket text as
context. Everything from here through "regression test stays" is owned by
`bug-fix`:

- Reproduce locally (failing test, manual steps, or captured error).
- Write the failing test (red) that pins the **observable contract**, not
  the implementation.
- Identify root vs symptom (which call site is actually wrong; can the
  same class of bug exist elsewhere).
- Minimum fix (smallest change that turns red green; refuse adjacent
  cleanup).
- Verify the fix addresses the root, not the symptom.
- Regression test stays in the suite.
- Commit body explains *what was wrong, why, and why this shape of fix*.
- Loop back to the tracker (PR URL + next transition) — `bug-fix` step 9.
  Stages 6–7 below are the Jira-specific mechanism for this; do not
  treat it as separate work.

If the user has not installed `bug-fix`, point them at
`agent-ready-repo/.claude/skills/bug-fix/SKILL.md` rather than improvising.

### Stage 4 — Branch

Generate the branch name deterministically. Two agents working the same
ticket should land on the same branch:

```bash
BRANCH=$(python scripts/branch_name.py $KEY "$SUMMARY")
git checkout -b "$BRANCH"
```

`$SUMMARY` is the Jira issue's `summary` field from stage 1. Override the
prefix with `--prefix` or `JIRA_DEFECT_FIX_PREFIX` if the repo's convention
is `bugfix/` or `hotfix/`.

### Stage 5 — Review

Before opening the PR, run the consumer repo's review pass. At minimum
`adversarial-reviewer`. Add `security-reviewer` if the diff touches a
security boundary, `quality-engineer` if you added meaningful new test
surface or new logic. Iterate until each returns `Clean — ready to commit.`

This step is not optional and not in this skill — it's in the consumer
repo's `work-loop`. Defer to it.

### Stage 6 — PR (bug-fix step 9, part 1)

Open the PR with `gh`. The PR body uses the consumer repo's template
(four questions: *what / why / how to verify / what you did not change*).
**The `Why?` section must include `Closes: $KEY`** — the PR template's
loopback contract. Put the Jira key in the title too so it shows up in
notifications.

```bash
gh pr create \
  --base main \
  --title "fix($SCOPE): <subject> ($KEY)" \
  --body-file .context/defects/$KEY-pr-body.md
```

Generate `$KEY-pr-body.md` from the template — do not paste a freeform
description. The "What did you not change" section is the most useful
field; fill it honestly.

### Stage 7 — Jira loopback (bug-fix step 9, part 2)

`bug-fix` step 9 mandates that the tracker gets the PR URL and the
next transition. This is the Jira-specific implementation. Via the
`jira` skill, discover the next transition the same way as stage 2:

```
comment $KEY --body "PR: <pr-url>. Reproduction test at <test-path>. Awaiting review."

list-transitions $KEY
transition $KEY --to "In Review"
```

The subcommand names (`comment`, `list-transitions`, `transition`)
belong to the `jira` skill — see its `SKILL.md` for the full set. If
the user has a Jira MCP installed under a different skill name instead,
the verbs are equivalent — name that skill and use the same contract.

### Stage 8 — Deploy to dev (optional, consumer-repo specific)

This stage is *beyond* `bug-fix` step 9 — the upstream skill stops at
"PR + transition". Dev-deploy is environment-specific and only runs
when the consumer repo provides a hook.

There is no universal "deploy to dev" command. The skill runs whichever
hook the consumer repo provides, in this order:

1. `$DEPLOY_DEV_CMD` environment variable.
2. Executable `.context/deploy_dev.sh` in the repo root.
3. Neither exists → **stop and ask the user how to deploy.** Do not invent
   a command. Do not run `terraform apply`, `kubectl apply`, `gh workflow
   run`, or any deploy-shaped command on speculation.

After the deploy succeeds, loop back to Jira once more with the dev URL
and the next transition (commonly "Ready for QA" / "Dev Deployed").

## Don't

- **Don't transition the ticket past your scope.** "Done" / "Closed" is
  QA's call, not yours.
- **Don't skip stage 1's intake check.** A defect without environment,
  repro, or expected-vs-actual is a question, not a bug. Comment, don't
  code.
- **Don't write the fix before `bug-fix` says you have a failing test.**
  That ordering is what makes "minimum diff" verifiable.
- **Don't re-implement Jira API calls here.** If the `jira` skill is
  missing a verb you need, extend that skill — don't shim around it.
- **Don't hardcode transition names** (`"Code Review"` vs `"In Review"` vs
  `"Ready for Review"` all exist in the wild). Always go through
  `list-transitions` and confirm with the user.
- **Don't invent a deploy command.** Stage 8 is opt-in.
- **Don't invoke the `jira` skill's `delete-issue` (with or without `--yes`) — ever, in any flow.**
  Defects don't get deleted; if a ticket is wrong, the team transitions
  it to "Won't Fix" or "Duplicate".
- **Don't add `Co-Authored-By` to commits** unless the repo asks for it.
  Check the repo's local git config / CLAUDE.md before assuming.

## Edge cases

- **The ticket is not actually a defect** (it's a feature request, a
  question, or a duplicate). Stop, comment to that effect, and ask the
  user whether to convert the issue type or close it. Do not run this
  skill on a non-defect.
- **Repro is environmental and you can't get the environment** (prod data,
  customer-specific config). Document what was tried, comment on the
  ticket with the gap, and stop. "Couldn't reproduce on my machine" is
  a hypothesis, not a closing condition (see `bug-fix` anti-patterns).
- **The fix turns out to need a spec** (multiple files, new behavior
  surface, architectural change). Stop and hand off to `new-spec`; this
  skill is for defects, not for refactors discovered while debugging.
- **PR template doesn't exist in the consumer repo.** Use the four-question
  shape (what / why / how to verify / what you did not change) manually
  and flag the gap to the user — the template should be added.
- **Jira workflow has no transition out of the current state for your
  user** (permission issue). `list-transitions` returns an empty array;
  surface this and ask the user to either grant permission or to apply
  the transition themselves. Do not try to backdoor it via `update-issue`.

## Examples

See [`references/examples.md`](references/examples.md) for three end-to-end
patterns: full happy path, intake-blocked-by-missing-info, and the
no-deploy-hook case.
