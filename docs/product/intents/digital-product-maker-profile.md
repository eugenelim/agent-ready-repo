# Add a digital-product-maker profile

- **Slug:** `digital-product-maker-profile`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **De-risked:** 2026-11-05

## Outcome

A digital product maker can install the practitioner toolkit for product strategy, product engineering and experience design in one step, and finds a journey page and first-session guide that position it against the existing profiles.

## Opportunity

The catalogue's three user-scope profiles do not serve the digital-product-maker persona.

## What this absorbs

### digital-product-profile

This is the `ini-003` follow-on after the Digital Experience Doctrine initiative ships. The four disciplines — `product-strategy`, `product-engineering`, `experience-design`, and `frontend-engineering` — form a coherent digital product chain with a shared contract, skill boundaries, and a cross-pack eval. The catalogue's three user-scope profiles do not serve the digital-product-maker persona: `solution-architect` is `architect+research+contracts` with an infrastructure focus; `inception` is `research+PE+architect` with a tech-venture focus; and `full-ceremony` is a repository-governance bundle with repository scope.

The complete profile analysis is retained: `solution-architect` stays as-is because the infrastructure/system-architect persona is distinct. `full-ceremony` stays as-is because it is a governance bundle rather than a discipline toolkit. `inception` combines `desk-research+product-engineering+architect`; its `architect` pack serves a tech-founding persona that does system design before build. For pure digital product inception, `product-strategy` matters more than `architect`, but amending `inception` changes its meaning and breaks existing adopters. The decision for the future spec is either (A) amend `inception` to swap or add `product-strategy` alongside `architect`, or (B) leave `inception` as-is for tech ventures and let a new profile serve the digital-product persona. The recorded recommendation is B: retain `inception` for the “tech founder / solo dev” shape and add a profile for the “product maker / digital team” shape, because the personas are genuinely different.

The proposed `digital-product` user-scope profile is `product-strategy+product-engineering+experience-design+desk-research`, ordered deps-first, as the complete four-discipline toolkit for digital product work. `frontend-engineering` is outside the proposed profile: it defaults to user scope and also allows repo scope, so it installs separately, and the repository-only `core` pack covers the build loop. The user-scope profile supplies the practitioner's thinking toolkit; `core` and `frontend-engineering` cover the build layer. The future spec must cover: a new `profiles/digital-product.toml`; confirmation that `inception` stays as-is, or amendment if `ini-003` adoption evidence changes the case; a `web/` journey page for the digital-product-maker persona matching the existing solution-architect journey-page shape and positioning the profile against `inception` and `solution-architect`; a `site/` guide entry point with the first-session workflow “install profile → run product-strategy → shape → design → hand off contract to a repo's core pack”; and a pack-profiles spec AC update because the “ask first” boundary currently says “Adding a third shipped first-party profile” although `inception` made three. Named locations are `profiles/digital-product.toml` (new), `web/src/pages/journeys/`, and `guides/`.

Unblocks when: all `ini-003` specs ship, because the skill set must be final before guide content is authored and premature guide content will drift.

### Relationship to the Claude-plugin route

[ADR-0107](../../adr/0107-claude-plugin-route-serves-non-technical-adopters.md)
(Accepted 2026-09-10) settled how the same four disciplines reach a
non-terminal adopter: the Claude-plugin route is a supported surface, and the
packs install there individually. It deliberately creates **no** aggregate
plugin, because that is the meta-pack shape ADR-0003 / RFC-0013 option F
rejected and ADR-0107 upholds.

So the curation this intent expresses stays CLI-only by decision, not by
omission. A `profiles/*.toml` is read only by the `agentbundle` CLI and never
reaches the plugin route; a Claude-apps adopter gets the same four packs as
separate installs, and an organisation wanting one-shot setup scripts it itself.
This intent still owns the profile, the persona journey page, and the
first-session workflow, and its `ini-003` unblock is unchanged.

## Assumptions

- No accepted decision authorises a new user-scope profile yet; the profile follows the Digital Experience Doctrine initiative shipping. The gap is concrete because the existing `solution-architect`, `inception`, and `full-ceremony` profiles do not serve the digital-product-maker persona.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 768c0a90b87e635220c3c784d7cdae67644d7e1d

## Readiness

Decision 2026-11-05 by the owner: ship now, option B. `inception` stays as is and a new `digital-product` profile serves the product-maker persona. The earlier wait for every `ini-003` spec is dropped: the four packs, the shared contract, the skill boundaries and the experience-design index all exist.

Route: `new-spec`, one session. First slice: `profiles/digital-product.toml` (`product-strategy`, `product-engineering`, `experience-design`, `desk-research`, deps-first), the pack-profiles spec AC wording fix, a web journey page and a guide entry point. Agent-only proof: the profile-resolution tests load the profile and resolve every pack, and the guide and journey link checks pass. Checked 2026-11-05: `profiles/` holds only `full-ceremony`, `inception` and `solution-architect`. The profile is CLI-only by ADR-0107.

## Non-goals

- Changing `inception`, `solution-architect` or `full-ceremony`.
- Bundling `frontend-engineering` or `core` into the profile; they install separately.
- An aggregate Claude plugin, which ADR-0107 rules out.

**Riskiest assumption:** the profile's pack set resolves deps-first with the existing profile machinery and fits the pack-profiles contract. Tested agent-only by the profile-resolution tests loading the new profile and resolving every pack.

## De-risk result

2026-11-05. Built a scratch catalogue copy with a draft `digital-product` profile (`desk-research`, `product-strategy`, `product-engineering`, `experience-design`, user scope). `agentbundle list-profiles` lists it with scope `user`, and `agentbundle install --profile digital-product --dry-run` plans all four packs in order (two to install, two already present) with no error. The three new-pack allowed scopes include `user`. Verdict: supported. The journey page, guide entry and pack-profiles spec AC wording were not tested; they stay in the work-loop session.
