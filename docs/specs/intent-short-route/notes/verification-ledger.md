# Verification ledger: intent-short-route

## 2026-10-10 — isolation probe falsifies the AC-0023 isolation method

Two headless probes ran with Claude Code 2.1.296, each a single `claude -p` call from a fresh temporary directory outside any repository. Each call asked the host to list every skill the `Skill` tool can invoke.

- **Isolated `HOME`:** `HOME` and `CLAUDE_CONFIG_DIR` pointed at an empty scratch directory. Output: `Not logged in · Please run /login`. Exit 1. Authentication does not survive this isolation, so no activation run is possible this way. This host has 51 user-scope skills under the user skill directory.
- **`--setting-sources project,local`:** `HOME` was the real one. Exit 0. Every user-scope skill was hidden. Only these 14 Claude Code built-in skills were listed:
  - `dataviz`, `update-config`, `keybindings-help`, `code-review`, `simplify`;
  - `fewer-permission-prompts`, `loop`, `schedule`, `claude-api`;
  - `workflow-authoring`, `run`, `plugin-authoring`, `init`, `security-review`.

Disposition: this settled design decision is falsified, so it goes through controlled amendment. eugenelim approved the amendment in session on 2026-10-10:

- each run isolates with `--setting-sources project,local`;
- the discoverable set is the three projected packs plus the host's built-in skills, which are identical in both worlds;
- the scratch driver wraps the existing detector, which `run_eval` accepts as an argument.

## 2026-10-10 — pre-fold classifications show today's skills misroute two cases

Eleven pre-fold classifications ran as `notes/routing-classification-evidence.md` records:

- nine matched at high confidence;
- R1, the route question, selected `intake-intent` at low confidence, where `frame-intent` was expected;
- M1, the market signal, selected `frame-situation` at medium confidence.

R1 misses because today's route menu sits in `frame-intent`'s body and its description never names route choice. Pre-fold results are fixed, so AC-0020's both-worlds pass rule cannot be met by any description change.

Disposition: this is a falsified settled decision, so it goes through controlled amendment. eugenelim approved the amendment in session on 2026-10-10:

- the pre-fold run becomes a recorded baseline only;
- the high-confidence pass rule applies to the eleven post-fold cases;
- the release notes name the pre-fold misses.

## 2026-10-10 — T1 pre-fold activation setup

- **Held-out set:** `notes/held-out-queries.json` holds 42 queries.
  - 30 are positives, 10 per verb.
  - 12 are negatives, 2 each owned by `intake-intent`, `frame-situation`, `discovery-loop`, `new-spec`, `bug-fix`, and `architect-design`.
  - None matches any of the 54 distinct queries in the three source eval files.
  - None matches any of the 11 probe prompts.
- **Projection:** `product-engineering`, `core`, and `architect` are projected separately into fresh OS temporary directories, then merged.
  - Separate projections are needed because one shared projection root sweeps the earlier packs' skills as orphans.
  - The merged directory is outside every repository, which the driver asserts.
- **Listed skills (pre-fold):** the host listed these with `--setting-sources project,local`. No user-scope skill appears.
  - All 15 `product-engineering` skills.
  - Core and `architect` skills: `adapt-to-project`, `architect-assess`, `architect-design`, `architect-diagram`, `architect-review`, `architecture-lenses-reference`, `author-brief`, `author-delivery-brief`, `bug-fix`, `close-work`, `contract-acquisition`, `conventions-check`, `explain-diff`, `init-project`, `intake-intent`, `new-spec`, `operational-safety`, `project-knowledge`, `receive-brief`, `repository-exploration`, `repository-grounding`, `security-checklists`, `security-checklists-reference`, `work-intake`, `work-loop`, and `workspace-status`.
  - The 14 host built-ins recorded above.
- **Run:** `pack_evals.run_eval` runs with a detector that adds `--setting-sources project,local`, and with 3 runs per query.
  - The driver is a scratch file outside the repository, so no runner code changed.
  - The pre-fold world is a disposable detached worktree of `HEAD`, with only the measured query files and the evals list replaced.

## 2026-10-10 — owner direction: lifecycle orientation and next-mode offers

eugenelim directed in session on 2026-10-10 two additions to the `intent` skill:

- every mode offers to progress to the next logical mode or modes;
- the skill anchors the user in how the whole intent lifecycle works, and in which part of it each mode sits.

This adds behavior to an approved contract, so it goes through controlled amendment and fresh spec and plan approval.

## 2026-10-10 — owner direction: map the review gates and offer them at the right point

On 2026-10-10, eugenelim directed in session that the lifecycle amendment also map the required reviews and offer them at the right point.

The order follows ADR-0111 and frame-intent's existing sections:
1. `shaping-reviewer` in intent mode checks well-formedness after `frame`. It is a gate.
2. `adversarial-reviewer` in intent mode then reads the assumptions before `de-risk`. It is advisory, and `de-risk` never dispatches it.
3. The downstream gates belong to `author-delivery-brief` and `new-spec`, and run after the hand-off.

This is the fourth controlled amendment.

## 2026-10-10 — T1 pre-fold activation baseline

- **Result:** `notes/activation-pre-fold.json` holds the merged `run_eval` summary.
  - Positive trigger rate: **0.70**. This is the mean `trigger_rate` of the 30 positives, each measured against its owning source.
  - False-trigger rate: **0.00**. This is the mean, over the 12 negatives, of the highest of the three per-source rates.
  - Errored runs: **0**.
- **Re-runs needed to reach zero errors:**
  - The first pass had 32 errored runs on 11 negative queries, 9 of them in the last skill measured. They match a host usage limit that was reached and then reset mid-run.
  - Those 11 queries were re-run, leaving 5 errored runs on one query: "Take a raw idea for a pet-care booking app all the way through discovery to a decision brief".
  - That query fires `discovery-loop`, which ran past the 180-second default. It was re-run with a 600-second limit, set in the scratch driver, and errored 0 times.
  - In every run it fired `discovery-loop` and no source skill.
- **Pre-fold positives below 1.0:** 9 of 30. These are 1 frame, 4 de-risk, and 5 decompose queries, mostly phrased as "split", "slice", or "cut".
- **Classification baseline:** `notes/routing-classification-evidence.md` records 9 of 11 at high confidence. R1 and M1 missed, and they are a baseline only, under AC-0020.
- **Dispatch:** T1 ran in the controller session, because it dispatches cold classification subagents, which the implementer cannot do.

## 2026-10-11 — local gates run with standalone tools

`make lint-ruff lint-mypy` calls `python3 -m ruff` and `python3 -m mypy`. This host's Python 3.14.6 has neither module installed, so make exits 1.

The same checks ran through the standalone binaries:

- `ruff check .` reports "All checks passed!".
- `mypy --config-file pyproject.toml` over the three typed packages reports "Success: no issues found in 155 source files".

This held at the end of wave 1.

## 2026-10-11 — T2 built `intent/` beside the sources

The implementer agent built `intent/`; its dispatch receipt is recorded. The three source directories are unchanged.

- **Description:** 764 characters.
- **Gates:** 95 tests passed (`packs/product-engineering/tests` plus five roster modules), and `ruff` is clean.
- **Not carried over:** frame's `## Pick a route` section did not move into `references/frame.md`, because it became `## Route mode` in `SKILL.md`. The new structure test replaces the menu assertions in `test_intent_triad_execution_wiring.py`.
- **Later retargets:** these AC-0007 assertions still pass against the sources, and are retargeted or dropped later:
  - the integration entries, in T6;
  - discovery-loop wiring, in T4;
  - the de-risk `evals.json` assertion, in T3.
- **Test runners:** pytest ran through `uv tool run --with jsonschema --with pyyaml`, and catalogue lint through `uv run --no-project`, because the host Python lacks those modules. Catalogue lint returns `ok`, with warnings only. The CAT-S004 `examples/` warning also appears on existing skills.


## 2026-10-11 — T3 eval merge

`intent/evals/` now holds the merged queries and cases. The three source skills are unchanged.

**Counts**
- Source queries: 55 (frame 19, de-risk 18, decompose 18). 54 are distinct; "Shape this idea into an intent" appears in both the de-risk and decompose files and is kept once.
- Merged file: 59 queries. Positives 41: frame 14, de-risk 14, decompose 13. Negatives 18, of which 5 are new intake-intent negatives and 13 are carried.
- Several source negatives were another folded skill's positive (for example, a de-risk query in the frame file). Owner labels follow what the query asks, so those became positives with a mode.

**New intake-intent negatives (AC-0017)**
- Add this goal to the repo as a bare-bones intent: halve onboarding time for new admins
- Log a one-sentence intent for faster invoice approval in the repository, no framing needed
- Capture the stated outcome 'customers self-serve their plan changes' as a minimal intent file
- Register this outcome as a minimum viable intent so it is tracked: lift trial conversion by 10%
- Put the outcome we agreed, fewer failed payments, into the repo as a minimal intent record

