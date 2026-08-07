# Manual QA — sso-store-transition-serialization

The spec's only manual-QA criterion. Everything else is machine-checked.

## AC10 — the uncontended critical section is bounded

**Why this is manual.** No runner in this repo's CI can execute it. There is no
macOS runner; on Linux `_tier2_backend` is `None`, so `rm` spawns
`/usr/bin/security` zero times and the cost being bounded does not exist; on
Windows Credential Manager is reached in-process through `ctypes`, a different
cost model from which the 2 s bar was not derived. An automated version would
pass green without ever exercising the thing being measured.

**What is measured.** The longest-held region in the change: `rm` on a profile
with continuation slots, where `_delete_cookie_jar` calls `_purge_credential`
per slot and each is up to four `/usr/bin/security` spawns (delete, verify-read,
scrub-write, verify-read — the last two only when the backend ignores deletes).

### Run of 2026-08-07

- **Machine:** Apple silicon (arm64), macOS 26.5.2
- **Engine:** `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py` at
  wave 4 of this spec
- **Method:** the per-spawn cost of `/usr/bin/security` measured directly over
  20 iterations, then multiplied by the call count `rm` performs. The end-to-end
  form — driving the projected broker against the real login keychain — was not
  run, because it writes credential entries into the operator's own keychain;
  see *Outstanding* below.

| Measure | Result |
|---|---|
| `/usr/bin/security` spawn, median | **53.8 ms** |
| `/usr/bin/security` spawn, max over 20 | 125.1 ms |
| 4 slots × 2 spawns (ordinary path) | 0.430 s |
| 4 slots × 4 spawns (backend ignores deletes) | 0.860 s |
| 10 slots × 4 spawns | **2.151 s** |
| 40 slots × 4 spawns | **8.602 s** |

**Verdict against AC10 as written — PASS, and the bar is fragile.**

AC10 specifies "a profile with at least four continuation slots". At exactly
four slots the worst case is 0.860 s, comfortably under the 2 s bar. But the
cost is linear in slot count and the bar breaks at ten.

`CRED_MAX_CREDENTIAL_BLOB_SIZE_BYTES` is 2048
(`sso-broker.py:96`), so ten slots is a ~20 KB jar and forty is ~80 KB. A
captured corporate SSO jar is deliberately over-broad — the engine stores
`context.cookies()` unfiltered — so jars in that range are ordinary, not
pathological. **A realistic profile therefore exceeds the 2 s bar**, and with
the default 10 s wait budget a `rm` on an 80 KB jar could hold the lock for most
of it.

This is the risk the plan named ("The macOS critical section is longer than
assumed"), and AC10 was written so the measurement could fail rather than divert
into a remedy. Recorded as `sso-keychain-call-timeouts` in
`workspace.toml [backlog].open` and raised as a decision rather than fixed here:
adding `timeout=` to the `security` calls changes behaviour on a projected file
(it would turn "the operator is typing their keychain password" into a store
failure) and belongs to whoever owns that call, not to this spec.

### Outstanding

- **End-to-end run against the real keychain.** AC10's literal procedure — twenty
  consecutive `rm` invocations through the projected broker — writes throwaway
  `agentbundle:sso:*` entries into the operator's login keychain and may prompt
  for keychain access. Not run unattended. The spawn-cost measurement above
  bounds the same quantity (the cost is dominated by process spawns; the
  in-process work is a dict update and a file replace), so the verdict stands,
  but the end-to-end confirmation is still owed.
