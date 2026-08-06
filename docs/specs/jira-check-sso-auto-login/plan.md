# Plan: jira-check-sso-auto-login

- **Status:** Approved
- **Spec:** [`spec.md`](./spec.md)
- **Architecture:** [`docs/architecture/credentials.md § The `sso-cookie` broker`](../../architecture/credentials.md#the-sso-cookie-broker)
- **Mode:** full (risk triggers: **security boundary** — auth, secrets, subprocess on the credential path; **public-interface change** — new `credbroker` API)

> **Supersedes** the Shape A draft of this plan, which had `check` resolve the
> broker path and call `subprocess.run` directly. That is now a spec *Never do*.
> Nothing below routes a spawn through a skill script.

## Approach

Four layers change, bottom-up, and the dependency order is forced:

1. **`credbroker`** gains the grammar validator, a cross-platform spawn helper,
   and the two recapture verbs. Everything above consumes these.
2. **`sso-broker.py`** (the engine) gains its own independent grammar guard plus
   path containment, and two behaviour fixes the design review surfaced —
   unconditional jar re-materialisation (with a unique temp name, since making the
   write unconditional makes the shared-temp collision routine; **ordering between
   concurrent materialisers is deliberately unspecified** — see AC6a and
   `sso-materialisation-ordering`) and a distinct not-registered exit code.
   It cannot import `credbroker`, so its grammar copy is pinned equal by test.
3. **The `jira` skill** gains the typed discriminator, the `check` recovery
   flow, `--register`, and the honest `--insecure` warnings.
4. **Docs, CI wiring, bookkeeping, version bumps** — bumps strictly last, so
   `make build-self` regenerates projections against settled content.

Layer 2 has no dependency on layer 1 (separate implementations by design), so
T5/T6 run in parallel with T1–T4. The parity test (T7) is the join. T5 and T6
both edit `sso-broker.py`, so they serialise against **each other** — run T6
first (it changes an exit code T5's tests assert).

## Constraints

- **Cross-platform is a hard requirement.** `start_new_session` / `os.killpg`
  are POSIX-only; `Path.home()` reads `USERPROFILE` on Windows. Follow the
  established pattern at `workspace_mcp.py:1069-1092` rather than inventing one.
- **`credbroker` is published** (PyPI, 0.4.1). New API is additive, but the pip
  layer *precedes* the vendored floor on `sys.path`, so an old pinned install
  shadows the new floor — hence AC30's feature-detect guard.
- **The engine cannot import `credbroker`** — `credbroker` subprocesses it.
- **`catalogue_tooling/lint.py:439-459`** pins verbatim SKILL.md security phrases
  for both `auth: sso-cookie` and `auth-fallback: creds`, matched after
  whitespace normalisation. They cannot be reworded; only the unpinned lead-in
  may be re-scoped.
- **`tools/test-lint-sso-config.py:90-96`** pins `_sso_config.py`,
  `setup_sso.py`, `test_sso_config.py`, `test_setup_sso.py`,
  `test_auth_selector.py` byte-identical across `jira/` and
  `confluence-crawler/`. Edit by copy, never retype.
- **`jira.py` is not importable flat** — `import scripts.jira` is the only route
  (verified). Tests must reach every symbol through `scripts.*` or the typed
  `except` will not match.
- **`.claude-plugin/marketplace.json`, `.agentbundle/bin/sso-broker.py`,
  `.agentbundle/lib/credbroker/`** are generated. Regenerate with
  `make build-self`; never hand-edit.
- **Two version-shaped values in `packs/atlassian/pack.toml`** — only
  `[pack].version` moves; `[pack.adapter-contract] version` does not.

## Assumption trio

**Files I will touch**

| Layer | File | Change |
|---|---|---|
| credbroker | `packages/credbroker/credbroker/_sso.py` | grammar validator, spawn helper, two recapture verbs, new error types |
| credbroker | `packages/credbroker/credbroker/__init__.py` | export the new public surface |
| credbroker | `packages/credbroker/tests/unit/test_sso_recapture.py` | **new** — AC1–AC5, AC10 |
| credbroker | `packages/credbroker/tests/unit/test_sso_broker_verbs.py` | AC6–AC9, AC6a, AC6b cases |
| engine | `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py` | profile guard, containment, re-materialisation, exit 4, `_capture(persist=)` split + `--ephemeral`, `refresh` rejects connection args, `_write_profile` escaping |
| jira | `packs/atlassian/.apm/skills/jira/scripts/_client.py` | typed subclass, guarded jar read, whoami guards |
| jira | `…/jira/scripts/_sso_config.py` | validation delegation (+ mirror) |
| jira | `…/jira/scripts/setup_sso.py` | refactor onto `register_sso_session` (+ mirror) |
| jira | `…/jira/scripts/jira.py` | `_run` routing, `_probe`, recovery, `--register`, `--insecure`, version floor |
| jira | `…/jira/scripts/test_check_sso_login.py` | **new** — AC11–AC20, AC30, AC31 |
| credbroker | `packages/credbroker/tests/unit/test_sso_derivation.py` | **new** — AC32 chain + fetch bounds |
| governance | `docs/rfc/0035-…md`, `docs/rfc/0013-credential-broker-contract.md` | Approver-signed `## Errata` entries — RFC-0035 narrows its non-goal, RFC-0013 records the verb-table/exit contract change (AC34) |
| jira | `…/jira/scripts/test_setup_sso.py` | rewritten onto `register_sso_session` (+ mirror) |
| release | `packs/figma/{pack.toml,.claude-plugin/plugin.json}`, `packs/linear/{pack.toml,.claude-plugin/plugin.json}`, `packs/credential-brokers/.claude-plugin/plugin.json` | dependency declaration + minor bump (`plugin.json` required — CAT_L009) |
| jira | `…/confluence-crawler/requirements.txt` | `credbroker>=0.5.0` (AC30: both consuming skills) |
| jira | `…/jira/requirements.txt` | `credbroker>=0.5.0` |
| jira | `…/jira/SKILL.md`, `…/jira/evals/evals.json` | carve-out, pre-flight rule, exit table, negative eval |
| mirror | `…/confluence-crawler/scripts/{_sso_config,setup_sso}.py` | byte-identical mirrors |
| CI | `.github/workflows/build-check.yml` | wire the new jira suite |
| CI | `packages/agentbundle/…/self_host_windows.py` | add credbroker suite + the new jira suite |
| docs | `docs/architecture/credentials.md` | already landed; reconcile with shipped behaviour |
| docs | `guides/atlassian/how-to/authenticate-jira-confluence-with-sso-cookies.md`, `guides/_shared/reference/`, `docs/product/changelog.md` | AC21–AC24 |
| bookkeeping | `workspace.toml` | queue entry + deferred slugs |
| release | `packages/credbroker/pyproject.toml`, `packs/atlassian/{pack.toml,.claude-plugin/plugin.json}`, `packs/credential-brokers/pack.toml` | version bumps (**last**) |

**Tests that demonstrate "done"** — canonical list; every task's `Done when:`
references this block by number rather than restating commands.

```bash
# 1  credbroker
cd packages/credbroker && python -m pytest
# 2  both skills' script suites
cd packs/atlassian/.apm/skills/jira/scripts && python -m pytest
cd packs/atlassian/.apm/skills/confluence-crawler/scripts && python -m pytest
# 3  byte-parity + schema parity
python tools/test-lint-sso-config.py
# 4  repo gates (SAST ON — this change adds subprocess on the credential path)
make lint-ruff && python3 tools/lint-mypy.py && make build-check
# 5  spec hygiene
python .claude/skills/work-loop/scripts/lint-spec-status.py --root .
# 6  manual QA — token path untouched, no browser
cd packs/atlassian/.apm/skills/jira && python scripts/jira.py check
cd packs/atlassian/.apm/skills/jira && python scripts/jira.py check --insecure
```

**What I am not changing**

- The token path's credential resolution (only AC18's warning is added).
- Any `jira.py` subcommand other than `check`.
- `confluence-crawler`'s `check` behaviour (it *does* inherit the shared-file
  changes — see spec scope; that is not "no change").
