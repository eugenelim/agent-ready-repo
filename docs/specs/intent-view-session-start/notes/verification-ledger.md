# Verification ledger: intent view for session start

## Activation (AC-0046)

- Case added to `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json` (index 42, id `q42`, `should_trigger: true`): "Export the offline intent view so I can pick what to work on this session". The file now holds 47 queries (28 positive, 19 negative); the description is unchanged.
- Procedure as the export ledger's "Activation (AC-0067)" entry: three fresh tool-less processes in an empty directory, `claude -p --safe-mode --disable-slash-commands --tools ""`, prompt on stdin, each seeing the description of every `core` skill plus `navigate-decisions` and the query as a delimited block, one call at a time (retries allowed, none needed). Fidelity is `reported`: a description-match judgement, not the real router.
- Claude Code 2.1.296: the three runs reported `navigate-intents`, `navigate-intents`, `navigate-intents`; 0 errored runs.
- Graded with `agentbundle pack evals run --pack core --mode in-harness --reports <file>` over a reports file holding only `q42`: `[ok ] q42 should_trigger=True trigger_rate=1.00`. The other 46 queries were not re-run (the description is unchanged since the export ledger's 45/45 run), so the command's per-skill total shows them as unmeasured; only the `q42` line is evidence here.
- Result: pass, trigger rate 1.00 (3 of 3).
