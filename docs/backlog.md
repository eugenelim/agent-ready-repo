# Backlog — open items by spec

Single index of **open** work across every spec in `docs/specs/`. Each
item names the spec, the Acceptance Criterion (where one applies),
what's blocking it, and how it gets unblocked. Closed/shipped work is
**not** kept here — see each spec's Changelog and
[`product/changelog.md`](product/changelog.md).

This file is governance about *this repo's* evolution, not adopter
scaffolding. The adopter-facing **product roadmap** (strategy, not a
work index) lives at [`product/roadmap.md`](product/roadmap.md) (a
*Projected* path sourced from `packs/core/seeds/`). This file is the
tactical **backlog**: per-instance, no pack-side source, surfaces as an
`[info]` line under `make build-check` per AC6 of the self-hosting spec.
Deferred acceptance criteria point here by anchor (the `(deferred: <anchor>)`
marker — see RFC-0016).

## How this file is maintained

- Every spec records its own `Status:` field and `Acceptance Criteria`
  checkboxes. This file aggregates the **open** items so they're visible
  in one place — it is not the source of truth.
- When an AC closes or a spec ships, update the spec first, then **remove**
  the now-closed item here in the same PR (closed work lives in the spec
  Changelog / `product/changelog.md`, not here).
- When a new spec lands with open ACs, add a section here.
- If an item here is no longer accurate against the underlying spec,
  trust the spec and fix this file.

---

## `agent-spec-cli`

- **Deferred to a follow-up RFC** (named in RFC-0004): user-scope
  hook-wiring merge story (Rail B keeps hook-bearing packs
  user-scope-refused until it lands); `global` system-wide scope
  (absent, not reserved); new user-scope packs (the dimension shipped
  without a consumer).
- **Deferred to v1.1:** SSH git URL support in `install`
  (`git+ssh://…` exits non-zero with a "deferred to v1.1" message);
  full `--strict` `validate` against the v0.1 conformance fixtures
  (owned by RFC-0003's deferred F-conformance task).
- **Tier-2 upgrade prompt — v0.1 ships companion-drop only.** RFC-0001
  specifies a three-option in-CLI prompt on `agentbundle upgrade` Tier-2
  collisions (keep / overwrite with `.pre-update.bak` / invoke
  `adapt-to-project`). The shipped `upgrade.py` is non-interactive
  (writes a `*.upstream.<ext>` companion and continues); the
  `.pre-update.bak` overwrite path is unimplemented. **Unblocks when:**
  the interactive prompt + backup path are implemented, or RFC-0001's
  Tier-2 contract is amended to match the companion-drop-only shape.

## `adapt-to-project`

- **APM / Claude-plugins install-route nudge parity.** Adopters
  installing via APM or Claude-plugins never hit the install-marker
  write, the session-start nudge, or the chained `adapt.run`. The spec
  is CLI-only by contract; RFC-0004 parity work would close this.
  **Unblocks when:** APM/Claude-plugins adapter parity lands.
- **AC4b — deferred manual-QA rows.** v1 ships the AC4a automation/grep
  rows; AC4b's transcript rows stay open (see
  `specs/adapt-to-project/notes/manual-qa-matrix.md`):
  - Repo-scope class-2/3/4 transcripts (rows 8–16): Claude-simulated
    captures are recorded inline as preparatory evidence. **Closes when:**
    a real-adopter session replaces them with a real transcript.
  - User-scope LLM-judgment rows (rows 19–28). **Closes when:** the first
    pack declaring `allowed-scopes = ["user"]` lands.

## `dropped-primitives-coverage`

- **Auto-detect the v0.7 → v0.8 codex re-projection case** so `--force`
  (or `agentbundle upgrade`) re-projects under the new contract without
  the documented manual `uninstall + install` two-step. Named in the
  spec § Risks; deferred to a future RFC.

## `repo-scope-per-adapter-projection` / `pack-allowed-adapters`

