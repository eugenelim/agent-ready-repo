# The predeclared kill condition

The single load-bearing guard of the pack. The discipline is one sentence:
**write down what result would kill the bet, before you run the test.** Declaring
the line *after* seeing the result lets you rationalize whatever happened — the
failure mode this exists to prevent.

## Currency-adaptive — name the line in the test's own units

The *form* of the kill condition flexes to what the test can actually measure;
the *timing* (declare before) never does.

- **You have traffic / an A/B surface** → a **quantitative threshold**: a minimum
  detectable effect, a conversion floor, a retention line. Tooling (Statsig,
  Eppo, Amplitude) makes you predeclare an MDE anyway — lean on it.
- **0-to-1 / pre-PMF / low traffic** → a **qualitative bar**, predeclared just as
  firmly: "proceed only if ≥ 4 of 6 target users complete the task unaided and
  none report feeling unsafe." A fabricated conversion number here is fake rigor;
  a clear qualitative bar is real.
- **Architectural / capability-level** → a feasibility or adoption line: "the two
  services sustain p99 < 200 ms at 10× today's load", or "≥ 2 stream teams commit
  to adopting the capability before we build the platform".

## Front it with "what would have to be true"

Roger Martin's elicitation: list the conditions that must hold for the bet to pay
off, rank by risk × ignorance, and attach the kill condition to the top one.
WWHTBT is the on-ramp (it opens the space); the predeclared kill condition is the
teeth (it closes it). Use both — and note that pure pass-all-tests falsification
sometimes finds *nothing* passes; the kill condition is a decision aid, not a
veto that forbids conviction on a genuinely novel bet.

## The shape

```
Riskiest assumption: <one sentence>
What would have to be true: <the conditions>
Kill condition (predeclared <date>): <result, in the test's own currency>
```

Record it on the intent before the test runs. The verdict step compares the
actual result to this line — survived or killed — and never edits the line to fit
the result.
