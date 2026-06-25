# ADR-0036: The install-source default resolves through a trusted-by-construction precedence chain — editable detection as the downstream default, no repo-scoped source, no cwd fallback

- **Status:** Accepted
- **Date:** 2026-06-25
- **Decision-makers:** eugenelim
- **Consulted:** RFC-0046 (the accepted decision this records, incl. its five-decision set, the editable-detection spike, and the options-considered table); RFC-0031 (the package-manager posture — no server, no index, no daemon — and D7's "bare pack → public default catalogue" this locates); RFC-0011/0012 + the adapter state-hint (the resolver cascade, and the *correctness-not-convenience* nature of the state-hint that justifies **not** auto-persisting source); **RFC-0040 + ADR-0030 §Risks** (the untrusted-origin / confirm-before-write control for a hostile repo-root file — the precedent for omitting a repo-scoped source rather than gating it); ADR-0002 (per-pack install scope); the external layered-config prior art (Cargo `registry.default`, npm `.npmrc` precedence, pip CLI›env›config) confirmed in RFC-0046's evidence section
- **Supersedes:** none
- **Related:** RFC-0046 (the accepted decision this ADR records); RFC-0031 (the runtime-infra-free package-manager posture this honours); RFC-0011/0012 (the resolver cascade and adapter state-hint); RFC-0040 + ADR-0030 (the untrusted-origin precedent); `docs/specs/convenient-install-defaults/` (the implementing spec); `docs/CHARTER.md` Principle 3 ("a habit, not a tool… not infrastructure")

## Context

`agentbundle install` and `upgrade` take `catalogue` as a **required positional** with no default (`cli.py:247`, `:400`), so every invocation must spell out a full source URI. For the public PyPI user that URI is always the same GitHub repo — re-typed every time. For a downstream org fork behind an API gateway it is **unspecifiable**: `resolve_catalogue` only parses `git+https://github.com/...` (the `_HTTPS_RE` regex is hardcoded to `github.com`, `catalogue.py:43`), the gateway blocks direct internal-URL access, and a fixed filesystem path cannot be baked because every machine clones to a different location. RFC-0031 D7 already promises that a bare pack "resolves to the public default catalogue," and `resolve_catalogue` already accepts a local path (`catalogue.py:72`, returning `Path(uri)` **without any existence or marker validation**) — but nothing locates that default.

The forces in play when deciding *how* to locate it:

- **CHARTER Principle 3 (a habit, not infrastructure).** RFC-0031's posture forecloses a server, a hosted registry/index, or a discovery daemon. Whatever resolves the default must be **runtime resolution + reading files only**.
- **The source is a code-provenance boundary.** The catalogue source decides *where executable packs are fetched from*. This is strictly higher-stakes than the adapter-projection *target* RFC-0040 governs (which decides only *where generated files are written* in the user's own tree). A wrong source runs someone else's code; a wrong target writes a file the user can inspect.
- **RFC-0040's precedent for a repo-supplied control.** ADR-0030 / RFC-0040 §Risks already classified a **hostile repo-root config file** as untrusted-origin and gated the *lower-stakes* where-files-are-written case behind Ask-first / confirm-before-write. That precedent is available to copy — or to decline as insufficient for the higher-stakes case.
- **Two populations, one command.** The public wheel user (no editable record, wants GitHub) and the editable gateway-bound fork (clone-anywhere, wants its local clone) must both get a working bare `install --pack X` with **zero extra command**.
- **Layered-config-plus-baked-default is settled package-manager prior art.** Cargo (`registry.default = "crates-io"`, deeper-dir overrides home), npm (project `.npmrc` over `~/.npmrc`, CLI flag wins, default registry), and pip (CLI › env › config) all converge on a precedence chain terminating in a distribution-shipped default — but they put *project*-config **over** *user*-config for a project's own build tooling, a precedent that does **not** transfer to a code-fetch decision.

## Decision

> We will make `catalogue` **optional** on `install`/`upgrade` and resolve a default through a four-layer, **trusted-by-construction** precedence chain — `--catalogue` arg › user `[settings].source` › **editable-install detection** (PEP 610) › packaged `_data/install-defaults.toml` — with **no repo-supplied source layer** and **no fall-back to the current working directory**, because the source is a code-provenance boundary. Resolution is stateless (no write-on-install); persistence is the explicit `config set source`. The default ships in a packaged **data file** so a downstream fork re-points it with zero code edits.

Five load-bearing, expensive-to-reverse sub-decisions. (The numbering here is the ADR's own. RFC-0046's D1 — make `catalogue` optional — is the change's premise, stated in the Decision sentence above and scoped under *Boundaries*; ADR D1/D2/D4/D5 record RFC-0046's D2/D3/D4/D5, and ADR D3 lifts the no-repo-source / no-cwd half of RFC-0046's D2 into its own decision given its security weight.)

- **D1 — The precedence chain is trusted by construction, highest-first, first-wins.** The four layers, in order, are: (1) the `--catalogue` arg the user typed; (2) the user's own `[settings].source` set via `config set source` on their machine; (3) editable detection reading the user's own `pip install -e` record; (4) the distribution's packaged default. **Every layer reduces to something the user already trusts** — their invocation, their machine's config, their filesystem clone, or the wheel they installed. User-config (2) deliberately **outranks** editable detection (3): an explicit `config set source` is intentional and should beat auto-detection. When **no** layer yields a source the command **errors clearly** (`pass --catalogue, run 'agentbundle config set source …', or pip install -e the catalogue`) — never a silent fall-through.

- **D2 — Editable detection is the blessed downstream default mechanism (PEP 610 + a hardened, repo-bounded walk-up).** Layer 3 reads this distribution's PEP 610 `direct_url.json` (`importlib.metadata.distribution("agentbundle").read_text("direct_url.json")`); when `dir_info.editable == true`, it parses the `file://` URL with the standard parser (rejecting a non-empty/non-localhost host), **canonicalizes** the path (`Path.resolve()`), then **walks up over canonicalized ancestors** to the first one containing **both** `packs/` and `.claude-plugin/marketplace.json` — **bounding the ascent to the enclosing repository root** (the nearest ancestor with a `.git` entry, file or directory, computed before any marker test). This is what lets the gateway-bound fork `pip install -e <wherever-cloned>` and get clone-location-independent bare installs with zero command. The two markers are an **accident-guard, not a trust control** — they are forgeable, so the residual (a pair planted in an *intermediate* dir inside the clone) is bounded by canonicalize + stop-at-first + no-ascent-above-the-repo-root, and is acceptable because writing inside the clone already implies write access to the user's own catalogue. No `direct_url.json` (an older pip, or a wheel install) → no detection → fall through to layer 4.

- **D3 — There is no repo-scoped source and no cwd fall-back (the security-load-bearing call).** This is the decision this ADR's title turns on. A *cloned repo* dictating where executable code is fetched from is a supply-chain hazard. Rather than replicate RFC-0040's confirm-before-write gate for this higher-stakes case, **the layer is omitted entirely** — the explicit arg plus editable detection already meet the downstream need, so a repo-supplied source buys nothing and costs a code-provenance escalation. Likewise **no layer ever resolves from `.`/cwd**: the only terminal states are a validated source or a clear error. This is the deliberate divergence from the layered-config prior art, which *does* let project config win — that precedent governs build config, not a code-fetch decision.

- **D4 — Resolution is stateless; `config set source` is the only persistence path (no auto-persist).** A one-off `--catalogue` never writes itself back to config. A user wanting a persistent custom default runs `config set source <uri>` (layer 2) — visible and intentional. This deliberately **departs** from the in-repo adapter state-hint, which remembers the adapter as a **correctness** mechanism (an upgrade/uninstall must re-target the adapter it actually wrote files for); source-memory would be mere convenience with no package-manager precedent and a surprising side-effect.

- **D5 — The packaged default is a data file, not a constant, with an asymmetric integrity posture.** Layer 4 is a new packaged `_data/install-defaults.toml` (joining `adapter.toml`, the schemas, and `install-marker.py`, picked up by the existing `package-data = ["_data/*"]` wiring). Upstream ships `git+https://github.com/eugenelim/agent-ready-repo`; **a private downstream fork blanks or drops the file** (absent/empty = no layer-4 default), re-pointing with zero code edits — the baked-default-registry model (PyPI/crates-io). Layer 4's `git+https` default is the one path that **crosses the network**: the existing resolver fetches an **unauthenticated** GitHub-archive tarball with a missing ref defaulting to `main` (`catalogue.py:84` — TOFU against the current tip, no checksum/signature/pin). The integrity posture is therefore **asymmetric by layer** — layers 1–3 reduce to local trust (strong), layer 4 alone crosses the network unauthenticated. This is accepted for now because the network layer is the upstream public default, off the gateway-fork path; **integrity-pinning for the layer-4 fetch is a named follow-on, not part of this decision.**

Boundaries on the decision:

- **Scope is `install`/`upgrade` only.** The discovery verbs `list-packs`/`list-profiles` keep requiring an explicit catalogue — defaulting a *query* needs its own justification and must not silently fetch the upstream URL on a gateway-bound fork. Deferred to a follow-on.
- **The adapter resolver is untouched.** `scope.DEFAULT_ADAPTER` and the user-config adapter layer are unchanged; this decision adds `source` alongside `adapter` in the `[settings]` schema and nothing more. The in-repo *adapter* override that some users want (the Claude-Code-style repo-overrides-user precedence for the projection *target*) is cleanly separable and spun out to its own future RFC.
- **No new infrastructure, no new dependency.** Runtime resolution and stdlib file/metadata reads only (`importlib.metadata`, `urllib.request.url2pathname`, `pathlib`). Principle 3 holds.

## Decision drivers

- **The downstream gateway-fork is hard-blocked today** — drives doing this now over do-nothing: a `git+https`-github-only resolver plus a clone-anywhere fork has *no usable source at all*, and editable detection is the only mechanism that expresses "the clone, wherever it is."
- **The source is a code-provenance boundary, not a file-write target** — drives D3 (no repo source, no cwd) and the asymmetric integrity framing: the cost of getting source wrong is running someone else's code, so the layer a hostile repo could supply is removed, not merely gated.
- **Principle 3 (habit, not infrastructure)** — rules out a hosted registry/index/discovery service; forces runtime-resolution-plus-file-reads.
- **No package-manager precedent for auto-persisting a one-off** — drives D4: npm/pip/cargo persist a source only via explicit config, never as a side-effect of an install.
- **A fork must re-point with zero code edits** — drives D5's data-file-not-constant: a constant URL is dead for the gateway fork and un-substitutable per-distribution without a patch.
- **Most users hit exactly one layer** — mitigates the one real cost (more precedence to reason about): the public user lands on layer 4, the fork on layer 3, and the table makes the order legible.

## Consequences

**Positive:**

- A bare `agentbundle install --pack X` Just Works for both populations with **zero extra command** — the public user via the packaged GitHub default, the editable fork via clone-location-independent detection — closing RFC-0031 D7's promise.
- The code-provenance boundary is **closed by omission, not by a gate** — there is simply no resolution layer a cloned repo or the cwd can drive, which is a stronger guarantee than a confirmation prompt and needs no new control surface.
- A downstream fork's whole adoption story is **"blank `install-defaults.toml`, rely on editable detection"** — no patch to code, no baked path, clone anywhere.
- Stays inside Principle 3 and adds **no dependency**: stdlib metadata + path reads only.

**Negative:**

- **More precedence to reason about** (four layers) than a single required arg — mitigated by the precedence table and by most users hitting one layer.
- Detection is **install-method-dependent**: a *wheel* downstream loses layer 3 and must use explicit `--catalogue` or a bakeable source — accepted, since editable is the blessed downstream path.
- The layer-4 default crosses the network **unauthenticated** (TOFU against `main`, no pin) — a real residual, scoped to the upstream public default and explicitly handed to an integrity-pinning follow-on.
- The in-repo *adapter* override some users want is **deferred**, not delivered here — a known gap with its own future RFC.

**Neutral / to revisit:**

- **Whether layer 2 should outrank layer 3** (chosen: yes — explicit config beats auto-detection). A user who sets a stale source recovers with `config unset source`, named in the diagnostic. Revisit if real usage shows the auto-detected clone is more often the intended source than the persisted one.
- **The `list-packs`/`list-profiles` default and integrity-pinning** stay deferred; a future RFC that backs either reopens the relevant edge of this scope (the query-defaulting edge, or the layer-4 integrity edge). *(Update 2026-06-25: the **query-defaulting edge is reopened and decided by RFC-0047** — the discovery verbs now default through the same chain, because a gateway-bound fork is editable and resolves via layer 3, so a bare query never silently fetches upstream. The **layer-4 integrity edge stays deferred**.)*
- **The forgeable-marker residual in editable detection** is bounded, not eliminated; if a real planted-marker hijack is ever observed, the walk-up's accident-guard would need promoting to a trust control.

## Confirmation

- The implementing spec's acceptance criteria encode the decision — `catalogue` optional on `install`/`upgrade` (and **still required** on `list-packs`/`list-profiles`); `resolve_default_source()` walking the four layers in order and **validating** each output before handing it to the unvalidated `resolve_catalogue`; editable detection with a **real `pip install -e` construction test** plus the editable-detection hardening ACs from D2 (canonicalize-before-walk, reject non-localhost `file://` host, repo-bounded ascent, closed-interval `.git`-root match); the no-cwd and no-repo-source invariants as explicit negative criteria; `source` added to `_KNOWN_KEYS` and the user `[settings]` schema with a validator; the new `_data/install-defaults.toml`; and a clear-error AC for the all-layers-empty case — so conformance is checkable against the spec.
- The spec-stage and diff review passes — **`security-reviewer` mandatory here** because the change crosses a code-provenance / path-and-file / supply-chain boundary, plus `adversarial-reviewer` for spec↔plan↔RFC drift — confirm that **no repo-scoped source or cwd fall-back creeps back in**, that editable detection's walk-up stays repo-bounded and canonicalized, and that the layer-4 network residual is documented rather than silently widened.
- **Enforcement is review-time plus the existing test suite**, not a new CI gate — matching Principle 3. The ~13 adapter default-resolution tests and `tests/unit/test_resolve_user_scope_target_adapter.py` must stay green (the adapter resolver is untouched), which is the regression fence around "this changed source resolution and nothing else."

## Alternatives considered

- **(a) Do nothing — keep `catalogue` required.** Rejected against the **downstream-blocked** driver: the gateway-bound fork has no usable source at all, and every public install re-types the URI.
- **(b) A single hardcoded constant.** Rejected against the **fork-must-re-point-with-zero-edits** driver: un-substitutable per-distribution without a code edit, and a constant URL is dead for the gateway fork.
- **(c) Packaged default file only.** Rejected against the **clone-anywhere** need: substitutable by the fork, but cannot express "the clone, wherever it is" — the clone-anywhere fork still cannot bake a path.
- **(d) Install-context detection only.** Rejected against the **public-user** need: a wheel (public PyPI) has no editable record, leaving the public user with no default.
- **(e) The trusted layered chain (chosen).** Covers public (layer 4), editable fork (layer 3), and explicit/persistent overrides (layers 1–2) **without** a repo-supplied code-source — at the cost of more precedence, mitigated by the table.
- **A repo-committed `source` (gated like RFC-0040's adapter-target).** Rejected against the **code-provenance-boundary** driver: source is higher-stakes than a file-write target, the downstream need is already met by editable detection, so the layer is **omitted entirely** rather than gated behind a confirmation — a stronger guarantee than a prompt.
- **A cwd / `.` fall-back when no layer resolves.** Rejected against the same driver: fail-open to cwd is exactly the silent code-provenance escalation D3 forecloses; the terminal state is a clear error instead.
- **Auto-persisting a one-off `--catalogue` to config.** Rejected against the **no-precedent** driver: a surprising side-effect with no package-manager analogue; `config set source` is the visible, intentional path (D4), and the adapter state-hint is *correctness*, not the convenience this would be.

## References

- RFC-0046 — Convenient install defaults (the accepted decision this ADR records; the five-decision set, the editable-detection spike, the options-considered table, and the asymmetric-integrity framing).
- RFC-0031 — package-manager posture (no server, no index, no daemon; D7's "public default catalogue" this locates).
- RFC-0011 / RFC-0012 + the adapter state-hint — the resolver cascade, and the correctness-not-convenience nature of the state-hint that justifies not auto-persisting source.
- RFC-0040 + ADR-0030 §Risks — the untrusted-origin / confirm-before-write control for a hostile repo-root file (the precedent this ADR declines to replicate, omitting the layer instead).
- `docs/specs/convenient-install-defaults/` — the implementing spec and plan.
- [PEP 610](https://peps.python.org/pep-0610/) — `direct_url.json` carries `dir_info.editable` and an absolute `file://` url, and MUST NOT be created for index installs.
- [Cargo config](https://doc.rust-lang.org/cargo/reference/config.html), [npm config](https://docs.npmjs.com/cli/v11/using-npm/config/), [pip configuration](https://pip.pypa.io/en/stable/topics/configuration/) — the layered-config-plus-baked-default prior art, and the project-over-user precedent this decision deliberately does **not** extend to `source`.
- CHARTER Principle 3 — the habit-not-infrastructure bar this decision clears.
