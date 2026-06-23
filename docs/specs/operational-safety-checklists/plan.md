# Plan: operational-safety-checklists

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Build a second progressive-disclosure depth library by **copying the proven
shape** of `security-checklists`, then wire its consumer and routing. The work is
a new skill directory plus three small prose edits, ordered so the modules exist
before anything routes to them:

1. **Scaffold the skill** — `packs/core/.apm/skills/operational-safety/SKILL.md`
   (front matter + "How it loads" + the reliability-vs-security carve) and the
   six `references/*.md` modules, each grounded per the RFC-0041 module table and
   written tool-neutral.
2. **Add the routing table** to `work-loop` SKILL.md so the orchestrator loads
   matching modules on the infra/destructive trigger and inlines them into the
   `quality-engineer` brief.
3. **Wire the consumer** — a one-line note in `quality-engineer.md` that it
   consumes orchestrator-inlined `operational-safety` depth (mirroring how
   `security-reviewer` consumes `security-checklists`).
4. **Add the deferred-authority pointer** to `security-checklists`'
   `config-misconfig.md` (URL-free, version-free) and state the carve in both
   skills.
5. **Manifest + projection** — exclude `operational-safety` from `[pack.evals]`,
   bump `core`, `make build-self`, run the three lint surfaces, changelog.

The riskiest part is **content discipline, not mechanism**: keeping the six
modules MECE (especially the deliberate `state-and-idempotency` ÷
`drift-and-rollback` split), tool-neutral, and on the reliability side of the
carve — the `quality-engineer` read at REVIEW is the lens-fit check. The
mechanism itself is a known-good copy of `security-checklists`. Verification is
goal-based (structure, wiring presence, pointer hygiene, projection, lint) +
judgmental (carve correctness, tool-neutrality). No production test file.

## Constraints

- **ADR-0031** — operational safety → `quality-engineer` (no new reviewer);
  doctrine + reference library only, no executable code; the
  reliability-vs-security carve against `security-checklists`.
- **RFC-0041** — six modules exactly (Decision 4); state/drift kept separate;
  observability the sixth; the URL-free deferred-authority pointer.
- **ADR-0018** — the orchestrator-loaded progressive-disclosure mechanism this
  reuses; the routing is table-driven, reused as-is for a second library.
- **ADR-0023** — three-reviewer ceiling; `quality-engineer` is the consumer.
- **`security-checklists`** — the structural template; mirror its SKILL.md
  sections and `references/` shape rather than inventing a new one.

## Construction tests

Per-task checks live under each task's `Tests:` subsection (goal-based or
judgmental — no production test file). Cross-cutting:

**Integration tests:** none beyond per-task checks.
**Manual verification:** after `make build-self`, confirm `.claude/skills/
operational-safety/` is projected with all six modules, and read the
`work-loop` routing table + `quality-engineer` note in their projected form to
confirm they reference the library coherently.

## Design (LLD)

n/a — a new prose reference-library skill plus prose wiring edits. No application
LLD; the module taxonomy (the "design") is fully specified by the spec's
Acceptance Criteria and grounded in the RFC-0041 module table. The skill's
structure is a deliberate mirror of `security-checklists`, not a fresh design.

## Tasks

### T1: Scaffold the `operational-safety` skill (SKILL.md + six modules)

**Depends on:** none

**Tests:**
- `ls packs/core/.apm/skills/operational-safety/references/` returns exactly the
  six named files (spec AC: six modules, exact names).
- `grep` SKILL.md for the front-matter `description`, the "How it loads
  (orchestrator-driven, not self-discovered)" section, and the
  reliability-vs-security carve (spec AC: skill exists, mirrors the pattern;
  carve stated).
- Each module carries a greppable `> **Grounded in:**` line naming its **exact**
  RFC-table groundings (spec AC3 pins them per module: state-and-idempotency →
  F1.2/F1.3; blast-radius → F3.1/F3.2; environment-isolation → F3.3;
  cost-and-teardown → F3.4/F3.5; drift-and-rollback → F1.4/F2.6;
  observability-and-smoke → F2.2 + taxonomy follow-up), `grep`s for its coverage
  terms, and contains no tool-specific normative sentence (illustrative examples
  labelled) (spec AC: grounded greppably + tool-neutral).
- `drift-and-rollback.md` `grep`s for the unresolved auto-remediation tension
  (gate-it vs auto-sync), surfaced not resolved (spec AC: six modules —
  drift-and-rollback).
- `find packs/core/.apm/skills/operational-safety/ -type f` returns only `.md`
  files and there is no `scripts/` dir — the skill ships prose only (spec AC: no
  executable mechanism).

**Approach:**
- Copy the `security-checklists/SKILL.md` skeleton; rewrite the `description`,
  "How it loads", carve, and the three-bucket legend for the operational lens.
- Author the six modules from the RFC-0041 module table and `0041-notes/
  research.md` groundings (F1.2/F1.3, F3.1/F3.2, F3.3, F3.4/F3.5, F1.4/F2.6, and
  the observability follow-up). Keep `state-and-idempotency` (write-path
  convergence) distinct from `drift-and-rollback` (divergence detection +
  recovery).

**Done when:** the six files exist; SKILL.md mirrors the security-checklists
shape; no module binds to one IaC tool; no executable code is present.

### T2: Add the `operational-safety` routing table to `work-loop` SKILL.md

**Depends on:** T1 (the table routes to modules that must already exist)

**Tests:**
- `grep` `work-loop` SKILL.md for the `operational-safety` boundary→module
  routing table and confirm it instructs loading 1–N matching modules (never a
  flat march of all six) into the `quality-engineer` brief on the
  infra/destructive trigger (spec AC: routing table).