- **codex-plugins install-route parity** (sibling RFC, not yet opened;
  modeled on RFC-0008's claude-plugins precedent). RFC-0012 § Alternatives
  #2 rejected building it inline.
- **Sibling RFC for repo-only-pack `allowed-adapters`** — deferred during
  RFC-0012 review as out of scope; opens as its own RFC when prioritised.
- **AC19 + plan T (lines 316/321/324) target the retired `add-credentialed-skill`
  skill.** The `add-credentialed-skill` author skill was deleted 2026-05-31
  (credential-broker-contract § Changelog; RFC-0013 § Errata). AC19's
  `allowed-adapters` author-guidance paragraph has no host skill any more —
  when this Draft spec is implemented, add that `allowed-adapters`
  author-guidance paragraph to the how-to
  `docs/guides/how-to/add-a-credentialed-skill.md` instead (the deleted
  skill's "Adapter portability" section was not carried over — it's
  pack-authoring guidance this spec owns). Left unfixed here to avoid
  editing another spec's open ACs out of scope; the references are
  warn-only (invariant iii).

## `user-scope-hooks`

Spec drafted from RFC-0005; **all 31 ACs open** (AC1–AC29 + AC17b + AC19b),
unblocking incrementally as tasks T1–T9 land code (T10/T11 amend sibling
specs). Two forks: Claude Code at user scope (`user-merge-json` into
`~/.claude/settings.json`) and Kiro at both scopes (`merge-into-agent-json`).

- **ADR is post-acceptance** (the array-append merge contract); lands
  after T1–T9, not gating.
- **First user-scope hook-bearing consumer pack — deferred** (RFC-0005
  § First consumer); correctness measured via fixture packs.

## `kiro-ide-hook`

Sibling of `user-scope-hooks` for RFC-0005's third surface (standalone
`.kiro/hooks/<name>.kiro.hook` IDE-event files). Non-probe tasks
(T-A/B/C1-4/D1) are landable in-session.

- **T-CONTRACT (v0.4 contract bump) — probe-gated.** Requires two probes
  against a real Kiro install: **Q6** (does Kiro recurse into
  `.kiro/hooks/<subdir>/`? glob `*.kiro.hook` or read every file?) and
  **Q11** (capture a real IDE-authored `.kiro.hook` to fix the canonical
  `ide-event`/`ide-action` vocabularies).
- **T-F (ADR) — post-implementation:** merge contracts + primitive-per-surface.
- **RFC drift in § State-file impact — deferred:** RFC-0005 describes
  uninstall as unconditional/verbatim; shipped `uninstall.py` is Tier-2
  warn-and-preserve. RFC text edit is a follow-up.
- **First `kiro-ide-hook` consumer pack — deferred.**

## `skill-secrets`

- **AC34, AC35 — inheritance invariants** (orphan-fixture guard; no live
  writes to developer keychain/dotfile). Enforced by every future test PR
  adding fixtures under `packages/agentbundle/tests/fixtures/creds/`.
- **New ADR ("Credential storage for credentialed skills")** is
  post-implementation (RFC-0006 § Follow-on artifacts); verify whether
  ADR-0003 (credential-broker) already subsumes it.

## `wire-session-start-hook`

- **Kiro session-start support — deferred to a separate spec.** Kiro has
  no true session-start event; the right primitive is `steering`, which
  the contract doesn't model. The parallel spec must introduce `steering`,
  decide build- vs install-time render from `patterns.jsonl`, pick
  `inclusion: always|auto`, and resolve scope-filtering.
- **`pre-pr.py` wiring.** No PR-open lifecycle event exists; `Stop` fires
  after every turn (wrong semantics). A behavior decision is required if
  anyone wants it auto-wired.
- **Latent — `cc-user-hooks` fixture produces flat shape** that Claude
  Code's schema rejects; the test only asserts JSON structure. Surfaces
  in `user-scope-hooks` or a follow-up.
- **R4 — pack↔pack `SessionStart` collision.** The merge-json
  `dict.update()` (`claude_code.py:101-103`) is key-level; a second pack
  wiring `SessionStart` wipes the first's array. Latent (no other pack
  wires it today).
- **R5 — repo-scope uninstall doesn't remove the merged entry.**
  `install.py` only populates `hook_wiring_owned` state at user scope.

## `apm-install-route-parity`

- **Deferred per AC17** (manual-QA rows 32-34): three live-install
  transcripts — `apm install` of core at project scope, `apm install -g`
  of converters at user scope, per-target characterisation at
  Copilot/Cursor/Gemini. Verification = transcript; rows exist (AC17
  closed), transcripts pending. Three uncovered HookIntegrator targets
  (Codex, OpenCode, Windsurf) run the documented `agentbundle adapt`
  fallback.

## `credential-broker-contract`