- `[pack.adapter-contract] version`.
- `catalogue.toml` / `install-defaults.toml` — deferred to the RFC-0074 addendum.

## Declined patterns

| Tempted to add | Why declined |
|---|---|
| Keeping the spawn in `jira.py` (Shape A) | Puts the platform split in an un-mypy-checked script and duplicates it into the next consumer. Rejected in the architect pass. |
| A TTY/stdin confirmation gate | A TTY the agent owns is not out-of-band (survey F4 / OWASP ASI09). Replaced by destination pinning on the automatic path (AC1) + operator-typed `--register` (AC15), with derivation as defence in depth (AC32). |
| Any CLI flag beyond `--register` | `--register` is earned by a real second caller (first-run vs steady-state trust). Nothing else has one. |
| A retry loop around recapture | Exactly one attempt per process. A loop re-opens browsers against a broken profile. |
| Making the engine import `credbroker` to share the grammar | Inverts the dependency — `credbroker` subprocesses the engine. Duplicate + pin by test instead. |
| Fixing the non-JSON-2xx guard on *all* read paths | Every method calls `resp.json()`; widening beyond `whoami` changes subcommands the spec scopes out. Deferred with a slug. |
| Hardening `browser-state` mode and the unfiltered at-rest jar | Real, but a different concern from recapture. Deferred with a slug. |
| Bumping `[pack.adapter-contract]` alongside `[pack].version` | Different contract, unchanged here. |

## Domain grounding

Three claims about components outside the `jira` skill, each grounded by reading
source or executing a probe — none recalled:

1. *`_do_refresh` with no connection args reads the destination from the stored
   profile TOML and returns non-zero when unregistered.* Read at source. This is
   what makes destination pinning possible.
2. *`_do_get_cookies` skips re-materialisation when the file exists, while
   `_store_cookie_jar` writes to the keychain on Tier-2-capable platforms.* Read
   at source — this is the bug AC6a fixes, and without it the whole feature is a
   no-op on macOS/Windows.
3. *`start_new_session` + `os.killpg` removes the grandchild on POSIX;
   `os.killpg` is absent on Windows.* Executed probe, plus the repo's own
   precedent at `workspace_mcp.py:1069-1092`.

## Anchor-test sweep record

Tests and lints that pin exact content of files this change edits:

| Site | Pins | Disposition |
|---|---|---|
| `catalogue_tooling/lint.py:439-459` (via `make build-check`) | verbatim SKILL.md security phrases, both brokers | **keep** — carve-out is additive prose (T13) |
| `tools/lint-catalogue-curation-guard.py` (`build-check.yml:478`) | hard-fails any change under `packs/credential-brokers/**` or engine code outside `build/recipes/` + `/tests/` | **exempt via trailer** — `Engine-Change-RFC: RFC-0035` on every commit (AC34) |
| `tools/test-lint-sso-config.py:90-96` | byte-equality of five files across two skills | **change both sides** (T9) |
| `packages/credbroker/tests/unit/test_sso_broker_verbs.py` | engine verb behaviour incl. `get-cookies` exit codes | **extend** — AC6b changes an exit code, so existing assertions on `3` must be re-read (T6) |
| `jira/scripts/test_exit_codes.py:59-65,100-102` | source-index assertions over `jira.py` text | **verify** — re-run after every `jira.py` edit, not just at the end |
| `jira/evals/evals.json:188-199` | eval 16 asserts the agent defers setup to the user | **extend** — token-path-scoped today; T13 adds the `setup_sso.py` negative case |
| `make build-check` drift gates | `marketplace.json`, `.agentbundle/bin/`, `.agentbundle/lib/` | **regenerate** in T15 |

## Resolve-vs-surface disposition record

