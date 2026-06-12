# agentbundle changelog

All notable changes to the `agentbundle` Python package.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
the package targets pre-1.0 semver as documented in `docs/CONVENTIONS.md`
— a minor bump on a 0.x release MAY be breaking.

## [0.3.0] — 2026-06-12

### Added

- **Cursor full-parity distribution adapter** (RFC-0026) — projects all
  primitives for both install scopes via the single-writer
  `.cursor/` model.
- **Gemini CLI full-parity distribution adapter** (RFC-0027) — keeps and
  maps tools, projects a tier model map, supports the
  `gemini-command-toml` mode, and bridges `AGENTS.md` through the
  single-writer `.gemini/settings.json`.
- **`--dry-run` for `install` and `upgrade`** — preview the projection
  without writing any files.
- **Upgrade surfaces Tier-2 companion-drops** — `upgrade` now reports the
  `.upstream` companion files that an adopter must reconcile by hand.
- **credbroker install-time user-scope delivery rail** — the build
  pipeline vendors `credbroker` to `.agentbundle/lib` (drift-gated) and
  consumer bootstraps append the `~/.agentbundle/lib` floor at lowest
  precedence (new `user_libs` module).

### Changed

- **Copilot adapter projects skills as first-class `SKILL.md`** and
  corrects the web-tool documentation (adapter contract v0.12).
- **Codex adapter projects agent model and tool config** into the
  generated agent TOML.
- **Pack admittance** — credentialed packs admit the `copilot` and
  `cursor` adapters (RFC-0013 erratum); `research` and `architect` opt
  into the `cursor` adapter.

### Removed

- **Retired the shared-libs shim projection.** Credentialed skills now
  `import credbroker` from the user-scope lib floor instead of a
  build-projected shim.

## [0.2.0] — 2026-05-26

### Removed (breaking)

- `agentbundle.credentials` — the public loader module (`load_credentials`,
  `Credentials`, `CredentialsMissingError`, `Tier2HardFailError`,
  `parse_env_file`, `EnvParseError`).
- `agentbundle.creds` — the entire subpackage (`loader`, `exceptions`,
  `_keychain_macos`, `_credman_windows`), including the schema parser
  `_parse_schema` and the `CredsSchema` / `KeyDef` dataclasses.
- `agentbundle creds` CLI subcommand and its four verbs (`setup`,
  `check`, `where`, `rm`).

### Migration recipe (RFC-0013 § 9)

Out-of-tree credentialed skills that previously imported the loader
from `agentbundle.credentials` must change four things to migrate to
0.2.0. None of the four are optional; missing one leaves the import
unresolvable.

**1. Add four frontmatter declarations** to the skill's `SKILL.md`
(nested under the `metadata:` escape hatch):

```yaml
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: creds                       # selects the build-projected shim broker
  namespace: <your-namespace>       # matches your creds-schema.toml
  keys: ["<KEY>"]                   # the secret keys this skill resolves
```

The build pipeline reads `auth: creds` to decide which skills receive
the projected shim. Without that line the projection doesn't fire.

**2. Change the import line** in each script that resolves
credentials:

```python
# Before (0.1.x)
from agentbundle.credentials import (
    CredentialsMissingError,
    Tier2HardFailError,
    load_credentials,
)

# After (0.2.0)
from .credentials_shim import (
    CredentialsMissingError,
    Tier2HardFailError,
    load_credentials,
)
```

**3. Run `make build-self`** in the catalogue's clone (or invoke
`agentbundle install --pack credential-brokers --scope user .` if
you install via the CLI). This materialises the three shim files —
`credentials_shim.py`, `_keychain_macos.py`, `_credman_windows.py`
— into your skill's `scripts/` directory. Without this step the
relative import resolves to nothing and you get
`ModuleNotFoundError`.

**4. Replace `agentbundle creds setup <namespace>` invocations** in
docs and error messages with the `credential-setup` skill — shipped
by the `credential-brokers` pack at user scope. Authors invoke it
from their agent's skill loader instead of from the shell. There is
no longer an `agentbundle creds` CLI verb.

Verification: invoke the consumer skill's own `check` verb (or
equivalent low-stakes call). The shim walks Tier 1 → 2 → 3 the same
way the prior loader did and surfaces the same exceptions; no
behavioural delta.

### Adopter pin policy

Pin to `agentbundle < 0.2` in your dependency manifest until you have
completed the migration above. The pre-0.2 minor (`0.1.0`) is the
intended rollback target; that release ships from the `agentbundle-v0.1.0`
git tag and is published from the same release workflow this PR
amends. Adopters who cannot migrate immediately should stay on
`agentbundle < 0.2` until they have shipped the four-step recipe.

If no `agentbundle-v0.1.0` tag exists on the upstream remote at the
time you read this changelog, the rollback target has not yet been
published — open a release issue against the catalogue requesting
one before bumping any production pin.

### Why this is breaking inside the 0.x window

Per RFC-0013 § *Drawbacks* — the migration removes a public surface
that one or more out-of-tree consumers may depend on. The deprecation
window inside 0.x is the prior minor (0.1.0) staying available on
PyPI; the migration recipe above is mechanical (one import-line
change per consumer); and the new shim is byte-equivalent (per
spec § AC6) to the prior loader's behaviour. No behavioural change.

## [0.1.0] — pre-0.2.0

The `agentbundle` build / install / adapt CLI and the
`agentbundle.credentials` public loader surface. See `docs/CHARTER.md`
and `docs/specs/skill-secrets/spec.md` for the historical scope.