**Disjointness (AC-0023):** no merged query equals any of the 42 held-out queries or any of the 11 probe prompts in `routing-classification-evidence.md`. The closest new negative to a held-out query has a character similarity ratio of 0.54. The pack test `test_merged_queries_share_no_query_with_the_held_out_set` enforces exact disjointness.

**evals.json carry (AC-0018):** 16 cases carried, each with a `mode` key; `skill_name` is `intent`.
- frame-intent (12 cases): all carried. Case id `1` became `frame-1`. Skill names in prompt and expected text now read "`intent` (frame mode)".
- de-risk-intent (2 cases): both carried. Case `1` became `de-risk-1`. The reviewer-boundary assertion reads "In de-risk mode, declines to dispatch the reviewer".
- decompose-intent (2 cases): both carried. Case `1` became `decompose-1`.
- `evals/files/cognitive-load/ordinary-prose.md` copied to `intent/evals/files/cognitive-load/`. The case's path `evals/files/cognitive-load/ordinary-prose.md` is relative to the skill root, so it still resolves.
- Dropped: none.
- Sources stay until T9. `test_de_risk_intent_reviewer_boundary.py` now checks both the source and `intent/evals/evals.json`.

**Gates:** pytest `packs/product-engineering/tests` 66 passed; `ruff check .` clean; catalogue lint `ok`.

**Per-query owner labels** (query, owner, polarity and mode)

| Query | Owner | Polarity |
| --- | --- | --- |
| Shape this idea into an intent before we spec it | frame-intent | positive, frame |
| What's the intent behind the new referral program? | frame-intent | positive, frame |
| Frame the problem we're actually solving with notifications | frame-intent | positive, frame |
| Before we build the loyalty feature, let's get the intent down | frame-intent | positive, frame |
| Turn this rough request into a product brief | frame-intent | positive, frame |
| Help me articulate the outcome we want from the onboarding redesign | frame-intent | positive, frame |
| We have a strategy doc — frame the capability intent from it | frame-intent | positive, frame |
| Write a PRD-style intent for self-serve signup | frame-intent | positive, frame |
| What outcome and opportunity are we chasing with the new dashboard? | frame-intent | positive, frame |
| Shape a generic feature intent with output_dir configured through a repository symlink that leaves the repo | frame-intent | positive, frame |
| Test whether this bet holds before we build it | de-risk-intent | positive, de-risk |
| What's the riskiest assumption in this intent? | de-risk-intent | positive, de-risk |
| Break this intent down into shippable specs | decompose-intent | positive, decompose |
| Slice this capability into child intents | decompose-intent | positive, decompose |
| Should we validate this assumption or just build it? | de-risk-intent | positive, de-risk |
| What should this error message say? | ux-writing | negative |
| Set up a value-stream meta-repo for the program | align-value-stream | negative |
| Write the spec for the referral feature | new-spec | negative |
| Fix the broken signup redirect | bug-fix | negative |
| De-risk this intent before we commit engineering time | de-risk-intent | positive, de-risk |
| Is the assumption that users want SSO actually true? | de-risk-intent | positive, de-risk |
| What would have to be true for the marketplace bet to pay off? | de-risk-intent | positive, de-risk |
| Should we validate this with a prototype or just build it? | de-risk-intent | positive, de-risk |
| Test the bet that self-serve will cut support load | de-risk-intent | positive, de-risk |
| Name the riskiest assumption in the new pricing model | de-risk-intent | positive, de-risk |
| What's the kill condition for the AI-summary feature? | de-risk-intent | positive, de-risk |
| Is this a one-way door? Help me de-risk it before we proceed | de-risk-intent | positive, de-risk |
| Run a quick validation on whether teams will adopt the dashboard | de-risk-intent | positive, de-risk |
| Shape this idea into an intent | frame-intent | positive, frame |
| Frame the problem behind the pricing change | frame-intent | positive, frame |
| What's the intent behind the pricing change? | frame-intent | positive, frame |
| Break this de-risked intent into specs | decompose-intent | positive, decompose |
| Slice the marketplace intent into child intents | decompose-intent | positive, decompose |
| Write the spec for SSO | new-spec | negative |
| What should the empty state say? | ux-writing | negative |
| Coordinate delivery across our component repos | align-value-stream | negative |
| Diagram the marketplace architecture | architect-diagram | negative |
| Decompose this intent into child intents | decompose-intent | positive, decompose |
| Break this capability down into shippable specs | decompose-intent | positive, decompose |
| Slice the onboarding intent into deliverable pieces | decompose-intent | positive, decompose |
| What specs come out of the marketplace intent? | decompose-intent | positive, decompose |
| Push these child intents to Linear | decompose-intent | positive, decompose |
| Break this down one level — what's next under it? | decompose-intent | positive, decompose |
| Cut this intent into a spec at the leaf | decompose-intent | positive, decompose |
| Project this decomposition onto our Jira board | decompose-intent | positive, decompose |
| What's the next level down from this capability intent? | decompose-intent | positive, decompose |
| What's the intent behind onboarding? | frame-intent | positive, frame |
| Test whether this intent's bet holds | de-risk-intent | positive, de-risk |
| Is the core assumption true before we commit? | de-risk-intent | positive, de-risk |
| Set up the value-stream meta-repo for the program | align-value-stream | negative |
| Decompose this 40-page PRD we got from the client | work-intake | negative |
| Write the spec for the leaf feature | new-spec | negative |
| Fix the failing onboarding test | bug-fix | negative |
| What should this button be labeled? | ux-writing | negative |
| Add this goal to the repo as a bare-bones intent: halve onboarding time for new admins | intake-intent | negative |
| Log a one-sentence intent for faster invoice approval in the repository, no framing needed | intake-intent | negative |
| Capture the stated outcome 'customers self-serve their plan changes' as a minimal intent file | intake-intent | negative |
| Register this outcome as a minimum viable intent so it is tracked: lift trial conversion by 10% | intake-intent | negative |
| Put the outcome we agreed, fewer failed payments, into the repo as a minimal intent record | intake-intent | negative |

## 2026-10-11 — T4 discovery-loop retarget

Files changed: `discovery-loop/SKILL.md`, its `references/gate-state-machine.md`,
`requirements-crosswalk.md`, `sidecar-schema.md`, `agents/discovery-lead.md`, and
`tests/pack/test_intent_triad_execution_wiring.py`.

Gate literals, old to new: G0 `frame-intent` to `intent frame`; G1 `de-risk-intent`
to `intent de-risk` and `decompose-intent` to `intent decompose`; G3 and the product
lens `decompose-intent` to `intent decompose`. Pointer "`frame-intent`'s `## Pick a
route`" to "`intent`'s `## Route mode`". Sidecar example `produced_by` is
`"intent decompose"` (the schema types it as free text: the skill or agent that wrote it).

Description, before: "... and hands off to work-loop at G3 — with no new engine ... Do
NOT use to build a spec (use new-spec → work-loop), ...". After: "... and hands off
through work-intake at G3 — with no new engine ... (use new-spec), ...". The second
edit was needed because AC-0015 forbids naming `work-loop` anywhere in the description.

Assertions replaced: the AC5 walk literals now check the `intent` mode names; the AC13
`## When to invoke` pointer checks `intent` and `## Route mode` (was `frame-intent` and
`## Pick a route`). Added: AC-0015 (description names work-intake, not work-loop, and
is at most 1024 characters) and AC-0014 (no retired name in either surface; gate rows
name the modes). The Core-absent and recursive-decomposition clause tests already have
`intent` retargets; the originals stay until T9. The frame-intent `## Pick a route`
assertions stay until T9.

## 2026-10-11 — out-of-scope stale statements found in T4

These still say that `discovery-loop` hands off to `work-loop` at G3:

- the `discovery-loop/SKILL.md` body, at line 17;
- `agents/discovery-lead.md`: the description, line 13, and line 105.

The G3 gate table already says `work-intake`.

- **Why not fixed here:** AC-0015 covers only the description. These are skill-file edits, which the bundled-fixes rule's clause (iv) refuses.
- **Who fixes it:** `intent-longer-and-supervised-verbs`, which owns the rest of the `discovery-loop` stale-statement fixes.

## 2026-10-11 — T5 Core and package callers

**Red before the engine change** (expectations moved to `intent` in `tools/test_workspace_status.py` and `test_routing_precedence.py`, engine and SKILL.md untouched):

```
FAILED tools/test_workspace_status.py::TestWorkspaceStatusCases::test_029_ac3f_shaping_item_guard
FAILED tools/test_workspace_status.py::TestWorkspaceStatusCases::test_031_ac3f_shaping_guard_top_level_backlog
FAILED tools/test_workspace_status.py::TestWorkspaceStatusCases::test_038_f1b_untyped_backlog_not_shaping
FAILED tools/test_workspace_status.py::TestWorkspaceStatusCases::test_046_f4d_work_loop_slug_normalization
FAILED packs/core/tests/skills/work-intake/test_routing_precedence.py::test_public_precedence_routes_explicit_work_directly
5 failed, 85 passed
```

