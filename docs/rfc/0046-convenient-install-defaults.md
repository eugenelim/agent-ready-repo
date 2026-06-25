# RFC-0046: Convenient install defaults — resolve the catalogue source from install context

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-25
- **Date closed:** 2026-06-25
- **Related:** RFC-0031 (package-manager posture; D7 "bare pack → public default catalogue" — this RFC defines *how* that default is located), RFC-0011/0012 (adapter resolver cascade + the state-hint short-circuit), RFC-0040 + ADR-0030 (`agentbundle-layout.toml` shipped-default + path anchoring; **and its untrusted-origin / confirm-before-write control for a hostile cloned repo** — the precedent for omitting a repo-supplied source), ADR-0002 (per-pack install scope), `docs/CHARTER.md` (Principle 3: "a habit, not a tool… not infrastructure")

## The ask

- **Recommendation (BLUF):** Make `--catalogue` **optional** on `install`/`upgrade` and resolve a default through a narrow, **trusted-by-construction** chain — `--catalogue` arg › **user** `[settings].source` › **editable-install detection** (PEP 610) › packaged `_data/install-defaults.toml`. Because the catalogue source decides *where executable packs come from* (a code-provenance boundary), there is deliberately **no repo-supplied source layer** and **no fall-back to the working directory**. Install-UX hygiene under RFC-0031's posture — no server, no index, no daemon.
- **Why now (SCQA):**
  - *Situation* — RFC-0031 D7 already says a bare pack "resolves to the public default catalogue," and `resolve_catalogue` (`agentbundle/catalogue.py:72`) already accepts a local path.
  - *Complication* — but `catalogue` is a **required positional** (`agentbundle/cli.py:247`), so every install must spell out a source; and a downstream fork behind a **GitLab API gateway** has nowhere valid to point: the resolver's `git+https` regex is **github.com-only** (`agentbundle/catalogue.py:43`), and a fixed local path can't be baked because users clone anywhere.
  - *Question* — how does a bare `agentbundle install --pack X` find the right source automatically — for the public PyPI user (→ GitHub) **and** the gateway-bound editable fork (→ its local clone, wherever cloned) — with zero extra command, no server, and **without letting a cloned repo or the cwd dictate where code is fetched from**?
- **Decisions requested** (all recommended; decide-by: at sign-off, default = accept as written):
  1. **Optional `catalogue` + default resolution on `install`/`upgrade`** (the *discovery* verbs `list-packs`/`list-profiles` are a follow-on — defaulting a query needs its own justification and must not silently fetch the upstream URL on a gateway fork). *Recommended: accept.*
  2. **The four-layer source chain** (no repo-supplied source, no cwd fall-back). *Recommended: accept.*
  3. **Editable detection via PEP 610 `direct_url.json`**, with a canonicalized, repo-bounded walk-up. *Recommended: accept.*
  4. **No auto-persist**; add a `source` key to the existing user `[settings]` schema — `config set source` is the persistence path. *Recommended: accept.*
  5. **Ship a packaged `_data/install-defaults.toml`** (upstream = GitHub URL); a private downstream fork **blanks** it. *Recommended: accept.*

## Problem & goals

**Diagnosis.** `catalogue` is a required positional with no default, so the common case costs a full URI every time. For the public user that URI is always the same GitHub repo. For a downstream org fork it is *unspecifiable*: `resolve_catalogue` only parses `git+https://github.com/...` (`catalogue.py:43`), an internal GitLab URL is rejected, the API gateway blocks direct internal-URL access, and a fixed filesystem path can't substitute because each machine clones to a different location.

**Goals.**

- A bare `agentbundle install --pack X` resolves a sensible source with **no extra command**, for both the public PyPI user (→ GitHub) and the editable downstream fork (→ its local clone, clone-location-independent).
- An explicit `--catalogue` **always overrides** the default; the user's own `config set source` overrides auto-detection.
- **No code-provenance escalation:** no resolution layer lets a *cloned repo* or the *current working directory* decide where packs are fetched from.
- **No new infrastructure** — runtime resolution + reading files only; honors RFC-0031 + Principle 3.

**Non-goals** (could-have-been-goals, deliberately dropped):

- **A repo-committed catalogue source.** A repo dictating where executable code is fetched from is a supply-chain hazard (see Risks); the explicit arg + editable detection already meet the downstream need, so the layer is omitted entirely.
- **An in-repo *adapter* override** (the Claude-Code-style repo-overrides-user precedence for the projection target). It is cleanly separable from the source motivation and is spun out to its own future RFC; this RFC leaves the adapter resolver unchanged.
- **A hosted registry / index / discovery service.** RFC-0031 defers this; zero runtime infra here.
- **Auto-persisting a source from a one-off install.** A surprising side-effect with no package-manager precedent; explicit `config set source` instead.
- **Arbitrary git hosts, integrity-pinned fetches, a dependency resolver, scoped-identity changes.** Out of scope (the editable-detection path sidesteps the host limitation; pinning is flagged as a follow-on).

