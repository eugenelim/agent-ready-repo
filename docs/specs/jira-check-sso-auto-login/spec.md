# Spec: jira-check-sso-auto-login

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](./plan.md)
- **Constrained by:** [RFC-0035](../../rfc/0035-sso-cookie-auth-for-atlassian-pack.md)
  — pins the dual-auth selector and the fail-closed no-downgrade rule;
  [ADR-0026](../../adr/0026-sso-consumer-resolution-in-credbroker.md) — places
  SSO consumer resolution in `credbroker`, which this spec extends from
  resolution-only to resolution-plus-recapture; and
  [RFC-0084](../../rfc/0084-sso-destination-trust-boundary.md) with
  [ADR-0080](../../adr/0080-generic-headed-sso-capture-remains-operator-only.md)
  — accepts the baseline's same-principal destination limitation, keeps headed
  capture operator-only, and requires automatic refresh to remain headless.
- **Architecture:** [`docs/architecture/credentials.md § The `sso-cookie` broker`](../../architecture/credentials.md#the-sso-cookie-broker) — the engine/library split, the consumer API, destination pinning, the profile grammar, and the auto-recovery contract live there. This spec does not restate them; it implements them.
- **Contract:** none
- **Brief:** none
- **Shape:** integration

Mode: full (risk triggers: **security boundary** — auth, secrets, subprocess invocation on the credential path; **public-interface change** — new `credbroker` API)

> **Spec contract:** this document defines what "done" means. The implementing PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`jira.py check` on the SSO-cookie path re-establishes an **expired** session
without a second operator command, and `check --register` establishes a new one
in a single command.

The recapture operation lands in `credbroker`, per the architecture page's
engine/library split. `jira.py` never resolves a broker path, builds an argv, or
calls `subprocess`. Three consequences follow, and they are the reason for the
placement:

- **Destination pinning is structural — against implementer error, not malice.**
  `refresh_sso_session(profile)` takes no destination parameter, so no *caller*
  can choose where the browser goes; that is enforced by the signature rather
  than by a rule an implementer can forget. It does **not** stop a hostile
  same-principal process editing `~/.agentbundle/sso-profiles/<profile>.toml`,
  which `_do_refresh` reads before launching. Per the accepted profile that is
  conceded, not defended — see AC15 for the one exposure that is.
- **The cross-platform parts are written once.** Timeout, process-tree kill, and
  environment composition are where POSIX and Windows diverge. In `credbroker`
  they are type-checked by `tools/lint-mypy.py` and exercised by CI; in a skill
  script they would be neither, and would be copy-pasted into the next consumer.
- **One broker-path resolver.** The probe path already resolves the broker via
  `credbroker._sso._broker_path()` (`_client.py:204` → `_sso.py:100`).

First-run establishment stays an explicit human act but costs **one** command:
`check --register`. It is the ordinary first-run path and the **only** one that
attests the destination (AC32). Bare `check` never registers. `setup_sso.py`
remains, limited to exactly two cases — scripted pre-bake, and the AC32
mismatch / cannot-derive escape where attestation is unavailable — because
routing an ordinary first run through it would bypass attestation even when
derivation would have succeeded.

Recovery is keyed to a **typed** session-unavailable signal, not the collapsed
`AuthError`.

### Why automating this refresh does not weaken the "user runs it themselves" rule

The rule — retained verbatim because `catalogue_tooling/lint.py:458` pins it,
see AC21 — guards `credential-setup`, which reads a **secret on stdin**: a token
typed into a prompt the agent owns is a token the agent can observe. The
automated refresh passes no secret through the agent's stdio and no cookie value
through argv.

An earlier draft justified safety by claiming the browser's URL bar is the
operator's confirmation surface. **That claim is false and is not used here.**
`_do_register` launches with
`launch_persistent_context(user_data_dir=~/.agentbundle/browser-state/<profile>)`,
so on every run after the first the Chromium profile still holds the IdP
session: `page.goto` auto-SSOs, the success pattern matches inside the first
500 ms poll, and the window opens and closes sub-second with nothing for a human
to read. Safety rests on destination pinning instead.

## Boundaries

### Always do

- Perform recapture through `credbroker`, never by spawning the broker from a skill.
- Key recovery on the typed session-unavailable signal, never on a bare `AuthError`.
- Validate `[sso].profile` before it reaches argv, and again inside the engine before it reaches a path.
- Assert resolved-path containment inside the engine, not just grammar.
- Bound every broker spawn and kill its whole process tree on both platforms.
- Emit a stderr warning whenever `--insecure` fires or is ignored.
- Keep the lint-pinned SKILL.md security phrases byte-identical.

### Ask first

- Widening auto-recovery beyond `check`.
- Adding any CLI flag to `check`.
- Relaxing the profile grammar.
- Calling `register_sso_session` from any path that is not explicitly operator-invoked.

### Never do

- Resolve the broker path, build a broker argv, or call `subprocess` from any skill script.
- Invoke recapture from any `jira.py` path other than `check`, or more than once per process.
- Give `refresh_sso_session` a parameter that could carry a sign-in destination.
- Forward a cookie value, a jar path, or `--insecure` to the broker from any path.
- Interpolate an exception's `str()` into a message on the jar path — it may carry cookie bytes.
- Write a human-facing notice to **stdout** on any subcommand.
- Edit `.claude-plugin/marketplace.json`, `.agentbundle/bin/sso-broker.py`, or `.agentbundle/lib/credbroker/` by hand — all are generated.
- Read, print, or echo the cookie jar's contents.

## Boundaries — scope

**In scope**

- `credbroker` 0.4.1 → 0.5.0: `refresh_sso_session`, `register_sso_session`,
  `validate_sso_profile`, `derive_sso_destination`, and the cross-platform spawn
  helper behind them.
- `jira` skill: `check` auto-recovery, `setup_sso.py`, the typed
  discriminator, and the token path's missing `--insecure` warning (a live
  `docs/CONVENTIONS.md:1197,1214` violation in a file this change already edits).
- `sso-broker.py`: independent profile guard plus path containment.
- `packages/agentbundle`: add `packages/credbroker`'s suite to the Windows
  parity list, plus the two test files that pin this change's own
  behaviour — `tests/unit/test_self_host_windows.py` (the parity list's own
  test) and `tests/unit/test_shipped_pack_manifests.py` (AC33's
  dependency-declaration and install-gate tests). No `agentbundle`
  *source* change beyond the parity list, and it is warranted
  because Shape D puts the cross-platform kill logic in credbroker, whose tests
  run Linux-only today (`self_host_windows.py` lists agentbundle suites and the
  two skill script dirs, not credbroker). No agentbundle version bump — the
  single prior commit touching that file did not bump either.
- `confluence-crawler`: the byte-parity mirror of the shared files
  `tools/test-lint-sso-config.py` pins — which **does** carry behaviour. AC2
  refactors `setup_sso.py` onto `register_sso_session`, so that skill's
  registration gains the AC3 timeout, composed environment and tree-kill; AC20
  adds control-character and `ttl_hint_minutes` validation, so its loader begins
  rejecting configs it accepts today. Both are named in the atlassian changelog
  entry. Its `test_sso_config.py` must pass unchanged after the mirror;
  `test_setup_sso.py` **cannot** — all four of its tests bind symbols AC2
  removes (`setup_sso.build_register_argv`, `setup_sso._broker_path`,
  `setup_sso.subprocess`), so it is rewritten against a stubbed
  `credbroker.register_sso_session` and mirrored byte-identically. AC2 also
  fixes `setup_sso.main()`'s exit mapping, which returns
  `subprocess.run(...).returncode` today and must map the raised `Sso*Error`
  types onto the same `0` / `2` contract its tests assert.
- `docs/architecture/credentials.md`: the `sso-cookie` broker section this spec
  implements against (landed with this change; it was the one broker of four
  with no section).

**Out of scope**

- The token path's credential resolution; every `jira.py` subcommand but
  `check` — **with two carve-outs, both recorded at implementation
  (2026-08-06).** The second: AC11 requires `_cmd_check`'s display fallback and
  the cookie path's expired-session guard to use the *identical* selector, so
  `check` on the **token** path now also reads `key` and `accountId`. A token
  response carrying only one of those prints `as <value>` where it printed
  `as ?`. That is the point of single-sourcing — two lists that happened to
  agree would drift — but it is a token-path output change, so it is named here
  rather than left implied. The first carve-out is AC18's `--insecure`
  warning, on **both** paths: every token-path subcommand gains the
  "verification disabled" line, and every SSO-cookie subcommand gains the
  "ignored" line. Both follow from the *Always do* boundary's "fires **or is
  ignored**", which no scoping to `check` could satisfy. That warning
  lives in `_run`'s shared client construction (`jira.py:722`), which every
  subcommand reaches, because `docs/CONVENTIONS.md:1197,1214` require it
  *whenever the flag fires* and scoping it to `check` would leave the violation
  live everywhere else. So every token-path subcommand gains one stderr line
  when `--insecure` is passed, and nothing else about them changes. (Recorded at
  implementation, 2026-08-06: AC18's own wording already implied this by citing
  the shared construction site, but this bullet read as forbidding it.)
- `confluence-crawler`'s `check` auto-recovery. See *Deferred*.
- `tools/lint-sso-config.py` — a build-time grammar copy would be a further drift site.
- Sourcing `auth_default` / `base_url` from `catalogue.toml`. See *Deferred*.
**Reopened by AC6a/AC6b — `packs/credential-brokers` 0.2.2 → 0.3.0.** The
earlier decision not to bump rested on precedent for *crash fixes*
(7 of the last 8 `sso-broker.py` commits, including `81d53097`, did not bump).
AC6b changes an **exit code** — `3` → `4` for not-registered-on-refresh — which
is a contract change any other caller of the engine can observe, and AC6a
changes what `get-cookies` writes. That is categorically different from a crash
fix, so the pack bumps and the change is named in the changelog.

## Acceptance Criteria

### `credbroker` — the recapture API

