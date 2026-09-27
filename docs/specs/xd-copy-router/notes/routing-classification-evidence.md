# XD copy-router routing-classification evidence

Date: 2026-09-26

## Owner authorization

The scope owner directed this delivery to use the bounded cold-classification
approach accepted for the sibling `xd-genre-router` fold: nine fixed cases
classified once against the pre-fold descriptions and once against the exact
post-fold candidate, from descriptions alone, with no retries. The probe runs
outside the work-loop and is used as external input to it.

This is a decision input, not a Claude `Skill` activation measurement. The
delivery makes no production-activation claim.

## Accepted result

All 18 classifications matched the expected route at high confidence.

- Pre-fold accuracy: 9/9
- Post-fold accuracy: 9/9
- Post-fold copy-layer convergence: 6/6 select `content-design`
- Boundary retention: 3/3 in both worlds
- Total classifier runs: 18
- Retries: 0

| Case | Expected pre | Actual pre | Expected post | Actual post | Result |
| --- | --- | --- | --- | --- | --- |
| C1 message and narrative structure — onboarding page | `content-design` | `content-design` (high) | `content-design` | `content-design` (high) | Pass |
| C2 message and narrative structure — API quickstart | `content-design` | `content-design` (high) | `content-design` | `content-design` (high) | Pass |
| C3 per-surface acquisition copy goals — pricing hero | `copy-direction` | `copy-direction` (high) | `content-design` | `content-design` (high) | Pass |
| C4 per-surface acquisition copy goals — tagline feel | `copy-direction` | `copy-direction` (high) | `content-design` | `content-design` (high) | Pass |
| C5 brand-level register — cross-channel voice | `tone-of-voice` | `tone-of-voice` (high) | `content-design` | `content-design` (high) | Pass |
| C6 brand-level register — arbitration rule | `tone-of-voice` | `tone-of-voice` (high) | `content-design` | `content-design` (high) | Pass |
| C7 boundary — product UI string | `ux-writing` | `ux-writing` (high) | `ux-writing` | `ux-writing` (high) | Pass |
| C8 boundary — visual direction | `creative-direction` | `creative-direction` (high) | `creative-direction` | `creative-direction` (high) | Pass |
| C9 boundary — screen hierarchy | `information-architecture` | `information-architecture` (high) | `information-architecture` | `information-architecture` (high) | Pass |

The six copy-layer cases cover each surviving mode twice: C1 and C2 message and
narrative structure, C3 and C4 per-surface acquisition copy goals, C5 and C6
brand-level register. Before the fold they select `content-design`,
`copy-direction` and `tone-of-voice` twice each; after it, all six select
`content-design`. The three boundary cases keep their route in both worlds.

## Method

Each case/world pair ran once in its own `codex exec` process with
`--ephemeral` (no persisted session), `-s read-only`, and a working directory
outside any repository, so the classifier inherited no dialogue turns and could
not read this repository. It saw only the fixed input below, selected one route
from descriptions alone, and returned one JSON object. Pre-fold and post-fold
runs were separate processes. There were no retries, and no run was repeated.

The classifier rule was: choose the single candidate whose description most
directly owns the request; choose `none` only when no candidate owns it.

## Fixed cases

- `C1`: Before wireframes, decide what our onboarding page must say and how the story should unfold
- `C2`: What does our API quickstart page need to communicate to developers?
- `C3`: Name the copy goals for this pricing-page hero before anyone writes the lines
- `C4`: Before we write the tagline for this surface, we need to name what it should feel like
- `C5`: Our teams sound inconsistent; define the brand voice every channel should share
- `C6`: What's the copy arbitration rule when urgency and warmth conflict across our communications?
- `C7`: Write the error message for when login fails
- `C8`: What's the visual aesthetic direction for the landing page?
- `C9`: Order the content on this settings screen by priority

## Shared neighboring candidates

