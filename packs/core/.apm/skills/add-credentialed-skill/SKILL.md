---
name: add-credentialed-skill
description: Use this skill when the user wants to author a new credentialed primitive — a skill that calls an authenticated external API on behalf of the user. Triggers on "add a credentialed skill", "new credentialed primitive", "wire up `<service>` API access". The skill walks the author through picking the broker (env, cli, creds, sso-cookie), copying the matching `assets/credentialed-skill-SKILL-<broker>.md` template, declaring frontmatter and schema, and (for the creds broker) running `make build-self`. Do NOT use for skills that just shell out to an already-credentialed binary the user has on PATH — those are not credentialed primitives. See `docs/specs/credential-broker-contract/spec.md` for the full architecture.
---

# Skill: add-credentialed-skill

A credentialed primitive owns the secret on disk and constructs the API
call inside its own process; the LLM never sees the cleartext token as
a tool argument. This skill walks the author through writing one
end-to-end.

## When this fires

The user is about to write a skill that calls a credentialed external
service (Jira API, GitHub API via PAT, a vendor's REST endpoint with
an API token, a service behind corporate SSO, etc.). The *architecture
rule* — skills do not hold credentials; credentialed primitives do —
is the load-bearing distinction; if you're tempted to shell-quote a
secret into an `argparse` arg, stop and load this skill first.

## The procedure

1. **Pick the broker** by asking the author one question: *"How does
   the credential get into the primitive's process?"* Four answers,
   keyed on `metadata.auth`:
   - **`env`** — the credential is a plain environment variable
     (`<NAMESPACE>_<KEY>` after uppercasing both). The catalogue
     contributes lint and naming convention; no runtime resolver.
   - **`cli`** — the primitive shells out to a vendor-authenticated
     binary (`gh`, `aws`, `kubectl`, `gcloud`). The vendor CLI owns
     the credential.
   - **`creds`** — the credential is a static token resolved via the
     three-tier model (env → OS keychain → 0600 dotfile floor). The
     build pipeline projects `credentials_shim.py` plus per-platform
     Tier-2 backends into your `scripts/` directory.
   - **`sso-cookie`** — the credential is a session cookie acquired
     through a headed-browser SSO flow. Your primitive
     subprocess-invokes `~/.agentbundle/bin/sso-broker.py`.

2. **Pick the primitive class** (orthogonal to broker):
   - **`credentialed-cli`** — your primitive is a Python CLI you invoke
     from skill bodies (`subprocess.run([...])`). The argv ban applies
     (no `--token` / `--api-token` / `--bearer` / `--pat` / `--password`
     flags) regardless of broker.
   - **`mcp-server`** — your primitive is a long-lived MCP server the
     user wires into their MCP host configuration. Header-naming flags
     (`--bearer-header`, `--auth-header`, `--header-prefix`) are
     allowed because they name *which* header to consult, not the
     value.

3. **Copy the matching template.** The four broker templates live
   under `assets/`:
   - `assets/credentialed-skill-SKILL-env.md`
   - `assets/credentialed-skill-SKILL-cli.md`
   - `assets/credentialed-skill-SKILL-creds.md`
   - `assets/credentialed-skill-SKILL-sso-cookie.md`

   Open the one matching your broker, copy everything below the
   horizontal rule *verbatim* into your new skill's `SKILL.md` body,
   and substitute the placeholders (`<your-skill-name>`, `<service>`,
   `<namespace>`, `<KEY>`, `<sso-profile>`, `<vendor-cli>`). The
   `### Security rules (non-negotiable)` block stays verbatim — the
   lint greps for the per-broker substrings.

4. **Declare the schema** at `<skill-dir>/references/creds-schema.toml`
   (only `auth: creds` and `auth: env` need this):

   ```toml
   [namespace]
   name = "<namespace>"

   [[namespace.keys]]
   name = "<KEY>"
   label = "<service> API token"
   secret = true
   ```

