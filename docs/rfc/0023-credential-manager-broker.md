# RFC-0023: `credbroker` — a standalone, pip-installable credential library replacing the build-projected shim

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim (self-approved reversal under the single-maintainer model, CHARTER § Governance — this overturns Accepted ADR-0003; the superseding ADR is the first follow-on artifact)
- **Date opened:** 2026-06-03
- **Date closed:** 2026-06-03
- **Related:** [RFC-0006](0006-skill-secrets-storage.md) (three-tier storage; Alt C), [RFC-0013](0013-credential-broker-contract.md) (four-broker contract; the projected shim; Alt I), [ADR-0003](../adr/0003-credential-broker-contract.md) (projected-shim decision — **this RFC reverses it**), [`credentialed-cli-exit-code-contract`](../specs/credentialed-cli-exit-code-contract/spec.md) (reserved `3–9`, deferred authsome's exit numbers "to A+B" — this RFC is that home for the *credential-resolution subset*; the daemon/connection numbers stay deferred, see Follow-on)

## The ask

- **Recommendation (BLUF):** Replace RFC-0013's build-projected, vendored, stdlib-only `credentials_shim` with a **standalone, pip-installable `credbroker` library** consumed **in-process** by credentialed skills. Core stays stdlib-only (env → OS keyring → dotfile); an **optional `credbroker[crypto]` extra** adds an encrypted-at-rest vault (Argon2id → KEK → AES-256-GCM) — closing the plaintext Tier-3 gap the stdlib floor can't (there is no AEAD in the standard library): **strong** where an OS keyring holds the master, a **modest** ciphertext-at-rest improvement where there's no keyring (see Proposal). **Daemon/proxy credential injection (authsome's model) is explicitly out of scope.**
- **Why now (SCQA):** *Situation* — credentialed skills resolve secrets through a stdlib shim that the build pipeline projects byte-identically into every skill's `scripts/`, kept honest by a drift gate. *Complication* — that shim leaves the Tier-3 dotfile **plaintext** (no stdlib AEAD), carries real projection/drift machinery, and its pip-free purity buys little now that the API-client skills already `pip install` `httpx` (the lone exception, `credential-setup`, is accounted for below). authsome shows a stronger vault is feasible, but its daemon + MITM-CA make it a non-starter in the locked-down corporate environments this catalogue targets. *Question* — can we get authsome's encrypted-vault benefit in a shape that survives corporate lockdown?
- **Decisions requested:**
  1. **Replace the projected shim with a pip-installable `credbroker` library (in-process)?** · recommended: **yes** · reverses ADR-0003 · decide-by: at circulation (default: yes).
  2. **Encrypted vault as an optional `[crypto]` extra, stdlib core as the floor?** · recommended: **yes** · decide-by: at circulation (default: yes).
  3. **Phase delivery: repo-path install now → PyPI for GA?** · recommended: **yes** · decide-by: at circulation (default: yes).
  4. **Preserve env Tier-1 as the pip-free floor; daemon/proxy (C) out of scope?** · recommended: **yes** · decide-by: at circulation (default: yes).

## Problem & goals

**Diagnosis.** RFC-0013 chose a vendored, build-projected, stdlib-only shim specifically to keep credential *resolution* free of a PyPI dependency, because APM/Claude-plugin adopters may never `pip install`. That choice bought one real thing (zero-pip resolution) and cost three:

1. **Plaintext at-rest floor.** The Tier-3 dotfile is mode-0600 plaintext. The standard library has no AEAD, so a stdlib-only resolver *cannot* encrypt it. OS-keyring (Tier 2) is encrypted, but the Linux/corporate-no-keyring path falls to plaintext.
2. **Projection + drift machinery.** The shim is byte-copied into every `auth: creds` skill's `scripts/` and policed by a three-outcome drift gate (`make build-check`/`build-self`) — real surface to maintain.
3. **A purity that mostly no longer pays.** The five API CLIs already require `pip install -r requirements.txt` (for `httpx`), so "the resolver adds no pip dependency" is academic *for them*. The lone exception is `credential-setup`, which ships no `requirements.txt` today — migrating it does add its **first** pip dependency (it runs interactively, where pip is available, and env Tier-1 remains its floor), so the cost is real for that one consumer, not academic.

Meanwhile authsome demonstrates the missing capability — an encrypted vault (Argon2id → KEK → AES-GCM) — but bundles it with a daemon + MITM proxy + trusted-CA requirement that corporate security commonly **bans outright**, so it can't be adopted as-is.

