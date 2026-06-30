# Spec: self-coverage-gate

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0051 (governing — the self-coverage goal + cross-loop seam + the `work-loop` thin slice this spec wires); RFC-0048 (the foundation; § Amendments 2026-06-29 — operating-model doctrine is per-loop skill doctrine, *not* a CONVENTIONS section); ADR-0042 (reviewer selection — keyed to loop + work type); RFC-0041 + ADR-0031 (the reference-library-carried-by-the-loop idiom, no new runtime/reviewer); RFC-0025 (the light/full progressive mode this reuses)
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An agent running `work-loop` carries the self-coverage gate's **cross-loop seam** — the
**resolve-vs-surface disposition** plus a **non-skippable coverage record** — as a *thin,
skill-resident slice* layered onto the passes `work-loop` already runs, so the build loop
proceeds more autonomously between human gates without a design-convergence battery bolted
onto it. Concretely: `work-loop`'s own doctrine **names its existing passes as the gate's
steps** (REVIEW *is* the fresh-context-adversarial step; the PLAN assumption trio +
declined-pattern register *are* the pre-mortem hook; `Surface` + DECIDE's apply/defer routing
*are* the resolve-vs-surface bones), and adds only what is genuinely net-new: a
**resolve-vs-surface disposition record** and a **conditional domain-grounding** check at spec
time / DECIDE, governed by the light/full mode `work-loop` already activates, plus **one**
end-of-session-checklist refusal item that makes the record non-skippable. The doctrine and its
one reference file (a seeded `resolve-vs-surface.md`) live **entirely within the
`work-loop` skill** — the `core` pack ships the gate with **no edit to `docs/CONVENTIONS.md`**.
Success: an agent finishing any `work-loop` session cannot declare done without a coverage
record that disposes of every open item as resolved-with-referent or surfaced-with-reason, and
the build loop gains this without a new reviewer, a new pack, a runtime lock, a second
right-sizing knob, or any of the heavy seven-module design-convergence battery (that battery is
`discovery-loop`'s, specified in RFC-0051 for RFC-0053 to carry — never built here).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Carry the gate as skill-resident doctrine.** Edit the source
  `packs/core/.apm/skills/work-loop/SKILL.md` and add the one reference file under
  `packs/core/.apm/skills/work-loop/references/self-coverage/`, then `make build-self` to
  project — never edit the projected `.claude/` copies directly.
- **Name `work-loop`'s existing passes as the gate's steps** rather than re-implementing them:
  REVIEW = fresh-context-adversarial; PLAN's assumption trio + declined-pattern register =
  the pre-mortem hook; `Surface` + DECIDE's apply/defer routing = the resolve-vs-surface bones.
- **Attach the net-new checks to the spec time `work-loop` already right-sizes** (PLAN /
  DECIDE under the existing light/full mode), so the slice is small in both modes by
  construction.
- **Reuse the existing reviewers** for the fresh-context step — selected per ADR-0042 from
  `work-loop`'s existing work-type-keyed roster (`adversarial-reviewer` always;
  `security-reviewer` / `quality-engineer` as the diff warrants) in a fresh context.
- **Make the resolve-vs-surface reference self-contained** — it states its own append-only,
  supersede-by-new-entry discipline inline (citing `docs/knowledge/patterns.jsonl` as
  precedent), so it depends on no CONVENTIONS edit to ship.

### Ask first

- **Adding any reference module under `work-loop`'s `references/self-coverage/` beyond the
  seeded resolve-vs-surface reference** — the heavy design-convergence modules are `discovery-loop`'s by
  RFC-0051 Decision 3; a new `work-loop` module is a scope change.
- **Changing the cross-loop seam wording** (the goal + resolve-vs-surface + the non-skippable
  coverage record) that `discovery-loop` / `release-loop` must also conform to — it is the
  one cross-copy invariant RFC-0051 owns.
- **Touching the other end-of-session-checklist refusal items** (reviewer-clean, doc-drift,
  clean `git status`) — this spec adds exactly one and leaves the rest as they are.

### Never do

- **Never ship a `docs/CONVENTIONS.md` edit for this gate** — the operating-model doctrine
  lives in the loop skills (RFC-0048 § Amendments 2026-06-29). The `core` pack must ship the
  gate without relying on a CONVENTIONS change.
- **Never add the heavy seven-module design-convergence battery under `work-loop`**
  (`taxonomy-walk`, `saturation-declaration`, `scenario-variation`, a standalone `pre-mortem`
  module) — those are `discovery-loop`'s, at its native altitude.
- **Never add a new reviewer agent, and never a fourth `work-loop` code-review lens**
  (ADR-0042) — the fresh-context step reuses the existing roster.