| Question | Disposition | Resolution |
|---|---|---|
| Where does the recapture operation belong? | **surfaced → resolved** | `credbroker` (Shape D). User ratified 2026-08-05. |
| Does auto-recovery actually work on macOS/Windows? | **resolved** | No — sticky materialisation. AC6a fixes the engine. Found by design review, verified at source. |
| Is exit `3` a usable "not registered" signal? | **resolved** | No — ten distinct sites. AC6b adds exit `4`. |
| Can a stale session return exit 0? | **resolved** | Yes — parseable JSON without identity fields. AC11 site 5. |
| Can `--register` be enforced outside the prose layer? | **resolved** | Partly. A pack-shipped `permissions.deny` does not exist as a mechanism; a `PreToolUse` hook is shippable but lands in an agent-writable repo file with uneven adapter coverage (deferred). An **operator-applied** user-scope deny rule is real but **Claude Code only** — the adapter contract has no permissions abstraction, and the other five adapters offer only coarse sandbox levels or tool-name allow-lists. Documented as adapter-specific hardening; nothing in the design depends on it. |
| Is destination pinning airtight against a hostile agent? | **resolved** | No. TOFU was designed and rejected (baseline written after the poisoned register). Server-side derivation was then designed and **downgraded to defence in depth** — `base_url` sits in the same file, so one write defeats it. Consent rests on AC15 (operator-typed `--register`), not on attestation. |
| Does the new API break old pinned installs? | **resolved** | Yes, silently. AC30 feature-detects + pins `>=0.5.0`. |
| Bump `packs/credential-brokers`? | **surfaced → reversed** | Initially no (crash-fix precedent). AC6b changes an exit code = contract change → bump to 0.3.0. Reported to user. |
| Materialise red stubs now? | **surfaced** | User said "no code". Stub bodies are specified below; each task writes its own immediately before implementing it. |
| Windows `taskkill` arm | **surfaced** | Reasoned, not executed. Verified only when AC26's parity run is green; named limitation until then. |

## Design (LLD)

### credbroker surface

```
_sso.py
  validate_sso_profile(profile)            -> None            (raises SsoConfigError)
  derive_sso_destination(base_url, *, strategies=()) -> str | None  (public; AC32)
  _spawn_broker(argv, *, timeout, env_profile, capture) -> CompletedProcess                      (private; tree-kill, env allowlist)
  refresh_sso_session(profile)             -> None            (no destination parameter)
  register_sso_session(profile, *, login_url, success_url_pattern,
                       cookie_domains, validation_endpoint,
                       session_filename=None, ttl_hint_minutes=None) -> None
  SsoProfileNotRegisteredError(SsoSessionUnavailableError)     (refresh exit 4)
  SsoRecaptureFailedError(SsoError)                            (refresh/register exit 3/unknown)
  SsoInteractionRequiredError(SsoError)                        (refresh exit 5)
  SsoBrokerUnavailableError(SsoError)                          (timeout / spawn /
                                                                materialisation write /
                                                                get-cookies 3)
  # no lock error class: AC6a specifies no lock and no ordering protocol
  # per-verb mapping is AC1's table — do not restate it here
```

### `check` control flow

```
_run(args)
  └─ auth_path == "sso-cookie" and args.command == "check"     (AC31: BEFORE :717-725)
       └─ _cmd_check_sso(sso_config, args)
            1. warn if args.insecure                            (AC18)
                        3. rc = await _probe(sso_config)      # whoami() direct, close in finally (AC13)
                 └─ not SsoSessionUnavailable → return rc        (AC11: 403/config terminal)
            5. stderr notice + log.info                          (AC16)
            6. credbroker.refresh_sso_session(profile)           (AC1, AC9 destination-free)
                 SsoProfileNotRegisteredError → exit 2, "ask the user … --register"
                 SsoInteractionRequiredError  → exit 2, "run check --register"; NO browser
               SsoRecaptureFailedError      → exit 2, engine stderr already shown
            7. rc = await _probe(sso_config)      # exactly one retry (AC17)
  └─ every other command / token path → today's construction, unchanged
```

### Failure matrix

| Case | Behaviour |
|---|---|
| `403` on probe | plain `AuthError` → exit 2, **no** recapture |
| cookie-domain confinement fails | `SsoConfigError` → exit 2, no recapture |
| broker not installed | `SsoBrokerNotInstalledError` → exit 2 (credbroker's own remediation) |
| profile not registered | engine exit 4 → exit 2 naming `check --register` |
| headless refresh needs a human | engine exit **5** → exit 2 naming `check --register` (the attested path); no browser, no retry |
| playwright absent / sign-in not completed | engine exit 3 → `SsoRecaptureFailedError` → exit 2, engine stderr surfaced |
| refresh ok but jar unusable | post-recapture construction fails → exit 2, no second attempt |
| spawn exceeds timeout | tree killed, exit 2 |
| corrupt / wrong-shape jar | mapped to `SsoSessionUnavailable` → recovery runs (AC12) |
| 2xx non-JSON, or JSON without identity | `SsoSessionUnavailable` → recovery runs (AC11 sites 4, 5) |
| derived host ≠ configured `login_url` host (`--register` only) | exit 2, **no browser**, names both hosts + `setup_sso.py` (AC32) |
| derivation cannot resolve (`--register` only) | exit 2 naming `setup_sso.py`; never falls back to the config value (AC32) |
| old pinned credbroker | exit 2 with upgrade remediation (AC30) |
| two concurrent `check`es | **undefined** — deferred slug |

## Tasks

> **Red stubs.** Each TDD task below carries a compilable body with a real
> assertion that **fails against today's code** — not a comment-only body (which
> raises `IndentationError`) and not an `...` body (which compiles and passes
> green, giving a vacuous gate). No stub body is `...` — `packs/AGENTS.md:135` requires
> `raise NotImplementedError  # STUB: ACn`, because a bare `...` is valid Python
> that passes immediately and defeats the red-green cycle. Stubs are
> materialised **per task, immediately before implementing that task** — not all
> up front. Materialising every stub at once would put red tests from T1–T7 into
> canonical suite 1 while each of those tasks independently requires that whole
> suite to pass, so no intermediate gate could ever be green. Each task writes
> its own stubs, observes them red, implements, then gates on the suite. Per the user's "no code" instruction, that materialisation has not
> happened yet.
>
> **Fixture shape.** `test_sso_broker_verbs.py`'s `broker` fixture yields a
> 2-tuple `(mod, backend)` and is parametrised over the pack-source and the
> generated `.agentbundle/bin/` copies. Every engine stub below must unpack it
> (`mod, _ = broker`) or it fails with `AttributeError` on a tuple — red for a
> harness reason, which proves nothing. T7's parity test reads the **pack-source**
> copy as canonical; the projected copy is covered by the existing drift gate.
> AC6a's dual-store arms are the fixture's own `mod._tier2_backend` assignment
> (a stub backend = keychain-backed, `None` = file-floor); the file-floor arm is
> the **control**, not the regression guard, because store and materialisation
> are the same file there.

