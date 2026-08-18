# RFC-0088 Experimental round 10 — the bounded measurement round

**Status:** partial. Two of four named tasks are complete; the round is written up
at this point because the work is real and the remaining tasks are independent of
it, not because the list is finished. What is outstanding is stated as outstanding.

Round 9 established that RFC-0088's six pre-acceptance blockers are dominated by
approver dispositions no experiment can settle, and that the measurement work
genuinely remaining is a finite list of four tasks. This round runs that list.

**It measures the architecture and does not re-measure the apparatus.** No
coverage percentage, claim-accounting total, or mutation-harness figure is a
deliverable here. Round 9 showed that number moves when controls are added, so a
round that both adds facts and re-measures coverage would be reporting its own
activity as progress.

## Reproduction identity

- Repository ref: `e0a9c536`
- Host: macOS 26.5.2, Darwin 25.5.0, arm64
- Node v26.4.0; Playwright 1.62.0; bundled Chromium 151.0.7922.34 — the same
  versions as the promoted round-7 evidence, verified before any measurement
- **Environment: an explicit allowlist, not the ambient environment.** Every arm
  ran under `env -i` with exactly `PATH`, `HOME`, `TMPDIR`, `LANG`,
  `PLAYWRIGHT_BROWSERS_PATH` and `RFC88_SANDBOX` (plus `__CF_USER_TEXT_ENCODING`,
  which macOS injects into every child and which round 3 already recorded). No
  `SSH_AUTH_SOCK`, no session token, no credential, no personal browser profile,
  no protected config. Verified by having the child print its own environment.

  This differs from the historical suite: `run-all-r7.sh` unsets three Playwright
  variables and otherwise inherits the ambient environment. Because the
  environment differs, **round 10 does not compare its sandboxed arm against the
  promoted round-7 artifact.** It runs its own off-mode arm under identical
  conditions and compares against that. Comparing across environments is the
  measured-on-a-stand-in defect this evidence base has been corrected for
  repeatedly.

## Task 1 — the S1 lifecycle corpus, sandboxed

The corpus had no sandboxed arm. Round 7 parameterised two drivers — the realm
matrix and the opaque-realm probe — so "the rails are sandbox-invariant" was
established for the rails and *inferred* for everything else, which is the
inference item 1 marks as unproven.

**Result: sandbox-invariant.** Both modes: 13 asserted, 12 passed, 1 failed,
1 recorded, `fatal: null`, identical row for row. The mode is read back from the
launched browser rather than asserted — the off arm observes `--no-sandbox`
present and the renderer sandbox inactive, the on arm observes it absent and the
sandbox active — and a run whose observed mode disagreed with its requested mode
would fail rather than quietly report the other configuration.

### The row that fails, and what round 10 found about it

`S1-ATTACHMENT-ENDPOINT-CONFINEMENT` fails in both modes. The failure is declared
(`expectedFailingRows`) because the failure *is* the finding.

**The RFC's S1 verdict misattributes this row to Linux.** It reads "Pass on the
named gates (macOS and Linux); one platform row fails on Linux". Measured on
macOS under the **real per-user temp root** — `/var/folders/…/T`, mode `0700` at
depth 3, the genuine platform layout — the row fails there too.

The reason is sharper than a wrong platform label. The row asserts
`ownedThroughout && privateAncestor !== undefined`, and `ownedByCurrentUserThroughout`
requires user ownership of every ancestor **up to `/`**, which no path on a real
filesystem satisfies. So the row cannot pass on any platform. The genuine
platform difference is real but lives in a different field: macOS reports
`confinedByAncestorDepth: 3`; the promoted Linux artifacts report `null`. The RFC
is reading a distinction the row's verdict does not carry.

A caveat recorded as a caveat: an earlier round-10 arm ran under a synthetic
world-traversable temp root and failed the same row for a *different* reason
(`confinedByAncestorDepth: null`). That was an artifact of the harness, not a
finding. It does independently corroborate item 1's existing diagnosis — flip the
temp root's mode and the confinement field flips, so the confinement was never a
property of Playwright.

## Task 2 — the S3 trust rail drivers, sandboxed

Neither trust driver had a sandboxed arm, including the one the RFC cites for
"trust and method enforcement composed in one launch".

| Driver | Off | On | Mode verified both arms | Checks differing |
| --- | --- | --- | --- | --- |
| `r5-mitm-trust` | 9 of 9 | 9 of 9 | yes | **none** |
| `r7-trust-and-method-composed` | 9 of 9 | 9 of 9 | yes | **none** |

**Result: both sandbox-invariant**, stated per driver rather than as one
aggregate "no differences" summary.

### The instrument gap this exposed

**The renderer-sandbox mode cannot be read back from a headless browser.** Under
the new headless mode `chrome://version` fails with `net::ERR_INVALID_URL`, so
*both* page instruments this evidence base has return `readBack: false`. Both
trust drivers run headless. The mode was therefore unobservable for exactly the
drivers this task exists to measure, and "sandbox-invariant" could not have been
established for either of them.

This surfaced because the new assertion **failed** rather than treating a `null`
read-back as agreement. Written as a descriptive row instead, both drivers would
have reported passes with an unverified mode and the round would have called it
invariance.