- [x] **AC1 (`refresh_sso_session`).** `credbroker.refresh_sso_session(profile)`
      resolves the broker via the module's existing `_broker_path()`, validates
      *profile* per AC4, and runs `sso-broker refresh <profile>` with **no**
      connection arguments. Its signature accepts no destination parameter.
      Exit-code mapping: `0` → return; **`4`** → `SsoProfileNotRegisteredError`
      (new, subclassing the existing `SsoSessionUnavailableError` so current
      handlers still catch it); `refresh` exit `3` or unknown →
      `SsoRecaptureFailedError`; timeout or spawn failure →
      `SsoBrokerUnavailableError`; broker absent → the existing
      `SsoBrokerNotInstalledError`. The full per-verb mapping is the table
      below — exit `3` is **not** assigned two types; its meaning is
      verb-dependent.

      **The engine-exit taxonomy is defined once, here, per verb, and every other
      AC defers to this table rather than restating it.** Exit `3` is not
      assigned two types: its meaning is verb-dependent.

      | Verb | Engine result | credbroker raises | Recoverable? |
      |---|---|---|---|
      | `get-cookies` | `2` (unregistered / no jar) | `SsoSessionUnavailableError` | **yes** |
      | `get-cookies` | `3`, unknown, timeout, spawn failure | `SsoBrokerUnavailableError` | no |
      | `refresh` | `4` (not registered) | `SsoProfileNotRegisteredError` | **yes** |
      | `refresh` / `register` | `3`, unknown | `SsoRecaptureFailedError` | no |
      | `refresh` | **`5`** — headless flow needs a human | `SsoInteractionRequiredError` | no |
      | `refresh` / `register` | timeout, spawn failure | `SsoBrokerUnavailableError` | no |
      | any | materialisation write failure | `SsoBrokerUnavailableError` | no |
      | any | broker absent | `SsoBrokerNotInstalledError` | no |

      Only the two rows marked recoverable reach AC11's recovery path. Without
      that split, an internal broker or grammar failure would trigger a
      browser recapture while the stored session is perfectly valid — the
      behaviour AC3 exists to prevent. **`3` must not mean "not registered"**: the
      engine returns it from ten distinct sites (verified), including
      `_import_playwright` (playwright absent) and `_do_register`'s
      success-pattern-not-matched — the *ordinary* "operator didn't finish
      signing in" case. AC6a gives not-registered-on-refresh its own code. The
      engine's stderr already reaches the operator via AC3's inherited stdio, so
      `SsoRecaptureFailedError` surfaces that rather than substituting a guessed
      remediation.

- [x] **AC2 (`register_sso_session`).** `credbroker.register_sso_session(profile,
      *, login_url, success_url_pattern, cookie_domains, validation_endpoint,
      session_filename=None, ttl_hint_minutes=None)` builds the `register` argv
      and spawns it under **AC3's `register` bound**, always passing
      **`--ephemeral`**. The engine's `register` keeps `persist=True` as its
      default so a direct operator invocation is unaffected; `--ephemeral` is the
      opt-in and `register_sso_session` is its only user. It is the **only**
      function accepting a destination. No cookie value, cookie name, jar path, or
      `Cookie:`-header shape may appear in the argv it constructs. `setup_sso.py`
      is refactored onto it, so `build_register_argv` and the duplicate
      `_broker_path` leave the skill scripts entirely.

- [x] **AC3 (bounded spawn, process tree killed, both platforms).** Both
      functions spawn through one shared helper that:
      - applies a **per-operation** wall-clock timeout — there is no single value
        for "both functions", because their worst cases differ by an order of
        magnitude:

        | Operation | Timeout | Derivation |
        |---|---|---|
        | `register` (incl. `--ephemeral`) | **540 s** | 300 s sign-in poll + 30 s `page.goto` + ~90 s import/launch + ~60 s AC35 seeding launch + 60 s margin |
        | `refresh` | **180 s** | ~90 s import/launch + 30 s `page.goto` navigation + AC14a's 20 s silent-completion window + 10 s context cleanup + 30 s margin — **no** sign-in poll |
        | `get-cookies` | **30 s** | keychain unlock + read; see the probe note below |

        The `register` derivation, spelled out:
        300 s sign-in poll + 30 s default `page.goto` navigation + ~90 s for
        `_import_playwright()` and `launch_persistent_context(headless=False)`
        on a cold browser cache = 420 s; **plus ~60 s for AC35's second, headless
        persistent launch and cookie seeding**, which happens *after* the poll
        and was not in the original sum; plus a 60 s margin so the parent's
        tree-kill does not race the engine's clean exit = **540 s**. Re-derive if
        any component changes;
      - passes `start_new_session=True` and, on timeout or `KeyboardInterrupt`,
        kills the whole tree following the repo's established pattern at
        `workspace_mcp.py:1069-1092` — `getattr(os, "killpg", None)`, SIGTERM →
        bounded grace → SIGKILL on POSIX; on Windows (`os.killpg` absent)
        `taskkill /T /F /PID` first, falling back to `proc.terminate()` then
        `proc.kill()`. Without the tree kill, playwright's Chromium survives
        holding a live corporate session and the `browser-state/<profile>` lock;
      - passes an explicitly composed environment from a named
        `_BROWSER_ENV_ALLOWLIST` constant, never a bare `os.environ`, so a headed
        browser spawned from an agent session cannot inherit `JIRA_API_TOKEN` or
        unrelated provider keys. The allowlist is enumerated in code and split by
        platform, and must include — beyond the obvious `HTTP_PROXY` /
        `HTTPS_PROXY` / `NO_PROXY` / `SSL_CERT_FILE` / `SSL_CERT_DIR` —
        **`REQUESTS_CA_BUNDLE`** (`docs/CONVENTIONS.md:1210`, two lines from the
        `:1214` AC18 cites), the **lowercase** `http_proxy` / `https_proxy` /
        `no_proxy` forms Chromium and curl read, **`NODE_EXTRA_CA_CERTS`** (where
        a corporate MITM CA must land for playwright's Node driver),
        `PLAYWRIGHT_BROWSERS_PATH`, `PATH`, the platform home variables, the
        POSIX display/session variables, and on Windows the minimum set without
        which Chromium and CPython's TLS init fail to start (`SYSTEMROOT`,
        `SYSTEMDRIVE`, `TEMP`, `TMP`, `APPDATA`, `LOCALAPPDATA`, `PROGRAMFILES`,
        `WINDIR`, `PATHEXT`, `COMSPEC`). A test asserts each name is forwarded
        when present in `os.environ`, and that `JIRA_API_TOKEN` is not;
      - takes an explicit **output mode** rather than one fixed stdio posture,
        because the three callers genuinely differ: `register` and `refresh` are
        interactive and inherit **all** stdio; `get-cookies` must **capture
        stdout** — the engine returns the materialised jar path on stdout and
        `load_sso_cookies` parses it — while still letting stderr reach the
        operator. The helper therefore returns a completed-process result, not an
        `int`, so a captured stdout is available to the caller. A helper that
        inherits stdout and returns only a status code would break every
        SSO-cookie client construction even when `get-cookies` succeeds.

      **A timeout is not an expired session.** `load_sso_cookies` maps every
      unsuccessful engine access to `SsoSessionUnavailableError`, which AC11
      site 1 makes *recoverable* — so a slow or locked keychain holding a
      perfectly valid session would be killed by the 30 s probe timeout and then
      trigger a browser recapture. Timeout, spawn failure and any unexpected
      engine exit therefore map to a **non-recoverable** `SsoError` subtype
      (`SsoBrokerUnavailableError`), leaving `SsoSessionUnavailableError` for a
      genuinely missing or unusable session. A test drives a fake `get-cookies`
      past an injected short timeout and asserts exit 2 with
      `refresh_sso_session` never called.

      **`load_sso_cookies` is refactored onto the same helper.** It runs
      `get-cookies` with `env={**os.environ}` and **no timeout**
      (`credbroker/_sso.py:113-119`) — the exact two properties this AC forbids,
      in the same module, on the path AC14's post-recapture re-probe uses. So a
      keychain-unlock prompt after a fresh capture blocks `check` with no
      backstop, and `JIRA_API_TOKEN` crosses to the engine. It takes a short
      (30 s) timeout and the allowlist minus the display/browser variables.

- [x] **AC4 (`validate_sso_profile`, canonical grammar).** Raises
      `SsoConfigError` unless *profile* is a `str` matching **`re.fullmatch`** of
      `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$` and is not a case-insensitive Windows
      reserved device name (`CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`,
      `LPT1`–`LPT9`), with or without an extension. Rationale for `fullmatch` and
      the denylist is in the architecture page; both were confirmed by spike. A
      non-`str` raises `SsoConfigError` (exit 2), never `TypeError` (exit 1).

- [x] **AC5 (`load_sso_cookies` validates too).** The existing
      `load_sso_cookies` calls `validate_sso_profile` before composing its argv,
      so every credbroker entry point that reaches the engine is guarded.

### `sso-broker.py` — the sink