**Changed:**
- Engine: `_SHAPING_TYPE_TO_SKILL["shape"]` and both `check_shaping_guard` fallbacks now `intent`, in `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` and the byte-identical mirror `packages/agentbundle/agentbundle/_data/workspace_status_engine.py` (`cmp` clean). `strategy` stays `frame-situation`.
- `packages/agentbundle/agentbundle/workspace_mcp.py`: `dispatch_skill` is `intent`.
- Core text: `work-intake/SKILL.md` (owner list), `work-loop/SKILL.md` (guard table line), `workspace-status/SKILL.md` and `references/agentbundle-layout.md`, `init-project/SKILL.md`, `work-intake/scripts/intent_shape.py` docstring, `work-loop/scripts/lint-traceability.py` comment, `test_intent_shape.py` docstrings.
- The work-loop Step 0 contract hash pin in `tools/test_workspace_status.py` moved (name-only edit; engine updated in the same change).

**Versions:** Core 3.0.2 -> 3.0.3 (`pack.toml`, `.claude-plugin/plugin.json`); agentbundle 0.52.0 -> 0.52.1 (`version.py`, `pyproject.toml`). Not done: a changelog entry, README-pypi note, or release. `tests/roster/test_okf_catalogue_discovery.py` pins `0.52.0` and will fail until the release step moves it.

**Green after:** `tools/test_workspace_status.py` 86 passed; work-intake and workspace-status suites pass; ruff and mypy clean; catalogue lint `--deep` ok.
- Also re-pinned `workspace_status_engine.py` in `tests/roster/test_workspace_status_progressive_disclosure.py` (BACKEND_DIGESTS) to 2e74ec70...; that suite now passes.

## 2026-10-11 — T5 follow-ups

- **Pre-existing failure:**
  - **Test:** `test_loop_engine.py::test_recover_engine_state_tmp_never_tracebacks_and_deletes_only_bad_content[deep-nesting]`.
  - **Evidence:** it fails on an unmodified detached `HEAD` worktree (`/tmp/pe-t1/wt-pre`), so this slice did not cause it.
  - **Handling:** recorded as a known skip in `[backlog].open`, as `pre-existing-recover-engine-state-deep-nesting`.
- **Release coupling for T9:** `agentbundle` moved from 0.52.0 to 0.52.1. `tests/roster/test_okf_catalogue_discovery.py` pins 0.52.0 across four places:
  - `CLI_VERSION`;
  - `pyproject.toml`;
  - the `README-pypi.md` "What's new" heading;
  - the `CHANGELOG.md` heading.

  T9's AC-0029 work adds the `packages/agentbundle/CHANGELOG.md` entry, and must move that pin and heading in the same change.

## 2026-10-11 — T6 other packs and integrations

**Rewrite rule:** name-only. `frame-intent` -> `intent frame` (or `intent` where it names the consumer skill: process-mapping, align-value-stream); `de-risk-intent` -> `intent de-risk`; `decompose-intent` -> `intent decompose`; `<source>/references|assets|examples/` -> `intent/...`.

**Integration entries (AC-0013):** `core-delivery-handoff` consumers `["skill:discovery-loop", "skill:intent"]`; `core-intent-shaping-review` consumers `["skill:intent"]` (purpose text retargeted to `intent` (frame mode)); governance-extras `design-proposal-product-engineering` providers `["skill:intent"]` (`when` retargeted). product-engineering `first-value` verification/recovery retargeted to `intent`.

**Versions:** experience-design 4.1.4 -> 4.1.5; governance-extras 1.0.1 -> 1.0.2; product-strategy 0.2.7 -> 0.2.8 (`pack.toml` + `.claude-plugin/plugin.json`). product-engineering unchanged (1.0.0 in T9); Core unchanged.

**Files changed:** see `git diff --stat` for T6; tests retargeted: `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py`, `tests/roster/test_shaping_handoff_pack_surface.py`, `tests/roster/test_shaping_intake_handoff_matrix.py`; process-mapping eval assertion text. Not touched: PE pack docs (README/JOURNEY/DESIGN), `[pack.evals].skills`, discovery-lead, projections (T7/T9).

**Edited descriptions, before/after (full text).** Probe candidates (product-engineering siblings) are frozen to the `After` text per AC-0021; experience-design ones are not probe candidates.

### `packs/experience-design/.apm/skills/process-mapping/SKILL.md` (after: 670 chars)

Before:
```
description: "Use when a team asks how an internal business operation works today or should work tomorrow across actors and handoffs. Produces a SIPOC scope, swimlane map, as-is/to-be flow, and pain-and-waste register. Use `journey-mapping` for the customer's experience, `service-blueprint` to connect a journey to backstage support, and `user-flow` for screens. Operating or product strategy belongs upstream; shaping an automation bet belongs to `frame-intent`; implementing workflow software belongs to engineering. Triggers on \"map our monthly close process as it works today\", \"show the handoffs in our supplier invoice process\", \"design the to-be process for customer refunds\"."
```
After:
```
description: "Use when a team asks how an internal business operation works today or should work tomorrow across actors and handoffs. Produces a SIPOC scope, swimlane map, as-is/to-be flow, and pain-and-waste register. Use `journey-mapping` for the customer's experience, `service-blueprint` to connect a journey to backstage support, and `user-flow` for screens. Operating or product strategy belongs upstream; shaping an automation bet belongs to `intent`; implementing workflow software belongs to engineering. Triggers on \"map our monthly close process as it works today\", \"show the handoffs in our supplier invoice process\", \"design the to-be process for customer refunds\"."
```

### `packs/experience-design/.apm/skills/service-blueprint/SKILL.md` (after: 752 chars)

Before:
```
description: "Use when someone asks what people, services, and systems support each step of an existing customer journey. Produces a service blueprint across evidence of service, frontstage, line of visibility, backstage, and support. Use `journey-mapping` to discover the customer path first, `user-flow` for screen transitions, and `process-mapping` for an internal operation without the customer lens. Service strategy belongs upstream; framing the initiative belongs to `frame-intent`; implementing service calls or frontend behavior belongs to engineering. Triggers on \"blueprint the services behind our account-opening journey\", \"map what happens backstage at each checkout step\", \"connect this customer journey to the teams and systems that support it\"."
```
After:
```
description: "Use when someone asks what people, services, and systems support each step of an existing customer journey. Produces a service blueprint across evidence of service, frontstage, line of visibility, backstage, and support. Use `journey-mapping` to discover the customer path first, `user-flow` for screen transitions, and `process-mapping` for an internal operation without the customer lens. Service strategy belongs upstream; framing the initiative belongs to `intent frame`; implementing service calls or frontend behavior belongs to engineering. Triggers on \"blueprint the services behind our account-opening journey\", \"map what happens backstage at each checkout step\", \"connect this customer journey to the teams and systems that support it\"."
```

### `packs/experience-design/.apm/skills/interaction-design/SKILL.md` (after: 749 chars)

Before:
```
description: "Use when someone asks how one screen or component should respond to actions, validate input, transition, recover, or feel in use. Produces behavioral and state specifications for the interaction. Use `information-architecture` for hierarchy, `user-flow` for cross-screen routes, and `creative-direction` for visual mood; `ux-writing` owns the strings shown in those states. Product strategy is upstream; framing and scoping the feature belongs to `frame-intent`; implementing the state machine, motion, or component code belongs to `frontend-engineering`. Triggers on \"design how this search component validates, loads, and recovers\", \"map the state transitions inside this checkout form\", \"spec the feedback and motion for this async button\"."
```
After:
```
description: "Use when someone asks how one screen or component should respond to actions, validate input, transition, recover, or feel in use. Produces behavioral and state specifications for the interaction. Use `information-architecture` for hierarchy, `user-flow` for cross-screen routes, and `creative-direction` for visual mood; `ux-writing` owns the strings shown in those states. Product strategy is upstream; framing and scoping the feature belongs to `intent frame`; implementing the state machine, motion, or component code belongs to `frontend-engineering`. Triggers on \"design how this search component validates, loads, and recovers\", \"map the state transitions inside this checkout form\", \"spec the feedback and motion for this async button\"."
```

### `packs/experience-design/.apm/skills/design-review/SKILL.md` (after: 741 chars)

Before:
```
description: "Use when someone asks to critique an existing rendered screen, flow, or mockup for usability, quality-floor, clarity, and aesthetic-fit problems. Produces a severity-rated findings list grounded in the actual artifact. Use `creative-direction` to name a new visual direction, `information-architecture` to design hierarchy, and `design-system` to derive tokens. Reviewing product strategy or choosing a bet is upstream strategy work; framing the work belongs to `frame-intent`; reviewing code defects or implementation quality belongs to frontend engineering. Triggers on \"review this checkout flow for usability problems\", \"critique this landing page mockup against our design principles\", \"what's wrong with this rendered dashboard\"."
```
After:
```
description: "Use when someone asks to critique an existing rendered screen, flow, or mockup for usability, quality-floor, clarity, and aesthetic-fit problems. Produces a severity-rated findings list grounded in the actual artifact. Use `creative-direction` to name a new visual direction, `information-architecture` to design hierarchy, and `design-system` to derive tokens. Reviewing product strategy or choosing a bet is upstream strategy work; framing the work belongs to `intent frame`; reviewing code defects or implementation quality belongs to frontend engineering. Triggers on \"review this checkout flow for usability problems\", \"critique this landing page mockup against our design principles\", \"what's wrong with this rendered dashboard\"."
```

