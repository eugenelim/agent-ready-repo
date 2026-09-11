# S7 handoff — make the four-discipline walk walkable

Written at the close of S6 for whoever picks up S7. It is a session prompt, not
a spec: it carries the facts, constraints and traps that S6 paid for, so the
next session does not re-derive them. The governing artifacts are the brief's S7
row and, when it exists, S7's own spec.

---

Continue the SDLC guide uplift. Start from `main` — the `eugenelim/team-sop`
branch landed there on 2026-09-11.

MAKE THE FOUR-DISCIPLINE WALK ACTUALLY WALKABLE.

The ask behind this: a new team — including a Claude Desktop user with no
terminal — should be able to take a product idea through desk research, product
strategy, experience design and product engineering as one sequence, and
actually execute it, not just find it. Every pack in that walk must be operable
by someone who has never used the catalogue.

This is slice **S7** of `docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md`.

## Ownership is already settled — do not re-derive it

The previous session spent four review rounds discovering this. The answer:

- **S7 belongs to the sdlc-guide-uplift brief.** Its intent's own outcome is a
  team that "can go from install to a shipped, governed change by following the
  guides alone: every skill they must invoke shows what to type, what to supply,
  what comes back, and what they hold at the end." That *is* this work. Do not
  author a new intent.
- `cohort-orientation-surfaces` puts journey pages explicitly out of its
  Boundary, but **owns `guides/README.md`'s navigation model** — adding content
  within the hub is fine, restructuring its navigation is not.
- `digital-product-guides-update` is RFC-0071 M6: its chain carries
  frontend-engineering rather than desk-research, and it is gated behind
  unstarted M5. It does not own this.
- `digital-product-maker-profile` names the same four disciplines but its unit
  is a `profiles/*.toml`, which by its own record "is read only by the
  `agentbundle` CLI and never reaches the plugin route". Not this reader.

## What S6 shipped, and what it deliberately did not

S6 (`docs/specs/four-discipline-sequence/`) is **Shipped and is discoverability
only**. Its Objective was narrowed on delivery to drop "and can walk it",
because no criterion in it ever tested walkability. It delivered:

- the journeys index as three collection-derived groups, with the four in an
  ordered `<ol>`, membership derived so nothing can silently drop;
- `guides/README.md` **P2b** — an alternative beside `P2`, not a trailing seventh path;
- the two chooser rows that ordered these four strategy-first, reconciled.

Read its `notes/verification-ledger.md` before starting. It records three
mutation proofs, a cold read, and two build facts you will otherwise re-derive.

## The gaps S7 must close — measured, not asserted

1. **No literal request anywhere in the path.** The brief's own success metric
   requires each step to state "its prerequisite, a literal request, its result,
   and the next link". `P2b` has everything except the literal request. A reader
   still does not know what to type.
2. **Entry is partly closed, and the remainder is the harder half.** `P2` now
   points to `P2b` at the moment a reader chooses a shaping route, and the
   journeys index routes onward into it. **Still open:** the docs home does not
   link the path, `web/src/pages/index.astro` contains **zero** references to
   `/journeys/`, and `journeys` is absent from `[shared_chrome].header` in
   `site.toml` — it appears only in the footer's `product` group. The brief
   names this failure mode: "Content presence therefore overstates
   discoverability."
3. **No worked handoff.** A cold read of the shipped surfaces found the handoffs
   name the artifact and the receiving discipline but "neither explicitly says
   how each artifact is passed into the next discipline." No example carries a
   real artifact across a handoff.
4. **No route for the Claude Desktop reader.** `docs/specs/claude-apps-route-docs/spec.md`
   is Draft, registered, unimplemented — 22 criteria, 6 tasks. It is the
   dependency for the no-terminal half of this ask.
5. **Pack operability is uneven, and step 3 is the weak one.** Guides vs skills
   in the walk: `desk-research` 8 guides / 12 skills (2 how-to, 2 tutorial);
   `product-strategy` 7 / 9 (3 how-to, 1 tutorial); **`experience-design` 5
   guides / 20 skills, 2 how-to and zero tutorials**; `product-engineering`
   19 / 15 (13 how-to, 1 tutorial). Corpus-wide the audit reports chat input
   44%, demonstrated input 5%, sample output 32%, stated outcome 31%; 21 guides
   name a skill in prose without ever showing the input, and only 2 of 208 carry
   all five affordances. Re-run `python3 tools/audit-guide-affordances.py`
   yourself — those numbers move, and `--ledger` traces every hit to its line.