- [x] **AC6 (independent guard).** The engine enforces the AC4 grammar on
      `register`, `get-cookies`, `test` and `refresh` before any path is
      composed — `:274` (jar), `:293` (`_profile_path`), `:376`
      (`browser-state` user-data dir) and the keychain target name all
      interpolate `profile` unguarded today — exiting `3` with a message naming
      the constraint. It carries its own copy per the architecture page's
      dependency direction.

      **`_write_profile` is guarded independently too.** It interpolates
      `f'{key} = "{value}"'` unescaped (`sso-broker.py:308-324`), and
      `_do_refresh` reads the stored table then re-writes every value back
      through it — so AC20's consumer-side guard only covers *newly supplied*
      values, and a profile poisoned before this change is re-injected on every
      automatic refresh. `_write_profile` either **TOML-escapes** every written string or
      rejects **every character a TOML basic string forbids literally** — `"`,
      `\`, and the whole `U+0000`–`U+001F` / `U+007F` control range, not the
      four-character subset. A subset is not enough: TOML input can encode
      `U+0001` as `\u0001`, so after parsing the value holds a bare control
      character with no literal backslash, passes a quote/backslash/CR/LF check,
      and is interpolated straight into the quoted string — producing a profile
      that `tomllib` can no longer read, which breaks every later `check`,
      `refresh` and `rm`. Guarded independently of the consumer.

- [x] **AC6a (the refreshed jar must actually reach the consumer).**
      `_do_get_cookies` materialises the jar to
      `sso-cookies/<profile>.jar` **only** `if not materialised.exists()`
      (`sso-broker.py:467-469`), while on Tier-2-capable platforms
      `_store_cookie_jar` writes the refreshed jar to the **keychain**. So after a
      successful `refresh` on macOS or Windows the re-probe reads the *stale*
      file the pre-refresh probe wrote, the retry 401s, and `check` exits 2
      having opened a browser for nothing. It works only where `_tier2_capable()`
      is false (Linux) — which is where CI runs, so no existing rung would catch
      it. The guard is removed: `_do_get_cookies` rewrites the materialised file
      unconditionally from the store it just loaded.

      **Making the write unconditional makes an existing race routine — and that
      race is deferred, not specified here.** `_file_floor_write` composes a
      **shared** temp path (`path.with_suffix(path.suffix + ".tmp")`) and
      previously fired at most once per profile; every `check` now rewrites, so
      two concurrent `check`es for one profile can collide, and a stale snapshot
      can replace a fresher one. AC6a requires exactly one thing about it: a
      **unique temp name per write** (pid + random suffix), which removes the
      shared-path collision.

      It deliberately specifies **no ordering guarantee** between concurrent
      materialisers. Seventeen review rounds established that the ordering
      protocol cannot be pinned down in prose here: a write-only guard permits
      generation reversal; a lock and a generation check cannot be distinguished
      by any single deterministic test; and a generation check is itself racy
      unless compare-and-replace is atomic. Each formulation admitted the next
      hole. That is a concurrency protocol needing its own design and its own
      tests, not an acceptance criterion bolted onto a jar-materialisation fix.
      The Risks section already records concurrent `check` behaviour as
      undefined; materialisation ordering was explicitly outside this AC's
      original claim. It was subsequently resolved by
      [`sso-store-transition-serialization`](../sso-store-transition-serialization/spec.md),
      which serialises load plus materialisation under the per-profile lock.

      A test asserts two sequential `get-cookies` calls straddling a store change
      return different bytes, under both a keychain-backed and a
      file-floor-backed store — the AC6a regression, which is deterministic.

- [x] **AC6b (distinct not-registered code).** `_do_refresh` returns **`4`** when
      the profile is not registered, leaving `3` for every other engine failure.
      Pinned by AC10's parity test so credbroker's mapping and the engine agree.

- [x] **AC7 (containment, not just grammar).** Each guarded verb additionally
      asserts that the **resolved** profile and jar paths have the engine's store
      directories as their direct parent (canonicalize-then-verify-parent, the
      CWE-73 depth), independent of the grammar, and case-insensitively on
      Windows. Grammar alone is not the control: it is a denylist of shapes,
      while containment is an allowlist of locations.

- [x] **AC8 (`rm` stays usable).** `rm` is gated on **containment only**, not the
      AC4 grammar. A profile registered before this change under a now-invalid
      name must remain deletable — `list-profiles` enumerates the filesystem
      directly (`sso-broker.py:591-602`) and would otherwise keep showing a live
      corporate cookie jar the operator cannot remove.

- [x] **AC9 (traversal proven closed, per verb).** For each guarded verb a test
      asserts exit `3` **and** that stderr names the constraint. An
      exit-code-only assertion would already be green for most cases today
      (`get-cookies` and `test` return 2 for an unregistered profile; `register`
      returns 3 before `mkdir` when `--login-url` is absent), so it would not be
      a red stub. Vectors: `"../../../../tmp/pwn"`, `"abc\n"`, `"abc\r\n"`, a
      65-character name, a non-ASCII name, `""`, `"."`, `".."`, `"CON"`,
      `"con.toml"`, and a non-`str`. Two argv shapes are asserted separately
      because they behave differently: a bare flag-shaped value (`-x`) is
      `SystemExit(2)` from argparse before any guard runs, while
      **`-- -x` parses `profile="-x"` successfully and must reach the guard**
      (verified by spike — the `--` escape is why the grammar's leading-`-`
      rejection is load-bearing rather than cosmetic).

- [x] **AC10 (grammar cannot drift).** A test under `packages/credbroker/tests/unit/`
      extracts the pattern literal and the device-name denylist from
      `sso-broker.py` and from `credbroker` and asserts equality — the same
      byte-equivalence shape as `test_sso_broker_verbs.py`'s existing
      sibling-parity tests. Drift is a fail-open: `load_sso_cookies` maps every
      non-zero engine exit to a session error, so a name credbroker accepts and
      the engine rejects would make `check` attempt recapture on every
      invocation. Under AC1's taxonomy a grammar rejection is a
      **non-recoverable** `SsoBrokerUnavailableError`, so the drift surfaces as a
      hard exit 2 rather than a recapture loop — but the parity test is what stops
      it arising at all.

### `jira` skill — `check` recovery

- [x] **AC11 (typed discriminator).** A typed `SsoSessionUnavailable(AuthError)`
      subclass in `_client.py` marks "no usable session", raised at exactly **five**
      sites and nowhere else:
      1. `from_sso_cookies` — `credbroker.SsoSessionUnavailableError` from `load_sso_cookies`;
      2. `from_sso_cookies` — jar read, parse, or **shape** failure (AC12);
      3. `_request` — `401`, or an unfollowed `3xx`, on the SSO-cookie path only;
      4. `whoami` — a `2xx` whose body is not parseable JSON, on the SSO-cookie
         path only. Required because an SSO reverse proxy commonly answers an
         expired session with `200` plus the IdP login page, and `resp.json()`
         (`_client.py:397`) then raises `JSONDecodeError`, which is neither
         `AuthError` nor `JiraError` — today that escapes to `main`'s catch-all
         as exit 1, outside the exit-2 credential band, and no recovery fires.
      5. `whoami` — a `2xx` whose body **parses** but carries no identity, on the
         SSO-cookie path only. The predicate is one **shared selector**: *the
         first non-empty `str`* among `displayName`, `name`, `emailAddress`,
         `key`, `accountId`. Presence alone is not enough — `{"displayName":
         null}` or `{"name": ""}` satisfies a presence test while
         `_cmd_check`'s truthiness `or` chain still falls through to `as ?` at
         exit 0, which is the failure this site exists to stop. **`_cmd_check`
         uses the identical selector** for its display fallback
         (`jira.py:405-410` reads only the first three, by truthiness, today), so
         `{"displayName": null, "accountId": "abc"}` both passes and displays
         `abc`. Both halves are required: listing a field the raise
         site accepts but `_cmd_check` does not still prints `as ?` at exit 0,
         and omitting `displayName` from the raise site would reject a valid
         `{"displayName": …}` response and open a spurious browser. Without site
         5 at all, an SSO proxy answering an expired session with a parseable
         non-identity body returns **exit 0** — an expired session reported as
         success, worse than a missed recovery.

      `SsoConfigError`, `SsoBrokerNotInstalledError`, the construction-time https
      guard, and `403` stay plain `AuthError` → exit 2 with **no** recapture.
      Because the subclass *is* an `AuthError`, every existing handler and exit
      code is unchanged.

- [x] **AC12 (jar failures are in the contract, without leaking bytes).**
      `from_sso_cookies` reads, parses **and shape-checks** the jar inside the
      guarded block. A list-of-dicts check is **not** sufficient: `filter_jar_to_domains`
      calls `.lstrip()` on `domain` and indexes `c["name"]`, so
      `[{"domain": 1, "name": "sid"}]` raises `AttributeError` and a record
      missing `name` raises `KeyError` — both escaping as exit 1, the very band
      AC12 exists to close. Validate **each record**: `raw` is a `list`, every
      entry a `dict`, `name` / `domain` / `value` present and `str`, **and a
      supplied non-null `path` also `str`** — `_client.py` passes
      `c.get("path") or "/"` straight to `httpx.Cookies.set`, so
      `{"path": 7}` reaches the cookie jar and raises `TypeError` mid-request,
      escaping as exit 1 exactly like the cases above. Map `OSError` / `JSONDecodeError` / `UnicodeDecodeError` / shape
      mismatch to the AC11 type. Today the read at `_client.py:210` sits outside
      the `except credbroker.SsoError` block, and a valid-JSON-wrong-shape jar
      additionally reaches `filter_jar_to_domains` and raises `AttributeError`;
      both escape as exit 1. The raised message is a **fixed** remediation string
      naming only the profile, cause chained via `from exc` and never
      interpolated — a `UnicodeDecodeError`'s text quotes the offending bytes of
      a cookie jar, which `jira.py:798-800` already refuses to echo.

- [x] **AC13 (`_probe` preserves the discriminator).** The probe helper
      constructs the client, calls `client.whoami()` **directly**, and closes it
      in a `finally`. It must not route through `_cmd_check`, which catches
      `AuthError` (`jira.py:399-401`) and returns an `int` — that would swallow
      the subclass at raise sites 3 and 4, the primary expired-session cases.

- [x] **AC14 (automatic path).** On `SsoSessionUnavailable`, `check` calls
      `refresh_sso_session(profile)` and re-probes **once**.
      `SsoProfileNotRegisteredError` yields exit 2 with a remediation addressed
      to the **user** — `ask the user to run: python scripts/jira.py check --register` — with no retry and no registration. Any other recapture
      failure yields exit 2 with no retry. A post-recapture **construction**
      failure is equally terminal: `refresh` shares `_capture` with
      `register` (AC35) and returns 0 whenever the success-URL pattern matched, so
      it can succeed while leaving nothing resolvable. It does **not** delegate to
      the headed interactive path — AC14a fixes `refresh` at
      `headless=True`. The post-recapture probe, not the exit code, is
      the success criterion.

- [x] **AC14a (the automatic path never renders a login page to a human).**
      Automatic refresh may re-establish a session **only without human
      interaction.** If the recapture would require a person to type credentials
      — the IdP session has also expired, so the warm browser profile cannot
      complete the flow silently — the automatic path **aborts** with exit 2 and
      the **`check --register`** remediation — the only first-capture path that
      *attempts* destination attestation — and does **not** leave a login page in
      front of the operator. The qualifier matters: AC32 verifies the destination
      only where derivation succeeds; on **branch 2** (configured sign-in host ==
      `base_url` host, i.e. SP-initiated SAML, the majority topology) derivation
      short-circuits and attests nothing. So `check --register` is strictly better
      than `setup_sso.py`, which attempts no attestation at all — but it is not
      universally attested, and this AC does not claim it is.

      This closes the gap between this spec's own threat analysis and its ACs.
      The spec identifies "a human types credentials into a page whose
      destination the agent could influence" as the single exposure whose blast
      radius leaves the machine. RFC-0084 records that the supported deployment
      cannot enforce a destination-integrity boundary against its own principal.
      Bare `check` nevertheless reached exactly that state whenever the IdP
      session had expired, using destination fields from the agent-writable
      `~/.agentbundle/sso-profiles/<profile>.toml`. Accepting that limitation
      while shipping an automatic headed flow is not a defensible order of
      operations.

      So the harvest surface is removed from the automatic path entirely rather
      than guarded: silent re-auth ships (it is the common case and involves no
      human), interactive capture is reachable **only** from an operator-typed
      command. RFC-0084 accepts the current deployment's lack of a
      same-principal destination boundary. No automated path may render a login
      page; changing that ceiling requires a new proposal with an independently
      bound authorization mechanism.

      **The enforceable engine contract: `refresh` is universally headless.**
      An abort rule alone is unimplementable — `_do_refresh` delegates to
      `_do_register`, which launches `headless=False` and polls for 300 s, so
      there is no state in which the engine can report "this would need a human"
      before a window is already on screen. Therefore `refresh` launches
      `headless=True` and never polls for sign-in: if the warm browser profile
      completes the IdP flow, capture succeeds silently; if it cannot, the launch
      fails with engine exit **`5`**, which `credbroker` maps to
      `SsoInteractionRequiredError` (non-recoverable), and which `check` surfaces
      as exit 2 plus the **`check --register`** remediation without retrying.

      **"Never polls" is too blunt: the contract is a bounded silent-completion
      window.** A warm IdP session still redirects asynchronously, so a zero-wait
      launch would fail flows that would have succeeded. `refresh` therefore waits
      up to **20 s** for the success-URL pattern to appear *unaided* — long enough
      for a redirect chain, far short of a human sign-in — then, if a login page is
      still displayed, closes the headless context and returns `5`. The engine
      distinguishes the two by URL, not by timing out silently.

      `refresh` also carries its **own** spawn timeout, not AC3's 540 s: with no
      human-duration poll its worst case is import + launch + navigation + the
      20 s window + cleanup + margin, so **180 s** — the derivation is AC3's
      per-operation table, which is the single source for all three values.
      Interactive capture belongs solely to `register` / `setup_sso.py`, which
      keep `headless=False`. Added to AC1's taxonomy table and to the
      RFC-0013 erratum, since it changes the verb's contract.

- [x] **AC15 (`check --register`, under the accepted threat profile).**
      `check --register` performs first capture from `sso-config.toml` and then
      completes the check — one command, not two. Accepted on `check` only.

      **Why it ships, having once been withdrawn.** The withdrawal argued that a
      registration flag on the agent's own command surface is reachable by
      prompt injection. Under the accepted profile
      (`credentials.md § Threat model`) that argument does not hold up: a hostile
      same-principal agent can already invoke
      `sso-broker.py register <profile> --login-url …` directly, so the flag
      confers **no capability it did not have**. Removing it amputated the UX
      without closing the path.

      **What the real boundary is.** Not a verb and not a subsystem, but: *does a
      human type credentials into a page whose destination the agent could
      influence?* That catches `--register` **and** an interactive refresh when
      the IdP session has also expired — both harvest the operator's IdP password
      and MFA, which reach far beyond this tool. That is the one exposure in this
      design whose blast radius leaves the machine, and it is the only one that
      earns a control.

      **The control, narrowed to fit.** Integrity-protect the headed-login
      destination policy rather than the whole config or the whole flow.
      RFC-0084 records that the current user-scope installation cannot provide
      that integrity boundary. Everything in `sso-config.toml` remains
      adopter-editable, and the exposure is an accepted limitation rather than
      deferred baseline work.

      AC21 still puts `--register` under the SKILL.md rule that the agent relays
      the command rather than running it, and AC21's negative eval still asserts
      that. That is belt, not the boundary: it reduces accidental invocation by an
      erring agent, which is exactly the threat the accepted profile *does* cover.

- [x] **AC16 (disclosure and record).** Before any recapture, `check` writes one
      stderr line naming the profile. The wording is **path-specific**: on
      `--register` it states that a headed browser will open and names the
      resolved `login_url` host; on the **automatic** path it states that recapture
      is headless, that no browser will be shown, and that the destination comes
      from the engine's stored profile rather than from `sso-config.toml`. The
      automatic notice must not mention a headed browser, because AC14a forbids
      one. The profile and the outcome are
      echoed via `log.info`. **This is not an audit record:** `jira.py:780-783`
      calls `logging.basicConfig` with no `filename` and no handler, so the line
      goes to the stderr of a process the agent spawns and may discard. It makes
      the attempt visible in the invoking session; an unattended
      re-authentication remains repudiable. A durable sink is
      *(deferred: sso-recapture-audit-sink)*. `check` itself writes
      nothing to stdout before the retry probe; inherited stdio means the
      engine's child may write to the shared streams, which is noted rather than
      claimed away.

- [x] **AC17 (exactly one attempt).** `check` invokes recapture at most once per
      process, on either path.

- [x] **AC18 (`--insecure` is honest on both paths).** On the **token** path it
      emits a stderr warning whenever it fires — `docs/CONVENTIONS.md:1197` and
      `:1214` require it and `jira.py:722` is silent today. On the **SSO-cookie**
      path the flag is inert (`from_sso_cookies` hardcodes `_sso_ssl_context()`),
      and it is never forwarded to the engine.

      **Corrected at implementation (2026-08-06): the ignored-notice is *not*
      scoped to `check`.** This AC first said it was, which contradicts the
      *Always do* boundary — "emit a stderr warning whenever `--insecure` fires
      **or is ignored**". Scoped to `check`, `jira.py --insecure whoami` on the
      cookie path would ignore the flag in silence, which is the case the
      boundary exists to prevent. The notice therefore fires on every
      SSO-cookie subcommand, exactly as the token-path warning fires on every
      token-path subcommand.

- [x] **AC19 (blast radius).** No `jira.py` path other than `check` invokes
      recapture. On the token path `check` behaves exactly as today apart from
      AC18's warning. A malformed `sso-config.toml` — non-`https` URL, unknown or
      missing `[sso]` key, over-broad `cookie_domains`, `base_url` host outside
      `cookie_domains`, path-bearing `session_filename`, an AC4-rejected
      `profile`, or a wrong-typed `ttl_hint_minutes` (AC20) — fails at the
      selector with exit 2 and no recapture; `auth_default = "creds"` and an
      absent file run the token path unchanged.

- [x] **AC20 (forwarded-field validation).** `_sso_config.load_sso_config`
      delegates `profile` to `validate_sso_profile` **before any `str()`
      coercion** — `_sso_config.py:155` currently does
      `profile=str(sso["profile"])`, which would turn an int `5` into `"5"` and
      make AC4's non-`str` rejection unreachable from this path — type-checks
      `ttl_hint_minutes` as an integer (`_sso_config.py:162` passes it through
      untyped today despite its `int | None` annotation), and rejects `"`, `\` and **every**
      `U+0000`–`U+001F` / `U+007F` control character (not just `\n` / `\r` /
      `\t` — a TOML source can encode any of them as `\uXXXX`, so the parsed
      value carries a bare control char) in every `[sso]` string field that
      can reach an argv or the engine's profile writer. Control characters matter
      because `validate_https_url` cannot see them — `urlsplit` strips CR/LF
      before parsing (verified by spike) — while `sso-broker.py:308-324`
      interpolates values into `f'{key} = "{value}"'` unescaped, injecting lines
      into the profile store. AC1 removes this exposure from the automatic path;
      AC2's `register` path retains it, which is why the guard lives at load.

