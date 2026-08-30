> **Superseded by the register, 2026-08-30.** This file records the de-risking
> as it ran; the spec's `## Follow-ons` carries the final dispositions and wins
> where the two differ. Three entries were closed after this was written:
>
> - **R1** — both halves built. The `.`-segment half was the owner call and was
>   authorised on 2026-08-30 after confirming no adopter emits one; the verdict
>   below still calls it open.
> - **R2** — closed as not planned. The verdict below says "shrunk, not killed"
>   and leaves the retention half untested. It was closed on desk evidence — a
>   per-invocation process, one caller, ~1.2 KiB — and the predeclared probe
>   ("instrument one real session") was **not run**.
> - **R4** — closed as deliberate. The verdict below says "likely inverted,
>   needs an owner call". The call was made: `close-work` ships as a whole skill,
>   so an unresolvable seam means a broken install. The predeclared probe
>   ("enumerate install states") was **not run** in full; the closure rests on
>   the packaging evidence.
>
> Desk evidence closing a bet whose probe was predeclared is worth naming rather
> than glossing: it is weaker than running the probe, and either could be
> reopened on the reopen conditions the register states.

# De-risked residuals

Each `## Follow-ons` entry, put through reversibility triage, riskiest
assumption, and a predeclared kill condition, so it can be picked up without
re-deriving the analysis.

**Outcome: one half built, one dropped, two resized.** R1's control-character
half shipped under AC32; R3 is closed at the razor's first rung; R2 lost its
performance framing; R4 gained a seam and may be pointing the wrong way. Where evidence was already in hand before the kill condition was written,
this file says so rather than dressing it as a predeclared test — a threshold
written after the result rationalises whatever happened.

Desk-grounding is not validation. Every hook below is `to-validate`.

---

## R1 — The `locator` pattern diverges from the contract

- **Triage:** one-way door. `locator` is a published contract field. Changing
  which locators validate changes what a conforming producer may write, and any
  record already on disk encodes the old behaviour.
- **Measured divergence** (5 cases, both directions): the validator admits the
  C0 control range, `U+007F`, and NUL, which the contract's `$defs/locator`
  pattern rejects; the contract admits a `.` segment, which the validator
  rejects.
- **What would have to be true:** one side is demonstrably authoritative, *and*
  no existing record depends on the divergent behaviour.
- **Riskiest assumption:** that anyone has decided which side is right. Nobody
  has. The spec pinned only the numeric bound precisely because the pattern
  question was open.
- **Kill condition, predeclared:** if a survey of real lifecycle records finds
  any locator carrying a `.` segment or a control character, this stops being a
  one-line pattern change and becomes a migration — reframe rather than build.
  Independently: if the contract owner cannot state which side is authoritative
  in one round, it is not ready to pick up.
- **Prototype-approach:** `validate-first`. The probe is a corpus survey, not a
  build.
- **Evidence so far:** `docs/lifecycle/` in this repository holds only
  `README.md` — no records exist here, so local migration risk is zero and
  adopter risk is unmeasured.
- **Verdict, revised after applying the razor:** this was never one bet. The
  control-character half needed no decision — the contract and both blessed
  helpers already applied the rule, so `_is_locator` was simply the one surface
  of four missing it. Built under AC32. The `.`-segment half survives as a
  contract change and remains the owner call.

```
validation_hook:
  assumption: one side of the locator divergence is authoritative, and no shipped record relies on the other
  kill_condition: any real record carrying a `.` segment or a control character in its locator
  activity: survey adopter lifecycle records; put the direction question to the contract owner
```

---

## R2 — The authority registry is never evicted, and the check scans it

- **Triage:** two-way door. Process-global state behind a private helper; no
  published surface.
- **Measured:** the registry is not evicted on the write path, the same binding
  is accepted twice, and a full scan costs 15.8 µs at 1 grant, 3.6 ms at 250,
  and 55.8 ms at 4000 — linear.
- **What would have to be true:** worth building only if N grows large enough in
  one process for the scan to matter, or the growth causes real memory pressure.
- **Riskiest assumption:** that N is large in practice.
- **Desk evidence, already in hand before any kill condition was written:**
  shipped pack code contains exactly **one** caller of
  `resolve_mutation_authority`, on the deletion path, resolving one grant per
  confirmed effect. Realistic N in one session is single digits, where the scan
  costs well under a millisecond. A binding that is in the registry also
  short-circuits on first match, so the measured figure is worst-case.
- **Consequence:** the performance framing does not survive contact with the
  caller count. What remains is hygiene — a process-global dict that never
  shrinks for the process lifetime.
- **Kill condition for the surviving question, predeclared:** if a real
  `close-work` session cannot be shown to exceed 50 resolved grants, eviction is
  not worth a change to an authority-carrying path. Record the reasoning and
  close it.