## Boundary against the sibling slices

S3, S4 and S5 are Draft and open on the same corpus. **Do not absorb them.**
S3 closes chat-input and outcome gaps against its own accepted-base ledger, S4
tutorial worked examples, S5 how-to sample outputs. S7's claim is narrower and
different: the four packs *on the walk* are operable end to end as a sequence.
Where S7 needs an affordance inside a guide that S3–S5 already own, either take
it from that slice explicitly and say so in both, or link rather than duplicate.
Decide this before authoring, not during review.

## Constraints that bit repeatedly — inherit them, do not rediscover

- **Claude plugins carry agents, Agent Plugins 1.0.0 do not.** Of the four,
  `product-engineering` ships 3 agents, `desk-research` 2, `experience-design` 1,
  `product-strategy` 0. All four install as Claude plugins; three of four are
  refused on the Agent Plugins route. Never describe the two routes as
  equivalent.
- **`web/src/content/journeys/*.md` are generated** (`generated: true`) from
  `packs/*/JOURNEY.md`. Editing them by hand is a four-pack released change.
- **A guide cannot carry an image** that renders on both GitHub and the docs
  site; the projector rewrites Markdown image paths into page URLs and copies no
  assets. If S7 wants a diagram of the walk, that defect
  (`docs-site-build-contract-hardening/notes/guide-image-projection.md`) is on
  your critical path and is currently parked.
- **No first-value or install-success claim** until the probe runs. The probe is
  prepared but unrun at
  `docs/specs/claude-apps-route-docs/notes/install-to-first-value-probe.md`; it
  needs a human on a real Claude app. `product-strategy` is the recommended
  probe pack because it is the only one of the four with zero agents.
- **`make bootstrap-sites` installs npm deps only.** `make site-build` writes
  `build/` then `build/docs/`. Four web vitest cases fail until you run the
  latter; that is not a defect.
- **Pack degradation fallbacks key on the agent being ABSENT**, so none fires on
  the Claude apps chat surface where it is present-but-unrunnable, and a Shipped
  named-skip guarantee passes silently there
  (`claude-plugin-route-scope/notes/subagent-present-but-unrunnable.md`, parked).

## Protocol

Follow the a6 authoring and review-response contract at
`docs/specs/acceptance-criteria-set-construction/spec.md` **in the `a6`
worktree** — it is in flight there, not in this one. Read it rather than the
new-spec skill guidance.

- Build the acceptance-set construction record as you go: candidates,
  dispositions, one red input and exactly one observer per criterion, coverage
  read both ways. Do not reconstruct it afterwards.
- Name which of the eight responses you are using before any repair. They are:
  repair; narrow the claim to what its check reaches; cut the item; dismiss with
  the reason recorded; repair the generator not the instance; route to an owner
  that already covers it; bound out of scope with a follow-on naming its new
  owner; accept as proportionate with the reason recorded. In the S6 rounds,
  six of round 4's seven findings originated in prior repairs — reflexive repair
  is the failure mode this protocol exists to prevent.
- Run a mechanical set-level sweep as a script before each review round:
  numbering, declared counts vs actual rows, one AC id per admitted row,
  red-input uniqueness, criterion→task coverage, coverage-back tracing, dangling
  references. It catches the stale-companion class that dominated S6's round 4.
- **Review rounds run on Codex, not Claude subagents.** gpt-5.6-sol for
  decision-sensitive review. Rescoping restarts the rounds.
- Every criterion must be able to fail. S6 shipped one that could not
  (`make site-link-check` proves link resolution, never link existence) and it
  took a round to catch. Require a mutation proof for every guard, and prefer a
  count-preserving mutation where a count is involved.

## Verification

```bash
make site-build                      # writes build/ then build/docs/
npm run test --prefix web            # vitest; needs the build above
python3 tools/validate_guides.py
python3 tools/lint-guide-titles.py
python3 tools/check-guide-index.py
make site-link-check
python3 tools/audit-guide-affordances.py --ledger <path>
.agents/skills/author-delivery-brief/scripts/lint-brief-coverage.py
```

Remote CI, after pushing — all four are partial evidence, never a required gate:

```bash
git push -u origin HEAD && B="$(git branch --show-current)"
gh workflow run build-check.yml --ref "$B"
gh workflow run test-corpus.yml  --ref "$B"
gh workflow run test-roster.yml  --ref "$B"
gh workflow run pages.yml        --ref "$B"
```