### `packs/experience-design/.apm/skills/user-flow/SKILL.md` (after: 721 chars)

Before:
```
description: "Use when an approved customer journey needs to become screens, transitions, failure paths, and navigation routes. Produces a complete screen sequence plus one self-contained brief per screen and a whole-flow walk-through. Use `journey-mapping` to understand the journey first, `interaction-design` for behavior within one screen, and `service-blueprint` for backing services. Adoption strategy belongs upstream; appetite and scope belong to `frame-intent`; implementing routes and screens belongs to `frontend-engineering`. Triggers on \"turn this account-recovery journey into screens and transitions\", \"map the error paths across our checkout screens\", \"create a screen flow and brief for every onboarding screen\"."
```
After:
```
description: "Use when an approved customer journey needs to become screens, transitions, failure paths, and navigation routes. Produces a complete screen sequence plus one self-contained brief per screen and a whole-flow walk-through. Use `journey-mapping` to understand the journey first, `interaction-design` for behavior within one screen, and `service-blueprint` for backing services. Adoption strategy belongs upstream; appetite and scope belong to `intent frame`; implementing routes and screens belongs to `frontend-engineering`. Triggers on \"turn this account-recovery journey into screens and transitions\", \"map the error paths across our checkout screens\", \"create a screen flow and brief for every onboarding screen\"."
```

### `packs/experience-design/.apm/skills/design-system/SKILL.md` (after: 983 chars)

Before:
```
description: "Use when an approved aesthetic direction or an existing product system exists and someone asks what the design system should actually be — the typography, color, spacing, shape, depth and motion decisions a build can implement. Produces a project-specific system: relationships plus the concrete values that make them executable, derived from the approved direction, the incumbent system and the platform floor. Use `creative-direction` to establish the direction first, `information-architecture` for page hierarchy, and `design-review` to evaluate an existing surface. Product differentiation belongs to product strategy; framing a design-system initiative belongs to `frame-intent`; writing component code belongs to `frontend-engineering`. Triggers on \"turn our approved direction into a real design system\", \"what should our type, color and spacing actually be\", \"extend our existing tokens for this new surface\", \"our spacing is too dense — fix it at the system level\"."
```
After:
```
description: "Use when an approved aesthetic direction or an existing product system exists and someone asks what the design system should actually be — the typography, color, spacing, shape, depth and motion decisions a build can implement. Produces a project-specific system: relationships plus the concrete values that make them executable, derived from the approved direction, the incumbent system and the platform floor. Use `creative-direction` to establish the direction first, `information-architecture` for page hierarchy, and `design-review` to evaluate an existing surface. Product differentiation belongs to product strategy; framing a design-system initiative belongs to `intent frame`; writing component code belongs to `frontend-engineering`. Triggers on \"turn our approved direction into a real design system\", \"what should our type, color and spacing actually be\", \"extend our existing tokens for this new surface\", \"our spacing is too dense — fix it at the system level\"."
```

### `packs/experience-design/.apm/skills/creative-direction/SKILL.md` (after: 1009 chars)

Before:
```
description: "Use when someone says a digital surface should feel premium, calm, playful, or otherwise has a vibe but no shared visual direction. Also use when refining or amending an existing direction, or when inheriting it into a new section, component, or feature. Produces ranked aesthetic goals and, when due, a `<output_dir>/direction/<slug>.md` record grounded in referents and arbitration rules. Use `design-system` after the direction to derive tokens, `information-architecture` for page hierarchy, and `design-review` to critique existing work. Product positioning belongs to product strategy; framing or scoping the bet belongs to `frame-intent`; implementing colors, type, or components belongs to `frontend-engineering`. Triggers on \"turn this calm, premium vibe into a shared visual direction\", \"name and rank the aesthetic goals for our mobile app\", \"ground this visual mood before we choose colors and type\", \"refine the existing direction to be bolder\", \"amend the direction doc to be quieter\"."
```
After:
```
description: "Use when someone says a digital surface should feel premium, calm, playful, or otherwise has a vibe but no shared visual direction. Also use when refining or amending an existing direction, or when inheriting it into a new section, component, or feature. Produces ranked aesthetic goals and, when due, a `<output_dir>/direction/<slug>.md` record grounded in referents and arbitration rules. Use `design-system` after the direction to derive tokens, `information-architecture` for page hierarchy, and `design-review` to critique existing work. Product positioning belongs to product strategy; framing or scoping the bet belongs to `intent frame`; implementing colors, type, or components belongs to `frontend-engineering`. Triggers on \"turn this calm, premium vibe into a shared visual direction\", \"name and rank the aesthetic goals for our mobile app\", \"ground this visual mood before we choose colors and type\", \"refine the existing direction to be bolder\", \"amend the direction doc to be quieter\"."
```

### `packs/product-engineering/.apm/skills/place-bet/SKILL.md` (after: 415 chars)

Before:
```
description: Step 5 of the PE six-step shaping sequence — the bet-commitment gate. Reads a diverge-solutions artifact if present (offers to run it first if absent); accepts options from any source; folds in validation-notes when available; emits bet.md with the full betting table anchoring map-capabilities. Do NOT use to generate options (use diverge-solutions or explore-options) or validate assumptions (use de-risk-intent).
```
After:
```
description: Step 5 of the PE six-step shaping sequence — the bet-commitment gate. Reads a diverge-solutions artifact if present (offers to run it first if absent); accepts options from any source; folds in validation-notes when available; emits bet.md with the full betting table anchoring map-capabilities. Do NOT use to generate options (use diverge-solutions or explore-options) or validate assumptions (use intent de-risk).
```

### `packs/product-engineering/.apm/skills/explore-options/SKILL.md` (after: 643 chars)

Before:
```
description: Use to generate multiple candidate product shapes before the discovery loop converges on one — the divergence stage that guards against myopic-greedy commitment. Triggers on "give me candidate product shapes", "diverge on the product shape", "what are the options before we commit", "explore alternatives for X", "don't converge yet". Generates N candidates across altitude × mechanic, each with its riskiest assumption, then frames an explicit compare-and-choose. Do NOT use to break down a chosen approach (use `decompose-intent`), to critique one produced artifact (use `devils-advocate`), or to converge (that is the discovery loop's job).
```
After:
```
description: Use to generate multiple candidate product shapes before the discovery loop converges on one — the divergence stage that guards against myopic-greedy commitment. Triggers on "give me candidate product shapes", "diverge on the product shape", "what are the options before we commit", "explore alternatives for X", "don't converge yet". Generates N candidates across altitude × mechanic, each with its riskiest assumption, then frames an explicit compare-and-choose. Do NOT use to break down a chosen approach (use `intent decompose`), to critique one produced artifact (use `devils-advocate`), or to converge (that is the discovery loop's job).
```

### `packs/product-engineering/.apm/skills/plan-validation/SKILL.md` (after: 666 chars)

Before:
```
description: Use to turn a converged product's load-bearing assumptions into a validation plan — and to scaffold the primary-research instruments that would test them. Triggers on "plan the validation", "how do we validate these assumptions", "turn assumptions into a validation plan", "scaffold an interview guide / usability test", "what would confirm this". Produces assumption → kill-condition → real-world-activity hooks and the instrument scaffolds (interview guide, usability-test plan, transcript-synthesis frame). Do NOT use to run the sessions (out of charter — a human runs them), to test a single bet (use `de-risk-intent`), or to converge (the discovery loop's job).
```
After:
```
description: Use to turn a converged product's load-bearing assumptions into a validation plan — and to scaffold the primary-research instruments that would test them. Triggers on "plan the validation", "how do we validate these assumptions", "turn assumptions into a validation plan", "scaffold an interview guide / usability test", "what would confirm this". Produces assumption → kill-condition → real-world-activity hooks and the instrument scaffolds (interview guide, usability-test plan, transcript-synthesis frame). Do NOT use to run the sessions (out of charter — a human runs them), to test a single bet (use `intent de-risk`), or to converge (the discovery loop's job).
```

### `packs/product-engineering/.apm/skills/frame-domain/SKILL.md` (after: 801 chars)

Before:
```
description: Use when grounding a product in the real-world activity it serves and bounding its MVP before any screen, service, or architecture is drawn — at the G1.5 Domain & MVP point of the discovery loop, or standalone. Triggers on "frame the domain", "how is this activity really done", "ground this before we design", "what's in/out of the MVP", "draw the scope boundary", "is this scope creep". Produces two typed artifacts from one research-grounded pass — Domain Framing (real-world-activity grounding + best practice + naive-failure modes, plus a brownfield current-system half) and Scope Boundary (the MVP out-of-scope register). Do NOT use to shape the intent behind the work (use `frame-intent`), to test whether a bet holds (use `de-risk-intent`), or to break an intent down (use `decompose-intent`).
```
After:
```
description: Use when grounding a product in the real-world activity it serves and bounding its MVP before any screen, service, or architecture is drawn — at the G1.5 Domain & MVP point of the discovery loop, or standalone. Triggers on "frame the domain", "how is this activity really done", "ground this before we design", "what's in/out of the MVP", "draw the scope boundary", "is this scope creep". Produces two typed artifacts from one research-grounded pass — Domain Framing (real-world-activity grounding + best practice + naive-failure modes, plus a brownfield current-system half) and Scope Boundary (the MVP out-of-scope register). Do NOT use to shape the intent behind the work (use `intent frame`), to test whether a bet holds (use `intent de-risk`), or to break an intent down (use `intent decompose`).
```