- **Prototype-approach:** `validate-first`. Instrument one real session and
  count; do not build eviction first.
- **Verdict:** **shrunk, not killed.** The O(N) half is desk-refuted. The
  retention half is untested.

```
validation_hook:
  assumption: a real close-work session resolves enough grants for retention or scan cost to matter
  kill_condition: fewer than 50 resolved grants in a realistic session
  activity: instrument one real close-work run and count resolve_mutation_authority calls
```

---

## R3 — Host degradation is indistinguishable from bad input

- **Triage:** one-way door. `REFUSAL_CODES` is a published frozenset; adding a
  member is a contract change an adopter may switch on.
- **Measured:** `EACCES`, `EMFILE`, `EIO`, and a genuinely bad zone all produce
  `record-invalid` from `validate_payload` and `unknown-timezone` from
  `compute_review_on`. The module logs nothing, so the cause is unrecoverable
  from the result.
- **What would have to be true:** worth a published-contract change only if an
  operator hits tz-database degradation *and* is actually blocked by the
  ambiguity.
- **Riskiest assumption:** that cooling is the first or only signal an operator
  sees when the tz database degrades. A host that cannot read
  `/usr/share/zoneinfo` is usually failing louder elsewhere.
- **Kill condition, predeclared:** proceed only if at least 2 of 3 surveyed
  operator scenarios show cooling as the first or only signal. Below that, a new
  published code buys no diagnostic gain and costs a contract change.
- **Cheaper alternative to test first:** leave the code set alone and have the
  *caller* log the distinction. That is a two-way door and avoids the contract
  change entirely — if it satisfies the need, R3 never becomes a one-way bet.
- **Prototype-approach:** `validate-first`, on the caller-logging alternative
  before the code addition.
- **Verdict, revised after applying the razor:** **killed at rung 1.** "Not
  genuinely needed? Skip it. Say so in one line." A host that cannot read its
  timezone database fails louder elsewhere, so cooling is not the signal an
  operator is missing. The three-rung ladder below was itself a razor violation —
  checking rungs beneath the first one that held. Recorded as not-planned.

```
validation_hook:
  assumption: an operator hitting tz-database degradation is blocked by cooling's ambiguous refusal
  kill_condition: fewer than 2 of 3 operator scenarios show cooling as the first or only signal
  activity: walk three degradation scenarios with an operator; test caller-side logging first
```

---

## R4 — An unresolvable `close-work` seam escapes six public seams

- **Triage:** nominally two-way, but the repair changes which refusal code an
  existing input shape produces, which this spec's own Boundaries put behind
  *Ask first*. Treat as one-way.
- **Measured, with a genuinely confirmed candidate:** `enrol`, `update_record`,
  `verify_identity`, `deletion_allowed`, `review`, and `review_exception` all
  raise `ImportError`. Only `load_record` refuses cleanly. The register recorded
  "five reaches", counting call sites; six public entry points is the number
  that matters to a caller.
- **What would have to be true:** worth wrapping only if an unresolvable seam is
  reachable in a working installation, *and* a refusal code is more useful there
  than a traceback.
- **Riskiest assumption:** both halves are doubtful, which is why this is the
  entry most likely to be pointing the wrong way.
- **Desk evidence, already in hand before any kill condition was written:**
  `close_work.py` sits beside `cooling.py` in all three shipped copies and is
  projected by the same self-host step. An unresolvable seam therefore means a
  broken installation, not a runtime condition.
- **Consequence — the bet may invert.** For a broken installation, an
  `ImportError` naming the missing module is *more* actionable than
  `lifecycle-state-unwritable`. Wrapping it would destroy diagnostic
  information and convert an install fault into what reads as a data fault.
- **Kill condition, predeclared:** if no scenario produces an unresolvable seam
  in an intact installation, close this as won't-fix and correct the register to
  say the escape is deliberate rather than a defect.
- **Prototype-approach:** `validate-first`. The probe is enumerating install
  states, not writing a wrapper.
- **Verdict:** **likely inverted.** Needs an owner call before anyone builds it.
  Building the "obvious" fix here would make diagnosis worse.

```
validation_hook:
  assumption: an unresolvable close-work seam is reachable in an intact installation
  kill_condition: no such scenario exists, in which case wrapping destroys diagnostic value
  activity: enumerate install and packaging states that could separate cooling.py from close_work.py
```

---

## What this changes about the register

| Residual | Recorded as | After de-risking |
| --- | --- | --- |
| R1 locator | open question | unchanged; correctly deferred, needs an owner direction call |
| R2 registry | unbounded growth + O(N) | O(N) desk-refuted; hygiene only |
| R3 degradation | needs a distinct code | test caller-side logging first; the code addition is one-way |
| R4 close-work | five reaches to wrap | six seams, and the fix may be the wrong direction |

Two would have been picked up at the wrong size, and one at the wrong sign.