- **Manual-QA matrix — transcripts pending** (recorded under
  `specs/credential-broker-contract/notes/`):
  - `creds` × macOS — `/usr/bin/security` Tier-2; consuming skill resolves PAT.
  - `creds` × Windows — `advapi32.CredReadW`/`CredWriteW` Tier-2; consuming skill resolves PAT.
  - `creds` × Linux — dotfile floor; consuming skill resolves PAT.
  - `sso-cookie` × macOS — real corporate-SSO endpoint; headed Chromium `register`; `test` returns 0.
  - `sso-cookie` × Windows — same against the same endpoint.
  - `sso-cookie` × Linux — file-floor cookie jar; same flow.
- **Deferred security-hardening** (spec changelog 2026-05-26):
  - **D3 dotfile-read substring scan is bypassable by part-composition.**
    Rewrite as an AST walk over `open(…)` / `Path.read_text` /
    `Path.read_bytes` using `_path_chain_components`, asserting the
    resolved tail doesn't match the dotfile path under `Path.home()`.
  - **`_is_canonical_shim` byte-equality is a lint-time check, not a
    runtime tampering guard.** Path-anchor the exemption, or sign the
    canonical shim and verify at build time.
  - **Integration tests don't cover the projection path.**
    `_load_cli_module()` loads from pack source, not the projected
    `.claude/skills/…` mirror; parametrise over both.

## `agentbundle-wheel-release`

Implementation shipped (`.github/workflows/release-agentbundle.yml`, three
jobs: build-and-smoke / publish-pypi / publish-artifactory). One AC remains
open (AC14, Artifactory first-firing); the PyPI-side deferrals below resolved
with the first publish (`agentbundle-v0.2.0`, 2026-06-07) + PR-B.

### readme-route3-after-first-publish

**Resolved by PR-B (2026-06-07).** AC11 — README install-route-3 headline now
names `pip install agentbundle` directly; landed after the first PyPI publish
made the claim true.

### pypi-first-publish-gesture

**Resolved 2026-06-07.** AC13 — first PyPI publish (`agentbundle-v0.2.0`) via
Trusted-Publisher OIDC succeeded; clean-venv `pip install agentbundle` +
`agentbundle --help` smoke confirmed.

### artifactory-first-publish-gesture

AC14 — corp Artifactory publish first-firing. **Unblocks when:** the three
Artifactory secrets (`ARTIFACTORY_URL` / `ARTIFACTORY_USER` /
`ARTIFACTORY_TOKEN`) are configured and a tag is pushed.

## `event-contract-engine`

Shipped. AC8's drift-by-number quality gate is present as a prose checklist item,
as RFC-0018's resolved Open Q1 specified ("anchor both copies on the shared
`[#NNN]` numbers + a diff-by-number quality-gate item; no cross-skill file
dependency; escalate only if drift is observed in practice").

### drift-by-number-mechanical-gate

Quality-engineer review (post-ship) noted the by-number check is trivially
mechanizable: extract `[#NNN]` tokens from `api-contract/references/events.md`
ch. 19-21 and from the six `event-contract` phase rule files, fail on any
asymmetric difference (two `grep -oE '#[0-9]+' | sort -u` lists, compared).
**Deferred** — RFC-0018's Open Q1 deliberately chose the prose gate now and
"escalate to a shared file only if drift is observed in practice", and a CI lint
reading both skills' files is exactly the cross-skill dependency the RFC declined.
**Unblocks when:** drift between the two copies is observed in practice, or the
team decides to override the RFC's wait-and-see stance (then build a stdlib
`tools/` lint — mind the Windows bash→py and two-lint-surface wiring traps — and
wire it into `make build-check`).

## Cross-spec / outside-the-spec-tree

Open items called out by accepted RFCs or multiple specs, without a spec
of their own yet.

- **F-conformance fixtures (RFC-0003).** The per-adapter conformance suite
  `agentbundle validate --strict` would consume. Scoped out of v1; needs
  its own spec.
- **Copilot `agent`-projection enablement (RFC-0016 open question 1) — RESOLVED
  2026-06-05.** Shipped by [`docs/specs/copilot-full-parity/spec.md`](specs/copilot-full-parity/spec.md)
  (RFC-0024 / ADR-0013): copilot's `agent` primitive flipped `dropped` → `copilot-agent-md`
  (`.github/agents/<name>.agent.md`), `hook-wiring` → `copilot-hooks-json` (`.github/hooks/`),
  and copilot became user-scope-capable (contract v0.9 → v0.10). The `adversarial-reviewer`
  "Spec drift" check now reaches all four adapters. Open follow-ons under
  *copilot-full-parity* below.
