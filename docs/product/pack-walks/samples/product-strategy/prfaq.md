# Northwind quotes freight in under a minute

### Shippers moving loads in the Midwest corridor get a firm, carrier-backed price without waiting for a broker to call back.

CHICAGO — 14 May 2027 — Northwind Logistics today opened instant quoting to all
shippers in its Midwest corridor. A shipper enters a lane, a date and a trailer
type, and receives a firm price backed by a contracted carrier in under sixty
seconds.

Booking freight on the spot market still means sending a request and waiting.
Median quote turnaround across the corridor is over half an hour, and by the time
a price arrives the capacity behind it may be gone. Shippers told us they book
with whoever answers first, not whoever is cheapest.

Northwind prices against eight years of settled loads and its own contracted
carrier base, so the number a shipper sees is one a carrier has already agreed to
haul for. There is no follow-up call to confirm.

> "We had the carrier relationships and the pricing history. What we did not have
> was a way for a shipper to see either of them in the moment they were deciding."
> — VP Product, Northwind Logistics

Shippers can quote a lane at northwind.example/quote with no account.

> "We stopped sending the same load to four brokers. The first firm number that
> comes back is usually theirs now."
> — Logistics Manager, a Midwest food manufacturer

## Customer FAQ

**Is the price firm, or does it change after I book?**
Firm for the quoted lane, date and trailer type. If we cannot cover it at that
price we cover the difference — we do not re-quote you.

**How is this different from the instant quotes I already get elsewhere?**
Most instant quotes are estimates that a broker confirms later. Ours is backed by
a contracted carrier at the moment you see it. The trade-off is coverage: outside
the Midwest corridor we are slower than competitors, and we say so on the quote.

**What if my lane is not covered?**
You get a decline, not a slow quote. We would rather you go elsewhere in ten
seconds than wait forty minutes for us to say no.

## Internal FAQ

**What is the riskiest assumption?**
That carriers will pre-commit capacity at a quoted price without seeing the load
first. If they will not, every quote degrades to an estimate and the entire
differentiator collapses.

**What is the hardest technical problem?**
The rating engine is owned by one engineer and undocumented. Instant quoting puts
it on the critical path for every request rather than one per dispatcher.

**What does success look like in 12 months?**
Spot-market win rate in the corridor, not quote volume. Quote volume rises the
moment quoting is free, and tells us nothing.

<!-- A worked example. Produced by running `write-prfaq` against the Northwind
     scenario, following its procedure step by step. The company is fictional. -->
