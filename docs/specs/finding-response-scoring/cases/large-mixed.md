# Case: Large mixed
Source: docs/specs/knowledge-enquiry-scope-reachability/notes/adjudication-round-1.md
Baseline: docs/specs/finding-response-scoring/cases/large-mixed.baseline.md

- F1 — The spec's `Constrained by: none` claim is false because AC3 contradicts the accepted RFC-0077 ancestor-only scope-matching contract.
- F2 — AC4 falsely claims nested result sets: its query-independent sort followed by top-12 truncation allows a subset's top 12 to contain an entry outside its superset's top 12, although AC4's operative matching clause remains true.
- F3 — `_scope_matches` has an uncovered second caller in `_pending_from_loaded_partitions`, where changing matching semantics would also affect journal-capacity processing and couple modes governed as isolated by ADR-0082.
- F4 — The version-bump acceptance criterion omits the changelog entry required in the same pull request by repository conventions, RFC-0095, and `packs/AGENTS.local.md`.
- F5 — Plan task T4's `atoms(pre)` versus `atoms(split(pre))` assertion cannot detect a wrong splitter because both sides use the same splitter, and its set comparison hides a deduplication the sanctioned writer would refuse.
- F6 — AC9 specifies a before-and-after process step but plan task T4 names no artifact location for its record.
- F7 — The plan leaves the `.` atom's specificity undefined; its stated base reduction makes `.` specificity 1 and ranks `.`-scoped topics above every empty-base glob, contrary to the Objective.
- F8 — Plan task T4 bypasses the sanctioned `write_topic` path, including scope validation and the writer lock, even though RFC-0077 requires that path.
- F9 — The proposed migration blesses glob syntax while repairing comma-joined scopes without giving a rationale, although RFC-0077's scope grammar admits neither form.
- F10 — The spec and plan duplicate load-bearing facts, including the version-bump conclusion, the count of 30 topics, and the `enquiry_bodies=12` limit, creating repair drift across multiple sites.
- F11 — The spec retcons earlier work as though it had already occurred at `spec.md:27`, `spec.md:90-92`, and `spec.md:119`.
- F12 — The Objective's success statement that enquiry would find what a maintainer would have found by grepping by hand has no observable post-condition or derivable test.
- F13 — AC6 leaks the plan-owned mechanism phrase `reduces to an empty base` into the contract instead of using the spec's own `corpus-wide` term.
- F14 — Plan task T7 cites AC10 and AC11, but its actual acceptance criteria are AC11 and AC12.
- F15 — Plan tasks T2, T5, and T6 declare no verification mode, and T6's behavior has no Testing Strategy row from which to inherit one.