- **Tier-1 lint invariant (iii) — promote to hard? (RFC-0016 open question 3).**
  Code-path references **shipped** in the `spec-code-ref-lint` spec (warn-only):
  `work-loop`'s `scripts/lint-spec-status.py` invariant (iii) now flags dangling repo-relative
  doc *and* code references. **Residual:** promoting (iii) from warn-only to a
  hard (exit-non-zero) invariant stays deferred — the measured baseline is ~16
  dangling code references in the corpus, almost all on Frozen specs whose
  bodies cannot be edited, so a hard gate would need that backlog cleaned first.
  Revisit once the warn rate is driven down (or a cleanup pass lands).
- **v2 RFC: Linux `libsecret` tier (RFC-0006).** Defers the Linux keyring
  tier to a v2 RFC alongside an adopter-profile audit (headless/SSH, WSL2,
  Docker, corporate fleet). Three integration paths on the table
  (`secret-tool` CLI, `gi.repository.Secret`, `ctypes` direct). Until then
  Linux lands on Tier 3 (dotfile).

- **`core-install-seed-delivery` reviewer nits (deferred, non-blocking).** Two
  cosmetic items from the issue #190 review, deferred as out of the change's
  scope: (a) `deliver_seeds`' `PathJailError` raise-path is exercised via
  `scaffold`'s monkeypatch test but `install`'s identical catch arm has no
  dedicated test — add one if the catch arms are ever touched; (b)
  `_strip_markdown_code` and `_collect_unresolved_markers` each carry a local
  `import re` (matches install.py's local-import idiom; hoist if the module is
  ever refactored to module-level imports). Neither affects behaviour.

- **`lint-plan-deps.py` is unwired (RFC-0015 / `wave-scheduled-supervisor` AC7).**
  AC7's deliverable `tools/lint-plan-deps.py` (repo-wide plan-DAG sweep) is invoked
  by **no gate** — not in `Makefile`, `.github/workflows/`, or `pre-pr` — and has no
  test; `adopter-clean-enforcement-gate` removed its last anchor (the `new-spec`
  `plan.md` template now points adopters at the shipped per-spec `loop-cohort
  schedule`). Decide in `wave-scheduled-supervisor`: wire it into `build-check` to
  enforce AC7 continuously, or retire it as redundant with `loop-cohort schedule`.
- **Credentialed-authoring skills don't belong in adopter-facing `core` (RFC-0013 /
  `credential-broker-contract`).** From first principles the adopter artifact for
  *authoring* a credentialed skill is the **how-to** — which already exists
  (`docs/guides/how-to/add-a-credentialed-skill.md` + `docs/guides/explanation/credentialed-skills.md`).
  The `add-credentialed-skill` **skill** is redundant for adopters and bound to the
  catalogue build pipeline (`make build-self`, `assets/` templates), and
  `example-credentialed-skill` is `auth: creds` (same coupling). Reconcile their
  adopter-shipping — demote to catalogue-local / retire in favour of the how-to —
  against `credential-broker-contract` AC27/AC43 and RFC-0013 §7. Not touched by
  `adopter-clean-enforcement-gate` (that spec owns these primitives).

---

## `product-brief-intake`

- **Follow-up (reviewer-flagged, not an unmet AC):** the adopter-facing
  leak guard (no `agent-ready-repo` / `RFC-NNNN` / catalogue-spec-name) is
  enforced by `tools/lint-seeds.py` for **seed** files only. The shipped
  `receive-brief/SKILL.md` and `receive-brief/examples/*.md` live under
  `packs/core/.apm/skills/` and are outside that lint's scope — clean today by
  inspection, but unguarded against regression. Extend the seed-content
  blocklist (or `tools/lint-agent-artifacts.py`) to cover shipped-skill bodies
  and `examples/`. Pre-existing catalogue gap surfaced by this spec, not
  introduced by it.

## `credbroker`

RFC-0023 follow-on, **Phase 1 shipped 2026-06-09** (`docs/specs/credbroker/`,
Status: Shipped). The items below are deferred out of Phase 1 by spec decision.

