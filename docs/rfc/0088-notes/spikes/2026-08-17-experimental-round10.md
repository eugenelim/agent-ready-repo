# RFC-0088 Experimental round 10 — the bounded measurement round

**Status:** all four named tasks are complete; the round is written up
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
| R10-5 | Task 3's argv probe measured the argv read | **It measured whether `/bin/ps` could be executed.** Using `ps` as the probe conflates "can I exec this binary" with "can I read another process's argv" — and `ps` is setuid root, so `sandbox-exec` refuses it for a reason that has nothing to do with `sysctl*`. That is the measured-on-a-stand-in defect, inside the fixture built to measure item 5 | **Fixed.** The two mechanisms are probed separately and recorded separately: exec of `/bin/ps`, the sysctl binary on a harmless OID, and the `kern.procargs2` OID itself. The conflated version would have reported "argv read denied" and let a reader conclude the profile denies it, when the profile admits the capability and only the tooling is unavailable |
| R10-6 | Task 3's permission-model arms measured a denied read | **Two of the three arms never started.** Node's permission model realpaths an absolute entry script's ancestors, which a subpath grant does not cover, so the runtime died in the module loader — and the arm recorded the read as denied. A denial the arm had not earned, which is the same shape as R10-1 one layer up: the row that would have failed never ran | **Fixed.** The entry script is passed relative with cwd inside the granted scope. Measured rather than guessed: granting the directory, the directory with a trailing wildcard, and the file itself all fail with an absolute entry; the same grants with a relative entry run |
| R10-7 | Task 4's control told restored profiles from fresh ones | **It did not.** It read `navigator.serviceWorker.controller` after load, and the worker calls `clients.claim()`, so a FRESH profile also reports a controller by then — both arms read `true` and the arms were indistinguishable. "Restored" would have been an assertion about which directory was passed, with a control that could not fail | **Fixed.** The reading moved to document start, captured by an init script before any page script runs: restored reads `true`, fresh reads `false`. The after-load value is still recorded, precisely so the note can show why the naive reading was useless |
| R10-8 | The Linux trust arm needed a new driver | **It needed a runner.** Round 10 stated in this note, in its spec's assumptions and in two pull requests that both trust drivers are "macOS-only, so there is nothing to merely re-run" — inferred from filenames carrying no `-linux`, not from the code. Neither driver contains a macOS-specific construct: `r5-mitm-trust.mjs` shells to `/usr/bin/openssl`, which the image has, and `r7-trust-and-method-composed.mjs` already branches on `process.platform` for the browser registry path. The claim inflated the cost of a residual and would have justified leaving it open | **Corrected, and the arm is run.** Both drivers pass 9 of 9 on Linux under a runner of about seventy lines. The estimate was wrong in the direction that let the gap stay open, which is the direction to distrust |

## Task 3 — the OS profile composed with the Node permission model

Never run in any round. RFC-0088 item 5 says the profile requires `file-read*`
unrestricted, so a confined adapter host can read the live browser profile off
disk — the correction-9 defeat — and that the filesystem confinement is supposed to
come from the Node permission model, which no arm had composed with the profile.
It also says `sysctl*` is required and admits `kern.procargs2`, reading another
process's argv, which is where the interception SPKI pin lives.

**task 3 measured 5 of 5.** Three arms, all of which ran:

| Arm | Browser-profile read | `/bin/ps` | sysctl binary | Pin recovered |
| --- | --- | --- | --- | --- |
| profile only (control) | **READ** | denied | works | no |
| + permission model | denied | denied | blocked | no |
| + `--allow-child-process` | **denied** | denied | works | no |

**Item 5's two halves get different answers.**

**The filesystem half is closed by composition.** The profile-only arm READs the
synthetic browser profile, so the defeat is real and not hypothetical; both
permission-model arms deny it — including the third arm, which grants
`--allow-child-process` because a Playwright host cannot spawn a browser without
it. That is the configuration a real adapter host would ship, and the profile read
stays closed in it.

**The argv half is not confirmed, and this refines item 5 rather than supporting
it.** `sysctl*` is admitted and the sysctl binary runs, but **no arm recovered the
pin: no**. Two mechanisms, measured separately rather than conflated:

- `/bin/ps` is refused with `DENIED:EPERM` in the control — it is setuid root
  (`-rwsr-xr-x`) and `sandbox-exec` refuses to exec it. That is independent of the
  permission model, so the usual way to read another process's argv is unavailable
  under the profile at all.
- `kern.procargs2` cannot be addressed through the `sysctl(8)` CLI, which needs the
  three-element MIB with a pid. It fails identically **outside** the sandbox, so
  that is a CLI limitation and not a denial the profile earned.

So the profile admits the capability while denying both standard tools that would
use it. **This is a bound, not an all-clear:** the capability is still admitted, and
a native addon or compiled code could plausibly make the call. Node gates addons
behind `--allow-addons`, which this fixture does not test, and an adapter host
loading a native addon is a different threat than one shelling out to `ps`.

Everything here is synthetic: the browser profile is a file the fixture creates and
the pin is a random token in a process it spawns. The pin's **value** is never
recorded — only whether it was recoverable — because an artifact that archives a
credential value is a defect regardless of where the credential came from.

### A usability finding about the permission model

Node's permission model resolves an absolute entry-script path by realpath'ing its
ancestors, and a subpath grant does not cover them, so an absolute entry dies in
the module loader before any probe runs. Measured directly: granting the directory,
the directory with a trailing wildcard, and the file itself all fail with an
absolute entry; the same grant with a **relative** entry and cwd inside the scope
runs. Two arms of this fixture reported a denied read while the runtime had never
started — a denial the arm had not earned — until the entry path was fixed.

