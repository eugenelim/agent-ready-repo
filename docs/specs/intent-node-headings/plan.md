# Plan: Intent node headings

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py` (`_first_h1_heading`, the brief and spec node builders in `derive`); `navigate_intents.py` `_build_outstanding_items`; the byte-identity assertion in `packs/core/tests/pack/test_intent_delivery_relations_copies.py`; the preamble boundary in `_preamble_visible` and `_visible_line`; the node-heading test precedent `test_derive_intent_node_records_first_h1_heading` in `test_derivation_contract.py`.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md`. A genuine artifact error
> follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material.

## Approach

One change to the shared heading helper and the two node builders that lack it, one field added to `outstanding` items, and the release bookkeeping. Follows RFC-0105 (derived, never persisted) and RFC-0108 D1 rule 3 (names lead).

## Constraints

- Standard library only (ADR-0074); no new file under `scripts/`.
- Both `intent_graph.py` copies stay byte-identical; `test_intent_delivery_relations_copies.py` already enforces it.
- The heading comes from bytes the builders already hold, so the derivation's read count and limits do not change.

## Construction tests

Each task's `Tests:` names the suite and seam. All run with `python3 -m pytest packs/core/tests/skills/navigate-intents packs/core/tests/skills/close-work packs/core/tests/pack/test_intent_delivery_relations_copies.py -q`.

## Durable-output map

| Spec durable output | Task |
| --- | --- |
| Interface compatibility (SKILL.md `outstanding` paragraph and `search` `text` comment) | T3 |
| Release history (changelog entry) | T3 |
| Current product truth (`intent-navigation` amended-by line) | T3 |

## Design (LLD)

### Design decisions

Owned by T1, except the `outstanding` field (T2).


- **One boundary, shared with the preamble reader.** `_first_h1_heading` walks lines through `_visible_line`, the comment-hiding step `_preamble_visible` uses, and stops where `_preamble_visible` stops. One boundary rule means the shipped `intent-navigation` AC-0002 (bytes below the first `## ` change nothing) holds for headings too. On 2026-10-12 a read-only scan of every intent, brief and spec, fixtures included, found no file whose heading changes under the bounded rule. Code fences are not hidden, matching the preamble reader.
- **Raw text.** The heading keeps any "Spec:", "Brief:" or "Intent:" label. The view hides it; the owner chose this on 2026-10-12, so intent search and stored intent headings stay as they are.
- **`close-work` is unaffected beyond the copy.** It never reads `heading`, so its verdicts cannot change; no verdict-comparison run is needed.

### Data & schema

Owned by T1 and T2.


- Brief and spec nodes gain `heading: str`, as intent nodes already have.
- `outstanding` items gain `heading: str`, copied from `node_by_id[item_id]["heading"]`.

### Interfaces & contracts

Owned by T2.


The query JSON gains the two additive fields above. The export payload's `nodes` already mirror the derivation, so the export carries brief and spec headings with no export code change.

### Failure, edge cases & resilience

Owned by T1.


- A file with no title line above its first `## `: `heading` is the empty string.
- Control characters and long titles pass through unchanged, as for intents today; the view's existing display escape handles them.

## Tasks

### T1: Bounded heading rule and brief/spec headings

- **Implements:** AC-0001, AC-0002, AC-0004
- **Mode:** TDD
- **Depends on:** none
- **Touches:** `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py`, `packs/core/.apm/skills/close-work/scripts/intent_graph.py`, `packs/core/tests/skills/navigate-intents/test_derivation_contract.py`
- **Tests:**
  - AC-0001, AC-0002: new tests in `test_derivation_contract.py` drive `ig.derive` over a `tmp_path` corpus written in the test. It holds:
    - a spec titled `# Spec: Alpha` and a brief titled `# Brief: Beta`;
    - a spec with no title line;
    - an intent whose only `# ` line sits below a `## ` line;
    - a spec whose only `# ` line is inside an HTML comment;
    - a brief whose `## ` boundary line begins with a closed comment (`<!-- x -->## Outcome`) and that has a `# ` line below it.
  - They assert the labelled headings, and `""` for the other four. The last case fails if the heading boundary drifts from the preamble reader's.
  - AC-0004: the byte-identity assertion in `test_intent_delivery_relations_copies.py` passes.
- **Done when:** the new tests and that assertion pass.

### T2: Headings on outstanding items

- **Implements:** AC-0003
- **Mode:** TDD
- **Depends on:** T1
- **Touches:** `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py`, `packs/core/tests/skills/navigate-intents/test_outstanding.py`
- **Tests:**
  - AC-0003: a new test in `test_outstanding.py` runs the `outstanding` operation over the `mixed` fixture and checks both halves of the criterion.
- **Done when:** the new test and the existing outstanding suite pass.

### T3: Release bookkeeping

- **Implements:** AC-0005; the spec's Durable Outputs
- **Mode:** Goal-based check
- **Depends on:** T2
- **Touches:**
  - `packs/core/.apm/skills/navigate-intents/SKILL.md` (the `outstanding` paragraph and the `search` `text` comment) and `evals/eval_queries.json`;
  - `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`, from 3.1.0 to 3.1.1;
  - `docs/product/changelog.md`;
  - the `docs/specs/intent-navigation/spec.md` header;
  - the self-host projections.
- **Tests:**
  - AC-0005: `python3 -c "import json;q=json.load(open('packs/core/.apm/skills/navigate-intents/evals/eval_queries.json'));assert any(e['should_trigger'] and 'title' in e['query'].lower() for e in q)"` exits 0.
  - `agentbundle catalogue self-host --root . --write` run twice leaves no diff on the second run.
  - `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` pass.
  - `make lint-ruff lint-mypy` passes.
- **Done when:** all of these commands succeed and the changelog entry exists at `## [core][3.1.1]`.

## Rollout

Ships in core 3.1.1, straight to the default branch. It is additive and reversible by revert.

## Risks

- A consumer that compares whole node objects sees a new key. No shipped consumer does: the export mirrors nodes, and `close-work` ignores the field.
- Until slice 10 ships, the current view's detail panel shows brief and spec headings with their raw labels, such as "Spec: Alpha". The owner chose raw headings on 2026-10-12; slice 10's view hides the label.

## Changelog

- 2026-10-12: drafted.
