# Measurement protocol — frozen task set and run design

Committed because choosing the prompts is choosing part of the experiment. An
implementer who picks them makes the run unreproducible and its admission
unauditable.

## Arm order, fixed before the run

**Interleaved.** The inner loop is the arm, not the repetition: for each
repetition, each task runs against the control tree and then the treatment tree
before the next task begins. The pilot ran all nine control runs before all nine
treatment runs and confounded the arms with time; repetition does not reduce
that, so ninety-six runs in two blocks would still be two blocks.

## Permission mode

`--allowedTools Read,Grep,Glob`. Read-only, and no network-reaching tool: no
`Bash`, no `Write`, no `WebFetch`, no `WebSearch`. Read tools are the
measurement — every prompt below is "read these files and explain" — so they are
bounded rather than forbidden. Sessions run against a disposable copy; the copy
is additional containment, never an alternative to the read-only bound.

## Artifact path

Raw replies land under `.context/ablation/<timestamp>/` (gitignored). The
committed record under `notes/` is derived from them and carries no reply text.

## Admission

Each task was admitted on its own draw against the unchanged tree, listed below.
Those draws are **discarded** and are never one of the scored arms: selecting on
the same measurement that is later scored regresses to the mean and manufactures
an apparent gain under a zero-effect null. Admission requires only that the reply
clears the scorer's 30-word floor, which all three do by two orders of magnitude.

For contrast, the pilot's control runs on these same prompts scored 66.92, 51.33
and 61.82 — every one higher than its admission draw here. That spread across
independent draws of one prompt is the run-to-run variance the design exists to
read differences against.

| Task | Admission ease | Admission grade | Reply words | Admitted |
| --- | ---: | ---: | ---: | --- |
| T1 | 61.65 | 7.51 | 693 | yes — clears the 30-word floor |
| T2 | 46.46 | 10.86 | 452 | yes — clears the 30-word floor |
| T3 | 52.93 | 10.22 | 597 | yes — clears the 30-word floor |

## Frozen prompts

Verbatim. A change to any character below is a new task set and a new protocol.

### T1

```text
Read packages/agentbundle/agentbundle/build/self_host.py and then contracts/adapter.toml. Explain the relationship between EXCLUDED_PATTERNS and seed projection, and which root-level files are adopter-owned versus regenerated.
```

### T2

```text
Read packs/core/pack.toml, then read the SKILL.md of one skill it ships. Describe what this pack provides and the situations that skill is for.
```

### T3

```text
Read docs/specs/README.md and then open one active spec it lists. Describe how specs work in this repository and what that spec changes.
```

