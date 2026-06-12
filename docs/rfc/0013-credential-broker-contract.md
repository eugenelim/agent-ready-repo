# RFC-0013: Credential broker contract — in-process shim for static tokens, adapter-root subprocess for SSO; formalise four-broker model

- **Status:** Accepted
- **Author:** eugenelim
- **Date opened:** 2026-05-26
- **Date closed:** 2026-05-26
- **Amends:** [RFC-0006](0006-skill-secrets-storage.md) — the two-layer
  architecture rule is preserved; the storage-tier model graduates from
  "the resolver" to "one resolver", and the loader's Python-import shape
  is restructured as a build-projected vendored shim (for `creds`) plus
  an adapter-root subprocess (for `sso-cookie`).
- **Consumes:** [RFC-0004](0004-install-scope-per-pack.md) — adds a
  fifth user-scope-eligible pack alongside [RFC-0007](0007-user-scope-converter-pack.md)'s
  `converters` precedent; reuses ADR-0002's "hook-shaped" narrow
  reading frozen by RFC-0006's follow-on ADR amendment.
- **Consumes:** [RFC-0011](0011-pack-allowed-adapters.md) — the
  `[pack.install] allowed-adapters` field and the `[pack.adapter-contract]
  v0.6` baseline. **RFC-0013 cannot be Accepted before RFC-0011 closes**;
  the contract amendment introduced here (widening
  `allowed-prefixes.user` for Claude Code and Kiro to include
  `.agentbundle/`) bumps to v0.7, strictly above RFC-0011's v0.6 baseline,
  so the two contract changes do not share a version label.
- **Related:** [RFC-0005](0005-user-scope-hook-support.md) — no
  hook-wiring needed (the new pack ships only credentialed-CLI
  primitives and one cooperative setup skill); RFC-0006's ADR amendment
  freezing "hook-shaped" stays load-bearing.

## Summary

Today every credentialed skill in the catalogue resolves secrets by
importing `agentbundle.credentials` in-process — a Python API that
forces a hard `pip install agentbundle` step onto every consuming
skill and has no idiomatic shape for corporate-SSO credentials
(cookie jars with TTLs, refreshed via a browser flow). Empirically,
a downstream consumer of this catalogue carries two near-identical
`browser_auth.py` files plus two `setup_credentials.sh` scripts to
work around the SSO gap; the variance between them is two
parameters.

The naive subprocess-broker fix (skills `subprocess.run([...creds get
namespace key])`) re-introduces the wrap-and-leak shape RFC-0006 § 5
Anti-pattern register explicitly refused — the cleartext crosses
the broker → consumer process boundary on stdout, where any
LLM-driven Bash invocation reads it back. The architecture rule
("skills don't hold credentials; primitives do") **degrades from
structural guarantee to cooperative prose** the moment the resolver
is a separate process that prints tokens on stdout.

This RFC amends RFC-0006 with a redesign that preserves the
structural guarantee:

1. **Promote the security invariants to the broker-agnostic
   contract** — argv ban, "Don't" block, no plaintext dotfile reads,
   never-logged — and demote the env → keychain → dotfile resolver
   from "the convention" to "one of several brokers."
2. **Introduce a four-broker model** keyed by a new
   `metadata.auth: <broker-id>` frontmatter field — `env`, `cli`,
   `creds`, `sso-cookie`. Each broker satisfies the same contract.
3. **`creds` broker is an in-process vendored Python shim**, not a
   subprocess CLI. A single source-of-truth at
   `packs/credential-brokers/.apm/shared-libs/credentials_shim.py`
   is projected by the build pipeline into every consuming skill's
   `scripts/` directory (one copy per consumer, byte-identical,
   gated by `make build-check` drift detection). Consumers import
   it as `from .credentials_shim import load_credentials` — the
   same API surface RFC-0006's `agentbundle.credentials.load_credentials`
   provided, just resolved from a sibling file rather than a PyPI
   package. The cleartext lives only inside the consumer's Python
   interpreter; no subprocess, no stdout, no LLM-readable surface.
4. **`sso-cookie` broker is a subprocess at the catalogue's
   user-scope artifact root (`~/.agentbundle/bin/`), not in any
   adapter's skills directory.** Playwright state is unavoidable,
   so the broker stays a separate process — but it lives at the
   single canonical path `~/.agentbundle/bin/sso-broker.py`, the
   same user-scope root RFC-0006 already established for
   `state.toml`, `credentials.env`, and `sso-profiles/`. Sibling
   to skills directories, adapter-independent, not
   LLM-auto-discoverable. Output is the cookie-jar **path**,
   never the cookie values; the consumer opens the file in its
   own process.
