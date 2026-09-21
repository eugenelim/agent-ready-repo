# gate-main dependency partition — spike evidence

Measured 2026-09-21 on scratch branches. No branch is merged. Every figure below
is read from a CI run, not from the workflow source.

## What was changed on every spike branch

- All 11 provisioning steps hoisted to the front of `gate-main`, with the bandit
  install kept immediately before `Run make build-check` (`tools/test_build_gate_chain.py`
  pins that adjacency).
- The remaining 70 steps marked `if: '!cancelled()'`. The anchor is deliberately
  unmarked: nothing but provisioning precedes it, so a marker would change nothing
  and `anchor-no-if` stays intact.
- `tools/lint-ci-parity.py` and `tools/test-build-check-workflow.py` amended to
  admit that one marker **by string equality**.

## Why the guard amendment was unavoidable

Annotating without it produced, measured locally:

| Guard | Violations | Cause |
| --- | ---: | --- |
| `tools/lint-ci-parity.py` | 59 | AC-0005: a `PR_GATED` entry may not name a step carrying an `if:` |
| `tools/test-build-check-workflow.py` | 4 | `site-step-no-if[...]` on the four site steps |

`lint-ci-parity.py` is chained into `make build-check`, which **is** gate-main's
anchor step. Unamended, every spike run would have gone red at the anchor before
reaching any injection, and each injection's red count would have been noise.

The amendment is surgical, not a weakening. After it:

- `test-build-check-workflow.py`: baseline clean, **180 mutations each caught**,
  all 80 assertion families still exercised. The falsy-`if` mutations
  (`if-false-on-contrast-step`, `if-false-on-site-step`, `if-false-on-anchor`)
  are still caught.
- `test-lint-ci-parity.py`: **200/200**, including
  `if-false-is-conditional-by-presence`.

`!cancelled()` only ever *widens* when a step runs. Every one of these controls
was written against conditions that *narrow*. That mismatch — not a defect in the
controls — is the whole reason the marker reads as neutering.

## Injection results

Each injection is a **new** failing step, not an edit to an existing one, so every
byte-pin and every `PR_GATED` reachability claim survives and the only reds a run
can show are the injection and its true dependents.

| Branch | Run | Injection point | gate-main | Reds |
| --- | --- | --- | --- | ---: |
| `b0-baseline` | 35617361413 | none | success | **0** (87/87) |
| `b1-ruff` | 35617369311 | step 16, after `ruff lint` | failure | **1** |
| `b2-producer` | 35617377276 | step 15, after the anchor; `rm -rf dist build` | failure | **1** |
| `b3-mid` | 35617385318 | step 40, after `pytest credential-setup skill` | failure | **1** |
| `b4-stale` | 35620526256 | step 15, after the anchor; corrupt 40 files in `dist/` | failure | **1** |

The one non-green step besides the injection in each failing run is
`Post Set up Python`, a runner-generated cache-save action, not a gate.

## Conclusion

**The partition holds. No dependent was found at any injection point.**

The brief predicted dependents would live immediately after `Run make build-check`,
the one check step that is also a producer. Both variants of that hypothesis were
tested directly and both are refuted:

- `b2` deleted `dist/` and `build/` outright — 70/70 downstream steps passed.
- `b4` corrupted `dist/` in place instead, because this repository's history says
  an *absent* build directory passes where a *stale* one fails, and stale is the
  state a real mid-run anchor failure leaves. The step logged `40`, so forty
  markdown files were present and passed to `sed -i` — 70/70 downstream steps
  still passed.

The acceptance criterion — "the root cause is always distinguishable from its
cascade" — is satisfied trivially, because there is no cascade to distinguish.

## Residuals, stated plainly

1. **Three positions out of 70 were tested.** The claim supported is not "all 70
   are provably independent"; it is that no dependent was found at early, mid, and
   producer-adjacent positions, and that the only hypothesis with a concrete
   mechanism was tested directly and refuted in both variants.
2. **`b4`'s corruption is evidenced by file count, not by read-back.** The step
   proved 40 files were present and handed to `sed -i` and reported no `sed`
   error; it did not re-read one to confirm the marker landed. `b2`'s outright
   deletion is the unambiguous half of the pair, and the two agree.
3. **The artifact-dependent phase is empty.** The brief's three-phase design
   collapses to two: 12 provisioning, 70 independent, 0 dependent. An axis whose
   third value no member takes is a value no test exercises — a future genuinely
   dependent step could be declared into it, or wrongly left out of it, with
   nothing failing. The roster extension must keep `DEPENDENT` declarable and
   state what evidence moves a step into it.