## Proposal

### D1 — Optional `catalogue`, default resolution on `install`/`upgrade`

`catalogue` becomes `nargs="?"` (default `None`) on `install` and `upgrade`. When omitted, the handler calls a shared `resolve_default_source()` before `resolve_catalogue`; an explicit arg passes through unchanged (backward compatible). `list-packs`/`list-profiles` keep requiring an explicit catalogue for now (follow-on) — defaulting a *discovery* query must not silently fetch the upstream URL on a gateway-bound fork.

### D2 — The source precedence chain (four layers; no repo source, no cwd)

Highest precedence first; the first layer that yields a source wins. Every layer is **trusted by construction** — the invocation, the user's own machine config, the user's own editable install, or the distribution wheel:

| # | Layer | Source | Trust basis |
| --- | --- | --- | --- |
| 1 | `--catalogue <uri>` | the invocation | the user typed it |
| 2 | user `[settings].source` | `~/.config/agentbundle/config.toml` (via `config set source`) | the user set it on their own machine |
| 3 | **editable detection** | PEP 610 `direct_url.json` → repo-bounded walk-up to the dir with `packs/` + `marketplace.json` | the user ran `pip install -e` on their own machine |
| 4 | packaged default | `_data/install-defaults.toml` in the wheel | shipped by the distribution |

There is **no repo-scoped `source`** and **no cwd/`.` fall-back** (see Risks). If **no** layer yields a source, the command **errors clearly**: `no catalogue source: pass --catalogue, run 'agentbundle config set source …', or pip install -e the catalogue`.

User-config (2) outranks editable detection (3): an explicit `config set source` is deliberate user intent and should win over auto-detection. A user who sets a stale source recovers with `agentbundle config unset source` (named in the diagnostic text).

### D3 — Editable detection (layer 3)

Read this distribution's PEP 610 record: `importlib.metadata.distribution("agentbundle").read_text("direct_url.json")`. If present with `dir_info.editable == true`:

