# Loop-engine: Mode selection and checkpoint reference

`loop-engine` is the phase FSM for full-mode work-loop. It owns
`engine-state.json` (session-local, gitignored) and has two layered
responsibilities: **A. phase tracker** (validate ordering, run the read-only
guard if one exists, record phase state) and **B. workflow orchestrator** (fire
loop-cohort mutations after each transition). Light mode never invokes either
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

Events to fire as you move through each phase. After each transition exits 0,
fire the side effect shown (B column) if one is listed.

| State | Exit event | Human gate? | Guard (A) | Side effect (B) | Modes |
|-------|-----------|-------------|-----------|-----------------|-------|
| `SPEC-PLAN-DRAFTING` | `spec-ready` | — | — | — | code, spec-plan |
| `SPEC-PLAN-REVIEW` | `reviewers-clean` | — | — | — | code, spec-plan |
| `SPEC-PLAN-REVIEW` | `findings-remain` | — | — | — | code, spec-plan |
| `SPEC-PLAN-HUMAN-GATE` | `plan-approved` | **G-plan** (human sign-off required first; `loop-cohort approve-plan` must have run before firing this event) | `loop-cohort check --phase plan` | `loop-cohort schedule <spec-dir>` | **code only** |
| `SPEC-PLAN-HUMAN-GATE` | `plan-approved` | **G-plan** (same gate) | `loop-cohort check --phase plan` | — | **spec-plan only** |
| `SPEC-PLAN-HUMAN-GATE` | `plan-rejected` | — | — | — | code, spec-plan |
| `CODE-IMPLEMENTATION` | `wave-complete` | — | `loop-cohort check --phase implement` | — | code |
| `CODE-VERIFICATION` | `wave-passed` | — | — | — | code |
| `CODE-VERIFICATION` | `gates-clean` | — | — | — | code |
| `CODE-VERIFICATION` | `gates-failed` | — | — | — | code |
| `CODE-REVIEW` | `reviewers-clean --report <path>` | — | `check-spec-status.py` (**Status:** must be `Shipped`) | `loop-cohort review record <spec-dir> --report <path>` | code |
| `CODE-REVIEW` | `findings-remain --fingerprints <h>...` | — | `loop-cohort check --phase review` | `loop-cohort review record <spec-dir> --fingerprint <h>...` | code |
| `CODE-HUMAN-GATE` | `done` | **G-pr** (human merges PR; fire only after confirmed merge) | — | — | code |
| `CODE-HUMAN-GATE` | `blocker-applied` | — | — | — | code |
| `DOC-DRAFTING` | `doc-ready` | — | — | — | doc |
| `DOC-REVIEW` | `reviewers-clean` | — | — | — | doc |
| `DOC-REVIEW` | `findings-remain` | — | — | — | doc |
| `DOC-HUMAN-GATE` | `doc-approved` | **human approves** | — | — | doc |
| `DOC-HUMAN-GATE` | `doc-returned` | — | — | — | doc |

**`wave-passed` vs `gates-clean`:** fire `wave-passed` when gates pass for the
current wave but more waves remain in the schedule (returns to
`CODE-IMPLEMENTATION`). Fire `gates-clean` only when all waves are complete and
the full diff is ready for review (proceeds to `CODE-REVIEW`).

**`findings-remain` floor:** must accompany at least one `--fingerprints` hash.
A round with no hashable findings fires `reviewers-clean` instead.

**`blocker-applied` has no side effect.** A human-returned blocker is not an
LLM review round; `iteration_count` is not incremented.

## Human-wait states and session boundaries

A session may end in any of: `SPEC-PLAN-HUMAN-GATE`, `CODE-HUMAN-GATE`,
`DOC-HUMAN-GATE`, or `DOC-REVIEW` (async external review only¹). Before ending
the session, ensure work product is committed on a named branch or open PR.

When resuming: read `loop-engine status <spec-dir>` first. If `pending_side_effect`
is non-null, resolve the incomplete transition before firing any new events (see
docs/architecture/loop-infrastructure.md §Recovery). Then wait for the human
signal before firing any event that exits a human-wait state — do not fire
autonomously.

¹ `DOC-REVIEW` is only a human-wait state when review is async/external. When
the LLM runs review itself, `reviewers-clean`/`findings-remain` may fire
autonomously.

## Valid **Status:** values in spec.md

`Draft | Approved | Implementing | Shipped | Archived`

The `check-spec-status.py` guard enforces `Shipped` before G-pr. The
`lint-spec-status.py` CI linter enforces the full enum.
