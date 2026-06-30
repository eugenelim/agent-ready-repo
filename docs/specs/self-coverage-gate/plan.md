# Plan: self-coverage-gate

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **prose in one skill plus one markdown reference file** — no code, no new
dependency, no CONVENTIONS edit. The shape: edit `packs/core/.apm/skills/work-loop/SKILL.md`
to (a) **name** the passes it already runs as the self-coverage gate's steps, (b) add the two
net-new spec-time/DECIDE checks (the resolve-vs-surface **disposition record** and the
**conditional domain-grounding** check), and (c) add **one** refusal item to the end-of-session
checklist; then seed a self-contained `references/self-coverage/resolve-vs-surface.md`
from note 09; then `make build-self` to project, bump `core`, and record the changelog entry.
The riskiest part is **discipline, not difficulty**: keeping the slice genuinely *thin* — naming
existing passes rather than duplicating REVIEW, and routing everything net-new through the
already-progressive spec time — so the build loop does not acquire a design-convergence battery
it should never carry. Verification is overwhelmingly goal-based (grep for the named prose and
the refusal item; confirm the projection is clean and no CONVENTIONS line moved), closed by one
dogfood pass that produces the gate's own coverage record for this spec.

## Constraints

- **RFC-0051** (governing): the `work-loop` adoption is the **thin slice only** (disposition
  record + conditional domain-grounding); the full seven-module gate is `discovery-loop`'s.
- **RFC-0048 § Amendments 2026-06-29**: operating-model doctrine is per-loop **skill** doctrine
  — **no CONVENTIONS operating-model section**.
- **ADR-0042**: the fresh-context step reuses the existing work-type-keyed roster; no new
  reviewer, no fourth core-loop lens.
- **RFC-0025**: right-size with the existing light/full mode — no second knob.
- **RFC-0041 / ADR-0031**: the reference-library-carried-by-the-loop idiom — prose + a routing
  table, no runtime.

## Construction tests

**Integration tests:** none beyond per-task checks (the change ships no executable code).
**Manual verification:** the T6 dogfood — produce the resolve-vs-surface disposition record for
this spec and append it as a read to the seeded reference; record the produced record.

## Design (LLD)

### Design decisions
- **Name, don't duplicate.** The fresh-context-adversarial step *is* REVIEW; the pre-mortem
  hook *is* the PLAN assumption trio + declined-pattern register; the resolve-vs-surface bones
  *are* `Surface` + DECIDE's apply/defer routing. The edit adds cross-references and a phase
  name, not parallel machinery (Principle 2 — no duplication). Traces to: AC1, AC9.
- **Net-new attaches to spec time.** The disposition record and the conditional
  domain-grounding check live at PLAN/DECIDE under the existing light/full mode, never at
  EXECUTE and never as a separate convergence battery. Traces to: AC2, AC3.
- **Non-skippability = named phase + one mechanical refusal.** Reuse the exact shape the
  done-checklist already enforces (reviewer-clean, doc-drift); the coverage record's absence is
  mechanically detectable, joining refusals the loop already honors. Traces to: AC4, AC6.
- **Self-contained resolve-vs-surface reference.** The reference states its own append-only discipline inline so the
  `core` pack ships with zero CONVENTIONS dependency; `patterns.jsonl` is cited as precedent,
  not required as a contract. Traces to: AC5, AC7.
- **Ship as ordinary pack content.** The edits project through `make build-self` like every
  pack-content change; the `core` version bump (`pack.toml` + `plugin.json`, marketplace
  re-aggregated) and the changelog entry ride the same PR. No new dependency, no new file type.
  Traces to: AC10, AC11, AC12.

## Tasks

### T1: Name `work-loop`'s existing passes as the gate's steps

**Depends on:** none

**Tests:**
- Goal-based: `grep` the source SKILL.md shows the literal phrase **"self-coverage gate"**
  **named as a phase the loop runs** (not a self-discovered skill) — the phase-naming half of
  AC6, keyed on that exact token — with
  REVIEW identified as the fresh-context-adversarial step, the PLAN assumption trio +
  declined-pattern register as the pre-mortem hook, and `Surface` + DECIDE's apply/defer routing
  as the resolve-vs-surface bones (AC1, AC6). No new pass is introduced (the PLAN/REVIEW/DECIDE
  headings and their existing bodies are unchanged except for the added naming/cross-references).