## Trap worth keeping

`_step_named` in `tools/test-build-check-workflow.py` matches by **substring**. A
probe step named after its target was returned in the target's place and made
`anchor-step`, `anchor-no-if` and `no-working-directory[...]` all misreport against
the probe. Any step name added to this workflow must not contain another step's name.

## Runtime: no cost on green runs

Green-only runs of the modified job against the unmodified job at the same base
commit (`spike/gate-main-b5-control`).

| | n | mean | values |
| --- | ---: | ---: | --- |
| treatment | 4 | 448.8s | 418, 449, 456, 472 |
| control | 5 | 394.8s | 348, 353, 366, 452, 455 |

Pooled, that reads +53.9s (+13.7%) — and it is an artefact. The control set is
**bimodal**: three runs near 355s and two near 453s, which is GitHub runner-class
variation. All four treatment runs landed in the slow tier.

- treatment vs **all** control: **+53.9s**
- treatment vs **slow-tier** control: **−4.8s** ← like-for-like

The per-step evidence says the same thing independently. The pooled +54s is
concentrated in the two heaviest steps, and the ratio is near-identical across
all three of the heaviest:

| Step | treatment / control |
| --- | ---: |
| `Run make build-check` | 1.177 |
| `pytest catalogue-test carve-out destinations` | 1.158 |
| `pytest shared-test dedup guard` | 1.165 |
| whole job | 1.137 |

A uniform multiplicative factor across unrelated steps is a slower machine. Added
work would be additive and would land on the steps that changed — but the two
steps carrying the largest deltas are untouched by the hoist and only carry the
marker. Two provisioning steps got *faster* (`Install tools dependencies` −3.3s,
Markdown→Office libs −1.0s), consistent with resolving pip once up front.

**Conclusion: no measurable runtime cost on a green run.** This matters because
`docs/product/intents/ci-gate-main-runtime-budget.md` records gate-main already
missing a shipped 200s budget; the change does not make that worse.

The one real runtime cost is **on failing runs**, by design: a failed step no
longer skips the rest, so a red run does more work than it used to. That is the
trade being bought — one round with every independent failure, instead of one
round per failure.

## Containment: `!cancelled()` alone does NOT contain a provisioning failure

`!cancelled()` means "unless the **workflow** was cancelled". It does not skip on
a prior step's failure — every injection run above proves it, since 70 marked
steps ran to completion after each failure. Hoisting provisioning therefore
relocates the brief's credbroker scenario rather than fixing it.

Both branches break `Install credbroker (editable, with crypto extra)` itself.

| Branch | Run | Marker | failure | skipped | success |
| --- | --- | --- | ---: | ---: | ---: |
| `b6-provfail` | 35627735026 | `!cancelled()` | **9** | 7 | 71 |
| `b7-fix` | 35627800391 | provisioning-gated | **1** | 77 | 9 |

### b6 — one root cause, eight spurious reds

| # | Step | Missing because |
| ---: | --- | --- |
| 8 | `Install credbroker (editable, with crypto extra)` | **the root cause** |
| 39 | `pytest credential-setup skill` | credbroker |
| 40 | `pytest jira SSO suites` | httpx install skipped |
| 41 | `pytest confluence-crawler SSO suites` | httpx install skipped |
| 76 | `pytest markdown-to-pptx renderer` | Office libs skipped |
| 77 | `pytest markdown-to-docx renderer` | Office libs skipped |
| 78 | `pytest markdown-to-xlsx renderer` | Office libs skipped |
| 79 | `pytest file-to-markdown extraction` | Tier-0 PDF lib skipped |
| 80 | `pytest msg-to-markdown extraction` | olefile skipped |

The mechanism compounds: a provisioning failure correctly skips all *later*
provisioning (those steps are unmarked), but the marked checks run anyway and
red for dependencies that were never installed. Hoisting makes this **worse**,
because with provisioning contiguous at the front, one failure skips every
remaining install rather than just the ones after it.

The anchor behaved correctly — `Run make build-check` (step 14) was skipped, not
run, because it carries no marker.

### b7 — the fix contains exactly

```yaml
if: "!cancelled() && steps.provisioned.conclusion == 'success'"
```

with `id: provisioned` on the **last** provisioning step. Every earlier
provisioning step is unmarked, so any provisioning failure skips that one, its
conclusion is `skipped` rather than `success`, and every check goes grey.

Result: **1 red, 77 grey**. The nine successes are job setup plus the six
provisioning steps that ran before the break. Containment is by omission, and
the root cause is the only red.

## Consequence for the spec

