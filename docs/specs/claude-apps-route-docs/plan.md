# Plan: the Claude-apps route is reachable and honest

- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)

## Constraints

Follows [ADR-0107](../../adr/0107-claude-plugin-route-serves-non-technical-adopters.md).
Design inputs: [the practitioner journey](../../design/journeys/claude-apps-practitioner-current-state.md),
[the docs surface spec](../../design/content/claude-apps-route-surface.md), and
the 2026-09-10 amendment in
[the marketing-home brief](../../design/content/marketing-home.md).

Two ownership areas in one spec, deliberately: the guide pages are worthless
without the route, and the route is misleading without the pages. Splitting them
ships a half-change either way.

**Re-parented 2026-09-10 — see the spec's Provenance.** This slice belongs to
`claude-apps-first-value-entry`, not `cohort-orientation-surfaces`. The doors
were ceded between intents after a review found them owned twice, and ownership
here resolves by outcome: these surfaces serve reaching a route, not
comprehending the operating model.

**Neither parent blocks it.** `cohort-orientation-surfaces`' delivery gate,
`review-experience-designs`, passed 2026-09-10. The current parent is blocked
only for the method-to-artifact tutorial and certified first-value claims,
which this spec does not make — AC12 is the fence that keeps it honest.

**The de-risk still points here.** `cohort-orientation-surfaces`' 2026-09-10
de-risk recommended shipping the reversible surfaces first as the probe, and
these are those surfaces. That recommendation survives the re-parenting: it was
about sequencing risk, not about ownership.

**What the de-risk withholds stays withheld here:** the gate-identifier removal
and the `guides-sidebar-generation` amendment are one-way and are not in this
spec's scope.

`web/` requires `npm ci` in a fresh worktree before the site builds.

## Design (LLD)

**Shape: mixed** — prose pages plus one Astro component change.

**Content placement** is settled by the surface spec, with one correction now
carried back into it: the page is a **how-to**, not a tutorial, chosen by reader
posture as this repository's conventions require. The reader arriving through
the door has a named task — get this catalogue into the app they already use.
That is how-to posture. Tutorial posture would be on-rails learning of a
discipline method ending in a recognisable artifact, and that is precisely the
work `claude-apps-first-value-entry` owns and cannot yet reach. The split is
therefore clean rather than a relabelling: the how-to carries the reader to a
submitted install with the evidence boundary stated, a tutorial teaches the
method to an artifact, and only the second needs the first-value contract. Both
pages join existing quadrants; no new quadrant is created.

**Stack.** Guides are Markdown with `title:` frontmatter under
`contracts/guide.schema.json`. The home page composes section components from
`web/src/components/marketing/`; the start zone is `InstallTerminal`, and the
second door is a sibling within that zone rather than a new top-level section —
`web/src/pages/index.astro`'s section list does not grow.

**The pinned-literal hazard.** `tools/lint-plugin-route-docs.py` matches literal
substrings. Any reflow of `install-routes.md` risks moving punctuation inside a
pinned string. T3 runs the linter and diffs the pinned strings before and
after, because a passing linter alone does not prove they were left alone.

## Decisions this build inherits

Settled this session, recorded here so the implementer does not re-derive them:

| Decision | Consequence for the build |
| --- | --- |
| The Claude apps take plugins on any paid plan, self-service, no administrator | The how-to's happy path needs no admin step; an administrator appears only in the restriction case |
| The two plugin stores are separate | Register-once-per-surface is a step-level warning at the registration step, not a footnote |
| Sub-agents and hooks are Cowork-only; skills work everywhere | `product-strategy` is the worked example because it ships no sub-agents, so nothing degrades silently while a reader is learning to trust the surface |
| Inline SVG is removed by GitHub's renderer; `<img>` and `<picture>` survive | Any future diagram is `<img>`; the capability reference is a table |
| Guides cannot carry a working image on both surfaces | AC19 forbids images in both new pages until the projection defect is fixed |
| An organisation marketplace needs a private repo synced from its default branch | The how-to names the personal path first; the organisation path is the admin fallback, not the default |

## Tasks

### T1 — Capability reference

**Depends on:** none
**Implements:** Objective outcome 3; AC4, AC5, AC19
**Mode:** goal-based check

**Tests:** `validate_guides.py` and `lint-guide-titles.py` cover frontmatter and
title-H1 identity for the new file; neither exists as a per-page assertion, so
the check is that both exit 0 with the file present. Row completeness is
verified by reading the rendered table against the four surfaces named in AC3 —
there is no fixture, and inventing one would pin the table to itself.

**Approach:** Add the reference page. Source every row from ADR-0107 and the
distribution survey; add no capability claim that neither carries. **A table,
not a diagram** — guides cannot carry a working image on both surfaces until
the projection defect is fixed, and a matrix is the better form for a lookup
anyway.

### T2 — Registration how-to

**Depends on:** T1
**Implements:** Objective outcome 2; AC1, AC2, AC3, AC17, AC18
**Mode:** goal-based check, then manual QA in T6

**Tests:** Same two gates as T1. AC2's placement is checked by reading the
registration step, not by grepping the file — the criterion is that the warning
sits *at* the step, and a file-level grep would pass with it anywhere.

**Approach:** Steps end at the reader having **submitted** the install action.
Success is explicitly unclaimed — the page says what to do and what to expect
to see, never that it will work. `product-strategy` is the named example because it
ships no sub-agents, so nothing in its listing degrades silently. Link to the T1
reference for surface differences and to `install-routes.md` for why routes
differ; restate neither.

### T3 — install-routes links