### `packs/product-engineering/.apm/skills/map-capabilities/SKILL.md` (after: 560 chars)

Before:
```
description: Step 6 (terminal) of the PE six-step shaping sequence. Translates a committed bet into a Capability Map — L1 domain organisation, Wardley × strategic-criticality annotation, Build/Buy/Partner/Adopt disposition, and a Build-only suggested build sequence anchoring M3–M6 spec-writing. Run after `place-bet`. Triggers on "map our capabilities", "what do we need to build", "what's our build/buy split", "capability areas for this bet". Do NOT use for a single feature (use `frame-intent`) or to author a brief (use `lean-canvas` / `author-delivery-brief create`).
```
After:
```
description: Step 6 (terminal) of the PE six-step shaping sequence. Translates a committed bet into a Capability Map — L1 domain organisation, Wardley × strategic-criticality annotation, Build/Buy/Partner/Adopt disposition, and a Build-only suggested build sequence anchoring M3–M6 spec-writing. Run after `place-bet`. Triggers on "map our capabilities", "what do we need to build", "what's our build/buy split", "capability areas for this bet". Do NOT use for a single feature (use `intent frame`) or to author a brief (use `lean-canvas` / `author-delivery-brief create`).
```

### `packs/product-engineering/.apm/skills/frame-situation/SKILL.md` (after: 617 chars)

Before:
```
description: Use when holding a raw signal (market observation, OKR gap, user pain pattern, engineering finding, competitive signal) at initiative or capability level — turning it into a typed finding, a Wardley capability maturity assessment, and an anchor into the PE six-step shaping sequence. Triggers on "frame this situation", "what do we do with this signal", "is this an opportunity or a risk", "where should we start", "map this to the shaping sequence". Do NOT use for a feature-scoped request (use `frame-intent`), testing an assumption (use `de-risk-intent`), or breaking down a shaped intent (use `decompose-intent`).
```
After:
```
description: Use when holding a raw signal (market observation, OKR gap, user pain pattern, engineering finding, competitive signal) at initiative or capability level — turning it into a typed finding, a Wardley capability maturity assessment, and an anchor into the PE six-step shaping sequence. Triggers on "frame this situation", "what do we do with this signal", "is this an opportunity or a risk", "where should we start", "map this to the shaping sequence". Do NOT use for a feature-scoped request (use `intent frame`), testing an assumption (use `intent de-risk`), or breaking down a shaped intent (use `intent decompose`).
```

### `packs/product-engineering/.apm/skills/lean-canvas/SKILL.md` (after: 414 chars)

Before:
```
description: Use when a product engineer or PM is ready to produce an initiative brief through an adapted Lean Canvas elicitation — after the PE shaping sequence or as a standalone exercise. Triggers on "lean canvas", "initiative brief", "canvas this initiative", "author initiative brief". Do NOT use for a feature-scoped request (use `frame-intent`) or for individual shaping steps (use `frame-situation`, `place-bet`, etc.).
```
After:
```
description: Use when a product engineer or PM is ready to produce an initiative brief through an adapted Lean Canvas elicitation — after the PE shaping sequence or as a standalone exercise. Triggers on "lean canvas", "initiative brief", "canvas this initiative", "author initiative brief". Do NOT use for a feature-scoped request (use `intent frame`) or for individual shaping steps (use `frame-situation`, `place-bet`, etc.).
```

### `packs/product-engineering/.apm/skills/ux-writing/SKILL.md` (after: 995 chars)

Before:
```
description: Use when shaping the actual words a user reads in a product's UI — characterizing the UI copy voice (how the brand register applies to UI states), writing recurring UI-state microcopy (error, empty, button, label), or reviewing copy before it ships. Triggers on "what should this error say", "write the empty-state copy", "name this button", "characterize our product's UI copy voice", "make this microcopy blame-free", "review this copy". Characterizes voice along a few axes, writes each UI state from a blame-free + actionable formula, and runs a content checklist. When a per-screen state matrix from `user-flow` is present, writes copy per screen × state keyed to the matrix; when absent, behaves as today. Do NOT use to frame the intent behind the feature (use `frame-intent`), to make visual or layout design decisions, to write documentation prose (use `author-product-docs` if installed), or to establish the brand-level copy register (use `content-design`'s brand-level register mode).
```
After:
```
description: Use when shaping the actual words a user reads in a product's UI — characterizing the UI copy voice (how the brand register applies to UI states), writing recurring UI-state microcopy (error, empty, button, label), or reviewing copy before it ships. Triggers on "what should this error say", "write the empty-state copy", "name this button", "characterize our product's UI copy voice", "make this microcopy blame-free", "review this copy". Characterizes voice along a few axes, writes each UI state from a blame-free + actionable formula, and runs a content checklist. When a per-screen state matrix from `user-flow` is present, writes copy per screen × state keyed to the matrix; when absent, behaves as today. Do NOT use to frame the intent behind the feature (use `intent frame`), to make visual or layout design decisions, to write documentation prose (use `author-product-docs` if installed), or to establish the brand-level copy register (use `content-design`'s brand-level register mode).
```

### `packs/product-engineering/.apm/skills/align-value-stream/SKILL.md` (after: 758 chars)

Before:
```
description: Use at business-unit scale to stand up and keep current a value-stream meta-repo — a coordinating repo with no app code that holds the cross-component artifacts a polyrepo has nowhere else to put (the federated Backstage catalog, the shared-contract authority, the C4/bounded-context architecture, and the cross-component delivery rollup). Triggers on "set up a value-stream meta-repo", "coordinate across component repos", "stand up the cross-component catalog", "where does the shared contract live", "is this feature delivered across all the repos". Reads the per-component slices that decompose-intent produces and rolls up their delivery. Do NOT use at app scale (use decompose-intent — the leaf is one repo's brief) or to author an intent (use frame-intent).
```
After:
```
description: Use at business-unit scale to stand up and keep current a value-stream meta-repo — a coordinating repo with no app code that holds the cross-component artifacts a polyrepo has nowhere else to put (the federated Backstage catalog, the shared-contract authority, the C4/bounded-context architecture, and the cross-component delivery rollup). Triggers on "set up a value-stream meta-repo", "coordinate across component repos", "stand up the cross-component catalog", "where does the shared contract live", "is this feature delivered across all the repos". Reads the per-component slices that intent decompose produces and rolls up their delivery. Do NOT use at app scale (use intent decompose — the leaf is one repo's brief) or to author an intent (use intent).
```

## 2026-10-11 — wave 3 gates (T3–T6)

All suites passed, with standalone `ruff` and `mypy` and pytest through `uv tool run`:

| Check | Result |
| --- | --- |
| `ruff check .` | clean |
| `mypy` | 155 files, no issues |
| governance-extras `navigate-decisions` | 244 passed |
| `packs/product-engineering/tests` | 68 passed |
| `packs/experience-design/tests` | 31 passed |
| `tools/test_workspace_status.py` | 86 passed |
| `packs/core/tests/skills/work-intake` | 879 passed |
| `packs/core/tests/skills/workspace-status` | 277 passed, 1 skipped |
| six roster modules | 53 passed |

## 2026-10-11 — T7 sweep

### AC-0010 search

```bash
git grep --untracked -n -E 'frame-intent|de-risk-intent|decompose-intent' -- \
  packs guides web/src tools tests packages contracts workspace.toml \
  docs/architecture docs/product/journeys docs/guides \
  docs/product/workspace-toml-deps.md AGENTS.md ARCHITECTURE.md README.md docs/CHARTER.md \
  ':!packs/product-engineering/.apm/skills/frame-intent' \
  ':!packs/product-engineering/.apm/skills/de-risk-intent' \
  ':!packs/product-engineering/.apm/skills/decompose-intent' \
  ':!packs/core/tests/skills/work-loop/fixtures/corpus' \
  ':!packs/agent-skill-engineering/tests/fixtures/skill-census.json'
```

Output, 25 lines, every one an allowed match:

- `packs/product-engineering/pack.toml:43` — the `[pack.evals].skills` line. T9 clears it.
- Five `RETIRED_SHAPING_SKILLS` constants, three lines each, in `packs/product-engineering/tests/pack/{test_de_risk_intent_reviewer_boundary,test_frame_intent_experience_handoff,test_frame_intent_shaping_review,test_intent_skill_structure,test_intent_triad_execution_wiring}.py`, plus one each in `tests/roster/test_rfc0099_activation_coverage.py` and `tools/test_live_demo_guide.py`.
- `workspace.toml:421`, `:2194`, `:2478` — directory names of two Shipped specs, `m2-frame-intent-jtbd` and `frame-intent-escape-verdicts`.

