# Spec: architect-review-knowledge-surfaces

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A solution architect using `architect-review` to critique a design today gets
a review shaped only by the reviewer's *recall* — the rubric checks whether the
artifact is well-formed (testable goals, real alternatives, labelled trust
boundaries), but it never asks whether the design's *factual* claims are true.
A design doc can assert "the billing service already publishes to the event
bus", "TLS 1.3 is mandated", or "no team is touching this surface" — and the
review will sail past all three even when the environment exposes a knowledge
surface that could have grounded or refuted them. This is the review-side
counterpart of what `architect-design` gained in PR #297 (the architect pack's
`0.3.0`): design now *consults* the enterprise's own knowledge to build a
grounded design; review should *check that a design was grounded*. The two
close a loop — design consults surfaces, review verifies they were consulted.

The lens is deliberately different from design's. `architect-review` does **not
redesign and does not consult surfaces to author a better answer**. Its job is
to **flag, in its critique**, any landscape / standards / in-flight / interface
claim the design asserts as fact without grounding (no cited surface *and* no
"unverified — confirm" marker), and to flag when an available knowledge surface
was ignored. If an internal retrieval surface is reachable this session, the
review *may* spot-check the load-bearing claims against it — to confirm or
refute them, never to supply a better design; if none is reachable, it flags the
unverified claims for the author to confirm rather than guessing. The mechanism must be **distribution-agnostic** (the skill ships to
many IDEs/CLIs and cannot know an adopter's knowledge topology) and **zero-cost
when unused** — the verification checklist loads only when the artifact under
review actually asserts grounding-relevant claims.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Frame the reference as a **verification checklist** ("is this area's claim
  grounded?"), not a consult guide — the lens difference from `architect-design`
  is the whole point of this spec.
- Reuse the **same 8-area MECE taxonomy and the modality×space axis** as the
  shared canonical core (`architect-design`'s `knowledge-surfaces.md` anticipates
  this: "only the consult triggers and this lens paragraph change"), duplicating
  the file per the pack's per-skill convention.
- Detect knowledge surfaces **harness-agnostically** — from the tools/CLIs the
  session actually exposes — and name no concrete tool or CLI in the skill or
  reference.
- **Degrade honestly** when no surface is reachable: flag the unverified
  load-bearing claims for the author to confirm rather than guessing, and never
  fabricate a "ground truth" to judge a claim against.
- Keep the `architect-review/SKILL.md` addition frugal (a single conditional
  step); put the substance in the progressive-disclosure reference.
- Bump the architect pack version, add a changelog entry, and run
  `make build-self` so `marketplace.json` reflects the bump.

### Ask first

- Extending the awareness to `architect-diagram` (deferred:
  architect-review-diagram-knowledge-surfaces — this PR ships the
  `architect-review` half only).
- Introducing any declared registry, shared-config file, or `~/.agentbundle`
  lookup for knowledge surfaces.
- Any edit to `docs/CONVENTIONS.md` or `docs/CHARTER.md` (would require an RFC).

### Never do

- Ship an enterprise knowledge server, RAG index, or any retrieval *engine* —
  out of charter. We ship review *awareness*, not a backend.
- Read shared user-global state (`~/.agentbundle/…`) from the skill — it breaks
  skill isolation.
- Create a cross-pack or cross-skill shared artifact, or make `architect`
  depend on another pack. The reference is duplicated inside the
  `architect-review` skill (the rejected Route B from #297 stays rejected).
- Add a new dependency, a new module boundary, or a new top-level directory.
- Edit `architect-design/SKILL.md` or `architect-diagram/SKILL.md` in this PR
  (the T2 `git diff` check enforces byte-for-byte non-change; the
  `architect-diagram` extension is deferred above).
- Have the review **redesign** the artifact or **consult surfaces to author a
  better answer** — that is `architect-design`'s lens, not review's.
- Edit projected paths directly (this repo is self-hosting; edit `packs/…`
  source, then `make build-self`).

## Testing Strategy

- **Reference + SKILL.md content** — *goal-based check*. The artifacts are
  prose; correctness is verified by the lint/build gates (`lint-skill-spec`,
  `lint-packs`, `lint-agent-artifacts`, `validate`, `build`, the marketplace
  `pytest` suites) plus a `grep` proving no concrete tool/CLI name was
  hardcoded and that the canonical 8-area core was preserved. A unit test would
  only assert what the linter already proves.
- **Sibling-skill non-change** — *goal-based check*. `git diff origin/main...`
  shows `architect-design/SKILL.md` and `architect-diagram/SKILL.md` byte-for-
  byte unchanged.
- **Marketplace drift** — *goal-based check*. `make build-self` runs clean and
  `marketplace.json` shows architect at `0.4.0`; `git status` shows no stray
  artifacts (`__pycache__`).
- **Verification behaviour** — *manual QA*, two halves, both recorded in the
  plan (T5). (1) A **real structural check**: `make build` projects the change
  and the projected `architect-review/SKILL.md` + reference are byte-identical
  to source — what an adopter install delivers. (2) A **decision-logic
  walkthrough**: an independent agent runs the new step against a fixed driver —
  a design doc carrying **one grounded claim and one ungrounded assertion** —
  and the review must flag the ungrounded claim and **not** the grounded one,
  naming which surface it checked against (or "none"). **Harness limitation,
  stated honestly:** this session can't inject a *live* mock MCP knowledge tool,
  so per-scenario tool presence is *described* (a simulation of the branch
  logic), not a live MCP detection — the same deferred enhancement already
  tracked as `live-mock-mcp-detection-qa` in `docs/backlog.md`.

## Acceptance Criteria

- [x] A new reference
  `packs/architect/.apm/skills/architect-review/references/knowledge-surfaces.md`
  exists and carries the **same 8-area MECE taxonomy** as
  `architect-design`'s canonical core — (1) business domain & meaning, (2)
  current landscape, (3) interfaces & contracts, (4) operational reality, (5)
  constraints & standards, (6) patterns & references, (7) decisions &
  rationale, (8) in-flight & roadmap — with the table's `#`, `Area`, and `The
  question it answers` **columns byte-for-byte verbatim** (only the trigger
  column changes) and the modality×space MECE axis + the 2/3/4 adjacency seam
  preserved (the canonical core that does not change across lenses).
- [x] The reference is framed as a **verification lens**, not a consult guide:
  the per-area trigger column reads as *"flag when the artifact asserts this
  area's claim as fact without grounding"* rather than *"consult it when…"*,
  and an opening lens paragraph states the review **checks grounding and does
  not redesign or consult-to-author** (contrasting it explicitly with
  `architect-design`). **All other consult-framed prose is recast too** — the
  table-intro directive ("Consult the ones your current design decision turns
  on…") and the Detection/degrade sections — so the verbatim canonical core is
  scoped to exactly the area rows + the three columns named in the prior
  criterion + the modality×space subsection + the 2/3/4 adjacency seam, and the
  recast is **not** limited to the trigger column and lens paragraph alone.
- [x] The reference defines **"grounded"** precisely: a claim is grounded when
  it cites a knowledge surface **or** carries an explicit "unverified — confirm"
  marker; a claim asserted as bare fact with neither is the flaggable failure.
- [x] **Harness-agnostic detection** (grep- + read-verified): the reference
  describes discovering retrieval surfaces from the session's available
  tools/CLIs (tool search where the harness defers tools; the loaded tool list
  otherwise), contains **no hardcoded tool/CLI names**, and **excludes public
  web search** as an internal surface. Crucially, the recast Detection section
  states that surface discovery serves **only the optional spot-check path** —
  the review **flags ungrounded claims whether or not a surface is reachable**,
  so detection is never the primary action (the design-lens "consult to author"
  framing must not survive the recast).
- [x] **Three honesty rails, recast for review** (read-verified): (a)
  **name-what-you-checked-against** — the review states which surface it
  verified claims against, or "none"; (b) **never fabricate a "ground truth"**
  — the review must not invent a contradicting fact to declare a claim wrong;
  when it can't verify, it flags for author confirmation rather than asserting
  falsity; (c) **one source is weak corroboration** — confirming a claim against
  a single unconfirmed surface carries residual uncertainty and is noted, not
  treated as proof.
- [x] The reference states the **two flaggable conditions** (both read-verified
  in T1, since the severity *gradation* and condition (b) are doctrine prose the
  fixed T5 driver does not exercise — see the harness note below): (a) a
  load-bearing landscape/standards/in-flight/interface claim asserted as fact
  without grounding, and (b) an **available knowledge surface the design
  ignored**; and it gives **severity guidance** that maps into the existing
  `architect-review` severity glossary (an ungrounded claim the verdict turns
  on → major or, if acting on it as fact would be unsafe/misleading → blocker;
  an ungrounded claim the design doesn't lean on → minor).
- [x] `architect-review/SKILL.md` gains a single **conditional** procedure step
  that loads the reference **only when** the artifact under review asserts
  grounding-relevant (landscape/standards/in-flight/interface) factual claims
  (progressive disclosure), and is skipped otherwise; the step names no concrete
  tool and is **orthogonal to artifact type and to the well-architected lens
  mode** (so it applies across design-doc / diagram / RFC / ADR / generic /
  WA-lens reviews, not just one rubric).
- [x] The SKILL.md step reuses the skill's existing review vocabulary
  (severity-tagged findings, verdict) rather than inventing a parallel
  mechanism, and instructs the review to **flag, not redesign**.
- [x] No registry, no shared-config file, no `~/.agentbundle` read, no new
  dependency, and no cross-pack/cross-skill shared artifact are introduced
  (verified by diff inspection). The reference lives wholly inside the
  `architect-review` skill.
- [x] `architect-design/SKILL.md` and `architect-diagram/SKILL.md` are
  **byte-for-byte unchanged** (verified by `git diff origin/main...`).
- [x] The architect pack's `[pack]` version specifically (not the
  `[contract] version`, which stays `0.10`) is bumped `0.3.0 → 0.4.0` in both
  `packs/architect/pack.toml` and `packs/architect/.claude-plugin/plugin.json`.
- [x] `docs/product/changelog.md` `[Unreleased]` has an entry describing the
  new review-side awareness behaviour.
- [x] `make build-self` has been run; `marketplace.json` reflects architect
  `0.4.0`; `git status` shows no stray/untracked artifacts.
- [x] All gates green: `lint-skill-spec`, `lint-packs`, `lint-agent-artifacts`,
  `validate`, `build`, and the marketplace `pytest` suites
  (`test_self_host_check.py`, `test_pipeline.py`).
- [x] Verification QA recorded against a **fixed driver** in two halves: (1)
  **structural (real)** — projected `architect-review/SKILL.md` + reference
  byte-identical to source; (2) **decision-logic walkthrough** by an independent
  agent — given a design doc with one grounded and one ungrounded claim, the
  review flags the ungrounded claim (with severity + a name-what-I-checked line)
  and does **not** flag the grounded one. Live mock-MCP detection is *simulated*
  (harness limitation), already logged as `live-mock-mcp-detection-qa`; the
  **ignored-available-surface** condition (b) and the major/blocker/minor
  severity *gradation* are also simulated-only for the same reason (no live
  surface injectable; single-claim driver) and fold into that deferral —
  read-verified in T1 instead.
- [x] `docs/backlog.md`'s `architect-review-diagram-knowledge-surfaces` item is
  updated to record that the `architect-review` half shipped and only
  `architect-diagram` remains.

## Assumptions

- Technical: architect is currently `0.3.0`; bump target is `0.4.0`, with
  `[contract] version` left at `0.10` (source: `packs/architect/pack.toml`).
- Technical: architect is a user-scope-default pack, not projected into this
  repo's `.claude/` tree; a version bump drifts top-level `marketplace.json`
  (the aggregation at `_aggregate_marketplace` ignores the self-host filter,
  which is why marketplace.json drifts despite the pack being user-scope), and
  `make build-self` refreshes it (source: `packs/architect/pack.toml`
  `default-scope=user`; `SELF_HOST_PACKS` at `self_host.py:95`;
  `_aggregate_marketplace` at `self_host.py:494`; prior learning).
- Technical: the SKILL.md hard lint cap is 1000 body lines;
  `architect-review/SKILL.md` is 99 lines pre-change, so a frugal few-line step
  stays far under the cap; "~100" is authoring discipline, not a gate (source:
  `tools/lint-skill-spec.py:490`; `wc -l`).
- Technical: the architect pack duplicates references per-skill by convention
  ("intentionally duplicated"; no cross-skill sharing), so duplicating
  `knowledge-surfaces.md` into `architect-review` matches the established
  pattern (source: `packs/architect/.apm/skills/*/references/*.md` grep).
- Technical: `architect-design`'s `knowledge-surfaces.md` already names the
  8-area taxonomy + modality×space axis as the shared canonical core reused
  under other lenses (source:
  `packs/architect/.apm/skills/architect-design/references/knowledge-surfaces.md:13-16`).
- Process: no RFC — the doctrine lives in the skill reference, mirroring #297,
  not in CONVENTIONS/CHARTER (source: user confirmation 2026-06-13).
- Process: changelog `[Unreleased]` is the home for user-visible skill changes
  (source: `docs/product/changelog.md`).
- Product: the lens is **verification/check** (flag ungrounded claims + ignored
  surfaces; spot-check only if a surface is reachable; never redesign), and
  `architect-diagram` is deferred to a separate PR (source: user confirmation
  2026-06-13).
