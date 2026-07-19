# Interaction pattern families

Recognized pattern families a per-screen brief can invoke. Each family is **referenced** — this file names the pattern, describes its purpose, and points to where it is documented. These are not authored as standalone skills; a brief reaches for the family, and the design applies the specific pattern that fits the context.

## Onboarding patterns

Onboarding patterns address the **first-use experience** — guiding users from initial arrival to their first meaningful action without friction or overwhelm. Three recognized families:

### Progressive onboarding

Introduce features incrementally as the user's actions make them relevant. The user learns by doing rather than by reading. The design question is: "at what moment in the user's task does knowing this feature actually help them?" Surface the feature at that moment, not before.

**Reference:** [NN/g: Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/) and [NN/g: User Onboarding](https://www.nngroup.com/articles/onboarding-checklist/) cover the principle and the research. The *progressive onboarding* pattern specifically delays non-essential feature introductions until the user's context makes them relevant.

### Empty-state as onboarding

The empty state — the screen before a user has added any data or taken any meaningful action — is the most underused onboarding surface. A well-designed empty state orients the user (what is this for?), invites the first action (what should I do?), and shows what the fulfilled state will look like. It is not a blank screen.

**Reference:** [NN/g: Empty State Design](https://www.nngroup.com/articles/empty-state-mobile-app-design/) and the quality floor's handle-all-states section (distinguishing first-run from no-results). The empty state is a designed state, not an oversight.

### Contextual coachmarks

In-context overlays or tooltips that appear at the moment a user encounters a feature for the first time. Unlike modal onboarding tours, coachmarks are anchored to the specific UI element they explain and dismiss individually. Overuse degrades trust; reserve for non-obvious affordances the user is about to encounter.

**Reference:** [NN/g: Tooltip Guidelines](https://www.nngroup.com/articles/tooltip-guidelines/) covers when contextual overlays help vs. interrupt. The pattern is most effective when: (1) the feature is genuinely non-obvious, (2) the user is about to need it, and (3) the explanation is one sentence.

## Search-interaction patterns

Search-interaction patterns address the **user's active information-finding task** — how a search surface behaves from the moment of intent through result-exploration and refinement. Three recognized families:

### Typeahead / autocomplete

Suggest completions as the user types, reducing keystrokes and steering toward valid queries. The pattern has a behavioral contract: suggestions appear promptly (perceived-performance: Doherty Threshold applies), are navigable by keyboard, and reflect the user's likely intent rather than arbitrary string matching.

Design decisions to record in the brief:
- At how many characters do suggestions appear?
- Are suggestions queries (what others searched for) or items (direct results)? Both can appear in separate groups.
- What happens when there are no suggestions? (A no-suggestions state is a designed state, not an empty gap.)

**Reference:** [NN/g: Autocomplete Design Guidelines](https://www.nngroup.com/articles/autocomplete-design/) covers the research and the key design decisions. Keyboard accessibility is required; pointer-only autocomplete fails the quality floor's accessibility commitment.

### Faceted filtering

Allow users to narrow a result set by selecting attributes across multiple dimensions simultaneously. The design question is: which facets are most discriminating for the user's task, and in what order should they appear?

Behavioral design decisions:
- **Instant vs. apply-button filtering** — instant feedback (results update as facets are selected) is preferred for small to medium sets; an explicit apply step is appropriate when the query is expensive.
- **Active filter summary** — show the user which filters are active and make each independently removable. A "clear all" is always available.
- **No-results state** — when filter combination yields no results, show what filters are causing it and suggest a relaxation path. Never a dead end.

**Reference:** [NN/g: Filters vs. Facets](https://www.nngroup.com/articles/filters-vs-facets/) and [NN/g: Faceted Search](https://www.nngroup.com/articles/faceted-search/) cover the distinction and the design choices. The pattern is most effective when the item set is large and heterogeneous.

### Zero-result and error-result handling

The zero-result state (a search that matched nothing) and the error-result state (a search that failed) are distinct designed states, each with a different recovery path.

**Zero results** — the user should understand *why* nothing matched and have a clear path to broaden the query or try a related search. Suggestions ("Did you mean…?", "Try removing the [filter] filter") are more useful than a blank page with a generic "no results" message.

**Error results** — the search surface encountered a system error. Name what happened in user terms, confirm that the user's query was received, and offer a retry. If partial results are available, show them with a note; "some results could not be loaded" is better than hiding everything.

**Reference:** [NN/g: No Results Found](https://www.nngroup.com/articles/no-results-search-ux/) covers the research on user responses to empty search results. The quality floor's error and partial states apply to the search surface; this pattern operationalizes them in the search context.

---

## Wizard-and-stepper patterns

Wizard-and-stepper patterns address **multi-step flows where the user must complete steps in a defined order** — checkout, onboarding configuration, complex form sequences, account setup, and transaction journeys. Three recognized families:

### Linear stepper

A stepped sequence with a visible progress indicator (step count, progress bar, or step labels). Each step collects information or requires a decision before the next step is available. The design contract: the user always knows how many steps remain, where they are, and how to go back.

Design decisions to record in the brief:
- Is the step sequence fixed, or can steps be skipped based on earlier answers?
- Is the back action destructive (clears the current step's state) or restorative (returns the user to their previous answers)? Back must be restorative by default.
- Does the final step show a review of all prior answers before submission? For consequential transactions, yes — the review step is not optional.

**Reference:** [NN/g: Wizard Design](https://www.nngroup.com/articles/wizards/) covers step-indicator design, back-button behavior, and when to use a wizard vs. a single long form. The `marketplace-design` skill's transaction bridge section names the handoff from marketplace to wizard.

### Save-and-resume

Multi-step flows longer than a single session must support save-and-resume: the user's progress is saved at each step completion, and returning to the flow restores them to their last completed step. This is not autosave (continuous background save); it is explicit step-completion save.

Design decisions to record in the brief:
- At what granularity is progress saved? (On step completion? On field blur? On navigation away?)
- How is a draft-in-progress surfaced to the user when they return? (Email link, in-app notification, "continue where you left off" banner?)
- What is the expiry policy for an incomplete flow? The user must be informed of expiry before their draft expires, not after.

### Conditional disclosure (branching steps)

When the user's answer to a step determines which step comes next, the stepper implements conditional disclosure — steps appear or are skipped based on prior answers. The user should not see a step that does not apply to them.

Design decisions to record in the brief:
- Which steps are conditional, and on which prior answer?
- When a conditional branch is taken, does the step count update to reflect the actual remaining steps? It should — a count that says "step 3 of 7" when the user's path only has 5 steps is misleading.
- Can the user change an earlier answer that would change their branch? If yes, the flow must handle the state reset of the downstream steps cleanly.

---

## Data-table patterns

Data-table patterns address **tabular data surfaces** where users need to scan, filter, sort, act on, or drill into rows. Three recognized families:

### Filter, sort, and column control

The user's ability to narrow, reorder, and reshape the table to match their task. Design decisions:
- **Filter scope:** does the filter apply to the entire table or just the visible columns? Column-level filters (inline filter inputs) and table-level filters (sidebar or toolbar) serve different tasks — column filters serve column-specific lookup; table filters serve cross-column query.
- **Sort behavior:** single-column vs. multi-column sort; ascending vs. descending defaults; visual indicator (sort arrow) must be on the active column, not all columns.
- **Column visibility control:** for tables with more columns than the viewport can show, provide a column selector. The default column set is the one a new user needs; power users customize from there.

**Reference:** [NN/g: Data Tables](https://www.nngroup.com/articles/data-tables/) covers the research on table scanning, row identification, and sort expectations.

### Bulk operations

When users need to act on multiple rows simultaneously, the table provides bulk selection and a bulk-action surface:
- **Selection model:** checkbox per row; a header checkbox selects/deselects all visible rows. Make the selected count visible ("3 rows selected") before any bulk action is available.
- **Bulk action surface:** appears contextually when rows are selected (toolbar, action bar, or floating panel). Does not appear when nothing is selected.
- **Destructive bulk actions** (delete, archive) follow the destructive-action escalation pattern (see below) — at minimum a modal confirmation naming the count of affected rows.

### Row detail: expand vs. navigate

When a row has more information than fits in the table, provide a way to access it. Two recognized patterns:
- **Inline expand (row expansion):** clicking the row reveals additional detail beneath it without leaving the table. Best when the detail is supplementary and the user's task returns to the table (scanning a list, comparing multiple items).
- **Navigate to detail page:** clicking the row navigates to a dedicated detail view. Best when the detail is the primary task and the user is unlikely to immediately return to the table.

Name which pattern applies and why — the choice has IA implications for wayfinding (the detail page needs a back path to the table, including filter/sort state preservation).

---

## Destructive-action escalation patterns

Destructive-action patterns address **actions that delete, overwrite, or irrevocably modify data**. The escalation pattern defines 5 tiers — matched to the severity and reversibility of the action.

### 5-tier escalation

| Tier | Pattern | When to use | Examples |
|------|---------|------------|---------|
| **1 — Inline (no confirmation)** | Action executes immediately; outcome is instantly visible and reversible | Low-stakes, immediately reversible actions | Archive a draft, clear a search field, collapse a section |
| **2 — Toast + undo** | Action executes immediately; a toast notification appears with an undo affordance for a brief window | Moderate-stakes, briefly reversible actions | Delete a comment, remove a tag, unsubscribe from a notification |
| **3 — Modal confirmation** | Action is blocked by a modal asking the user to confirm before executing | High-stakes, irreversible or hard-to-reverse actions | Delete an item, leave a team, cancel a subscription |
| **4 — Typed confirmation** | Modal requires the user to type a specific word or name to confirm | Very high-stakes actions affecting irreplaceable data or many records | Delete an account, delete a project with all its contents, drop a database |
| **5 — Two-factor or two-person confirmation** | Action requires a second authentication step or a second person's approval | Mission-critical, organizational-scope actions | Transfer account ownership, delete a production environment, approve a large financial transaction |

**Design decisions to record in the brief:**
- Which tier applies to each destructive action on this surface? Map every destructive affordance to a tier before any are designed.
- For Tier 3 (modal): name the exact action and its consequence in the modal body. "Are you sure?" without context does not help the user make an informed decision. "Delete [item name]? This cannot be undone." does.
- For Tier 4 (typed): name what the user types (the item name, not a generic phrase like "DELETE" — the item name confirms the user read what they are deleting).

**Reference:** [NN/g: Confirmation Dialog](https://www.nngroup.com/articles/ok-cancel-or-cancel-ok/) and [NN/g: Preventing User Errors](https://www.nngroup.com/articles/slips/) cover the research on error prevention vs. confirmation dialogs. The 5-tier escalation extends the quality floor's handle-all-states section for destructive paths.

---

## Save-state patterns

Save-state patterns address **how a surface communicates that the user's work is safe** — the signal between action and persistence. Three recognized families:

### Autosave with indicator states

The surface saves automatically as the user works. The autosave indicator has three states, each visible to the user:

| State | What it communicates | Indicator design |
|-------|---------------------|-----------------|
| **Saving** | A save is in progress | Subtle animated signal (spinner, pulsing dot) — ambient, not demanding |
| **Saved** | The most recent state is persisted | Static confirmation ("Saved" + timestamp, or a checkmark) — remains visible briefly, then fades |
| **Error — not saved** | A save failed | Persistent error signal — does not fade until the save succeeds or the user takes action; includes a retry affordance |

The "saved" state must be visible, not assumed. A user who does not know if their work was saved will hesitate to navigate away — or will navigate away and lose work.

### Unsaved-changes guard

When a user attempts to leave a surface with unsaved changes (navigate away, close the tab, start a new document), the surface intercepts with an unsaved-changes warning:
- Names what is unsaved ("You have unsaved changes to [document/form/section].")
- Offers three options: Save and continue, Discard and continue, Cancel (stay on the page).
- Does not execute the navigation until the user has made an explicit choice.

The guard applies to any navigation that would lose data: route changes, browser back, tab close, external links from within the editing surface.

### Draft vs. published state

When a surface supports the concept of a draft (work in progress) and a published or submitted state (committed to others), the two states must be visually distinct at all times:
- The user always knows which state they are in.
- Editing a draft does not affect the published version — changes are isolated to the draft until the user explicitly publishes.
- The "publish" or "submit" action is distinct from the "save draft" action — they are never the same button.

---

## Analytical-dashboard-widget patterns

Analytical-dashboard-widget patterns address **the behavioral design of individual widgets on an analytical surface** — how each widget signals, alerts, and enables drill-down. Three recognized families:

### KPI card anatomy

A KPI card is the atomic unit of a Tier 1 primary signal. Its anatomy:

| Element | Purpose | Design constraint |
|---------|---------|-----------------|
| **Metric name** | Names what is being measured | Plain language; no internal jargon or code names |
| **Primary value** | The current state of the metric | Largest element in the card; the user reads this first |
| **Trend indicator** | Direction of change (up, down, flat) | Arrow or sparkline; color alone is insufficient (accessibility) |
| **Comparison baseline** | What the primary value is compared against (prior period, target, industry benchmark) | Named explicitly — "vs. last week" not just a delta number |
| **Status signal** | Whether the current state is good, concerning, or critical | Color + icon (never color alone); calibrated to the metric's thresholds |

A KPI card that is missing the comparison baseline produces a primary value the user cannot interpret. "1,247 active users" means nothing without "vs. 1,100 last week" or "vs. target of 1,500."

### Alert and signal design

An alert on an analytical surface is a KPI card in an abnormal state — the primary value has crossed a threshold that requires attention. Alert design decisions:
- **Threshold definition:** what value or change rate triggers an alert? Name the threshold explicitly in the design brief; don't leave it to implementation.
- **Alert severity levels:** at minimum, distinguish Warning (attention warranted) from Critical (action required). Design each level as a distinct visual state (color + icon + text label).
- **Alert routing:** does the alert appear only on the dashboard, or does it also surface in a notification channel (email, in-app notification, mobile push)? The routing decision is a design-phase decision, not an ops decision.

### Drill-down affordance

Every Tier 1 KPI that a user might want to investigate further needs a consistent drill-down affordance — the interaction that takes the user from the status signal to the diagnostic detail:
- **Affordance form:** a clickable/tappable card, a "View details" link, or a selected-state that opens a panel. Name one — inconsistent drill-down affordances across a dashboard teach the user nothing about what is interactive.
- **Drill-down destination:** names where the user goes (Tier 2 diagnostic widget, detail page, filtered data table). The destination is part of the drill-down design — "show more" without a destination is incomplete.
- **Back path:** the user returns to the Tier 1 overview without losing their filter context. Breadcrumb or back affordance is required; relying on the browser back button is not sufficient when filter state is involved.

**Reference:** `analytical-design` covers the full widget hierarchy and spatial layout grammar for dashboard IA. The patterns in this section complement that IA by specifying the behavioral layer of individual widgets.