### Files changed

- **Tools:** `render-lifecycle-graphics.py` (route lists now `intent frame`, `intent de-risk`, `intent decompose`); `add-rendering-directives.py` (the three retired entries dropped); `lint-knowledge-surface-parity.py` and `repo/check_contract_drift.py` (pinned paths now `intent/references/...`); their tests `test-check-contract-drift.py`, `test-lint-knowledge-surface-parity.py`, `test_live_demo_guide.py`; a comment in `test_workspace_status.py`.
- **Tests:** the four pack tests and `test_intent_skill_structure.py` read the source directories through `RETIRED_SHAPING_SKILLS`; `tests/roster/test_rfc0099_activation_coverage.py`, `test_intent_template_shape_conformance.py`, `test_shaping_handoff_pack_surface.py`.
- **Eval data:** `intent/evals/eval_queries.json` owner labels `frame-intent`, `de-risk-intent`, `decompose-intent` are now `intent frame`, `intent de-risk`, `intent decompose`. The matching test accepts the new labels.
- **Guides:** 28 files under `guides/`, including the regenerated `the-operating-model-full-map.svg`.
- **Site and pack docs:** `web/src/content/packs/product-engineering.md`, `web/src/content/journeys/product-engineering.md` (re-synced from `JOURNEY.md` by `build-site.py --journeys-only`), and `packs/product-engineering/{README,JOURNEY,DESIGN}.md`. JOURNEY's three skill entries became one `intent` entry, because `lint-pack-journeys` requires each name to be a real skill directory.
- **Docs:** `docs/architecture/lifecycle-flow.md`, `docs/product/journeys/{engineer-adopts-coordination,product-engineer-shapes-initiative,team-evaluates-and-adopts}.md`, `docs/product/workspace-toml-deps.md`, and one `workspace.toml` comment.
- **AC-0027:** `the-operating-model.md` names `intent frame`, `intent de-risk`, and `intent decompose` for the short route.
- **AC-0028:** `frame-the-intent.md` now says the discovery loop starts from a raw idea, not an approved intent. The table row, the prompt, and a new opening sentence all say so.

### Tests replaced or dropped (AC-0007)

- None dropped at T7. T9's replacements and removals are listed in § T9 test changes (AC-0007) below.
- `test_rfc0099_activation_coverage.py` R2: `expected_route` still equals the frozen RFC-0099 cell, built from `RETIRED_SHAPING_SKILLS[0]`. RFC-0099 is not edited. R2's evidence path moved to `intent/SKILL.md`, which carries the same activation phrase, so it survives T9.
- `test_intent_template_shape_conformance.py`: reads `intent/assets/intent-template.md` (replaced, because the template exists in the new path).
- `test_shaping_handoff_pack_surface.py`: the untrusted-read boundary check reads `intent`; the capability and fallback pin reads `intent/references/decompose.md`.
- Tests that still read a source directory (four pack tests, `test_intent_skill_structure.py` merge checks, the live-demo receipt pin) hold the names only in `RETIRED_SHAPING_SKILLS`. T9 must delete or repoint them when it deletes the sources. The live-demo receipt pins a recorded 2026-08 walkthrough in a Shipped spec's note, so its source-skill list stays historical.

### AC-0034

`python3 tools/render-lifecycle-graphics.py` run twice. Both runs give `76c58dad50e7e6db6cc37e0e6984f5342d013a6c` for `the-operating-model-full-map.svg`, so a re-run leaves it unchanged.

### Versions

No pack version bump. `packs/AGENTS.md` bumps for non-cosmetic `.apm/**` and `seeds/**` content and says pack documentation is not projected. Only `packs/product-engineering/{README,JOURNEY,DESIGN}.md` changed under `packs/` outside tests and the eval label field, and T9 bumps product-engineering to 1.0.0. The `intent/evals/eval_queries.json` label edit is inside the unreleased `intent` skill. The atlassian, github, and linear READMEs under `guides/` are guides, not pack files, so they have no version.

### Gates

`ruff check .` clean. 251 pytest tests pass across the product-engineering, experience-design, `test_workspace_status`, `test_live_demo_guide`, `test_add_rendering_directives`, skill-census, handoff-surface, handoff-matrix, template-conformance, and RFC-0099 suites. `test-lint-knowledge-surface-parity.py` passes all 8 cases. `lint-pack-journeys`, `lint-journey-contract`, `validate_guides`, `lint-guide-titles`, `check-guide-index`, and `catalogue lint` pass.

Known red until T9: `lint-web-journey-parity` reports the journey lists 13 skills and the pack has 16, because the three source directories still exist. It matches at 13 after T9.
Pre-existing, not from T7: `tools/test-check-contract-drift.py` case A fails because its fixture anchors `core` where the checker expects `frontend-engineering`. The real checker `tools/repo/check_contract_drift.py` exits 0.

## 2026-10-11 — wave 4 (T7) close

- **Pre-existing failure:** `tools/test-check-contract-drift.py` fails on an unmodified `HEAD` worktree, so this slice did not cause it. It is recorded as a known skip, `pre-existing-check-contract-drift-selftest`.
- **Red until T9:** `tools/lint-web-journey-parity.py` expects the source directories to be gone. It is red until T9 deletes them.
- **Eval owner labels:** T7 retargeted the `owner` labels in `intent/evals/eval_queries.json` to `intent <mode>`. The runner reads only `query` and `should_trigger`. The T3 owner table above keeps the old names as the merge record.

## 2026-10-11 — post-fold probe attempt 1 stopped; description revised

The first post-fold probe matched the skill in 11 of 11 cases. It missed mode or confidence in 4: F1, F2, D2, and C1. Under AC-0020 the slice stopped before any deletion.

**Approval:** on 2026-10-11, eugenelim chose to revise the description and re-run the probe. That is the Ask-first approval for changing the description after the probe ran.

**What changed in the description:**
- It now names the three modes explicitly.
- It limits route mode to requests that ask which way to shape something.
- It is 847 characters, written as a YAML double-quoted scalar because the text contains `: `.

**Re-runs:** both are re-run on this text. The post-fold activation run that used the old description was stopped unscored.

## 2026-10-11 — T8 post-fold probe, attempt 2: stopped by AC-0020

- The revised `intent` description re-ran all eleven cold classifications.
- Skill and mode matched 11 of 11. F2 came back at medium confidence; the other ten were high.
- AC-0020 requires high confidence, so the slice stops before source deletion. The post-fold activation run was not started.
- Record: `routing-classification-evidence.md` § Post-fold world, attempt 2.

## 2026-10-11 — T8 post-fold probe, attempt 3: stopped by AC-0020

- The `frame` clause and `intake-intent` exclusion were revised; all eleven cases re-ran cold.
- Skill and mode matched 11 of 11. F2 rose to high. D2 fell to medium on wording unchanged since attempt 2, where it was high.
- AC-0020 requires high confidence, so the slice stops before source deletion. The post-fold activation run was not started.
- Record: `routing-classification-evidence.md` § Post-fold world, attempt 3.

## 2026-10-11 — owner direction: AC-0020 uses repeated runs

Across attempts 2 and 3, all eleven post-fold cases matched in skill and mode every time. Confidence labels moved on unchanged text: D2 scored high in attempt 2 and medium in attempt 3 on the same `de-risk` wording. A single cold run therefore cannot tell a description fault from run-to-run noise.

On 2026-10-11, eugenelim chose to amend AC-0020 in session: each post-fold case runs three times, and passes when all three runs match in skill and mode and at least two are at high confidence. AC-0019 counts 44 classifications (11 pre-fold, 33 post-fold). Attempts 1–3 stay in the evidence note as history and do not count toward the amended rule.

This is the fifth controlled amendment.

## 2026-10-11 — T8 scored post-fold probe: passes AC-0020

- 33 cold runs, three per case, on one byte-identical candidate set (the attempt-3 `intent` description).
- 33 of 33 matched skill and mode; 33 of 33 at high confidence. All eleven cases pass.
- Record: `routing-classification-evidence.md` § Post-fold world, scored attempt.
- Next: the post-fold activation run (AC-0023).

## 2026-10-11 — T8 post-fold activation run: stopped by AC-0023

- **Result:** `notes/activation-post-fold-attempt4.json` (unscored history); the host's skill list is in `notes/post-fold-listed-skills-attempt4.txt` (`intent` listed; the three sources absent).
  - Errored runs: **0**.
  - Positive trigger rate: **0.644**, against a bound of at least 0.67 (pre-fold 0.70 − 3 points). **Fails.**
  - False-trigger rate: **0.000**, against a bound of at most 0.03. Passes.
