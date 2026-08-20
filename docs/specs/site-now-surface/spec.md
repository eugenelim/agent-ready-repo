# Spec: Site Now surface

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0089
- **Brief:** docs/product/briefs/tech-site-completion.md
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what done means. The implementing
> change matches this spec or updates it before merge.

## Objective

Adopters can visit `/now/` to see concise, sourceable outcomes that have
actually shipped. The surface reuses the existing changelog lifecycle, never
publishes in-progress work, and requires no editorial team or runtime AI
pipeline.

## Boundaries

### Always do

- Use optional `Highlights` subsections in
  `docs/product/changelog.md` as the only initial content source.
- Publish a highlight only after its enclosing release entry has a version and
  release date and is outside the `Unreleased` section.
- Keep highlight drafting inside the normal development/release lifecycle:
  ground it in the implemented diff and verification evidence, and use the
  ordinary implementation reviewer.
- Generate `/now/` deterministically at build time with no model call.
- Remove the public `/work/` route, projection, and destination completely.
- Preserve `m6-astro-work-index` as the frozen historical record of what
  shipped; use the living specs index and this spec to identify the approved
  successor rather than rewriting or prematurely annotating its Status.

### Ask first

- Add a content source other than released changelog Highlights, extend Now to
  a new editorial format, change the freshness/order contract, or introduce a
  separate editorial review gate.
- Publish an outcome that lacks stable repository-owned source evidence.
- Restore `/work/` or add a redirect or compatibility route.

### Never do

- Publish `Unreleased` content, plans, briefs, queue state, commits, pull
  requests, backlog, or claims about what the team is building.
- Invent customer names, adoption numbers, usage claims, testimonials, or
  credibility copy.
- Require an LLM in CI, release automation, or site generation.
- Add a dependency or create a second changelog/publishing pipeline.

## Content and projection contract

- The route and H1 are exactly **Now** at `/now/`.
- A changelog release entry may contain one optional `Highlights` subsection at
  the heading level appropriate to that entry. Its bullets are outcome-led,
  user-facing prose reviewed in the same PR as the implementation or release.
- Entries beneath `Unreleased` never project, even if they contain Highlights.
- A released entry without Highlights remains in the technical changelog and
  is absent from Now.
- Now orders released entries by release date descending and preserves source
  order for ties. Each projected group names the released package/version and
  date and links to the corresponding changelog entry.
- Launch content contains every meaningful released highlight dated within the
  seven calendar days ending on launch day, inclusive. The seed is written
  only from those released changelog entries—not reconstructed from plans,
  commits, or unfinished work.
- The seven-day window is an authoring rule for the launch seed. The projection
  applies no date window at all: it publishes every released entry carrying
  Highlights, and a filter evaluated at build time would contradict the
  determinism requirement below by changing the page at midnight from unchanged
  source. A reader expecting a seven-day filter in the projection will not find
  one, and should not add one.
- If no released highlight qualifies, the page remains valid and says **No
  released highlights yet.** followed by a **Read the changelog** link.
- `/now/` may later expand to other shipped adopter-facing formats only through
  an approved amendment; the name and route do not imply a changelog-only
  permanent boundary.

## Testing Strategy

- Relative changelog-section parsing, release eligibility, ordering, omission,
  and launch-window rules use TDD with valid and invalid fixtures.
- Route generation, removal of `/work/`, source links, and absence of
  Unreleased/development content use goal-based emitted-output checks.
- Highlight quality and grounding use ordinary content review against the
  implemented diff, verification evidence, and released changelog source.

## Acceptance Criteria

- [x] The marketing build emits `/now/` with H1 `Now` and emits no `/work/`
  page, redirect, navigation route, or public work-index projection.
- [x] The only initial Now content source is an optional `Highlights`
  subsection in the existing `docs/product/changelog.md` lifecycle; no new
  source file, service, dependency, or publishing pipeline exists.
- [x] Only Highlights belonging to versioned, dated release entries outside
  `Unreleased` project to Now; fixtures prove that Unreleased content and
  releases without Highlights are absent.
- [x] Projected release groups identify package/version and date, link to their
  changelog entry, sort by release date descending, and preserve source order
  for equal dates.
- [x] The launch seed contains all and only meaningful released highlights in
  the inclusive seven-calendar-day window ending on launch day and is grounded
  in those released changelog entries.
- [x] The changelog maintenance contract permits AI-assisted drafting from the
  implementation diff and verification evidence, requires ordinary PR review,
  and forbids publication while content remains Unreleased.
- [x] No model or nondeterministic editorial operation runs in CI, release
  automation, or site generation; repeated builds from the same source produce
  identical Now content.
- [x] When no released highlight qualifies, `/now/` emits the exact approved
  empty state and a working internal link to the complete changelog.
- [x] Emitted-output tests fail when Unreleased text, work/queue terminology,
  an ineligible date, broken changelog fragment, or `/work/` route appears.
- [x] Shared chrome may consume the `Now` label and `/now/` target only after
  the route contract passes; shared chrome remains the sole owner of its
  final navigation taxonomy, ordering, mobile behavior, and current-state
  treatment. The Now slice owns only replacing the current `Work` label and
  `/work/` target in place so it leaves no broken or stale public link.
- [x] The frozen `m6-astro-work-index` spec and plan remain byte-unchanged; the
  living specs index identifies `site-now-surface` as its approved successor,
  and retirement removes the old public implementation, projection exporter,
  and their tests while preserving historical provenance.

## Assumptions

- Technical: `docs/product/changelog.md` already receives user-visible entries
  in the implementation PR and distinguishes the `Unreleased` region from
  released version/date entries (source: repository inspection on 2026-08-17).
- Product: public updates announce shipped adopter value, not development
  activity; `/work/` is removed outright and `/now/` is the approved long-term
  container (source: user approvals 2026-08-17).
- Product: launch uses the inclusive seven-day released-highlight seed and the
  existing changelog remains the initial source (source: user approval
  2026-08-17).
- Process: AI assistance is optional drafting inside the normal development
  lifecycle, not a new editorial team or automated publication authority
  (source: user approval 2026-08-17).
