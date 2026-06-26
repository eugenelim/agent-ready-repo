# pre-execute-review — spec-stage review depth (full doctrine)

> **Loaded when:** a pre-EXECUTE review trigger fires during PLAN — a **spec
> amendment** or a **structural change** (adversarial), or the
> **security-boundary** trigger (secure-design). `SKILL.md` keeps the triggers
> and the one-line dispatch; the depth — how the reviewer measures, the re-plan
> re-fire, the gate mechanism, the Profile-A opt-out, and the infra-mandatory
> secure-design pass — lives here.
> **Why progressive disclosure:** the *triggers* are evaluated every full-mode
> PLAN, but this depth only matters once a trigger actually fires on a given
> loop, so it loads on demand rather than sitting inline.

## Adversarial spec/plan review — how the reviewer measures

Both triggers route to the same reviewer mode and the same spec-stage checklist;
what differs is the standard the reviewer measures against.

When the **structural-change** trigger fires, the reviewer checks the plan
against the spec's **Boundaries** section (defined by the `new-spec` skill's
bundled `spec.md` template) — primarily `Never do` for hard structural rules and
`Ask first` for the ones that require sign-off; `Always do` for positive defaults
the plan must honour. If `Boundaries` is empty, that's the finding to surface
first — an empty Boundaries section is a spec-stage gap, **not** a fallback cue.
Only when the spec has no Boundaries section at all (an unmigrated template, say)
fall back, in order, to: the PLAN step's **declined-pattern register**, and the
AGENTS.md **"Check before acting"** list (when installed elsewhere this slug
arrives as a fragment under `docs/AGENTS.fragments/`; merge the items the adopter
wants into their own AGENTS.md).

## Re-fire on mid-EXECUTE re-plan

If EXECUTE discovers a missing or wrong task and updates `plan.md` per the
*Design tests up front* rule, re-evaluate the structural-change checklist against
the updated plan. If a re-plan introduces any of the four conditions (new module
boundary / new dependency / new abstraction layer / new top-level directory) that
the original plan did not, the trigger re-fires and the reviewer re-runs before
EXECUTE resumes. This is where most over-engineering emerges in practice — a
tempting abstraction surfaces mid-flight, not during the original PLAN — so the
one-shot trigger is not enough.

## Why early, and the gate mechanism

Cheap-to-fix-early applies harder to specs and structural decisions than to code
— catching a vague behavior, a missing `Depends on:`, a mismatched verification
mode, or a misplaced module boundary here costs a sentence; catching it
post-EXECUTE costs a re-do. Gate mechanism is unchanged: the `loop-cohort
approve-plan` verb flips `state.json.plan_review_status` to `approved` once the
reviewer is clean; `loop-cohort check <spec-dir> --phase plan` unlocks EXECUTE.
No new state fields. **Both triggers respect the Profile-A opt-out:** skip if the
project doesn't use the reviewer at all.

## Secure-design review — net-new wiring and the infra-mandatory pass

The spec-stage `security-reviewer` dispatch is **net-new wiring** — distinct from
the adversarial-only firing above and from the separate light→full escalation use
of the same security-boundary trigger; it is not a re-use of either. The
boundary-matching `security-checklists` modules are inlined into its brief in
their **proactive-control framing**, per the
[`security-checklists` Module index](../../security-checklists/SKILL.md#module-index)
— the boundary→module routing authority.

**For infra-flavored work this spec-stage pass is mandatory, not discretionary.**
"Infra-flavored" is a **defined signal, not an ad-hoc judgement**: work that the
**destructive/irreversible risk trigger** routes to full mode *and* whose spec
matches the Module index's IaC / deploy-config entry — the same classifier that
already drives security-module loading (the spec-stage half keys this match on
the spec; the diff-stage half on the diff — same Module-index entry). When that
signal is present the `security-reviewer` runs at spec stage **regardless of** the
discretionary security-boundary trigger, and the orchestrator **force-loads** the
infra-relevant `security-checklists` modules (the candidate set the REVIEW
`security-reviewer` bullet names), loaded 1–N as the spec warrants per that Module
index. The matching diff-stage pass, the reviewer-plus-scanner pairing, and the
Profile-A / missing-subagent interaction all live in that REVIEW bullet — this is
the spec-stage half of the same non-skippable, both-stages pass. (Full
infra-mandatory detail: [`infra-verification.md`](infra-verification.md) §
*REVIEW — mandatory, multi-module security on infra-flavored work*.)
