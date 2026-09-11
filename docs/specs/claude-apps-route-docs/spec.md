# Spec: the Claude-apps route is reachable and honest

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0107
- **Brief:** none — but see Provenance below; this is a slice of a registered intent
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Provenance

This spec is **one slice of**
[`claude-apps-first-value-entry`](../../product/intents/claude-apps-first-value-entry.md),
which owns reaching a route without a terminal: the marketing home's two start-zone
links, and that route's copy through a submitted install.

**Re-parented 2026-09-10.** It previously named `cohort-orientation-surfaces`,
on the reasoning that that intent owns the marketing home's structure. The doors
were then ceded — this repository resolves ownership by *outcome*, and these
surfaces serve reaching a route, not comprehending the operating model. The old
Provenance cited an addition that no longer exists in the intent it named. Found
by a coverage pass reading obligations back to owners, after six review rounds
reading criteria forward to tests had missed it.

**The parent is unblocked for exactly this scope.** That intent cannot reach a
spec for the method-to-artifact tutorial or any certified first-value claim
until `[pack.first-value].surfaces` can represent the Claude apps — but it
states explicitly that the entry links and the install how-to are *not* blocked
by that question, because they promise a route and a submitted install rather
than a completed method. This spec claims only the unblocked half, which is why
AC12 exists.

**One coordination point, not split ownership.** AC9 adds a link in
`guides/README.md`, whose navigation model belongs to
[`cohort-orientation-surfaces`](../../product/intents/cohort-orientation-surfaces.md).
One link into an existing hub does not restructure that model; if the hub's
navigation is reworked, this link travels with it.

Both trace to the prime journey,
[`team-orientation-future-state`](../../design/journeys/team-orientation-future-state.md),
whose Stage 2 amendment was ratified at the `approve-journey` re-gate on
2026-09-10. This slice discharges **only** that amendment's surface-plural
entry path and its next-action validation hook — not Stage 2's unchanged
"prove it on real work" outcome, which needs the first-value work this spec
deliberately stops short of.

## Objective

A first-time user who works in the Claude apps and has no terminal finds, from
the public home page, a documented route into this catalogue — and can tell,
before spending effort, which surface does what.

Three user-visible outcomes:

1. **The home page offers two ways to start, not one.** Its start zone carries a
   terminal route and a Claude-apps route as equal doors. Neither is labelled or
   positioned as a fallback.
2. **The Claude-apps door opens onto actionable registration steps.** A reader
   who follows it finds the registration path, which packs the marketplace
   carries, and where to go next — expressed as a task they perform, not as a
   promised result.
3. **Surface limitations are stated before they cost anything.** Where a
   capability differs by surface — sub-agents, hooks, where an artifact lands —
   a reader can look it up in one table, and the registration steps warn at the
   point where a mistake is actually made.

**This spec documents a route. It does not promise that an install succeeds or
that a method completes on the Claude apps.** That promise belongs to the
first-value contract, which cannot yet name this surface, and to a dated
observation that does not yet exist.

## Assumptions

- Technical: `tools/lint-plugin-route-docs.py` pins literal substrings across a
  declared set of sites and exits non-zero when a required literal is absent
  (probe: the gate exits 0 today, and failed mid-edit on a moved character).
- Technical: among `README.md`, the docs-site getting-started install page,
  `guides/_shared/explanation/pack-catalogue.md`, and
  `guides/core/how-to/adapt-to-project.md`, none mentions the Claude apps
  (bounded grep over those four files: 0 hits).
- Technical: no existing page under `guides/_shared/explanation/` appears in
  `guide-nav-baseline.toml`, so a new page needs `title:` frontmatter and no
  baseline entry (`grep -c` over that file).
- Technical: `guides/_shared/how-to/` and `guides/_shared/reference/` both
  already exist, so neither new page creates a quadrant (`ls` per quadrant).
- Technical: `[pack.first-value].surfaces` records *verified* first-value
  surfaces and is subset-bound to `allowed-adapters`
  (`portfolio-pack-first-value-contract/spec.md:226`). **This is not why this
  spec avoids a first-value claim.** Plugin reach is already derivable from
  `allowed-scopes` plus the route's user-scope admission, so the vocabulary was
  never the blocker; what is missing is a dated observation that a pack
  delivers first value in the Claude apps. AC12 fences the claim, not the
  field.
- Technical: `product-strategy` carries no sub-agents, while the other three
  discipline packs do (`find packs/*/.apm/agents`). This bounds what degrades
  in chat; it proves nothing about installability.
- Technical: `make site-link-check` builds `web/` then `docs-site/` and audits
  emitted internal links (`Makefile:694`).
- Process: ADR-0107 is Accepted and names `install-routes.md` in its
  Confirmation signal, which the working tree already satisfies.
