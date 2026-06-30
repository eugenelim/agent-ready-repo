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
