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
- **Resolved-tombstone exception.** Retain a closed item (marked
  `**Resolved <date>.**`, kept terse) instead of removing it when a durable
  artifact still links its `#anchor` — a frozen RFC amendment, or a spec's
  checked AC — so the inbound link doesn't dangle. The full record still lives in
  the spec/changelog; the tombstone is just the anchor's landing page.
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
  `docs/guides/credential-brokers/how-to/add-a-credentialed-skill.md` instead (the deleted
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

## `architect-knowledge-surfaces`

### architect-review-diagram-knowledge-surfaces

**Resolved 2026-06-13.** All three sibling skills now carry knowledge-surface
awareness: `architect-design` (consult-to-build, all eight areas; pack `0.3.0`),
`architect-review` (verification lens that *checks* a design was grounded; pack
`0.4.0`), and now **`architect-diagram`**
(`docs/specs/architect-diagram-knowledge-surfaces`, pack `0.5.0`) — an
**as-is-drawing consult lens** scoped to the **descriptive current-system facets
(the 2/3/4 seam: current landscape, interfaces & contracts, operational
reality)**, *not* the current-landscape area alone, and gated to **document and
update mode** (design mode draws the hypothetical and review mode routes to
`architect-review`, so neither triggers it). This tombstone is **retained** (not
removed) because the Shipped `architect-review-knowledge-surfaces` spec links
this `#anchor` (its `Ask first` Boundary + AC16).

**The `product-engineering` sibling has also shipped**
(`docs/specs/product-engineering-knowledge-surfaces`, product-engineering pack
`0.3.0`): `frame-intent` gained the problem-framing-lens projection (domain,
in-flight, brownfield-landscape, operational), guarded against drift from the
architect canonical core by `tools/lint-knowledge-surface-parity.py` (which the
`architect-diagram` PR extends to register the fourth copy + its self-test).

**The whole knowledge-surface line is now shipped** — `architect-design`,
`architect-review`, `architect-diagram`, and the `product-engineering`
`frame-intent` sibling. Nothing remains open under this anchor; the tombstone is
retained only because the Shipped sibling specs link it.

### live-mock-mcp-detection-qa

The detection QA (`architect-design`/`architect-review` per their specs,
`architect-diagram` per `architect-diagram-knowledge-surfaces` AC13, and
`frame-intent` per `product-engineering-knowledge-surfaces` AC13) was verified in
two halves: a real structural projection check (`make build` → projected
artifacts byte-identical to source) and a decision-logic walkthrough by an
independent agent. The walkthrough *described* per-scenario tool presence rather
than exercising a **live mock MCP knowledge tool**, because the authoring harness
can't inject one. **Each skill's live-mock run is pending under this one
anchor** — landing a live run for one does not satisfy the others. **Unblocks
when:** a harness/test fixture can register a stub MCP retrieval tool, at which
point the present/absent/sensitive (and, for `frame-intent`, brownfield)
scenarios can run end-to-end against real detection for each skill.

- **`architect-diagram` contradicted-edge rail — walkthrough coverage gap
  (quality-engineer, 2026-06-13).** The `architect-diagram-knowledge-surfaces`
  T5 walkthrough exercised honesty rails (a) name-what-drew-from and (b)
  `<unnamed>`-or-ask, but rail (c) — *a surface-derived edge the repo contradicts
  is flagged, not drawn over* — is **read-verified only**, because the fixed
  single-edge driver carries no contradiction. This needs no MCP injection (a
  two-fact driver: surface says edge X→Y, repo shows X→Z). **Fold into the fixture
  work above:** when the stub-surface fixture lands, extend the driver with a
  contradicting fact so rail (c) gets scenario-level proof like (a)/(b).

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
  (`docs/guides/credential-brokers/how-to/add-a-credentialed-skill.md` + `docs/guides/credential-brokers/explanation/credentialed-skills.md`).
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

**Resolved 2026-06-10.** `credbroker 0.1.0` was published to PyPI by
`release-credbroker.yml`'s OIDC Trusted-Publishing job on tag `credbroker-v0.1.0`
(token-free, modelled on `release-agentbundle.yml`). The first real upload claimed
the `credbroker` name, so the **no-repo APM / Claude-plugin adopter** can now
`pip install credbroker` (or `credbroker[crypto]`) — the profile RFC-0023's
pre-mortem flagged as stranded. The six consumers carry a `credbroker>=0.1.0`
floor. The `credbroker` spec's final AC is checked. This tombstone is **retained**
(not deleted) because the spec AC, the credbroker plan, and the RFC-0023 amendment
still reference the `#credbroker-phase-2` anchor — same pattern as the resolved
`agentbundle-wheel-release` items above.

**Name-registration decision (2026-06-07, as executed):** RFC-0023 recommended a
*defensive* placeholder upload to reserve the `credbroker` name as soon as it was
fixed. The maintainer **declined the interim placeholder** and claimed the name
with the **first real publish** instead — accepting a small interim squat risk. (A
PyPI *pending* Trusted Publisher does **not** reserve the name — per the PyPI docs,
only an actual upload does — so reservation and the first release were the same
event, which is how it played out on 2026-06-10.)

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

### active-with-credbroker-pip
The "active B" convenience — an `agentbundle install … --with-credbroker` flag that
**auto-runs `pip install credbroker[crypto]`** during install, instead of leaving pip
a separate user step — is deferred (spec Boundaries → *Ask first*). It is not an unmet
acceptance criterion: the shipped vendored floor (layer 1) already gives a no-repo
user-scope install full Tier-1/2/3 resolution with zero pip, so auto-pip is a
*convenience* (it would auto-enable the encrypted `[crypto]` vault, layer 2), not a
correctness gap. **Deferred because** the open risk is interpreter/venv targeting —
which Python `install` would pip *into* (the consumer skill runs under whichever
interpreter invokes it, not necessarily the one `agentbundle` runs under), and a wrong
target silently lands the package where the skill can't import it. **Unblocks when:** a
concrete adopter need surfaces **and** the interpreter/venv-resolution question is
settled (then surface it before wiring, per the spec's *Ask first* boundary).

## `copilot-full-parity`

Shipped 2026-06-05 (RFC-0024 / ADR-0013 → [`docs/specs/copilot-full-parity/spec.md`](specs/copilot-full-parity/spec.md)):
copilot became a full-parity, user-scope-capable adapter — `agent` →
`copilot-agent-md` (`.github/agents/`), `hook-wiring` → `copilot-hooks-json`
(`.github/hooks/`), `hook-body` retargeted to `.github/hooks/`, `skill` gained a
`~/.copilot/instructions/` user target; contract v0.9 → v0.10; two-pack bump
(`core`, `research`). Open follow-ons:

- **Copilot `command` / prompt projection.** `command` stays `dropped` — the Copilot CLI won't
  load custom slash-command files by design (copilot-cli#618/#1113 closed; prompt files
  superseded by skills, which the catalogue projects to Copilot as `.github/skills/<name>/SKILL.md`).
  A follow-on RFC would only flip it to a tested `.github/prompts/` target if Copilot ships such a
  surface — not projected speculatively.
- **`WebFetch` / `WebSearch` re-map. — RESOLVED 2026-06-11** by
  [`docs/specs/copilot-skills-and-web/spec.md`](specs/copilot-skills-and-web/spec.md)
  (RFC-0024 § Errata E1). Copilot custom agents *do* get the `web` tool on the
  CLI + app — the official custom-agents reference documents `web` aliasing
  `WebSearch`/`WebFetch`; `WebFetch`/`WebSearch` already pass through verbatim
  and resolve to it, so `research`'s retrieval subagents keep live web access
  (no mapping needed). The earlier "no web tool" finding was a confounded CLI
  1.0.59 probe. The only residual non-coverage is the Copilot **cloud agent**.
- **Per-shell hook commands.** `copilot-hooks-json` carries the shell-agnostic source command
  into both `bash` and `powershell` handler keys. A wiring with per-shell commands would need a
  source-side shape extension — out of scope; no shipped wiring needs it.
- **Repo-scope hook execution on Copilot CLI — trust/opt-in gated (CLI-side).** The AC23 live
  smoke (2026-06-05, CLI 1.0.60) found that repo-scope `.github/hooks/*.json` wiring **was not
  executed** — the artifact is byte-correct and correctly placed, the identical user-scope hook
  (`~/.copilot/hooks/`) fires, and the CLI loads `.github/agents/` fine, but no repo-scope hook
  entry appeared in the debug log. **Re-verified 2026-06-11 against the live copilot-cli changelog
  + issues (latest CLI 1.0.61, 2026-06-09):** repo `.github/hooks/` is a supported, loaded source,
  but loading is **conditional** — the CLI loads repo hooks only after folder-trust is confirmed
  (changelog 1.0.8) and, in prompt mode (`-p`), behind an opt-in (changelog 1.0.41 / 1.0.51). So
  the 1.0.60 non-execution is most plausibly the trust/opt-in gate, **not** a scope-wide regression
  (the 1.0.59 firing in RFC-0024 Runs 2–4 presumably ran in a trust-approved folder — the runs
  did not record the trust state, so this is inference, not a logged fact). Known **open** conditional bugs
  to watch, not a blanket failure: repo hooks are skipped on `--resume`
  ([copilot-cli#1503](https://github.com/github/copilot-cli/issues/1503), open); and plugin-defined
  `preToolUse` hooks (distinct from repo `.github/hooks/`) don't fire
  ([copilot-cli#2540](https://github.com/github/copilot-cli/issues/2540), open). Our projection is
  forward-compatible and needs no change. Follow-up: a live smoke on 1.0.61 with the folder trusted
  to confirm repo-hook firing, then close or re-scope this item. Subagent discovery + read-only +
  user-scope hooks/instructions all pass.
- **User-scope hook-command resolution.** `copilot-hooks-json` rewrites a carried command's
  `tools/hooks/` prefix to the repo-scope `.github/hooks/` so the wiring references the body
  where `direct-file` lands it. At **user** scope the body lands at `~/.copilot/hooks/` and the
  session CWD is arbitrary, so a relative command path won't resolve — an unsolved follow-on.
  Not exercised today: `core` (the only hook-body pack) is repo-only; no shipped pack ships a
  user-scope copilot hook. Needs a fresh probe of Copilot's user-scope hook CWD semantics.

### Untrusted-catalogue inside-tree symlink exfiltration at install time (cross-adapter)

- **Surfaced by the `copilot-skills-and-web` security review (2026-06-11); pre-existing,
  not introduced by that PR.** `agentbundle install` resolves an arbitrary catalogue pack and
  calls `render_pack(pack_dir)` with **no `lint_pack` gate**; `render.py::_collect_tree` does
  `path.read_bytes()`, which **dereferences inside-tree symlinks** in the pack. A malicious pack
  shipping `.apm/skills/x/leak -> /etc/passwd` lands the target's bytes under an in-jail relpath
  (`.github/skills/x/leak` repo, `.copilot/skills/x/leak` user) — the path-jail passes (the
  relpath is in-jail) and the secret is written to the adopter's disk. This is a property of
  **all four `direct-directory` adapters** (claude-code/kiro/codex/copilot all funnel through
  `_collect_tree`); the skill flip brought copilot to parity with the others, it did not create
  the hole. The adapter-level top-of-tree symlink skip + `symlinks=True` copytree does **not**
  close it. **Amplified on the Python 3.11/3.12 floor** (`requires-python >= 3.11`): `Path.rglob`
  follows directory symlinks before 3.13, so a `dirlink -> /etc` would recurse and slurp the whole
  target tree. *Fix options* (cross-adapter, one of): gate the install-path `render_pack` with
  `lint_pack` (already flags inside-tree symlinks at `build/lint_packs.py`), or make `_collect_tree`
  skip/refuse symlinked entries (prefer `os.walk(followlinks=False)` over `rglob` so the 3.11 floor
  and 3.13 behave identically). Warrants its own spec — spans `render.py` + `install.py` + every
  adapter, out of scope for the copilot skill flip. This is the install-time delivery facet of
  the standing untrusted-catalogue symlink-guard concern.

## `projection-dry-run`

### install dry-run preview governance seeds

- **`install --dry-run` previews the rendered adapter projection only.** The
  preview walks the per-adapter projection (`.claude/…`, `tools/…`) and labels
  each file via `_classify_for_install`. It does **not** enumerate the
  governance **seeds** a real repo-scope install also delivers (`AGENTS.md`,
  `docs/CHARTER.md`, `docs/CONVENTIONS.md`) — those go through
  `_common.deliver_seeds`, a content-equality delivery path distinct from the
  tier classifier. **Blocking:** previewing seeds without writing needs
  `deliver_seeds` split into a read-only classify half + a write half (today
  it writes as it walks); the spec forbids forking the classifier or writing
  under `--dry-run`, so the no-cost path is a refactor, not a copy. **Unblock:**
  extract `deliver_seeds`' classification into a pure function both the dry-run
  preview and the real delivery call. Disclosed in the
  [preview how-to](guides/_shared/how-to/preview-install-or-upgrade.md) so the
  preview's silence on seeds is stated, not implied-complete.

### unify the path-jail projection probe

- **The prefix-jail rule has three near-verbatim copies.** install's standalone
  Step 8 probe (`install.py`), the new `upgrade --dry-run` probe (`upgrade.py`),
  and `safety.write_jailed`'s inline prefix block each re-implement "resolve the
  target, assert it's under the root, assert it starts with an allowed prefix
  (directory-boundary match)." A change to the matching semantics must touch all
  three or they drift. **Blocking:** the clean fix extracts a read-only
  `safety.assert_projection_jailed(root, relpaths, allowed_prefixes, *, command)`
  and routes install Step 8, the upgrade dry-run probe, **and** the real upgrade
  write loop through it — but rewiring the non-`--dry-run` write loop was out of
  scope for the dry-run spec (*Never do: change non-`--dry-run` behavior*).
  **Unblock:** a focused refactor PR that introduces the helper and migrates all
  three call sites under its own regression coverage.

## `cursor-full-parity`

Shipped 2026-06-11 (RFC-0026 / ADR-0015 → [`docs/specs/cursor-full-parity/spec.md`](specs/cursor-full-parity/spec.md)):
new native `cursor` full-parity adapter projecting all five primitives to `.cursor/*` at both
scopes (skill → `.cursor/skills/`, agent → `.cursor/agents/<name>.md` with `tools` dropped +
`readonly` derived, hook-body → `.cursor/hooks/`, hook-wiring → `.cursor/hooks.json`, command →
`.cursor/commands/`); contract v0.10 → v0.11, no new projection mode, no schema change;
distribution-only. Open follow-ons:

- **Live Cursor smoke.** RFC-0026 § Evidence verified the `.cursor/*` paths and the agent /
  hook / command vocabularies against current Cursor docs, but no test loads the generated
  artifacts on the real tool (mirrors the copilot AC23 smoke, not gated here). Follow-up: drop a
  generated `core` `.cursor/` tree into a Cursor workspace + `~/.cursor/`, confirm skills /
  subagents / commands load and the `readonly` reviewers are restricted, and record the Cursor
  version + per-primitive results.
- **Agent `model` alias map.** The `cursor-agent-frontmatter-v0.11` mapping passes `model`
  through verbatim (our aliases `opus`/`sonnet`/`haiku`). Cursor resolves a known id or falls
  back to inherit; if a shipped alias proves unresolvable on the live tool, add a
  Cursor-model-id `values` map (the kiro precedent) after a probe.
- **Nested-symlink read at install time — cursor hardened; siblings remain (cross-adapter).**
  `cursor.py`'s `_project_direct_directory` now copies with `ignore=_ignore_symlinks`, so a
  **nested** symlink inside a skill dir is dropped (not reproduced), closing the install-time
  read-through for cursor (RFC-0026 ride-along, with a regression test). **`kiro.py`, `codex`,
  `copilot`, and `claude-code` still copy nested symlinks via `copytree(..., symlinks=True)`** —
  the same install-time exposure (flagged by the cursor security review as shared, not
  cursor-introduced). Follow-up: lift cursor's symlink-skipping copy into a **shared** helper
  (e.g. `projections/direct_directory.py`, which already hosts `sweep_orphans`) and adopt it in
  the other four adapters so they stop reproducing nested symlinks.
- **Block-style YAML `tools:` over-privileges on parse miss (cross-adapter, shared).** The
  line-oriented `_parse_frontmatter` (duplicated from `kiro.py`) reads inline `[...]` and
  comma-string `tools:` but not a multi-line YAML block list; an agent using block syntax would
  parse to no `tools`, so `_derive_readonly` omits `readonly` (writable). Shipped packs use the
  inline/comma form, so this is latent. If block-list frontmatter ever ships, the shared parser
  needs a multi-line list branch (fix once, across kiro + cursor).
- **Lexical contract-version compare (`install.py` Step 4b) — RESOLVED (RFC-0026 ride-along).**
  `_resolve_target_adapter`'s Step-4b gate was `contract_version >= "0.7"`, a lexical compare
  (`"0.11" < "0.7"` lexically). Replaced with the numeric `scope.contract_version_at_least`
  helper + a regression test pinning `"0.11" >= "0.7"`. It was latent (both branches returned
  `DEFAULT_ADAPTER`); the v0.11 bump pushed it into live two-digit territory, so the inline
  comment's "two-digit minor bumps → move into a helper" was honored now.
- **Pack opt-in for credentialed CLIs — RFC-0013-gated, catalogue-wide. Resolved 2026-06-12.**
  PR #273 added `cursor` to no pack's `allowed-adapters`; #276 opted the two non-credentialed
  full-parity packs (`research`, `architect`) in. The 5 credentialed packs (atlassian, contracts,
  converters, figma, credential-brokers) now declare
  `["claude-code", "kiro-ide", "codex", "copilot", "cursor"]` via **RFC-0013 § Errata
  (2026-06-12)** — both full-parity adapters already declare `.agentbundle/` in
  `allowed-prefixes.user` (the § 4d precondition), and the broker delivery rail is
  adapter-agnostic; verified by real cursor/copilot installs of the broker + a consumer pack. No
  contract change. Full record: RFC-0013 § Errata + `docs/specs/credential-broker-contract/spec.md`
  § Changelog (2026-06-12).

## `gemini-full-parity`

Follow-ons deferred from the gemini-full-parity implementation (RFC-0027 / ADR-0016).
None blocks the shipped adapter; each is a bounded enhancement.

### context-bridge-without-core

The `context.fileName = ["AGENTS.md", "GEMINI.md"]` bridge is written in the single
hook-wiring `.gemini/settings.json` write (the single-writer / cursor model — repo-scope
install writes merge-json targets whole-file, so a per-pack settings.json would clobber
another pack's hooks). Consequence: an adopter who installs *only* a non-`core` pack with
`--adapter gemini` (no shipped hook-wiring) gets no `settings.json`, so an `AGENTS.md` of
their own is not bridged. Every catalogue adopter installs `core` (which ships both the
session-start wiring and `AGENTS.md`), so the bridge lands in practice. The clean fix —
emit `context` whenever an `AGENTS.md`/`GEMINI.md` exists at the install root regardless of
wiring — needs install-time merge-json (the adapter renders to an isolated tempdir and
cannot see the install root, and the install writer overwrites merge targets whole-file).
Out of scope for the adapter PR.

### command-positional-arg-context-aware-guard

`gemini_command_toml`'s fail-closed positional-argument guard matches `$<digit>` body-wide,
so a literal dollar-amount in prose (`$10/month`) or a `$1` inside a fenced code block also
refuses the build. Fail-closed (a loud, actionable error — never a silent bad emit), and no
shipped command contains a `$<digit>`. A context-aware parser (skip fenced/inline code,
require an injection-shaped token) would remove the false positives.

### hook-body-path-rewrite-anchor-cross-adapter

`_rewrite_hook_body_path` does an unanchored `command.replace("tools/hooks/", ".gemini/hooks/")`,
so a command carrying `tools/hooks/` in a second position (an argument, a comment) is also
rewritten. Source commands are catalogue-controlled (not adopter input) and this is
byte-identical to the merged `cursor.py` / `copilot_hooks_json.py` precedents — no live
exploit. When the rewrite is consolidated into a shared cross-adapter helper, anchor it to the
command-leading token.

### frontmatter-quote-unescape-cross-adapter

`_parse_frontmatter` strips outer quotes but leaves inner `\"` literal; `_serialize_frontmatter_md`
then escapes the backslash, so a frontmatter `description` carrying escaped quotes round-trips
double-escaped (`\\\"…\\\"`). This is **byte-identical to the merged `cursor.py`** (an inherited
cross-adapter behavior, not a gemini regression). Fix both adapters together: unescape `\"`→`"`
in the quote-stripping branch.

## `house-voice-writing-craft`

### apm-leak-lint-rfc

A `lint-seeds`-analogue for `packs/*/.apm/**` that mechanically catches
internal-governance citations (RFC/ADR numbers, `docs/specs|rfc|adr` paths,
`make`/`tools/lint` references, "this catalogue" identity asides) in shipped
skills, agents, commands, and hooks. Today the rule is hand-checked
(`AGENTS.local.md` § "Shipped pack content carries no internal-governance
citations"). Adding the lint is a new convention and therefore RFC-gated;
open an RFC before building it.

A 2026-06-13 sweep found the `core` pack still carries ~10 such references in
shipped `.apm/**` that a hand-pass left in place — `work-loop/SKILL.md` (an
`RFC-0025` reference; a `make build-check` mention), `hooks/pre-pr.py` ("this
catalogue's own"), the work-loop and receive-brief `scripts/` (`make
build-check` in comments), `hook-wiring/session-start.toml` (`make
build-self`), and `adapt-to-project/assets/reference.md` ("this catalogue").
These were left untouched deliberately: sweeping the most sensitive pack
(work-loop's `SKILL.md` carries a byte-identical risk-trigger block mirrored
across four files) is exactly the systematic job the lint should drive, not a
hand-sweep. Land the lint under the RFC, then do the sweep under it.
(`RFC-1918` in `security-checklists/references/outbound-ssrf.md` is a real IETF
standard, not an internal citation — leave it.)

## `apm-internal-ref-sweep`

### credbroker-frozen-pack-ref-sweep

The `credential-brokers` pack's shipped `.apm/**` carries `RFC-0023` / `RFC-0006`
citations in `skills/credential-setup/scripts/setup.py` and the
`user-libs/credbroker/` library docstrings/comments (`__init__.py`, `_core.py`,
`_vault.py`). These are the same dangling-on-arrival class the `apm-internal-ref-sweep`
cleaned from core + figma, but the pack is **frozen by RFC-0013 (§4/§4d)** and
the citations sit in library-provenance docstrings rather than agent-facing
prose, so they were left for a separate, deliberate pass that respects the
freeze. Fold this into the `apm-leak-lint-rfc` work, or do it as a focused
comment-only PR against the frozen pack with explicit sign-off.

## architect-rubric-parity-guard

### design-reviewer-rubric-drift

`packs/architect/.apm/agents/design-reviewer.md` (RFC-0032) inlines a condensed
copy of `architect-review`'s verdict scheme, severity glossary, and 🔧/🧭
mechanical-judgment taxonomy — guarded only by a one-time authoring
byte-faithfulness diff plus a prose note, per the pack's standing
duplication-over-DRY convention. There is no mechanical guard forcing the agent
copy to reconcile when `architect-review/SKILL.md` or `rubric-well-architected.md`
next changes those labels/definitions. Note this is **not** a new gap unique to
the agent: the same verdict/severity rubric is already duplicated
`architect-design`↔`architect-review` without a parity guard (the existing
`tools/lint-knowledge-surface-parity.py` covers only the *knowledge-surface*
taxonomy, not these rubrics). A guard here would therefore also imply guarding
that pre-existing duplication — a deliberate design call beyond RFC-0032's scope.

Deferred from the `architect-design-reviewer` quality-engineer pass (Concern 1).
If pursued: extend `lint-knowledge-surface-parity.py` (or add a sibling lint) to
assert the verdict labels / severity glyphs / mechanical-judgment definitions are
byte-identical across `architect-design`, `architect-review`, and the
`design-reviewer` agent, wired into CI alongside that lint. Weigh against the
pack's duplication-over-DRY principle first — it may be a deliberate non-goal.

### design-reviewer-cursor-readonly-projection-assertion

The `architect-design-reviewer` projection test asserts the agent lands under
each adapter's `agents/` route but not that the `cursor` adapter emits
`readonly: true` for it (cursor's documented degradation that makes "flag, never
rewrite" hold for that target). The generic readonly-derivation mechanism is
already covered by `test_adapter_cursor.py`, so this is a coverage-tightening
nit, not a gap. Deferred from the quality-engineer pass (Nit 2); if pursued, add
a one-line `assertIn("readonly", …)` to the cursor subTest.
