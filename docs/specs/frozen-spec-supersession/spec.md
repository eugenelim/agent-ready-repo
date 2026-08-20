# Spec: frozen-spec-supersession

- **Status:** Shipped (§ Survey's register anchor `frozen-spec-supersession-survey` was closed by [`frozen-doc-supersession-annotations`](../frozen-doc-supersession-annotations/spec.md), which also corrects this § Survey's counts; not a supersession — every decision here stands)
- **Owner:** eugenelim
- **Plan:** none — see § Named deviation
- **Mode:** full (governance surface — it writes a rule into
  `docs/CONVENTIONS.md`, the repo's source of truth for document lifecycle, and
  annotates two frozen documents)
- **Constrained by:**
[ADR-0084](../../adr/0084-nosec-reason-delimiter-and-stderr-as-a-gate.md)
  (the supersession being recorded);
  [ADR-0027](../../adr/0027-adr-format-is-madr-aligned-but-lean.md)
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Named deviation from full mode

The `loop-engine` / `loop-cohort` state machine was not run, and there is no
`plan.md`. The two human approval gates it sequences were **granted up front by the
requester** as a standing instruction to carry this through to merge.
`adversarial-reviewer`
was run.

## Objective

ADR-0084 reversed ADR-0017's Bandit suppression-comment form. ADR-0017's Status
line already carries a partial-amendment pointer to it. Its **implementing
spec** does not — and that spec and plan are where the old form is actually
taught, at nine sites — three in `spec.md`, six in `plan.md`. A reader who
starts there follows a rule the repo no
longer keeps.

The two file edits are the trivial half. The durable half is writing down the
mechanism, so the next frozen-doc supersession is not decided from scratch.

## Decision 1 — the carrier is the `Status` field, not `Constrained by:`

`Constrained by:` is the better *semantic* fit: it is the field that cites the
ADRs governing a spec, and ADR-0084 now governs this one. It was still
rejected, for four reasons:

