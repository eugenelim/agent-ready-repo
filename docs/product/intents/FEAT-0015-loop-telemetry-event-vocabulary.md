# Reconcile INI-005's telemetry event names with what the loop can emit

- **Slug:** `loop-telemetry-event-vocabulary`
- **Level:** feature
- **Status:** Withdrawn
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:loop-telemetry-governance

## Disposition — withdrawn 2026-11-05, decided: the answers are recorded here and the work waits for INI-005

**Do not shape this intent.** Its only consumer, the ecosystem's INI-005 (Infra & Observability), has not started: `docs/product/roadmap.md` lists it with the trigger "INI-004 M1 ships", and no spec, brief or queue entry was ever implied. The three questions below are answered so the research is not lost:

- **`gate-waived`:** drop it. The supervisor has no waiver operation, and a retry cap is the only override.
- **`budget-exceeded`:** narrow it to time. Time is derivable from the gap between consecutive `at` values, and no pack can see token counts.
- **Per-event metadata:** narrow the clause to the fields the loop line carries. `milestone` and agent identity are not on it, and joining them would need a harness change.

Checked 2026-11-05: the derivability research and `docs/product/shaping/ecosystem-overview.md` (the defining source of the eight names) both exist and still list them, and the roadmap still gates INI-005 on INI-004 M1. Reopen when INI-004 M1 ships.

## Outcome

INI-005's eight telemetry event names and what the work-loop can actually emit are reconciled, so a future INI-005 RFC uses names and metadata that each have a real source.

## Boundary

- Admits: renaming, narrowing, or dropping any of the eight names; deciding where a token budget and an agent identity are sourced from, if anywhere.
- Excludes: adding an event, field, or key to `.loop-run/events.jsonl`. Measurement showed no new event closes any of the three gaps below.
- Excludes: the sender and its mapping profile, owned by `docs/specs/jsonl-otlp-exporter` and `docs/specs/loop-telemetry-export`.
- Excludes: effective retry-cap telemetry. The supervisor line carries no retry fields (`work-supervisor.py status --json` reports them), and none would resolve the vocabulary decisions below.

## Owner

- Repository maintainers. They hold this intent now, and answer for whether it is picked up, reshaped, or dropped.
- The ecosystem INI-005 (Infra & Observability) initiative is the eventual consumer, not the current owner: it is unstarted, listed under the roadmap's "Not in scope (this repo)" with trigger "INI-004 M1 ships", so it has no one to answer for this today. Not this repository's `ini-005` (AgentBundle Portable Catalogue Tooling), which is a different initiative in a separate namespace.

## Unresolved questions

- `gate-waived` names a waived gate *verdict*, which the supervisor cannot perform — it has no waiver operation, and a retry cap is the only override. Drop the event, or redefine it as "an override flag was supplied" and accept that `waived` does not prove a cap fired (the retired phase engine's own test asserted `waived: true` at 0 of 5)?
- `budget-exceeded` is defined as "(time or token)". Time is derivable from the gap between consecutive `at` values; the retired engine's `phase_s` is not on the supervisor line. Tokens are not available to any pack, which `telemetry.md` § 4 records as settled rather than postponed. Narrow the event to time, or source tokens from the harness (INI-003 / INI-004)?
- Each event is required to carry "spec slug, milestone, agent identity, timestamp, gate name, outcome metadata". `milestone` and agent identity are not on the line. Join them (via `spec` into `workspace.toml`, and via the harness), or narrow the metadata clause?

## Projection

- An ecosystem INI-005 RFC, or an amendment to the roadmap's "Telemetry events schema" research thread. No spec or delivery brief is implied, and no queue entry is registered.

## Opportunity

The eight names were authored before the envelope existed and have never been checked against it. Measurement against `core` 2.25.26 found six of the eight derivable from the thirteen fields the retired phase engine emitted; the remaining two fail for reasons no new event fixes. The supervisor line carries ten fields, so the six verdicts need a re-check before use. Full evidence and re-runnable commands live in the source document.

## Assumptions

- **Riskiest assumption:** `docs/product/shaping/ecosystem-overview.md` is the defining source for the eight names; `docs/product/roadmap.md` only lists them. Resolving the names from the roadmap alone resolves them against the wrong document.
- Effective retry-cap reporting does not supply token usage, agent identity, or milestone and therefore does not close this intent.
- **Knowledge surface:** In-repository telemetry research, roadmap, shipped loop contract, and delivery history.


## Source

- Mode: repo-origin
- Locator: docs/product/research/loop-telemetry-event-derivability.md
- Revision: sha256-bytes-v1:22fd532582aa051b88d305e8e5d5d477b952543482c7c7434b2149eb6024c91f
- Authority: repo-origin
