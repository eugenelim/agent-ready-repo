# Plan: design-handoff-read

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` § Security and authoring rules, which
  binds every pack, and root `AGENTS.md`'s non-waivable list. Analogous
  implementation: `packs/experience-design/.apm/skills/copy-direction/SKILL.md`
  steps 1, 3 and 6 — the only place in either pack that approves a resolved
  `output_dir`, re-canonicalizes a final target, checks product belonging for
  user-profile config, and states an extraction contract over a loaded artifact.
  Its construction path is prose review, not a test: no gate reads pack
  instruction text. Named deviation: `frontend-engineering/SKILL.md` carries no
  containment prose at all, so this change authors the pattern into that pack for
  the first time rather than extending an existing step. That is compliance with
  a rule binding every pack, not a new design.

> **Plan contract:** implementation strategy. It may change substantively only
> while Status is `Drafting`. Execution observations belong in
> `notes/verification-ledger.md`.

## Approach

Five tasks in a chain. The reference comes first because it is the only artifact
here a static check can read, and it fixes the field sets the read step then
implements — authoring the step first would leave the contract to be inferred
from the step.

Review shape is **DEEP**, not mixed. There is no mechanically uniform work: every
task is either a trust-boundary control or its verification.

## Constraints

- No gate reads pack instruction prose, so nothing here fails closed. That is why
  the spec's `Never do` makes an unpaired control a blocking condition needing a
  named owner waiver rather than an accepted gap.
- A single observed refusal from a non-deterministic agent establishes that a
  control fired once, not that it holds. The paired-run requirement is the
  honest ceiling available, and each recorded observation says which half it is.
- Two of the three artifacts have no address until `design-output-addressing`
  ships, so the fixtures for this spec cannot be staged before it does.

## Construction tests

No new automated test. Stated plainly because the alternative — inventing a
prose-presence checker — certifies phrasing rather than the control, and this
repository has a recorded instance of that failure where a validator named
`_validated_root` that validated nothing scanned clean.

Two static goal-based checks stand in where they can:

- **Reference content.** `references/design-handoff.md` enumerates a field set per
  artifact, states the discard rule, states the `type:` caveat, and names the
  `[design]` section without restating its base.
- **No duplicated base.** The reference contains no `docs/` path literal, so the
  deferred base flip cannot strand it.

Everything else is paired manual QA, recorded in the ledger.

## Durable-output map

| Durable output | Tasks | Evidence |
| --- | --- | --- |
| User-facing promise | T4 | Guide present, linked, `lint-guidebook-steps.py` exits 0 |
| Interface compatibility | T1 | Reference names the section, states no base |
| Operations | T3 | Paired runs recorded per control |
| Release history | T5 | Topmost `frontend-engineering` entry names the new version |
| Reusable learning | T5 | `project-knowledge` receipt or recorded unavailability |

## Design (LLD)

### Design decisions

**Approval precedes confinement.** Without approving the resolved `output_dir`,
a prefix check confirms only that a path is under a root the adopter's config
named — and a hostile `agentbundle-layout.toml` in a cloned repository names any
absolute root. The two are one control in two parts, and this spec's first
criterion is the half that was missing.

**`type:` is a collision guard, not authentication.** It sits in the same
adopter-writable file as the content it labels, so anyone who can place the
artifact can set it. It usefully separates a token taxonomy from a direction doc;
it establishes nothing about provenance. The closed field set is the real control,
and the reference says so rather than letting a reader infer trust from a marker.

**The field set is the contract, so it lives in the reference.** A criterion
describing what an agent extracts at runtime cannot be falsified by reading
anything. A criterion requiring the reference to enumerate the set can.

**Bounds are stated, not left to the implementer.** A criterion requiring a limit
without giving its value asks the implementer to invent a decision, and an
invented limit reads as a considered one. The values come from the largest design
tree available, and the ordering claim says which fires first.

### Interfaces & contracts

The read resolves `[design] output_dir` by name — the same section
`experience-design` declares — and reads three fixed paths beneath it. It is a
consumer of that section, not a declarer: the reference is named
`design-handoff.md` rather than `agentbundle-layout.md` precisely because in this
repository the latter name means the pack writes there, and the layout
conformance test reads only files with that name.

### Failure, edge cases & resilience

| Condition | Result |
| --- | --- |
| No `agentbundle-layout.toml`, or no `[design]` section | Named skip; canonical reference list used |
| Section resolves, directory holds none of the three | Differently worded named skip |
| Repo-root value resolving outside the repository tree | Explicit confirmation before use |
| Artifact real path outside the approved root | Named refusal, distinct from both skips |
| Declared `type:` absent or wrong | Surface the collision; do not consume |
| User-profile config, artifact from another product | Surface the mismatch; do not consume |
| More than 12 matches, a file over 128 KiB, depth over 2, or a link in the scan | Surface which bound was exceeded |

## Tasks

### T1: The handoff reference

**Depends on:** none

**Tests:**
- Goal-based: the reference enumerates a field set per artifact, states the
  discard rule for content outside it, states the `type:` collision-guard caveat,
  and names the `[design]` section.
- Goal-based: the reference contains no `docs/` path literal.

**Approach:**
- Author `references/design-handoff.md` as the contract the read step implements:
  what is extracted from each of the three artifacts, what is discarded, what
  `type:` does and does not establish, and where the section comes from.
- Name it for reading. `agentbundle-layout.md` means the pack writes there, and
  the layout conformance test keys on that filename.

**Done when:** both checks pass against the file.

### T2: The read step

**Depends on:** T1

**Tests:**
- Goal-based: the step states each of the seven conditions in the Design table
  above and its result.
- Goal-based: the step sits ahead of the canonical product-reference list in the
  shared pre-flight, so the fallback is reached only when nothing resolves.

**Approach:**
- Insert the step into the shared pre-flight: approve `output_dir` source-aware,
  confirm each artifact's canonicalized real path under the approved root,
  validate `type:`, check product belonging for user-profile config, enforce the
  stated bounds, then extract the field set the reference fixes.
- State every surfaced path relative to `output_dir` plus the configuration
  source, so no absolute home path can reach an artifact or the ledger.
- Word the two skips differently from each other and from the refusal.

**Done when:** both checks pass and the step precedes the reference list.

### T3: Paired fixture runs

**Depends on:** T2, and on `design-output-addressing` having shipped, without
which two of the three artifacts have no address to stage.

**Tests:**
- Visual / manual QA, paired per control: a benign fixture holding all three
  artifacts, then one fixture per control that must make it fire — a hostile
  repo-root `output_dir` outside the tree, a symlinked `direction/` resolving
  outside the approved root, an artifact carrying an embedded instruction, a wrong
  `type:`, a foreign-product artifact under user-profile config, and a set
  breaching each bound.
- Visual / manual QA: no `[design]` section, then a resolving-but-empty directory,
  confirming the two skips read differently.

**Approach:**
- Stage fixtures with an absolute `output_dir` pointed at a temporary tree, which
  is what makes the symlink and foreign-product cases stageable rather than
  hypothetical.
- Record, per run, the fixture, the observed output, and which half of the pair it
  is. A run that cannot be staged is a blocking condition needing a named owner
  waiver in the spec, not an unverified pass.

**Done when:** every control criterion has both halves recorded in the ledger, or
a waiver recorded in the spec with its owner.

### T4: Guide

**Depends on:** T2

**Tests:**
- Goal-based: `tools/lint-guidebook-steps.py` exits 0.
- Goal-based: the new guide is linked from `guides/frontend-engineering/README.md`.

**Approach:**
- Write `how-to/read-the-design-handoff.md`: what the agent reads, from where, what
  it ignores, and what the two skips and the refusal mean to a reader. Add its
  index row. `tools/check-guide-index.py` cannot observe page reachability, so the
  index row is checked by reading it, not by that tool.

**Done when:** the lint exits 0 and the index row resolves.

### T5: Release surface

**Depends on:** T3, T4

**Tests:**
- Goal-based: `agentbundle catalogue verify --root .` exits 0, which owns the
  `pack.toml` / `plugin.json` version agreement.
- Goal-based: the topmost `frontend-engineering` changelog heading names its new version.
- Goal-based: the skill's `evals/evals.json` carries a case covering the handoff read.

**Approach:**
- Bump `frontend-engineering` (minor — a new reference and a new pre-flight step)
  in `pack.toml` and `plugin.json`; regenerate `marketplace.json` by self-host.
- Route learnings through the `project-knowledge` seam.

**Done when:** the three checks pass and `git status` is clean.

## Rollout

No runtime component. An adopter with no `[design]` section sees the named skip and
the unchanged canonical reference list, which is the current behaviour — so a
frontend-only adopter is unaffected. An adopter with the design pack installed and
configured gains the handoff on upgrade.

## Risks

- **The controls cannot be verified beyond a paired run.** Accepted and stated:
  no gate reads pack prose. The mitigation is that the pairing is required rather
  than optional, and an unstageable case blocks on a named waiver.
- **A fixture cannot be staged honestly.** Most likely for the foreign-product
  case, which needs a user-profile config pointing outside the repository. If it
  cannot be staged, the criterion is waived by a named owner, not quietly passed.
- **The bound values prove wrong in practice.** They are calibrated against one
  tree — this repository's. If an adopter's legitimate tree exceeds them the
  surfaced bound tells them which, which is why the criterion requires naming it.

## Changelog

- 2026-09-16 — Initial plan. Separated from `design-output-addressing` on the
  owner's instruction after two review rounds established that the read path is the
  only new trust boundary in that work and was carrying nine criteria and all of
  the security findings inside a spec otherwise made of mechanical declarations.