### T0 — Gate **and bookkeeping** (AC25)

**Depends on:** none · **Mode:** goal-based · `no stub (gate)`
Bookkeeping moves **first**, not last: `lint-spec-status.py`'s deferral-anchor
invariant is status-independent and hard, so every `(deferred: <slug>)` in the
spec must already resolve in `workspace.toml [backlog].open` or canonical 5 is
red from here through T13. Add the queue entry under `["ini-002".work]` and **exactly** the
`[backlog].open` slugs this spec's `(deferred: …)` anchors name — no more, no
fewer. An anchor with no slug is a hard lint violation; a slug with no anchor is
stale bookkeeping that exposes withdrawn work through backlog tooling. The
current set is: `browser-state-lifetime`, `confluence-crawler-check-auto-login`, `insecure-warning-sibling-clis`, `lint-sso-config-profile-charset`, `nonjson-2xx-guard-all-read-paths`, `pack-config-catalogue-sso-defaults`, `sso-branch2-destination-attestation`, `sso-broker-at-rest-minimisation`, `sso-broker-register-concurrency`, `sso-cookie-lint-phrase-amendment`, `sso-destination-field-integrity`, `sso-live-browser-destination-derivation`, `sso-materialisation-ordering`, `sso-privilege-separated-config`, `sso-recapture-audit-sink`, `sso-recapture-cooldown`, `sso-register-pretooluse-hook`. Derive it, do not transcribe it:
`grep -o '(deferred: [a-z0-9-]*)' spec.md | sort -u`.
Then flip `spec.md` → `Implementing` and this plan → `Executing`, and run
`loop-cohort approve-plan`. **Done when:** canonical 5 green (it now can be).

### T1 — `credbroker.validate_sso_profile` (AC4)

**Depends on:** none · **Mode:** TDD · `stub: true`
```python
def test_profile_grammar_rejects_newline():        # STUB: AC4
    with pytest.raises(credbroker.SsoConfigError):
        credbroker.validate_sso_profile("abc\n")   # re.match would accept this
def test_profile_grammar_rejects_windows_device(): # STUB: AC4
    for bad in ("CON", "con.toml", "NUL", "COM1"):
        with pytest.raises(credbroker.SsoConfigError):
            credbroker.validate_sso_profile(bad)
def test_profile_grammar_rejects_non_str():        # STUB: AC4
    with pytest.raises(credbroker.SsoConfigError):
        credbroker.validate_sso_profile(5)
def test_profile_grammar_accepts_ordinary():       # STUB: AC4
    credbroker.validate_sso_profile("jira")
```
**Approach:** `re.fullmatch` + case-insensitive device-name denylist (stem
compared, so `con.toml` is caught). **Done when:** canonical 1.

### T2 — Cross-platform spawn helper (AC3)

**Depends on:** none · **Mode:** TDD · `stub: true`
```python
def test_spawn_kills_process_tree(tmp_path):       # STUB: AC3
    # fake broker forks a grandchild then sleeps past the timeout
    cp = _spawn_broker([sys.executable, str(fake), "refresh", "p"],
                       timeout=2, env_profile="browser", capture=False)
    assert cp.returncode != 0
    assert _no_survivors(pgid)                     # POSIX; skipped on Windows
def test_probe_timeout_is_not_recoverable(tmp_path):       # STUB: AC3
    raise NotImplementedError  # STUB: AC3 — fake get-cookies exceeds an injected short timeout ->
         # SsoBrokerUnavailableError, exit 2, refresh_sso_session NEVER called
def test_get_cookies_captures_stdout_but_not_stderr(tmp_path):  # STUB: AC3/F20
    raise NotImplementedError  # STUB: AC3 — fake engine prints a jar path to stdout + a diagnostic to stderr;
         # load_sso_cookies returns the path, the diagnostic stays visible
def test_spawn_env_is_allowlisted(monkeypatch, tmp_path):  # STUB: AC3
    monkeypatch.setenv("JIRA_API_TOKEN", "secret-should-not-cross")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/etc/ssl/corp.pem")
    env = _capture_child_env(tmp_path)
    assert "JIRA_API_TOKEN" not in env
    assert env["REQUESTS_CA_BUNDLE"] == "/etc/ssl/corp.pem"
```
**Approach:** `start_new_session=True`; `getattr(os, "killpg", None)` →
SIGTERM/grace/SIGKILL on POSIX, `taskkill /T /F /PID` then
`terminate()`/`kill()` on Windows; `_BROWSER_ENV_ALLOWLIST` split by platform.
**Done when:** canonical 1 + 4 (mypy).

### T3 — `refresh_sso_session` / `register_sso_session` + error taxonomy (AC1, AC2)

**Depends on:** T1, T2, T5b · **Mode:** TDD · `stub: true`
> Needs T5b: AC2 always passes `--ephemeral`, so the engine must accept it before
> any real `register` invocation, or argparse rejects it.
```python
def test_per_operation_timeouts_match_ac3_table(fake_broker):  # STUB: AC3
    raise NotImplementedError  # STUB: AC3 — assert the timeout each public
                               # function passes: register 540 s, refresh 180 s,
                               # load_sso_cookies 30 s. Lives here because T3 is
                               # where all three callers exist.
def test_refresh_argv_carries_no_destination(fake_broker):   # STUB: AC1
    credbroker.refresh_sso_session("jira")
    argv = fake_broker.last_argv
    assert argv[-2:] == ["refresh", "jira"]
    assert not any(a.startswith("--") for a in argv)
def test_refresh_signature_has_no_destination_param():       # STUB: AC1
    params = set(inspect.signature(credbroker.refresh_sso_session).parameters)
    assert params == {"profile"}
def test_exit4_is_not_registered(fake_broker):               # STUB: AC1
    fake_broker.exit_code = 4
    with pytest.raises(credbroker.SsoProfileNotRegisteredError):
        raise NotImplementedError  # STUB: AC1
@pytest.mark.parametrize("verb", ["refresh", "register"])
def test_exit3_is_generic_failure(fake_broker, verb):        # STUB: AC1
    #  drives the matching public function: refresh_sso_session / register_sso_session
    fake_broker.exit_code = 3          # playwright absent / sign-in incomplete
    with pytest.raises(credbroker.SsoRecaptureFailedError):
        raise NotImplementedError  # STUB: AC1
def test_exit5_maps_to_interaction_required(fake_broker):         # STUB: AC14a
    fake_broker.exit_code = 5
    with pytest.raises(credbroker.SsoInteractionRequiredError):
        raise NotImplementedError  # STUB: AC14a
def test_timeout_is_broker_unavailable(fake_broker):         # STUB: AC1
    with pytest.raises(credbroker.SsoBrokerUnavailableError):
        raise NotImplementedError  # STUB: AC1
```
**Done when:** canonical 1 + 4.

