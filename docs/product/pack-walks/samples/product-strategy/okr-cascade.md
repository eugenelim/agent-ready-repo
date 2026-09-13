---
type: okr-cascade
---
# OKR cascade — FY27 H1

## Company OKRs

### O1: Win the Midwest corridor spot market

- KR1.1 Spot-market win rate in corridor — baseline 11% → target 25%
- KR1.2 Carrier retention, corridor — baseline 68% → target 80%

### O2: Reduce cost to serve per load

- KR2.1 Support minutes per load — baseline 14 → target 6

## Team OKRs

### Booking — rolls up to O1

- **Objective:** Make a quote something a shipper can act on in the moment
- KR Median quote latency — 40 min → under 60 s
- KR Quotes issued as firm rather than estimate — 0% → 90%

### Carrier platform — rolls up to O1 and O2

- **Objective:** Let drivers update a load without calling a dispatcher
- KR Status updates arriving without a phone call — 0% → 60%

## Gap registry

| Gap slug | Description | Blocks |
| --- | --- | --- |
| `rating-engine-single-owner` | The rating engine has one reader and no documentation. Instant quoting puts it on the critical path for every request. No owning team has capacity booked. | KR1.1 |
| `driver-mobile-surface` | No driver-facing surface exists. Support-minute reduction has no delivery path without one, and no team currently owns it. | KR2.1 |
| `carrier-precommit-terms` | Firm quoting assumes carriers pre-commit capacity at a quoted price. No commercial terms exist for this and it is not a product decision. | KR1.2 |

<!-- A worked example. Produced by running `run-okr-cascade` against the Northwind
     scenario, following its procedure step by step. The company is fictional. -->
