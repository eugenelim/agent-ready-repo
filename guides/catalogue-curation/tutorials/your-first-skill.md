# Your first skill

**What you'll build:** A standard-compliant skill with valid frontmatter, shaped body, activation evals, output-quality evals, and all four lint gates passing — ready for PR review.
**Prerequisites:** `agentbundle`, `core`, `governance-extras`, and `catalogue-curation` packs installed; a clear idea of what the skill does and one situation where using it would be wrong.
**Time:** 60–90 minutes.

**Goal:** write one standard-compliant skill from scratch and land it in the catalogue.
By the end you'll have a skill with valid frontmatter, a shaped body, activation evals, and a definition of done you can verify.

This is the main journey. The side journey — bringing in skills and repos from outside — starts at [Your first assimilation](./first-assimilation.md) after you've completed this one.

**Before you start.** Read [Skill standards](../explanation/skill-standards.md) — one page that names the three standards and tells you what each is checking.
This tutorial introduces each standard at the point where it applies; the standards file is where you verify the full picture before opening your PR.

**Prerequisites:**
- `agentbundle`, `core`, `governance-extras`, and `catalogue-curation` packs installed
- A clear pair in hand: what this skill does, and one situation where using it would be the wrong choice

---

## 1. Understand the workspace your skill lives in

Before writing a line, know where your skill sits in the workspace design.

The workspace has two rooms:

```
Shaping room → [shaping_queue]              Build room → [work].queue
───────────────────────────────             ─────────────────────────
Decide what the skill does.                 Write it. That's this tutorial.
Shape it as a brief with rationale.
```

If you've come from the shaping room with a spec, your `workspace.toml` already has your work item:

```toml
[[work.queue]]
id = "skill-<your-skill-name>"
spec = "docs/specs/<pack>/<your-skill-name>.md"
status = "In Progress"
```

If you're starting ad-hoc — no workspace set up yet — that's fine.
Skills must handle both: a skill that only works when the full arc has already run is fragile.
You'll handle this in Step 3.

Run `workspace-status` at any point to see what the queue currently looks like.

**Where the skill lives on disk:**

```
packs/<pack>/
└── .apm/
    └── skills/
        └── <your-skill-name>/
            ├── SKILL.md                ← write this first
            ├── scripts/                ← cross-platform scripts (add if needed)
            ├── references/             ← context loaded on demand (add if needed)
            └── evals/
                ├── eval_queries.json   ← activation evals (Step 5)
                └── evals.json          ← output-quality evals (Step 6)
```

**Workspace vocabulary** — the verbs you'll see in other skills and in the workspace design:

| Verb | What it does |
|---|---|
| `capture-work` | Captures a new work item into the queue |
| `workspace-status` | Surfaces the current queue state without modifying it |
| `receive-brief` | Pulls a shaped brief from `[brief_queue]` into `[work].queue` |

Name your skill for what it does, not for internal mechanism.
If a skill in the codebase already uses a similar verb, align with it.

---

## 2. Write the frontmatter

Create `packs/<pack>/.apm/skills/<your-skill-name>/SKILL.md`.

```yaml
---
name: <your-skill-name>
description: >
  Use when <specific trigger situation>.
  Do NOT use when <the near-miss situation that shares keywords but belongs in a different skill>.
license: Apache-2.0
compatibility:
  claude_code: ">=0.2.0"
  kiro: ">=0.10.0"
metadata:
  boundary: filesystem_read
  scope: repo
allowed-tools:
  - Read
  - Bash
---
```

**[Standard 1 — agentskills.io structural]**
Six keys, no others: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.
`description:` is a single-line scalar (or a `>` block scalar that collapses to one line), under 1024 characters.
`lint-skill-spec.py` enforces this — it's the authority, not this page.

**[Standard 2 — Catalogue craft] `description:` is the activation signal.**
This is the most important sentence you will write.
The agent reads it to decide whether your skill applies to the user's prompt.
Write it as two sentences: "Use when [specific situation]." and "Do NOT use when [near-miss]."
The second sentence separates your skill from the two or three others that sound similar at first glance.

**[Standard 3 — OWASP AST03] `allowed-tools:` must be minimal.**
List only the tools your skill body actually instructs the agent to invoke.
Start with the smallest plausible set and add only when a step in the body genuinely requires it.
Every tool listed must be justified by the skill's stated purpose.
Over-declaring expands the blast radius of any prompt injection that reaches this skill.