- `ux-writing`: Use when shaping the actual words a user reads in a product's UI — characterizing the UI copy voice (how the brand register applies to UI states), writing recurring UI-state microcopy (error, empty, button, label), or reviewing copy before it ships. Triggers on "what should this error say", "write the empty-state copy", "name this button", "characterize our product's UI copy voice", "make this microcopy blame-free", "review this copy". Characterizes voice along a few axes, writes each UI state from a blame-free + actionable formula, and runs a content checklist. When a per-screen state matrix from `user-flow` is present, writes copy per screen × state keyed to the matrix; when absent, behaves as today. Do NOT use to frame the intent behind the feature (use `frame-intent`), to make visual or layout design decisions, to write documentation prose (use `new-guide`), or to establish the brand-level copy register (use `tone-of-voice`).
- `creative-direction`: Use when someone says a digital surface should feel premium, calm, playful, or otherwise has a vibe but no shared visual direction. Also use when refining or amending an existing direction, or when inheriting it into a new section, component, or feature. Produces ranked aesthetic goals and, when due, a `<output_dir>/direction/<slug>.md` record grounded in referents and arbitration rules. Use `design-system` after the direction to derive tokens, `information-architecture` for page hierarchy, and `design-review` to critique existing work. Product positioning belongs to product strategy; framing or scoping the bet belongs to `frame-intent`; implementing colors, type, or components belongs to `frontend-engineering`. Triggers on "turn this calm, premium vibe into a shared visual direction", "name and rank the aesthetic goals for our mobile app", "ground this visual mood before we choose colors and type", "refine the existing direction to be bolder", "amend the direction doc to be quieter".
- `information-architecture`: Use when someone asks what goes where on a screen or flow, in what order, or how a genre-specific surface helps people understand, navigate, decide, or act. Produces IA and layout specs for general screens and flows plus analytical dashboards/reports/monitoring; conversion landing, home, pricing, and acquisition pages; documentation sites, help centers, API references, and guide sets; informational articles/news/editorial pages; marketplace catalogues/listings/comparison/transaction paths; and sustained-work collaboration or agentic workspaces. Selects the genre from the brief and applies its method for hierarchy, reading flow, navigation, wayfinding, filters, comparison, context persistence, or action-oriented reporting. Use `interaction-design` for within-screen behavior and transactional journeys, `design-system` for tokens and components, `design-review` for critique, and `creative-direction` for visual mood. Strategy/scope stay upstream; final copy and implementation belong elsewhere.
- `define-content-strategy`: Use when a strategist needs to set the organizational content direction before content design begins — the governance and structural layer above per-surface content execution. Triggers on "define the content strategy", "I need to set the content strategy before content design", "content governance framework", "Halvorson content strategy", "Purpose Process Structure Governance". Produces a committed content-strategy.md. Do NOT use to write per-surface content or microcopy — that belongs to the content-design skill in the experience-design pack.

## Pre-fold candidates

- `content-design`: Use when someone asks what a surface should communicate, to whom, in what form, and in what order before wireframes or final copy. Produces a content brief for acquisition, product, or reference surfaces. It owns message and narrative structure; `tone-of-voice` owns the brand register, `copy-direction` owns acquisition-surface copy goals, and `ux-writing` owns product UI strings. Organization-level content strategy belongs to `define-content-strategy`; feature framing belongs to `frame-intent`; page or content-system implementation belongs to `frontend-engineering`. Triggers on "create a content brief for our onboarding flow", "decide what this pricing page needs to say and in what order", "shape the message hierarchy before we wireframe the help page".
- `copy-direction`: Use when someone asks what the copy on one marketing or acquisition surface should feel like before the lines are written. Produces ranked, grounded copy goals and a `copy-direction.md` record for that surface. `tone-of-voice` owns the cross-surface brand register, `content-design` runs first to decide message and narrative structure, and `ux-writing` owns product UI strings. Product or growth strategy belongs to product strategy; framing the acquisition bet belongs to `frame-intent`; implementing the surface belongs to `frontend-engineering`. Triggers on "name the copy direction for our pricing page before we write it", "what should this onboarding campaign sound like", "set ranked copy goals for this landing page".
- `tone-of-voice`: Use when a team asks how the brand should sound consistently across channels and surfaces. Produces a brand-register document with named, ranked voice goals and arbitration rules. It is the upstream anchor: `content-design` owns a surface's message and structure, `copy-direction` owns acquisition-surface copy goals, and `ux-writing` owns product UI strings. Organization-level product or content strategy belongs to the strategy packs; shaping a product initiative belongs to `frame-intent`; implementing copy in templates or components belongs to `frontend-engineering`. Triggers on "define how our brand should sound across product and marketing", "name and rank our cross-surface voice goals", "create a brand register for our support, sales, and product copy".

The pre-fold candidate set was the three entries above plus the four shared
neighboring candidates.