## Task 4 — the realm a restored profile carries

Item 6 lists this realm as "untested rather than covered" and says plainly: "No
fixture creates a restored-profile realm at all, so nothing was measured about it."
Correction 11's requirement — register the shim before any document exists — is
named there as the standing answer, and the note is explicit that it is "a
requirement, not a measurement". This measures it.

The mechanism is a **service worker**, because a service-worker registration is the
realm that genuinely survives a restart: it lives in the profile directory, it has
its own global scope, and `addInitScript` — the way the shim is installed — applies
to documents and frames, not to workers.

**task 4 measured 4 of 4.**

| | Restored profile | Fresh profile (control) |
| --- | --- | --- |
| Controller **at document start** | **true** | **false** |
| Controller after load | true | true |
| Page realm | `SecurityError` | `SecurityError` |
| Service-worker realm | constructed | constructed |

Two facts, and they are separable — which is why both arms are reported.

**A restored profile carries a realm from the very first document.** The
restored profile reports a controller at document start: true, so a worker
persisted in the profile controlled the first document of the next session. It
therefore predates every document `addInitScript` can reach. **a fresh profile
reports false** at that same instant, which is what makes the comparison a
comparison.

**The shim does not reach that realm at all, on any profile.** The page realm
emitted 0 UDP packets — the shim covers it, throwing `SecurityError`. The
service-worker realm emitted 4 UDP packets, in the restored arm *and* in the fresh
arm. So this is not a restoration bug: nothing installs the shim into a
service-worker scope, and no ordering of `addInitScript` changes that.

**Taken together, correction 11's requirement does not close this case.**
Registering the shim before any document exists is necessary and is not sufficient,
because the realm that matters here is not a document. That is a finding against
item 6's standing answer, and it is the kind of answer only a fixture could give —
the requirement reads as sufficient right up until something creates the case.

### The discriminator was wrong first

The first version read `navigator.serviceWorker.controller` *after* load and got
`true` in both arms, because the worker calls `clients.claim()` and claims the page
mid-load on a fresh profile too. That check measured "did a worker claim this page",
not "did the realm pre-exist" — so "restored" would have been an assertion about a
directory. The reading now happens at document start, from an init script, before
any page script runs.

## The Linux trust arm — item 1's platform-coverage residual

Blocker item 1 absorbs the residual "no Linux trust arm": the trust/method
composition was measured on macOS only. It is measured on Linux now.

| Arm | Result | provenance.platform |
| --- | --- | --- |
| Linux mitm trust | 9 of 9 | linux |
| Linux composed trust | 9 of 9 | linux |

Both drivers pass identically to their macOS counterparts, and the platform field
is asserted from each artifact rather than inferred from the runner, because round 6
promoted a macOS artifact as a Linux measurement and a copy-back with no check is
how that happened. This runner refuses to report success for an artifact whose own
provenance does not say `linux` — and that guard fired twice during development,
both times correctly, when a failed container run let the pre-existing macOS files
be copied back unchanged.

**Sandbox off, for a measured reason.** With the renderer sandbox ON this container
dies at launch — `No usable sandbox!`, because Chromium needs unprivileged user
namespaces, which round 7's runner supplied with `--cap-add=SYS_ADMIN`. This arm
exists to close a *trust* coverage gap, and task 2 established on macOS that both
trust drivers are sandbox-invariant, so it runs in the weaker container a design
would actually ship rather than putting two variables in play at once. **The
sandbox-on Linux trust arm remains unrun**, and no capability the arms do not use is
granted — a result taken inside a `SYS_ADMIN` container would describe a stronger
container than the one being proposed.

## Verification

Every figure quoted above is derived by the round-7 figure verifier, which now
takes this note as part of its corpus: **92 figures derived, zero wrong, zero
claimed-nowhere**.

**Each of the twenty-five facts added for round 10 was mutation-tested individually** —
mutate the artifact field it guards, confirm the fact fails, restore. All twenty-five
were caught and the tree restored clean. The test ships with the evidence as
`r10-fact-negative-tests.py`, because a fact not shown to fail is not a control.

Two of the facts were wrong on their first version and the tests are why that is
known rather than believed: one derived `12/13` while the note says `12 passed`,
and one captured an empty group, so both reported mismatches against prose that
was correct. A verifier that disagrees with itself about formatting is noise a
reader learns to ignore.

Two derivations were corrected in kind rather than in value, both the same
mechanism: a live glob standing in for a historical set. The Linux artifact count
drifted 11 to 13 when round 10 added two Linux artifacts, restating a round-7 claim
about a corpus round 7 never saw. And the same for the mutation corpus. The round-9
corpus figure was derived from a live glob, so round 10 adding six artifacts
drifted it from 23 to 29 — silently restating round 9's denominator and leaving
its 9.0% coverage figure describing a corpus it never measured. It now excludes
round-10 artifacts by name: round 9's corpus is what round 9 measured.

## What is NOT done

- **The sandbox-on Linux trust arm.** The trust arms ran sandbox-off because the
  container cannot start a sandboxed renderer without `SYS_ADMIN`. Task 2 showed the
  drivers are sandbox-invariant on macOS, so this is a coverage gap rather than an
  open question — but it is a gap, and it is stated as one.

No result in this note authorizes acceptance or implementation, and no blocker
item is closed. The RFC stays `Experimental`.
