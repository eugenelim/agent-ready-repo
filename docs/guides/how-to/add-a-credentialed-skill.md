# How to add a credentialed skill

This is a one-page walk-through for authoring a credentialed primitive — a skill that calls an authenticated external API on behalf of the user. The architecture rule ([RFC-0006 § 1](../../rfc/0006-skill-secrets-storage.md#1-two-layer-architecture-skills-dont-hold-credentials)) is *skills don't hold credentials*; a Python CLI under the skill's `scripts/` directory owns the secret on disk and constructs the API call inside its own process. The LLM never sees the token as a tool argument.

The worked example at [`packs/core/.apm/skills/example-credentialed-skill/`](../../../packs/core/.apm/skills/example-credentialed-skill/) is the runnable reference you copy from; this guide is the procedure that gets you there.

> **When to use this** — your skill calls an external service that takes API tokens, Bearer auth, or similar (Jira, GitHub PAT, an internal vendor REST endpoint). If your skill only shells out to a binary the user has already authenticated on PATH (`gh`, `git`, `kubectl`), it is *not* a credentialed primitive — leave it as a plain skill.

## Before you start

You need:

- The target service's authentication shape (token, bearer header, key+secret pair). Note which fields are secret and which aren't (`API_TOKEN` is; `BASE_URL` usually isn't).
- A namespace name — a short kebab/snake-case identifier the credential store will use (`jira`, `github`, `acme_corp`). This becomes the env-var prefix and the keychain account label.
- `agentbundle` installed (`pip install -e packages/agentbundle/` in this repo, or your distribution's equivalent).

## Step 1 — Pick the primitive class

Two classes, picked once per skill:

- **`credentialed-cli`** — your primitive is a Python CLI invoked from the skill body via `subprocess.run([sys.executable, "scripts/cli.py", ...])`. The argv ban applies (no `--token` / `--api-token` / `--bearer` / `--pat` / `--password` flags); the three-tier storage convention applies.
- **`mcp-server`** — your primitive is a long-lived MCP server the user wires into their MCP host configuration. Header-naming flags (`--bearer-header`, `--auth-header`, `--header-prefix`) are allowed; the storage convention does not apply because the server holds no on-disk credential state.

The rest of this guide assumes **`credentialed-cli`** (the common case). For `mcp-server`, the SKILL.md frontmatter and template variant differ but the lint, the loader API, and the architecture rule are identical.

## Step 2 — Scaffold the skill directory

```
your-skill-name/
├── SKILL.md
├── scripts/
│   └── cli.py
└── references/
    └── creds-schema.toml
```

Place this under your pack's `.apm/skills/` directory (e.g. `packs/<your-pack>/.apm/skills/your-skill-name/`).

## Step 3 — Declare the schema

The schema lives at `<skill-dir>/references/creds-schema.toml` and declares the credential namespace plus its required keys:

```toml
[namespace]
name = "your-namespace"

[[namespace.keys]]
name = "API_TOKEN"
label = "<service> API token"
secret = true

[[namespace.keys]]
name = "BASE_URL"
label = "<service> instance base URL"
secret = false
```

`secret = true` keys are prompted via `getpass.getpass` (no echo); `secret = false` keys are prompted via `input()`. The full schema format and the canonical path are pinned in [spec § AC24](../../specs/skill-secrets/spec.md#acceptance-criteria) and [§ AC24b](../../specs/skill-secrets/spec.md#acceptance-criteria).

## Step 4 — Import the loader in `scripts/cli.py`

```python
from agent_ready.credentials import (
    CredentialsMissingError,
    Tier2HardFailError,
    load_credentials,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="your-skill-name")
    parser.add_argument("verb", choices=("call", "check"))
    args = parser.parse_args(argv)

    try:
        creds = load_credentials(
            "your-namespace",
            required_keys=["API_TOKEN", "BASE_URL"],
        )
    except CredentialsMissingError as exc:
        sys.stderr.write(f"{exc}\n")
        sys.stderr.write(
            "run `agentbundle creds setup your-namespace` to set the missing keys\n"
        )
        return 2
    except Tier2HardFailError as exc:
        # Adopters: copy this catch verbatim. macOS Keychain unlock
        # failures and Windows DPAPI errors surface here; never let
        # the traceback escape, since its repr can include keyring
        # error strings that narrow attacker reconnaissance.
        sys.stderr.write(f"keychain unavailable: {exc}\n")
        return 3

    # `creds.API_TOKEN` and `creds.BASE_URL` are attribute-accessible
    # strings. Never print them, log them, or echo them.
    ...
```

`agent_ready.credentials` is the **only** public entry point — do not reach into `agentbundle.creds.loader` directly. The loader resolves each key through Tier 1 (env var) → Tier 2 (OS keyring) → Tier 3 (dotfile), first-hit-wins per key.

## Step 5 — Embed the "Don't" block in `SKILL.md`

Copy the `### Variant: credentialed-cli` block from [`add-credentialed-skill/assets/credentialed-skill-SKILL.md`](../../../packs/core/.apm/skills/add-credentialed-skill/assets/credentialed-skill-SKILL.md) *verbatim* into your `SKILL.md` body. The lint (`tools/lint-credentialed-skills.sh`) pins the three RFC-0006 § 4 anchor phrases:

- `**Never** read that file, print it, or echo the token`
- `**Never** put the token on the command line`
- `do not run it for them`

A skill missing the heading or any of the three phrases ships as a lint finding.

## Step 6 — Declare the frontmatter

Per the [agentskills.io specification](https://agentskills.io/specification), `credentialed` and `primitive-class` are project-specific fields and live under the spec's `metadata:` escape hatch rather than at top level:

```yaml
---
name: your-skill-name
description: <one-line description; what triggers the skill>
metadata:
  credentialed: true
  primitive-class: credentialed-cli
---
```

Both `metadata.credentialed: true` and `metadata.primitive-class: credentialed-cli` are required for the lint to scope its checks to your skill. Without `metadata.credentialed: true`, your skill is treated as a non-credentialed skill and the loader / argv / dotfile checks don't fire — the architecture rule depends on the flag being present.

## Step 7 — Run `setup` and `check`

Once everything is in place:

```bash
agentbundle creds setup your-namespace
```

The CLI reads your `creds-schema.toml`, prompts for each required key (secret keys via `getpass`; non-secret via `input`), and writes to the highest-available tier:

- On macOS / Windows: keyring (Tier 2). Stderr announces `wrote to keyring (<backend>)`.
- On Linux: dotfile (Tier 3). Stderr announces `wrote to dotfile (Linux — Tier 2 deferred to v2 RFC)`.

If you need to force the dotfile path on a Tier-2-capable host (corporate environment without keychain access, say), pass `--allow-insecure-fallback`.

Then verify:

```bash
agentbundle creds check your-namespace
```

Exits 0 if every required key resolves, 2 if any is missing, 3 on other errors (Tier-2 hard fail, schema parse error). Pair with `agentbundle creds where your-namespace` to see *which tier* each key resolved at — useful when debugging precedence.

## Step 8 — Run the lint

```bash
python3 tools/lint-agent-artifacts.py     # frontmatter schema
bash tools/lint-credentialed-skills.sh    # credentialed-skill rules
```

The first lint accepts the nested `metadata.credentialed: true` and `metadata.primitive-class: credentialed-cli` keys (T9; agentskills.io-spec-compliant top-level allow-list). The second walks every credentialed skill and reports findings on:

- Missing `### Security rules (non-negotiable)` heading or any of the three RFC-0006 § 4 anchor phrases.
- Any `argparse.ArgumentParser.add_argument` call under `scripts/**/*.py` whose normalised flag name matches the banned set (`token`, `api_token`, `api_key`, `bearer`, `pat`, `password`).
- Any line under `scripts/**/*.py` containing `.agent-ready/credentials.env` without the opt-out comment `# credentialed-primitive: reads-creds-directly` on the same line.

Both lints exit 0 against the worked example; aim for the same.

## Common pitfalls

- **Printing `creds.API_TOKEN` inside a debug `print(...)`.** The token reaches stdout where any caller can capture it. Use `len(creds.API_TOKEN)` only if you must prove resolution, and ideally don't even disclose the length (token length is a small side-channel).
- **Reading the dotfile directly from a skill body** (`open("~/.agent-ready/credentials.env")`). The lint catches the literal substring; obfuscated reads bypass the lint but still defeat the architecture rule.
- **Adding a `--token` flag "just for local testing".** The argv ban applies in every environment; the `agentbundle creds setup --allow-insecure-fallback` flow is the supported escape hatch.
- **Skipping the `Tier2HardFailError` catch.** When the macOS Keychain is locked or the Windows DPAPI key derivation fails, an uncaught traceback exposes loader internals. Adopters who copy the worked example inherit the safe handling; if you write your primitive from scratch, copy the catch arm too.

## Reference

- Spec: [`docs/specs/skill-secrets/spec.md`](../../specs/skill-secrets/spec.md)
- RFC: [`docs/rfc/0006-skill-secrets-storage.md`](../../rfc/0006-skill-secrets-storage.md)
- Author skill: [`packs/core/.apm/skills/add-credentialed-skill/`](../../../packs/core/.apm/skills/add-credentialed-skill/)
- Worked example: [`packs/core/.apm/skills/example-credentialed-skill/`](../../../packs/core/.apm/skills/example-credentialed-skill/)
