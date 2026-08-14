# Manual QA record — catalogue corporate trust store

Satisfies the spec's end-to-end-install criterion. Re-run after the adversarial
and security review rounds, so the
observations describe the shipped code.

**Where the recovery proof actually lives.** It is
`packages/agentbundle/tests/integration/test_trust_fallback_tls.py`, not this
file. That test stands up a throwaway certificate authority and a `localhost`
TLS server, so attempt one fails a *real* handshake and the retry recovers from
one — no network, and independent of how the local trust store happens to be
shaped. The runs below corroborate behaviour against a real remote host; they no
longer carry the recovery claim on their own, for the reason in the next section.

## Why the original repro stopped demonstrating recovery

The first version of this record used `SSL_CERT_FILE` pointed at an empty PEM to
force a verification failure, and the fallback recovered. That worked only
because the fallback then also read Apple's
`SystemRootCertificates.keychain`, which supplied the public root the emptied
store had removed.

Security review established that reading Apple's root program was unnecessary
and widening: the retry context already starts from
`ssl.create_default_context()`, so the public roots are present, and on a
corporate host reading `System.keychain` alone produced the same anchor count as
reading both. `SystemRootCertificates.keychain` was dropped.

That correction invalidated the repro rather than the feature. Emptying the whole
trust store is not the corporate failure shape — a real intercepted machine has
its 190-odd public roots intact and is missing exactly one corporate root. With
the store emptied, `System.keychain` alone cannot verify a public host, so the
artificial repro now fails at the retry. Measured: 30 anchors from
`System.keychain`, and `github.com` does not verify against them alone.

This is a limitation of the simulation, not a regression. It is what motivated
building the integration test.

## Observed behaviour against a real host

Reproduced with `SSL_CERT_FILE` pointed at an empty PEM
(`193` trusted certificates unset, `0` with the stale value):

| Scenario | Observed |
| --- | --- |
| Fallback active | stderr notice fires naming the host; retry attempted; fails at the retry for the store-shape reason above |
| `AGENTBUNDLE_NO_SYSTEM_TRUST=1` | no notice, one connection, message states the fallback "was not attempted"; troubleshooting list correctly ends at step 4 rather than advising the variable already set |
| `system_anchor_pem` stubbed to `None` (non-macOS shape) | no notice, exactly one connection, message names the platform and that the fallback covers macOS only |

The verbatim notice:

```
agentbundle: certificate verification failed for github.com; retrying with operating-system trust anchors
```

The normal path — no relevant variable set, default store intact — resolves the
catalogue in one connection with no notice, unchanged from before this work.

## Deliberately NOT exercised

Recorded so nobody reads more into this than it proves:

- **A real TLS-inspecting proxy.** Nothing here runs on an intercepted network.
  The affected adopters are the only people who can confirm the end-to-end
  recovery on the machines that motivated this work. `tools/diagnose-tls-trust.py`
  in this repository is what they run to produce that evidence.
- **A corporate root absent from `System.keychain`.** If the org's authority is
  installed elsewhere (an NSS store, a per-application store), the fallback finds
  nothing and the adopter sees the no-anchors message.
- **Windows and Linux on real hosts.** Only the no-anchors branch is simulated.
  Windows needs no fallback (Python reads its certificate store directly); the
  residual is WSL, tracked as `catalogue-trust-store-wsl-diagnosis`.
- **A proxy requiring Kerberos or NTLM.** `urllib` cannot satisfy either,
  regardless of trust configuration.
- **The cross-host egress case.** The fetch redirects `github.com` →
  `codeload.github.com`; an allowlist permitting only the first host fails after
  certificates are correct. Named in the error text, not reproduced.
- **An administrator "Never Trust" marking.** No such marking exists on the host
  used, so the deferred gap
  (`catalogue-trust-store-trust-settings`) is latent here rather than observed.
- **A real keychain dump with unparseable material.** Covered by the integration
  test's dirty-dump case and by unit tests, because a real dump is
  machine-specific and its contents identify the operator's employer.