5. **Declare the frontmatter** on your new skill's `SKILL.md`. The
   shape varies by broker — the matching template names the exact
   fields. Common shape:

   ```yaml
   ---
   name: <your-skill-name>
   description: <what triggers it>
   metadata:
     credentialed: true
     primitive-class: credentialed-cli   # or mcp-server
     auth: <broker-id>                   # env / cli / creds / sso-cookie
     # broker-specific extras (namespace / keys / sso_profile / …)
   ---
   ```

6. **For `auth: creds`: run `make build-self`** before running any
   test that imports `credentials_shim`. The build pipeline projects
   `credentials_shim.py`, `_keychain_macos.py`, and
   `_credman_windows.py` into your skill's `scripts/` directory only
   after it sees `auth: creds` in your frontmatter; without that step
   the import fails with `ModuleNotFoundError`.

7. **For `auth: creds`: invoke the `credential-setup` skill yourself
   once** to write the token to the right tier (keyring on
   Darwin/Windows; dotfile on Linux). For `auth: env`: export
   `<NAMESPACE>_<KEY>` in your shell. For `auth: cli`: run the
   vendor's auth flow (`gh auth login`, `aws configure`, …). For
   `auth: sso-cookie`: register the profile via
   `python3 ~/.agentbundle/bin/sso-broker.py register <profile> ...`.

8. **Run `conventions-check`** to verify your skill passes the
   broker-agnostic rules (Don't-block presence; no argv-borne
   credential flags; no direct dotfile reads from skill scripts) plus
   the broker-specific rule (`from .credentials_shim` import for
   `auth: creds`; per-`<NAMESPACE>_<KEY>` env read for `auth: env`;
   subprocess-invoke of the canonical broker path for
   `auth: sso-cookie`).

## What the lint enforces

`tools/lint-credentialed-skills.sh` (wired into the `conventions-check`
slash command) reports findings on:

- **Broker-agnostic:** `### Security rules (non-negotiable)` heading
  absent, or the per-broker substrings missing inside that section;
  argv-borne credential flags in `scripts/**/*.py` (argparse-only
  scope — see AGENTS.md); any `scripts/**/*.py` line literally
  embedding `.agentbundle/credentials.env` without the opt-out marker
  `# credentialed-primitive: reads-creds-directly` on the same line.
- **`auth: creds`:** AST-walk for `ImportFrom(module="credentials_shim")`
  in `scripts/**/*.py`.
- **`auth: env`:** for each declared `<NAMESPACE>_<KEY>`, AST-walk
  asserts at least one matching `os.environ[...]` / `os.getenv(...)`
  read in `scripts/**/*.py`. Reads of non-declared env vars (e.g.
  `os.getenv("PATH")`) are NOT flagged.
- **`auth: sso-cookie`:** AST-walk for a `subprocess.run` whose first
  argument resolves to a path ending in `.agentbundle/bin/sso-broker.py`
  via `Path.home()`. Absolute paths and inline Playwright invocations
  are flagged.
- **`auth: cli`:** no positive-grep enforcement; broker-agnostic
  checks only.

The architectural rule is wider than the lint can enforce; PR review
catches what the lint can't.

## Adapter portability — `[pack.install] allowed-adapters`

If your pack's content is portable across IDEs (skills-only, no
IDE-specific agent shape), list every adapter in `allowed-adapters`
that supports user scope. The credentialed packs in this catalogue
(`atlassian`, `figma`) list `claude-code`, `kiro`, and `codex`
because their skills are pure text + Python and travel cleanly
across all three adapters' user-scope skill directories. Bumping
`[pack.adapter-contract] version` to `"0.7"` opts the pack into the
broker contract; the credential-brokers pack itself ships at
contract v0.7 with `allowed-adapters = ["claude-code", "kiro", "codex"]`.

## Reference

- Spec: `docs/specs/credential-broker-contract/spec.md`
- RFC: `docs/rfc/0013-credential-broker-contract.md`
- Worked example: the `example-credentialed-skill` skill