## Post-fold candidates

- `content-design`: Use when someone asks what a surface should communicate or how its copy should feel before final words are written, or when a team needs a cross-surface brand register. Runs in three modes: message and narrative structure for a content brief; per-surface acquisition copy goals for a copy-direction record; brand-level register for named, ranked voice goals and arbitration rules. Use `ux-writing` for final product UI strings and state microcopy, `creative-direction` for visual mood, and `information-architecture` for page hierarchy. Organization-level content strategy belongs to `define-content-strategy`; product positioning and growth strategy stay upstream; implementation belongs to `frontend-engineering`. Triggers on "shape the message hierarchy before we wireframe", "set ranked copy goals for this landing page", and "define how our brand should sound across product and marketing".

- `ux-writing` **(post-fold)**: Use when shaping the actual words a user reads in a product's UI — characterizing the UI copy voice (how the brand register applies to UI states), writing recurring UI-state microcopy (error, empty, button, label), or reviewing copy before it ships. Triggers on "what should this error say", "write the empty-state copy", "name this button", "characterize our product's UI copy voice", "make this microcopy blame-free", "review this copy". Characterizes voice along a few axes, writes each UI state from a blame-free + actionable formula, and runs a content checklist. When a per-screen state matrix from `user-flow` is present, writes copy per screen × state keyed to the matrix; when absent, behaves as today. Do NOT use to frame the intent behind the feature (use `frame-intent`), to make visual or layout design decisions, to write documentation prose (use `new-guide`), or to establish the brand-level copy register (use `content-design`'s brand-level register mode).

The post-fold candidate set was the `content-design` entry, the post-fold
`ux-writing` entry, and the three shared neighboring candidates this delivery
does not edit.

`ux-writing` appears in both worlds with different text, deliberately. This
delivery edits that description: its pre-fold form ends "(use `tone-of-voice`)",
a routing target naming a removed skill that the registration sweep obliges the
delivery to retarget. Testing the pre-fold text in the post-fold world would
have classified a boundary candidate that does not ship.

## Shipped-description binding

The tested post-fold `content-design` description is 895 characters,
within the 1,024-character cap that `skill_spec_lint.py` enforces as an error.
The shipped description must be byte-identical to it; T9 checks that. The
shipped post-fold `ux-writing` description must likewise be byte-identical to
the post-fold entry above, or the divergence recorded as immaterial with its
reason.

A material routing or boundary change to either description requires a new
owner-approved bounded probe, or stops the slice.

## Abort path

Three triggers, any one of which stops this fold before a skill directory is
deleted:

1. a classification mismatch or any result below high confidence;
2. an explicit owner stop;
3. the brief's approximately three-week appetite window elapsing before the
   fold lands.

On any trigger the two directories are not deleted and nothing in this slice
ships. The deciding owner is `eugenelim`. None of the three fired: the probe
returned 18/18 at high confidence, there is no owner stop, and the window has
not elapsed.

## Limits

This is a classification proxy, not a Claude `Skill` activation event. Codex
retained its own platform system context despite inheriting no dialogue turns
and no repository access. One sample per case and world does not establish
broad recall, false-positive rates, repeated-sampling stability, or production
activation behavior. The nine cases are fixed and were written before the runs;
they are not a random sample of real requests.

## T9 — shipped-description binding, verified

Checked 2026-09-27 against the shipped tree.

| Description | Tested | Shipped | Verdict |
| --- | ---: | ---: | --- |
| `content-design` | 895 chars | 895 chars | **Byte-identical** |
| `ux-writing` (post-fold) | 972 chars | 972 chars | **Byte-identical** |

Both are within the 1,024-character cap `skill_spec_lint.py` enforces as an
error rather than a warning. No divergence had to be recorded as immaterial,
because there is none, and no second probe was run.

The `ux-writing` row is the one worth naming. That description is a boundary
candidate the probe classified, and this delivery edits it — its pre-fold form
ended "(use `tone-of-voice`)", a routing target naming a removed skill. Had T1
tested the pre-fold text, the shipped boundary would have been unverified even
with an 18/18 result, because only `content-design`'s description was bound.

The pooled corpus also holds: 29 distinct positive and 32 distinct negative
queries, no query under both `should_trigger` values, with 8 negatives owned by
`ux-writing` and 3 by `creative-direction` retained.

No live activation run and no repeated classifier sampling occurred.