**[Standard 3 — OWASP AST06] `metadata.boundary:`**
If your skill instructs code execution or file writes, declare the containment boundary here.
Accepted values: `filesystem_read`, `filesystem_write`, `network_fetch`, `shell_exec`.
"The agent will have access" without naming the scope is a finding.

---

## 3. Write the body

The body is the procedure the agent follows. Four named sections.

### Opening clause

One to three sentences. What this skill does — and one clear "not": the situation where using it would be the wrong choice.

```markdown
Summarises a thread of agent messages into a human-readable session report.
Does NOT generate new analysis or suggest next actions — use `synthesise-findings` for that.
```

The "not" sentence primes the agent to route correctly when a near-miss prompt arrives.

### Prerequisites

List what must exist before the skill can proceed. Use the three-tier policy:

- **T1 — Declare and detect.** Check for the dependency; if absent, stop cleanly.
- **T2 — Optional, gated, idempotent.** Install only if the user opts in.
- **T3 — Banned.** Never install this from a skill.

**[Craft: graceful ad-hoc handling]**

A skill that silently breaks when an earlier arc step hasn't run is fragile.
Write T1 prerequisites to handle direct invocation gracefully:
detect what's missing, name it explicitly, and stop with a clear message.

```markdown
**Prerequisites**

- Python 3.11+ on PATH.
- `jq` on PATH — detected via `shutil.which("jq")`.
  If absent: stop and tell the user. Do not attempt to install it.
- If a `workspace.toml` exists in the working directory, read the current queue item.
  If no `workspace.toml` is found: note that workspace tracking is inactive and continue
  without updating the queue. Tell the user they can run `capture-work` to set it up.
```

The workspace-absent case shows the pattern: detect, name, proceed-with-note or stop — never silently ignore.

### Instructions

Numbered steps. Each step is one concrete action the agent takes.

**[Craft: progressive disclosure]**
Detail that only matters in one branch of the workflow goes in a `references/` file.
Load it at the point the workflow reaches that branch — not pre-loaded for every invocation.

```markdown
3. Determine the thread format. Load `references/thread-format.md` now.
4. Parse the messages using the shape described in the reference.
5. ...
```

The `references/` file is not in context until Step 3 loads it.
Every invocation that doesn't reach Step 3 never pays for that context.

**[Craft: path discipline]**
Discover context from the workspace's own structure at runtime.
Do not hardcode paths that are only valid in your environment.

Wrong:
```markdown
3. Read from `/Users/yourname/projects/myproject/.agentbundle/state/`.
```

Right:
```markdown
3. Find `.agentbundle/` by walking up from the current working directory.
   If not found, stop: the skill requires an installed pack.
```

This is what makes the skill portable — any workspace with the pack installed gets consistent behavior.

### Arc handoff

When the skill's main work is done, suggest the next step in the arc.
Do not invoke the next skill automatically — name it and let the user choose.

```markdown
## Next steps

The summary has been saved to `<output-file>`.

When you're ready:
- Review the summary, then run `export-catalogue` to produce the redistributable bundle.
- Or run `workspace-status` to see the full queue before deciding what's next.
```

The arc handoff pattern is what makes a series of skills feel like a coherent journey
rather than a collection of unrelated commands.
Each skill knows about the next step in its arc and surfaces it — but leaves the choice to the user.

### Status pairing

If your skill modifies shared state — writes to a ledger, updates a queue, creates a record —
pair it with a `<subsystem>-status` skill.

The status skill reads the current state and reports it.
It does not modify state.
It lets the user check where things stand without triggering a side-effect.

Example: `assimilate-primitive` writes to the assimilation ledger.
`catalogue-curation-status` reads that ledger and reports what's been assimilated, what's pending, what failed.

If your skill creates or mutates shared state, check whether a status skill for the subsystem already exists.
If it does, update it to include the new state.
If it doesn't, create one named `<subsystem>-status`.

---

## 4. Write cross-platform scripts (if needed)

Scripts go in `scripts/`. Always Python — not shell scripts.

```python
#!/usr/bin/env python3
"""Format a message thread into a session report."""
from __future__ import annotations
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    tool = shutil.which("jq")
    if not tool:
        print("jq not found on PATH. Install it and retry.", file=sys.stderr)
        sys.exit(1)

    thread = Path("thread.json")
    if not thread.exists():
        print(f"Expected thread file not found: {thread}", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        [tool, ".messages[]", str(thread)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    print(result.stdout)


if __name__ == "__main__":
    main()
```

