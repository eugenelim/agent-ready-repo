# State coverage reference — the 18-state set

> **Reference** — information-oriented. The canonical 18-state set shared by
> `design-review` (at design time) and `frontend-engineering` (at build time),
> aligned so design vocabulary and build vocabulary match. For the design-intent
> floor rules each state must clear, see
> [`quality-floor.md`](../../../../packs/experience-design/.apm/skills/design-review/references/quality-floor.md)
> in the pack. For how to apply this during a review, see the
> [how-to guide](../how-to/design-review.md).

The 18-state set is the complete set of conditions an interactive surface can be
in. A surface is not designed until every applicable state has a design decision.
Not all states apply to every surface — note states that are genuinely inapplicable
and record the reason in the per-screen brief.

## The 18 states

| # | State | When it applies | Design-intent treatment | Example |
|---|---|---|---|---|
| 1 | **loading** | Any async operation is in flight | Show a placeholder that matches the final layout shape; communicate that work is in progress; preserve layout to prevent jarring shifts when content arrives | A dashboard card shows a shimmering placeholder matching the chart's dimensions while data loads |
| 2 | **empty** | Nothing exists yet, or nothing matches a query; the surface has been populated before | Orient the user to what belongs here; invite the first meaningful action; distinguish from first-run | A shared folder shows an icon, label "Nothing here yet", and a link to upload |
| 3 | **first-run** | The surface has never had data — the user's first encounter | Orient and invite the primary action; make starting low-risk; never show the generic empty state | An onboarding workspace shows a welcome illustration with a single "Create your first project" action |
| 4 | **no-results** | A search or filter returned an empty set | Show what query was applied; give a clear recovery path (clear filter, broaden search, start fresh); never a dead end | A search results page shows "No results for 'X'" with a "Clear search" button |
| 5 | **error** | An operation failed | Name what happened in the user's terms; say what it means for them; give the next action; preserve prior content where possible | A form submission shows "We couldn't save your changes — your session may have expired. Please sign in again." with a Sign-in button |
| 6 | **partial** | Some data is present, some missing; some operations succeeded, some failed | Show what you have and mark what you don't; make missing portions recoverable | A multi-select bulk action shows "3 of 5 items archived. 2 items could not be archived — view errors." |
| 7 | **disabled** | An action cannot be taken right now | Make the *why* recoverable — what would re-enable it — not just the *that*; render it visibly disabled | A "Publish" button is disabled with a tooltip "Add a title before publishing" |
| 8 | **content** | The surface is in its normal loaded, populated state | Design this state first — it defines the layout shape every other state is measured against; its silhouette is the loading placeholder | The populated dashboard with data in all widgets |
| 9 | **success** | An action completed | Confirm completion visibly and proportionately to the action's weight — subtle for low-stakes, prominent for high-stakes; never silent | A saved item shows a brief "Saved" toast; a completed onboarding shows a celebration banner |
| 10 | **permission/denied** | The viewer is unauthorized or locked out of this gated surface | Show a read-only or locked view with a recoverable note — who can act, how to request access; never a blank screen or dead end; this extends the state set for gated surfaces, not replaces it | A report page shows a lock icon and "You don't have access to this report. Ask your admin for the Analytics role." |
| 11 | **offline** | The network is unavailable | Show cached content where possible; provide a manual retry; indicate that shown content may be stale | A mobile app shows a banner "You're offline — showing last synced data from 2 hours ago" with a Retry button |
| 12 | **blocked** | An action cannot proceed because of an external dependency or policy | Name the specific blocker and its resolution path; never leave the user with no next step | A deploy button shows "Blocked — waiting for review from @teammate. Ping them to unblock." |
| 13 | **destructive-confirmation** | The user is about to take an irreversible action | Require explicit confirmation with a clear statement of what will be destroyed; provide a safe default (cancel); never ambiguous or dismissible for high-consequence actions | A delete dialog shows "Delete 'Q4 Report'? This cannot be undone. All 12 linked assets will be removed." with a red Delete and a Cancel |
| 14 | **long-content** | Content is significantly longer than typical for this surface | Offer progressive disclosure, a table of contents, or pagination; do not silently truncate or show only the first segment | A changelog page with hundreds of entries shows a table of contents at the top and paginated entries with visible entry count |
| 15 | **large-data-set** | A query returns more records than the surface can reasonably show at once | Design for pagination or sampling; show the user that more exists; never silently show only the first page | A contacts list shows "Showing 50 of 4,208 contacts — Load more" at the bottom |
| 16 | **high-zoom** | The surface is used at 200–400% browser or system zoom | Design so text reflows, controls remain reachable and operable, and no horizontal scrolling is forced | At 200% zoom, a two-column form stack becomes single-column and the submit button remains fully visible |
| 17 | **reduced-motion** | The user has requested reduced motion | Replace all animation with an instant or cross-fade transition that preserves the information the motion carried; no sliding, scaling, or spinning remains | A sidebar that normally slides in instead appears instantly; a progress spinner becomes a progress bar |
| 18 | **keyboard-only** | All interactions are navigated via keyboard alone, with no pointer | Every action is reachable and completable via keyboard; the tab order is logical; focus indicators are always visible; no pointer-only affordances exist | The "More options" menu opens on Enter, its items are navigable with arrow keys, and pressing Escape returns focus to the trigger |

## Applying the state set

**At design time (`design-review`):** for each applicable state, decide what the
user sees and can do. Record missing states as findings — the tier depends on
whether the user has a path forward without the state:
- State missing with no fallback → **Blocker**
- State missing but degraded fallback present → **Concern**

**At build time (`frontend-engineering`):** implement and test each state from
the spec. The state vocabulary here is shared, so a "blocked" state in the
design brief corresponds directly to the "blocked" state in the implementation.

**Not all states apply to every surface.** A static informational page has no
`loading`, `empty`, `first-run`, `partial`, `blocked`, or `destructive-confirmation`
state — it legitimately omits them. An internal dashboard that is always accessible
omits `permission/denied`. Record omissions in the per-screen brief so the build
team knows the omission was intentional, not forgotten.