- Product: the home page's reader is a first-time user whose goal is Execution;
  the adoption champion is served on the tech site (user confirmation
  2026-09-10).
- Product: a paid-plan user can add a marketplace under Customize › Plugins ›
  Personal plugins without an administrator (user confirmation 2026-09-10).
- Technical: **a guide cannot carry an image that works on both surfaces.**
  `guides/**` is browsed on GitHub and projected into Starlight, but
  `tools/build-site.py` copies no assets and its one link regex cannot
  distinguish an image from a link, so a Markdown image path is rewritten into
  a page or blob URL and an HTML `<img>`/`<picture>` is left pointing at
  nothing. Recorded as a defect at
  `docs/specs/docs-site-build-contract-hardening/notes/guide-image-projection.md`.
  No guide carries an image today, so the two pages this spec creates would be
  the first to hit it.
- Technical: GitHub's renderer removes inline `<svg>` outright and keeps
  `<img>` and `<picture>` (probed 2026-09-10 against `gh api POST /markdown`).
  So even once the projection defect is fixed, a diagram in a guide is an
  `<img>`, never inline — and the capability reference is a **table** for that
  reason, not a diagram.
- Product: **whether a plugin from this marketplace installs, exposes its
  skills, and completes a method in the Claude apps is unverified**, pending the
  dated probe required by
  [`claude-apps-first-value-entry`](../../product/intents/claude-apps-first-value-entry.md)
  § Projection. No criterion below depends on it.

## Durable outputs

| Role | Destination | Owner | Evidence | Closeout |
| --- | --- | --- | --- | --- |
| User-facing promise | `guides/_shared/how-to/<slug>.md` | guides maintainers | Cold-read comprehension check | Reader can state their next action and its surface |
| Reference | `guides/_shared/reference/<slug>.md` | guides maintainers | The matrix renders with stable columns | Every supported surface is a row |
| Current product truth | `web/src/pages/index.astro` start zone | web maintainers | Captures at desktop and 375 px | Two doors render with equal treatment |
| Navigation | `guides/README.md`, docs-site install page | respective maintainers | `make site-link-check` | Emitted links resolve |
| Decision rationale | ADR-0107 | eugenelim | Already Accepted | Done |
| Reusable learning | `docs/design/journeys/`, `docs/design/content/` | design | Already written | Done |

Release history and interface compatibility are **not applicable**: nothing
published changes and documentation takes no version bump.

## Boundaries

### Always do

- State the surface a capability applies to whenever the capability differs by
  surface.
- Keep `title:` frontmatter identical to the leading H1 on every new page.
- Link to `install-routes.md` for the four-route comparison and the
  organisation path rather than restating either, and keep the new pages free
  of any restatement of each other's content.

### Ask first

- Changing any literal that `tools/lint-plugin-route-docs.py` pins.
- Changing the home page's primary action, or the relative prominence of the
  two doors, beyond what the content brief's amendment specifies.
- Adding a fifth route to the install-routes table.

### Never do

- Never state or imply that a pack delivers first value on the Claude apps,
  that an install will succeed there, or that a method will complete there; and
  never add a Claude-apps entry to any `[pack.first-value].surfaces`.
- Never present the Claude-apps route as a fallback, a lite version, or a
  workaround.
- Never publish a count of reviewers, security modules, scanners, lifecycle
  stages, feedback loops, or knowledge topics on a public surface.
- Never embed an image in either new page. The projection defect above makes
  it silently broken on the docs site, and a capability matrix is the better
  form regardless. If a diagram becomes necessary, that defect is fixed first.
- **Structural:** never add a new top-level directory, a new guide quadrant, a
  new linter, or a new npm or Python dependency.

## Testing Strategy

| Outcome | Mode | Why |
| --- | --- | --- |
| 1 — two doors | Visual / manual QA | Equal treatment is a rendered property; captured at desktop and 375 px, light and dark. |
| 2 — actionable registration steps | Manual QA, cold read | Whether steps are followable is a comprehension property, checked by a reader stating their next action — not by executing against a third party. |
| 3 — limitations stated first | Goal-based check | Presence and placement are mechanically checkable. |
| Route integrity | Goal-based check | `make site-link-check` plus the four guide gates decide it. |

No TDD-mode outcome: this changes prose and one component's content, and a unit
test over prose would assert its own fixture.

## Accepted residuals

Sustained findings answered by acceptance rather than repair, with the reason
recorded so a later round does not re-raise them as open.

- **AC5's observer is a person, not a command.** "Every cell traceable to
  ADR-0107 or the survey, or reads `not established`" is checked by a reviewer
  reading the table against two documents. No mechanical oracle exists, and
  inventing one would compare the table to itself. Accepted as proportionate:
  the criterion can still fail, the comparison documents are named, and AC16
  already carries a human-observed check, so this adds no new class of
  verification burden.
