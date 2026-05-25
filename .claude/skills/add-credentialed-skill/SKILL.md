---
name: add-credentialed-skill
description: Use this skill when the user wants to author a new credentialed primitive — a skill that calls an authenticated external API on behalf of the user. Triggers on "add a credentialed skill", "new credentialed primitive", "wire up `<service>` API access". The skill walks the author through picking the primitive class (credentialed-cli vs. mcp-server), copying the matching `### Variant:` from `assets/credentialed-skill-SKILL.md`, declaring the schema, and importing the loader. Do NOT use for skills that just shell out to an already-credentialed binary the user has on PATH — those are not credentialed primitives. See `docs/specs/skill-secrets/spec.md` for the full architecture.
---

# Skill: add-credentialed-skill

A credentialed primitive owns the secret on disk and constructs the API
call inside its own process; the LLM never sees the cleartext token as
a tool argument. This skill walks the author through writing one
end-to-end.

## When this fires

The user is about to write a skill that calls a credentialed external
service (Jira API, GitHub API via PAT, a vendor's REST endpoint with
an API token, a service that takes Bearer auth, etc.). The
*architecture rule* — skills do not hold credentials; credentialed
primitives do — is the load-bearing distinction; if you're tempted to
shell-quote a secret into an `argparse` arg, stop and load this skill
first.

## The procedure

1. **Pick the primitive class.** Two options:
   - **`credentialed-cli`** — your primitive is a Python CLI you invoke
     from skill bodies (`subprocess.run([...])`). The argv ban applies
     (no `--token` / `--api-token` / `--bearer` / `--pat` / `--password`
     flags); the storage convention (Tier 1 → 2 → 3) applies.
   - **`mcp-server`** — your primitive is a long-lived MCP server the
     user wires into their MCP host configuration. Header-naming flags
     (`--bearer-header`, `--auth-header`, `--header-prefix`) are
     allowed; the storage convention does **not** apply because the
     server holds no on-disk credential state.

2. **Copy the matching variant from the template.** The template is
   at `assets/credentialed-skill-SKILL.md` relative to this skill.
   Open it, find the `### Variant: <your-class>` heading, copy
   everything under it (including the `### Security rules
   (non-negotiable)` heading and the three-bullet "Don't" block)
   *verbatim* into your new skill's `SKILL.md` body. Substitute the
   primitive name and namespace placeholders.

3. **Declare the schema** at `<skill-dir>/references/creds-schema.toml`
   per spec § AC24 (`docs/specs/skill-secrets/spec.md`):

   ```toml
   [namespace]
   name = "<your-namespace>"

   [[namespace.keys]]
   name = "API_TOKEN"
   label = "<service> API token"
   secret = true

   [[namespace.keys]]
   name = "BASE_URL"
   label = "<service> instance base URL"
   secret = false
   ```

4. **Import the loader** in your primitive's Python entry point:

   ```python
   from agent_ready.credentials import load_credentials

   creds = load_credentials("<namespace>", required_keys=["API_TOKEN"])
   token = creds.API_TOKEN  # never printed, never echoed
   ```

5. **Declare the frontmatter** on your new skill's `SKILL.md`. Per
   the [agentskills.io specification](https://agentskills.io/specification),
   `credentialed` and `primitive-class` are project-specific data
   and live under the spec's `metadata:` escape hatch — not at top
   level:

   ```yaml
   ---
   name: <your-skill-name>
   description: <what triggers it>
   metadata:
     credentialed: true
     primitive-class: credentialed-cli   # or mcp-server
   ---
   ```

6. **Run `agentbundle creds setup <namespace>`** yourself once to
   write the token to the right tier (keyring on Darwin/Windows;
   dotfile on Linux). Then run `agentbundle creds check <namespace>`
   to confirm resolution.

7. **Run `conventions-check`** to verify your skill passes the three
   credentialed-skill rules (Don't-block presence; no argv-borne
   credential flags; no direct dotfile reads from skill scripts).

## What the lint enforces

`tools/lint-credentialed-skills.sh` (wired into the `conventions-check`
slash command) reports findings on:

- `### Security rules (non-negotiable)` heading absent, or the three
  RFC-0006 § 4 substrings missing inside that section.
- Any `argparse.ArgumentParser.add_argument` call in `scripts/**/*.py`
  whose first positional collapses to a banned name after AC27
  normalisation. The walker recognises every shape that reduces to a
  literal string at parse time:
  - Direct `Constant(str)` — `"--token"`.
  - `BinOp(op=Add)` chain of literal strings — `"--" + "token"`.
  - `JoinedStr` (f-string) with literal-only `FormattedValue` parts —
    `f"--{'token'}"`.
  - `Starred(Tuple)` argument spread of a literal tuple/list —
    `add_argument(*("--token",))`.
  - `Subscript` constant indexing into a literal tuple/list —
    `("--token",)[0]`.
- **Argparse-only scope.** The lint walks `argparse.ArgumentParser.add_argument`
  calls; it does NOT see `click.option(...)`, `typer.Option(...)`,
  decorator-style flag declarations, name-via-variable lookups, or
  flag names assembled from runtime sources (env reads, function
  return values). If your credentialed-CLI primitive uses `click` or
  `typer`, the lint reports zero findings and PR review is the only
  enforcement. Prefer `argparse` for credentialed-CLI primitives so
  the lint can do its job; if you reach for `click` or `typer`
  anyway, name the choice in the PR description so reviewers know to
  spot-check the flag set by hand.
- Any `scripts/**/*.py` line containing `.agent-ready/credentials.env`
  without the opt-out marker `# credentialed-primitive: reads-creds-directly`
  on the same line.

The architectural rule is wider than the lint can enforce; PR review
catches what the lint can't.

## Reference

- Spec: `docs/specs/skill-secrets/spec.md` (this skill is canonical for AC28)
- RFC: `docs/rfc/0006-skill-secrets-storage.md` § 4 (the "Don't" block source)
- Worked example: `packs/core/.apm/skills/example-credentialed-skill/`
  (ships in T12; until then, this skill's template is the reference)
