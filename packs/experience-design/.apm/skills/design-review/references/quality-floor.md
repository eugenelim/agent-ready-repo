# The `quality-floor` checklist

The **pack-shared floor** every `experience-design` artifact is held to — one file,
referenced by skills across the pack, never copied into a private sibling. The
authoring and connective skills (`creative-direction`,
`design-token-taxonomy`, `information-architecture`,
`user-flow`, `interaction-design`) reference it as they work via the
sibling-relative path `../design-review/references/quality-floor.md`;
`design-review` applies it as an explicit pass; `product-engineering`'s
`ux-writing` defers to it by-name (cross-pack, so by reference, not a
hard file load). It lives in `design-review/references/` because that is the
one location every consumer can resolve once the pack projects every skill as a
sibling under the adapter's skills root — a pack-level `references/` directory
does not project to any adapter. It is three commitments, not a values sheet —
it points at the recognized standards and names the principle, never the numbers.

## 1. Handle all states

A surface is not designed until every state it can be in is designed. The
happy path is one state among several; the others are where products feel
broken. For each interactive surface, decide what the user sees and can do
in each of the 18 canonical states. The full set is aligned with the
`frontend-engineering` build-time state matrix so that design time and build
time share the same vocabulary; the treatments here are design-intent
descriptions, not build-time implementation prescriptions.

Not all states apply to every surface — explicitly note states that are
genuinely inapplicable and record why in the design brief.

| State | When it applies | Design treatment |
|---|---|---|
| **loading** | Any async operation is in flight | Show a placeholder matching the final layout shape; communicate that something is happening and, where predictable, approximately how much remains; preserve layout so content arrival causes no jarring shift |
| **empty** | Nothing exists yet, or nothing matches; surface has never been populated | Distinguish *first-run* (below) from *no-results* (below); for a generic empty, orient the user to what belongs here and invite the first meaningful action |
| **first-run** | The surface has never had data — the user's first encounter | Orient and invite the first meaningful action; do not show the generic empty state; make the starting action visible and low-risk |
| **no-results** | A search or filter emptied the result set | Show what query was applied; show how to recover (clear filter, broaden search, start fresh); never a dead end |
| **error** | An operation failed | Say what happened in the user's terms; say what it means for them; name the next action; preserve prior content where possible; never a dead end |
| **partial** | Some data is present, some missing; some operations succeeded, some failed | Show what you have and mark what you don't rather than hiding the whole; make the missing portions recoverable |
| **disabled** | An action cannot be taken right now | Make the *why* recoverable — what would re-enable it — not just the *that*; render it visibly disabled, not invisible |
| **content** | The surface is in its normal loaded state | Spec this state too — it defines the layout shape every other state is measured against; its skeleton is the loading placeholder |
| **success** | An action completed | Confirm completion visibly and proportionately to the action's weight: subtle for low-stakes, prominent for high-stakes; never silent |
| **permission/denied** | The viewer is unauthorized or locked out of this surface | Show a read-only or locked view with a recoverable note — who can act, how to request access; never a blank screen or a dead end; this *extends* the state set for gated screens, it does not replace the other states — a gated screen still handles all applicable states *and* permission/denied |
| **offline** | The network is unavailable | Show cached content where possible; provide a manual retry; indicate that the content shown may be stale; never a silent failure |
| **blocked** | An action cannot proceed because of an external dependency or policy | Name the specific blocker and the resolution path; never leave the user with no next step |
| **destructive-confirmation** | The user is about to take an irreversible action | Require explicit confirmation with a clear statement of what will be destroyed; provide a safe default (cancel or back); never an ambiguous or dismissible confirmation for high-consequence actions |
| **long-content** | Content is significantly longer than typical for this surface | Offer progressive disclosure, a table of contents, or pagination; do not silently show only the first segment |
| **large-data-set** | A query returns more records than the surface can reasonably show at once | Design for virtual scrolling, pagination, or sampling; never slice the data silently — show the user that more exists |
| **high-zoom** | The surface is used at 200–400% zoom | Design so text reflows, controls remain operable, and no horizontal scrolling is required; test at the design stage by examining the layout at extreme zoom |
| **reduced-motion** | The user has requested reduced motion | All animation is replaced with an instant or cross-fade transition that preserves the information the motion carried; no sliding, scaling, or spinning remains |
| **keyboard-only** | All interactions are navigated via keyboard alone, with no pointer | Every action is reachable and completable via keyboard; the tab order is logical; focus indicators are always visible; no pointer-only affordances exist |

## 2. Accessibility floor

Accessibility is a floor the design clears, not a feature added later. Hold
the work to the **recognized standard — WCAG, at the conformance level your
context requires** — and read the criteria from the source; this checklist
points to them rather than reprinting any threshold. The principles that
recur:

- **Perceivable contrast** between text/meaningful elements and their
  background, at the standard's required level — verified against the
  standard, never eyeballed.
- **Operable without a pointer** — every action reachable and completable by
  keyboard and other non-pointer input, in a sensible order, with the
  current focus always visible.
- **Meaning never carried by one channel alone** — not by color alone, not
  by position alone; pair it with text, shape, or label.
- **Named for assistive tech** — every control and image has an accessible
  name and role that conveys what a sighted user sees.
- **Targets and timing forgiving** — interactive targets large enough to hit;
  time limits avoidable or extendable.

When a choice can't meet the floor, that is a finding to surface, not a
detail to defer.

## 3. Motion communicates state — honor reduced-motion

Motion earns its place by carrying meaning: it shows a **state change**,
preserves **continuity** across a transition, or expresses a **spatial
relationship** (where a thing came from, where it went). Motion that
communicates nothing is decoration, and decoration is the first thing to
distract or nauseate.

Two commitments follow:

- **Every animation answers "what does this tell the user?"** If the answer
  is "nothing," cut it.
- **Always provide a reduced-motion path.** Some users need motion
  minimized — for vestibular safety, for focus, by preference. The design
  must honor that signal: replace movement with an instant or gentle
  state change that preserves the *information* the motion carried, never
  stripping the meaning along with the movement. Express this as the
  principle in the design intent; the build wires it to the platform's
  own reduced-motion signal.