Do not hand-write a spec's status into the brief's Spec map — set the cell to
`<auto>` and let `lint-brief-coverage` derive it. The five older S1–S5 rows are
pre-existing debt owned by the brief.

## Open, and not S7's to close unless you choose to take them

- The install-to-first-value probe is unrun; every claim it would settle is
  unverified.
- Both parked defects above have a recorded disposition and no owner.
- Whether the adoption blocker is explanatory or commercial is open in
  `docs/design/discovery/team-orientation-decision-log.md`; the top-ranked
  measured blocker was 47% organisational. Size S7 accordingly rather than
  defending it as an adoption fix.

---

# Harvested from the S6 session — read this before planning S7

## The finding that reframes the slice

**The owner could not tell what experience-design skills to run, in what order,
to build the team SOP — and the SOP being built is itself a four-discipline
sequence.** The pack that should teach sequencing could not teach its own use
for this task. That is not a side observation; it is the strongest available
evidence for why S7 exists, and S7 should treat it as the primary defect.

The order **is** documented, in two places:
`packs/experience-design/DESIGN.md` § 1 "The full sequence" and § 5 "The craft
sequence", plus `guides/experience-design/explanation/the-experience-thread.md`
adopter-facing. It was still not findable in practice. Diagnose *why* before
adding more prose: the answer is probably that nothing routes a reader to it at
the moment they need it, which is the same defect as the path being unreachable from the surfaces a reader starts on.

## The craft sequence, as the pack itself declares it

```
journey-mapping → content-design → copy-direction → user-flow
  → design-principles + creative-direction
  → information-architecture (or a genre-direct skill) + design-system
  → interaction-design → design-review → experience-reviewer
```

`service-blueprint` and `process-mapping` run parallel, not as gates. The
minimal viable thread is `journey-mapping` → `user-flow` → one craft pass
(`information-architecture` → `interaction-design`) → `experience-reviewer`.

**Genre-direct skills replace the `information-architecture` step only** — the
rest of the sequence still runs. For the surfaces in play: the marketing home
and the journeys index are `conversion-design`; the guides hub and docs are
`documentation-design`. A listing surface like the journeys index may instead
route to `marketplace-design` (listing-card IA, filter/facet architecture);
decide that explicitly rather than defaulting.

The pack's stated reason the order exists: "Skipping a step doesn't save time —
it pushes the missing input forward as an implicit assumption, where it gets
designed around rather than decided." S6 skipped all of it and produced exactly
that.

## S6's design failure, so S7 does not repeat it

S6 shipped a component with no information architecture. Measured after the
fact:

- **`journeys` is in the site footer only** (`shared-chrome.generated.json`
  `footer[0].destinations[4]`). The header nav groups are `how-it-works`,
  `use-cases`, `catalogue`, `now`, `docs`, `try-the-build-loop` — **no
  Journeys**. `web/src/pages/index.astro` contains **zero** references to
  journeys.
- The marketing home *does* link to three individual journeys — `core`,
  `product-engineering`, `release-engineering` — via `ThreeLoops`. Those are the
  supervised loops. The four disciplines appear nowhere on the home, so the one
  journey-shaped thing the home surfaces reinforces the older framing.
- In `guides/README.md` the path shipped **seventh**, below the P6 branch
  section and the whole walkthrough, under a heading reading "Another route",
  with nothing linking to it. **Corrected since**: it is `P2b`, directly after
  `P2`, which points to it. The lesson stands even though the instance is
  fixed — the placement was decided by where there was room, not by design.

**None of S6's 22 criteria tested placement, entry, or findability.** They
tested grouping, order, markup semantics, link targets and prohibitions. The
placement criteria added afterwards are now S7's inherited half. S7 must still
carry at least one criterion that fails when the sequence is unreachable **from
the marketing home**, which is where a first-time reader actually starts and
where nothing points at it yet.

## Gate-approved design artifacts already exist and were ignored

This is the specific process failure, and it is worse than not knowing the
sequence. Both edited surfaces already had content briefs from the earlier
experience-design thread:

- `docs/design/content/marketing-home.md` — carries an 11-zone IA for the home.
- `docs/design/content/docs-guides-index.md` — carries the guides index IA. It
  specifies **"The six ordered paths … | must-say | Immediately below"**, and
  records that `information-architecture` "has already fixed the navigation
  model and the job grouping".
- `docs/design/journeys/team-orientation-future-state.md` — the standing,
  gate-approved prime journey. `web/AGENTS.md` says to anchor on it before
  changing what the marketing surface says, and to reconcile contradictions
  there rather than only in a content brief.

