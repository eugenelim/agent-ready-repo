# Process defect: two task gate receipts were admitted before their implementation existed

- **Kind:** defect
- **Status:** Closed
- **Discovered:** 2026-11-05, during the promotion-drain-hardening run's adversarial review
- **Run:** `run-ab615caaae11a770`, spec `docs/specs/work-item-promotion-handoff`

## What happened

The run's evidence ledger holds two task-admission receipts whose gate
claims were false at admission time:

- `a-route-with-no-dispatch-wired-holds-the-item-1646c3a2` (T19), committed
  as `0b8454304`
- `a-classification-is-one-of-the-six-classify-tabl-9aef571e` (T20),
  committed as `a51b1aee8`

Both commits contain only the ledger line — no code, no tests. The
hardening implementation for every task T19–T23 landed later, in the
commits labeled "implement T21" through "implement T23" (`207eaa08d`,
`f5dd7ff77`, `98d8b5ada`).

## Cause

An automation script — a load-retry driver reporting the already-implemented
verification tasks T2–T18 in sequence — matched its stop-guard against
guessed slug fragments instead of the supervisor's title-derived task ids,
so it reported T19 and T20 as gate-passed with no code present. The fault
was the script's, filed by the controller that ran it.

## Correction

The implementations and their gates landed in the same session, before any
later task was reported; the AC-level gate receipts (written after the code
landed) and this run's review rounds verify them. The review recorded the
defect as finding `adv-hardening-002` of report `rr-adversarial-hardening-1`
and this note is its repair: a reader of the delivery's evidence record can
now find the admission defect and its correction from the repository alone,
without the review packet.
