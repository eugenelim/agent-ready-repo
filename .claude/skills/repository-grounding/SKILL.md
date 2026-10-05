---
name: repository-grounding
description: Use this skill to answer "what already governs these paths?" before writing a spec, plan, or implementation. Probes the paths a change will touch and reports governing files, references, phrase pins, gates, co-change partners, and dead links — selected by stage. Use it at discovery to orient before authoring and at review to check what the authored artifacts reference. Do NOT use for provider-based code intelligence, live index queries, or any inquiry that mutates repository state.
metadata:
  boundaries: [filesystem_read_untrusted]
---

# Skill: repository-grounding

Answer "what already governs these paths?" from a seed set of paths, selected by the current stage. The inquiry reports; it never decides. Every finding is evidence for the consuming workflow to act on.

## Running the inquiry

```
python '<skill-dir>/scripts/explore-grounding.py' --root <root> --phase <phase> <seed...>
```

- `<skill-dir>`: the directory containing this `SKILL.md`, wherever the skill is installed.
- `<root>`: the repository root. Pass `.` when the working directory is the root.
- `<phase>`: one of `discovery`, `task`, `review`, or `all`. Selects the probe set for the current stage.
- `<seed...>`: one or more relative paths — files or directories the change touches.

Run from the repository root. The script resolves all paths relative to `<root>`. Pass at least one seed; multiple seeds are space-separated on the same invocation.

## Exit codes

- **Exit 0** — always, including when every probe found nothing or an input was unavailable. A probe whose input is absent reports it as unavailable; it does not fail the run.
- **Exit 2** — only when a seed path escapes the invocation root. This is the one condition that stops the tool.

There is no exit code for "found something", because a finding is never a failure.

## Probes by phase

| Phase | Probes |
|---|---|
| `discovery` | Governing files (scoped rules), path references, phrase pins, runner gates, known surfaces |
| `task` | Governing files, path references, phrase pins, runner gates, co-change history |
| `review` | Path references, dead references, co-change history |
| `all` | All probes |

At discovery, nothing is authored yet, so a dead-reference scan returns a reassuring empty result. At review, governing files are already known and the question is what the authored artifacts reference.

## What the report covers

- **Scoped rules** — which governing files sit above a seed, root-ward.
- **Path refs** — which files name a seed path.
- **Phrase pins** — which files quote a distinctive line from a seed file.
- **Gates** — which runners would execute a seed path.
- **Co-change** — which files historically move with a seed path.
- **Surfaces** — which known grounding surfaces exist and carry content.
- **Dead refs** — which paths a seed names that no longer resolve.

## Outcomes and report discipline

Every probe has distinguishable outcomes. A probe whose input can be missing reports three: found, none found, and input unavailable. A probe that reads the tree itself reports two: found or none. A probe that returns empty when its input is missing is indistinguishable from a clean result, so the unavailable outcome is always explicit.

Nothing about the repository's directory names, file types, or runner conventions is hardcoded. The script derives them at run time from the seed paths and their surroundings, so it works on any repository shape.

The report names the probes it ran and their basis. A reader who cannot see the probe set cannot tell an empty result from a probe that never ran.
