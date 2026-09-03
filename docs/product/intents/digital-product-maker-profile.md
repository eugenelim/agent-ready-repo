# Add a digital-product-maker profile

- **Status:** Draft
- **Level:** feature

## Outcome

Digital product makers have a portable profile for the complete four-discipline toolkit.

## Opportunity

The catalogue's three user-scope profiles do not serve the digital-product-maker persona.

## What this absorbs

### digital-product-profile

This is the `ini-003` follow-on after the Digital Experience Doctrine initiative ships. The four packs — `product-strategy`, `product-engineering`, `experience-design`, and `core` — form a coherent digital product chain with a shared contract, skill boundaries, and a cross-pack eval. The catalogue's three user-scope profiles do not serve the digital-product-maker persona: `solution-architect` is `architect+research+contracts` with an infrastructure focus; `inception` is `research+PE+architect` with a tech-venture focus; and `full-ceremony` is a repository-governance bundle with repository scope.

The complete profile analysis is retained: `solution-architect` stays as-is because the infrastructure/system-architect persona is distinct. `full-ceremony` stays as-is because it is a governance bundle rather than a discipline toolkit. `inception` combines `desk-research+product-engineering+architect`; its `architect` pack serves a tech-founding persona that does system design before build. For pure digital product inception, `product-strategy` matters more than `architect`, but amending `inception` changes its meaning and breaks existing adopters. The decision for the future spec is either (A) amend `inception` to swap or add `product-strategy` alongside `architect`, or (B) leave `inception` as-is for tech ventures and let a new profile serve the digital-product persona. The recorded recommendation is B: retain `inception` for the “tech founder / solo dev” shape and add a profile for the “product maker / digital team” shape, because the personas are genuinely different.

The proposed `digital-product` user-scope profile is `product-strategy+product-engineering+experience-design+desk-research`, ordered deps-first, as the complete four-discipline toolkit for digital product work. `core` (`frontend-engineering`) remains repository scope and installs per repository rather than as a portable user skill. The user-scope profile supplies the practitioner's thinking toolkit; the repository-scope `core` pack covers the build layer. The future spec must cover: a new `profiles/digital-product.toml`; confirmation that `inception` stays as-is, or amendment if `ini-003` adoption evidence changes the case; a `web/` journey page for the digital-product-maker persona matching the existing solution-architect journey-page shape and positioning the profile against `inception` and `solution-architect`; a `site/` guide entry point with the first-session workflow “install profile → run product-strategy → shape → design → hand off contract to a repo's core pack”; and a pack-profiles spec AC update because the “ask first” boundary currently says “Adding a third shipped first-party profile” although `inception` made three. Named locations are `profiles/digital-product.toml` (new), `web/src/pages/journeys/`, and `guides/`.

Unblocks when: all `ini-003` specs ship, because the skill set must be final before guide content is authored and premature guide content will drift.

## Assumptions

- No accepted decision authorises a new user-scope profile yet; the profile follows the Digital Experience Doctrine initiative shipping. The gap is concrete because the existing `solution-architect`, `inception`, and `full-ceremony` profiles do not serve the digital-product-maker persona.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 768c0a90b87e635220c3c784d7cdae67644d7e1d