Rules: `pathlib` for all paths; `encoding="utf-8"` on every file and subprocess; `subprocess` as a list, never `shell=True`; `shutil.which()` for tool detection, not `command -v`.

---

## 5. Author activation evals

This step verifies your `description:` field actually works as an activation trigger.
Run it before you think you're done — description problems caught here cost far less than ones caught in production.

Create `evals/eval_queries.json`:

```json
[
  {
    "query": "summarise the messages from last session into a report",
    "should_trigger": true
  },
  {
    "query": "what patterns appear across these agent runs",
    "should_trigger": false,
    "note": "cross-run analysis — use synthesise-findings"
  },
  {
    "query": "format the conversation thread for the team to review",
    "should_trigger": true
  },
  {
    "query": "generate action items from the session",
    "should_trigger": false,
    "note": "action generation, not summarisation"
  }
]
```

Write 8–10 `should_trigger: true` cases (the prompts that should activate this skill) and
8–10 `should_trigger: false` near-misses (prompts that share keywords but should route to a different skill).

Register the skill in `pack.toml`:
```toml
[pack.evals]
skills = ["<your-skill-name>"]
```

Run:
```bash
python3 tools/run-pack-evals.py --pack <pack>
```

**Reading the results:**
- `should_trigger: true` query scoring < 0.5: the description is too narrow or too specific — broaden the "Use when" clause.
- `should_trigger: false` query scoring > 0.5: the description bleeds into another skill's territory — strengthen or add the "Do NOT use when" clause.

Both kinds of failures tell you the same thing: the description and the test cases are your primary documentation of what this skill is for. They have to agree.

---

## 6. Author output-quality evals

Create `evals/evals.json` with at least one eval per major workflow branch:

```json
[
  {
    "name": "produces formatted session report",
    "input": "summarise the last session thread",
    "expected_output": "A markdown report with a header, a summary paragraph, and bulleted key points. No action list, no recommendations.",
    "assertions": [
      "Output contains a markdown H1 or H2 header",
      "Output contains a bullet list",
      "Output does not contain a section headed 'Next steps' or 'Actions'"
    ]
  }
]
```

Assertions must be falsifiable behavior-level statements.
"Agent does the right thing" is not an assertion — name what the output contains or does not contain.

---

## 7. Run the gates

All four must pass before the PR.

```bash
python3 tools/lint-skill-spec.py              # Standard 1: agentskills.io structural
make build-self                                # project source → adapters
python3 tools/lint-agent-artifacts.py         # verify projection is clean
python3 tools/run-pack-evals.py --pack <pack> # Standard 2: activation evals
```

After `make build-self`, confirm the skill appears:
```bash
agentbundle show <pack>
```

It should list your new skill by name.
If it doesn't appear, the pack registration is missing — check `pack.toml`.

---

## 8. Open the PR via work-loop

The adversarial review is the last gate and the one that catches what linters cannot:
scope creep, description drift against the spec, missing edge cases, and Standard 3 (OWASP AST) findings.

Load the `work-loop` skill and run the PR flow.
The adversarial review must return `Clean — ready to commit.` before merge.

---

## Definition of done

Check every item before asking for review.
The [full table](../explanation/skill-standards.md#the-definition-of-done--both-paths) is in the standards file;
this is the writing-path subset:

- [ ] `lint-skill-spec.py` passes — no errors; warnings reviewed
- [ ] `make build-self` clean; `lint-agent-artifacts.py` passes
- [ ] Activation evals: all `should_trigger: true` queries > 0.5; all `should_trigger: false` < 0.5
- [ ] `evals/evals.json` exists with at least one output-quality eval
- [ ] `agentbundle show <pack>` lists the skill by name
- [ ] `workspace-status` shows the work item as `Done` (if workspace tracking is active)
- [ ] PR open; adversarial review returned `Clean — ready to commit.`

---

Your skill is live in the catalogue.

The side journey — bringing existing skills and repos from outside into the catalogue — starts at
[Your first assimilation](./first-assimilation.md).
For the full pack arc from survey to publish, see [Catalogue operator journey](../explanation/catalogue-operator-journey.md).