**Goals.**
- Encrypted-at-rest credentials for the floor tier, without a daemon, a proxy, or a trusted CA.
- Preserve the in-process security guarantee (cleartext never crosses a process boundary to the LLM).
- Remove the projection/drift machinery; use ordinary dependency hygiene instead.
- Stay viable in locked-down corporate environments: `pip install` of a pure-Python library is routine; daemons and MITM CAs are not.

**Non-goals** (could-have-been-goals, deliberately dropped):
- **Network-layer credential injection / a credential daemon** (authsome's model). This is runtime infrastructure — it fails CHARTER Principle 3 ("A habit, not a tool"; "not a piece of infrastructure"), the same line that ruled out the browser-bridge design, and it's the part corporate environments reject. If ever pursued, it gets its **own RFC**, not this one.
- **Polyglot (non-Python) consumers.** Every credentialed primitive shipping today is Python; a non-Python consumer picks the `env` broker, unchanged.
- **Re-homing credentials into `agentbundle`.** `agentbundle` shed `credentials` in 0.2.0 on purpose; `credbroker` is a *separate* package so the build tool stays a build tool.

## Proposal

**`credbroker` — a standalone Python package** developed at `packages/credbroker/` (a sibling of `agentbundle`, co-tested in this repo, released independently), consumed **in-process** by credentialed skills.

- **Core (stdlib-only).** The current shim's logic — `load_credentials(namespace, required_keys=[...])` resolving env → OS keyring → 0600 dotfile, with the per-platform Tier-2 backends and the public exception surface (`CredentialsMissingError`, `Tier2HardFailError`). API-compatible with today's shim so consumer call sites barely change. No third-party dependency.
- **`credbroker[crypto]` extra (optional).** Adds `cryptography` + `argon2-cffi` and an **encrypted-file vault** (master → Argon2id → KEK → AES-256-GCM-wrapped DEK → encrypted values), authsome's vault design. Dep-gating: corporate-minimal installs `credbroker`; environments that allow it add `[crypto]`; absent the extra, resolution degrades to keyring/dotfile (the stdlib floor).
- **Build-vs-buy — `cryptography` only, not the full `keyring` stack.** The Python ecosystem's `keyring` + `keyrings.cryptfile` would give "OS store + encrypted file" off the shelf, but `keyring`'s **Linux backends need D-Bus/Secret Service** — the headless/SSH/container regression RFC-0006 deliberately avoided. So credbroker keeps its **stdlib Tier-2 backends** (`/usr/bin/security`, `ctypes`/CredMan) and uses **`cryptography`'s vetted AEAD** only for the file vault (no hand-rolled cipher).
- **Master-secret unlock — no daemon.** The vault's master lives in the **OS keyring via credbroker's own stdlib Tier-2 backend** (Keychain/CredMan); the KEK is derived **per-invocation** (Argon2id ≈ tens of ms — fine for a once-per-command CLI, no resident process). Where there is **no OS keyring** (headless Linux / locked-down corporate — the case the file vault targets), the master comes from an **env var** (ephemeral, wrapper-injected) with a **0600-file fallback**. *Honest caveat:* in that no-keyring case the key sits beside the ciphertext, so the gain over today's plaintext Tier-3 is **modest** — ciphertext-at-rest with a separable key (better against backups / log-capture / misconfigured sync, not the strong protection the keyring case gives). The encrypted vault pays most where a keyring exists and least where it doesn't — which is the environment it was meant for; named here rather than oversold. (Borrows `sagecipher`'s "reuse a key store you already have" idea — here the OS keyring — rather than inventing a new master-secret home.)
- **Consumption is in-process.** Skills do `from credbroker import load_credentials` (replacing `from .credentials_shim import …`); `credential-setup` writes through a library `set`/`store` API. Cleartext stays inside the consumer's interpreter — the RFC-0006 structural guarantee is preserved. No subprocess that prints a token (wrap-and-leak), no daemon.
- **No new CLI (pure library).** `credbroker` ships **no `setup`/`check` CLI** in v1: `credential-setup` (the existing skill) remains the interactive write surface and each consumer CLI's own `check` verifies. So the reserved `3–9` exit band stays **unclaimed** for a future daemon RFC. A thin convenience CLI is a follow-on only if a non-skill use appears (`keyring` ships one outright; `python-dotenv` gates its CLI behind an optional `[cli]` extra — credbroker starts with **no** CLI at all in v1).
- **env Tier-1 stays the pip-free floor.** An adopter who can't `pip install` at all still injects `<NAMESPACE>_<KEY>` via the environment; `credbroker` is only needed for Tier-2/Tier-3 resolution. This is the explicit mitigation for the one adopter profile the pip dependency costs.

**Delivery — phased, to defer version-coordination:**
- **Phase 1 (now): repo-path install.** Skills install `credbroker` from the repo (`pip install -e ./packages/credbroker`, or a path/VCS dependency). No published version, so **no version pinning** — this repo and clone adopters use whatever's at the commit. Fast iteration; the drift gate retires immediately for these consumers. **Register the chosen name on PyPI defensively** (an empty placeholder) as soon as it's fixed, so it can't be squatted before Phase 2.
- **Phase 2 (GA): PyPI.** Publish `credbroker` (name **available** — see Evidence); skills pin a version. This is what unblocks the **APM/Claude-plugin adopter, who has no repo** — until Phase 2 they remain on the projected shim or env Tier-1. Phase 2 is gated on the package stabilising, not on a date.

**Migration.** **Six** in-tree consumers import the shim today — the five credentialed CLIs (`jira`, `jira-align`, `confluence-publisher`, `confluence-crawler`, `figma`) **plus `credential-setup`**, the `credential-brokers` pack's own setup skill (`packs/credential-brokers/.apm/skills/credential-setup/`). Each swaps `from .credentials_shim import …` → `from credbroker import …`. The five CLIs add `credbroker` to their existing `requirements.txt` (beside `httpx`); `credential-setup`, which ships **no** `requirements.txt` today, gains `credbroker` as its **first** pip dependency (a real new cost for that one skill, not academic — see the diagnosis). The `shared-libs` projection of the shim and its drift gate retire once no consumer imports the vendored shim. **`credential-setup` is the load-bearing case:** it lives in the broker pack, so migrating it makes the `credential-brokers` pack *depend on* `credbroker`, and the pack's reason-for-being narrows from "projects the shim" to "ships the interactive setup skill (which now wraps `credbroker`)." That coupling is acceptable — `credential-setup`'s job is precisely to write into the store `credbroker` reads — but it's named here, not glossed. `test_credentials_wheel.py` (pins the *absence* of `agentbundle.credentials`) stays valid — `credbroker` is a *different* package, not the resurrection of `agentbundle.credentials`.

**What changed since ADR-0003 rejected this exact shape.** Option B *extends* RFC-0013 **Alternative I** ("ship `credentials_shim` as a PyPI package consumers import") with the `[crypto]` vault — and on the one axis ADR-0003 rejected Alternative I, *portability*, it is the same shape. ADR-0003 rejected Alt I on one ground: *"same portability problem (consumer carries an implicit `pip install`)"* — aimed squarely at the **APM/Claude-plugin adopter who never pips at all**. That rationale has **not** evaporated; it has **narrowed**. For the *Python* consumer it's moot (they already pip `httpx`). For the **zero-pip plugin adopter it survives unmitigated until Phase 2 (PyPI)** — and even then they must pip *something*. This RFC overturns Alternative I deliberately, on the judgment that (a) the encrypted-vault gain + the retirement of the projection/drift machinery outweigh that one adopter profile's cost, and (b) that profile keeps a working path via **env Tier-1** (zero pip). If you weight the never-pip adopter more heavily than the encrypted floor, the honest answer is do-nothing (Option A) — that is the live alternative this decision rejects.

## Options considered

**Axis: how the credential resolver is *delivered* and what *runtime shape* it takes** — the two dimensions that determine corporate viability and the pip/portability cost. These four points exhaust the practical space (vendored-vs-pip × in-process-vs-out-of-process, minus the incoherent cell):

| Option | Delivery / shape | At-rest | Corporate-viable? | Verdict |
|---|---|---|---|---|
| **A. Do nothing** — projected stdlib shim (status quo, RFC-0013) | vendored byte-copies; in-process | plaintext Tier-3 floor | yes | no encryption; keeps drift machinery; purity no longer pays |
| **B. `credbroker` pip library, in-process** ★ | pip package; in-process import | encrypted via `[crypto]` extra | **yes** (`pip install` a lib is routine) | **recommended** |
| C. Subprocess CLI broker — skills shell out, broker prints the token | pip/standalone; out-of-process, prints value | any | n/a | **rejected** — wrap-and-leak (cleartext on stdout, LLM-readable); RFC-0006 §5 / RFC-0013 Alt G refused it |
| D. Daemon + MITM proxy injection (authsome) | resident service; network interception | encrypted | **no** (banned CA + daemon) | out of scope — fails CHARTER Principle 3; own RFC if ever |

**Why these four exhaust the space.** The axis is a 2×2 — *delivery* (vendored-projected vs pip) × *runtime shape* (in-process vs out-of-process). A and B are the two **in-process** cells (vendored / pip); C and D are the two **out-of-process** cells (subprocess that prints / resident daemon). The fourth nominal delivery×shape combination — *vendored-projected out-of-process* — is incoherent (you don't byte-project a resident subprocess into each skill's `scripts/`), so the space is four meaningful points, not a round number.

Prior-art grounding: A is the status quo; B is the `keyring`/`python-dotenv` model (a small focused library adopters pip-install); C is the wrap-and-leak shape RFC-0006 named by example; D is authsome / Vault-Agent-style injection. Do-nothing's cost of delay: the plaintext floor persists and the projection machinery keeps accruing maintenance.

## Risks & what would make this wrong

**Pre-mortem (assume it shipped and failed):**
- **The pip dependency strands a real adopter.** *Failure:* an APM/plugin adopter who never clones the repo can't get `credbroker` until Phase 2, and can't use env Tier-1 either. *Mitigation:* keep env Tier-1 working with zero pip; ship Phase 2 (PyPI) before deprecating the projected shim for plugin adopters; until then, the shim and `credbroker` can coexist.
- **`[crypto]` extra unavailable in the locked-down env that most wanted encryption.** *Failure:* the corporate box that can't add `cryptography` is exactly the one with no OS keyring → back to plaintext. *Mitigation:* honest — encryption requires the extra; where neither keyring nor `[crypto]` is available, the 0600 dotfile remains the floor (no worse than today).
- **Version skew once on PyPI.** *Failure:* skills pin an old `credbroker`; a security fix doesn't reach them. *Mitigation:* normal dependency hygiene + a documented minimum-version pin; Phase 1 (repo-path) has no skew by construction.
- **Master-secret lifecycle is the `[crypto]` vault's single point of failure.** *Failure:* an in-process library has **no resident unlock** (unlike authsome's daemon), so every invocation must source the master secret and re-derive the Argon2id KEK. If the secret comes from an env var, it's the same exposure class the vault exists to fix; if it's an interactive prompt, it breaks non-interactive/agent use; a lost or wrong secret means an **unrecoverable vault**. *Mitigation:* the unlock model is **decided in the Proposal** — master in the **OS keyring** (Tier-2-protected, via the stdlib backend), KEK derived per-invocation, never in process env; the encrypted-*file* vault is opt-in for exactly the no-keyring case, where the master falls to an env var (wrapper-injected) or a 0600 file — no worse than today's plaintext Tier-3, and modestly better (values AEAD-encrypted even if the key sits beside them). The implementing spec pins the fine details (env-vs-file precedence, Argon2id parameters).

**Key assumptions (falsifiable):**
- *"`pip install` of a pure-Python lib is corporate-acceptable where a daemon + MITM CA is not."* If false (an environment that forbids all `pip` but the skills somehow still run), env Tier-1 is the only path and B adds nothing for them — but also costs them nothing.
- *"In-process import preserves the no-leak guarantee."* True by the same argument as RFC-0013's shim — cleartext never crosses a process boundary.
- *"Principle 3 is satisfied because `credbroker` is not a catalogue artifact at all."* P3 governs what the **catalogue ships** (skills, agents, commands — habits/disciplines). `credbroker` is **not a pack and not projected**; it's an external PyPI dependency the adopter installs, in the same category as `httpx`, `keyring`, or `python-dotenv`. The catalogue keeps shipping only the credentialed-skill *habit* (the skills that depend on it). The harder reading — "P3 forbids shipping a *tool*, and a released vault library is a tool" — is answered by **who ships it**: the catalogue ships the discipline; the library is a *dependency of* that discipline, not a catalogue deliverable. The daemon (D) differs precisely because adopting it would make a catalogue pack responsible for *running infrastructure*. (If false — if reviewers judge that publishing *any* library under this project's name is "shipping a tool" regardless of the pack boundary — the fallback is to develop `credbroker` in a wholly separate repo, which costs co-testing but removes all doubt.)