**Approach:**
- Edit `packs/core/.apm/skills/work-loop/SKILL.md`: add a short "self-coverage gate" framing
  (a named phase the loop runs, not a skill it may discover) that points at the existing
  passes by name, with a one-line cross-reference each. Keep it lean — no restating of REVIEW.

**Negative check (the thinness guarantee):** scope `git diff origin/main` to the existing
REVIEW / PLAN / DECIDE section bodies — those bodies are byte-unchanged except for added
naming/cross-reference lines. A duplicated pass body (the risk this AC exists to forbid) shows
up as a body-line change and fails the check.

**Done when:** the grep above passes, the negative check holds (no REVIEW/PLAN/DECIDE body
line changed beyond added cross-references), and the diff adds naming/cross-references only.

### T2: Add the resolve-vs-surface disposition record + conditional domain-grounding

**Depends on:** T1

**Tests:**
- Goal-based: `grep` the source SKILL.md shows, at spec time / DECIDE, a **resolve-vs-surface
  disposition record** that marks every open item resolved-with-referent or
  surfaced-with-reason (value-origination / irreversible-risk / value-conflict / failed
  referent), governed by the light/full mode (AC2).
- Goal-based: `grep` shows a **conditional domain-grounding** check that fires only on an
  ungrounded load-bearing domain claim and degrades to "the spec already grounds this",
  explicitly distinct from the EXECUTE contract-grounding gate (AC3).

**Approach:**
- Add the two checks to the PLAN (spec-time) / DECIDE prose, each one short paragraph, each
  noting it is governed by the existing light/full mode (small in both).

**Negative check (no second knob — Boundary `spec.md` Never-do):** `git diff origin/main` adds
no new mode *definition* — the two checks reference the existing light/full mode but introduce
no added `light`/`full` mode-definition heading or new right-sizing knob (references are fine,
a new definition is not).

**Done when:** both greps pass, the negative check holds, and neither check introduces a new
mode or knob.

### T3: Add the one end-of-session-checklist refusal item

**Depends on:** T1

**Tests:**
- Goal-based: the DECIDE end-of-session checklist contains exactly one new refusal item — *do
  not declare done until the resolve-vs-surface disposition record exists and every
  fresh-context finding is resolved* — phrased like the existing reviewer-clean / doc-drift
  items, and the light-mode relaxation note covers it the same way (AC4, AC6).

**Approach:**
- Insert the single refusal line into the existing checklist; touch no other refusal item.

**Counted check:** `git diff origin/main` on the end-of-session checklist block
(`SKILL.md` § DECIDE) shows exactly **one** added refusal bullet — a line-count delta of one on
that list, so a second slipped-in item fails the check mechanically, not by eyeball.

**Done when:** the checklist has exactly one added line (verified by the counted check) and the
light-mode paragraph references it consistently.

### T4: Seed the self-contained resolve-vs-surface resolve-vs-surface reference

**Depends on:** none

**Tests:**
- Goal-based: `packs/core/.apm/skills/work-loop/references/self-coverage/resolve-vs-surface.md`
  exists, carries the reads seeded from note 09, states its own
  append-only/supersede-by-new-entry discipline inline (citing `patterns.jsonl` as precedent),
  and names no `docs/CONVENTIONS.md` edit as a precondition (AC5, AC7).
- Goal-based: it is the **only** file added under `references/self-coverage/` — no heavy
  design-convergence module ships (AC8).

**Approach:**
- Create the `references/self-coverage/` dir under the `work-loop` source; write the reference with
  a short header stating the discipline, then the seeded reads lifted from note 09.

**Done when:** the file exists with the seeded content + inline discipline, and it is the sole
addition under `references/self-coverage/`.

### T5: Project, bump `core`, record the changelog

**Depends on:** T1, T2, T3, T4

