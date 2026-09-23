# Amendment 001 — § Grounding invocation paths, and the dominated discovery channel

- **Date:** 2026-09-17
- **Run:** `b9900572-04c5-40b5-ac46-a02ea5b54bd5`
- **Raised at:** `CODE-IMPLEMENTATION`, wave 0, before T0 was dispatched. No task
  had started; `completed_task_ids` was empty.
- **Owner authority:** the repository owner, in session, selected the scope
  "fix the paths and the channel" when both routes were priced against each
  other. This file is that decision's repository record.

## Defect 1 — the nine derivation commands cannot run from the repository root

§ Grounding writes each command as `python3 notes/grounding/<script>.py`. There
is no `notes/` directory at the repository root, and root `AGENTS.md`
§ Development workflow requires a new top-level directory to go through the
repository decision process, so creating one is not a mechanical fix.

The established convention is the spec-local `notes/` directory: five other
specs already carry one — `skill-script-exit-2-collision`,
`wave-scheduled-supervisor`, `pack-test-boundary-remaining-packs`,
`catalogue-corporate-trust-store`, and `catalogue-curation-qa-coverage`. T0's
`Touches` field already declares
`docs/specs/catalogue-sync-dry-run/notes/grounding/`, which agrees with that
convention.

So the location is right and the commands are wrong. Until they carry the
`docs/specs/catalogue-sync-dry-run/` prefix, T0's `Done when` — "every
§ Grounding command runs from the repository root and exits 0" — is
unsatisfiable. `Done when` is a pinned contract field, so T0 was unexecutable
as approved.

**Change:** prefix all nine § Grounding derivation commands with
`docs/specs/catalogue-sync-dry-run/`. No derivation's value, oracle, or
arguments change; only the path by which each script is reached.

## Defect 2 — the discovery channel was dominated and could never fire

§ Discovery channel declares that T0 "resolves only the location and invocation
mechanics of scripts under `notes/grounding/`", refinable while T0 is unstarted.
Defect 1 is exactly that case, and T0 was unstarted when it was found.

The channel could not be used, because the plan's contract block states:

> A Grounding derivation command, value, or oracle that a criterion or
> verification obligation reads is pinned and changes only through the
> controlled amendment path.

T0's `Tests` covers **every** row of § Grounding ("Every row of § Grounding
names a script under `notes/grounding/` that exists and exits 0") and its
`Done when` reads the commands directly. Every derivation command is therefore
read by a verification obligation, so the pinning rule removed every case the
channel was written to handle. The channel was live text describing a mechanism
that could not fire.

The pinning sentence arrived as a correct round-2 repair: a reviewer sustained
that the derivations were declared amendment-free while criteria gate on them.
It over-reached by one noun. Four review rounds did not catch the domination
because each rule was checked against the artifact, not against the other rule.

**Change (option A of the two priced):** narrow the pinning rule so a
derivation's **value and oracle** stay amendment-only, while a script's
**location and invocation arguments** are refinable under § Discovery channel.
The channel's own predicate, kill condition, bounded alternative, refinable-task
set, append-only decision record, scoped review, and history preservation are
unchanged.

Option B — deleting § Discovery channel as dominated — was rejected: the owner
specified the channel with six named components, and deleting a commissioned
mechanism is a larger change than correcting the sentence that swallowed it.

## Scope of this amendment

Only `docs/specs/catalogue-sync-dry-run/plan.md`:

1. Nine § Grounding derivation commands gain the spec-directory path prefix.
2. The contract block's pinning sentence is narrowed as above.

No acceptance criterion changes. No task outcome, `Touches`, `Tests`,
`Done when`, or dependency edge changes. `spec.md` is untouched; its approved
hash must come back identical.

## Scoped review

§ Discovery channel requires a refinement to re-review the changed task and its
declared dependants. This amendment changes no task section, but it changes what
T0 must invoke, so the scoped set is T0 and its declared dependants, T1 and T2.
