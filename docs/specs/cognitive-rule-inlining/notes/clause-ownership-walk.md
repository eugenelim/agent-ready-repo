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
| "Before adding a rule, merge rules, notes, and links that say the same thing"; "Keep a scoped rule file to local changes"; "Put a lasting rule in one place that is easy to find" | § Rule lookups in both `AGENTS.md` files | **Corrected after review.** These first went to `docs/AGENTS.md`, which carries the same words — but under a scope that stops at `docs/`, while the retired file applied them to every file, agent rule and skill. Same words, narrower reach, is a lost control. `docs/AGENTS.md` keeps its own copy as a scoped delta. |
| "Keep a backlog item fit for a choice" | § Rule lookups in both `AGENTS.md` files | **Corrected after review round 5.** This first went to `docs/AGENTS.md` on the same reasoning that had already been wrong once: the words were there, the scope was not. The canonical backlog is root `workspace.toml`, and adopters get another at `packs/core/seeds/workspace.toml` — both outside `docs/`. The clause list already declared "backlog items" as a governed surface, so the control was missing from the one place that named it. |
| (both rows above, previously listed separately here) | — | Folded into the corrected row. The headers do say where the canonical file is, but a header is not the rule, and neither header mentions merging duplicates before adding. |

## What a mechanical check reports, and why it is not the last word

A word-overlap probe over the 24 clauses first reported two as unowned, and this
note originally dismissed both as false negatives of a strict matcher. An
independent review showed that was wrong: the words were present in
`docs/AGENTS.md`, but under a scope that stops at `docs/`, so the controls had
in fact been narrowed. The probe was pointing at something real and the prose
explained it away.

The lesson is the reason the table now records a scope for each destination, not
just a file. "Which file carries this sentence" is the easy question; "does it
still reach the same work" is the one that decides whether a control survived.

That lesson had to be learned twice. Round 4 caught three controls routed to
`docs/AGENTS.md` that the retired file applied repository-wide; round 5 caught a
fourth, routed the same way for the same reason, in a table that had just been
rewritten to warn against exactly that. Re-homing prose to the file whose
*topic* matches is the default move, and the scope question has to be asked
about each clause separately.

The controls that ARE pinned mechanically, and red if deleted, are in
`tests/roster/test_cognitive_load_repository_contract.py`:
`test_the_inlined_clauses_keep_each_behavioral_control` for the inlined set and
`test_simplified_docs_delta_keeps_each_scoped_control` for the `docs/` set.