**Drawbacks (not "none"):**
- **Reverses RFC-0013/ADR-0003** — a deliberate architecture reversal, with the migration + governance cost that implies.
- **Trades "can't drift" for "must version-coordinate."** The vendored shim is byte-projected and literally cannot drift; a released package must be versioned and pinned (Phase 2 onward). Phase 1 sidesteps this; Phase 2 reintroduces it as ordinary dependency hygiene.
- **A new package to maintain, test, and (eventually) release.**

## Evidence & prior art

- **De-risk (riskiest assumption: charter-fit).** *The check run:* read `docs/CHARTER.md` against the proposal. Principle 3 governs what the *catalogue ships* (habits); `credbroker` is a dependency, not a catalogue artifact (see the P3 assumption above), so the charter is satisfied at the level it operates on. That is a real check against the governing text, and it holds. **The corporate-pip-acceptability assumption is *not* spiked** — I can't exercise a locked-down corporate environment from here. It's stated as a falsifiable assumption below (pip-install-a-lib ≫ daemon + MITM-CA), grounded in the plain fact that MITM-CA trust and resident daemons are common *explicit* corporate bans while `pip install` of a pure-Python lib is the standard dependency path. If that ranking is false for a given org, env Tier-1 is their path and `credbroker` costs them nothing.
- **Name availability (checked 2026-06-03).** PyPI JSON API returns **404** for `credbroker`, `agentcreds`, and `credential-broker` — all available. Primary: **`credbroker`**.
- **Repo precedent.** RFC-0006 Alt C (external/manager) and RFC-0013 Alt I (pip shim) were rejected on *portability*; ADR-0003 chose the projected shim. RFC-0013 §9 removed `agentbundle.credentials` in 0.2.0; `packages/agentbundle/tests/integration/test_credentials_wheel.py` pins that absence — `credbroker` does not reverse it (different package). The `credentialed-cli-exit-code-contract` spec reserved `3–9` and deferred authsome's exit *numbers* "to A+B" — `credbroker` ships **no `setup`/`check` CLI** in v1 (decided — pure library), so the *credential-resolution subset* of that band is left **unclaimed**; the daemon/connection numbers stay deferred to a future daemon RFC.
- **External prior art.** authsome (`.context/authsome`, this session): the maximal version — daemon + MITM proxy + `Argon2id→KEK→AES-GCM` vault + identity/audit; its **vault** is `credbroker[crypto]`'s reference, its **daemon/proxy** is option D. The [`keyring`](https://pypi.org/project/keyring/) library is the standard cross-platform OS-credential-store approach (pluggable backends; [docs](https://keyring.readthedocs.io/en/stable/)); its [`keyrings.cryptfile`](https://pypi.org/project/keyrings.cryptfile/) backend is the off-the-shelf "encrypted file with a master password" and [`sagecipher`](https://pypi.org/project/sagecipher/) derives the key from the running `ssh-agent` (no daemon-you-run) — both inform the unlock model and the build-vs-buy choice (we reuse the OS keyring rather than pull `keyring`'s D-Bus-bound Linux backends, the regression [RFC-0006](0006-skill-secrets-storage.md) flagged). [`python-dotenv`](https://pypi.org/project/python-dotenv/) gates *its* CLI behind an optional `[cli]` extra — a close parallel to credbroker's `[crypto]` gating; credbroker starts library-only, without even a gated CLI. Secret-manager landscape (1Password/Doppler/Vault/Infisical) is consumed today via the **env broker**, which is why the env Tier-1 floor is preserved.

## Open questions

The substantive decisions are **settled in the Proposal**, not parked here: build-vs-buy (`cryptography` only, not the full `keyring` stack), the no-daemon master-secret unlock model (keyring-sourced master + per-invocation KEK; env/0600-file in the no-keyring case), single-`[crypto]`-extra granularity, pure-library-no-CLI (exit band left unclaimed), and the Phase-2/PyPI trigger. One genuinely-open item remains:

1. **Package name** — `credbroker` (recommended; PyPI-available, re-confirmed 404) vs `agentcreds` / `credential-broker` (also available). · owner: eugenelim · decide-by: before Phase 1 scaffold (default: `credbroker`, then register it defensively on PyPI). The implementing spec still pins the *fine* unlock details (env-vs-file precedence in the no-keyring case, Argon2id parameters) — implementation detail under the decided model, not an open RFC question.

## Follow-on artifacts

Filled in upon acceptance:
- **ADR-NNNN** — records the reversal of ADR-0003 (projected shim → pip `credbroker`), the in-process-library decision, and the daemon (D) exclusion.
- **Spec: `docs/specs/credbroker/`** — the package's API, the stdlib core, the `[crypto]` vault + master-secret unlock model, the graceful-degrade matrix, the env-Tier-1 floor, and the migration of the **six** in-tree consumers (five CLIs + `credential-setup`) off the projected shim (retiring the `shared-libs` projection + drift gate).
- **Convention change: `docs/CONVENTIONS.md` § Credentialed skills** — `auth: creds` now resolves via `import credbroker`, not the vendored shim.
- **Exit-code alignment (partial).** `credbroker` ships no CLI in v1 (pure library), so the reserved `3–9` band stays **unclaimed** for now; a future convenience-CLI follow-on may claim the **credential-resolution subset** (e.g. keyring-hard-fail, vault-locked). authsome's **connection/provider/daemon** exit numbers — which the exit-code spec's deferral also named — stay **deferred to a future daemon RFC** (the daemon is out of scope here), so the band does not silently strand.
- **Guide update** — `docs/guides/how-to/add-a-credentialed-skill.md` Step 6 (`import credbroker`) + Step 8 (`pip install credbroker[crypto]`).

## Amendments

This RFC is Accepted: the body above is preserved as the original decision
record. Post-acceptance changes are appended here, Approver-signed.

- **2026-06-09 (Approver: eugenelim) — layered delivery resolves the deferred
  no-repo-adopter problem (vendored floor → offline/local pip → PyPI).** The
  Proposal's § Delivery deferred the **APM/Claude-plugin adopter who has no
  repo** to Phase 2 (PyPI): "until Phase 2 they remain on the projected shim
  or env Tier-1." The Pre-mortem named the same gap first ("the pip dependency
  strands a real adopter"). That deferral is now resolved by a **layered
  delivery model**, specified and shipped in
  [`docs/specs/credbroker-user-scope/spec.md`](../specs/credbroker-user-scope/spec.md)
  (Shipped 2026-06-09):

  1. **Vendored floor (zero-pip, always present).** User-scope install vendors
     the stdlib-base `credbroker` package source to `~/.agentbundle/lib/credbroker/`,
     which the consumer bootstrap appends to `sys.path` at **lowest** precedence.
     This restores Tier-1/2/3 resolution (plaintext Tier-3) for the no-repo
     adopter with **no pip at all** — the profile this RFC's Pre-mortem flagged
     as stranded until Phase 2.
  2. **Offline / local pip (corporate, no PyPI).** The `release-credbroker.yml`
     workflow builds a `py3-none-any` wheel + sdist, so a locked-down site can
     `pip install` from an internal index (`--index-url`) or a local `.whl` —
     no PyPI dependency. Because pip lands the package in site-packages, it
     **wins** over the floor and unlocks the `[crypto]` vault.
  3. **PyPI (open adopters).** Unchanged from the original Phase-2 plan: a
     gated, manual-publish job in the same workflow; the first publish + name
     claim stays a maintainer action (see `docs/backlog.md#credbroker-phase-2`).

  **The floor is *additive*, not a return to the projected shim.** The primary,
  highest-precedence contract is still `import credbroker` from **site-packages**
  (pip — PyPI / internal mirror / local wheel / editable), exactly as this RFC
  and ADR-0003's posture intend. The floor is a *fallback* for that **same
  import**, appended at lowest `sys.path` precedence so a pip-installed copy
  always shadows it (and a stale floor can never downgrade a newer, vault-capable
  install). It is therefore **one shared copy** at `~/.agentbundle/lib/`, not the
  N-per-skill byte-projected shim ADR-0003 reversed — the projection/drift
  machinery this RFC retired does not return. ADR-0003's reversal (projected
  shim → pip `credbroker`) is **not itself reversed**, so **no new or annotating
  ADR is required**; this amendment is the governance record of the fallback.

  The same delivery rail also closes the long-missing user-scope half of
  [RFC-0013](0013-credential-broker-contract.md)'s `adapter-root-bins` →
  `~/.agentbundle/bin/` projection (the `sso-broker` companion), which had only
  ever shipped its self-host half.
