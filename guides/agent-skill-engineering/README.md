---
title: Create and improve agent skills
summary: Frame, author, review, and improve a portable skill with explicit control over writes.
pack: agent-skill-engineering
kind: how-to
---

# Create and improve agent skills

Frame, author, review, and improve a portable skill with explicit control over writes.

## Install the pack

You install the pack in your repository from a catalogue that includes it:

```bash
agentbundle install --pack agent-skill-engineering --scope repo
```

The pack supplies `author-or-update-agent-skill` and `review-or-optimize-agent-skill`. For catalogue selection and prerequisites, see [Install packs](../_shared/how-to/install-packs.md).

## Frame the skill

You ask your agent to define the task before writing files:

```text
Use author-or-update-agent-skill in frame mode. Design a skill that checks a
release note for missing migration steps. Define when it should run, its
output, non-goals, and checks. Do not write files.
```

The agent returns a read-only design: when the skill activates, what it produces, and what it may change. You decide whether that boundary fits. A skill is a `SKILL.md` instruction file with supporting references or scripts only where needed.

## Author or update the skill

After reviewing the design, you authorize creation at an exact directory inside your repository:

```text
Enter create mode. I authorize creating the framed skill at
skills/check-release-note/. State the files and checks before writing.
```

The agent confirms the confined destination and writes only the authorized files. For an existing skill, request `update` mode, name its exact root and requested change, and state which behavior must remain. A request with no clear target or change stays in read-only framing. Find the result at the agreed path; see [Find and open your files](../_shared/how-to/find-and-open-your-files.md).

## Review and measure improvements

You ask for review before authorizing another edit:

```text
Use review-or-optimize-agent-skill in review mode on
skills/check-release-note/. Check activation, portability, authority, and
verification. Report evidence and the smallest safe fixes; do not edit.
```

The agent reports findings without changing files. Optimization needs an observed failure or measured baseline, your request to change it, and an explicit transition authorizing the exact root and write set. It compares the result with that baseline; a cleanup request alone stays read-only.

These workflows cover portable skills. They do not author plugins, hooks, runtime packages, runtime profiles, or subagents. Knowledge-provider design starts read-only and needs separate write authorization.

Next: [Your first skill](../catalogue-curation/tutorials/your-first-skill.md).