S6 added a **seventh** path at the **bottom** without amending a brief that
specifies six, positioned immediately below the opening. That was corrected on
2026-09-11 — the brief carries two amendments and the path is now `P2b` — but
the failure mode is what matters here. **S7 must not author
new design artifacts before reading these three and deciding, explicitly,
whether the four-discipline sequence is a seventh path, a reframing of the six,
or a different surface entirely.** Changing a stage's actions or residual pains
requires re-gating through `approve-journey`; `docs/design/README.md` carries
gate state.

## Ownership crosses intents here

`cohort-orientation-surfaces` has **In** scope "the marketing home page's
structure and copy" and "the documentation guides index and its navigation
model". Any placement or navigation fix crosses it. Settle that before editing,
not in review — S6 lost four review rounds to exactly this class of question.

## A real gap with no owner: guided next-step suggestions

The owner's framing: "our skills need guided suggestions on what to run next, in
what order, hand-hold the journey throughout with breadcrumbs". **No intent or
backlog item owns this.** Searched `docs/product/intents/`,
`docs/product/briefs/` and `workspace.toml`. The nearest neighbours, none of
which covers it:

| Artifact | Status | Why it does not cover this |
| --- | --- | --- |
| `docs/product/briefs/work-loop-next-action.md` | Draft | Scoped to the work-loop state machine, and explicitly "reporting only" — one authoritative next action from persisted loop state. Not cross-pack, not the craft sequence |
| `docs/product/briefs/stage-input-readiness.md` | Draft | Consumer-side readiness — asks whether the next stage *can* work from its input. Adjacent and useful, but it does not tell a reader which skill to run next |
| `docs/specs/workspace-status-next-actions/spec.md` | Shipped | Workspace queue next-actions only |

**This needs its own intent**, and it spans both sides the owner named: the
skills side (a skill ending by naming what comes next, with the sequence
position visible) and the guides side (breadcrumbs and next-step links through
the walk). Decide whether it is one intent with two slices or two intents before
folding any of it into S7 — S7's own scope is the four-discipline walk, and
absorbing a catalogue-wide affordance would repeat S6's boundary mistake in the
other direction.

## Pack operability, measured

`desk-research` 8 guides / 12 skills · `product-strategy` 7 / 9 ·
**`experience-design` 5 guides / 20 skills, 2 how-to, zero tutorials** ·
`product-engineering` 19 / 15. The walk's design step is its weakest, and it is
the step whose absence the owner personally hit.

## Card IA is part of S7, added 2026-09-11

The design review found the journey cards' own content contradicts the sequence
the page asserts. `product-engineering`'s tagline reads "Raw idea → build-ready
decision brief" while the group copy says it receives a designed bet and ends at
an approved merged change — so the last discipline appears to restart the
sequence and stop before implementation.

S6 could not fix it: taglines are generated from `packs/*/JOURNEY.md`, and its
AC-0018 forbids touching generated journey content. Fixing it is a **released
pack change**.

It lands in S7 because it shares a source with the walk's handoff semantics —
the same `JOURNEY.md` files carry the stage order, the `youProvide`/`youReceive`
contract, and the taglines. Settle them together or they will drift apart.

**What card IA has to answer:** what one card must carry when twenty of them sit
on a page; whether a tagline written to describe a pack standalone can also be
true of that pack's position in a sequence; and whether the four sequence cards
need a different content contract from the other sixteen. The content brief at
`docs/design/content/journeys-index.md` routes this to `marketplace-design` and
records what that genre does **not** license here — no faceting, no transaction
bridge.

---

# Added 2026-09-11, after S6 landed on main

## S7 absorbed the S8 design-contract slice

S7 now owns two halves of different kinds, and conflating them is the first way
this goes wrong.

**Half one — already true in code, must not regress.** The design contract for
the journeys index and the guides hub: distinct group signatures, the onward
route from the sequence into the guides path, the alternative path's placement
beside `P2` and its selection axis, and the walkthrough cases' definition of a
stage. It is implemented and tested. It is governed by **no live spec**, because
S6 froze on shipping. S7 carries it as inherited criteria with existing tests,
not as new build.

**Half two — unbuilt.** Everything else in this prompt: literal requests per
step, worked handoffs, the Claude Desktop route, pack operability, card IA.

Write the spec so a reader can tell which is which. A criterion that is already
green is not evidence of nothing — it is a regression guard — but presenting it
as delivered work would overstate the slice.