### T4 — `load_sso_cookies` validates (AC5)

**Depends on:** T1 · **Mode:** TDD · `stub: true`
```python
def test_load_sso_cookies_validates_profile():     # STUB: AC5
    with pytest.raises(credbroker.SsoConfigError):
        credbroker.load_sso_cookies("../../../../tmp/pwn")
```
**Done when:** canonical 1.

### T5 — Engine: grammar guard, containment, `rm` carve-out (AC6, AC7, AC8, AC9)

**Depends on:** none · **Mode:** TDD · `stub: true`
```python
@pytest.mark.parametrize("verb", ["register", "get-cookies", "test", "refresh"])
@pytest.mark.parametrize("bad", ["../../../../tmp/pwn", "abc\n", "abc\r\n",
                                 "x"*65, "café", "", ".", "..", "CON", "con.toml"])
def test_profile_rejected_per_verb(broker, verb, bad, capsys):   # STUB: AC6/AC9
    mod, _ = broker
    assert mod.main([verb, bad]) == 3
    assert "profile" in capsys.readouterr().err.lower()   # exit code alone is already green today
def test_flag_shaped_via_double_dash_reaches_guard(broker):      # STUB: AC9
    mod, _ = broker
    assert mod.main(["get-cookies", "--", "-x"]) == 3            # `--` escape parses -x as the positional
def test_bare_flag_is_argparse_exit(broker):                     # STUB: AC9
    mod, _ = broker
    with pytest.raises(SystemExit) as e: mod.main(["get-cookies", "-x"])
    assert e.value.code == 2
def test_rm_still_deletes_legacy_invalid_name(broker):           # STUB: AC8
    mod, _ = broker
    _seed_profile(mod, "legacy name")               # pre-change, grammar-invalid
    assert mod.main(["rm", "legacy name"]) == 0
    assert not mod._profile_path("legacy name").exists()   # rc==0 alone is green today
    assert not mod._cookie_floor_path("legacy name").exists()
```
**Approach:** `_require_valid_profile` at each verb dispatch + resolved-parent
containment assertion; `rm` gets containment only. **Done when:** canonical 1.

### T6 — Engine: unconditional re-materialisation + exit 4 (AC6a, AC6b)

**Depends on:** none · **Mode:** TDD · `stub: true`
```python
def test_write_uses_unique_temp_name(broker, tmp_path):          # STUB: AC6a
    mod, _ = broker
    raise NotImplementedError  # STUB: AC6a — two writes must use distinct *.tmp
                               # names (pid+random), and leave none behind
def test_get_cookies_rewrites_stale_materialised_jar(broker):    # STUB: AC6a
    _store(broker, "jira", b'[{"name":"old"}]'); p1 = _get_cookies(broker, "jira")
    _store(broker, "jira", b'[{"name":"new"}]'); p2 = _get_cookies(broker, "jira")
    assert p1 == p2                                  # same path…
    assert b"new" in p2.read_bytes()                 # …fresh bytes (fails today)
def test_refresh_unregistered_returns_4(broker):                 # STUB: AC6b
    mod, _ = broker
    assert mod.main(["refresh", "never-registered"]) == 4


```
Run under **both** a keychain-backed and a file-floor-backed store — the bug is
invisible on the file-floor (Linux/CI) path.
**Approach:** drop the `if not materialised.exists()` guard; write via a
**unique** temp name (pid + random suffix, not the shared `<profile>.jar.tmp`);
use a **unique** temp name (pid + random suffix), removing the shared-path
collision. Ordering between concurrent materialisers is **not** specified —
see AC6a and `sso-materialisation-ordering`;
`_do_refresh` returns 4 for `FileNotFoundError`. **Done when:** canonical 1.

### T5b — Engine capture split + `refresh` argument rejection (AC35 engine half)

**Depends on:** T6 · **Mode:** TDD · `stub: true`
Split `_do_register` into `_capture(profile, args, *, persist, headless)`; add
`--ephemeral` to the `register` verb (default `persist=True`); make `refresh`
launch **`headless=True`** with a bounded **20 s** silent-completion window and
return exit **`5`** when a login page is still displayed at the end of it (AC14a).
`refresh`'s spawn timeout is **180 s** per AC3's per-operation table, not the
540 s `register` bound — that code is what makes AC14a
implementable, since an abort rule alone has no state in which the engine can
report "needs a human" before a window is on screen; and make `refresh` reject
every connection argument with exit 3. Serialises with T5/T6 on `sso-broker.py`.
AC32's derivation stays in T11.

