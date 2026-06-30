# Plan: discovery-loop

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **agent + skill content** (markdown the harness reads) plus one **carried schema
reference** and one **carried plan-tree asset**, all in `packs/product-engineering/.apm/…` — **no
runtime, no engine, no new dependency** beyond child-4's already-shipped traceability lint. The shape:
land the **typed substrate first** (the sidecar schema reference + the plan-tree template asset),
because every other piece reads or writes against it; then the **`discovery-loop` skill** carrying the
gate state machine (consent gates, the typed verdict set, cascade-invalidation, persistence, resume),
the bounds, the supervisor topology, the security & integrity controls, and the requirements
crosswalk; then the **`discovery-lead` agent** + the **two discovery reviewers**; then the **two D6
skills** (`explore-options`, `plan-validation`) and the `de-risk-intent` / `decompose-intent`
extensions; then the **seams** (G3, self-coverage pre-G2 phase, traceability slot, backlog bridge) and
the **DRIFT-G producer** (`new-spec` `Discovery:` header + `type:` markers in `CONVENTIONS.md` § 4,
then the `--strict` flip); then the **Diátaxis guide set**; then **package** (PE version bump,
changelog, manifest, the coordinator ADR, `make build-self`); and finally the **empirical validation
run** that forces the modelled-not-run cap-pause + the security negative paths on a recursive tree.
The riskiest part is **discipline, not difficulty**: keeping it *content* (the no-engine line is the
whole bet), keeping the schema **single-sourced** in the producing skill (consumers read instances by
convention, never import), and keeping the security controls **first-class, falsifiable ACs** rather
than prose afterthoughts. Verification is overwhelmingly goal-based (presence-and-shape greps + clean
projection), with the traceability lint as the one executable conformance check and a single manual-QA
end-to-end run as the load-bearing gate for the cap / recursion / forged-consent / tamper / fan-out
transitions the spike modelled but did not run live.

> **Authoring note (updated for the implementing PR).** The spec + plan were authored against an
> already-Accepted RFC-0053; **this PR is the implementing PR** — it builds the capability the tasks
> below describe (the agent + skills + carried schema + asset + DRIFT-G + guides + ADR-0043 +
> packaging + the validation-run record), so the spec is now **Shipped** and this plan **Done**. The
> earlier "author now, build as the gated follow-on" framing (the `release-loop` / `experience-pack`
> precedent) applied to the authoring PR; it no longer holds here — the build has landed.

## Constraints

- **RFC-0053** (governing): the no-engine contract, the six decisions, the sidecar schema home (carried
  in the skill), and the validation-run + DRIFT-G spec gates.
