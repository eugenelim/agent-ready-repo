# Release checklist

> Manual-QA rows that GitHub Actions cannot exercise. Run through this
> before tagging a release; tick each row in the release PR description.

This file is *living* — every spec whose work needs out-of-band
verification should add a row here. The header for a spec's rows is the
spec slug; the row body is the exact behavior being verified.

## How to use this checklist

1. On the release branch, copy each section's checkbox block into the
   release PR description.
2. Run the manual exercise on a fresh machine where the spec applies
   (Windows VM, fresh macOS user, …).
3. Tick the box only when the exercise actually passes. A row that
   fails is a release blocker — file an issue, do not silently leave
   the box unchecked.

## Credential storage (CredBroker and credential-setup)

These three Windows observations remain unrecorded here. Current unit tests
do not replace a real terminal, logoff or service-account observation. Keep the
boxes unchecked until an operator records the result for the current CredBroker
and credential-setup implementation; old skill-secrets delivery status does not
prove them. See [current credential boundaries](../architecture/credentials.md).

- [ ] **`getpass.getpass` real-tty refusal** — on a Windows
      developer box with a real tty, use `credential-setup`
      with a test namespace/schema. The prompt MUST appear,
      MUST hide the typed token (no echo), and the resulting Tier-2
      entry MUST resolve at Tier 2 through the current CredBroker consumer. CI
      unit tests monkeypatch `sys.stdin.isatty`; only a real terminal
      observation can verify this path.
- [ ] **`CRED_PERSIST_LOCAL_MACHINE` survives logoff** — on a Windows
      box, create a test entry with `credential-setup`, log out, log
      back in, then resolve it through the current CredBroker consumer. The entry
      MUST still resolve at Tier 2 (CI runners are single-session and
      can't exercise this).
- [ ] **`ERROR_NO_SUCH_LOGON_SESSION` under `LocalSystem`** — schedule
      a Windows Task Scheduler job running as `LocalSystem` that
      resolves a test namespace through CredBroker. The operation MUST
      raise `Tier2HardFailError` naming `ERROR_NO_SUCH_LOGON_SESSION (1312)`
      — proving the resolver does *not* silently fall through to
      Tier 3 in a no-logon-session context.

Backend failure contracts: `packages/credbroker/credbroker/_credman_windows.py`.

## site-browser-quality-gate (`docs/specs/site-browser-quality-gate/spec.md`)

The deterministic browser gate in `pages.yml` covers eight marketing routes and two
documentation routes at 360, 375, 390, 414 and 1440 CSS pixels, both docs themes,
and blocks the deploy on overflow, serious axe findings, broken keyboard paths or
unresolved fragments. It cannot cover a real device: touch ergonomics, iOS Safari's
dynamic viewport and toolbar behaviour, Android Chrome's address-bar collapse, real
font rasterisation and pinch-zoom are all outside a headless engine at a 375px
viewport. WCAG target-size conformance was measured from emitted geometry, which is
evidence about the page, not about a thumb.

The exact gesture is in
[`docs/guides/how-to/verify-a-site-release.md`](../guides/how-to/verify-a-site-release.md).
Record device, OS, browser and version there as well as ticking here.

- [ ] **Compact iOS browser pass** — on a phone-sized iOS browser, open the
      deployed site root, open the marketing navigation drawer and follow one
      destination, open `/now/` and follow one release-notes link into the
      changelog, open `/docs/` and one nested guide, scroll one wide code block and
      one wide table sideways, and rotate to landscape and back.
- [ ] **Compact Android browser pass** — the same gesture on a phone-sized Android
      browser.

**Status at the gate's ship (2026-08-18): BLOCKED, not passed.** No physical iOS or
Android device was reachable from the environment that shipped the spec. The
deterministic 60-case matrix passed; this gesture did not run. Owner: eugenelim. It
must be performed before the next site release is approved — do not tick a box you
did not observe.

Cross-ref: `docs/specs/site-browser-quality-gate/spec.md` AC15.
