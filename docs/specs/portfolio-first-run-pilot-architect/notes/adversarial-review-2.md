# Adversarial review — round 2

**Date:** 2026-07-22  
**Reviewer:** adversarial-reviewer subagent

All round-1 findings (3 Blockers, 5 Concerns, 1 Nit) confirmed resolved.

## Blocker (new)

**1. Never-do #5 forbade what AC5 required.** spec.md:49 — Never-do #5 banned carrying the starter-prompt verbatim in files other than tutorial and pack.toml, but AC5 requires the transcript to record the input prompt verbatim. Fixed: scope to user-facing/projected files, exception added for transcript evidence record.

## Concern

**2. T2 pack-presence check targeted wrong scope.** plan.md:56 — checked `.claude/skills/architect-design/SKILL.md` (repo-scope path) but architect installs at user scope. Fixed: use `agentbundle list-installed --scope user`.

## Nit

**3. T5 grep lacked `-i` flag.** plan.md:105 — comment claimed case-insensitivity but command didn't have it. Fixed: added `-i`.
