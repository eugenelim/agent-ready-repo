# Verification ledger: Related intents field

## Owner decisions at the assumption checkpoint — 2026-10-10

Taken by eugenelim, the spec owner, before the spec body was written ("all as recommended"). They settle points that FEAT-0002 delivery decision 4 leaves open or words loosely, and the spec and plan cite this record.

1. **Target liveness.** A valid target is any non-tombstone intent, whatever its `Status:`, `Superseded` included. Decision 4's "as it already checks `Superseded by:`" names the kind of check — a corpus-scoped resolution in the intent corpus lint — not that check's exclusion of `Superseded` targets, which exists only because supersession resolves in one hop.
2. **Kind match.** The lint also refuses an item whose prefix differs from the target's kind, so a lint-clean corpus shows no refused related edge in the navigator.
3. **Refusal states.** The navigator reuses the slice 1 states and adds `self_reference` to their closed set, for this field only.
4. **Trust class.** Related edges carry `pointer_checked`, because only typed values are admitted and a shipped `core` check governs the field.
5. **Display.** `record` shows both ends in two lists; `tree` JSON and text show them; `search`, `ancestors`, and `outstanding` are unchanged; related entries count toward the 400-edge result limit.
6. **Navigator contract.** The `intent-navigation` spec body stays unchanged; its header gains an `Amended in part by:` pointer.
7. **Versions.** `core` stays 3.1.0 and this slice's bullets fold into `[core][3.1.0]`, setting aside `packs/AGENTS.md`'s "Do not borrow an unreleased version" for this slice as the owner did for slice 2. `product-engineering` bumps 0.13.24 → 0.13.25 through the integration branch.
8. **Evaluations.** One related-intents positive prompt is added to `navigate-intents/evals/eval_queries.json`; no activation run is claimed.
9. **No-reconciler pin.** A source scan over `packs/core/.apm/` Python files, plus a `close-work` verdict-equality fixture.

## Owner ruling on the spec-stage adversarial adjudication — 2026-10-10

The round 3 adjudication (local-only, non-durable evidence: `.context/reviews/7f4ee554-13ab-4692-8c7e-5cfd7fab5e58/3-pre-execute-adversarial-reviewer-adjudication.md`, sha256 `26a45d798d3e9e45e719828a3a46ec120f2e5ccbaa4c79be9a41cfa9bde8738a`) ruled on every finding but carried the indeterminate stop line with an empty indeterminate audit, so the classifier refused it as `indeterminate-present`. eugenelim, the spec owner, ruled that its sustained and refuted findings stand as written. The round 1 adjudication, refused on the same ground, reached the same substance. Repairs proceed from the round 3 sustained findings and the round 1 spec-mode shaping findings.

## Real-corpus lint run — 2026-10-10

Command, run from each checkout: `python3 packs/core/.apm/skills/work-intake/scripts/intent_corpus_lint.py --dir docs/product/intents --root .`

| Checkout | Commit | Exit code | Violations | Summary line |
| --- | --- | --- | --- | --- |
| Base | `3584b0a6f` (base copy of the script over a base worktree) | 0 | 0 | `clean — 182 entries, 168 live, 14 tombstone, 0 unreadable` |
| This slice | `4cbf4816c` plus the uncommitted T5 edits | 0 | 0 | `clean — 182 entries, 168 live, 14 tombstone, 0 unreadable` |

The two outputs are identical line for line (169 lines each, a `diff` shows no difference). No intent in the corpus carries a `Related intents:` field, so the new rule adds no violation, as expected.