- **Never add a second right-sizing knob** — reuse `work-loop`'s existing light/full mode.
- **Never make the gate a self-discovered skill, and never build a runtime lock** — it is a
  named phase in the loop's own doctrine plus a mechanical checklist refusal (RFC-0051
  Decision 2; layer-3 structural enforcement is used where a harness offers it, never
  depended on).
- **Never add a new dependency** — the change is skill prose + one markdown reference file.

## Testing Strategy

- **The SKILL.md doctrine edits** (existing passes named as steps; the disposition record at
  PLAN/DECIDE; the conditional domain-grounding check; the one new done-checklist refusal
  item): **goal-based check** — `grep` the source SKILL.md for each named phrase and the
  refusal-item text; the contract is presence-of-prose, not a compressible invariant, so a
  unit test would be a tautology.
- **The seeded `resolve-vs-surface.md`** (seeded from note 09; self-contained
  append-only discipline; no CONVENTIONS dependency): **goal-based check** — file exists at
  the source path, contains the seeded reads and an inline append-only/supersede
  statement, and names no `docs/CONVENTIONS.md` edit as a precondition.
- **The guardrails** (no CONVENTIONS edit; no heavy modules under `work-loop`; no new
  reviewer/lens; no new dependency): **goal-based check** — `grep` the PR diff for the
  absence of a `docs/CONVENTIONS.md` change, of new `references/self-coverage/<heavy>.md`
  files, and of any new agent file.
- **Projection**: **goal-based check** — `make build-self` runs clean and the projected
  `.claude/` copies of the SKILL.md + the resolve-vs-surface reference match the source (the
  source-edit-then-rebuild discipline every pack-content change follows here).
- **End-to-end dogfood**: **manual QA** — exercise the gate on one worked example by
  producing a resolve-vs-surface disposition record for *this very spec* and appending it as a
  read to the seeded reference (the RFC-0048 D9 series-execution obligation — every effort
  runs the lens and appends its own reads). Record the produced disposition record as the
  observed artifact.

## Acceptance Criteria

- [x] `work-loop`'s SKILL.md **names its existing passes as the gate's steps** — REVIEW is
  identified as the fresh-context-adversarial step, the PLAN assumption trio +
  declined-pattern register as the pre-mortem hook, and `Surface` + DECIDE's apply/defer
  routing as the resolve-vs-surface bones — adding no new pass, only the naming.
- [x] `work-loop`'s doctrine **prescribes a resolve-vs-surface disposition record** produced at
  spec time / DECIDE: for every open item, the record marks it either **resolved-with-referent**
  (the referent cited) or **surfaced-with-reason** (value-origination, irreversible-risk,
  value-conflict, or a referent that genuinely failed). The doctrine states it is governed by
  the existing light/full mode and small in both. *(Two-part verification: the named doctrine
  prose is **present** in the source SKILL.md — goal-based grep owns this half; and a
  **conforming** record is produced once by the T6 dogfood — manual QA owns the shape half.)*
- [x] `work-loop`'s doctrine **prescribes a conditional domain-grounding check** that **fires
  only when the build rests on an ungrounded load-bearing domain claim** and **degrades to "the
  spec already grounds this"** otherwise — never a blanket gate, and explicitly distinct from the
  EXECUTE contract-grounding gate (which grounds API/library contracts, not domain claims).
  *(Two-part verification: the check's doctrine prose is **present** — goal-based grep; and the
  T6 dogfood **exercises whichever branch(es) this spec honestly presents** — manual QA —
  recording explicitly when the fire branch has no honest instance on this doctrine-only spec
  rather than fabricating a synthetic ungrounded claim to satisfy the box.)*
- [x] The end-of-session checklist gains **exactly one** refusal item: *do not declare done
  until the resolve-vs-surface disposition record exists and every fresh-context finding is
  resolved* — the same shape as the existing reviewer-clean and doc-drift refusal items, and
  it relaxes in light mode the same way those do (a surviving Blocker escalates to full mode).
- [x] A **`resolve-vs-surface.md`** ships under
  `packs/core/.apm/skills/work-loop/references/self-coverage/`, **seeded from
  [`0048-notes/09`](../../rfc/0048-notes/09-gap-resolutions.md)**'s reads, and is
  **self-contained**: it states its own **append-only, supersede-by-new-entry** discipline
  inline (an example that stops holding earns a *new* entry citing the old, never an edit;
  `patterns.jsonl` cited as precedent) and **names no `docs/CONVENTIONS.md` edit as a
  precondition**.
- [x] The doctrine makes the gate **non-skippable harness-neutrally** — it names the gate as a
  **phase the loop runs** (not a self-discovered skill) and rests non-skippability on that named
  phase **plus** the mechanical done-checklist refusal item (AC4). The doctrine **also notes**
  that layer-3 structural enforcement is used where a harness offers it but is never depended on.
  *(The box attests to one verifiable claim: the doctrine names the gate with the literal phrase
  **"self-coverage gate"** as a phase the loop runs, paired with the AC4 refusal-item text —
  goal-based grep keys on that literal phrase plus the refusal text, the way AC4 pins its own
  wording. The layer-3 sentence is doctrine content noting a posture; its presence is checked,
  but the box does not attest to a layer-3 behavior this slice builds.)*