- [x] **AC30 (credbroker version floor).** The pip layer **precedes** the
      vendored floor on `sys.path`, so an adopter pinned to `credbroker==0.4.1` (or earlier)
      with atlassian 0.8.0 gets the old library. The failure differs by call
      site, and the guard is scoped to match: `_sso_config.py:85` uses
      `from credbroker import (…)`, so a missing name raises **`ImportError`** —
      not `AttributeError` — inside `load_sso_config`, which `_run`'s handler at
      `jira.py:713` already turns into **exit 2**; and it is unreachable on the
      token path because `load_sso_config` returns `None` at `:80-81` before that
      import. Only `credbroker.refresh_sso_session`, a module attribute
      referenced in `jira.py`, produces the uncaught-`AttributeError` exit-1
      path, and only on `check` + sso-cookie.
      So the guard is a feature-detect (`hasattr(credbroker,
      "refresh_sso_session")`) placed **in the sso-cookie branch of `_run`,
      before `_cmd_check_sso`** — never in the shared bootstrap, which would
      break every token-path subcommand and contradict AC19.

      **Corrected at implementation (2026-08-06): the guard has two sites, not
      one, and the second is in the shared bootstrap.** The analysis above is
      right that the loader's `ImportError` already lands on exit 2 — but it
      lands there carrying the raw `cannot import name … from 'credbroker'
      (/path/to/site-packages/…)`, with no upgrade command, and it fires
      *first*: a real 0.4.1 install never reaches the feature-detect, because
      `_sso_config.py` imports `validate_sso_profile` by name. So `_run` also
      catches a credbroker `ImportError` around `_select_auth_path()` and routes
      it to the same remediation. That does not gate the token path: the loader
      returns before its credbroker import when `auth_default` is absent or
      `creds`, so no token-path subcommand can reach the handler. Both sites are
      tested, the second against a stub built from the real module minus every
      0.5.0 addition. It exits 2 with an
      upgrade remediation naming the required version. `requirements.txt` pins
      `credbroker>=0.5.0` in **both** consuming skills (`confluence-crawler` is
      at `>=0.1.0` today and inherits the mirrored files); a test asserts the
      guard fires against a stub 0.4.1 module.

