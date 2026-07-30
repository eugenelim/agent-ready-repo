# Loop-engine: Mode selection and checkpoint reference

`loop-engine` is the phase FSM for full-mode work-loop. It owns
`engine-state.json` (session-local, gitignored) and coordinates with
`loop-cohort` as guards and side effects. Light mode never invokes either
script.

## Mode selection

Choose once at `loop-engine init`:

| Work type | Mode | `loop-engine init --mode` |
|-----------|------|--------------------------|
| Multi-task spec implementation | Full delivery | `code` |
| Spec/plan authoring only | Spec/plan drafting | `spec-plan` |
| RFC, ADR, arch doc, any review-and-approve document | Document lifecycle | `doc` |
| Light mode | — | skip — not used |

## Checkpoint table

Events to fire as you move through each phase.

| State | Exit event | Human gate? | Guards that run | Modes |
|-------|-----------|-------------|-----------------|-------|
| `SPEC-PLAN-DRAFTING` | `spec-ready` | — | — | code, spec-plan |
| `SPEC-PLAN-REVIEW` | `reviewers-clean` | — | — | code, spec-plan |
| `SPEC-PLAN-REVIEW` | `findings-remain` | — | — | code, spec-plan |
| `SPEC-PLAN-HUMAN-GATE` | `plan-approved` | **G-plan** (human sign-off required first; `loop-cohort approve-plan` must have run) | `loop-cohort check --phase plan` | code, spec-plan |
| `SPEC-PLAN-HUMAN-GATE` | `plan-rejected` | — | — | code, spec-plan |
| `CODE-IMPLEMENTATION` | `wave-complete` | — | `loop-cohort check --phase implement` | code |
| `CODE-VERIFICATION` | `gates-clean` | — | — | code |
| `CODE-VERIFICATION` | `gates-failed` | — | — | code |
| `CODE-REVIEW` | `reviewers-clean --report <path>` | — | `check-spec-status.py` (**Status:** must be `Shipped`) | code |
| `CODE-REVIEW` | `findings-remain --fingerprints <h>...` | — | `loop-cohort check --phase review` | code |
| `CODE-HUMAN-GATE` | `done` | **G-pr** (human merges PR) | — | code |
| `CODE-HUMAN-GATE` | `blocker-applied` | — | — | code |
| `DOC-DRAFTING` | `doc-ready` | — | — | doc |
| `DOC-REVIEW` | `reviewers-clean` | — | — | doc |
| `DOC-REVIEW` | `findings-remain` | — | — | doc |
| `DOC-HUMAN-GATE` | `doc-approved` | **human approves** | — | doc |
| `DOC-HUMAN-GATE` | `doc-returned` | — | — | doc |

## Human-wait states and session boundaries

A session may end in any of: `SPEC-PLAN-HUMAN-GATE`, `CODE-HUMAN-GATE`,
`DOC-HUMAN-GATE`, or `DOC-REVIEW` (when review is async). Before ending the
session, ensure work product is committed on a named branch or open PR.

When resuming: read `loop-engine status <work-dir>` first and wait for the
human signal before firing the next event — do not fire autonomously from a
human-wait state.

## Valid **Status:** values in spec.md

`Draft | Approved | Implementing | Shipped | Archived`

The `check-spec-status.py` guard enforces `Shipped` before G-pr. The
`lint-spec-status.py` CI linter enforces the full enum.