- **AC14 conjoins four linters.** Round 1 split criteria that joined different
  predicates, and by that logic this could be four. Accepted as one: the four
  are the same kind of check over the same tree with one remedy path — fix the
  file and rerun — and splitting them would inflate the set without changing
  what any implementer does. The `Verification` block in the plan already runs
  them separately so a failure names itself.

Neither is a defect discovered late; both are judgements recorded at the point
they were made.

## Review status

Six independent review rounds ran on this spec and the intent above it: two
shaping, one adversarial, and three Sol passes. Every finding was adjudicated;
sustained ones were answered, and the answers are visible in this document's
history.

**No round returned a clean verdict on the current text**, and reviewing
stopped by decision rather than by convergence. The trend is the reason:
blocking counts across rounds ran 2, 2, 4, 1, 3, 3 — flat, not declining — while
the share of findings introduced by the previous round's repair rose. That is
the pattern a repair-first habit produces, and continuing would most likely
have surfaced a seventh defect of the same origin.

What this spec has instead of a clean verdict: a coverage pass reading
obligations back to owners (which found the wrong parent that six rounds of
reading criteria forward had missed), two residuals accepted with reasons, and
an honest record that a human read is the control not yet applied.

## Acceptance Criteria

- [ ] **AC1.** `guides/_shared/how-to/` contains one page giving the steps a
      reader performs to register this catalogue's marketplace in the Claude
      apps and submit an install for a discipline pack.
- [ ] **AC2.** That page states, at the registration step itself, that Claude
      Code and the Claude apps keep separate plugin stores and that registering
      in one does not register the other.
- [ ] **AC3.** That page states before its first step that the route needs a
      paid plan, that an administrator can restrict it, and what to do when the
      named menu is absent. It distinguishes viewport support from client
      support, and does not imply the route works on mobile.
- [ ] **AC4.** `guides/_shared/reference/` contains one page whose single table
      carries the columns Surface, Skills, Sub-agents, Hooks, and where artifacts
      land, with a row for each of Claude Code, Claude Desktop chat, web chat,
      and Cowork.
- [ ] **AC5.** Every cell in that table is either traceable to a statement in
      ADR-0107 or the distribution survey, or reads `not established`. No cell
      states a behaviour neither source supports.
- [ ] **AC6.** At desktop and 375 px, in light and dark, the terminal and
      Claude-apps doors render under one shared start-zone heading with
      identical heading level, CTA component variant, typography scale, and
      container treatment.
- [ ] **AC7.** Neither door's visible copy describes the other as a fallback,
      secondary, alternative, lite, or workaround.
- [ ] **AC8.** The rendered Claude-apps door on the home page links to the
      how-to page created by AC1, and to no other destination.
- [ ] **AC9.** `guides/README.md` and the docs-site install page each carry one
      link to the how-to page.
- [ ] **AC10.** `guides/_shared/explanation/install-routes.md` links to both new
      pages.
- [ ] **AC11.** `make site-link-check` reports no unresolved emitted internal
      link.
- [ ] **AC12.** No file changed by this spec adds a Claude-apps entry to any
      `[pack.first-value].surfaces`, and no changed file asserts that a pack
      delivers first value on the Claude apps, that an install succeeds there,
      or that a method completes there.
- [ ] **AC13.** No file changed by this spec publishes a count of reviewers,
      security modules, scanners, lifecycle stages, feedback loops, or knowledge
      topics.
- [ ] **AC14.** Each of `lint-plugin-route-docs.py`, `validate_guides.py`,
      `check-guide-index.py`, and `lint-guide-titles.py` exits 0.
- [ ] **AC15.** Every literal pinned for `install-routes.md` by
      `lint-plugin-route-docs.py` is byte-identical to its accepted-base value.
- [ ] **AC16.** A reader who has not seen these surfaces, given only the home
      page, states without assistance which door applies to them, what their
      next action is, and which surface the documentation directs them toward.
      The result is recorded with the date and every hesitation point.
- [ ] **AC17.** Immediately before the install-submission action, the how-to
      states that its documented outcome ends at submission, and that
      successful installation and method completion in the Claude apps are not
      established.
- [ ] **AC18.** Neither page created by this spec embeds an image — no
      Markdown image, no `<img>`, no `<picture>`. Its red input is any image
      syntax in either file; the guide projector would rewrite or strand it,
      and nothing else in the gate set would notice.
- [ ] **AC19.** Before the reader selects a discipline pack, the how-to links
      to the capability reference created by AC4 as the place to check
      surface-specific limits.