The central mechanism is **not** "annotate with `!cancelled()`". It is "annotate
with a provisioning-conditioned expression, and give provisioning an explicit
boundary marker". That changes the acceptance criteria, and it lengthens the
string the guard amendment must admit by equality — the admitted value now
references a step id, so the equality pin has more surface to get right.

### The roster's third axis now has a real job

Correcting the earlier reading: `b7` gates every check on provisioning as a
whole, so one broken *optional* install — the Tier-0 `.msg` reader, say — greys
all 70 checks, including the ~60 that never needed it. That is not a regression
(fail-fast stops the job today) but it is not the maximum either.

Recovering those checks needs each one to declare *which* provisioning step it
depends on, which is exactly what a third `STEP_DISPOSITION` axis can encode.
So the axis is not a value nothing takes: `b6` names eight members of it and the
provisioning step each one needs. Whether to build that finer gating now, or ship
the all-or-nothing gate and leave the axis declaring intent, is a spec decision —
but it is now an evidenced one.

## The per-check provisioning dependency matrix

Ten dispatched runs, one per breakable provisioning step. In each, **every other
step carries `!cancelled()`** — provisioning and the anchor included — so
breaking step N does not skip the installs after it. Without that, the reds
conflate N with everything downstream, which is exactly what the earlier
`b6-provfail` probe did.

**Known confound, measured and subtracted.** The scratch relaxation these
branches carry (`False and self._step()["has_if"]`) trips ruff's `SIM223`, so
`ruff lint (style, imports, common bugs)` reds in **10 of 10** runs. Uniform
across every row, therefore a constant, therefore subtracted. It is not a
dependency of anything. The real change must not reproduce it: relax that guard
by deletion, not by a falsy conjunct.

| Broken provisioning step | Run | Dependent checks |
| --- | --- | ---: |
| `Install tools dependencies` | 35642465134 | 4 |
| `Install agentbundle (editable) + pytest` | 35642472761 | 1 |
| `Install ripgrep` | 35642480505 | 2 |
| `Install ruff + mypy` | 35642487339 | 1 |
| `Install credbroker (editable, with crypto extra)` | 35642494151 | 3 |
| `pip install httpx …` | 35642502543 | **0** |
| `pip install the Markdown→Office render libraries` | 35642509557 | 4 |
| `pip install the Tier-0 PDF library` | 35642516579 | 1 |
| `pip install the Tier-0 .msg reader` | 35642522857 | 1 |
| `Install bandit unconditionally` | 35642529928 | 2 |

Members, by provisioning step:

- **tools dependencies** → `Run make build-check`; `pytest import-time path leaks`;
  `pytest catalogue-test carve-out destinations`; `pytest loop-telemetry contracts`
- **agentbundle** → `pytest make-free gate chains`
- **ripgrep** → `converters source-attribution scrub (AC2)`; `converters Rail-C marker scrub (AC3)`
- **ruff + mypy** → `mypy type-check (typed packages only)`
- **credbroker** → `pytest credential-setup skill`; `pytest jira SSO suites`;
  `pytest confluence-crawler SSO suites`
- **httpx** → none
- **Markdown→Office libs** → `pytest markdown-to-pptx renderer`;
  `pytest markdown-to-docx renderer`; `pytest markdown-to-xlsx renderer`;
  `pytest file-to-markdown extraction`
- **Tier-0 PDF** → `pytest file-to-markdown extraction`
- **Tier-0 .msg** → `pytest msg-to-markdown extraction`
- **bandit** → `Run make build-check`; `pytest make-free gate chains`

### What the matrix decides

**The dependency graph is sparse.** Nineteen dependency edges over fifteen
distinct checks. Roughly 55 of the 70 checks depend on no provisioning step that
can fail independently, so per-check gating is worth its mechanism: a broken
`.msg` reader skips one check rather than greying all seventy.

**No universal prefix exists, so the derivation rule needs no shorthand.** Each
check's condition is `!cancelled()`, plus one
`&& steps.<id>.conclusion == 'success'` per declared dependency in roster order.
A check with no dependencies carries `!cancelled()` alone. `Set up Python` is
universal by construction — it is a `uses:` step whose failure stops the job —
and is not a declarable dependency.

### A discovery this surfaced, not acted on here

`pip install httpx for the atlassian SSO suites (RFC-0035)` has **zero**
dependents. The two SSO suites it names fail when *credbroker* is missing, not
when httpx is. Either httpx arrives transitively through credbroker's install or
the step is inert. The earlier `b6-provfail` probe read the SSO reds as httpx's
only because breaking credbroker also skipped the httpx install — the confound
this instrument removes. Out of scope here; it is a candidate for `work-intake`.
