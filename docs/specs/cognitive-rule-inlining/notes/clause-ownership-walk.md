# Clause ownership walk

The retired `.agents/rules/cognitive-load.md` carried 24 clauses. Deleting a file
that holds behavioural controls is only safe if every control survives somewhere
an agent still reads. This is the walk, so a reader can check the claim instead
of taking it.

Reproduce the source list with:

```bash
git show dac83a5af:packs/core/seeds/.agents/rules/cognitive-load.md
```

## Where each clause went

| Clauses | New owner | Why there |
| --- | --- | --- |
| The 14 rendering clauses, from "Start with the useful result" to "For common chat prose" | § Rule lookups in both `AGENTS.md` files | They are the reason for the change: inline, they reach a session without a tool call that can be skipped. |
| The 3 final-check clauses — test proof, reader-can-act, one ending | § Rule lookups in both `AGENTS.md` files | Same list, same reason. |
| "Keep each skill whole on its own" | § Rule lookups in both `AGENTS.md` files | The list already names skills as a governed surface, so it belongs with the clauses rather than in a scoped file. |
| "Prefer clear code shape and exact names"; "Add a comment only to explain intent, a hard limit, or a trade-off" | § Coding conventions in both `AGENTS.md` files | Code rules, not rendering rules. Putting them in the chat list would have made the list mean two things. |
| "Keep exact code, commands, errors, and tech terms when they matter" | The "group long lists" clause, which already lists code, diffs, errors and exact names | One clause, not two. Merging it is the prose-consolidation the spec asks for. |
| "Before adding a rule, merge rules, notes, and links that say the same thing" | `docs/AGENTS.md` § Authoring | Already owned it, in fuller wording that adds `history`. |
| "Keep a backlog item fit for a choice" | `docs/AGENTS.md` § Backlog and governance | Already owned it. |
| "Keep a scoped rule file to local changes" | `docs/AGENTS.md` § Backlog and governance, and both `AGENTS.md` headers | The docs delta names both `AGENTS.md` and `AGENTS.local.md`; the headers say to keep subtree deltas in the nearest scoped file. |
| "Put a lasting rule in one place that is easy to find" | Both `AGENTS.md` headers | Root says to keep repository-wide invariants there; the seed says it is the canonical agent context file. |

## What a mechanical check reports, and why it is not the last word

A word-overlap probe over the 24 clauses reports two as unowned: the two routed
to `docs/AGENTS.md` and the file headers, whose shipped wording differs from the
retired wording. Both are false negatives — the controls are present, the
sentences are not. That is the expected result of consolidating duplicated prose,
and it is the reason this table is written out rather than replaced by a grep.

The controls that ARE pinned mechanically, and red if deleted, are in
`tests/roster/test_cognitive_load_repository_contract.py`:
`test_the_inlined_clauses_keep_each_behavioral_control` for the inlined set and
`test_simplified_docs_delta_keeps_each_scoped_control` for the `docs/` set.
