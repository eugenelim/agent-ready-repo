# Infrastructure review

Review the exact saved plan against these seven local areas. Record each area
as `covered` or `gap`, cite evidence files by id, and record each finding's
severity and open or resolved status. Keep secrets and sensitive plan bytes out
of the review record. Evidence proves file identity, not that a review was done
well; a human reviewer owns that judgment.

Bind the record's subject to the saved plan's exact SHA-256 digest and its rubric
to this checklist's exact digest. Evidence entries contain an id, a root-relative
path and the exact file digest. A covered area needs at least one evidence id;
every cited evidence id must resolve to an unchanged file. Missing coverage takes
precedence over open blockers: it yields `insufficient-evidence`. With full coverage, an open blocker
yields `blocked`; otherwise the result is `pass`. A declared pass cannot repair
a gap, stale rubric, changed plan or unresolved evidence.

Installed core reviewers, `operational-safety` and `security-checklists` are
optional additions. They run after the direct local checks and never replace a local area.
Add their findings to the same record. Stop on their refusal or failed check;
never use a weaker fallback to bypass it.

## decisions

**Read:** The checked governance summary, its effective repository instructions,
accepted decisions and explicit inputs, plus the proposed configuration and plan.
Check authority and scope in the source documents themselves.

**Blockers:** Conflicting constraints, uncertain authority, unresolved material
choices, or a plan that violates a governing requirement.

**Coverage evidence:** The checked summary and source identities, with a review
that maps each applicable constraint to configuration or saved-plan effects.
State why a constraint does not apply when needed.

## schema

**Read:** The selected engine and provider versions, dependency lock file,
live `providers schema -json` output, configuration and `validate` output.

**Blockers:** A used resource or argument absent from the live schema, a failed
validation, or schema evidence from different engine or provider versions.

**Coverage evidence:** Version and lock identities, live schema output covering
every used resource type, and successful validation of the reviewed configuration.

## plan-effects

**Read:** The saved plan's inspection output, resource actions, replacements,
deletions, unknown values and dependencies, alongside the requested outcome.

**Blockers:** Unintended deletion or replacement, effects outside the requested
scope, or unknown values that prevent judging a material effect safely.

**Coverage evidence:** Inspection output bound to the saved plan and a review
of creates, updates, replacements and deletions, including why each is intended.
Record explicit absence of risky actions when none exist.

## privilege

**Read:** Execution identity, IAM changes, resource policies, trust relationships,
network exposure and secret references in the configuration and saved plan.

**Blockers:** Unneeded broad access, unsafe trust or public exposure, secret
leakage, or permissions too weak to carry out the intended operations safely.

**Coverage evidence:** A review of effective permissions and trust for each
changed boundary, with the required actions and resources justified. Record
why this area has no changes when applicable; do not copy credentials.

## policy

**Read:** Governing security and organization policies, required policy-check
outputs and the plan effects those policies constrain.

**Blockers:** A required policy fails, is missing, or has an unresolved exception;
a plan effect violates an applicable policy.

**Coverage evidence:** Applicable policy identities and their results tied to the
reviewed input, plus any owner-approved exceptions. When no policy checker is
required, record the source and reasoning that establish that scope.

## state-impact

**Read:** Backend and workspace identity, state locking and isolation settings,
resource addresses, moved or import declarations and any proposed state changes.

**Blockers:** A wrong environment or workspace, unprotected shared state,
unplanned loss of resource ownership, or unsafe state migration or concurrency.

**Coverage evidence:** Backend and workspace identity without secrets, the
address-change assessment and any migration prerequisites. Record explicit
absence of state changes when applicable. Do not run state mutations in review.

## reversibility

**Read:** Replacement and deletion effects, data retention, backup and restore
proof, dependency order, recovery steps and the limits of rollback.

**Blockers:** Irrecoverable loss without explicit owner authorization, an
unworkable recovery path, or missing recovery evidence for a destructive effect.

**Coverage evidence:** A recovery assessment tied to the saved plan, with restore
proof or a reason no restore is needed, stop points, ownership and known limits.
Review ends at the saved plan; it never runs apply or destroy.