**Doc follow-ups (deferred from T10 — stale shim/projection prose outside T10's named scope):**
- `docs/architecture/credentials.md` still documents the build-projected
  `credentials_shim` model as the `creds` delivery; after RFC-0023 the
  `creds` resolver is the `credbroker` library (the projected shim survives
  only as the adapter-root-bins companion for `sso-broker`). Rewrite the
  architecture map for the credbroker delivery. The `docs/architecture/overview.md`
  one-liner pointing at `credentials.md` moves with it.
- `docs/guides/how-to/install-agentbundle-from-clone.md` references the
  projected shim; reconcile with the `pip install credbroker` model.
  **Unblocks when:** picked up as a docs pass (no code dependency).

**credbroker-user-scope T3 review follow-ups (non-blocking):**
- **`_vault.py` module-docstring imprecision.** `packages/credbroker/credbroker/_vault.py:5`
  reads as if `_vault` itself defers the crypto import, but the lazy boundary is at the
  *package* level — `_core`/`__init__` import `_vault` lazily, so the base graph stays
  third-party-free even though `_vault`'s own top level pulls `cryptography`/`argon2`.
  Reword to "the vault *module* is imported lazily by the resolution core." Must fix the
  **source** package, not the vendored floor copies (`.agentbundle/lib/credbroker/_vault.py`
  + `packs/credential-brokers/.apm/user-libs/credbroker/_vault.py`), which are byte-faithful
  projections — re-run `make build-self` after to re-sync them. **Unblocks when:** picked up
  as a `packages/credbroker` docs pass (no code dependency).

**T5 review follow-ups (non-blocking, surfaced by the T5 review):**
- **Per-key vault KDF re-derivation.** `load_credentials` resolves `required_keys`
  one at a time; for a vault-backed namespace each key that reaches Tier 3 opens
  the vault afresh, re-running the deliberately-slow Argon2id (Profile A). For
  *N* vault-resolved keys that's *N* derivations (~150 ms each). Accepted for
  Phase 1 (resolution is once-per-command and *N* is small — often 1–2 secret
  keys, the rest at env/dotfile tiers). **Unblocks/­revisit when:** a
  high-key-count vault-backed namespace appears — then hoist `Vault.open` to once
  per `load_credentials` call.
- **Windows ACL parity for the vault master file.** The `0600` master-file branch
  enforces a POSIX mode check (refuse group/other-readable); the Windows side has
  no `_verify_icacls` check on the master-file *read* (consistent with the dotfile
  *read*, which also skips it — only writes run `icacls`). Consider running
  `_verify_icacls(master_file)` in the file branch on Windows for symmetry with
  the POSIX refuse. **Unblocks when:** Windows master-file hardening is prioritised
  (the helper already exists, import-free).

### credbroker-phase-2

**Phase 2: PyPI publication + version pinning** (the spec's final, deferred AC). Publish `credbroker`
to PyPI and switch the six consumers from the repo-path install
(`pip install -e ./packages/credbroker`) to a pinned PyPI version. This is what
unblocks the **APM / Claude-plugin adopter who has no repo** — until it ships,
that profile stays on env Tier-1 or the projected shim. Gated on the package
stabilising (not a date), per RFC-0023 § Delivery. **Unblocks when:** the
`credbroker` public surface is stable and a maintainer is ready to own a PyPI
release cadence.

**Name-registration decision (2026-06-07):** RFC-0023 recommended a *defensive*
placeholder upload to reserve the `credbroker` name as soon as it was fixed. The
maintainer **declined the interim placeholder** and will instead claim the name
with the **real Phase-2 publish when the package is ready** — accepting a small
interim squat risk on the name. (A PyPI *pending* Trusted Publisher does **not**
reserve the name — per the PyPI docs, only an actual upload does — so reservation
and the first real release are the same event here.) Publication is **token-free
via Trusted Publishing (OIDC)**, modelled on `release-agentbundle.yml`; the
`release-credbroker.yml` workflow + the PyPI pending-publisher config are Phase-2
artifacts, created when the publish is ready, not now.

## `credbroker-user-scope`

Open follow-ons surfaced during T4 (install-time user-scope delivery rail) review:

### floor-delivery-graceful-skip-on-missing-prefix
The T4 floor delivery writes under `.agentbundle/` via `safety.write_jailed`, which
relies on the resolved user adapter's `allowed-prefixes.user` containing `.agentbundle/`.
Every shipped adapter declares it, so this is unreachable today; but a future adapter
added without `.agentbundle/` in its user prefixes would make the floor `write_jailed`
raise `PathJailError` and **hard-abort the whole install** rather than skip the floor
rail. Follow-on: have `_deliver_user_scope_floor` detect a prefix list lacking
`.agentbundle/` and skip the rail with a stderr note (graceful degrade), or add
`.agentbundle/` to `_adapter_allowed_prefixes_user`'s defensive fallback. Deferred:
no second caller exists, and adding speculative degradation now is scaffolding for a
hypothetical adapter.

### floor-reference-counting-on-uninstall
The vendored floor (`~/.agentbundle/lib/credbroker/`) and the `sso-broker` bin scripts
are shared, idempotent infrastructure, so T4 deliberately does **not** record them in
any pack's `state.files` — uninstalling one credentialed pack must not strip a
co-installed pack's floor. The consequence: uninstalling the *last* credentialed pack
leaves the executable `~/.agentbundle/bin/sso-broker.py` (0o755) and the importable
floor behind indefinitely (owner-owned, mode-correct — no exploit on its own, but a
latent stale broker). Follow-on: a reference-counted `uninstall` that removes the floor
only when no credentialed pack remains. Deferred: out of T4's delivery scope.

## `copilot-full-parity`

Shipped 2026-06-05 (RFC-0024 / ADR-0013 → [`docs/specs/copilot-full-parity/spec.md`](specs/copilot-full-parity/spec.md)):
copilot became a full-parity, user-scope-capable adapter — `agent` →
`copilot-agent-md` (`.github/agents/`), `hook-wiring` → `copilot-hooks-json`
(`.github/hooks/`), `hook-body` retargeted to `.github/hooks/`, `skill` gained a
`~/.copilot/instructions/` user target; contract v0.9 → v0.10; two-pack bump
(`core`, `research`). Open follow-ons:

- **Copilot `command` / prompt projection.** `command` stays `dropped` until the Copilot CLI
  loads custom slash commands (copilot-cli#618/#1113). A follow-on RFC flips it to a tested
  `.github/prompts/` target once the feature lands — not projected speculatively.
- **`WebFetch` / `WebSearch` re-map.** Copilot exposes no web tool to custom agents (verified
  CLI 1.0.59), so `research`'s retrieval subagents lose live web access on Copilot (documented
  degradation — read/grep/glob only). When Copilot exposes a custom-agent web tool, a fresh
  probe against the then-current CLI can add the mapping to `copilot-agent-frontmatter`.
- **Per-shell hook commands.** `copilot-hooks-json` carries the shell-agnostic source command
  into both `bash` and `powershell` handler keys. A wiring with per-shell commands would need a
  source-side shape extension — out of scope; no shipped wiring needs it.
- **Repo-scope hook execution on Copilot CLI ≥ 1.0.60 (CLI-side).** The AC23 live smoke
  (2026-06-05, CLI 1.0.60) found that repo-scope `.github/hooks/*.json` wiring **is not executed**
  by the CLI — the artifact is byte-correct and correctly placed, the identical user-scope hook
  (`~/.copilot/hooks/`) fires, and the CLI loads `.github/agents/` fine, but no repo-scope hook
  entry appears in the debug log. This is **version-sensitive**: RFC-0024 § Acceptance Runs 2–4
  verified repo-scope hooks firing on **1.0.59**, so execution regressed (or gained a trust gate
  requiring repo approval) between 1.0.59 and 1.0.60. Our projection is forward-compatible and
  needs no change. Follow-up: re-probe on the then-current CLI, determine whether it's a
  regression or a new repo-hook trust/opt-in gate (file upstream if a regression), and record the
  outcome. Subagent discovery + read-only + user-scope hooks/instructions all pass on 1.0.60.
- **User-scope hook-command resolution.** `copilot-hooks-json` rewrites a carried command's
  `tools/hooks/` prefix to the repo-scope `.github/hooks/` so the wiring references the body
  where `direct-file` lands it. At **user** scope the body lands at `~/.copilot/hooks/` and the
  session CWD is arbitrary, so a relative command path won't resolve — an unsolved follow-on.
  Not exercised today: `core` (the only hook-body pack) is repo-only; no shipped pack ships a
  user-scope copilot hook. Needs a fresh probe of Copilot's user-scope hook CWD semantics.