- **By mode** (mean over each mode's ten positives, pre-fold → post-fold):
  - `frame`: 0.90 → 0.97.
  - `de-risk`: 0.70 → 0.43.
  - `decompose`: 0.50 → 0.53.
- **Pattern in the misses:** in most zero-rate runs the model searched the projection, found no matching artifact, and answered directly without calling the `Skill` tool.
- **Harness observation, both worlds:** runs share one projection directory per world, and some runs wrote intent files into it (pre-fold projection: 5 files under `docs/`; post-fold: 7). Later runs can see those files. This affects both worlds the same way and is recorded, not corrected.
- **Disposition:** under AC-0023 nothing is deleted. eugenelim decides whether to split the weakest mode back out or to end the slice.

## 2026-10-11 — owner direction: revise the description after the AC-0023 miss

On 2026-10-11, eugenelim chose in session to revise the `intent` description so the `de-risk` clause covers assumption and experiment wording, then re-measure. AC-0023 offered only "split the weakest mode back out" or "end the slice", so this adds a third path by controlled amendment.

The revision is informed by the held-out misses. That weakens the held-out set as an unseen test for this one revision: the new wording must stay general and must not copy a held-out query. The ledger records this caveat beside the re-measured result.

This is the sixth controlled amendment.

## 2026-10-11 — owner choice: revise after the AC-0023 failure

On 2026-10-11, after the AC-0023 failure recorded above (positive trigger rate 0.644 against a bound of 0.67), eugenelim chose the revise path in session and approved the revised `intent` description. The change is to the `de-risk` clause and its triggers:

- the clause now reads "finds the assumption that would sink an intent if it were wrong and picks a cheap test for it, with a kill condition set in advance";
- two triggers are added: "what's the riskiest assumption" and "how do we test this cheaply".

No held-out query appears verbatim in the revised description (substring check over all 42). The new triggers overlap the wording of probe case D1. This entry is the AC-0019 gate for the next scored attempt.

## 2026-10-11 — T8 scored post-fold probe on the revised description: passes AC-0020

- 33 cold runs, three per case, on one byte-identical candidate set; only `intent` changed from attempt 4.
- 33 of 33 matched skill and mode; 33 of 33 at high confidence.
- Attempt 4 and its post-fold activation run are now unscored history.
- Record: `routing-classification-evidence.md` § Post-fold world, scored attempt.

## 2026-10-11 — T8 post-fold activation run on the scored attempt: passes AC-0023

- **Result:** `notes/activation-post-fold.json`; skill list in `notes/post-fold-listed-skills.txt` (`intent` listed; the three sources absent). Fresh projection; this is the scored attempt's one post-fold run.
  - Errored runs: **0**.
  - Positive trigger rate: **0.711** (pre-fold 0.70; bound at least 0.67). Passes.
  - False-trigger rate: **0.000** (pre-fold 0.00; bound at most 0.03). Passes.
- **By mode** (pre-fold → post-fold): `frame` 0.90 → 0.97; `de-risk` 0.70 → 0.53; `decompose` 0.50 → 0.63.
- **Held-out caveat (AC-0023):** the held-out misses from attempt 4's run informed the `de-risk` revision behind this result. The held-out set is therefore not a fully unseen test for this revision. No held-out query appears verbatim in the revised description.
- **Remaining gap:** `de-risk` still triggers below its pre-fold rate; the aggregate bound holds.

## 2026-10-11 — T8 manual QA walks: AC-0008, AC-0038, AC-0039

- Walks ran headless in fresh git-tracked copies of the post-fold projection, with Core's `shaping-reviewer` installed. Requests and replies are quoted verbatim in `notes/manual-qa-walks.md`.
- **AC-0008:** one question; `git status` clean before and after. Pass.
- **AC-0038:** the route reply names the short route, says the user starts at step 1, and offers `frame` as an option. Pass.
- **AC-0039:** superseded by the re-walk entry below; the first walks did not reach `decompose` and most replies did not name the stage.

## 2026-10-11 — T9 install-then-update observation (AC-0031)

Observed in a scratch git repository, `claude-code` adapter, repo scope, with the worktree's `agentbundle`:

1. `agentbundle install <HEAD catalogue> --pack product-engineering --scope repo` (0.13.24): `.claude/skills/` holds `frame-intent`, `de-risk-intent`, and `decompose-intent`.
2. `agentbundle upgrade <this change> --pack product-engineering --scope repo`: reports `0.13.24 -> 1.0.0`. `intent/` is added, and **the three retired directories remain**.
3. `agentbundle install <this change> --pack product-engineering --scope repo --force` on that state: re-applies 1.0.0; the three directories still remain.
4. `agentbundle uninstall --pack product-engineering --scope repo`, then `install`: removes all four, then installs only `intent/`. No retired directory remains.

Adopter step for the changelog: after updating, either delete the three directories by hand, or run `agentbundle uninstall --pack product-engineering` and then `agentbundle install --pack product-engineering` at the same scope.

## 2026-10-11 — T9 delete, bump, record, self-host

- **AC-0009:** the three source directories are deleted; `[pack.evals].skills` lists `intent` and no retired name, and every listed name has a directory.
- **AC-0024:** product-engineering 1.0.0 (`pack.toml`, `plugin.json`); Core 3.0.3, experience-design 4.1.5, governance-extras 1.0.2, product-strategy 0.2.8 from T5/T6; agentbundle 0.52.1 with the `test_okf_catalogue_discovery` pin, `README-pypi.md`, and `CHANGELOG.md` moved together.
- **Census:** three entries removed, `population_size` 131; `test_skill_census.py` passes.
- **Changelog (AC-0025, AC-0029, AC-0031, AC-0032):** entries for all six artifacts; Core's heading sits directly beneath `[Unreleased]`.
- **AC-0040:** dated, approver-attributed erratum on ADR-0111.
- **AC-0026:** after self-host, `catalogue lint --deep` and `catalogue verify` pass.
- **AC-0010:** the search finds only `RETIRED_SHAPING_SKILLS` constants and the directory names of two Shipped specs; the gitignored generated `now-highlights` JSON is not in scope.
- **AC-0034:** re-rendering leaves the full-map SVG byte-identical.
- **Tests repointed:** the source-reading tests in `packs/product-engineering/tests/pack/` dropped their source parameters; tests whose only target was a deleted file were removed where an `intent` counterpart already asserts the same thing.
- **Brief lifecycle:** with `intent-short-route` Implementing, the brief moves Ready → Executing in the file and in `workspace.toml`; its Spec map row reads Implementing.
- **Suites:** roster, `tools/test_workspace_status.py`, and work-intake: 19 failures and errors also fail on unmodified HEAD (packaging venv, tracker matrix, credbroker wheel); none is caused by this change.

## 2026-10-11 — T9 test changes (AC-0007)

**De-risk boundary rescope (the Ask-first exemption).** `de-risk`'s sentence "This skill never dispatches it." became "The de-risk mode never dispatches `adversarial-reviewer`." in `intent/references/de-risk.md`. The reason, "marking its homework", is kept.
- Replaced assertion: `assert "This skill never dispatches it." in body` (and `in bullet`).
- Replacement: `test_de_risk_mode_states_the_no_dispatch_boundary` asserts the new sentence is present and the old one absent; `test_the_mode_boundary_is_stated_once_and_carries_no_dispatch_instruction` asserts the refusal bullet. Its mention count is 2 because the bullet's lead and its refusal sit on separate lines; it is still one bullet.

**Removed at T9, each with its `intent` counterpart:**

| Removed test | File | Replaced by |
| --- | --- | --- |
| `test_de_risk_intent_states_the_no_dispatch_boundary` | `test_de_risk_intent_reviewer_boundary.py` | `test_de_risk_mode_states_the_no_dispatch_boundary` (same file) |
| `test_the_boundary_is_stated_once_and_carries_no_dispatch_instruction` | `test_de_risk_intent_reviewer_boundary.py` | `test_the_mode_boundary_is_stated_once_and_carries_no_dispatch_instruction` (same file) |
| `test_the_decompose_skill_core_absent_sentence_names_work_intake` | `test_intent_triad_execution_wiring.py` | `test_the_intent_decompose_mode_core_absent_sentence_names_work_intake` (same file) |
| `test_the_recursive_decomposition_fallback_sentence_names_work_intake` | `test_intent_triad_execution_wiring.py` | `test_the_intent_recursive_decomposition_fallback_names_work_intake` (same file) |
| `test_frame_intent_carries_the_pick_a_route_section` | `test_intent_triad_execution_wiring.py` | `test_sections_appear_in_order_and_modes_table_has_four_rows` (`test_intent_skill_structure.py`): `## Route mode` holds the menu |
| `test_the_route_menu_names_three_routes_with_a_fit_line` | `test_intent_triad_execution_wiring.py` | `test_route_mode_names_three_routes_and_three_out_of_stage_owners` and `test_short_and_supervised_routes_and_stage_kinds` (`test_intent_skill_structure.py`) |
| `test_the_menu_names_no_six_step_skill_but_frame_situation` | `test_intent_triad_execution_wiring.py` | Dropped. The `intent` lifecycle map names the six longer-route steps on purpose (AC-0036), so "the menu names no later step" no longer holds; `test_longer_route_matches_frame_situation_step_four` pins the route instead. |

**Repointed at T9 (source parameter dropped, `intent` parameter kept):** every parametrised test in `test_frame_intent_shaping_review.py` and `test_frame_intent_experience_handoff.py`; `test_the_eval_harness_covers_the_boundary` now reads only `intent/evals/evals.json`.

**Changed at T9:** `test_merged_queries_have_no_duplicates_and_every_source_query` became `test_merged_queries_have_no_duplicates_and_the_sources_are_gone`. The source-query carry-over was verified against the sources before deletion (§ T3 eval merge, AC-0016).

## 2026-10-11 — AC-0039 re-walk after the stage instruction

The implementation review found that the walk never reached `decompose` and that most replies did not name the user's stage. The skill told the agent each mode's stage only in the reference file's `Stage:` line, with no instruction to say it to the user. `intent/SKILL.md` § Modes now says to open each mode's reply with the route and step, and to name the mode alone when no route is shown. This is the orientation the spec already required (AC-0037, AC-0039), so it falls under the Ask-first exemption for the orientation line. The `intent` eval cases `frame-1`, `de-risk-1`, and `decompose-1` each gained an assertion for it. The description is unchanged, so AC-0021 and the activation result still hold.

Re-walk results, all in `notes/manual-qa-walks.md`:
- Mode replies name the user's stage: frame, de-risk (bar set, survive), and decompose name "short route, step N of 3"; the no-route reply names "de-risk mode" alone. One supporting reply, where decompose stopped before a verdict, named no stage.
- No mode starts the next mode before the user chooses it. Two supporting replies show the gate holding: results that did not match the bar were recorded as undetermined, and decompose was declined on an undetermined bet.
- After frame, the reply recommends the shaping review. After the review passes, it recommends `de-risk` and offers the adversarial read.
- The short-route survive reply marks `decompose` recommended. The decompose reply produces one leaf delivery contract and recommends the hand-off, naming it "the spec-writing step" rather than `work-intake`.
- The no-route survive reply asks which route applies.
- **AC-0039:** pass.

## 2026-10-11 — Stage line in replies that stop at a gate

The implementation review found the one walk reply above that named no stage: decompose stopping before a verdict. `intent/SKILL.md` § Modes now says the stage line opens every mode reply, including one that stops at a gate or declines to run. A fresh session re-tested a gate stop of the same kind: decompose asked of a framed, reviewed intent that was not yet de-risked, where the original stop followed an undetermined verdict: the reply opens "Short route, step 3 of 3: decompose.", changes no file, and offers three options (`notes/manual-qa-walks.md` § AC-0039: decompose stopping at its gate). The other AC-0039 replies were recorded before the gate clause was added; apart from the earlier gate stop, each names its stage. This gate-stop reply is the only one walked on the current skill. **AC-0039:** pass.

## 2026-10-11 — Quality review repairs (tests)

- **AC-0030:** `test_moved_files_never_share_a_path` walked the deleted sources after T9, so it guarded nothing. It is now `test_moved_files_land_under_intent`: the files under `intent/references`, `assets`, and `examples` must equal a reviewed list of the fourteen moved files plus the three mode files. AC-0030's collision half was checked at T2 before the sources were deleted (§ T2).
- **Duplicates removed:** `test_the_intent_skill_template_matches_the_source_template` (same path as the repointed `TEMPLATE` checks), `test_intent_skill_description_carries_the_shaping_activation_phrase` (the R2 scenario already requires the phrase from `intent/SKILL.md`), and `test_intent_skill_and_decompose_mode_keep_the_handoff_contract` (repeats the boundary and capability checks in the same file).
- **Simplified:** the frame shaping-review and experience-handoff suites lost their single-case parametrization and unused path defaults; the duplicate frontmatter test in the shaping-review suite is gone (`test_frontmatter_tools_and_boundaries_are_exact` keeps it). The de-risk boundary suite keeps its constants at the top and carries the reasoning for its bullet-scoped slice again.
- **Held-out disjointness:** `test_merged_queries_share_no_query_with_the_held_out_set` read this spec's notes from a pack suite, which the pack-test boundary forbids. It is dropped; the disjointness was verified for the release gate (§ T3 eval merge, AC-0023).
- **Pack-test boundary:** `tools/lint-pack-test-boundary.py` failed on six variable path segments in `test_intent_skill_structure.py` added at T2; the suite now builds paths from literal directories and the lint passes.

## 2026-10-11 — owner direction: `intent` declares no `allowed-tools`

The security review found that Claude Code reads a skill's `allowed-tools` as tools it may use without asking permission, not as a restriction (Claude Code skills documentation: "It does not restrict which tools are available"). AC-0006's `allowed-tools: Read Write Edit Agent` therefore pre-approved writes, edits, and agent dispatch for every `intent` mode, including route mode, which only reads, and de-risk and decompose, which read untrusted input and had no pre-approval before the fold. The plan's statement that the list "narrows" de-risk and decompose holds only on a host that reads the field as a restriction.

On 2026-10-11, eugenelim chose in session to remove `allowed-tools` from `intent`. Writes then prompt under the user's permission settings in every mode, as they did for de-risk and decompose before the fold; frame loses the pre-approval it had. The boundaries metadata is unchanged.

This is the seventh controlled amendment.

## 2026-10-11 — AC-0006 implemented: `intent` pre-approves no tools

- `intent/SKILL.md` no longer declares `allowed-tools`; the boundaries metadata is unchanged.
- **AC-0007 (replaced assertion):** `test_frontmatter_tools_and_boundaries_are_exact` asserted `allowed-tools == "Read Write Edit Agent"`. It is now `test_frontmatter_pre_approves_no_tools_and_boundaries_are_exact`, asserting the key is absent; the boundaries assertion is unchanged.
- The product-engineering 1.0.0 changelog entry states the change for interactive and headless callers.

## 2026-10-11 — Reviewer dispatch without `allowed-tools`

Headless check on the amended skill, in a fresh git-tracked projection copy, with `--permission-mode acceptEdits --allowed-tools "Skill Read Write Edit Glob Grep"`. `Agent` was deliberately not granted.
- A frame request wrote the intent and dispatched `shaping-reviewer` through `Agent` twice: the review and a re-run after an edit. The session transcript shows both `Agent` calls with `subagent_type: shaping-reviewer`.
- The run's `permission_denials` lists one `Bash` listing call and no `Agent` call.
- A follow-up "Run the shaping review." reported the recorded pass and offered `intent de-risk` (recommended) and the advisory `adversarial-reviewer` read.

So removing `allowed-tools` does not stop reviewer dispatch on Claude Code: `Agent` needs no grant by default. Claude Code's permissions documentation (fetched 2026-10-11) agrees: its table of tool types that ask in Manual mode lists Bash commands, file modification, web fetch, and web search, and not `Agent`; subagents are limited by `Agent(name)` deny rules. Writes need one in a headless run, as the changelog states. In this run frame dispatched the review inside the frame turn; in the AC-0039 walk frame recommended it. frame's procedure allows both, and each reply's offers matched its review state.

## 2026-10-11 — owner direction: correct the plan's agent-dispatch sentence

The security delta review found that plan § Tool authority says agent dispatch prompts, while the headless check above shows `Agent` needs no grant by default. On 2026-10-11, eugenelim chose in session to correct the plan sentence. No criterion, code, or test changes; AC-0006 ("no mode is pre-approved") stays accurate.

This is the eighth controlled amendment.

## 2026-10-11 — Rebase onto origin/main

`origin/main` gained PR #1538, which shipped Core 3.0.3 and product-engineering 0.13.25 and added optional architect offers to `frame-intent`, `de-risk-intent`, `decompose-intent`, `frame-domain`, `diverge-solutions`, `explore-options`, and `map-capabilities`.
- **Versions:** Core moves to 3.0.4 (`pack.toml`, `plugin.json`, both changelogs); product-engineering stays 1.0.0.
- **Ported into `intent`:** the System-shape questions section (`references/frame.md`), the feasibility grounding (`references/de-risk.md`), the subsystem-boundary check (`references/decompose.md`), the `knowledge-surfaces.md` change, and four eval cases (`system-shape-question-architect-installed`, `system-shape-question-architect-absent`, `feasibility-architect-absent-silent`, `architect-absent-silent`) in `intent/evals/evals.json` under their modes.
- **Retargeted:** `test_architect_optional_offers.py` reads the `intent` mode files and evals; the two architect integrations in `pack.toml` name `skill:intent`; `test_shaping_reach.py`, `packs/architect/DESIGN.md`, the pack README, the operating-model guide, `hand-an-intent-to-build.md`, `guides/README.md`, `lifecycle-flow.md`, the discovery tutorial, and the graphics renderer name the `intent` modes; both SVGs are regenerated.
- **Descriptions:** #1538 changed no skill description, so the probe candidates and AC-0021 are unaffected.
- **Checks after rebase:** ordinals unique; self-host clean; catalogue lint and verify pass; ruff and mypy clean; pack-test boundary passes; product-engineering 60 passed, architect 290 passed; roster, workspace-status, work-intake, and close-work suites show the same 19 failures as unmodified HEAD; the AC-0010 search finds only allowed matches.
