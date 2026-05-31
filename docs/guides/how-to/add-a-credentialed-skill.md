# How to add a credentialed skill

This is a one-page walk-through for authoring a credentialed primitive — a skill that calls an authenticated external API on behalf of the user. The architecture rule ([RFC-0006 § 1](../../rfc/0006-skill-secrets-storage.md#1-two-layer-architecture-skills-dont-hold-credentials), preserved verbatim by [RFC-0013](../../rfc/0013-credential-broker-contract.md)) is *skills don't hold credentials*; a Python CLI under the skill's `scripts/` directory owns the secret on disk and constructs the API call inside its own process. The LLM never sees the token as a tool argument.

For a runnable, shipped reference, read a real consumer — [`packs/atlassian/.apm/skills/jira/`](../../../packs/atlassian/.apm/skills/jira/) is a live `auth: creds` credentialed-CLI whose `scripts/_client.py` resolves a PAT via the projected `credentials_shim`; this guide is the procedure that gets you to your own.

> **When to use this** — your skill calls an external service that takes API tokens, Bearer auth, or session cookies via corporate SSO. If your skill only shells out to a binary the user has already authenticated on PATH (`gh`, `git`, `kubectl`) and the vendor binary owns the credential end-to-end, the `auth: cli` broker fits; everything else picks a different broker below.

## Before you start

You need:

- The target service's authentication shape — static API token, vendor CLI, or corporate-SSO session cookie. The broker you pick depends on this.
- A namespace name — a short kebab/snake-case identifier (`jira`, `github`, `acme_corp`). For static tokens this becomes the env-var prefix and the keychain account label.
- The `credential-brokers` user-scope pack installed (`agentbundle install --pack credential-brokers --scope user`), if you're using the `creds` or `sso-cookie` broker.

## Step 1 — Pick a broker

`metadata.auth` names the broker that resolves the credential. Four ids, picked once per skill:

- **`env`** — the credential is a plain environment variable (`<NAMESPACE>_<KEY>`). Catalogue contributes naming convention and lint; no runtime resolver. Pick this for CI runners, ephemeral containers, and adopters whose threat model permits process env.
- **`cli`** — the primitive shells out to a vendor-authenticated binary (`gh`, `aws`, `kubectl`, `gcloud`). Vendor CLI owns the credential. Pick this when the user has already authenticated the vendor binary on their PATH.
- **`creds`** — static token resolved via the three-tier model (env → OS keychain → 0600 dotfile floor). The `credential-brokers` pack projects `credentials_shim.py` plus per-platform Tier-2 backends into your skill's `scripts/` directory on the next `make build-self`. Pick this for static API tokens / PATs.
- **`sso-cookie`** — session cookie acquired via a headed-browser SSO flow. Your skill subprocess-invokes `~/.agentbundle/bin/sso-broker.py get-cookies <profile>`. Pick this for corporate-SSO endpoints (e.g. enterprise Jira / Confluence behind Okta or AzureAD).

The rest of this guide picks `creds` as the worked example because it's the most common case. The verbatim per-broker `### Security rules (non-negotiable)` block you embed in your `SKILL.md` is given inline in [Step 7](#step-7--embed-the-security-rules-block-in-skillmd), one per broker; copy the one matching your choice.

## Step 2 — Pick a primitive class (orthogonal to broker)

- **`credentialed-cli`** — your primitive is a Python CLI invoked from the skill body via `subprocess.run([sys.executable, "scripts/cli.py", ...])`. The argv ban applies (no `--token` / `--api-token` / `--bearer` / `--pat` / `--password` flags) regardless of broker.
- **`mcp-server`** — your primitive is a long-lived MCP server the user wires into their MCP host configuration. Header-naming flags (`--bearer-header`, `--auth-header`, `--header-prefix`) are allowed; the storage convention does not apply because the server holds no on-disk credential state.

The rest of this guide assumes **`credentialed-cli`** (the common case).

## Step 3 — Scaffold the skill directory

```
your-skill-name/
├── SKILL.md
├── scripts/
│   └── cli.py
└── references/
    └── creds-schema.toml          # only for auth: creds / auth: env
```

Place this under your pack's `.apm/skills/` directory (e.g. `packs/<your-pack>/.apm/skills/your-skill-name/`).

## Step 4 — Declare the frontmatter

The frontmatter shape varies by broker. For `auth: creds`:

```yaml
---
name: your-skill-name
description: <one-line description; what triggers the skill>
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: creds
  namespace: your-namespace
  keys: ["API_TOKEN"]
---
```

For `auth: env`: same shape, `auth: env`. For `auth: sso-cookie`: `auth: sso-cookie` plus `sso_profile: <profile>` (no namespace/keys). For `auth: cli`: just `auth: cli` (no namespace/keys/profile).

`tools/lint-agent-artifacts.py` refuses unknown `auth:` values; `metadata.credentialed: true` requires `metadata.auth`.

## Step 5 — Declare the schema (`auth: creds` and `auth: env` only)

The schema lives at `<skill-dir>/references/creds-schema.toml`:

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

`secret = true` keys are prompted via `getpass.getpass` (no echo); `secret = false` keys are prompted via `input()`. `auth: cli` and `auth: sso-cookie` skip this step entirely.

## Step 6 — Import the broker in `scripts/cli.py`

For **`auth: creds`** — the build pipeline projects `credentials_shim.py` plus per-platform Tier-2 backends into your `scripts/` on the next `make build-self`. Import as a sibling:

```python
from .credentials_shim import (
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
            "run the `credential-setup` skill to set the missing keys\n"
        )
        return 2
    except Tier2HardFailError as exc:
        sys.stderr.write(f"keychain unavailable: {exc}\n")
        return 3

    # `creds.API_TOKEN` and `creds.BASE_URL` are attribute-accessible
    # strings. Never print them, log them, or echo them.
    ...
```

The shim is stdlib-only; no PyPI dependency. The architectural rule from RFC-0006 is preserved — cleartext stays inside your interpreter's process boundary.

For **`auth: env`** — just `os.environ["<NAMESPACE>_<KEY>"]`. The lint asserts at least one read per declared key.

For **`auth: cli`** — `subprocess.run(["<vendor-cli>", ...], env={**os.environ})`. The vendor CLI owns the credential.

For **`auth: sso-cookie`** — subprocess-invoke the canonical broker path:

```python
import subprocess, sys
from pathlib import Path

broker = Path.home() / ".agentbundle" / "bin" / "sso-broker.py"
result = subprocess.run(
    [sys.executable, str(broker), "get-cookies", "your-profile"],
    capture_output=True, text=True, env={**os.environ},
)
cookie_jar_path = result.stdout.strip()
```

The broker emits the *path* to a serialised cookie jar; load it inside your primitive and construct the authenticated request without surfacing cookie values to the LLM.

## Step 7 — Embed the Security-rules block in `SKILL.md`

Every credentialed skill carries a `### Security rules (non-negotiable)` block in its `SKILL.md` body. Copy the block matching your broker *verbatim* — the lint (`tools/lint-credentialed-skills.sh`) pins the heading and the broker-specific phrases, so a skill missing either ships as a lint finding. Substitute the placeholders (`<namespace>`, `<KEY>`, `<NAMESPACE>_<KEY>`, `<vendor-cli>`, `<sso-profile>`) for your service; leave the rest byte-for-byte.

**`auth: creds`:**

```markdown
### Security rules (non-negotiable)

- Secrets live only in `~/.agentbundle/credentials.env`
  (mode 0600 on POSIX; DACL-restricted on Windows), the OS keyring,
  or process environment variables.
  **Never** read that file, print it, or echo the token.
- **Never** put the token on the command line. The primitive
  refuses flags like `--token` / `--api-token` / `--bearer` /
  `--pat` / `--password` and exits — do not work around it.
- If `check` exits with the "missing credentials" code, tell the
  user to run the `credential-setup` skill themselves. It's
  interactive — do not run it for them.
```

**`auth: env`:**

```markdown
### Security rules (non-negotiable)

- Secrets live only in the process environment. **Never** print, log, or
  echo the value of `<NAMESPACE>_<KEY>`.
- **Never** put the credential on the command line. The primitive
  refuses flags like `--token` / `--api-token` / `--bearer` /
  `--pat` / `--password` and exits — do not work around it.
- If the env var is missing, tell the user to export
  `<NAMESPACE>_<KEY>` in their shell rc (or the equivalent for their
  process manager) and re-launch the session. Do not write the value
  anywhere yourself.
```

**`auth: cli`:**

```markdown
### Security rules (non-negotiable)

- Secrets live only in the vendor CLI's auth store. **Never** read
  that store, print it, or echo the token.
- **Never** put the token on the command line. The primitive
  refuses flags like `--token` / `--api-token` / `--bearer` /
  `--pat` / `--password` and exits — do not work around it.
- If the vendor CLI exits with an authentication error, tell the
  user to run the vendor's auth flow themselves (e.g.
  `<vendor-cli> auth login`). It's interactive — do not run it for
  them.
```

**`auth: sso-cookie`:**

```markdown
### Security rules (non-negotiable)

- Secrets live only in cookie jar in OS keychain (mode 0600 on POSIX;
  DACL-restricted on Windows). **Never** read the jar file directly,
  print its contents, or echo cookie values.
- **Never** put a session cookie on the command line. The broker
  refuses flags like `--token` / `--api-token` / `--bearer` /
  `--pat` / `--password` and emits only a *path* on stdout — do not
  parse the jar yourself.
- If the broker exits with the "re-auth required" code (2), tell the
  user the SSO session has expired and the next `get-cookies` will
  open a browser. It's interactive — do not run any setup helper for
  them.
```

## Step 8 — Run `make build-self` (`auth: creds` only)

```bash
make build-self
```

The build pipeline reads your `auth: creds` frontmatter and projects `credentials_shim.py`, `_keychain_macos.py`, and `_credman_windows.py` into your `scripts/` directory. Without this step the sibling import fails with `ModuleNotFoundError`. `make build-check` errors on three drift outcomes (modified / missing / orphaned projected copies); `make build-self` is the idempotent projector that resolves all three.

## Step 9 — Set up the credential

Once everything is in place, populate the credential for your namespace:

- **`auth: creds`** — invoke the `credential-setup` skill (ships with the `credential-brokers` pack). It reads your `creds-schema.toml`, prompts for each required key (secret keys via `getpass`; non-secret via `input`), and writes to the highest-available tier (keyring on Darwin/Windows; dotfile on Linux with `--allow-insecure-fallback`).
- **`auth: env`** — export `<NAMESPACE>_<KEY>` in your shell rc.
- **`auth: cli`** — run the vendor's auth flow (`gh auth login`, `aws configure`, …).
- **`auth: sso-cookie`** — register the SSO profile:

  ```bash
  python3 ~/.agentbundle/bin/sso-broker.py register your-profile \
      --login-url <login-url> --success-url-pattern <pattern>
  ```

  The first `get-cookies` invocation opens a headed Chromium window and saves the cookie jar to the OS keychain (or 0600 file on Linux).

## Step 10 — Run the lint

```bash
python3 tools/lint-agent-artifacts.py     # frontmatter schema
bash tools/lint-credentialed-skills.sh    # credentialed-skill rules
```

`lint-agent-artifacts.py` validates the nested `metadata.credentialed`, `metadata.primitive-class`, and `metadata.auth` keys. `lint-credentialed-skills.sh` walks every credentialed skill and reports broker-agnostic findings (Don't-block presence; argv-ban flags; plaintext dotfile reads without opt-out) plus broker-specific findings:

- `auth: creds` — refuse if `scripts/` does not import `from .credentials_shim`.
- `auth: env` — refuse if any declared `<NAMESPACE>_<KEY>` is never read in `scripts/`.
- `auth: sso-cookie` — refuse if `scripts/` does not subprocess-invoke the canonical broker path; refuse hard-coded absolute paths; refuse inline Playwright.
- `auth: cli` — no positive-grep enforcement; broker-agnostic checks only.

Both lints exit 0 against the worked example; aim for the same.

## Common pitfalls

- **Printing `creds.API_TOKEN` inside a debug `print(...)`.** The token reaches stdout where any caller can capture it. Use `len(creds.API_TOKEN)` only if you must prove resolution, and ideally don't even disclose the length.
- **Skipping `make build-self` after adding `auth: creds`.** The sibling import fails with `ModuleNotFoundError` because the build pipeline hasn't projected `credentials_shim.py` yet. `make build-check` catches this in CI.
- **Hard-coding the SSO broker path** (`subprocess.run(["/Users/me/.agentbundle/bin/sso-broker.py", ...])`). Absolute paths break across user accounts; resolve via `Path.home() / ".agentbundle" / "bin" / "sso-broker.py"` only.
- **Adding a `--token` flag "just for local testing".** The argv ban applies in every environment and every broker; the `credential-setup` skill is the supported escape hatch for the `creds` broker.

## Reference

- Spec: [`docs/specs/credential-broker-contract/spec.md`](../../specs/credential-broker-contract/spec.md)
- RFC: [`docs/rfc/0013-credential-broker-contract.md`](../../rfc/0013-credential-broker-contract.md)
- ADR: [`docs/adr/0003-credential-broker-contract.md`](../../adr/0003-credential-broker-contract.md)
- Reference consumer (runnable, shipped): [`packs/atlassian/.apm/skills/jira/`](../../../packs/atlassian/.apm/skills/jira/) — a live `auth: creds` credentialed CLI
- Explanation: [`docs/guides/explanation/credentialed-skills.md`](../explanation/credentialed-skills.md)