5. **Extract resolution from `agentbundle`.** After migration,
   `agentbundle` ships pack-installer logic only; the
   `agentbundle.credentials` module and the `agentbundle.creds/`
   subpackage are removed. Credential resolution lives in the
   `credential-brokers` pack (the shim's source-of-truth) and is
   build-pipeline-projected into consumers (no PyPI dependency on
   the consumer side).
6. **Migrate every in-tree consumer of `agentbundle.credentials`
   in this RFC's acceptance scope.** Six skills + one author-skill
   teaching block. Each consumer's migration is a one-line import
   change (`from agentbundle.credentials` → `from .credentials_shim`);
   the build pipeline supplies the vendored sibling. The migration
   pins the rip's sequencing: `agentbundle.credentials` cannot be
   removed until every consumer migrates.

## Motivation

Three load-bearing problems and one validation case.

**1. Portability — `agentbundle` as a runtime import is a hard
dependency.** RFC-0006 § Tooling deliverables specified
`agentbundle.credentials` as the loader every credentialed primitive
imports. The pack-catalogue model
([RFCs 0001-0003](0001-bundle-distribution-by-adapter-spec.md))
distributes skills via APM, Claude plugins, and the agentbundle CLI;
adopters consuming the catalogue via APM or Claude plugins may have
never run `pip install agentbundle` and have no reason to. Enterprise
rollouts where Python-package install is itself a ticket (RFC-0006 §
Motivation enumerates this constraint for adopters; the same
constraint now applies to `agentbundle` itself) cannot satisfy the
import. The vendored-shim shape removes the PyPI dependency at zero
structural cost — the same env → keychain → dotfile resolution
ships in the pack and is projected into the consumer's `scripts/`
directory by the build pipeline. Polyglot (non-Python) consumers
remain a real concern but they are not load-bearing for any
credentialed skill that ships today (every existing credentialed
primitive is Python); when one appears, it picks the `env` broker,
which is broker-agnostic at the consumer-language layer by
construction.

**2. SSO mismatch — the three-tier model has no shape for cookie+TTL+refresh.**
RFC-0006's three storage tiers (env var → OS keyring → dotfile)
model token-shaped secrets. A corporate-SSO credential is none of
those: it is a *cookie jar* with a TTL, refreshed by replaying a
browser flow when a downstream API returns 401. Tier 1 (env var)
is absurd for a cookie blob; Tier 2 (keychain) could hold the blob
but RFC-0006's loader API (`load_credentials(namespace,
required_keys=[...]) -> Credentials`) has no refresh hook, no
expiry handling, and no concept of "this credential needs the user
in front of a browser." The team has worked around the mismatch
by writing SSO logic outside the loader entirely — see (4).

**3. Lint enforcement currently confuses contract with implementation.**
RFC-0006 § 4 specifies the argv ban, the "Don't" block, and the
direct-dotfile-read check as conditions on credentialed primitives.
`tools/lint-credentialed-skills.sh` (AC26 a/b/c) implements them
correctly — but the spec prose treats them as inseparable from the
specific resolver implementation. A skill that legitimately uses
some other credential source (`gh` CLI's auth, an SSO broker, a
Vault Agent wrapper) has no clean way to declare itself; the lint
either does not fire (because `credentialed: true` is left off and
the security invariants go unenforced) or fires irrelevantly. The
invariants are the contract; the resolver is an implementation
choice. They should be named that way.

**4. Empirical validation case from a downstream consumer
repository.** A downstream consumer of this catalogue
(`agent-ready-repo`) — a private deployment used by the author
team — has shipped, in production, two near-identical SSO
scripts for corporate-SSO-fronted Jira and Jira Align, each
~150 lines of Playwright + cookie-jar handling, plus two
corresponding `setup_credentials.sh` files. The scripts are
**not** in this catalogue's tree (verifiable: `find packs/
-name "browser_auth*"` returns no matches today); they live
downstream. Per `feedback_dont_hide_unshipped_rfc_paths`, this
RFC names that honestly rather than implying the scripts ship
in-tree.

The meaningful variance between the two downstream scripts is
exactly two values: the session filename and the validation
endpoint. Login URL, success URL pattern, cookie domain set,
refresh-on-401 logic, and keychain storage are identical across
both. A single parameterised `sso-broker` script with
per-profile TOML config replaces both files at zero behavioural
cost; Confluence (downstream: token-only today) gets SSO
support when it needs it by adding a profile row, not a script.
The downstream consolidation is the falsifier for the broker
abstraction: it demonstrates the broker boundary is correctly
placed because it is the one place duplication accumulates in
actual deployment.

In-tree, the two-knob variance is reflected in the four
`atlassian` skills' existing `creds-schema.toml` files (one
required-key per vendor) — the schema shape RFC-0006 § 5
specified for `creds`, generalised here to also drive `sso-cookie`
profile registration. The downstream `browser_auth.py` scripts
are the empirical case; the in-tree schemas are the
load-bearing artefact the RFC pins against.

**Why this is not a follow-up to RFC-0006 rather than an amendment.**
The two-layer architecture rule (skills don't hold credentials)
survives unchanged; promoting and renaming as proposed here is a
substantive change to the storage layer that adopters reading
RFC-0006 must know about. Folding it into a separate "v2" RFC
would leave RFC-0006 as a stale reference for any adopter who
reads the convention chain in order. The amendment shape mirrors
RFC-0004's amendment of RFC-0001 (added a dimension without
relitigating the contract).

## Proposal

### 1. Promote security invariants to the broker-agnostic contract

The following are properties of *any* credentialed primitive,
independent of which broker resolves the secret:

- **Don't block presence.** Every credentialed skill carries the
  `### Security rules (non-negotiable)` heading and the three
  RFC-0006 § 4 substrings ("Never read that file, print it, or
  echo the token"; "Never put the token on the command line"; "do
  not run it for them"), with path/binary substitutions
  per-broker. Substitutions are listed in § 5.
- **Argv ban.** No credentialed primitive accepts a *value-shaped*
  flag (`--token`, `--api-token`, `--api-key`, `--bearer`,
  `--pat`, `--password`). MCP-server-class primitives that accept
  *header-naming* flags (`--bearer-header`, `--auth-header`,
  `--header-prefix`) remain allowed — they name *which* header to
  consult per-request, not the value.
- **No plaintext dotfile reads except by opt-in marker.** A skill
  whose `scripts/` content contains the substring of the
  user-scope credentials file path is flagged unless the
  same-line opt-out marker
  `# credentialed-primitive: reads-creds-directly` is present.
  Implementation must compose path checks via `basename` and
  `Path.parts` to avoid the substring trap (a refuse-guard that
  literally embeds the path string trips its own lint).
- **Never logged, never in `__repr__`, never echoed.** Carried in
  prose; not mechanically lintable but stated as part of the
  contract.
- **Corporate-network requirements (inherited from RFC-0006 § 7).**
  Every broker — and every subprocess it spawns, including the
  Playwright browser launched by `sso-broker` — honours
  `HTTPS_PROXY` / `NO_PROXY` from the environment and the
  system trust store via `REQUESTS_CA_BUNDLE` / `SSL_CERT_FILE` /
  `SSL_CERT_DIR`. The no-`SSL_VERIFY=False`-default ban applies:
  `--insecure` is opt-in only and emits a stderr warning when
  used. RFC-0006 § 7 establishes this for credentialed
  primitives; RFC-0013 extends the same obligations to the
  broker subprocesses themselves.

  **Propagation mechanism (pinned, not deferred).** Brokers spawn
  child processes with explicit env-var forwarding:
  `subprocess.run(..., env={**os.environ, ...overrides})` —
  inheriting the parent's `HTTPS_PROXY` / `NO_PROXY` / `REQUESTS_CA_BUNDLE` /
  `SSL_CERT_FILE` / `SSL_CERT_DIR`, never a fresh empty env. The
  Playwright browser context is launched via
  `chromium.launch_persistent_context(user_data_dir, env={**os.environ, ...})`
  with the trust-store variables forwarded explicitly; for
  Chromium specifically, the trust-store path must also be
  installed at OS level (corporate MDM typically does this; the
  broker's setup-time check verifies). A contributor adding
  `verify=False` to "make it work on my laptop" introduces a
  silent corporate MITM bypass; the implementation spec carries
  unit tests asserting the env-passthrough and a manual-QA row
  for the browser-context propagation.

`tools/lint-credentialed-skills.sh` already implements three of
the mechanical checks (AC26 a/b/c); the RFC's reframing is that
the lint now gates on the broker-agnostic contract, with
broker-specific extensions layered on top per § 4.

### 2. Four-broker model via `metadata.auth: <broker-id>`

A new field is added under the spec-blessed `metadata:` escape
hatch (the same hatch RFC-0006 § Amendments routes
`credentialed:` and `primitive-class:` through, so this change is
allowed by `lint-agent-artifacts.py`'s closed top-level key set):

```yaml
---
name: <skill-name>
description: <triggers>
metadata:
  credentialed: true
  primitive-class: credentialed-cli   # or mcp-server (existing)
  auth: env | cli | creds | sso-cookie   # NEW
  # Broker-specific extras (only the matching block applies):
  namespace: <ns>                        # auth: creds and auth: env
  keys: [<key>, ...]                     # auth: creds and auth: env
  sso_profile: <profile>                 # auth: sso-cookie only
---
```

`auth:` is required when `credentialed: true` is set. The four
broker ids:

| Broker id    | Transport            | What it does | When to pick it |
| ------------ | -------------------- | ------------ | --------------- |
| `env`        | none (env vars)      | Skill reads `<NAMESPACE>_<KEY>` from environment. Catalogue contributes naming convention and security-invariant lint only; no runtime. | Polyglot consumers; adopters with upstream secret managers (1Password CLI, Vault Agent, direnv); zero-install deployments. The lowest common floor. |
| `cli`        | subprocess           | Skill shells out to a vendor-authenticated binary (`gh`, `aws`, `kubectl`, `gcloud`). Vendor's CLI owns the credential. | Anything where the vendor already ships a credentialed auth-CLI; avoids reinventing it. Formalises pattern that was previously folklore. |
| `creds`      | **in-process import** | Consumer `from .credentials_shim import load_credentials`. The shim is a vendored sibling file (`scripts/credentials_shim.py`), projected by `make build` from a single source-of-truth at `packs/credential-brokers/.apm/shared-libs/credentials_shim.py`. Walks env → OS keychain → `~/.agentbundle/credentials.env`. **No subprocess, no stdout, no LLM-readable surface.** Cleartext lives only in the consumer's interpreter. Python-only consumers. | Static API tokens (Personal Access Tokens, vendor API keys); Python consumers; replaces today's `from agentbundle.credentials import load_credentials`. |
| `sso-cookie` | subprocess at `~/.agentbundle/bin/sso-broker.py` | Consumer subprocess-invokes the broker at the catalogue's user-scope artifact root (sibling to skills directories of every adapter; not LLM-auto-discoverable). Broker performs headed-browser SSO once via Playwright, captures cookies for declared domains, stores in keychain, refreshes on 401. Output is the cookie-jar **path**, not the cookie values; consumer opens the file in its own process. | Cookie-based REST after corporate SSO — Atlassian Data Center products (Jira / Confluence / Jira Align / Bitbucket DC), ServiceNow, MediaWiki, internal apps that share session between web UI and REST. |

Every credentialed skill picks exactly one.

**Why two transports.** Static-token resolution is small, stateless,
and reproducible (~50 lines of stdlib Python); in-process import
preserves RFC-0006's structural guarantee at zero capability cost.
SSO cookie capture is heavyweight (Playwright + Chromium), stateful
(cookie jar shared across consuming skills), and inherently requires
a separate process — the in-process shape doesn't apply. The two
transports model the two distinct credential shapes the catalogue
must handle; collapsing them to one transport sacrifices either
security (subprocess for static tokens reintroduces wrap-and-leak)
or feasibility (per-consumer Playwright is absurd).

#### Scope boundary for `sso-cookie` (anti-overpromising)

`sso-cookie` is **not** a universal SSO broker. It works where the
target vendor's REST API accepts the session cookie produced by
the SSO flow. It does **not** apply to:

- **GitLab, GitHub.com (when SSO-fronted), Salesforce, Notion,
  Linear, Figma** — whose REST APIs expect Personal Access Tokens
  or OAuth bearer tokens regardless of SSO state. These use
  `creds` (with the PAT) or `cli` (with the vendor CLI).
- **DOM-scraping for additional CSRF/XSRF tokens** beyond the
  session cookie. ServiceNow write paths sometimes need
  `X-UserToken`; some Atlassian write paths need a separate
  XSRF token. The broker captures cookies only in v1; DOM
  scraping is deferred to a future RFC when a concrete grey-zone
  consumer appears.
- **Browser-automated PAT minting** ("log in via SSO, navigate to
  the PAT-creation page, capture the token"). Useful for
  GitLab-like vendors; out of scope here. A separate `sso-pat-mint`
  broker design awaits a concrete consumer.

The broker id name (`sso-cookie`, not `sso`) telegraphs the scope
so adopters do not reach for it for the wrong vendor.

### 3. Extract credential resolution from `agentbundle` into `packs/credential-brokers/`

`agentbundle.credentials` (the public re-export shim) and
`agentbundle.creds/` (the implementation subpackage —
`loader.py`, `exceptions.py`, `_keychain_macos.py`,
`_credman_windows.py`) are **removed** from the
`packages/agentbundle/` distribution. After this change,
`agentbundle` ships pack-installer logic only (`install`,
`uninstall`, `upgrade`, `validate`, `init-state`, `scaffold`,
`build`, etc. per RFC-0003 / RFC-0004); no runtime-library
surface for consuming skills to import.

The equivalent resolution logic ships from
`packs/credential-brokers/` as two artefacts:

- A **vendored Python shim** (`credentials_shim.py`) for the
  `creds` broker — source-of-truth at
  `packs/credential-brokers/.apm/shared-libs/credentials_shim.py`,
  projected by the build pipeline into every consuming skill's
  `scripts/` directory. Consumers import it as a sibling file;
  the cleartext lives only inside the consumer's Python
  interpreter (the same structural guarantee RFC-0006's
  in-process loader provided).
- A **subprocess CLI** (`sso-broker.py`) for the `sso-cookie`
  broker — source-of-truth at
  `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py`,
  projected by the build pipeline to
  `~/.agentbundle/bin/sso-broker.py` (sibling to every adapter's
  skills directory, not LLM-auto-discoverable; the same
  user-scope artifact root RFC-0006 § 2 established for
  `state.toml`, `credentials.env`, and `sso-profiles/`).

The same env → OS keychain → dotfile precedence is preserved; the
same Win32 error-code dispatch matrix is preserved; the same
`--allow-insecure-fallback` and `--allow-permissive-acl`
discipline is preserved. What changes is the *distribution channel*:
PyPI module → pack-projected sibling file (for `creds`) or
adapter-root subprocess (for `sso-cookie`).

**No deprecation cycle.** `agentbundle` is at `0.x` per
[RFC-0001](0001-bundle-distribution-by-adapter-spec.md); semver
0.x permits breaking changes within the major. The six in-tree
consumers of `agentbundle.credentials` (identified by `grep -r
"from agentbundle.credentials" packs/`) migrate in this RFC's
acceptance scope per § 9.

### 4. New pack: `packs/credential-brokers/`

A new user-scope pack containing two broker artefacts and the
build-pipeline projection sources for both, plus one
LLM-cooperative skill for interactive credential setup (the
deliberate exception described in § 4e). The pack itself
contains **no LLM-addressable broker skills** — neither
`credentials_shim` nor `sso-broker` is exposed as a skill.

Pack manifest:

```toml
[pack]
name = "credential-brokers"
version = "0.1.0"
description = "User-scope credential brokering: credentials_shim (build-projected Python module for auth: creds skills), sso-broker (subprocess at ~/.agentbundle/bin/ for auth: sso-cookie skills), plus one LLM-cooperative credential-setup skill."

[pack.adapter-contract]
version = "0.7"

[pack.install]
default-scope = "user"
allowed-scopes = ["user", "repo"]
allowed-adapters = ["claude-code", "kiro", "codex"]
```

The `[pack.adapter-contract]` version bumps to `0.7` — strictly
above RFC-0011's v0.6 baseline — because RFC-0013 introduces a
second contract change (widening `allowed-prefixes.user` for
Claude Code and Kiro to include `.agentbundle/`) on top of
RFC-0011's v0.6 (which added `allowed-adapters` and Codex's
`.agentbundle/` prefix). Sharing one version label across two
RFCs' contract changes would leave adopters unable to tell
which subset they need; the v0.6 → v0.7 bump segregates the two
cleanly. RFC-0013 cannot be Accepted before RFC-0011 closes;
the implementation spec lands the schema patch for both in one
PR. The pack declares `allowed-adapters` explicitly because
user-scope installs of the broker pack must target a known
adapter set — the `adapter-root-bins/` projection (§ 4d) and the
contract
amendment widening `allowed-prefixes.user` to include
`.agentbundle/` per § 4d apply to exactly the listed adapters.

Source-of-truth layout:

```
packs/credential-brokers/
├── pack.toml
└── .apm/
    ├── shared-libs/                              ← NEW primitive class § 4c
    │   ├── credentials_shim.py                   ← projected into consumer skills' scripts/
    │   ├── _keychain_macos.py                    ← carried alongside; private helper
    │   └── _credman_windows.py                   ← carried alongside; private helper
    ├── adapter-root-bins/                        ← NEW primitive class § 4d
    │   └── sso-broker.py                         ← projected to ~/.agentbundle/bin/
    └── skills/                                   ← exactly one skill (§ 4e)
        └── credential-setup/                     ← LLM-cooperative, user-invoked
            ├── SKILL.md
            └── scripts/
                └── setup.py
```

The pack passes RFC-0004's three user-scope refusal rails by
construction:

- No `seeds/` — the pack ships primitives, not adopter-installed
  README/template/governance content.
- No hooks — neither `.apm/hooks/` nor `.apm/hook-wiring/`
  ([RFC-0005](0005-user-scope-hook-support.md)'s deferral does
  not constrain this pack).
- No `<adapt:NAME>` markers in any primitive file — credential
  resolution and SSO capture do not reference per-repo
  vocabulary.
- **No LLM-addressable broker skills** — `credentials_shim` and
  `sso-broker` ship outside `.apm/skills/`. The one skill that
  *does* ship (`credential-setup`, § 4e) is LLM-cooperative by
  design: its purpose is for the LLM to discover and tell the
  user to invoke; its output discipline keeps the cleartext out
  of LLM-visible scope. This is the deliberate exception to the
  "no skills" rule, named here so the rest of the pack
  description does not surprise later readers.

Falsifiable test (RFC-0004 § Per-pack default and allowance): the
same artefact serves every repo verbatim — the broker is a
function of the user's credentials and the SSO profile, neither of
which is project-scoped.

#### 4a. `credentials_shim.py` — the `creds` broker (vendored Python module)

The shim is the same env → OS keychain → dotfile loader RFC-0006
specified, *as a sibling-importable Python module* rather than a
PyPI package. Public API:

```python
from .credentials_shim import (
    Credentials,                  # immutable attribute-access object
    CredentialsMissingError,      # raised when a required key is unresolvable
    Tier2HardFailError,           # raised on Win32 matrix hard-fail codes
    load_credentials,             # the single entry point
)

creds = load_credentials("<namespace>", required_keys=["API_TOKEN", ...])
token = creds.API_TOKEN           # in-process; never crosses a process boundary
```

Identical to RFC-0006's `agentbundle.credentials.load_credentials`
API. The only difference is the import source: `from
agentbundle.credentials` → `from .credentials_shim` (sibling
relative import).

**Implementation constraints:**

- **Stdlib-only.** Same as RFC-0006 § 2 — `os`, `pathlib`,
  `subprocess`, `getpass`, `tomllib`, `ctypes` on Windows. No
  Python dependencies; no `pip install` for the shim itself.
- **Per-platform Tier-2 backends preserved.** `_keychain_macos.py`
  (subprocess wrapper over `/usr/bin/security`) and
  `_credman_windows.py` (ctypes over `advapi32.CredReadW`/`CredWriteW`/
  `CredDeleteW`/`CredFree`) carry over from
  `agentbundle/creds/_keychain_macos.py` and
  `agentbundle/creds/_credman_windows.py` byte-equivalent. The
  build pipeline projects them as siblings of `credentials_shim.py`
  into each consuming skill's `scripts/` directory.
- **No `get`, no `setup`, no CLI surface.** The shim is a Python
  module, not an executable. There is no stdout-emitting entry
  point that an LLM could Bash-invoke to read the cleartext.
  Interactive credential setup is a separate user-invoked
  artefact (§ 4e).

**Why vendored, not PyPI-shipped.**

- PyPI installation reintroduces the "`pip install <X>`" friction
  the RFC exists to remove (Alternative I).
- The shim is small (~150 lines including Tier-2 backends) and
  stable (RFC-0006 froze its API). Duplication cost is bounded
  per the build pipeline's drift gate.
- Source-of-truth lives in one file; projected copies are
  byte-identical and drift-checked by `make build-check`.

**Why in-process and not subprocess.**

- **The structural guarantee RFC-0006 § 1 codified.** Cleartext
  exists only inside the credentialed primitive's interpreter,
  never crosses a process boundary, never lands on stdout, never
  reaches a path an LLM-driven Bash invocation could exfiltrate.
- A subprocess broker (the v1 of this RFC, rejected as
  Alternative G) printed cleartext on stdout — exactly the
  wrap-and-leak shape RFC-0006 § 5 Anti-pattern register named
  by example. No defensive lint can prevent a future
  `logger.debug(result.stdout)`.
- The in-process import has the same attack surface as any
  Python module: a malicious skill body that reads
  `creds.API_TOKEN` and prints it leaks the token. That risk
  exists with the PyPI loader today; the vendored shim does not
  worsen it.

#### 4b. `sso-broker.py` — the `sso-cookie` broker (subprocess at adapter root)

A subprocess CLI consolidating the SSO-cookie-capture pattern.
Implementation language: Python; declares Playwright as a runtime
dependency per RFC-0007 § Runtime dependencies (one-time `pip
install playwright; playwright install chromium` documented in the
broker's setup-and-troubleshooting markdown — see § 4f).

**Installation location:**
`~/.agentbundle/bin/sso-broker.py`. The same user-scope artifact
root RFC-0006 § 2 established for `state.toml`, `credentials.env`,
and `sso-profiles/`. One canonical path independent of adapter;
consumers from any adapter resolve via `Path.home() / ".agentbundle"
/ "bin" / "sso-broker.py"`. **Sibling to every adapter's skills
directory, not inside any of them.** No SKILL.md; not
LLM-auto-discoverable as a skill.

**Contract amendment required: widen `allowed-prefixes.user` for
each supported adapter to include `.agentbundle/`.** RFC-0004
declared `allowed-prefixes.user = [".claude/"]` for Claude Code;
RFC-0011 declared `[".agents/skills/", ".agentbundle/"]` for
Codex (the `.agentbundle/` entry is already there). Claude Code
and Kiro need the same prefix added so the `adapter-root-bins/`
projection (§ 4d) can write to `~/.agentbundle/bin/`. The
implementation spec carries the schema amendment as a v0.7
contract update (strict superset of RFC-0011's v0.6); the prefix
list per adapter becomes:

| Adapter | allowed-prefixes.user (after this RFC) |
| ------- | --------------------------------------- |
| `claude-code` | `[".claude/", ".agentbundle/"]` |
| `kiro`        | `[".kiro/", ".agentbundle/"]`   |
| `codex`       | `[".agents/skills/", ".agentbundle/"]` *(unchanged — already declared per RFC-0011)* |

**Why not in `<skills-dir>/sso-broker/`.** A broker at
`<skills-dir>/<name>/SKILL.md` is auto-loaded by the adapter and
becomes LLM-addressable — the agent can invoke
`/sso-broker get-cookies <profile>` directly from chat. Even with
path-only output, exposing the broker as a skill multiplies the
attack surface (auto-loaded SKILL.md teaches the LLM the
invocation shape; the broker becomes one tool-call away from a
malicious prompt). Living outside the skills directory means the
LLM has no auto-discovered handle on the broker — it must be
called by name from inside a consuming skill's `scripts/` code
(which the LLM does not see).

**Why `~/.agentbundle/bin/` and not per-adapter
`~/.<adapter>/agentbundle/bin/`.** Per-adapter paths force
multi-adapter adopters to install N broker copies (one per
adapter they use), create cross-scope-resolution surface (a
user-scope consumer paired with a repo-scope broker can't find
it via the `__file__`-walk), and require a per-adapter target
table in the build pipeline. The single `~/.agentbundle/`
path uses RFC-0006's already-established artifact root,
collapses to one canonical location, and makes consumer
resolution adapter-agnostic. The trade is one contract
amendment (widening `allowed-prefixes.user` for Claude Code and
Kiro) — paid once.

Subcommands:

| Verb | Effect |
| ---- | ------ |
| `register <profile>` | Interactive: opens a headed browser at the profile's `login_url`, observes the SSO flow, captures cookies for declared domains on landing at `success_url_pattern`, persists the profile TOML and the cookie jar. |
| `get-cookies <profile>` | Prints the path to the on-disk cookie jar (exit 0 if valid, exit 2 if re-auth needed — the broker's `register` flow runs and retries). Output is a path, never the cookie values themselves. |
| `test <profile>` | Makes a request to the profile's `validation_endpoint`; exit 0 on 2xx, exit 2 on 401 (triggers re-register), exit 3 on other failures. |
| `refresh <profile>` | Equivalent to `register` but bypasses the "already registered" check; for adopters who want to proactively refresh before TTL. |
| `list-profiles` | Lists registered profiles and last-known validity (no cookie values). |
| `rm <profile>` | Removes a profile's TOML and its cookie jar. |

Profile schema (`~/.agentbundle/sso-profiles/<profile>.toml`,
written by `register`, never hand-edited):

```toml
[profile]
name = "<profile-name>"
login_url = "https://jira.acme-corp.com"
success_url_pattern = "https://jira.acme-corp.com/secure/.*"
cookie_domains = ["jira.acme-corp.com", "sso.acme-corp.com"]
session_filename = "jira-session.jar"
validation_endpoint = "/rest/api/2/myself"
ttl_hint_minutes = 480
```

Two of these — `session_filename` and `validation_endpoint` — are
exactly the two-knob variance the team's existing per-skill
scripts demonstrate. The remaining fields are derived by `register`
from observation (browser navigation captures `login_url`,
landing URL pattern, and cookie domains) or accepted defaults
(TTL hint).

Cookie jars are stored in the OS keychain when Tier-2 is
available and succeeds; fall back to a 0600 file under
`~/.agentbundle/sso-cookies/<profile>.jar` only when Tier-2 is
*deferred-by-policy* on the platform (Linux today). The
`sso-cookie` broker inherits **RFC-0006's Win32 error matrix
verbatim** — `ERROR_NOT_FOUND` is the only legitimate fall-through
(no credential at this target, run `register`); the hard-fail
codes (`ERROR_NO_SUCH_LOGON_SESSION`, `ERROR_INVALID_FLAGS`,
`ERROR_LOGON_FAILURE`) exit non-zero with stderr naming the
cause. Silent degradation defeats the security posture the user
chose, exactly as RFC-0006 § 2 specifies for `creds`. The
implementation reuses RFC-0006's per-platform Tier-2 backends
(`/usr/bin/security` on macOS, `ctypes` + `advapi32.CredReadW`/
`CredWriteW`/`CredDeleteW`/`CredFree` on Windows).

**Three Tier-2 outcomes distinguished:**

| Outcome | Trigger | Result |
| ------- | ------- | ------ |
| **Deferred-by-policy** | Linux today (libsecret integration is a v2 RFC) | Silent floor to 0600 file under `~/.agentbundle/sso-cookies/`; no warning (this is the documented Linux path, not a degradation). |
| **Hard-fail** | RFC-0006 Win32 matrix codes (no logon session, invalid flags, logon failure) | Exit non-zero; stderr names the cause; do **not** floor to file. |
| **Legitimate-empty** | `ERROR_NOT_FOUND` / Tier-2 backend present but no credential at this target | Trigger `register` (interactive) on platforms where Tier-2 is supported. On Linux, where Tier-2 is deferred-by-policy, the file floor is the documented path (per the row above). Tier-2-capable platforms do **not** silently floor to the file — that would re-introduce the silent-degradation anti-pattern RFC-0006 § 2 refuses. |

**Edge cases pinned in the implementation spec:**

- **Mid-session cookie rotation.** Some IdPs rotate `JSESSIONID`
  on activity. Policy: a downstream 401 triggers re-`register`
  on the next `test` failure; the broker does not attempt
  silent in-band refresh.
- **Concurrent profiles for the same vendor.** Two profiles
  targeting `jira.acme-corp.com` (e.g. `acme-jira` and
  `acme-jira-staging`). Cookie jars are keyed by **profile
  name globally**, not by `cookie_domains`; profile overlap on
  the same host is allowed and the user picks which to use
  via `sso_profile:` per-skill.
- **Cookie-jar size limits.** Windows Credential Manager's
  `CredentialBlob` is capped at ~2.5 KB per credential
  (5 × 512 bytes). Large jars (sub-domain cookies + third-party
  session cookies) can exceed it. Policy: split when the
  serialised jar exceeds **2 KB** (2 KB chosen explicitly to leave
  headroom under the cap), with continuation credentials named
  `agentbundle:sso:<profile>:<n>` and indexed in a header
  credential at `agentbundle:sso:<profile>`. Overflow-to-file
  fallback when the keychain backend itself refuses
  (e.g. corporate-locked-down Credential Manager that disallows
  multi-credential continuation).

  **Reserved namespace prefix `sso`.** The continuation scheme
  consumes the `<namespace>` slot of RFC-0006 § 2 Tier 2's
  `agentbundle:<namespace>:<key>` target-name convention. To
  prevent collisions with user-created credential namespaces,
  `sso` is reserved as a broker-only prefix in the
  `agentbundle:*` target-name space. The user-invoked
  credential-setup skill (§ 4e) rejects `sso` (and any other
  broker-reserved prefix added by future RFCs) at the namespace
  prompt with stderr naming the reserved set. The implementation
  spec carries the reserved-prefix list and the rejection AC.
- **TTL handling.** `ttl_hint_minutes` is a hint, not a contract
  — some IdPs extend TTL transparently on activity. The
  broker's `test <profile>` verb is the source of truth for
  validity; `get-cookies` returns whatever is stored and lets
  the consumer's 401 trigger `test` + re-`register`.
- **Tier-2 hard-fail.** Per the table above, no silent floor.

**Consumer path resolution for `sso-broker`:**

```python
# inside <consumer-skill>/scripts/_client.py
from pathlib import Path
import os, subprocess, sys

SSO_BROKER = Path.home() / ".agentbundle" / "bin" / "sso-broker.py"

if not SSO_BROKER.exists():
    raise RuntimeError(
        f"sso-broker not installed at {SSO_BROKER}; "
        f"install the 'credential-brokers' pack at user scope"
    )

result = subprocess.run(
    [sys.executable, str(SSO_BROKER), "get-cookies", profile],
    capture_output=True, text=True, check=False,
    env={**os.environ},   # per § 1 corporate-network propagation
)
```

`Path.home()` resolves to `$HOME` on POSIX (`/Users/<name>` /
`/home/<name>`) and `%USERPROFILE%` on Windows (`C:\Users\<name>`)
— platform-uniform via stdlib. The same absolute path applies to
consumers from every supported adapter (`claude-code`, `kiro`,
`codex`), so the resolution formula does not change per adapter.

**Consumers always reach the user-scope broker.** The broker pack
declares `default-scope = "user"`; a consumer at user scope or
repo scope both look at `~/.agentbundle/bin/sso-broker.py`. A
broker installed at repo scope (rare but allowed by
`allowed-scopes = ["user", "repo"]`) lands at
`<repo>/.agentbundle/bin/sso-broker.py` and would not be found by
the `Path.home()` resolution. The implementation spec carries
this as a known limitation: SSO-cookie use requires the broker
pack at user scope (or a future repo-scope-aware resolver — left
for follow-on if a concrete repo-scope SSO consumer appears).
The missing-broker error above names the install command so the
adopter has a clear remediation.

#### 4c. Build-pipeline projection — `shared-libs` (new primitive class)

The `creds` broker is a Python module the build pipeline copies
from one source-of-truth into many consumer skills. This requires
a new primitive class in the catalogue's build pipeline:

- **Source path:** `packs/credential-brokers/.apm/shared-libs/*.py`.
- **Target rule:** for every skill in any pack whose `SKILL.md`
  frontmatter declares `metadata.auth: creds`, project each
  `shared-libs/*.py` file into that skill's `scripts/` directory
  with the same basename. Projection is byte-identical; the build
  pipeline does not transform contents.
- **Trigger gating:** projection fires only for skills declaring
  `metadata.auth: creds`. Skills with `auth: env`, `auth: cli`, or
  `auth: sso-cookie` do not receive the shim (they do not need
  it). Skills with no `metadata.credentialed: true` are ignored.
- **Drift gate:** see § 6 for the two-command split.
  `make build-self` is the idempotent projector (write-capable;
  creates missing copies, removes orphans, overwrites modified
  copies); `make build-check` is the read-only gate that errors
  on any of the three drift outcomes (modified / missing /
  orphaned).

The `shared-libs/` primitive class also covers any future
broker-side library code other brokers need to share with
consumers. The implementation spec pins the projection AC and
the drift-detection AC.

**Why a new primitive class, not a sub-shape of skills.** Today's
five `.apm/` subdirectories (`skills/`, `agents/`, `commands/`,
`hooks/`, `hook-wiring/`) each project to one adapter target.
`shared-libs/` projects to *many* targets, one per consuming skill
in the catalogue — a many-to-many shape the existing classes do
not model. Treating it as a sub-shape of `skills/` would either
require a per-skill manifest declaring "I receive shared libs"
(redundant with `metadata.auth`) or break the one-target-per-class
contract.

**Why no manifest declaring which shim files to project.** All
files in `shared-libs/` project together — the build pipeline
copies the directory wholesale into each receiving skill. A future
manifest could pick subsets if shared libs grow heterogeneous; v1
ships one set.

**Inter-pack collision policy.** Two packs cannot both ship a
`shared-libs/` file with the same basename. If `pack-A/.apm/shared-libs/credentials_shim.py`
and `pack-B/.apm/shared-libs/credentials_shim.py` both exist
(regardless of whether their contents match), the build pipeline
**hard-errors** at projection time with stderr naming both
source paths. There is no last-writer-wins fallback; silent
collision would produce non-determinism the drift gate cannot
diagnose. The implementation spec carries this as an AC: a
fixture with two `shared-libs/credentials_shim.py` sources
verifies the rejection. In practice v1 ships exactly one
`shared-libs/` source (in `credential-brokers`); the policy
guards against a future second-pack collision.

**Receiving-skill `scripts/` directory.** If a consumer skill
declares `metadata.auth: creds` but does not have a `scripts/`
directory, the build pipeline **creates** it before projection.
The Acceptance Criterion is "the projection succeeds against a
skill that has a `SKILL.md` and `references/` but no
`scripts/`." Authors creating a new credentialed skill from
scratch via `add-credentialed-skill` get this for free — the
author skill scaffolds a `scripts/` directory by default — but
the build pipeline does not require it.

#### 4d. Build-pipeline projection — `adapter-root-bins` (new primitive class)

The `sso-cookie` broker is a Python executable the build pipeline
places at the catalogue's user-scope artifact root. This requires
a second new primitive class:

- **Source path:** `packs/credential-brokers/.apm/adapter-root-bins/*.py`.
- **Target rule:** project each `adapter-root-bins/*.py` file to
  `$HOME/.agentbundle/bin/<basename>.py` at user scope (the
  default and recommended scope for the broker pack). At repo
  scope, projection target is `<repo>/.agentbundle/bin/<basename>.py`
  — supported by `allowed-scopes = ["user", "repo"]` but
  discouraged (see § 4b's known limitation on cross-scope
  resolution).
- **Trigger gating:** projection always fires for the
  `credential-brokers` pack — there is no per-skill declaration
  needed because the binary is single-tenant (one per scope).
- **Contract amendment for path-jail compliance.** RFC-0004's
  `allowed-prefixes.user` defines what packs can write at user
  scope. This RFC's projection writes to `.agentbundle/`, which
  is **not** declared in every adapter's prefix list today.
  Codex declares it per RFC-0011 (`[".agents/skills/",
  ".agentbundle/"]`); Claude Code and Kiro do not (Claude Code
  is `[".claude/"]`; Kiro is `[".kiro/"]` per the contract
  reading). The contract is amended at v0.7 (strict superset of
  RFC-0011's v0.6 baseline) to widen each user-scope adapter's
  `allowed-prefixes.user` to include `.agentbundle/`. The schema
  change is one entry per adapter; the implementation spec
  carries the schema patch as an AC and pins acceptance ordering
  (RFC-0011 must close first).
- **`allowed-adapters` gates which adapters this projection
  applies to — at user scope only.** Per RFC-0011's post-merge
  erratum (the *Repo-scope projection* section), `allowed-adapters`
  has **user-scope semantics only**; at repo scope the field is
  inert. The pack's `allowed-adapters = ["claude-code", "kiro",
  "codex"]` (§ 4 manifest) refuses a user-scope install under any
  other adapter (e.g. Copilot, which has no user-scope root in the
  v0.7 contract). At repo scope, the gating mechanism is different:
  the v0.7 contract widens `allowed-prefixes.user` for the three
  named adapters to include `.agentbundle/`, but does **not** add
  the same prefix for Copilot — so a repo-scope install under
  Copilot is refused by the schema's path-jail check against the
  pack's projection target, not by `allowed-adapters`. Net effect:
  Copilot is gated out at both scopes via two different mechanisms,
  consistent with RFC-0011's user-scope-only framing of
  `allowed-adapters`.
- **Mode bits:** projected `*.py` files are written 0755 on POSIX
  (executable by the user) and read-only-for-group/other; on
  Windows the inherited DACL from `%USERPROFILE%` governs
  (matching RFC-0006 § 2 Tier-3 Windows behaviour).
- **No PATH manipulation.** The build pipeline does not modify
  `PATH`. Consumers resolve the broker path via `Path.home() /
  ".agentbundle" / "bin" / "sso-broker.py"` (§ 4b snippet) — no
  PATH dependency, no shell-config edits, no
  corporate-laptop-policy surface.

The `adapter-root-bins/` primitive class also covers any future
broker-side executables (an OAuth device-flow broker, etc.) that
ship as user-scope subprocesses rather than skills.

**Why `~/.agentbundle/` rather than per-adapter `~/.<adapter>/agentbundle/`.**
See § 4b's "Why `~/.agentbundle/bin/` and not per-adapter…"
explanation. Single canonical path; one resolution formula;
RFC-0006-aligned with the existing catalogue user-scope root;
trade is one contract amendment (widen `allowed-prefixes.user`
for two adapters) paid once.

#### 4e. Interactive credential setup — a user-invoked skill

RFC-0006 § 3 specified `agentbundle creds setup <namespace>` as
the interactive acquisition flow that prompts for tokens via
`getpass` and writes to the chosen tier. With `agentbundle` reduced
to pack-installer logic and no `agentbundle-creds` subprocess CLI,
the setup flow ships as a **user-invoked skill** in the
`credential-brokers` pack.

Wait — § 4 above says the broker pack ships **no skills**. The
setup flow is the exception: it is LLM-cooperative (the LLM
discovers the skill, tells the user to invoke it, but never reads
the token value itself). The skill's contract:

- `SKILL.md` describes when to invoke (`when the consumer skill
  reports a missing credential`); the LLM's role is to *tell the
  user to run the setup*, not to run it itself.
- `scripts/setup.py` runs in the user's terminal, prompts via
  `getpass`, writes to the tier the user picks
  (`--allow-insecure-fallback` discipline preserved per RFC-0006
  § 3).
- The skill's `description:` includes the verbatim phrase
  *"interactive, user-invoked, do not auto-run"* so the LLM's
  cooperative discipline (per the "Don't" block) treats it like
  the existing `agentbundle creds setup` instruction.
- The setup script never prints the token to stdout — it confirms
  success and exits.

This is the *one* LLM-discoverable skill in the
`credential-brokers` pack. Its existence is a deliberate
LLM-cooperative concession: the user has to run setup, and the
LLM is the natural place to surface that instruction. The setup
script's output discipline (no token in stdout) keeps the
cleartext out of LLM-visible scope.

A future variant lands setup as an `adapter-root-bins/` binary
adopters run directly without the LLM in the loop; v1 ships it
as a skill because the LLM-mediated instruction is the dominant
discovery path today.

#### 4f. First-use install experience — Playwright for `sso-broker`

The `sso-broker` script depends on Playwright (and on Chromium
installed via `playwright install chromium`). Neither is shipped
by the catalogue install routes; both are runtime dependencies
per RFC-0007's convention.

**Default behaviour (v1):**

- On the broker's first invocation (`register` or `get-cookies`),
  the script does `try: import playwright; except ImportError`
  and exits with stderr:
  ```
  sso-broker: playwright not installed.
  Run: pip install playwright && playwright install chromium
  ```
- Claude Code (or other host) reads the stderr, surfaces the
  install instruction, and typically offers to run it.
- After the user accepts (or runs it manually), `sso-broker`
  re-runs and succeeds.

**Documented preemptive path:**

The `credential-brokers` pack's pack-level README — projected via
`seeds/README.md` per the standard pack-source-of-truth split —
names the Playwright install as the first user-facing step:

> When you install this pack and want to use SSO cookie capture,
> run once: `pip install playwright && playwright install chromium`.
> Static-token credential resolution (`auth: creds`) does not need
> Playwright; only `auth: sso-cookie` skills do.

**No automatic pip invocation.** The broker does not run
`pip install` on the user's behalf. Corporate environments often
gate `pip install` behind tickets or internal mirrors; surfacing
the command and letting the user (or the agent at the user's
behest) run it is the safe default. A future `sso-broker setup`
verb that runs the install for the user is left as a follow-on
(the explicit user-invocation makes it less surprising than an
auto-pip on first use).

### 5. Skill frontmatter shape and broker-specific extras

A credentialed skill's `SKILL.md` frontmatter declares the broker
and any broker-specific configuration:

```yaml
# Example: a Jira skill behind corporate SSO.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: sso-cookie
  sso_profile: acme-atlassian

# Example: a GitLab skill using a PAT.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: creds
  namespace: gitlab
  keys: ["token"]

# Example: a GitHub skill using `gh` CLI.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: cli

# Example: a skill that just reads an env var.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: env
```

The "Don't" block substitutes per-broker:

- `auth: env` — drops the dotfile sentence; keeps argv ban; keeps
  "do not print or echo."
- `auth: cli` — replaces dotfile references with the vendor CLI's
  auth-store reference (`gh auth login`, `aws configure`, etc.);
  keeps argv ban.
- `auth: creds` — uses RFC-0006's existing block verbatim (the
  dotfile path is identical; the *resolver* changed from a PyPI
  import to a vendored sibling import — but the architectural
  rule, "skills don't hold credentials, primitives do," is
  preserved structurally rather than degraded to prose).
- `auth: sso-cookie` — substitutes "cookie jar in OS keychain"
  for "token in dotfile"; argv ban remains literal (the broker
  outputs a path, not a value, so argv leak is structurally
  impossible — but the rule stays for uniformity).

The four substituted variants ship as labelled sections under
the `add-credentialed-skill` skill's existing
`assets/credentialed-skill-SKILL.md` template (§ 6).

### 6. Lint changes

`tools/lint-credentialed-skills.sh` (AC26 today) gains
broker-conditional rules layered on top of the broker-agnostic
contract. Required behaviour:

- **Broker-agnostic checks (apply to all credentialed skills):**
  the existing AC26(a) Don't-block presence; AC26(b) argv-flag
  detection (still scoped to `primitive-class: credentialed-cli`
  per RFC-0006); AC26(c) dotfile substring + opt-out marker.
- **Broker-specific checks:**
  - `auth: creds` — the skill's `scripts/` must import the
    vendored shim (`from .credentials_shim import …` or
    equivalent relative-import shape; AST-walk for matching
    `ImportFrom` nodes with `module == "credentials_shim"`).
    The build pipeline guarantees the shim file is present in
    `scripts/`; the lint guarantees the consumer actually uses
    it (vs. reimplementing env → keychain → dotfile
    resolution by hand).
  - `auth: env` — **`namespace` and `keys` are required**
    frontmatter fields (the schema refuses an `env`-broker skill
    that omits either). The lint enforces **presence**, not
    exhaustivity: for each `<NAMESPACE>_<KEY>` in the declared
    namespace×keys product, the AST-walk verifies at least one
    `os.environ[...]` / `os.getenv(...)` read with a matching
    key argument exists in `scripts/`. **Reads of env vars
    *outside* the declared product (e.g. `os.getenv("PATH")`
    for diagnostics, `os.environ["LANG"]` for locale handling)
    are NOT flagged in v1** — the lint asks "does the skill use
    every credential it declares?", not "does the skill read
    only declared credentials?" Stricter enforcement (refusing
    non-declared env reads) is deferred until a concrete false
    positive surfaces and motivates the tradeoff. All
    broker-agnostic checks (AC26 a/b/c — "Don't" block, argv
    ban, no plaintext dotfile reads) apply to env-broker skills
    unchanged.
  - `auth: sso-cookie` — the skill's `scripts/` must subprocess-
    invoke the SSO broker at `Path.home() / ".agentbundle" /
    "bin" / "sso-broker.py"` (AST-walk for a `subprocess.run`
    whose first argument resolves to a path ending in
    `.agentbundle/bin/sso-broker.py`). Skills that inline
    Playwright are flagged; skills that hard-code a non-`Path.home()`
    absolute path are flagged because absolute paths break across
    user accounts.
  - `auth: cli` — no positive-grep enforcement; vendor CLIs
    have heterogeneous invocation shapes. The "Don't" block's
    vendor-CLI variant is the only mechanically checkable
    item.
- **Drift check for projected `shared-libs/`** — split across
  two commands with disjoint responsibilities:

  | Command | Role | Behaviour on each drift outcome |
  | ------- | ---- | ------------------------------- |
  | `make build-self` | **Idempotent projector** (write-capable). Always brings the projected tree into sync with the sources: creates missing copies, removes orphans, overwrites modified copies with the source. Never errors on drift — its job is to *resolve* drift. | All three drift outcomes (modified / missing / source-deleted projected exists) are silently corrected. |
  | `make build-check` | **Read-only gate** (no writes). Compares projected tree against sources; errors on any mismatch. Used in CI and pre-commit. | All three drift outcomes (modified / missing / source-deleted projected exists) produce a non-zero exit with stderr naming the offending file, the source path, and the regeneration command (`make build-self`). |

  The gate ordering is: CI runs `make build-check`, which errors
  on drift; the developer runs `make build-self` locally to fix
  it; `make build-check` then passes. Inner-loop is "edit
  source → `make build-self` → run tests"; CI loop is
  "`make build-check` → fail loudly if developer skipped the
  projection step."

  The three specific drift outcomes the gate distinguishes:

  | Outcome | Trigger | `build-check` (gate) | `build-self` (projector) |
  | ------- | ------- | -------------------- | ------------------------ |
  | **Modified projected copy** | byte mismatch between projected file and source | non-zero, error names source + regeneration command | overwrites projected with source bytes |
  | **Missing projected copy** | consumer declares `auth: creds` but `credentials_shim.py` is absent from its `scripts/` (e.g., never ran `make build-self` since adding the frontmatter, or author manually deleted the file) | non-zero, error names target + regeneration command | creates the file from the source |
  | **Orphaned projected copy** | consumer carries a `credentials_shim.py` but the consumer no longer declares `auth: creds` (or the broker pack's source-of-truth was removed) | non-zero, error names orphaned copy + regeneration command | removes the orphaned copy |

**Substring-trap discipline (two traps, not one).**

1. *Existing trap (AC26(c)):* refuse-guards that literally embed
   the path string `.agentbundle/credentials.env` trip the same
   lint that catches reads. Per memory
   `feedback_credentialed_lint_substring_trap.md`, the lint
   composes path checks via basename and `Path.parts`, never the
   literal full string. This rail extends to the new checks.

2. *New trap introduced by this RFC:* the positive-grep targets
   for the broker checks must avoid collisions with reference
   strings the lint shouldn't fire on.
   - For `auth: creds`, the check is AST-based (matching
     `ImportFrom(module="credentials_shim")`) rather than a raw
     grep. This avoids collisions with prose/doc references to
     the shim by name. A grep-based fallback would need to
     match the import-statement shape (`from .credentials_shim
     import`) not the bare module name.
   - For `auth: sso-cookie`, the check is AST-based — matching
     a `subprocess.run` whose first argument resolves to a path
     ending in `agentbundle/bin/sso-broker.py`. The bare string
     `sso-broker` collides with the broker's source-tree path
     (`packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py`)
     in test fixtures and doc references; AST-matching on the
     subprocess invocation shape disambiguates.
   - The lint script must itself avoid the same trap when it
     appears under a path that a future lint-of-lints would
     walk (e.g. construct the search pattern at runtime with
     parts assembled separately, not as a compile-time
     literal that would match itself).

### 7. `add-credentialed-skill` template restructure

The author-skill at `packs/core/.apm/skills/add-credentialed-skill/`
currently presents one template variant (per RFC-0006 § 4 §
Amendments, two variants since the `mcp-server` class was added).
After this RFC, the template variants are keyed on `auth:`, not on
`primitive-class:`:

```
add-credentialed-skill/assets/
├── credentialed-skill-SKILL-env.md
├── credentialed-skill-SKILL-cli.md
├── credentialed-skill-SKILL-creds.md
└── credentialed-skill-SKILL-sso-cookie.md
```

The author picks the broker first; the skill prompts for
broker-specific config (namespace+keys for `creds` and `env`,
profile name for `sso-cookie`, vendor CLI binary for `cli`) and
copies the matching block. Existing `primitive-class:
credentialed-cli` vs `mcp-server` distinction stays for the
(orthogonal) MCP-server case — a skill could be
`primitive-class: mcp-server, auth: creds` if the MCP server's
auth happens to be a static token resolved via the `creds`
broker.

**First-skill-creation flow for `auth: creds` authors.** When an
author creates a new skill declaring `auth: creds`, the
`credentials_shim.py` file does not yet exist in the new skill's
`scripts/` directory — the build pipeline projects it on the
next `make build-self` run, triggered by the new `auth: creds`
frontmatter. The author skill's prompt explicitly walks the
author through this:

> Your new skill declares `auth: creds`. The build pipeline
> will project `credentials_shim.py` into your skill's
> `scripts/` directory on the next build. Run
> `make build-self` before running your skill's tests, or the
> import will fail with `ModuleNotFoundError`.

The implementation spec adds an AC verifying the author skill's
prompt contains this note. The cost is one explicit step in the
new-skill workflow; the alternative (have the author skill
invoke `make build-self` itself, or ship a stub `credentials_shim.py`
in the template) is rejected because both make the build
pipeline's responsibility opaque to the author and complicate
the source-of-truth model.

### 8. Transport-agnosticism — MCP servers as a future variant

The broker *contract* is transport-agnostic in shape (a broker
takes a credential request from a consuming primitive and either
returns the credential or makes it usable by the primitive
without crossing an LLM-visible boundary). v1 ships two
transports — in-process import for `creds`, adapter-root
subprocess for `sso-cookie`. A future MCP-server transport is
additive evolution, not gated by this RFC:

- A future `creds-mcp` server could expose the same env →
  keychain → dotfile resolution over the MCP protocol. The
  consuming skill's frontmatter would change broker id (`auth:
  creds-mcp`) and the consumer would switch from
  `from .credentials_shim import load_credentials` to an MCP
  tool call.
- A future `sso-cookie-mcp` server could similarly expose the
  SSO broker's interface over MCP — useful for adopters whose
  governance permits MCP servers and prefers persistent broker
  processes over per-call subprocess spawns.

Neither is in scope here. The corporate-governance gates on MCP
servers (stdio: spawns subprocess with creds in scope; remote:
crosses corporate network boundary) are real today.
In-process-shim + adapter-root-subprocess is the floor that
works for the broadest adopter base.

### 9. Migration scope — commitment, not construction

This RFC **commits** to migrating every in-tree consumer of
`agentbundle.credentials` as part of its acceptance. The
construction (per-skill task list, code recipe, PR ordering)
lives in the implementation spec named in § Follow-on artifacts;
this section pins only the policy.

**The commitment.** Six skills and one author-skill body
currently reference `agentbundle.credentials`:

- The four `atlassian` skills: `jira`, `jira-align`,
  `confluence-publisher`, `confluence-crawler` (importers in
  their `scripts/_client.py`).
- The `figma` skill (importer in `scripts/_client.py`).
- The `example-credentialed-skill` worked example in `core`
  (importer in `scripts/cli.py`).
- The `add-credentialed-skill` author skill's own body
  (`packs/core/.apm/skills/add-credentialed-skill/SKILL.md`)
  contains the *teaching example* showing `from
  agentbundle.credentials import load_credentials`. Six
  consumer skills migrate; the seventh site is documentation
  in the author skill's prose and updates in lockstep.

All migrate to the `creds` broker. The atlassian skills move to
`auth: creds` (the PAT path) — adopters with corporate SSO
subsequently switch their deployment's frontmatter to
`auth: sso-cookie` with a registered profile, but that swap is
per-adopter, not in-tree. Figma is cloud SaaS with PAT-only auth;
`sso-cookie` does not apply. The example skill migrates first so
the canonical reference shows the new shape before the others
follow.

**The sequencing rule.** `agentbundle.credentials` and
`agentbundle.creds/` are removed from the `agentbundle` package
in the **last** PR of the migration sequence — so the import
remains available throughout the migration window. The package
release that performs the removal bumps `agentbundle`'s minor
version (`X.(Y+1).0`); intermediate PRs that touch in-tree
consumers do **not** bump the minor. The contract for adopters
is explicit:

> Adopters running `agentbundle X.Y` continue to receive
> bug-fix releases (`X.Y.Z+1`, `X.Y.Z+2`, …) throughout the
> migration window. Pin to `agentbundle <X.(Y+1)` until you
> have migrated. `X.(Y+1)` removes the module; the package
> release notes carry the migration recipe verbatim — adopters
> reading the changelog see the same diff shape the in-tree
> migration used.

**The migration shape per consuming skill** — a single import-line
change, identical across all six consumers:

```python
# before
from agentbundle.credentials import (
    CredentialsMissingError,
    Tier2HardFailError,
    load_credentials,
)

# after — the build pipeline supplies the sibling file
from .credentials_shim import (
    CredentialsMissingError,
    Tier2HardFailError,
    load_credentials,
)
```

Plus a frontmatter addition (`metadata.auth: creds`,
`metadata.namespace: <ns>`, `metadata.keys: [...]`) so
the build pipeline triggers shim projection and the lint scopes
broker-specific checks. Skill body code (`load_credentials("ns",
required_keys=[...])`, attribute access on the returned
`Credentials`, exception handlers) is unchanged.

**What lives in the implementation spec, not here:** per-skill
namespace and required-keys mapping; per-skill construction tests
verifying the shim import resolves and the exception paths
behave; the exact PR ordering; the cleanup-PR removal of
`agentbundle.credentials` and `agentbundle.creds/`. The
implementation spec is
`docs/specs/credential-broker-contract/spec.md` (§ Follow-on
artifacts); it carries one plan task per skill (six tasks), one
explicit task for the `add-credentialed-skill` author-skill
teaching block (the seventh site — its own task so it cannot be
silently dropped as a sub-bullet of cleanup), plus the cleanup
task that removes the module and bumps `agentbundle`'s minor
version.

**Version-delta substitution at acceptance.** The pin policy
above uses `X.Y` / `X.(Y+1)` as template literals because this
is a Draft RFC and `agentbundle`'s current version
(`packages/agentbundle/pyproject.toml`) is `0.1.0` — the
concrete delta depends on what version ships immediately before
acceptance. The implementation spec resolves the template
literals to concrete numbers, and the package changelog text
(§ Follow-on artifacts) carries the substituted form before
release.

**Why split commitment from construction.** Co-locating the
per-skill table and the code recipe in the RFC trades governance
clarity for procedural commitment that the implementation spec
already buys. If the broker contract needs an amendment after PR-3
lands but before PR-6, the RFC must be amended *during* its own
implementation rollout — the drift that the "specs are validation
gates" rule (CONVENTIONS § 4) exists to prevent. Keeping the
commitment in this RFC's Boundaries and the construction in the
spec preserves both gates.

### What this RFC does NOT do

Out of scope, named here so reviewers know:

- **Out-of-tree adopter migration**, beyond providing the recipe
  in the package changelog. Adopters with their own credentialed
  skills carry the same shape change as the in-tree six, but
  doing it for them is not this RFC's job.
- **Switching in-tree Atlassian skills to `auth: sso-cookie`.**
  All four migrate to `auth: creds` (the PAT path) in this RFC;
  the SSO path is a frontmatter change adopters make in *their*
  deployment when they want it, not an in-tree default. The repo
  has no corporate-SSO test deployment to validate against.
- **MCP-server transport for any broker.** Subprocess only in v1;
  MCP wrappers are additive (§ 8).
- **Pack bundling / pack-of-packs.** No mechanism in the
  catalogue for `credential-brokers` to depend on `atlassian` or
  `converters`. Downstream adopters compose independently
  installable packs as they like.
- **`sso-pat-mint` broker** for vendors that mint PATs via
  browser automation (GitLab's "Settings → Access Tokens → New").
  Deferred until a concrete consumer; `creds` covers the
  PAT-already-minted case today.
- **DOM-scraping of CSRF/XSRF tokens beyond cookies** (grey-zone
  ServiceNow / some Atlassian write paths). Broker captures
  cookies only in v1.
- **Linux Tier-2 (`libsecret`)** — still deferred per RFC-0006's
  unresolved questions. The dotfile remains the Linux floor for
  both `creds` and `sso-cookie` brokers.
- **CONVENTIONS.md edit.** Lands at acceptance as a follow-on,
  not in this RFC's own PR.
- **Lint code changes.** The broker-conditional rules per § 6
  are specified here but implemented in the follow-up spec.

## Alternatives considered

### A. Do nothing — keep `agentbundle.credentials` as the convention

The current state. Costs:

- Every new credentialed skill is Python-only or carries a hard
  `pip install agentbundle` step adopters in Node/Bash-only
  environments cannot satisfy.
- SSO use cases continue as per-skill duplication (two
  `browser_auth.py` files today, three by end of year, growing
  with each new SSO target).
- The lint conflates the security invariants with the resolver;
  legitimate `gh`-style skills either skip the lint by omitting
  `credentialed: true` or are flagged irrelevantly.

Rejected — the empirical validation case (4) shows the
duplication is already non-trivial, and the SSO mismatch is
structural.

### B. Add a `sso-cookie` broker only; keep `agentbundle.credentials` as the PyPI-shipped loader

Smallest delta. Ships the consolidated SSO broker, leaves the
PyPI-shipped Python-import loader for static-token consumers.
Rejected:

- The PyPI dependency on `agentbundle` (motivation 1) goes
  unresolved for static-token skills, which are the majority of
  credentialed skills.
- Skills carry inconsistent shapes: some import a vendored
  sibling (new), others import a PyPI module (old). Two import
  sources for the same logical resolver multiplies the cognitive
  surface for authors and the schema-walking surface for the
  lint.
- The work to vendor the shim into the catalogue is roughly
  parallel to the work to keep maintaining the PyPI module (the
  per-platform Tier-2 backends are the same code regardless of
  shipping channel); the saving is small and the structural
  coherence is large.

### C. Implement brokers as MCP servers from day one

Stronger interop story. Rejected:

- Corporate governance gates on MCP servers are real and
  documented by adopters (stdio servers spawn subprocesses with
  credentials in scope; remote servers cross the network
  boundary). Both attract security review that in-process
  imports and adapter-root subprocesses do not.
- An MCP server with a `get-credential` tool reproduces exactly
  the wrap-and-leak shape Alternative G rejects: the LLM can
  invoke the MCP tool directly from chat (MCP tools are
  LLM-addressable by design); the cleartext lands in the tool
  response that the LLM reads. The structural guarantee of
  in-process import does not survive the MCP transport.
- A future MCP wrap of either broker remains possible (§ 8)
  without breaking the in-process-import-for-`creds` /
  adapter-root-subprocess-for-`sso-cookie` shape v1 commits to.

### D. Single broker — collapse `env` / `cli` / `creds` / `sso-cookie` to one polymorphic `creds` broker

Simpler surface. Rejected:

- `env` would still need to be an out-clause for zero-dep
  skills; making it implicit ("a skill that declares no
  `auth:` defaults to env") confuses the lint's enforcement
  model (which broker's rules apply?).
- `cli` and `sso-cookie` have meaningfully different
  consumption patterns and different lint shapes (positive
  grep targets differ); merging them would force shared
  metadata to carry both unioned schemas.
- The four-broker split maps onto four real adopter scenarios
  that already exist today; collapsing them is parsimony at
  the cost of clarity.

### E. Skip the `env` broker — require keychain-backed resolution always

Tighter security posture. Rejected:

- The catalogue's adopters include people running in environments
  where neither OS keychain nor a dotfile is welcome (CI, headless
  VMs, agent harnesses that inject secrets via wrapper processes).
  RFC-0006 § 2 Tier 1 documents this exact case; removing the
  floor reintroduces the friction RFC-0006 went to lengths to
  solve.
- `env` is the broker that requires zero catalogue runtime — the
  catalogue contributes only the naming convention and the
  invariant lint. Removing it would force every credentialed
  skill into one of three brokers that all have runtime
  surface, contradicting the portability motivation.

### F. Pack bundling — `credential-brokers` is a meta-pack depending on `atlassian` and `converters`

The framing the user explored mid-design. Rejected:

- Pack-bundling does not exist in the current catalogue model;
  introducing it is its own RFC-scale change.
- Downstream adopters can compose independently installable
  packs already (RFC-0004's per-pack install model). The
  bundling would be a doc-level recommendation at adopter
  scope, not a catalogue mechanism.
- Keeps this RFC focused on the broker contract.

### G. Subprocess broker for `creds` (the original v1 of this RFC)

The first draft of this RFC specified `creds` as a subprocess
broker (`agentbundle-creds get <ns> <key>` printing the cleartext
on stdout, consumer subprocess-captures and uses). Symmetric
with `sso-cookie`'s subprocess shape; language-agnostic at the
consumer side; one transport for both brokers. **Rejected
mid-design** when the review surface caught it:

- The subprocess broker reproduces RFC-0006 § 5 Anti-pattern
  register's wrap-and-leak shape *by example*: "a skill author
  can `subprocess.check_output(['agentbundle', 'creds', 'get',
  ...])` and capture the cleartext into LLM-visible scope." That
  was the failure mode RFC-0006 refused; v1 of this RFC accepted
  it as a regression with prose-only mitigations. The structural
  guarantee RFC-0006 § 1 codified (cleartext only inside the
  primitive's process) degrades to cooperative discipline.
- Subprocess `capture_output=True` returns a `str` one log
  statement away from leakage. A typed `Credentials` object
  (RFC-0006's in-process return) required at least
  `creds.api_token` attribute access; the `str` is unstructured
  bytes any contributor adding `logger.debug(result.stdout)`
  leaks.
- The language-agnostic claim was overstated. No in-tree skill
  is non-Python; the polyglot case is hypothetical. The
  `env` broker already serves polyglot adopters without a
  broker subprocess at all.

The vendored-shim shape (this RFC's accepted approach) restores
RFC-0006's structural guarantee at the cost of Python-only
consumers — which matches the actual catalogue today, not the
hypothetical polyglot future the subprocess shape optimised for.

### H. Ship the brokers as skills inside `<skills-dir>/`

Both `agentbundle-creds` and `sso-broker` could be ordinary skills
at `<skills-dir>/agentbundle-creds/SKILL.md` and
`<skills-dir>/sso-broker/SKILL.md` — discoverable by the adapter,
LLM-auto-loaded, addressable from chat. The path resolution from
a consuming skill would be sibling-relative (one directory up,
one over). **Rejected:**

- A skill at `<skills-dir>/<name>/SKILL.md` is auto-discovered by
  the adapter. The LLM sees it in its tool catalogue at session
  start. `agentbundle-creds` with a `get` verb in its `scripts/`
  becomes one tool-call away from a malicious prompt or a
  confused-deputy slip.
- Even with prose discipline ("do not invoke me directly"),
  exposing the broker as a skill multiplies the attack surface:
  the SKILL.md teaches the LLM the invocation shape; the LLM
  knows the verb names; the cooperative guard is the only thing
  between intent and exfiltration.
- The adapter-root-bins path (`~/.agentbundle/bin/`) is outside
  every adapter's skills directory, has no SKILL.md, and is not
  surfaced in the LLM's auto-discovered tool catalogue. The LLM
  can still Bash-invoke if it knows the path, but the path is
  not visible to the LLM through any auto-discovery channel.

The setup skill (§ 4e) is the deliberate exception: it ships as
a skill *because* its purpose is LLM-cooperative (the LLM tells
the user to invoke it), and its output discipline keeps the
cleartext out of LLM-visible scope.

### I. Ship `credentials_shim` as a PyPI package consumers import

Publish a separate package (`agentbundle-credentials-shim` or
similar) to PyPI; consumers `from agentbundle_credentials_shim
import load_credentials`. Cleaner than build-pipeline projection
(no duplication, no drift gate). **Rejected:**

- Reintroduces the `pip install <something>` step this RFC exists
  to remove. Renaming the PyPI package from `agentbundle` to
  `agentbundle-credentials-shim` does not change the underlying
  friction (enterprise package gating, locked-down corporate
  Python envs, etc.).
- The shim is small and stable; the build-pipeline projection
  cost is bounded (one source-of-truth, drift gate catches
  mismatches). The maintenance burden of a separate PyPI
  package (versioning, release cadence, deprecation cycles)
  outweighs the projection complexity.
- A future PyPI shim is not foreclosed — if the duplication cost
  grows beyond the shim's bounded footprint, splitting it back
  out is a clean follow-on RFC.

### J. Land the `agentbundle.credentials` removal as a follow-up to the new pack

Ship `credential-brokers` first; remove `agentbundle.credentials`
in a later PR after the six in-tree consumers migrate. Rejected:

- Carries the duplication risk: both resolvers exist
  concurrently, skill authors picking between them is
  non-obvious, the lint has to handle both.
- The six in-tree migrations are mechanical (one import-line
  change, applied six times); naming them as a follow-up spec
  rather than co-landing them in this RFC's scope produces a
  stronger rollback story (the prior `agentbundle` minor stays
  on PyPI per Drawbacks) without sacrificing the broker
  contract's coherence.
- The RFC specifies the end state; the implementation spec
  sequences the rollout. Per § 9, `example-credentialed-skill`
  migrates first (canonical reference), then `figma` and the
  four `atlassian` skills, then the package-level removal as
  the last PR — so the import remains available throughout the
  migration window. This is structurally a follow-on at the
  PR level, but the *commitment* to migrate every consumer is
  in this RFC's scope, not a separate decision deferred to a
  future spec author.

## Drawbacks

- **Four broker ids is more surface than one resolver.** Adopters
  learn `env` / `cli` / `creds` / `sso-cookie` and pick correctly.
  The `add-credentialed-skill` author skill mitigates by walking
  authors through the choice; the lint mitigates by refusing
  incoherent combinations (e.g. `auth: sso-cookie` without an
  `sso_profile`). Cost remains real.

- **`creds` broker is Python-only at the consumer side.** The
  vendored shim is a Python module; a hypothetical Node or Bash
  skill cannot import it. Such consumers fall back to the `env`
  broker (which is language-agnostic by construction) and lose
  the keychain integration. No in-tree skill faces this today —
  every existing credentialed primitive is Python — but a future
  polyglot consumer is a real possibility the RFC does not solve
  beyond `env`. Mitigation: an `env`-broker adopter using
  1Password CLI / Vault Agent / direnv gets keychain-equivalent
  security upstream of the env var; the catalogue does not need
  to reinvent it.

- **Build-pipeline complexity grows by two primitive classes.**
  `shared-libs/` and `adapter-root-bins/` are new primitive types
  the build pipeline learns about. `shared-libs/` projection is
  many-to-many (one source file → N consumer skills' `scripts/`);
  `adapter-root-bins/` projection is one-per-adapter at a new
  target location. Both add code paths to `agentbundle build`
  and `make build-check`. The implementation spec carries ACs
  for both projection mechanisms and the drift gate.

- **`shared-libs` duplication is real, even if build-pipeline-
  managed.** Six consuming skills today, each carrying a
  byte-identical copy of `credentials_shim.py` (~150 lines).
  Updates to the shim mean re-projecting into N consumers; the
  drift gate catches mismatches but does not eliminate the
  storage. Mitigation: the shim is small and stable (RFC-0006
  froze its API surface); meaningful churn is rare. The
  alternative (a Python package on PyPI consumers import) was
  rejected as Alternative I because it reintroduces the
  PyPI-install friction this RFC exists to remove.

- **Public Python API removal.** `from agentbundle.credentials
  import load_credentials` is removed. The six in-tree consumers
  migrate within this RFC's scope (§ 9); external consumers of
  the `agentbundle` package break on upgrade. RFC-0006's `0.x`
  semver permits this; the package release notes carry the
  verbatim migration recipe (§ 9) so out-of-tree adopters can
  follow the same diff shape (one-line import change).

- **Playwright dependency at pack scope.** The `sso-broker`
  script declares Playwright as a runtime dep per RFC-0007
  § Runtime dependencies. Adopters who install
  `credential-brokers` but never use SSO never resolve the
  dependency. Adopters who do use SSO accept a one-time
  `pip install playwright; playwright install chromium`.
  Browser auto-install (~150 MB of Chromium) is the expected
  install flow. First-use friction surfaced via the import-guard
  + clear stderr message (§ 4f).

- **Linux Tier-2 deferral inherits.** The `creds` broker on Linux
  still falls through to the dotfile; the `sso-cookie` broker
  similarly stores the cookie jar in a 0600 file under
  `~/.agentbundle/sso-cookies/` on Linux. RFC-0006's deferral
  reasoning (D-Bus session matrix, headless/SSH/WSL/Docker corner
  cases) applies unchanged.

- **First user-scope pack with runtime broker behaviour.**
  `converters` (RFC-0007) was the first user-scope pack, but
  shipped only deterministic file-processing skills.
  `credential-brokers` is the first user-scope pack that holds
  authentication state — cookies in keychain, profiles in
  `~/.agentbundle/sso-profiles/`. The state shape is small and
  RFC-0006 already established `~/.agentbundle/` as the
  user-scope artifact root, but the surface is new. The
  implementation spec's manual-QA matrix needs Windows + macOS
  + Linux rows for each broker.

- **Developer iteration on cross-skill code requires
  `make build-self`.** The vendored shim and the user-scope SSO
  broker live at source paths
  (`packs/credential-brokers/.apm/shared-libs/` and
  `packs/credential-brokers/.apm/adapter-root-bins/`) that
  differ from their runtime locations (consumer skills'
  `scripts/` and `~/.agentbundle/bin/` respectively). A developer
  editing the shim or broker and running a consumer skill's
  tests must `make build-self` first to refresh the projected
  copies. The cost is bounded (projection is a fast copy
  operation) but real for inner-loop work.

  **No runtime override.** Earlier drafts proposed an
  `AGENTBUNDLE_SHIM_DIR` env-var override letting the consumer
  resolve the shim from the source path at test time. **Dropped**
  per Concern 9 — a runtime env-var override is a slippery
  slope: nothing prevents a production adopter from setting it
  to point at a worktree they control, undermining the
  byte-identity guarantee the drift gate provides. The inner-loop
  workflow is documented as "run `make build-self` after editing
  the shim source, before running consumer tests" with no
  runtime escape hatch. The wall-clock cost of `make build-self`
  is small; the safety property of "the shim consumers import is
  exactly the source-of-truth byte-for-byte, verified by the
  drift gate" is worth preserving.

- **First-use Playwright install is manual.** No automated pip
  invocation on the user's behalf (§ 4f). The user (or the agent
  acting on their behalf) sees the install instruction and runs
  it. Acceptable v1 friction; future evolution to an
  explicit-`setup`-verb is left as a follow-on.

- **`sso-cookie` broker is scoped, not universal.** The name
  telegraphs the scope (cookie-based REST after SSO), but the
  first reviewer who reads the RFC summary and assumes "SSO
  broker" means "all SSO" will need to read further. The
  alternative names considered (`sso-rest-cookie`, `atlassian-sso`,
  `cookie-broker`) each had their own drawbacks; the chosen name
  is the least-bad shape. Drawback acknowledged.

- **Author-skill template count grows from two to five.** The
  variants under `add-credentialed-skill/assets/` go from two
  (credentialed-cli, mcp-server per RFC-0006 § Amendments) to
  five (one per broker id). The author-skill copes (it asks "which
  broker?" first), but the maintenance surface grows.

- **In-tree migration breadth — six skills across three packs.**
  Co-landing every consumer of `agentbundle.credentials` in this
  RFC's acceptance scope concentrates the risk: a regression in
  the `creds` broker stops six skills, not one. Mitigations:
  (a) the `example-credentialed-skill` migrates first as the
  canonical reference; (b) the implementation spec carries
  construction tests per skill so each migration is independently
  verifiable; (c) the `agentbundle.credentials` module is removed
  in the **last** PR of the sequence, so the import remains
  available throughout the migration window. The alternative —
  shipping the broker contract first and migrating consumers
  later — was rejected as Alternative J; the duplication risk
  of having two resolvers concurrently is worse than the
  concentration risk of one migration window.

- **One-shot rip of `agentbundle.credentials` is irreversible
  inside the 0.x window.** Once the module is removed, restoring
  it requires a coordinated revert across the broker pack and
  the six migrated skills. RFC-0006's `0.x` semver permits the
  rip but an adopter mid-migration is in a non-trivial recovery
  position. Mitigation: the package release that removes the
  module bumps `agentbundle`'s minor version; the prior minor
  remains on PyPI for adopters who need a rollback. The release
  notes name the exact version delta.

## Prior art

**In repo:**

- [RFC-0001](0001-bundle-distribution-by-adapter-spec.md) +
  [RFC-0002](0002-self-hosting.md) +
  [RFC-0003](0003-spec-and-cli.md) — the pack-catalogue model
  this RFC's portability argument is grounded in.
- [RFC-0004](0004-install-scope-per-pack.md) — the user-scope
  dimension `credential-brokers` consumes; per-pack `[pack.install]`
  declaration; refusal rails.
- [RFC-0005](0005-user-scope-hook-support.md) — `credential-brokers`
  ships no hooks, so the deferral does not constrain it; the
  pattern (a new user-scope-by-nature primitive shape lands
  behind its own RFC) is reused.
- [RFC-0006](0006-skill-secrets-storage.md) — the storage tiers,
  two-layer architecture, Win32 error-code matrix, atomic-write
  discipline, and per-platform Tier-2 backends are preserved
  verbatim in the new broker. The amendment is the resolver's
  *location* and *transport*, not its *semantics*.
- [RFC-0007](0007-user-scope-converter-pack.md) — the precedent
  for a user-scope pack (pack.toml shape, no seeds, no hooks, no
  markers, runtime deps documented per-skill in SKILL.md). The
  new pack follows the same shape.

**External:**

- **`gh` CLI auth model** ([cli/cli](https://github.com/cli/cli)).
  Inspired RFC-0006's three-tier shape; the broker contract here
  inherits that lineage. `gh`'s lesson: silent degradation
  defeats the security posture the user chose. Preserved in the
  broker's tier-announce behaviour.
- **AWS CLI auth model** — credential resolution chain (env →
  shared credentials file → IAM role → SSO cache). The `cli`
  broker formalises the "vendor CLI owns auth" pattern this
  exemplifies.
- **Cookie-jar reuse for SSO-fronted REST** — the broader
  technique of capturing a session cookie via headed browser,
  storing it, and replaying for API calls. The pattern is
  documented for cookie-based REST authentication on Atlassian
  Data Center products (per Atlassian's own developer docs at
  `developer.atlassian.com/server/jira/platform/cookie-based-authentication/`).
  Several open-source implementations of this shape exist; this
  RFC consolidates the variant the team already operates as
  per-skill scripts.
- **OAuth 2.1 + MCP authorization servers** — the industry's
  longer-term direction for credentialed agent access. This RFC
  treats MCP-server transport as additive future work (§ 8); the
  broker contract's transport-agnosticism keeps the door open
  without forcing the dependency today.

## Unresolved questions

- **Will `sso-cookie` regret its scoped name when a second
  cookie-based-REST adopter shows up?** Author's lean: **no.**
  The naming explicitly telegraphs scope, and adopters reaching
  for it for the wrong vendor (GitLab, Salesforce) hit `creds`
  instead — which is what should happen. If a meaningfully
  different SSO broker shape appears (PAT-minting, DOM-scraping),
  it lands as its own broker id; renaming `sso-cookie` later is
  cheap (one frontmatter migration per consuming skill).

- **Is the two-primitive `credential-brokers` pack the right
  grouping, or should it ship as `sso-broker` + `creds-broker`
  (two single-tenant packs)?** Author's lean: **one pack with
  the domain noun.** This matches RFC-0007's `converters`
  precedent — the noun names the domain (`converters` for file
  conversion; `credential-brokers` for credential brokering)
  rather than gesturing at a future-undefined "starter" set.
  An earlier draft used `user-starter`; that framing failed the
  pressure-test (three-times rule: only two primitives confirmed,
  hypothetical third) and was rejected before this draft. Two
  single-tenant packs duplicate the `[pack.install]` boilerplate
  and the user-scope rails enforcement for zero categorical
  gain. The `credential-brokers` name is committed (binding
  per § Follow-on artifacts ADR); a future `oauth-device-flow`
  broker fits the same pack without renaming because OAuth
  device-flow credentials are still credentials.

- **`env` broker invariants are lint-enforced per § 6** — the
  broker-agnostic checks (AC26 a/b/c: "Don't" block, argv ban,
  direct-dotfile-read scan) apply to `auth: env` skills exactly
  as they apply to every credentialed primitive. The schema
  requires `namespace` and `keys` for `auth: env` (matching
  `auth: creds`). The lint additionally AST-walks
  `os.environ[...]` / `os.getenv(...)` for **presence-only**
  enforcement: for each declared `<NAMESPACE>_<KEY>`, at least
  one matching read must exist in `scripts/`. **Exhaustivity
  enforcement** (refusing reads of env vars *outside* the
  declared product) is deferred until a concrete false-positive
  case motivates the tradeoff — diagnostic reads like
  `os.getenv("PATH")` or locale reads like `os.environ["LANG"]`
  are NOT flagged in v1. Reviewer question: is presence-only
  right for v1, or should exhaustivity ship now? Author's lean:
  **presence-only in v1** — exhaustivity is a real false-positive
  surface and the additional safety is small relative to the
  broker-agnostic checks already in force.

- **Does the `creds` shim need a `--scope`-like override for the
  dotfile path?** RFC-0006 specified one user-scope dotfile path
  (`~/.agentbundle/credentials.env`); the shim inherits.
  RFC-0004's per-pack scope dimension does not extend to
  credentials (which are user-scope by nature, not pack-scope).
  Author's lean: **no override; the shim is intrinsically
  user-scope.** Reviewer can challenge if a repo-scope
  credentials use case appears.

- **Should the SSO broker support concurrent profile use within
  one skill invocation?** A future skill that talks to both
  Jira (`acme-atlassian` profile) and an internal ServiceNow
  (`acme-snow` profile) needs to call `get-cookies` twice. The
  broker handles this naturally (each call is independent), but
  the frontmatter shape (one `sso_profile:` per skill) implies
  a single profile per skill. Author's lean: **start with
  single-profile-per-skill; allow `sso_profiles: [...]` if a
  concrete consumer appears.** The lint stays simpler for v1.

## Follow-on artifacts

On acceptance:

- **ADR-NNNN: Credential broker contract.** Records the following
  as binding architectural choices — so future RFCs amend the
  contract rather than re-litigate:
  - Four-broker decision (`env`, `cli`, `creds`, `sso-cookie`).
  - **Two transports, not one.** `creds` is an in-process vendored
    shim (Python module imported by consumers); `sso-cookie` is
    an adapter-root subprocess. Rejection of Alternative G (the
    original subprocess-broker design that mirrored
    `sso-cookie`'s transport for `creds`) preserves RFC-0006's
    structural guarantee against wrap-and-leak — the cleartext
    never crosses a process boundary for static tokens.
  - **Brokers are not skills.** Rejection of Alternative H (broker
    as `<skills-dir>/<name>/`) keeps the SSO broker out of the
    LLM's auto-discovered tool catalogue. The single exception is
    the user-invoked credential-setup skill (§ 4e), whose output
    discipline keeps cleartext out of LLM-visible scope by
    construction.
  - **No PyPI shim package.** Rejection of Alternative I keeps the
    `creds` shim as a build-projected sibling file, not a separate
    pip-installable package.
  - Rejection of alternatives B (keep `agentbundle.credentials`
    + add `sso-cookie` only), D (single polymorphic broker), E
    (drop `env` floor), F (pack bundling), J (defer migration
    to follow-up).
  - Pack naming: `credential-brokers` (the domain noun), not
    `user-starter` (rejected for failing the three-times rule).
  - Two new build-pipeline primitive classes: `shared-libs/`
    (many-to-many projection into consumer skills) and
    `adapter-root-bins/` (single-target projection to
    `~/.agentbundle/bin/`, the catalogue's user-scope artifact
    root per RFC-0006).

- **Spec:** `docs/specs/credential-broker-contract/spec.md` — the
  implementation spec for this RFC. Tracks ACs for the broker
  contract, the `credential-brokers` pack, the two new
  build-pipeline projection classes, and the in-tree migration
  named in § 9 as a single coherent spec (the broker contract
  is the gate the migrations land against, so co-locating ACs
  prevents the gate drifting between the two). Areas covered:
  - **Pack manifest** for `packs/credential-brokers/` (validation
    against RFC-0004's three refusal rails plus the "no
    `.apm/skills/` except the setup skill" rail; integration
    test against a fixture `$HOME`).
  - **`shared-libs/` projection** — many-to-many copy from
    `packs/credential-brokers/.apm/shared-libs/*.py` into every
    consumer skill's `scripts/` directory, gated by
    `metadata.auth: creds`. Byte-equality drift gate per § 6's
    two-command split (`make build-self` projects;
    `make build-check` errors on drift). ACs cover both commands
    against all three drift outcomes (modified / missing /
    orphaned).
  - **`adapter-root-bins/` projection** — single-target copy to
    `~/.agentbundle/bin/`. Contract amendment widens
    `allowed-prefixes.user` for Claude Code and Kiro to include
    `.agentbundle/` (Codex already declares it per RFC-0011).
    Mode bits, path-jail compliance, `allowed-adapters` gating.
  - **`credentials_shim.py` content** — public API surface
    (`Credentials`, `CredentialsMissingError`, `Tier2HardFailError`,
    `load_credentials`); per-platform Tier-2 backends carried
    over from RFC-0006 § 2 byte-equivalent; stdlib-only
    constraints preserved.
  - **`sso-broker.py` subcommand surface** (`register`,
    `get-cookies`, `test`, `refresh`, `list-profiles`, `rm`),
    profile TOML schema, cookie-jar keychain integration with
    Win32 error matrix, Playwright import-guard, first-use
    install-instruction stderr.
  - **Credential-setup skill** (§ 4e) — the one LLM-cooperative
    skill the pack ships; reserved-prefix rejection AC; no
    token-on-stdout AC.
  - **Lint changes** — broker-conditional AST checks per § 6;
    drift check for projected shim copies; substring-trap
    discipline (two traps, not one).
  - **Frontmatter parser updates** (`metadata.auth` recognised
    by `lint-agent-artifacts.py` and `lint-credentialed-skills.sh`;
    schema accepts the four broker ids and the broker-specific
    extras).
  - **`add-credentialed-skill` template variants** per broker id.
  - **In-tree migration of the six consumers** named in § 9:
    `example-credentialed-skill` (first, as canonical reference);
    `figma`; the four `atlassian` skills (`jira`, `jira-align`,
    `confluence-publisher`, `confluence-crawler`). One plan task
    per skill; construction tests per skill verify the import
    resolves and the exception paths behave; no behavioural
    change vs. RFC-0006's loader.
  - **One explicit task for the author-skill teaching code block.**
    `packs/core/.apm/skills/add-credentialed-skill/SKILL.md` contains
    the worked instruction showing `from agentbundle.credentials
    import load_credentials`. The plan carries this as a *separate*
    task (not a sub-bullet of the cleanup task) so it cannot be
    silently dropped, with its own AC verifying the teaching
    example matches the new vendored-shim import shape.
  - **Cleanup task — the last PR.** Removes
    `agentbundle.credentials` and `agentbundle.creds/` from the
    `agentbundle` package; bumps `agentbundle`'s minor version;
    substitutes concrete version numbers into the package
    changelog text for the adopter pin contract (§ 9
    template-literal note).

- **Convention change:** `docs/CONVENTIONS.md` § Credentialed
  skills — updates to name the four brokers, the
  `metadata.auth` field, and the broker-specific lint
  variants. Lands at acceptance.

- **`agentbundle` package release:** minor-version bump with the
  `agentbundle.credentials` and `agentbundle.creds`
  module removal, announced in the package changelog with the
  verbatim migration recipe from § 9 so out-of-tree adopters can
  follow the same diff shape. The prior minor stays on PyPI as
  the rollback target named in Drawbacks.

- **Roadmap entry:** `docs/backlog.md` gains a section for
  `credential-broker-contract` covering the broker pack, the
  six in-tree migrations, and a manual-QA matrix line for each
  broker × OS combination — parallel to RFC-0006's matrix.

- **Guide update:** `docs/guides/how-to/add-a-credentialed-skill.md`
  rewrites the "pick a primitive class" section as "pick a
  broker." Updates land in the same PR as the
  `add-credentialed-skill` template variants.

- **No CHARTER edit.** This RFC operates within the
  charter's existing scope; no mission, principle, or
  scope-line change is implied.

## Errata

This RFC is Accepted: the body above is preserved as the original decision
record. Corrections are appended here, Approver-signed.

- **2026-05-31 (Approver: eugenelim) — § 9's two teaching skills are
  retired; § 5 / § 7's author-skill framing is superseded by the how-to.**
  § 9 ("Migration scope — commitment, not construction") committed two
  *teaching* primitives to `core`: the `example-credentialed-skill` worked
  example and the `add-credentialed-skill` author skill (the latter with the
  four `assets/credentialed-skill-SKILL-<broker>.md` templates from § 5, and
  the build-self walkthrough from § 7). Both are **retired** as structurally
  redundant.

  **Why the original framing was over-built.** The architectural enforcement
  is the lint (`tools/lint-credentialed-skills.sh` → `lint_credentialed_skills.py`)
  plus the frontmatter schema (`tools/lint-agent-artifacts.py`) — *not* the
  skills. The lint walks pack **source** (`packs/*/.apm/skills/*/SKILL.md`)
  and already covers every real credentialed skill: `credential-setup`
  (`credential-brokers`), `jira`, `jira-align`, `confluence-publisher`,
  `confluence-crawler` (`atlassian`), and `figma`. Deleting the fictional
  no-op `example-credentialed-skill` removes **zero** lint coverage. The
  `add-credentialed-skill` SKILL.md was instructional prose that duplicated
  the Diátaxis how-to (`docs/guides/how-to/add-a-credentialed-skill.md`)
  almost verbatim; the four verbatim per-broker `### Security rules
  (non-negotiable)` blocks (§ 5) are consolidated into the how-to's Step 7,
  and the `auth: creds` → `make build-self` step (§ 7) is stated there. The
  example only ran because `make build-self` committed a copy of
  `credential-brokers`' shim into `core`, coupling `core` to the broker pack.

  **What is unchanged.** The four-broker contract, the two transports, the
  brokers-not-skills architecture, the shim, the `credential-brokers` pack,
  and the five real consumer skills are untouched. Only the redundant
  teaching surface is removed.

  **Where this is recorded.** Implementation lives in
  `docs/specs/credential-broker-contract/spec.md` § Changelog (2026-05-31):
  AC27/AC28/AC34 superseded, AC30 takes the canonical-reference designation,
  consumer count six → five.

- **2026-06-12 (Approver: eugenelim) — the five credentialed packs admit
  `copilot` and `cursor`; § 4's three-harness `allowed-adapters` set widens
  to five.** § 4 / § 4d scoped the broker pack's `allowed-adapters` to
  `["claude-code", "kiro-ide", "codex"]` because the `adapter-root-bins/`
  projection writes the SSO broker to `~/.agentbundle/bin/`, and at RFC time
  only those three adapters declared `.agentbundle/` in
  `allowed-prefixes.user` (the RFC itself amended claude-code and kiro to
  add it). The set was a function of that precondition — not of any
  credential-handling property of the adapters.

  **Why the set widens now.** Two adapters shipped since have added
  `.agentbundle/` to their own `allowed-prefixes.user` (for their install
  state): `copilot` (`copilot-full-parity`, contract v0.10) and `cursor`
  (`cursor-full-parity`, contract v0.11). The § 4d precondition therefore
  now holds for both. The user-scope `.agentbundle/{lib,bin}/` delivery rail
  (`install.py` `_deliver_user_scope_floor`) is **adapter-agnostic** — it
  fires for any user-scope install and is fenced only by the target
  adapter's `.agentbundle/` prefix, with no per-adapter allow-list. Verified
  by a real user-scope install of `credential-brokers` via both `cursor` and
  `copilot`: `~/.agentbundle/bin/sso-broker.py` and
  `~/.agentbundle/lib/credbroker/` land, and the `credential-setup` skill
  projects to `.cursor/skills/` / `~/.copilot/skills/`. The four consumer
  packs (`atlassian`, `contracts`, `converters`, `figma`) ship skills only
  (the `creds` shim is build-baked into their `scripts/`) and resolve the
  broker from the canonical `~/.agentbundle/bin/`; they widen in lockstep so
  a `cursor`/`copilot`-only adopter can install both the broker and its
  consumers rather than a half-working consumer with no broker. All five now
  declare `["claude-code", "kiro-ide", "codex", "copilot", "cursor"]`.

  **No contract change.** The prefix precondition is already satisfied by the
  shipped contract (v0.12) — no `allowed-prefixes` amendment, no version
  bump. This erratum records a widening *permitted by* the current contract,
  not a contract change.

  **What is unchanged.** The four-broker contract, the two transports, the
  in-process `creds` shim, the subprocess `sso-cookie` broker at the
  canonical adapter-independent `~/.agentbundle/bin/`, the no-leak guarantees
  (RFC-0006 § 1), and the brokers-not-skills architecture are untouched. Only
  `allowed-adapters` membership widens.

  **Where this is recorded.** Implementation (the five pack.toml edits + the
  two exact-list test-pin updates) lands in
  `docs/specs/credential-broker-contract/spec.md` § Changelog (2026-06-12);
  the cursor opt-in follow-on in `docs/backlog.md` § `cursor-full-parity`
  closes.
