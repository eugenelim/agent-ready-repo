# Case: Judgment dominated
Source: docs/specs/cooling-untrusted-input-refusals/notes/adjudication.md
Baseline: docs/specs/finding-response-scoring/cases/judgment-dominated.baseline.md

- F1 — `validate_payload`, `compute_review_on`, and `is_due` catch `ZoneInfoNotFoundError` and `ValueError` but not the `OSError` raised by an over-long `timezone`, so a reachable public untrusted-input path can escape with a host path and errno instead of returning AC5's `unknown-timezone`, while the schema's 255-character bound remains unenforced.
- F2 — The spec's Follow-ons register cites pre-change line numbers, and three of its seven anchors name a different function than the surrounding prose does.
- F3 — `plan.md` cites eight `cooling.py` line numbers that have all drifted from the code they point at.
- F4 — The `_close_work()` follow-on asserts that `enrol` wraps the dependency, which is false: `_resolve_destination` is called at `:692` while `enrol`'s `try` opens at `:695`, so a shipped document makes a false statement about shipped code.
- F5 — `_resolve_destination`'s own `_close_work()` reach is a fifth uncaught path, and the Follow-ons register denies it while enumerating four.
- F6 — Line-number citations in this spec have gone stale under an insertion three separate times, so the citation style itself, rather than any individual anchor, is what keeps failing.