1. **No new exemption is needed.** `CONVENTIONS.md` § Document lifecycle already
   makes `Status` mutable on a frozen document ("Status fields can change
   (Accepted → Superseded), bodies cannot"). Using `Constrained by:` would
   extend body-mutability to a second field — an extension of the rule rather
   than an application of it, to say something `Status` already says.
2. **It matches the precedent at the other end of the pointer.** ADR-0017 itself
   was annotated on its Status line, as were ADR-0001, 0013, 0015 and 0016. One
   mechanism at both ends beats two.
3. **`Status` is the shorter carrier for "in part".** Not the only one —
   `docs/specs/copilot-full-parity/spec.md:6` carries a `supersedes-in-part`
   clause inside its `Constrained by:` field, so the field demonstrably can
   express it. But it does so in a long parenthetical inside a citation list,
   where `Status` says it in five words at the top of the document. (An earlier
   draft of this spec claimed only `Status` *could*; that was wrong, and is
   corrected here rather than quietly dropped.)
4. **`Constrained by: ADR-0017` is still true.** It records what governed the
   spec when it shipped. Amending it would rewrite history; annotating `Status`
   adds to it.

## Decision 2 — a shipped `plan.md` is frozen, and the ambiguity was the defect

`CONVENTIONS.md:103` puts "shipped `specs/*`" in the Frozen class, which reads
as the whole directory. The plan template's own contract line says "Unlike the
spec, this document is allowed to change as you learn." Those appear to
conflict, and an agent resolving it in the moment could go either way.

**Resolution: the licence is phase-scoped, not standing.** "As you learn" holds
while the plan is `Drafting` or `Executing` — while there is still something to
learn. Once the plan is `Done` and the spec `Shipped`, the work is over and both
are history. A plan editable forever would be a second, unversioned account of
what we did, competing with the ADR that records why.

So the plan is Living before ship and Frozen after, and gets the same Status
annotation as its spec. Both readings are now written into `CONVENTIONS.md`,
which is Living — **the ambiguity itself was the real defect**, and fixing it
there is the durable half of this change.

## Acceptance Criteria

- [x] **AC1 — the spec carries the pointer.**
      `docs/specs/sast-sca-tooling/spec.md`'s Status line reads
      `Shipped (superseded in part by ADR-0084 — …; everything else stands)`,
      linking the ADR. No body line changes.

- [x] **AC2 — the plan carries it too.** Same *form* of annotation (its own
      wording, naming task T3) on
      `docs/specs/sast-sca-tooling/plan.md`'s `Done` status, per Decision 2. No
      body line changes.

- [x] **AC3 — the status token still parses.** `parse_status` from
      `lint-spec-status.py`, run against the *edited* file, returns exactly
      `Shipped` — confirmed by construction, not inferred from the docstring —
      and `lint-spec-status.py --root . --base-ref origin/main` exits 0 with
      invariant (i) clean.

- [x] **AC4 — the general rule is written down.** `docs/CONVENTIONS.md`
      § Document lifecycle gains § *Superseding a frozen document*: the Status
      carrier, the form for both `spec.md` and `plan.md`, the four rules
      (say "in part"; point at the ADR; annotate both ends; never touch the
      body), and the explicit rejection of `Constrained by:` with its reason.

- [x] **AC5 — the freeze unit is disambiguated.** The same section states that a
      spec directory freezes as a unit and that the plan's "allowed to change"
      licence is phase-scoped, so the two statements no longer appear to
      conflict.

- [x] **AC6 — § Spec metadata contract points at it.** The status-vocabulary
      bullet records that there is no `Superseded` token, that `Archived` is not
      a substitute, and that a supersession is an annotation on the existing
      token — with a link to the lifecycle section.

- [x] **AC7 — the projected copy matches its source.** `docs/CONVENTIONS.md` is
      a projection of `packs/core/seeds/docs/CONVENTIONS.md`; both carry the
      change byte-identically, so `catalogue verify`'s drift check passes.

- [x] **AC4b — the rule does not forbid maintenance the repo performs.** Rule 4
      carves out meaning-preserving mechanical rewrites (path/link renames).
      Without it the convention would have forbidden `84d79223`, which rewrote
      references across 156 files under `docs/specs/` including shipped ones,
      and would block fixing `lint-spec-status.py`'s current invariant-(iii)
      warnings on a frozen spec.

- [x] **AC4c — the file no longer contradicts itself.** Two other sentences in
      `CONVENTIONS.md` carried the same ambiguity and are amended with it: the
      unconditional plan licence, and "the spec is reference material that
      should be updated alongside behavior changes" — which flatly contradicted
      the Frozen row. Fixing one copy and leaving two would have left the defect
      Decision 2 exists to remove.

- [x] **AC4d — the template is fixed at source.** The plan template's contract
      line — the text an author actually reads — now carries the phase scope, in
      `packs/core/.apm/skills/new-spec/assets/plan.md` and both projections.

- [x] **AC8 — gates pass.** `SKIP_SAST=1 make build-check` exits 0 and
      `lint-spec-status.py` reports `spec metadata clean`.

- [x] **AC9 — other candidates are surveyed, not fixed.** § Survey below records
      every shipped spec that cites a superseded ADR and carries no pointer.

## Survey — other frozen documents in the same position

Asked for as a sanity check; **deliberately not fixed here**.

**Teaching reversed content: only this one.** Grepping every `docs/**.md` for
the reversed suppression form finds it in four locations
(`sast-sca-tooling/` counted as one, since it spans spec and plan): ADR-0017 and
ADR-0084 (which quote it while explaining the reversal — correct usage),
`bandit-nosec-comment-hygiene/spec.md` (same), and
`docs/specs/sast-sca-tooling/`. Note the brief listed one occurrence in
`spec.md`; there are three (`:44`, `:147`, `:154`), plus six in `plan.md`
(`:146`, `:151`, `:154`, `:159`, `:161`, `:164` — all inside task T3).
That does not change the work — bodies stay frozen and one Status annotation
covers the document — but the annotation covers more than expected.

**Citing a superseded ADR without a pointer: 12 specs.** Scan scope matters:
this counts the `- **Constrained by:**` header only, not body mentions — a
plain grep returns roughly twice as many. A weaker signal, since
citing ADR-0017 does not mean a spec teaches the reversed spelling — most cite
it for the gate itself, which stands. Recorded for whoever picks this up:

| Superseded → by | Specs citing it with no pointer |
| --- | --- |
| ADR-0017 → ADR-0084 | `infra-aware-work-loop`, `local-gate-ci-parity`, `npm-sca-gate`, `operational-safety-checklists`, `security-reviewer-shift-left` |
| ADR-0023 → ADR-0042 | `architect-design-reviewer`, `infra-grounding`, `operational-safety-checklists` |
| ADR-0013/0015/0016 → ADR-0040 | `copilot-full-parity`, `copilot-skills-and-web`, `cursor-full-parity`, `gemini-full-parity` |

Not fixed here because the fix is **not** identical: each needs a judgment about
whether the superseded sub-decision is one that spec relied on, and ADR-0040 and
ADR-0042 supersede different sub-decisions than ADR-0084 does. Doing them
mechanically would stamp "superseded in part" onto specs that are wholly
unaffected, which is worse than no annotation. Recorded as
`frozen-spec-supersession-survey`.

## Boundaries

### Always do

- Always annotate both ends: the superseding ADR names what it supersedes, and
  the superseded document points forward.
- Always keep the projected `docs/CONVENTIONS.md` byte-identical to its seed.

### Ask first

- Ask before annotating a frozen document whose superseded sub-decision it may
  not actually rely on. A false "superseded in part" is worse than silence.

### Never do

- Never edit the body of a frozen document, including an "additive" append.
- Never introduce a `Superseded` status token; the vocabulary is closed and the
  linter enforces it.
- Never use `Archived` for a superseded spec — the feature shipped and is live.

## Testing Strategy

Goal-based; the linter is the gate:

- `parse_status` run against the edited `spec.md` returns `Shipped`. Executed,
  not inferred — the brief asked for confirmation by construction and the
  docstring alone would not have proven the annotation's link syntax is safe.
- `lint-spec-status.py --root . --base-ref origin/main` → exit 0,
  `spec metadata clean`.
- `SKIP_SAST=1 make build-check` → exit 0, including `catalogue verify`'s
  seed↔projection drift check, which is what caught the first attempt editing
  only the projection.

## Assumptions

- `plan.md` status is out of `lint-spec-status.py`'s v1 scope, so the plan
  annotation is unenforced by the linter. Stated rather than relied on: the
  plan's form matches the spec's so that a future v2 extension needs no
  migration.

## Declined

- **Adding a `Superseded` token to the status vocabulary.** It would need a
  linter change, a migration of the existing annotated statuses, and a decision
  about what "superseded in part" means as a single token. The annotation
  carries strictly more information for no schema change.
- **Amending the frozen bodies at their nine sites.** Forbidden, and the
  operative instruction already lives in `bandit.yaml`'s header — a Living file,
  at the point of use.
- **Fixing the 12 surveyed specs.** See § Survey.