1. Parse the `file://` `url` with the **standard** parser (`urllib.request.url2pathname` + percent-decoding), and **reject** a non-empty/non-localhost `file://` host.
2. **Canonicalize** the path (`Path.resolve()` — resolve symlinks and `..`) before walking.
3. **Walk up over canonicalized ancestors** (verify each candidate stays under the resolved repository root, so a symlinked intermediate can't redirect the search), stopping at the **first** ancestor containing **both** `packs/` and `.claude-plugin/marketplace.json`. The recorded path is the *editable package* (`packages/agentbundle`); the catalogue root (the clone) is **above** it, so the walk must ascend. **Bound the ascent to the enclosing repository root** — the nearest ancestor containing a `.git` entry (file *or* directory, covering worktrees/submodules), computed **before** any marker test — so a `packs/` + `marketplace.json` pair planted in a *shared parent above the clone* can never be matched.

The two markers are an **accident-guard** (don't misfire on an unrelated tree), **not a trust control** — they are forgeable, so a pair planted in an *intermediate* dir within the clone could be matched first; that residual risk is bounded by the canonicalize + stop-at-first + no-ascent-above-the-repo-root rules and is acceptable because writing inside the clone already means write access to the user's own catalogue. **No `direct_url.json` → no detection** (an older pip that omits it falls through to layer 4 — an accepted limitation, not a fallback heuristic).

**Fall-back-with-diagnostic:** if editable is detected but no catalogue root is found at/below the repo boundary (e.g. sparse checkout missing `packs/`), defer to layer 4 **and emit a one-line stderr diagnostic** naming what happened — never silent, never a hard error on a default, **never the cwd**.

### D4 — No auto-persist; `config set source` is the persistence path

Add a `source` key to the existing user `[settings]` schema (`user_config.py`, alongside `adapter`). Resolution is **stateless** (recomputed each run); there is **no write-on-install**. A user wanting a persistent custom default runs `agentbundle config set source <uri>` (layer 2) — visible and intentional. This departs from the in-repo *state-hint* (which remembers the *adapter* as a **correctness** mechanism — an upgrade/uninstall must re-target the adapter it wrote files for; source-memory would be mere convenience with no package-manager precedent).

### D5 — Packaged `_data/install-defaults.toml` (layer 4)

A new packaged data file (joining `adapter.toml`, the schemas, `install-marker.py` in `_data/`) declares the distribution's baked default:

```toml
# _data/install-defaults.toml
[defaults]
source = "git+https://github.com/eugenelim/agent-ready-repo"
```

Upstream ships the GitHub URL — a bare `agentbundle install --pack core` Just Works for public users. **A private downstream fork blanks/drops this file.** Absent/empty = no layer-4 default. A data file (not a constant) lets a fork re-point it with zero code edits (the baked default-registry model — PyPI / crates-io). **Integrity posture (asymmetric by layer).** Layers 1–3 reduce to **local trust** — an arg the user typed, config on the user's own machine, or the user's own filesystem clone — genuinely strong. Layer 4's `git+https` default is the one path that **crosses the network**: the existing resolver fetches an *unauthenticated* GitHub-archive tarball with a missing ref defaulting to `main` (`catalogue.py:75-91`) — trust-on-first-use against `main`'s current tip, with **no checksum/signature/pin**, so "distribution-controlled" here means *the repo*, not a fixed revision. Acceptable for now (the network layer is the upstream public default, off the gateway-fork path); **integrity-pinning — specifically for the layer-4 `git+https` fetch — is a named follow-on.**

### Migration

- `catalogue` positional → `nargs="?"` on `install`/`upgrade`; explicit invocations behave identically.
- `source` added to `_KNOWN_KEYS` + the user `[settings]` schema (user scope only).
- `resolve_default_source()` validates each layer's output (markers present for a path; parseable URI) **before** handing it to `resolve_catalogue`, which itself does no validation (`catalogue.py:72` returns `Path(uri)` unconditionally).
- New `_data/install-defaults.toml` via existing `package-data` wiring.
- The adapter resolver is **untouched** (`scope.DEFAULT_ADAPTER` and the user-config adapter layer are unchanged), so the ~13 default-resolution tests and `packages/agentbundle/tests/unit/test_resolve_user_scope_target_adapter.py:648` stay green.

### Private-fork pattern

A fork behind a gateway: **blank `_data/install-defaults.toml`** and rely on **editable detection** — each machine's `pip install -e <wherever-cloned>/packages/agentbundle` records that machine's absolute clone path (PEP 610), read at runtime. Clone anywhere → bare installs work, zero command, no URL, no baked path. Explicit `--catalogue <local-path>` remains available.

## Options considered

**Axis: where the default catalogue source comes from when none is specified.** Exhaustive — a default can come from *nowhere* (require explicit), a *constant*, a *shipped file*, *install-context detection*, or a *combination*; status quo is do-nothing.

| Option | Prior art | Trade-offs |
| --- | --- | --- |
| **(a) Do nothing** — keep `catalogue` required | — | Zero cost now; but the gateway-bound fork has no usable source at all, and every public install re-types the URI. The downstream story stays blocked. |
| **(b) Single hardcoded constant** | a baked URL constant | Trivial; un-substitutable per-distribution without a code edit, and a constant URL is dead for the gateway fork. |
| **(c) Packaged default file only** | pip/cargo baked registry | Substitutable by the fork — but can't express "the clone, wherever it is"; the clone-anywhere fork still can't bake a path. |
| **(d) Install-context detection only** | PEP 610; `pip`/`uv` reading editable records | Solves clone-anywhere — but a *wheel* (public PyPI) has no editable record, leaving the public user with no default. |
| **(e) Trusted layered chain (user config + detection + packaged file)** ★ | npm/pip/cargo layered config + baked default; PEP 610 | Covers public (layer 4), editable fork (layer 3, clone-anywhere), explicit/persistent overrides (layers 1–2) — **without** a repo-supplied code-source. Cost: more precedence to reason about (mitigated by the table; most users hit one layer). **Recommended.** |

## Risks & what would make this wrong

**Pre-mortem.**

- *A cloned repo silently redirects code provenance.* This is why there is **no repo-scoped `source`**. RFC-0040 (`§Risks`) classified a hostile repo-root file as untrusted-origin / Ask-first / confirm-before-write — for the lower-stakes *where-files-are-written* case. Source is higher-stakes (*where executed code comes from*), so rather than replicate a confirmation gate we omit the layer entirely; the downstream's need is met by editable detection.
- *Planted-marker hijack of editable walk-up.* → canonicalize + stop-at-first-match + bound the ascent to the enclosing `.git` repo root; markers documented as an accident-guard, not a trust control (D3).
- *Fail-open to cwd.* → explicit rule: no layer ever resolves from `.`/cwd; the only terminal states are a validated source or a clear error (D2).

**Key assumptions (falsifiable).**

- `pip install -e` records an absolute `file://` URL with `editable: true` (PEP 610) — *verified by spike*.
- The catalogue root is locatable by a repo-bounded walk-up from the editable path — *verified by spike*.
- `resolve_catalogue` accepts a local path (`catalogue.py:72`) but performs **no** existence/marker validation — so `resolve_default_source()` must validate before calling it.
- The catalogue root **coincides with the git root** (the `packs/` + `marketplace.json` markers sit at the `.git` directory). A catalogue nested inside a larger repo, or vendored as a submodule, is **out of scope** for editable detection — it falls through to layer 4.

**Drawbacks.** More layers to reason about (mitigated by the table; most users hit one); detection is install-method-dependent, so a *wheel* downstream loses it and must use explicit `--catalogue` or a bakeable source — accepted, since editable is the blessed downstream path. The in-repo adapter override that some users want is deferred (its own RFC), not delivered here.

## Evidence & prior art

**Spike (de-risk the keystone — editable detection).** In an isolated venv:

- `pip install -e packages/agentbundle` →
  `direct_url.json = {"dir_info": {"editable": true}, "url": "file:///…/hamburg/packages/agentbundle"}` — an **absolute** path, captured at install time.
- Walking up from that path (bounded by the enclosing `.git` root) locates the catalogue root `/…/hamburg` (contains `packs/` + `.claude-plugin/marketplace.json`).
- The ambient **wheel** install has **no `direct_url.json`** and a site-packages `__file__` → correctly resolves to layer 4.

So `pip install -e <wherever-cloned>` records that machine's real clone path, read by detection — clone-location-independent, zero command. The keystone holds.

**Repo precedent.** RFC-0031 D7 (the "public default catalogue" this RFC locates); RFC-0011/0012 + the state-hint (`commands/install.py` AC10b) — the resolver cascade, and the *correctness-not-convenience* nature of the adapter state-hint that justifies **not** auto-persisting source; **RFC-0040 §Risks** (the untrusted-origin / confirm-before-write control — the precedent for omitting a repo-scoped source); `agentbundle/catalogue.py:72` (local path accepted, unvalidated) and `:43` (github-only — why the fork needs detection); `_data/` packaged files; `user_config.py` `[settings]` schema.

**External prior art** (all fetched and confirmed to contain the cited claim):

- **PEP 610:** `direct_url.json` carries `dir_info.editable` (`true` for `pip install -e`) and an absolute `file://` `url`, and **MUST NOT** be created for index installs. [PEP 610](https://peps.python.org/pep-0610/)
- **Layered config + baked default registry:** [Cargo](https://doc.rust-lang.org/cargo/reference/config.html) (`registry.default = "crates-io"`; deeper-dir overrides home; env over TOML), [npm](https://docs.npmjs.com/cli/v11/using-npm/config/) (project `.npmrc` over `~/.npmrc`, CLI flag wins, default `registry.npmjs.org`), [pip](https://pip.pypa.io/en/stable/topics/configuration/) (CLI › env › config global‹user‹site). Grounds the chain and the packaged-default pattern. *(These put project-config over user-config for a project's own build tooling — a precedent this RFC deliberately does **not** extend to `source`, because source is a code-fetch decision, not build config.)*

## Open questions

None remaining. The two prior open questions (the repo-scope settings file location, and the adapter-resolver refactor sequencing) **dissolved** when repo-scoped config was dropped (scope decision: narrow to source only). The `list-packs`/`list-profiles` default and integrity-pinning are scoped as **follow-ons**, not open questions.

## Follow-on artifacts

Filled in on acceptance:

- [ADR-0036](../adr/0036-install-source-resolves-through-trusted-precedence-chain-no-repo-source-no-cwd.md): the install-source precedence chain + editable-detection-as-default + the no-repo-scoped-source / no-cwd trust decision.
- Spec: [`docs/specs/convenient-install-defaults/`](../specs/convenient-install-defaults/spec.md) — optional `catalogue` on install/upgrade, the four-layer chain, PEP 610 detection (with a real editable-install construction test + the canonicalize / repo-bounded-walk-up ACs), `_data/install-defaults.toml`, `config set source`.
- Adopter guide note: the private-fork "blank `install-defaults`, rely on editable detection" pattern.
- Possible follow-on RFCs: the **in-repo adapter override** (the deferred Claude-Code-style repo-overrides-user precedence for the projection target); integrity-pinning for catalogue fetches; default resolution for the `list-packs`/`list-profiles` query verbs.