> **T11b is the single regeneration point before the drift-gated tasks, and the
> ordering is enforced by the dependency graph, not by this note.** T11b depends
> on T4/T5/T5b/T6/T11 — every projection-source edit — and T12, T13 and T14a all
> depend on T11b, so T14a's bump-regeneration necessarily follows it and T15
> regenerates only the version-bump artifacts. No task before T11b runs
> `make build-self`. **From T5 through T11, projection-source tasks substitute two
> explicit commands** for canonical 1 and 4, because the projected copy is stale until
> T11b regenerates it:
> `cd packages/credbroker && python -m pytest -k 'source or not projected'`
> — the `-k` filter must keep the non-parametrised suites (`test_sso_recapture.py`,
> `test_sso_derivation.py`), which a bare `-k source` would silently drop — and
> `SKIP_SAST=1 make lint-ruff && python3 tools/lint-mypy.py` (no `build-check`,
> so no drift gate). **This substitution applies to T1–T4 as well**, not only the
> engine tasks: T4 edits `credbroker`, whose vendored projections
> (`.agentbundle/lib/credbroker/`, the pack copy) are drift-gated, so any task
> after it that ran plain `build-check` before T11b would fail on that drift. T11b runs `make build-self` and from there every task uses
> the unmodified canonical commands. The
> `broker` fixture parametrises over the pack source *and* the generated
> `.agentbundle/bin/` copy, and no task regenerates that copy before T11b — T14a
> now depends on T11b — so the projected arm is stale only for T5 through T11.
> From T11b onward every task, including T12/T13/T14a/T15, runs the full
> source-plus-projected suite.
```python
def test_register_capture_is_ephemeral_then_seeds(broker):   # STUB: AC35
    mod, _ = broker
    calls = _record_playwright(mod)
    mod.main(["register", "jira", "--ephemeral", "--login-url", "https://idp.example",
              "--success-url-pattern", "https://jira.example/x"])
    # capture must NOT use the persistent profile...
    assert calls.capture.kind == "ephemeral"
    assert calls.capture.headless is False        # interactive capture is HEADED
    # ...but a second, headless persistent launch must seed it (AC35), so
    # asserting launch_persistent_context is never called would reject a
    # correct implementation.
    assert calls.seed.kind == "persistent" and calls.seed.headless
    assert calls.seed.user_data_dir.endswith("browser-state/jira")
    assert calls.seed.add_cookies_called
@pytest.mark.parametrize("verb,persist,headless", [
    (["register", "jira"], True, False),                    # operator default
    (["register", "jira", "--ephemeral"], False, False),     # register_sso_session
    (["refresh", "jira"], True, True),                       # AC14a
])
def test_capture_mode_matrix(broker, verb, persist, headless):   # STUB: AC35
    mod, _ = broker
    raise NotImplementedError  # STUB: AC35 — pin all four rows of AC35's matrix
                               # (the seeding launch is asserted above)
@pytest.mark.parametrize("bad", ['a"b', "a" + chr(92) + "b", f"a{chr(1)}b", f"a{chr(0x7f)}b"])
@pytest.mark.parametrize("field", ["login_url", "cookie_domains"])  # scalar AND list-valued
def test_write_profile_rejects_toml_breaking_chars(broker, bad, field):  # STUB: AC6
    raise NotImplementedError  # STUB: AC6 — reject or escape; then tomllib round-trips
def test_refresh_silent_redirect_within_window_succeeds(broker):  # STUB: AC14a
    mod, _ = broker
    raise NotImplementedError  # STUB: AC14a — delayed unaided redirect inside 20 s -> 0
def test_refresh_login_page_returns_5_and_closes(broker):         # STUB: AC14a
    mod, _ = broker
    raise NotImplementedError  # STUB: AC14a — login page still shown -> exit 5,
                               # headless context closed, no browser left behind
def test_refresh_rejects_login_url(broker):             # STUB: AC35
    mod, _ = broker
    assert mod.main(["refresh", "p", "--login-url", "https://evil.example"]) == 3
```
**Done when:** canonical 1.

### T7 — Grammar parity test (AC10)

**Depends on:** T1, T5 · **Mode:** TDD · `stub: true`
```python
def test_grammar_literal_matches_engine():         # STUB: AC10
    assert _extract_pattern(BROKER_PY) == credbroker._sso._PROFILE_RE.pattern
    assert _extract_denylist(BROKER_PY) == credbroker._sso._RESERVED_DEVICE_NAMES
```
**Done when:** canonical 1.

### T8 — `_client.py`: typed discriminator + jar guards (AC11, AC12)

**Depends on:** none · **Mode:** TDD · `stub: true`
```python
def test_session_unavailable_is_subclass_of_autherror():   # STUB: AC11
    assert issubclass(SsoSessionUnavailable, AuthError)    # keeps exit band intact
def test_403_is_not_session_unavailable():
    raise NotImplementedError  # STUB: AC11
def test_config_error_is_not_session_unavailable():
    raise NotImplementedError  # STUB: AC11
def test_401_on_cookie_path_is_session_unavailable():
    raise NotImplementedError  # STUB: AC11
def test_2xx_non_json_is_session_unavailable():
    raise NotImplementedError  # STUB: AC11 site 4
@pytest.mark.parametrize("field", ["displayName","name","emailAddress","key","accountId"])
def test_identity_field_accepted_no_recapture(field):        # STUB: AC11 site 5
    raise NotImplementedError  # STUB: AC11 — each must NOT raise and must NOT print "as ?" — pins raise site == _cmd_check set
@pytest.mark.parametrize("body", [{"displayName": None}, {"name": ""}, {"key": 7}])
def test_present_but_unusable_identity_is_session_unavailable(body):  # STUB: AC11 site 5
    raise NotImplementedError  # STUB: AC11 — presence is not enough; selector is first NON-EMPTY str
def test_falls_through_to_later_usable_field():                       # STUB: AC11 site 5
    raise NotImplementedError  # STUB: AC11 — {"displayName": None, "accountId": "abc"} passes and displays "abc"
def test_2xx_json_without_identity_is_session_unavailable():  # STUB: AC11 site 5
    raise NotImplementedError  # STUB: AC11 — {"errorMessages": [...]} must NOT yield `ok: … as ?` / exit 0
def test_corrupt_jar_is_session_unavailable():
    raise NotImplementedError  # STUB: AC12
def test_wrong_shape_jar_is_session_unavailable():
    raise NotImplementedError  # STUB: AC12
@pytest.mark.parametrize("bad", [{"domain": 1}, {"name": None}, {"path": 7}])
def test_bad_cookie_record_field_is_session_unavailable(bad):  # STUB: AC12
    raise NotImplementedError  # STUB: AC12 — each must raise SsoSessionUnavailable -> exit 2, never TypeError/exit 1
def test_jar_error_message_does_not_interpolate_exc():     # STUB: AC12
    raise NotImplementedError  # STUB: AC12 — a UnicodeDecodeError quotes cookie bytes; message must be fixed text
```
**Done when:** canonical 2 (incl. `test_exit_codes.py`).