- [x] **No `docs/CONVENTIONS.md` edit ships** for this gate; the gate is named and defined
  entirely within the `work-loop` skill. The PR diff touches no `docs/CONVENTIONS.md` line.
- [x] **No heavy design-convergence module** (`taxonomy-walk`, `saturation-declaration`,
  `scenario-variation`, a standalone `pre-mortem` module) ships under `work-loop`'s
  `references/self-coverage/` — the seeded resolve-vs-surface reference is the only file added there.
- [x] **No new reviewer agent and no fourth `work-loop` code-review lens** are added; the
  fresh-context step reuses the existing work-type-keyed roster selected per ADR-0042, and
  **no second right-sizing knob** is introduced (the existing light/full mode governs the
  slice).
- [x] **No new dependency** is added — the change is skill prose plus one markdown reference
  file.
- [x] **`make build-self`** projects the edited `work-loop` SKILL.md and the new resolve-vs-surface reference
  to every adapter, and the dry-run drift gate is clean.
- [x] The `core` pack version is bumped (`packs/core/pack.toml` **and**
  `.claude-plugin/plugin.json`, with `marketplace.json` reconciled via `make build-self`), and
  a `docs/product/changelog.md` `[Unreleased]` entry records the `work-loop` behavior change.

## Assumptions

- Technical: the `work-loop` skill source is `packs/core/.apm/skills/work-loop/SKILL.md` with
  a `references/` dir; the projected copy lives at `.claude/skills/work-loop/` and is refreshed
  by `make build-self` (source: repo read 2026-06-29 — `packs/core/.apm/skills/work-loop/`
  contains `SKILL.md`, `references/`, `scripts/`, `assets/`).
- Technical: the end-of-session checklist that gains the refusal item, the light-mode bounded
  `adversarial-reviewer` pass, and the DECIDE apply/defer routing already exist in the source
  SKILL.md (source: `packs/core/.apm/skills/work-loop/SKILL.md` § DECIDE end-of-session
  checklist + § Modes light/full).
- Technical: the resolve-vs-surface reference is seeded from the resolve-vs-surface reads in
  [`0048-notes/09`](../../rfc/0048-notes/09-gap-resolutions.md) § *The resolve-vs-surface lens
  (resolve-vs-surface reference)* (source: repo read 2026-06-29).
- Technical: `core` is at version `0.5.0`; a projected pack bump needs both `pack.toml` and
  `.claude-plugin/plugin.json`, with `marketplace.json` aggregated via `make build-self`
  (source: `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`; reference memory
  *Pack bump needs plugin.json too*).
- Process: reviewer selection for the fresh-context step follows ADR-0042 (agent additions
  keyed to loop + work type), which caps the `work-loop` code-review gate at its three lenses
  (source: ADR-0042; RFC-0051 Decision 4).
- Process/governance: the gate is **skill-resident with no CONVENTIONS edit** — the
  operating-model doctrine was relocated into the loop skills by operator direction
  (source: RFC-0048 § Amendments 2026-06-29; RFC-0051 § Follow-on artifacts → *No CONVENTIONS
  touch*; user direction 2026-06-29).
- Process/governance: this PR **creates and seeds the `work-loop` *per-loop* resolve-vs-surface reference**
  (RFC-0051 Decision 6 / § Follow-on artifacts) — a file distinct from the RFC-0048-series
  cross-cutting reads that currently live in note 09. Because this PR creates the per-loop
  reference, **its own T6 dogfood read is that reference's first appended entry** — there is no
  contradiction with the "appends continue in note 09 until RFC-0048 is Accepted" rule, which
  governs *other in-flight siblings* appending to the **note-09 series reads** (which graduate
  into the gate's reference library on RFC-0048 acceptance), not this loop's own reference.
  Merge of this implementing PR is gated on RFC-0051 / RFC-0048 acceptance — the standard
  sequencing for every child of the RFC-0048 series (source: RFC-0051 Decision 6 migration
  note; sibling Draft specs `traceability-lint`, `release-loop`, `frame-domain` author against
  the foundation).
- Product: the value of the gate (raising autonomy between human gates by substituting
  rigorous checklists for what would otherwise be surfaced) and its thin `work-loop` share are
  pre-decided by RFC-0051; this spec wires, it does not re-open them (source: RFC-0051 § The
  ask + § Proposal Decision 6 inventory; note 09's "a child must not re-litigate what the
  foundation already settled").