The fix is an OS-level instrument that reads the browser process's own `argv`.
It is pointed: that is precisely the capability item 5 flags — the derived
profile minimum admits `sysctl*`, hence `kern.procargs2`, hence the SPKI pin on
the browser command line. **The instrument that rescues this measurement is a
working demonstration of the defeat item 5 describes**, and every artifact labels
it `ps argv (kern.procargs2 class)` so that is visible rather than buried.

Two constraints in it: it locates the browser by the unique profile directory the
run created, never by process name — matching on a browser name would pick up any
browser on the host, including a person's own, which is both wrong and a privacy
problem — and it reads while the browser is alive, before the profile is removed.

## Round-10 corrections

| # | Round-10 claim or control | What was established | Status |
| --- | --- | --- | --- |
| R10-1 | A driver that cannot complete reports that it could not complete | **It reports all-pass and exits 0.** Round 10 hit this twice in one hour — the browser could not be found, then the socket bind failed with `EINVAL` — and both artifacts recorded `passed == asserted`, `failed: 0`, `fatal` set, exit code 0. **No gate read `fatal`**, so such a file satisfied the failing-row gate for the only reason that matters: the rows that would have failed never ran. That is round 3's "a driver exits 0 regardless of row outcomes", alive in round 10 | **Fixed.** `gate_results` refuses an artifact with `fatal` set unless declared via `expectedFatal`, by the same declare-it-explicitly mechanism as `expectedFailingRows`. Negative-tested in four cells: clean baseline passes, undeclared `fatal` blocks, declared passes, restored passes |
| R10-2 | The sandbox read-back works wherever a browser runs | It does not work **headless**, which is how both trust drivers run. `chrome://version` returns `net::ERR_INVALID_URL` under the new headless mode and both page instruments go blind. The mode was unobservable for the drivers task 2 exists to measure | **Fixed** with an OS-level `argv` instrument, used only when the page instruments report `readBack: false`. Found because the assertion failed rather than accepting `null` as agreement |
| R10-3 | Round 10's arms wrote to round 10's artifacts | **Two of them overwrote promoted round-7 members at the round-7 names**, changing their digests — a re-run under a different environment sitting where a reader takes the round-7 measurement to be. Caught by comparing every touched member against the manifest, not by noticing at the time | **Fixed.** The round-7 files were restored from the archive and re-verified against the manifest; round 10's arms were given their own names; and the drivers now reproduce the round-7 path when `RFC88_SANDBOX` is unset, so an older reconstruction still works and round 10's pair is opt-in |
| R10-4 | A promoted artifact can be regenerated by re-running its driver | Not byte-identically, and that matters more than it sounds. Each artifact carries `provenance.runId` and `startedAtMs` — a per-run nonce, deliberately, since that is what makes three runs provably three executions. So **the manifest pins the promoted bytes, not a reproducible computation**, and any stray driver run destroys promoted bytes recoverable only from the archive. Round 10 destroyed them twice, once while *testing* that it had stopped destroying them | **Recorded, not fixed.** Removing the nonce would remove the replication guarantee. The mitigation is the one already relied on: the archive is the recovery path, and every touched member is compared against the manifest before promotion |

## Verification

Every figure quoted above is derived by the round-7 figure verifier, which now
takes this note as part of its corpus: **78 figures derived, zero wrong, zero
claimed-nowhere**.

**Each of the eleven facts added for round 10 was mutation-tested individually** —
mutate the artifact field it guards, confirm the fact fails, restore. All eleven
were caught and the tree restored clean. The test ships with the evidence as
`r10-fact-negative-tests.py`, because a fact not shown to fail is not a control.

Two of the facts were wrong on their first version and the tests are why that is
known rather than believed: one derived `12/13` while the note says `12 passed`,
and one captured an empty group, so both reported mismatches against prose that
was correct. A verifier that disagrees with itself about formatting is noise a
reader learns to ignore.

One derivation was also corrected in kind rather than in value. The round-9
corpus figure was derived from a live glob, so round 10 adding six artifacts
drifted it from 23 to 29 — silently restating round 9's denominator and leaving
its 9.0% coverage figure describing a corpus it never measured. It now excludes
round-10 artifacts by name: round 9's corpus is what round 9 measured.

## What is NOT done

- **Task 3 — compose the OS profile with the Node permission model.** Not started.
  This is the task that would test whether the correction-9 defeat (a confined
  adapter host reading the live browser profile) is closed by the composition, and
  it has never been run in any round.
- **Task 4 — the restored-profile realm fixture.** Not started. No fixture creates
  a restored-profile realm at all, so nothing has been measured about it; the
  standing answer is a requirement, not a measurement.
- **Task 2's Linux trust arm.** Deferred, not dropped. It needs a container image
  pull of roughly three gigabytes **and a new driver** — both trust drivers are
  macOS-only, so there is nothing to merely re-run on Linux. Deferred on a
  space-constrained host; recorded here so the gap stays visible rather than
  quietly becoming "not applicable".

No result in this note authorizes acceptance or implementation, and no blocker
item is closed. The RFC stays `Experimental`.