### T9 — `_sso_config.py` + `setup_sso.py`, both skills (AC20, AC2 consumer side)

**Depends on:** T1, T3 · **Mode:** TDD · `stub: true`
```python
def test_profile_validated_before_str_coercion():  # STUB: AC20
    cfg = _write_cfg(profile=5)                    # int, not str
    with pytest.raises(SsoConfigError): load_sso_config(cfg)   # not TypeError
def test_ttl_hint_minutes_must_be_int():
    raise NotImplementedError  # STUB: AC20
@pytest.mark.parametrize("bad", ['a"b', "a" + chr(92) + "b", f"a{chr(1)}b", f"a{chr(0x7f)}b"])
@pytest.mark.parametrize("field", ["profile", "base_url", "login_url",
                                   "success_url_pattern", "validation_endpoint",
                                   "session_filename", "cookie_domains"])
def test_control_chars_rejected_in_every_sso_field(field, bad):  # STUB: AC20
    raise NotImplementedError  # STUB: AC20 — urlsplit() strips CR/LF, so validate_https_url cannot see them
def test_setup_sso_uses_credbroker(monkeypatch):   # STUB: AC2
    raise NotImplementedError  # STUB: AC2 — no subprocess / no broker-path resolution left in the skill
```
Copy both files verbatim into `confluence-crawler/scripts/`.
**Done when:** canonical 2 + 3.

### T10 — `jira.py`: routing, probe, recovery, `--register`, `--insecure`, version floor (AC13–AC20, AC30, AC31)

**Depends on:** T3, T8, T9 · **Mode:** TDD · `stub: true`
```python
def test_automatic_path_aborts_rather_than_showing_login_page():  # STUB: AC14a
    raise NotImplementedError  # STUB: AC14a — engine returns 5; check exits 2 with the
                               # `check --register` remediation and NO login page
def test_expired_session_refreshes_then_retries():
    raise NotImplementedError  # STUB: AC14
def test_refresh_called_with_profile_only():
    raise NotImplementedError  # STUB: AC1/AC14
def test_unregistered_names_check_register():
    raise NotImplementedError  # STUB: AC14
def test_403_does_not_recapture():
    raise NotImplementedError  # STUB: AC11/AC19
def test_recapture_invoked_at_most_once():
    raise NotImplementedError  # STUB: AC17
def test_non_check_subcommand_never_recaptures():
    raise NotImplementedError  # STUB: AC19/AC31
def test_probe_does_not_route_through_cmd_check():          # STUB: AC13
    raise NotImplementedError  # STUB: AC13 — _cmd_check catches AuthError and returns int — would swallow the subclass
def test_register_flag_discloses_host_on_stderr():
    raise NotImplementedError  # STUB: AC15/AC16
def test_bare_check_never_registers():
    raise NotImplementedError  # STUB: AC15
def test_insecure_warns_on_token_path():
    raise NotImplementedError  # STUB: AC18
def test_insecure_warns_ignored_on_sso_path():
    raise NotImplementedError  # STUB: AC18
def test_old_credbroker_exits_2_with_upgrade_hint():
    raise NotImplementedError  # STUB: AC30
def test_nothing_written_to_stdout_before_retry():
    raise NotImplementedError  # STUB: AC16
```
Import via `sys.path.insert(0, <skill root>)` + `import scripts.jira`; reach
every symbol through `scripts.*`; drive the SSO path via
`scripts._sso_config._DEFAULT_CONFIG_PATH`; stub the two credbroker verbs at the
`scripts.jira` binding. **Done when:** canonical 2 + 4.

### T11 — Destination attestation + ephemeral register context (AC32, AC35)

**Depends on:** T3, T5, T6, T10 · **Mode:** TDD · `stub: true`
> Serialises against T5/T6 — all three edit `sso-broker.py`, and T11 refactors the
> function they patch. Engine stubs take the `(mod, backend)` fixture.
```python
def test_derives_login_host_from_login_jsp(fake_jira):        # STUB: AC32
    fake_jira.route("/login.jsp", status=302,
                    location="https://idp.corp.example.com/authorize?state=abc")
    assert _derive_login_host(fake_jira.base_url) == "https://idp.corp.example.com"
def test_register_refuses_on_host_mismatch(fake_jira, capsys):  # STUB: AC32
    fake_jira.route("/login.jsp", status=302,
                    location="https://attacker.example.com/authorize")
    rc = _cmd_check_sso(cfg_with_login_url("https://idp.corp.example.com/login"),
                        register=True)
    assert rc == 2
    err = capsys.readouterr().err
    assert "idp.corp.example.com" in err and "attacker.example.com" in err
    assert register_stub.call_count == 0        # no browser
def test_cannot_derive_refuses_and_names_setup_sso(fake_jira):  # STUB: AC32
    fake_jira.route("/login.jsp", status=200)   # SSO-with-fallback mode
    assert _cmd_check_sso(cfg, register=True) == 2
    assert register_stub.call_count == 0        # never falls back to the config value
# AC35's capture/seed assertions live in T5b's
# test_register_capture_is_ephemeral_then_seeds — not duplicated here.
```
Derivation is a plain unauthenticated GET with `follow_redirects=False` and no
cookies — it must not reuse the SSO client. Compare **scheme+host only**; the
query carries per-request `state` / `SAMLRequest`. `derive_sso_destination` is a
**credbroker** function, bounded per AC32 (https-only, no redirects, 5 s/5 s,
≤15 s total, 64 KiB cap, strict TLS, no auth headers).
**Done when:** canonical 1 + 2 + 4.

### T11b — Regenerate projections (before any drift-gated task)