## Do not reopen a frozen spec. This cost a full review round.

`docs/CONVENTIONS.md` § Documentation classes: shipped `specs/*` are "Immutable
history. Status fields can change, bodies cannot." § Lifecycle: after a feature
ships "the *code is the truth*, and the spec becomes the record of what was
agreed."

Two shipped specs were mutated during S6 — `four-discipline-sequence` was
reopened to `Implementing` with four criteria added, and
`install-to-ship-walkthrough`'s AC2 was amended in place. An independent review
sustained both as **blocking**, and both bodies were restored.

The trap is subtle and worth stating, because the owner's framing and the
convention sound opposed and are not: **a shipped contract is a historical
snapshot, not future-binding — which is exactly why you do not rewrite it.** When
a shipped criterion blocks a change that is right, the answer is a new slice. Not
contorting the content to satisfy the old criterion, and not editing the frozen
record. Both wrong moves were made in sequence before the right one.

## Re-derive the inherited tests. Do not trust their names.

`web/src/test/FourDisciplineSequence.test.ts` currently passes. **Three of its
assertions were written, believed correct, and then shown by mutation to be
unable to fail:**

- the group-signature check passed when two groups' modifiers were **swapped**,
  because it only verified each card carried exactly one modifier from the set —
  which a swap preserves;
- the same check passed when all three card treatments were made **identical**;
- it also passed when a modifier's base CSS rule was **deleted**, because the
  surviving `:hover` rule satisfied an any-rule match — leaving a card that looks
  identical at rest;
- the onward-route check asserted **substrings** (`/docs/guides/` and `#p2b`),
  which a different path sharing those fragments satisfies.

All four are tightened now. Treat that as the base rate, not as a run of bad
luck: for every guard S7 adds, write the mutation first and confirm it kills the
test. A count-preserving mutation is the useful shape where a count is involved
— omitting one item while duplicating another left a length comparison green.

## The design work that has been done, and what it left

`content-design` ran for both surfaces. Read these before touching either:

- `docs/design/content/journeys-index.md` — **authored 2026-09-11**, because that
  surface was never in the team-orientation design packet's scope at all. It sets
  Understanding before Decision, `technical-editorial` mode, an inverted-pyramid
  listing rather than any acquisition arc, and routes the IA step to
  `marketplace-design` while recording what that genre does **not** license here.
- `docs/design/content/docs-guides-index.md` — two amendments: the path's
  placement, and a heading pass that met its must-say #1 after it had been
  specified and absent since 2026-09-04.

An independent design review ran against the **rendered** surfaces and returned
SHIP WITH CHANGES — 1 blocking, 8 major, 3 minor. Its dispositions are in
`docs/specs/four-discipline-sequence/notes/design-review-2026-09-11.md`. Most
findings are pre-existing and routed to `cohort-orientation-surfaces`; do not
absorb them. **What remains genuinely open and is not S7's:** the guides hub's
prominent search and its route back to the internal-case material, the marketing
home's journeys entry (decided in its brief, not implemented, because the header
is the navigation model and `site.toml` drives both sites' chrome), and the
blocking "two equal doors" finding, which belongs to
`claude-apps-first-value-entry`.

## The literal requests you need already exist

`JOURNEY.md` stage bodies carry them — "Type `desk-research` and describe what
you want to find out" — plus fenced sample-output blocks. 18 stages carry a
literal input and 27 carry a sample block across the 14 packs. **That makes S7's
missing "literal request per step" a projection, not authoring**, for the packs
that have one. Confirm the count yourself before relying on it; three separate
predicates over one corpus gave three different answers earlier in this work.

## Verification

Run the roster suite. `tests/roster/` is not collected by `tools/`-scoped runs,
and it caught a lifecycle defect that four local gate runs and a full `web/`
suite all missed:

```bash
python3 -m pytest tests/roster/ -q
```

Two lifecycle rules it enforces, both learned the hard way: a spec's
`workspace.toml` list membership must match its status — a `Shipped` spec cannot
sit in an open queue, nor an `Implementing` one in `shipped` — and
`source.parent` on a spec entry must resolve to a **brief** path or be absent.
`chat-only` is valid in a document's own Source block but is **not** a valid
`workspace.toml` mode; `SOURCE_MODES` admits only `repo-origin` and
`tracker-origin`.

Never chain a gate with a commit or a push in one command. A red roster suite
scrolled past a `&&` chain and got pushed.