**Depends on:** T1, T2
**Implements:** AC10, AC14, AC15
**Mode:** goal-based check

**Tests:** `lint-plugin-route-docs.py` exits 0, and every literal the linter
pins for `install-routes.md` is compared against the accepted base with
`git diff <accepted-base> -- guides/_shared/explanation/install-routes.md`.
Omit the `..HEAD`: that form compares two commits and misses staged and
unstaged work, and a bare `git diff` goes empty once the task lands. The linter
proves the strings still exist; this comparison proves the edited file did not
alter them.

**Approach:** Two outbound links. No new prose; the page already carries the
mechanics and already discharges ADR-0107.

### T4 — Navigation pointers

**Depends on:** T2
**Implements:** AC9, AC11
**Mode:** goal-based check

**Tests:** `check-guide-index.py` exits 0 and `make site-link-check` audits
emitted internal links — an in-tree link can resolve while its generated form
does not, which is the failure this catches. That target builds `web/` before
`docs-site/`, which is load-bearing per `docs-site/AGENTS.md` § Build.

**Approach:** One link each in `guides/README.md` and the docs-site install
page.

### T5 — The second door on the home page

**Depends on:** T2
**Implements:** Objective outcome 1; AC6, AC7, AC8
**Mode:** visual / manual QA

**Tests:** Relative prominence has no selector, so captures at desktop and
375 px, light and dark, go in `notes/visual-qa.md`. Captures alone are not
sufficient: `web/AGENTS.md` requires the web e2e gate, which is what catches a
regressed focus order or broken keyboard behaviour in a radio-group component —
invisible in a screenshot. The existing gate asserts nothing about AC8's
destination, so this task adds that one assertion to the suite rather than
claiming the gate already covers it.

**Approach:** The start zone is `InstallTerminal.astro`, a CSS-only radio-group
with four tabs — not a two-CTA slot with a spare half. Adding an equal door is
an interaction and layout change to that component, and if it grows past one
reviewable PR it splits into structure then copy. Do not add a section to
`index.astro`'s list. Copy comes from the marketing-home brief's
amendment; wording that hedges the second door fails AC7, which owns visible
copy, while AC6 owns rendered equality and AC8 owns the destination.

### T6 — Cold-read QA and the honesty sweep

**Depends on:** T1, T2, T3, T4, T5
**Implements:** AC12, AC13, AC16
**Mode:** manual QA plus goal-based check

**Tests:** AC12 and AC13 are checked across the complete change, not per file —
a count or a success claim anywhere in it is a failure. Read
`git diff <accepted-base> --` for committed, staged and unstaged tracked
changes, **then** read every in-scope file from
`git ls-files --others --exclude-standard`. Neither `..HEAD` nor a bare
`git diff` covers that whole state, and the two new guide pages start untracked
— exactly the files most likely to carry an unsupported success claim.
Mechanical searches find candidates; whether a sentence *implies* install
success is a judgement, so it takes an independent reviewer's verdict rather
than the author's.

**Approach:** Recruit one reader who has not seen these surfaces. Give them the
home page only. Record the date, which door they identify as theirs, the next
action they name, the surface they expect their method to run on, and every
hesitation point, with its duration. Being unable to state any of the three, or
needing to ask, fails AC16. Durations are recorded as evidence for the next
slice; AC16 sets no hesitation-duration failure threshold, and the plan does not
invent one. The reader is not
asked to install anything — this spec promises no install outcome, so testing
one would test a claim it does not make.

## Verification

Run all four guide gates separately; a batched invocation hides which one
failed:

```bash
python3 tools/lint-plugin-route-docs.py
python3 tools/validate_guides.py
python3 tools/check-guide-index.py
python3 tools/lint-guide-titles.py
python3 -m pytest tests/roster/test_core_onboarding_documentation.py -q
make site-link-check
```

The web e2e gate runs per `web/AGENTS.md`; it is required by T5 and is not
optional because the start zone is an interactive component.

`make site-link-check` builds `web/` then `docs-site/` and audits emitted links;
a fresh worktree needs `npm ci` in both first. T5's captures are only valid
after that build.

## Follow-ons

- **A Claude-apps first-value record.** Blocked on the
  `[pack.first-value].surfaces` vocabulary decision, owned by
  `portfolio-pack-first-value-contract`. Tracked as
  [`claude-apps-first-value-entry`](../../product/intents/claude-apps-first-value-entry.md).
  This spec's AC12 exists to keep the boundary intact until that lands.
- **The narrative-arc question.** The marketing-home amendment leaves open
  whether the arc moves from StoryBrand to Conversion-Centred Design now the
  reader is Solution- to Product-Aware. That rewrites section jobs beyond this
  spec's start zone and needs its own decision.
- **A dated Claude-apps install observation**, owned by
  `live-adapter-and-client-smoke-evidence`. Until it exists, every behavioural
  statement here stays documentation-verified.

## Changelog

- 2026-09-10 — Drafted. Scope set to one spec across guides and the marketing
  surface after the audience for the home page was corrected from adoption
  champion to first-time user, which made the two doors a single coherent
  change rather than two.
- 2026-09-10 — Rescoped after shaping review. The draft contracted a completed
  method on the Claude apps, which crosses the first-value contract's ownership
  and depends on third-party execution nobody has observed. Every promise of a
  successful install or a finished artifact is removed; the page becomes a
  how-to rather than a tutorial, because a tutorial's defining property is the
  guaranteed result this spec cannot offer. The first-value tutorial stays with
  `claude-apps-first-value-entry`, behind its probe and the surfaces decision.