**Depends on:** T4, T5, T5b, T6, T11 · **Mode:** goal-based · `no stub (goal-based)`
All projection-source edits are done by here, so run `make build-self` to bring
`.agentbundle/bin/sso-broker.py` and the `.agentbundle/lib/credbroker/` +
`packs/credential-brokers/.apm/user-libs/credbroker/` copies back in sync. T12
and T13 both require canonical 4, which runs the drift gate, so regeneration
must precede them; T15's regeneration then handles only the version-bump
artifacts. From here the engine suites run **both** fixture arms again.
**Done when:** `git status` clean after `build-self`; canonical 1 + 4.

### T12 — CI wiring (AC26, AC27)

**Depends on:** T6, T10, T11b · **Mode:** goal-based · `no stub (goal-based)`
Add `test_check_sso_login.py` to `build-check.yml` and `self_host_windows.py`;
add `packages/credbroker`'s suite to `self_host_windows.py` so the Windows kill
arm is exercised on Windows. **Done when:** grep shows all three entries;
canonical 4.

### T13 — Docs (AC21–AC24)

**Depends on:** T10, T11, T11b · **Mode:** goal-based · `no stub (goal-based)`
SKILL.md carve-out as additive prose beside the pinned clause; `login_url`
pre-flight rule; exit-table split; invocation budget; negative eval extended to
`setup_sso.py`; how-to; reference guide; changelog; reconcile
`credentials.md` with shipped behaviour and drop its "planned" note.
**Done when:** all pinned phrases still pass `make build-check`; canonical 4 + 5.

### T14a — Bump `credential-brokers` first (AC29 exception)

**Depends on:** T11b · **Mode:** goal-based · `no stub (goal-based)`
T14 declares `atlassian → ^0.3`, unsatisfiable while the pack ships `0.2.2`, and
`verify.py`'s dependency step is a pass-through so nothing would catch it. Bump
`[pack].version` **and** `.claude-plugin/plugin.json` together —
`lint.py:1252-1258` (CAT_L009, ERROR) fails on a mismatch — **then run
`make build-self`**, because `.claude-plugin/marketplace.json` carries the pack
version and is drift-gated by the same `make build-check` this task's done-when
runs. A bump without regeneration reddens canonical 4 for every later task. This pack is then **removed from
T15's list**; AC29 carries the one-line exception.
**Done when:** canonical 4.

### T14 — Pack dependency declarations (AC33)

**Depends on:** T14a · **Mode:** goal-based · `no stub (goal-based)`

Add `[[pack.dependencies.required]]` on `credential-brokers` to `atlassian`
(`^0.3`), `figma` (`^0.2`) and `linear` (`^0.2`). **Done when:** a fixture
install of each pack without `credential-brokers` present fails the gate with a
message naming it; a fixture install **with** `credential-brokers` at `0.3.0`
succeeds for all three; canonical 4.

### T15 — Version bumps + regeneration (AC29) — **last**

**Depends on:** T11, T12, T13, T14 · **Mode:** goal-based · `no stub (goal-based)`
`credbroker` → 0.5.0 in **both** `pyproject.toml` `[project].version` **and**
`credbroker/__init__.py`'s `__version__`, plus the version assertion in
`tests/unit/test_sso_resolver.py` — all three carry 0.4.1 today, and the package
suite (canonical 1) runs **after** the bump so the drift is caught; and each of
`packs/atlassian` → 0.8.0,
`packs/figma` → 0.3.0, `packs/linear` → 0.2.0 — **`pack.toml` `[pack].version`
plus that pack's `.claude-plugin/plugin.json`**, since `lint.py:1252-1258`
(CAT_L009, ERROR) fails on a mismatch. `figma` and `linear` bump because T14
changes their published contents (the `[[pack.dependencies.required]]` block),
so leaving their versions stale ships changed packs under old numbers.
`packs/credential-brokers` is **not** here — T14a already bumped it, and owning
it twice is the contradiction AC29's exception line records. Then
`make build-self`. **Done when:** `git status` clean after `build-self`;
canonical **1** and 4; `[pack.adapter-contract]` unchanged; all five AC29 versions and
their `plugin.json` files agree; and the engine suites pass on **both** fixture
arms (source and projected) now that regeneration is final.

## Rollout

One PR. Releases `credbroker` 0.5.0 to PyPI and **four** packs through the
marketplace aggregate — `atlassian` 0.8.0, `credential-brokers` 0.3.0,
`figma` 0.3.0 and `linear` 0.2.0 — (`.apm` packs do not publish to PyPI — the bump PR *is*
the release). No feature flag: the token path is inert, and the SSO-cookie path
is dark until an enterprise pre-bakes `sso-config.toml`. Rollback is a revert; no
migration and no new persisted state. **Upgrade-time refusal:** AC33's install
gate turns a missing `credential-brokers` pack into an install failure for
`atlassian` / `figma` / `linear`; the gate message names
`agentbundle install credential-brokers --scope user` as the fix.

Behaviour changes to watch after release: `refresh` is now headless with a 20 s
silent-completion window and a new exit `5`, so a refresh that previously
prompted fails fast; the engine rejects `profile` values it
previously accepted and returns `4` where it returned `3`; `confluence-crawler`'s
registration inherits the new spawn bounds and its loader rejects configs it
previously accepted.

## Risks

- **The engine bug is the whole feature.** If AC6a regresses, recovery silently
  no-ops on macOS/Windows and CI stays green. T6's dual-store test is the guard;
  do not let it degrade to file-floor-only.
- **Exit-code change is a contract change.** Any other caller reading `3` as
  "not registered" breaks. T6 must re-read the existing engine assertions.
- **The typed subclass could over-narrow** — five sites now; tests assert each
  individually rather than asserting "recovery works".
- **Parity lint half-satisfied** — a one-sided edit fails at GATES, not at edit
  time. T9 ends with canonical 3.
- **Windows arms unverified** until T12's parity run — `taskkill` and the
  device-name behaviour are reasoned, not executed.

## Changelog

- 2026-08-05 — drafted (Shape A).
- 2026-08-05 — rewritten onto Shape D (recapture in `credbroker`) after the
  architect pass (5 spikes) and the design review's MAJOR REWRITE verdict;
  absorbs AC6a/AC6b (engine re-materialisation + exit 4), AC11 site 5,
  AC30–AC32, and the `packs/credential-brokers` bump reversal.