**Approach:**
- Mirror the existing `security-checklists` boundary→module table; add it at the
  REVIEW `quality-engineer` dispatch (and the orchestrator-loads description), so
  the operational depth loads the way the security depth already does.

**Done when:** the grep matches; the table coexists with the security routing
table without duplicating it; this edit targets the **`quality-engineer`** bullet
of the REVIEW "Specialist reviewers" step — distinct from `infra-aware-work-loop`'s
P5 edit to the **`security-reviewer`** bullet of the same step (see Risks).

### T3: Wire `quality-engineer` as the consumer

**Depends on:** T1

**Tests:**
- `grep` `quality-engineer.md` for the one-line note that it consumes
  orchestrator-inlined `operational-safety` depth without self-discovering the
  skill (spec AC: consumer wiring).

**Approach:**
- Add a single note to `quality-engineer.md` mirroring how the agent already
  relates to its inputs; do **not** rewrite its review checklists (out of scope).

**Done when:** the grep matches; the note states `quality-engineer` is the
consumer and no new reviewer is introduced; the rest of the agent is unchanged.

### T4: Deferred-authority pointer in `config-misconfig` + carve both ways

**Depends on:** T1

**Tests:**
- `grep` `security-checklists/references/config-misconfig.md` for the
  pointer naming CIS Benchmarks + the three providers' well-architected security
  guidance by document name (spec AC: deferred-authority pointer).
- `grep` the added block for `http`, `www`, or a version pattern → **no match**
  (spec AC: pointer hygiene; spec Testing Strategy).
- Confirm the reliability-vs-security carve is stated in both
  `operational-safety` and `security-checklists` (spec AC: carve stated both ways).

**Approach:**
- Add the thin pointer to `config-misconfig.md`, naming stable publisher +
  document only and noting the real depth lives in the self-updating scanner.
- State the carve in `security-checklists` SKILL.md (it already scopes itself to
  security; add the one-line "operational config → `operational-safety`" pointer)
  and in `operational-safety` SKILL.md (the converse).

> **Note — additive edit to a shipped skill.** The `security-checklists` side
> of this task (the `config-misconfig` pointer + the SKILL.md carve sentence) is
> the *only* edit in this PR that touches already-shipped, in-the-wild skill
> content; adopters get the new prose on their next pull. It is strictly
> additive — one pointer sentence in `config-misconfig.md` + one carve sentence
> in `security-checklists` SKILL.md — and changes **no existing check**.

**Done when:** both greps match; the no-URL/no-version grep is empty; the carve
reads symmetrically in both skills.

### T5: Eval exclusion, build-self, lint surfaces, version bump, changelog

**Depends on:** T1-T4

**Tests:**
- `packs/core/pack.toml` `[pack.evals]` excludes `operational-safety` with a
  naming comment (spec AC: eval exclusion).
- `make build-self` exits 0 and projects `.claude/skills/operational-safety/`
  with all six modules; `git status` shows no unexpected reverts.
- `make build-check`, `python tools/lint-agent-artifacts.py`, and `python
  tools/lint-agents-md.py` all exit 0 (spec AC: projection + lint).
- `git diff` shows `loop-cohort.py` / `lint-spec-status.py` byte-unchanged (spec
  AC: no executable mechanism).
- `core` version bumped; `marketplace.json` reflects it; `docs/product/
  changelog.md` `[Unreleased]` entry present (spec AC: release hygiene).

**Approach:**
- Add the `[pack.evals]` exclusion comment. Bump `core`. `make build-self`. Add
  the changelog entry. Run the three lint surfaces by hand.

**Done when:** all gates green; projection clean; manifest + changelog updated.

## Rollout

- **Delivery:** big-bang prose addition, fully reversible (delete the skill dir +
  revert the three wiring edits + version bump). Nothing irreversible.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** land `infra-aware-work-loop` first (or both in one
  PR) — both edit `work-loop` SKILL.md; this spec's routing-table edit is cleaner
  to apply once the infra-flavor prose exists. The `operational-safety` modules
  (T1) must exist before the routing table (T2) references them.

## Risks

- **Co-edit collision with `infra-aware-work-loop`.** Both specs edit `work-loop`
  SKILL.md at the REVIEW "Specialist reviewers" step, but at **different bullets**:
  this spec adds its routing table at the **`quality-engineer`** bullet; the
  sibling's P5 edits the **`security-reviewer`** bullet (plus the verification-mode
  step and the PLAN pre-EXECUTE secure-design step). Each bullet is touched by
  exactly one spec. Mitigation: sequence (the sibling first) or single PR; the
  conflict is small and mechanical.
- **Carve blur.** Security config drifting into an operational module, or
  reviewers confused about who owns IaC config. Mitigation: the carve is stated
  in both skills' front matter + the routing table; the `quality-engineer` read
  at REVIEW is the lens-fit check.
- **Over-segmentation** — six modules tempt a reviewer to skip some. Mitigation:
  the orchestrator loads 1–N by routing, never all six; the RFC's taxonomy
  follow-up justifies each as a distinct failure-mode family.
- **Pointer rot.** Mitigation: publisher + document name only, no URL/version;
  the real depth lives in the self-updating scanner, so a stale name never gates
  a real check.
- **Tool-specific drift** in a module. Mitigation: examples labelled
  illustrative; adversarial pass checks for stack-binding.

## Changelog

- 2026-06-23: initial plan (follow-on to Accepted RFC-0041; authored alongside
  ADR-0031 and the `infra-aware-work-loop` spec in a docs-only PR; implementation
  is a separate later PR).