- **RFC-0048** (foundation): this child marks D7/D8 spike-confirmed, owns all four acceptance blockers
  (DRIFT-G is #4), and carries the loop-scoped reviewer roster; the CHARTER reviewer ceiling stays a
  `work-loop`/code-review cap (tracked amendment, not a CHARTER edit).
- **RFC-0051**: `discovery-loop` is the full seven-module self-coverage home, wired as the pre-G2
  phase; conform to the cross-loop seam, never re-word it.
- **RFC-0040**: the sidecar paths obey the three-tier layout resolution (a `[discovery]` key, else a
  `.context/discovery/` default, else elicited; lazy dir creation).
- **RFC-0041 / ADR-0031**: doctrine + reference-library + reuse — no executable tooling, no new
  reviewer beyond the roster, no runtime.
- **RFC-0025**: the outer cap mirrors `work-loop`'s iteration cap; the security-lens depth keys on the
  same risk-trigger predicate.
- **ADR-0022**: the traceability slot's stable-id cross-repo references reuse the value-stream
  reference-by-version mechanism.
- **ADR-0042**: reviewer selection is keyed to loop + work type; the discovery roster is loop-scoped.

## Construction tests

**Integration tests:** the traceability lint (child-4, real Python) reads a fixture `_state/`,
reporting orphans / non-conforming slots / stale `schema_version` pre-recovery and CONVERGED after —
the one executable conformance surface; plus the append-only + **hash-chain** decision-log lint/CI
assertion (commits add-only *and* each row's hash covers the prior row's).
**Manual verification:** the end-to-end validation run — one structurally-different second example
that forces the concentration-bound + pause-at-bound-resume path on a ≥2-level recursive tree, exercises
the actual discovery reviewers, and runs the security negative paths (forged-consent self-write
rejected; in-place decision-log tamper detected; one over-threshold cascade surfaced); record the loop
trace, the lint transition, and each negative-path outcome.

## Design (LLD)

### Design decisions

- **Substrate before behaviour.** The sidecar schema + plan-tree template land first; every gate
  transition, bound, and lens write is defined against them. Traces to: AC4, AC5, AC6.
- **Data, not engine.** Recursion is `parent_id` nesting walked by one controller
  (HTN-over-blackboard); bounds are counters the controller increments; the verdict set is status edits
  + a recorded row. No scheduler, solver, or bus is ever introduced — that is the spike-confirmed bet.
  Traces to: AC1, AC2, AC12, AC16.
- **Single-owner schema, convention-read instances.** The definition lives in one skill; consumers read
  produced `_state/` by slot-name + `schema_version`, never import — so a bump moves definition +
  producer atomically and a non-conforming slot is *flagged*, not silently accepted. Traces to: AC3,
  AC9.
- **One cascade mechanism, two guards.** Every blackboard-changing verdict reuses walk-edges →
  mark-`stale` → re-run-affected-lenses; impact-before-blast + no-jumping-ahead bind every row. Traces
  to: AC11, AC12, AC13, AC29.
- **Security as falsifiable contract, not prose.** Verdict write-authority tests the *channel* (agent
  provably cannot forge the `human` row); the decision log is append-only + attested + tamper-evident
  (hash-chain *or* a named harness immutable log, verified by a lint + a tamper test); the security lens
  surfaces rather than degrades silently; lenses propose, the controller promotes; the circuit-breaker
  carries a tunable fan-out default. Traces to: AC25–AC31, AC44.
- **Producer-before-consumer for DRIFT-G.** `new-spec` emits the `Discovery:` header + `type:` markers
  first; the traceability `--strict` flip is sequenced after, downstream of the header landing. Traces
  to: AC36, AC37.
- **Adoption is a gate.** The Diátaxis set is an AC, not a someday-follow-on — the many new concepts
  make adoption risk as real as build risk. Traces to: AC40.

### Data & schema

The five working slots (`blackboard`, `open-questions`, `traceability`, `decision-log`, `meta`) + the
committed durable artifacts (`domain-framing`, `scope-boundary`, `journey-map`, `service-blueprint`,
`screens/`, `decision-brief` incl. the required success-metrics slot, `backlog`, the validation-plan
slot), with three partitioned status namespaces and a per-verdict cross-namespace write-set table.
Layout: one directory per initiative under the RFC-0040 discovery root, `_state/` (Tier 1) vs
committed-durable (Tier 2), lazy creation, stable-id cross-linking. Slot data-classification
(`public`/`internal`/`sensitive`/`regulated`) gating the checkpoint write + retention/export
expectations. Traces to: AC4, AC7, AC8, AC24, AC31.

### State & control flow

The gate ladder G0 → G1 → G1.5 → convergence loop → (self-coverage pre-G2 phase) → G2 → G3 handoff;
the answer-each-other ripple (lenses bounce through the open-questions queue); the rejection/recovery +
cascade-invalidation transition; the typed verdict transitions; the paused-at-bound transition; the
resume re-entry by per-node status. Traces to: AC10–AC15, AC17, AC33.

### Failure, edge cases & resilience

Forged consent (harness-attested channel + a negative test), blackboard poisoning (lens proposes /
controller promotes), denial-of-convergence (cascade circuit-breaker + budget accounting + a forced
over-threshold test), silent security degrade (surface on boundary), under-classified one-way door
(enum + mandatory gate), in-place log tamper (hash-chain + a tamper test), resume of a torn-down store
(Tier-2 re-hydration + per-gate snapshot), recursion explosion (depth/breadth bounds). Traces to: AC13,
AC15, AC25–AC31, AC44.

## Tasks

> Grouped into phases; each task is a coherent commit/PR. `Depends on:` lists prior task IDs. Every
> AC1–AC44 maps to at least one task below.

### T1: Sidecar schema reference — the typed substrate

**Depends on:** none

**Tests:**
- Goal-based: `packs/product-engineering/.apm/skills/discovery-loop/references/sidecar-schema.md`
  exists and defines the five slots with the field-sets (AC4), the three partitioned status namespaces
  + the per-verdict cross-namespace write-set table (AC5), the one-tree-per-initiative forest layout +
  `_state/`-vs-committed split + lazy creation + stable-id cross-linking (AC7), the structural
  anti-drift rule "read instances by convention, never import the definition" + the `schema_version`
  stamp (AC3, AC9), and the slot data-classification levels + retention/export (AC31).

**Approach:**
- Author the reference from RFC-0053 § Decision 2 + § Security & integrity (data-classification). Stable
  ids per ADR-0022.

**Done when:** the reference exists with every slot / field / namespace / layout / classification named
and the single-source / convention-read rule stated.

### T2: Plan-tree template asset

**Depends on:** T1

**Tests:**
- Goal-based: `packs/product-engineering/.apm/skills/discovery-loop/assets/plan-tree.<ext>` exists — a
  node = `intent` slot + `parent_id` + the per-node status lifecycle, a sub-idea index, the D6
  candidate-set + selection (not-chosen retained `rejected`/`parked`), and the per-node validation
  status + hook (AC6, AC22).

**Approach:**
- Author the instantiable scaffold; `discovery-lead` copies it per initiative.

**Done when:** the asset exists and the traceability lint can walk it.

### T3: `discovery-loop` skill — gate state machine, bounds, topology, security, crosswalk

**Depends on:** T1, T2

**Tests:**
- Goal-based: the skill `SKILL.md` (+ `references/` depth) carries: the recursion-is-data
  HTN-over-blackboard framing (AC2); the checkpoint-to-harness-store-not-main cadence gated by the
  classification check (AC8); the consent-gate pause / option-card + the resume design (AC10, AC15);
  rejection/recovery cascade-invalidation (AC11); the typed verdict table with all seven rows + the two
  integrity guards (AC12, AC13); two-tier persistence (AC14); the bounds + the paused-at-bound
  transition (AC16, AC17); solo / lens-team topology + the no-chat invariant (AC18); the security &
  integrity controls as enforced behaviour, falsifiably (AC25–AC31); the BRD/PRD/SRS/RTM crosswalk as
  guidance (AC38); and the loop-skill doctrine (two-loop split + surfacing-predicate stall clause),
  with **no `CONVENTIONS.md` operating-model section** (AC41).

**Approach:**
- Author `SKILL.md` + `references/` depth files from RFC-0053 §§ Decision 1–5 / Security & integrity /
  Folding-in-requirements / The-seam. Frontmatter trigger per the skill-discovery rules.

**Negative check (no engine):** `git diff origin/main` adds no scheduler / daemon / service / message
bus / solver — only markdown content + the schema/asset files.

**Done when:** every grep above passes and the negative check holds.

### T4: `discovery-lead` agent + the two discovery reviewers

**Depends on:** T3

**Tests:**
- Goal-based: `packs/product-engineering/.apm/agents/discovery-lead.md` exists (upstream supervisor,
  peer of `work-loop`'s supervisor, hands off at G3 — AC1); `discovery-threat-reviewer.md` +
  `discovery-reliability-reviewer.md` exist as **distinct collision-hardened names**, required at G2,
  degrade-in-depth-not-to-nothing (AC19); the diff adds **no fourth `work-loop` code-review lens** and
  records the CHARTER-ceiling-stays-a-code-review-cap amendment (AC20).

**Approach:**
- Author the three agent defs; cross-reference RFC-0048's roster table.

**Done when:** the three agents exist with the named distinctions and the amendment is recorded.

### T5: D6 skills — `explore-options` + `plan-validation` + intent-suite extensions

**Depends on:** T2, T3

**Tests:**
- Goal-based: `explore-options` (generate candidate shapes across altitude × mechanic) and
  `plan-validation` (validation plan + primary-research instrument scaffolds) skills exist; running the
  sessions is out of charter (AC21); `de-risk-intent` gains a validation-hook field, `decompose-intent`
  gains an optional ranking step, and a validation-plan slot is added (AC22); provisional-spine emission
  + grounded/surfaced/to-validate labelling is wired (AC23); and the decision-brief template carries the
  required success-metrics / North-Star slot (AC24).

**Approach:**
- Author the two PE skills; extend the two existing PE skills minimally; add the validation-plan slot +
  the required success-metrics brief slot to the schema reference (T1).

**Done when:** both new skills exist, both extensions land, provisional-spine emission is specified, and
the metrics slot is required in the brief template.

### T6: Seams — G3, self-coverage pre-G2 phase, traceability slot, backlog bridge

**Depends on:** T3

**Tests:**
- Goal-based: the skill wires the G3 handoff to `work-loop` (AC32); the self-coverage gate as the pre-G2
  phase carrying its own co-scoped seven modules (AC33); the traceability slot consumed by child-4's
  lint with the cascade walking the same edges, **naming the child-4 root→leaf reachability dependency**
  (AC34); and the backlog bridge (AC35).

**Approach:**
- Author the seam prose; carry the seven self-coverage modules co-scoped in `product-engineering`.

**Done when:** all four seams are wired and the child-4 reachability dependency is named.

### T7: DRIFT-G — `new-spec` `Discovery:` up-edge (producer), then the `--strict` flip

**Depends on:** none

**Tests:**
- Goal-based: `docs/CONVENTIONS.md` § 4 + the `new-spec` skill gain the **`Discovery:` up-edge header**
  + the discovery-artifact **`type:` markers** (spec-format, not operating-model doctrine — AC36); the
  traceability lint's `--strict` flip is wired at the G2/convergence gate **after** the header lands,
  warn-only until then (AC37). Resolves RFC-0048 blocker #4.

**Approach:**
- Edit `CONVENTIONS.md` § 4 (format only) + `new-spec` assets/SKILL; sequence the `--strict` flip
  downstream of the header.

**Negative check:** the `CONVENTIONS.md` diff touches **only** § 4 spec-format (the `Discovery:`
header + `type:` markers) — **no operating-model section** is added.

**Done when:** the header + markers ship, the `--strict` flip is sequenced after, and the negative
check holds.

### T8: Diátaxis guide set (a release gate)

**Depends on:** T3, T4, T5, T6

**Tests:**
- Goal-based + manual QA: four pages exist under `docs/guides/product-engineering/…` — Explanation,
  How-to (end-to-end + recurse + fold-in-requirements), Tutorial (a fully walked example), Reference
  (slots + plan-tree template + roster) (AC40); the tutorial walks a real example end-to-end.

**Approach:**
- Author via the `new-guide` skill per quadrant.

**Done when:** the four pages exist and the tutorial is a complete walk.

### T9: Package — coordinator ADR, PE version bump, changelog, manifest, projection

**Depends on:** T1-T8

**Tests:**
- Goal-based: a **coordinator ADR** is recorded (the ADR-0031 / RFC-0049 sibling — coordinator =
  `discovery-lead` + `discovery-loop` + carried sidecar schema, no engine, spike-confirmed) (AC39).
- Goal-based: `packs/product-engineering/pack.toml` `[pack] version` + `.claude-plugin/plugin.json`
  carry the bumped version; `marketplace.json` reconciled via `make build-self`; `discovery-lead` /
  `discovery-loop` added to the manifest; `docs/product/changelog.md` `[Unreleased]` records the new
  capability; **`core` is not bumped** for the schema (AC42).
- Goal-based: `make build-self` runs clean; the projected `.claude/…` copies match source; the dry-run
  drift gate is clean (AC43). **Authoritative path:** clear `__pycache__` under `packs/` + `.claude/`,
  then treat CI's `pip install -e` projection (or a fresh `origin/main` worktree diff) as authoritative,
  not the bare local run (reference memory *Local make build-check uses site-packages* + *stray
  `__pycache__` breaks local build-check*).

**Approach:**
- Author the coordinator ADR via `new-adr`; bump `[pack] version` (leave `[contract] version` unless the
  schema is a contract delta) + `plugin.json`; `make build-self`; add the manifest + changelog entries;
  confirm `core` untouched.

**Done when:** the ADR lands, build-self is clean, the bump + changelog + manifest land, and `core` is
unbumped.

### T10: Empirical validation run — force the cap-pause + security negative paths on a recursive tree

**Depends on:** T1-T9

**Tests:**
- Manual QA, end-to-end: run `discovery-loop` on **one structurally-different second example** that
  **forces a cap hit** on the **concentration-bound + pause-at-bound-resume** path (AC17), walks a
  **≥2-level recursive tree**, exercises the **actual discovery reviewers**, and runs the security
  negative paths — a forged-consent self-write that is rejected/flagged, an in-place decision-log tamper
  that is detected, and one over-threshold cascade that surfaces; record the loop trace, the
  traceability lint's orphan → CONVERGED transition, and each negative-path outcome (AC44). A full live
  on-`omnigent` run is recorded as a nice-to-have, not gated.

**Approach:**
- Promote a note-11 / note-12-style walk; inject the bound hit + the three negative paths deliberately;
  run the real reviewers.

**Done when:** the run is recorded with the forced cap-pause/resume, the three negative-path outcomes,
and the lint transition observed.

## Rollout

- **Delivery:** agent + skill content + one carried schema reference + one carried asset, projected by
  `make build-self`. Reversible — if reverted, the `product-engineering` pack loses the capability;
  nothing irreversible, no data migration. The capability is **additive** to the pack.
- **Infrastructure:** none — the contract is harness-neutral and ships no runtime; the harness
  (omnigent or a successor) supplies the runner, the HITL-attested verdict channel, and the
  checkpoint store.
- **External-system integration:** none in this catalogue; an adopter's harness must provide the
  agent-untokened verdict channel and the durable checkpoint store/branch (named as a hard
  harness-conformance precondition, AC25).
- **Deployment sequencing:** schema/asset (T1, T2) → skill/agent/reviewers (T3, T4) → D6 + seams (T5,
  T6) → DRIFT-G producer then `--strict` flip (T7) → guides (T8) → package + ADR (T9) → validation run
  (T10). Producer-before-consumer for DRIFT-G is load-bearing. Merge of the *implementing* PR is gated on
  RFC-0053 / RFC-0048 acceptance (satisfied by construction — the RFC is Accepted in the authoring PR).

## Risks

- **The no-engine line slips into shipping a runtime.** Mitigation: T3's negative check is an explicit
  absence-grep (no scheduler/daemon/service/bus/solver); the adversarial review keys on it; Option C is
  a hard Never-do.
- **The schema drifts across the three efforts that touch it** (child-4's lint, RFC-0049's release
  loop, `work-loop`). Mitigation: single-owner definition + convention-read instances + a
  `schema_version` conformance lint (AC3, AC9) — no shared cross-pack definition exists to drift.
- **The cap / recursion / security-negative transitions stay modelled-not-run.** Mitigation: T10 is a
  hard spec gate that forces the concentration-bound + pause-at-bound-resume path *and* the three
  security negative paths on a recursive tree — the RFC states the cap risk honestly as residual scale
  risk; the security negatives are added so the controls are falsifiable, not asserted.
- **DRIFT-G lands consumer-before-producer**, flipping `--strict` before specs carry the `Discovery:`
  header → mass false failures. Mitigation: T7 sequences the header first and keeps the lint warn-only
  until it lands.
- **A stray `__pycache__` or projected-path edit trips the local build-self drift gate.** Mitigation:
  edit only the source under `packs/product-engineering/.apm/…`, clear `__pycache__` before the dry-run,
  verify against a clean tree (reference memory *stray `__pycache__` breaks local build-check*).
- **Security controls degrade to prose.** Mitigation: AC25–AC31 are hard ACs; the verdict
  write-authority AC tests the *channel*, the decision-log AC ships a hash-chain + tamper test, and the
  circuit-breaker AC carries a tunable default + a forced over-threshold test; the security-reviewer
  pass at spec stage and on the diff keys on them.

## Changelog

- 2026-06-30: initial plan. Authored against RFC-0053 (flipped to Accepted in this PR) as the single
  implementing spec the RFC's § Follow-on names — owning the coordinator contract, the D6 scaffold, the
  security ACs, the seams, DRIFT-G (RFC-0048 acceptance blocker #4), the guides, and the validation-run
  spec gate. Spec is Draft; the build is the gated follow-on (the `release-loop` / `experience-pack`
  precedent). After spec/security review: numbered the spec's 44 ACs, added the success-metrics
  brief-template slot (AC24) + the coordinator ADR (AC39), and strengthened the security ACs
  (tamper-evidence hash-chain + test, verdict-forgery negative test, cascade fan-out default + forced
  test, classification gate on the checkpoint write) — all reconciled into the task AC references here.
- 2026-06-30: **implemented.** This PR built T1–T10 — the `discovery-loop` skill + references +
  self-coverage modules + plan-tree asset, the `discovery-lead` agent + the two discovery reviewers,
  the `explore-options` / `plan-validation` skills + the `de-risk-intent` / `decompose-intent`
  extensions, the DRIFT-G `Discovery:` up-edge producer (with the `--strict` flip sequenced after),
  the four Diátaxis guides, ADR-0043, the PE 0.9.0 bump + changelog, and the validation-run record
  (the executed traceability-lint orphan→CONVERGED transition + the modelled cap-pause / security
  negative paths). Spec → **Shipped**, plan → **Done**. Adversarial + security + quality review
  applied: anchored the decision-log hash-chain (the bare chain is re-chainable by the writing agent),
  pinned resume to re-derive `human` provenance from the untokened store, added an absolute-count
  companion to the cascade fan-out gate, required an untrusted-content marker for lens writes, made
  the validation-run negative paths honest (`degraded — harness-conformance precondition, not
  demonstrated`), corrected the AC34 reachability claim to name-the-dependency + flag the child-4 gap,
  and surfaced two follow-ups (eval coverage; child-4 reachability) in `docs/backlog.md`.