**Tests:**
- Goal-based: `make build-self` runs clean; the projected `.claude/skills/work-loop/` SKILL.md
  and resolve-vs-surface reference match the source; the dry-run drift gate is clean (AC11). **Authoritative
  verification path:** local `make build-self` in a Conductor worktree runs the *sibling* (main)
  editable install and a stray `__pycache__` red-fails it (reference memory *Local make
  build-check uses site-packages* + *stray `__pycache__` breaks local build-check*); so confirm
  the projection by (a) clearing `__pycache__` under `packs/` + `.claude/`, then (b) treating
  CI's `pip install -e` projection — or a fresh `origin/main` worktree diff — as authoritative,
  not the bare local run.
- Goal-based: the PR diff touches no `docs/CONVENTIONS.md` line, adds no new agent file, and
  adds no new dependency — **AC7, AC9, and AC10 are jointly verified by this single
  diff-absence grep** (one artifact, three ACs; map them as a set).
- Goal-based: the **`[pack] version`** line of `packs/core/pack.toml` (the `0.5.0` line that
  matches `plugin.json`, **not** the `[contract] version` line) and
  `packs/core/.claude-plugin/plugin.json` carry the bumped version; `marketplace.json` is
  reconciled via build-self; `docs/product/changelog.md` `[Unreleased]` has the `work-loop`
  behavior entry (AC12).

**Approach:**
- Bump `core`'s `[pack] version` in `pack.toml` (leave the `[contract] version` line untouched)
  + `plugin.json`; run `make build-self`; add the changelog entry; confirm the absence-greps.

**Done when:** build-self is clean, the version bump + changelog are present, and the guardrail
greps confirm no CONVENTIONS edit / new agent / new dependency.

### T6: Dogfood — produce this spec's own coverage record + append a read

**Depends on:** T1, T2, T3, T4

**Tests:**
- Manual QA: a resolve-vs-surface disposition record for *this very spec* is produced (every
  open item resolved-with-referent or surfaced-with-reason) and recorded as the observed
  artifact (exercises AC2); the **conditional domain-grounding check is exercised on whichever
  branch(es) this spec honestly presents** — recording which branch each open item took, and
  recording **explicitly** if the fire branch has no honest instance on this doctrine-only spec
  (the empirical claims it rests on are RFC-0051's, already referent-grounded — the degrade
  branch) rather than fabricating a synthetic ungrounded claim (exercises AC3); and a
  corresponding read is appended to the seeded reference (the RFC-0048 D9 series-execution
  obligation).

**Approach:**
- Walk this spec's open items through the gate; write the disposition record; append one
  calibrated read to `resolve-vs-surface.md` (append-only).

**Done when:** the disposition record exists and the reference carries the new appended read.

## Rollout

- **Delivery:** doctrine + one reference file, projected by `make build-self`. Reversible — if
  reverted, the `work-loop` done-checklist degrades to its prior set (the gate is additive).
  Nothing irreversible; no data, no migration.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** source edit → `make build-self` → version bump + changelog, in one
  PR. Merge is gated on RFC-0051 / RFC-0048 acceptance (the standard series sequencing). This PR
  creates the `work-loop` per-loop reference and writes its first entry (the T6 dogfood read); the
  "appends continue in note 09 until RFC-0048 Accepted" rule (RFC-0051 Decision 6) governs the
  separate note-09 *series* reads, not this loop's own reference.

## Risks

- **The slice creeps past thin.** Mitigation: AC7/AC8/AC9 are explicit absence-checks (no heavy
  module, no new reviewer/lens, no second knob); the adversarial review keys on them.
- **Naming the passes drifts into duplicating REVIEW.** Mitigation: T1's done-when forbids a
  duplicated pass body; the edit adds cross-references only.
- **A stray `__pycache__` or projected-path edit trips the local build-self drift gate.**
  Mitigation: edit only the source under `packs/core/.apm/...`, clear `__pycache__` before the
  dry-run, and verify against a clean tree (reference memory *stray `__pycache__` breaks local
  build-check*).

## Changelog

- 2026-06-29: initial plan. Authored against RFC-0051 after the operating-model doctrine was
  relocated out of CONVENTIONS into the loop skills (RFC-0048 § Amendments 2026-06-29) — so the
  spec is skill-resident with no CONVENTIONS touch.