- [x] **AC31 (`_run` routing is pinned).** Today `from_sso_cookies` is called at
      `jira.py:719` for **every** subcommand before dispatch, and its `AuthError`
      is caught at `:723` — so AC11 sites 1–2 raise from a block shared by all
      commands, and the obvious implementation would violate AC19. `_run` routes
      `auth_path == "sso-cookie" and args.command == "check"` to a dedicated
      handler **before** the shared construction at `:717-725`; every other
      command keeps today's construction path byte-for-byte. A test asserts the
      recapture stub is never called for `whoami` or `get-issue`.

- [x] **AC32 (server-attested destination on `--register`).** The automatic
      path already accepts no destination (AC1). `--register` does, so it
      attests it against the instance itself rather than trusting the config.

      **Mechanism — a vendor-agnostic strategy chain, not a Jira probe.**
      `credbroker` owns
      `derive_sso_destination(base_url, *, strategies: Sequence[str] = ()) -> str | None`
      — the keying parameter is explicit, because
      the broker is meant to serve any vendor with this shape (an on-prem
      Confluent admin console, any corporate tool behind SSO), not just
      Atlassian. It tries, in order, and returns the first **origin** it
      resolves — `scheme://host:port`, the port always explicit and an IPv6 host
      bracketed:

      1. **RFC 9728 — OAuth 2.0 Protected Resource Metadata.** Unauthenticated
         request → `401` carrying `WWW-Authenticate: … resource_metadata="…"` →
         fetch `/.well-known/oauth-protected-resource` → `authorization_servers`
         → fetch that AS's metadata → `authorization_endpoint`. The modern
         standard; adopted by MCP.
      2. **OIDC Discovery / RFC 8414.** `GET {base_url}/.well-known/openid-configuration`
         → `authorization_endpoint`. Older, far more widely deployed today.
      3. **Vendor probe (Atlassian/Seraph).** `GET {base_url}/login.jsp` with
         redirects **not** followed and no cookies → `302` whose `Location` is
         the IdP authorization URL. **Verified by live spike 2026-08-05:**
         `GET https://jira.atlassian.com/login.jsp` → `302`,
         `Location: https://auth.atlassian.com/authorize?…`. Registered as a
         named strategy in a module-level registry, requested by the caller as
         `strategies=("atlassian-seraph",)`, so `confluence-crawler` and
         `bitbucket` opt in (same Seraph framework) and a non-Atlassian consumer
         never runs it. Default `strategies=()` runs tiers 1–2 only.

      **The comparison lives in `jira.py`'s `--register` path, not in
      `register_sso_session`.** So `setup_sso.py` and `confluence-crawler` —
      which AC2 refactors onto the same function — get **no** attestation; only
      `check --register` attests. The `credbroker` placement buys reusability,
      not coverage. AC32's mismatch and cannot-derive tests therefore drive
      `check --register`, and `setup_sso.py` is documented as the unattested
      operator escape (AC23).
      4. **None** → cannot-derive.

      Only the **scheme and authority** — host *and port* — are compared; every
      tier's URL carries per-request `state` / `SAMLRequest` / `nonce` values
      that change on each call. (Implementation note, 2026-08-06: an earlier
      draft said "scheme+host", which would have accepted a derived
      `https://idp:8443` against a configured `https://idp:9999` — a different
      origin, and often a different service.)

      The same spike recorded that `jira.atlassian.com` answers its REST `401`
      with the **legacy** `WWW-Authenticate: OAuth realm="…"` form, *not* RFC
      9728's `resource_metadata` — so tier 1 is the right thing to try first and
      the wrong thing to depend on. SAML-only SPs expose no discovery at all
      (their SP metadata names the SP, never the IdP), which is why tiers 3 and 4
      exist.

      **This is defence in depth, not the control.** It closes
      *`login_url`-poisoned-alone*. It does **not** close config poisoning,
      because `base_url` — the derivation target — lives in the same
      agent-writable file: one write changes both, the attacker serves the `302`
      themselves, and the comparison passes. AWS's equivalent works only because
      its host suffix is hardcoded to `*.amazonaws.com`; there is no comparable
      invariant here, since everything we could compare against is also in the
      file. Consent for `--register` therefore rests on AC15 (operator-typed),
      not on this. `credentials.md` states the same limit (AC22).

      Comparison is **topology-aware**, not one string — plain host equality
      would refuse the *majority* Jira DC configuration. In SP-initiated SAML
      (the default for most DC SSO plugins) `login_url` sits on the **SP** host
      (`{base_url}/plugins/servlet/samlsso`) while tier 3's `302` names the
      **IdP** host. Accept when the derived host equals the `login_url` host
      (**branch 1**) **or** the `login_url` host equals the `base_url` host
      (**branch 2**).

      **Branch 2 attests nothing, and that is recorded rather than dressed up.**
      `require_host_in_cookie_domains` compares a host against the
      *config-supplied* `cookie_domains` and is called on the request base host
      (`_client.py:203`), never on `login_url` — so an attacker writing
      `base_url`, `cookie_domains` and `login_url` to the same host satisfies
      branch 2, derivation is never consulted, and within-host path/query is
      unconstrained (an on-host open redirector passes). Since branch 2 is the
      majority topology, **derivation is effective only on IdP-host topologies.**
      This is accepted rather than fixed: requiring derivation in branch 2 would
      refuse every SSO-with-local-fallback adopter, and derivation is explicitly
      not the control — AC15 is. RFC-0084 closes a standalone branch-2 remedy as
      part of the accepted same-principal limitation.

      **Branch 2 is evaluated first and short-circuits.** Where `login_url`'s host
      equals `base_url`'s host, **no derivation request is made** and the
      cannot-derive outcome does not apply — otherwise `setup_sso.py` would
      refuse the majority topology whenever `/login.jsp` returns 200, defeating
      the one-command objective. Derivation runs only when the hosts differ.

      Outcomes: **accept** → proceed; **mismatch** → exit 2, **no browser**,
      naming both hosts *and* the `setup_sso.py` escape — which performs **no**
      attestation, and is safe only because it too is operator-typed, the same
      basis as AC15 (a refusal with no remedy gets worked around by editing the
      config); **cannot derive** → exit 2
      naming `setup_sso.py`. It **never** falls back to the configured value.

      **Derivation is bounded — it is an outbound fetch on the credential path.**
      `credbroker` has no dependencies, so this is `urllib`, which follows
      redirects, honours `file://` and `ftp://`, and has no default timeout;
      tier 1 fetches a URL taken from a *response header* and then a second from
      that document, i.e. two attacker-influenceable targets. Required:
      `https` only at every hop (reject `http`/`file`/`ftp`, including inside
      `resource_metadata` and `authorization_servers`); redirects **not**
      followed, hop cap 0; 5 s connect + 5 s read and a ≤15 s total derivation
      budget; a 64 KiB body cap before `json.loads`; strict certificate
      verification that never honours `--insecure` and never reuses the token
      path's SSL context; no `Authorization`, `Cookie`, or proxy-auth header on
      any derivation request.

      **Plus an address bound, added at implementation (2026-08-06) — this AC
      first enumerated every constraint except the one that matters most.**
      Bounding the scheme, the hops and the clock still leaves the *target* free:
      a hostile or compromised instance can answer the first probe with a
      `resource_metadata` URL naming `https://169.254.169.254/…`, loopback, or
      any corporate-LAN host, and the operator's machine issues the request. So
      every hop whose origin is **not** the configured `base_url` origin is
      refused when the host resolves to a loopback, link-local, unique-local,
      RFC 1918, reserved, multicast or unspecified address — checked against the
      *resolved* address, not the literal.

      The exemption is keyed to the **origin**, not to "the first request":
      RFC 9728 puts `/.well-known/oauth-protected-resource` on the resource
      server itself, so tier 1's second hop is normally the same origin as its
      first, and a first-request-only exemption would silently kill tier 1 for
      every internally-hosted instance — the deployment this broker exists to
      serve. A resolver failure is refused rather than allowed, because
      `_derivation_opener` installs the environment's proxies and a proxy
      resolves the hostname itself. **Named limit:** it resolves and then
      connects, so it does not close DNS rebinding; a pinned-address connection
      would, and `urllib` does not offer one. The same bounds are recorded in
      `credentials.md`'s derivation table.

      **Named degradation, verified for the Atlassian tier.** Derivation is
      configuration-dependent
      and this is a *material* limitation, not a caveat: `/secure/Dashboard.jspa`
      returned `200`, confirming JRASERVER-66554 — SAML redirection fires only
      from `login.jsp`, never from the base URL or dashboard, so deriving from
      `base_url` (the design's first draft) does **not** work. `login.jsp` itself
      returns `302` only in forced-SSO mode; in SSO-with-local-fallback it
      returns `200` with a sign-in button and no `Location`. Those adopters land
      on the cannot-derive branch and register via `setup_sso.py`.

      **The engine is directly invokable, and no control here closes that.**
      `~/.agentbundle/bin/sso-broker.py` is an executable on disk; any process
      running as the operator — including the agent, with shell access — can call
      `sso-broker.py register <profile> --login-url https://evil…` with no
      `credbroker`, no AC15, no AC31 and no derivation in the path. Destination
      pinning is a property of the **library API**, not of the system. The
      *Never do* rules are constraints on skill authors, not on the agent. Stated
      so no reader mistakes the library boundary for a system boundary.

      **Threat model, stated plainly.** `sso-config.toml` is a skill-tree file
      the agent can edit, and `~/.agentbundle/sso-profiles/<profile>.toml` is
      protected by file permissions against *other users*, not against the
      principal the agent runs as. Attestation closes config poisoning **only
      where derivation succeeds**; where it does not, first-run is
      operator-driven and the agent-reachable path is closed by refusing rather
      than by trusting. A trust-on-first-use record was designed and rejected:
      its baseline would be written after the poisoned registration, so the
      attacker's host would become the reference.

- [x] **AC33 (declare the pack dependency, don't imply it).** Every pack
      shipping a `credentialed: true` skill declares
      `[[pack.dependencies.required]]` on `credential-brokers` — **`atlassian`,
      `figma`, `linear`** — i.e. every credentialed pack *other than the broker pack*
      itself, which ships `credential-setup` (`credentialed: true`) and cannot
      depend on itself. `github` is excluded because it shells out to `gh`, which
      owns its own credential chain, and declares no `credentialed:` frontmatter.
      The literal block, per `pack.schema.json:143` (`catalogue` / `pack` /
      `version` required, `additionalProperties: false`):

      ```toml
      [[pack.dependencies.required]]
      catalogue = "agent-ready-repo"
      pack = "credential-brokers"
      version = "^0.3"        # atlassian; figma and linear use "^0.2"
      ```

      `install.py:493-505` gates required dependencies **before any write**,
      resolving against the union of repo + user state; five packs already use the
      mechanism but no credentialed pack does, so today
      `agentbundle install atlassian --scope user` succeeds while the credbroker
      floor and `sso-broker.py` are absent, failing at runtime with no
      remediation. Ranges are per-need — the grammar is caret-minor and `^0.2` is
      satisfied by `0.3.0` (`install.py:4374-4381` — `^X.Y` means
      `>= X.Y.0, < (X+1).0.0`), so `atlassian` takes `^0.3` (it needs AC6b's exit-4
      engine) while `figma` and `linear` take `^0.2`.

      **Breaking-change note:** the gate resolves installed *packs*, not module
      importability, so an adopter who `pip install credbroker`-ed without
      installing the pack has a working `creds` install today and will be refused
      at upgrade. The gate message names the fix. This makes `figma` and `linear`
      minor bumps.

      **Named limit, found at implementation (2026-08-06): the gate is
      scope-blind.** `validate_dependencies_required` resolves the union of repo
      and user state and discards scope, so a **repo**-scoped
      `credential-brokers` satisfies a **user**-scope install of a credentialed
      pack — while the skill resolves the broker only under `~/.agentbundle/`.
      The declaration is still strictly better than none (it catches the common
      case, and `credential-brokers` defaults to user scope), and the
      consequence of the gap is the pre-declaration behaviour: exit 2 with
      "install the credential-brokers pack". Closing it needs a scope qualifier
      in the dependency entry, which `pack.schema.json` forbids today
      (`additionalProperties: false`), so it is a schema change with its own
      review rather than a ride-along.
      *(deferred: pack-dependency-scope-qualifier)*

- [x] **AC34 (engine-change governance — RFC-0035, amended).** The changeset
      edits `packs/credential-brokers/**` (AC6, AC6a, AC6b, AC35) and
      `packages/agentbundle/agentbundle/catalogue_tooling/self_host_windows.py`
      (AC26), both protected by `tools/lint-catalogue-curation-guard.py` —
      `CREDBROKER_PREFIX` is the whole pack with **no carve-out**, and the engine
      prefix carves out only `build/recipes/` and `/tests/`. `build-check.yml:478`
      runs it against `origin/main`, so **this cannot merge** without an
      `Engine-Change-RFC:` trailer on its commits. `has_exemption` is a substring
      check validating neither the RFC's existence nor its scope, so the trailer
      is a governance speed bump, not a resolver.

      Commits carry `Engine-Change-RFC: RFC-0035` — the RFC that introduced
      `sso-broker.py` and owns the `sso-cookie` broker. **No new RFC.**

      **The instrument is an Approver-signed `## Errata` entry, not an
      amendment.** Verified: RFC-0035 is `Status: Accepted` → Frozen, and already
      carries `## Errata` with four signed entries and **no** `## Amendments`
      section; the `new-rfc` convention reserves amendments for in-flight Open
      RFCs and states the two headings never coexist. The entry follows the
      existing form — `- **YYYY-MM-DD (Approver: <handle>) — …**` — recording
      (i) `refresh`'s not-registered exit `3` → `4` (AC6b), (ii) the
      `register --ephemeral` CLI-surface addition plus `refresh`'s rejection of
      connection arguments (AC35), and (iii) **`refresh` becoming headless with a
      bounded 20 s silent-completion window and the new exit `5`** (AC14a) — the
      break that turns a previously-prompting `refresh` into a fast failure. The RFC body is not edited.

      **Settled 2026-08-05.** The Approver signed the erratum (`eugenelim`) and
      chose the erratum alone — **no ADR**. Recorded in the entry itself: it
      narrows an existing non-goal and corrects engine behaviour this RFC already
      governs, rather than reversing the decision. **Two** entries are appended, because two RFCs are
      implicated: RFC-0035's `## Errata` records the narrowing of its
      engine-unchanged **non-goal**, and **RFC-0013 § Subcommands owns the verb
      table and exit semantics actually being changed** — `refresh` is no longer
      "equivalent to `register`" — so a companion Approver-signed entry lands
      there too. Neither RFC body is edited and no `## Amendments` section is
      introduced. Verification is the AC34 Testing Strategy row.

- [x] **AC35 (`register` captures in an ephemeral context, and still seeds the
      persistent one).** `_do_refresh` currently *is* `_do_register`
      (`sso-broker.py:583` → `return _do_register(profile, args)`), with
      `launch_persistent_context(user_data_dir=…/browser-state/<profile>)`
      hardcoded — so there is no branch to make ephemeral. The engine splits into
      `_capture(profile, args, *, persist: bool, headless: bool)` — both flags,
      because persistence and headedness vary independently:

      | Caller | `persist` | `headless` |
      |---|---|---|
      | `register` (operator, default) | `True` | `False` |
      | `register --ephemeral` (via `register_sso_session`) | `False` | `False` |
      | the AC35 seeding launch | `True` | `True` |
      | `refresh` (AC14a) | `True` | `True` |

      `register` selects
      `persist=False` **only when `--ephemeral` is passed** — the verb's default
      stays `True`, so a direct operator invocation is unchanged — and `refresh`
      is always `persist=True` **and always `headless=True`** per AC14a — it never
      polls for sign-in, so it cannot put a login page in front of an operator.
      The flag is added to AC2's argv contract.

      **The adopter-visible break is the persistence change, not the flag.** A
      caller relying on `register` leaving a reusable `browser-state/<profile>`
      now gets a *seeded* profile rather than the capture context itself; the
      errata name that, not the flag. Asserted in `test_sso_broker_verbs.py` — **not** the skill suite,
      which cannot observe a Playwright call inside a subprocessed engine.

      Note this interacts with AC14a: because `refresh` is headless, the seeded
      profile is what lets the *first* automatic refresh complete silently. If
      seeding fails, that refresh returns `5` and the operator re-registers — it
      does **not** open a browser.

      **The ephemeral capture must seed the persistent profile.**
      `launch_persistent_context` takes **no** `storage_state` argument — a
      persistent context owns its own state directory — so seeding is: export
      `storage_state` from the ephemeral context, then launch a second,
      *headless* persistent context on `browser-state/<profile>` and
      `add_cookies(state["cookies"])`. **`localStorage` / `sessionStorage` cannot
      be seeded this way**; if the IdP session depends on either, the seed
      silently fails and the first automatic `refresh` requires an operator. That
      is a named limitation, not a solved case — no probe has been run against
      Playwright's persistent-context model, unlike every other mechanism claim
      in this spec. Otherwise the first automatic `refresh` after first capture
      finds no usable browser session and — because `refresh` is headless with a
      bounded window (AC14a) — returns exit `5` rather than opening a browser, so
      the operator must re-register. That is a UX cost, not a security exposure:
      the automatic path never renders a login page.

      **Named non-control:** on a domain-joined machine where the IdP uses
      Negotiate/Kerberos, IWA, or a machine certificate, an ephemeral context
      still authenticates silently from the OS credential store, so no visible
      sign-in occurs. AC35 is a confirmation surface only where the IdP relies
      on a browser-resident session. This is recorded rather than assumed —
      the survey lists it as an open known-unknown.

      **`refresh` also stops accepting a destination.** `sso-broker.py:570-581`
      currently back-fills `args.login_url` from the stored table only `if not
      args.login_url` — so `--login-url` on `refresh` is honoured today. The verb
      now **rejects** any connection argument (`--login-url`,
      `--success-url-pattern`, `--cookie-domain`, `--validation-endpoint`,
      `--session-filename`, `--ttl-hint-minutes`) with exit 3; destinations come
      only from the stored profile. Asserted in `test_sso_broker_verbs.py`.
      Without this, AC1's "enforced by the signature" holds at the library layer
      only — which the Objective now says explicitly.

      These engine CLI-surface changes are a second reason
      `packs/credential-brokers` bumps.

### Docs

- [x] **AC21 (SKILL.md matches behavior, and still lints).** The phrases
      `catalogue_tooling/lint.py:439-459` pins for `auth: sso-cookie` **and**
      `auth-fallback: creds` (jira declares both) survive in the
      `### Security rules (non-negotiable)` section, matched after
      `_cs_normalize_whitespace` — the pinned clause is line-wrapped in the file
      today (`SKILL.md:106-107`), so verification is `make build-check`, never a
      single-line literal grep. The **unpinned** lead-in sentence is re-scoped
      (it currently tells the agent to hand every SSO recovery to the user, which
      the new `check` contradicts); the pinned clause is not reworded. The
      carve-out declares its own boundary — applies to `jira.py check` only; the
      agent never passes `--register` itself and never invokes `setup_sso.py` or
      `credential-setup` on the user's behalf. `check --register` is the
      **canonical** first-run path, and AC14's remediation, AC23's how-to, the
      plan's failure matrix and this section all name it. `setup_sso.py` is
      reserved for exactly two cases and named only there: scripted pre-bake, and
      AC32's mismatch / cannot-derive escape where attestation is unavailable —
      routing an ordinary unregistered first run through it would bypass AC32's
      attestation even when derivation would have succeeded. And **three** negative eval cases are
      added: (i) the agent still refuses to run `credential-setup` or
      `setup_sso.py`; (ii) driven by a prompt in which `check` has already emitted
      AC14's `ask the user to run: python scripts/jira.py check --register`
      remediation, the agent **relays that command as text and does not invoke it
      via Bash** — the assertion AC15's consent story actually depends on, and
      which no existing eval covers (`evals.json:188-199` is token-path scoped) — the latter is the helper the pinned phrase actually names,
      and that phrase's literal meaning is now false for `jira.py check`, so its
      amendment is recorded as a deferred slug rather than left unremarked. Additionally: a `login_url`
      agent pre-flight rule mirroring the `JIRA_BASE_URL` rule
      (`SKILL.md:81-91`); the exit-code table's exit-2 row split by auth path;
      and Step 1 stating that bare `check` **never** blocks for browser sign-in
      (AC14a: `refresh` is headless, worst case 180 s) while `check --register`
      does, with an
      invocation budget derived from AC3's **540 s** backstop — the post-margin
      value including AC35's seeding launch, not the 420 s pre-margin sum — plus two worst-case
      probes (`MAX_RETRIES` × `DEFAULT_TIMEOUT_S` plus backoff).

- [x] **AC22 (architecture page).** `docs/architecture/credentials.md` carries a
      `## The sso-cookie broker` section covering the engine/library split, the
      consumer API, destination pinning, the confinement controls, and the
      auto-recovery contract; the `auth:` paragraph routes to it instead of
      deflecting to the spec; and *Where to read next* links RFC-0035, ADR-0026
      and this spec. The destination-pinning paragraph states the AC32 trust
      boundary verbatim — the signature blocks implementer error, **not** an
      agent that can edit `sso-config.toml` — so the durable architecture doc
      does not outlive this spec carrying an unqualified security claim. The
      shipped behavior matches that page.

- [x] **AC36 (the authoring how-to stops teaching the banned pattern).**
      `guides/credential-brokers/how-to/add-a-credentialed-skill.md:139-151`
      instructs new `auth: sso-cookie` skills to build
      `Path.home() / ".agentbundle" / "bin" / "sso-broker.py"` and
      `subprocess.run([...], env={**os.environ})` — verbatim this spec's first
      *Never do*, and the scaffold every future SSO skill copies. It is replaced
      with `credbroker.load_sso_cookies(profile)` and the recapture verbs, and
      its re-auth exit-code note (`:220`) records AC6b's `4` alongside `2`.

- [x] **AC23 (adopter how-to).**
      `guides/atlassian/how-to/authenticate-jira-confluence-with-sso-cookies.md`
      states that `check` self-heals an expired session, that **`check --register`
      is the ordinary one-command first run** and the only path that attests the
      destination (AC32), that `setup_sso.py` is limited to scripted pre-bake and
      to the AC32 mismatch / cannot-derive escape where attestation is
      unavailable, that a **Claude Code** adopter may add a
      user-scope deny rule per AC15 — with the literal rule text, the reason it
      must live in `~/.claude/settings.json` rather than the repo, and an
      explicit statement that `kiro-ide`, `codex`, `copilot`, `cursor` and
      `gemini` have no equivalent per-command control. The how-to must describe
      that rule as **belt-only: protection against accidental invocation, not a
      boundary.** It does not put first capture out of agent reach, because an
      agent with shell access can invoke `~/.agentbundle/bin/sso-broker.py
      register` directly, bypassing every command-level rule. Only privilege
      separation would support an out-of-reach claim, and none is shipped. Also
      the profile grammar constraint.

- [x] **AC24 (changelog + API reference).** `docs/product/changelog.md` gains
      `## [credbroker][0.5.0]`, `## [atlassian][0.8.0]`,
      `## [credential-brokers][0.3.0]`, `## [figma][0.3.0]` and
      `## [linear][0.2.0]` — each `— <YYYY-MM-DD>` in the file's existing heading
      form. The bodies name the two adopter-visible breaks: the engine's exit-`3`→`4`
      change (AC6b), the **new `refresh` contract** — headless, with a bounded
      silent-completion window and a new exit `5`, so a `refresh` that previously
      prompted now fails fast (AC14a) — `refresh`'s rejection of connection
      arguments and `register`'s persistence change (AC35), and AC33's new install
      gate,
      and `guides/credential-brokers/reference/credbroker-sso-api.md` documents
      **all four** new `credbroker`
      functions alongside the existing SSO entries — `validate_sso_profile`,
      `refresh_sso_session`, `register_sso_session` and `derive_sso_destination`,
      the last of which AC32 requires be publicly exported from
      `credbroker/__init__.py` on the same additive-compatibility basis as the
      other three.

      **Corrected at implementation (2026-08-06):** this AC first named
      `guides/_shared/reference/`. There are no existing SSO entries there to
      sit alongside — the credbroker guides live in the owning pack's subtree,
      which is also what `AGENTS.md` § Guide trees routes to ("pack-specific in
      `guides/<pack>/{quadrant}/`"). The page landed under
      `guides/credential-brokers/reference/` and is indexed in that README.

- [x] **AC25 (deferred work recorded, with its constraint).**
      `workspace.toml [backlog].open` carries a slug per *Deferred* entry. The
      `pack-config-catalogue-sso-defaults` entry additionally records the
      destination-pinning constraint this spec discovered: a projected
      `~/.agentbundle/<pack>/defaults.toml` is **not** trusted merely because the
      installer wrote it — if it can supply `auth_default` or a sign-in
      destination it becomes a second adopter-writable source for an automated
      launch, so the addendum must keep the automatic path pinned to
      engine-written state exactly as AC1 does.

### Tests and release

- [x] **AC26 (credbroker suites, and they run on Windows).** `packages/credbroker/tests/unit/`
      covers AC1–AC5, AC10 and AC32 (the last in `test_sso_derivation.py`) with a
      **fake broker executable** in `tmp_path`,
      giving real argv, real exit codes and no browser. The single test seam is a
      redirected home: `monkeypatch.setenv` for **both** `HOME` and `USERPROFILE`
      — `Path.home()` reads `USERPROFILE` on Windows — following
      `test_sso_broker_verbs.py:69-77`, which additionally rebinds the engine
      module's `_AGENTBUNDLE_HOME` because `sso-broker.py:106` computes it at
      **import** time while credbroker's `_broker_path()` resolves at **call**
      time (verified by spike). `packages/credbroker`'s suite is added to
      `self_host_windows.py`'s parity list so the Windows kill arm is actually
      exercised on Windows; until that run is green the `taskkill` arm is a
      named limitation, not a verified control.

- [x] **AC27 (jira skill suite).** A new
      `packs/atlassian/tests/skills/jira/test_check_sso_login.py` covers
      AC11–AC20. It lives at the pack test boundary rather than under `.apm/`
      (ADR-0071 — `.apm/` is the runtime export boundary, so a suite there
      ships into every adopter's tree), and therefore resolves the skill by an
      absolute path from the repo root. It imports via
      `sys.path.insert(0, <skill root>)` +
      `import scripts.jira` — flat `import jira` raises `ImportError: attempted
      relative import with no known parent package` because the bootstrap block
      at `jira.py:54` is gated on `__spec__ is None` while the relative imports
      below it are unconditional. It reaches **every** symbol through `scripts.*`,
      never a flat `import _client` / `import _sso_config`: **verified by spike
      that `flat._client.AuthError is scripts._client.AuthError` → `False`**, so
      `jira.py`'s `except SsoSessionUnavailable` — bound to the `scripts.` copy —
      would not catch an exception raised from the flat copy, and sibling suites
      in the same pytest session load the flat copies. It drives the SSO path by
      pointing `scripts._sso_config._DEFAULT_CONFIG_PATH` at a `tmp_path` config
      (verified by spike to route the real loader to `sso-cookie`), not by
      patching `_select_auth_path`, which would bypass the loader AC19 verifies.
      It stubs the two `credbroker` recapture functions at the `scripts.jira`
      binding to assert call count, arguments, and that no destination reaches
      the refresh call. Wired into `.github/workflows/build-check.yml` and
      `self_host_windows.py`.

- [x] **AC28 (existing suites green).** `test_sso_config.py`,
      `test_sso_client.py`, `test_setup_sso.py`, `test_auth_selector.py` and
      `test_exit_codes.py` pass in **both** skills' `scripts/`;
      `python tools/test-lint-sso-config.py` passes; `pytest packages/credbroker`
      passes; `make build-check` passes **with SAST enabled** — the change adds
      subprocess spawning on the credential path, which is what the SAST leg
      exists to inspect.

      **Release-ordering precondition, found at implementation (2026-08-06) and
      not anticipated here.** The SCA leg runs
      `pip-audit -r <requirements.txt>` over every skill's requirements file, and
      `pip-audit` resolves each pin **against PyPI**. AC30's
      `credbroker>=0.5.0` could not resolve until `credbroker` 0.5.0 was
      published. That originally produced `Could not find a version that
      satisfies the requirement credbroker>=0.5.0` for both consumers.
      CredBroker is now at 0.6.0, both consuming skills retain the `>=0.5.0`
      floor, and the full build gate passes without weakening the SCA input.

- [x] **AC29 (version bump lands last).** After code, tests and docs are settled:
      `packages/credbroker` `[project].version` → `0.5.0` (**minor** — new public
      API, and the engine now rejects input it previously accepted);
      `packs/atlassian` → `0.8.0`, `packs/credential-brokers` → `0.3.0`,
      `packs/figma` → `0.3.0`, `packs/linear` → `0.2.0` — each `[pack].version`
      **plus that pack's `.claude-plugin/plugin.json`**, because
      `catalogue_tooling/lint.py:1252-1258` fails on any mismatch between the
      two; then `make build-self` regenerates
      `.claude-plugin/marketplace.json`, `.agentbundle/bin/sso-broker.py`, and the
      `.agentbundle/lib/credbroker/` + `packs/credential-brokers/.apm/user-libs/credbroker/`
      projections. `[pack.adapter-contract] version` is unchanged.

## Testing Strategy

| AC | Mode | Mechanism |
|---|---|---|
| AC1–AC5, AC10 | TDD | `packages/credbroker/tests/unit/` — fake broker executable, dual-env home redirect, real subprocess. Type-checked by `tools/lint-mypy.py`. |
| AC3 (tree kill) | TDD | POSIX: a fake broker that forks a grandchild; assert no survivors after timeout (spiked green). Windows: asserted on the parity runner per AC26. |
| AC6–AC9 | TDD | `test_sso_broker_verbs.py` — its `importlib` harness (`:24-41`) loads the engine from its real path; drive each verb per vector, assert exit 3 **and** stderr text, plus the `--` escape case. |
| AC11–AC20 | TDD | `test_check_sso_login.py` per AC27. |
| AC30, AC31 | TDD | `test_check_sso_login.py` per AC27 — version-floor guard against a stub 0.4.1 module; recapture stub never called for `whoami` / `get-issue`. |
| AC33 | Goal-based | fixture install of `atlassian` / `figma` / `linear` with and without `credential-brokers`; grep the three `[[pack.dependencies.required]]` blocks. |
| AC36 | Goal-based | grep the authoring how-to for `credbroker.load_sso_cookies` and the **absence** of `subprocess` / a hand-built broker path. |
| AC32 | TDD | `packages/credbroker/tests/unit/test_sso_derivation.py` — a fake resource server per tier, plus bounds assertions: non-`https` at any hop rejected, redirect not followed, connect/read timeouts, ≤15 s budget, 64 KiB cap, no auth headers on the wire. |
| AC35 | TDD | `test_sso_broker_verbs.py` — `register` ephemeral / `refresh` persistent; `refresh` rejects every connection argument; the seeding step. |
| AC34 | Goal-based | `git log --format=%B` on the branch contains `Engine-Change-RFC:`; grep **both** RFC-0035's and RFC-0013's `## Errata` for the `2026-08-05 (Approver: eugenelim)` entries; confirm neither file has an `## Amendments` heading. |
| AC21 | Goal-based | `make build-check` (runs the normalized pinned-phrase lint); all three negative eval cases in `evals.json`. |
| AC22–AC25 | Goal-based | grep the new heading + anchor in `credentials.md`; grep `--register` in the how-to; grep both bracketed changelog headings; grep all four function names in the reference guide; grep each slug in `workspace.toml`; `lint-spec-status.py --root .`. |
| AC26, AC27 | Goal-based | grep the new filenames in `build-check.yml` and `self_host_windows.py`. |
| AC28 | Goal-based | the plan's canonical command block. |
| AC29 | Goal-based | `make build-self` then `make build-check` (drift-gated); version grep across every site. |
| whole change | Visual / manual QA | `python scripts/jira.py check` against the shipped `sso-config.toml` (`auth_default = "creds"`) — token path untouched, no browser. Then `--insecure check` on the token path to observe AC18's warning (`--insecure` is global and precedes the subcommand). Observed stdout, stderr and exit code recorded in [`manual-qa.md`](./manual-qa.md), together with an SSO-path end-to-end run against the real engine and an explicit list of what the session did not exercise. |

**Named limitation.** A live corporate SSO sign-in is not reachable in this loop
— no Data Center instance and no identity provider. The fake-broker rung proves
argv, exit-code routing, destination pinning, timeout and retry bounds; it does
not prove what Chromium emits during a real redirect chain, nor Seraph's actual
status codes. AC4's Windows device-name behavior and AC3's `taskkill` arm are
reasoned from Win32 semantics and are only verified once AC26's parity run is
green.

## Assumptions

Every entry was established by reading source or executing a probe on
2026-08-05, not recalled.

- `_do_refresh` with no connection arguments reads the destination fields from
  the stored profile TOML and returns `3` when the profile is absent — this is
  what makes destination pinning possible. (source: `sso-broker.py` `_do_refresh`)
- `re.match` admits a trailing newline where `re.fullmatch` does not; `CON` and
  `NUL` satisfy the grammar. (source: executed spike)
- `sso-broker get-cookies -- -x` parses `profile="-x"` successfully, while bare
  `-x` is `SystemExit(2)` from argparse. (source: executed spike)
- `flat._client.AuthError is scripts._client.AuthError` → `False`. (source: executed spike)
- Patching `_DEFAULT_CONFIG_PATH` routes the real loader to the SSO-cookie path,
  and `profile = "../../../../tmp/pwn"` is **accepted today**. (source: executed spike)
- `start_new_session=True` + `os.killpg` removes the grandchild on POSIX;
  `os.killpg` is absent on Windows and `Path.home()` reads `USERPROFILE` there.
  (source: executed spike + `workspace_mcp.py:1069-1092`)
- `_cmd_check` catches `AuthError` and returns an `int`, so routing the probe
  through it would swallow the typed subclass. (source: `jira.py:396-404`)
- The probe path resolves the engine through `credbroker._sso._broker_path()`,
  not any skill-side resolver. (source: `_client.py:204` → `_sso.py:100`)
- agentbundle's knowledge of credbroker is a **file-copy** relationship
  (`build/user_libs.py` vendors the package source to three targets), never an
  API one — so new credbroker functions add no agentbundle coupling.
  (source: `build/user_libs.py:1-17,66-67`)
- `packs/credential-brokers` **is** bumped to 0.3.0. The initial no-bump call
  followed the crash-fix precedent (7 of the last 8 `sso-broker.py` commits did
  not bump), but AC6b changes an exit code and AC35 changes the engine CLI
  surface — both observable contract changes. (source: git history; user
  confirmation 2026-08-05, reversed same day on the AC6b finding)
- No TTY gate — it fails closed in exactly the agent-driven case this spec
  serves; destination pinning replaces it. (source: user confirmation 2026-08-05)

## Risks

- **Concurrent browser launches remain undefined.** Two processes can still
  collide on Chromium's singleton lock in the shared
  `browser-state/<profile>` directory. Jar materialisation ordering is no
  longer part of that risk: `sso-store-transition-serialization` serialises
  load plus materialisation under the per-profile store-transition lock.
  `sso-broker-register-concurrency` retains the distinct browser-launch work.
- **The Windows tree kill is reasoned, not executed**, until AC26's parity run.
  If disproved, the fallback leaves the Chromium grandchild alive.
- **The persistent browser profile becomes an agent-triggered credential.**
  `~/.agentbundle/browser-state/<profile>` holds a standing, silently-replayable
  corporate SSO session — that is *why* the sub-second auto-SSO happens, and this
  change converts replaying it from operator-triggered to agent-triggered. The
  `sso-broker-at-rest-minimisation` slug covers the directory mode and the
  unfiltered jar, not its lifetime. *(deferred: browser-state-lifetime)*
- **The typed subclass could over-narrow.** If a real expired-DC-session shape is
  none of AC11's five sites, recovery silently never fires. Mitigation: tests
  assert each site individually rather than asserting "recovery works".
- **The grammar is enforced in two implementations** — AC10's literal-equality
  test is the drift guard; the engine cannot import credbroker.
- **credbroker is published.** New public API is a compatibility surface for
  other consumers; all four functions are additive and
  `SsoProfileNotRegisteredError` subclasses the existing
  `SsoSessionUnavailableError`, so current handlers keep working.

## Deferred

- `auth_default` / `base_url` from `catalogue.toml [pack-defaults.atlassian]`,
  via an installer-side projection so skill scripts stay stdlib-only. The
  RFC-0074 cascade is Shipped but has no consumer, and its baked layer lives
  inside the `agentbundle` package at
  `packages/agentbundle/agentbundle/_data/install-defaults.toml`, unreachable
  from stdlib-only scripts. Needs an RFC-0074 addendum plus an ADR extending
  ADR-0059, and must carry AC25's destination-pinning constraint.
  *(deferred: pack-config-catalogue-sso-defaults)*
- Auto-recovery for `confluence-crawler`'s CLI was delivered by
  [`confluence-crawler-check-auto-login`](../confluence-crawler-check-auto-login/spec.md),
  reusing the operation that lives in `credbroker`.
- Serialising concurrent *browser launches* — two recaptures collide on
  Chromium's singleton lock in the shared `browser-state/<profile>` dir. Scoped to
  the browser launch only; it makes no claim about materialisation.
  *(deferred: sso-broker-register-concurrency)*
- Residual engine exposures: `browser-state/<profile>` is created with
  umask-default mode, and `_do_register` stores `context.cookies()` unfiltered,
  so IdP cookies are retained at rest even though the consumer filters at load.
  *(deferred: sso-broker-at-rest-minimisation)*
- The non-JSON-2xx guard on read paths other than `whoami` — every method calls
  `resp.json()`, so the same login-page body still exits 1 elsewhere.
  *(deferred: nonjson-2xx-guard-all-read-paths)*
- Headed-login destination poisoning remains an accepted limitation under
  RFC-0084: the supported user-scope installation cannot enforce a boundary
  against its own principal. Generic interactive capture stays operator-only;
  no baseline implementation is deferred.
- A pack-shipped `PreToolUse` hook denying **both** agent-facing capture
  commands — `jira.py check --register` and `setup_sso.py` — while allowing bare
  `check`. Explicitly **belt-only, not a boundary**: it lands in
  `.claude/settings.local.json`, an agent-writable repo file; adapter coverage is
  uneven (`kiro-ide` drops hook-wiring); and it cannot stop a direct
  `sso-broker.py register`. A real boundary needs privilege separation.
  *(deferred: sso-register-pretooluse-hook)*
- The profile grammar in `tools/lint-sso-config.py`, so a pre-baked traversal
  value fails at build time as well as at runtime.
  *(Deferred, and since **delivered** on 2026-08-16 by
  `spec/credentialed-cli-hygiene` — the lint restates the engine's grammar, with
  a self-test that pins the restatement equal to `credbroker._sso`'s so the two
  copies cannot drift.)*
- A cross-process recapture cooldown. AC17's bound is per-process and each agent
  turn is a new process, so a retry loop can spawn a **headless** recapture on
  every invocation — no browser is shown (AC14a), but each spawn still costs up to
  `refresh`'s 180 s and re-exercises the engine.
  *(deferred: sso-recapture-cooldown)*
- Amending the lint-pinned phrase `do not run any setup helper for them`
  (`catalogue_tooling/lint.py:458`), whose literal meaning the `check` carve-out
  inverts. *(deferred: sso-cookie-lint-phrase-amendment)*
- The `--insecure` stderr warning in the sibling credentialed CLIs.
  *(Deferred, and since **delivered** on 2026-08-16 by
  `spec/credentialed-cli-hygiene`. Note this line named four siblings and only
  two of them were silent: `confluence-publisher` already emitted the warning,
  and `figma` has no `--insecure` flag at all. The fix landed in
  `confluence-crawler` and `jira-align`, each with tests.)*
