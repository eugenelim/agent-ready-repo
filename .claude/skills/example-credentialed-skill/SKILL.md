---
name: example-credentialed-skill
description: Reference skill -- do NOT auto-load. Authoring a new credentialed primitive belongs in `add-credentialed-skill`; this directory ships only as a runnable worked example for adopters who explicitly ask to *see* one. The skill carries a no-op `scripts/cli.py` calling a fictional `example` API via the build-projected `credentials_shim` sibling, the canonical `references/creds-schema.toml` declaring `API_TOKEN` (secret) and `BASE_URL` (non-secret sibling), and the verbatim `### Security rules (non-negotiable)` block the credentialed-CLI lint pins. Read it; do not invoke it from production code.
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: creds
  namespace: example
  keys: ["API_TOKEN"]
---

# Skill: example-credentialed-skill

A no-op credentialed primitive bound to a fictional `example` API.
The skill exists to demonstrate the four moving parts a credentialed
primitive must wire up:

- `SKILL.md` frontmatter under `metadata:`
  (`credentialed: true`, `primitive-class: credentialed-cli`).
- The verbatim security-rules block below (the lint pins the heading
  and the three RFC-0006 § 4 anchor phrases).
- `scripts/cli.py` calling `load_credentials` via the build-projected
  `from .credentials_shim import …` (the broker ships
  `credentials_shim.py` alongside the skill's own `scripts/`).
- `references/creds-schema.toml` declaring the namespace's keys.

## How this skill works

This skill calls the `example` API via the credentialed primitive
at `scripts/cli.py`. The primitive owns the token; the skill body
never sees it.

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

## Usage

Invoke the primitive via `subprocess.run([sys.executable,
"scripts/cli.py", "<verb>", ...])`. The primitive resolves
credentials inside its own process and constructs the API call
without surfacing the token to the LLM.

## What to change when you copy this

When using this skill as your starting point for a real credentialed
primitive, three things are scaffolding you replace and three things
are load-bearing pattern you leave alone.

**Replace:**

- The namespace (`example` throughout `cli.py`, `references/creds-schema.toml`,
  and the SKILL.md body) with your service's namespace.
- The schema keys (`API_TOKEN`, `BASE_URL`) with your service's keys —
  match the casing your downstream API uses for env-var prefixing.
- The no-op `would call example API at ...` print in `cli.py` with
  your real API call. Keep the `urllib.parse.urlparse` validation;
  silent garbage-URL calls are the regression this guards.

**Leave alone:**

- The imports from `.credentials_shim`. The `credential-brokers` pack
  projects `credentials_shim.py` (plus its Tier-2 backends) into your
  skill's `scripts/` when the build pipeline sees `auth: creds` in
  your frontmatter — run `make build-self` before tests.
- The `metadata:` block carrying `credentialed: true` and
  `primitive-class: credentialed-cli`. The lint and the architecture
  rule both depend on these flags; the agentskills.io spec keeps
  project-specific fields nested under `metadata:` rather than at top
  level.
- The `### Security rules (non-negotiable)` block. The lint pins the
  three phrases verbatim; the architecture rule depends on the
  reminder being present.

## What this skill demonstrates

- **Frontmatter declarations.** Under `metadata:`,
  `credentialed: true` opts the skill into the credentialed-skill
  lint; `primitive-class: credentialed-cli` opts into the argv-ban
  check at AC26(b).
- **Verbatim "Don't" block.** The three bullets under `### Security
  rules (non-negotiable)` are pinned by the lint
  (`tools/lint-credentialed-skills.sh`) — the broker-agnostic
  Don't-block check refuses any deviation as a lint finding.
- **`load_credentials` import.** `scripts/cli.py` imports from
  `.credentials_shim` — the sibling shim file the build pipeline
  projects from `packs/credential-brokers/.apm/shared-libs/` into
  every consumer skill's `scripts/`. This is the surface every
  credentialed-skill author should write against.
- **Tier-resolved API call shape.** The primitive prints
  `would call example API with token=*** at <base_url>` to stdout;
  the token bytes never leave the function-local variable.

## Reference

- Spec: `docs/specs/credential-broker-contract/spec.md` (§ AC28 pins this skill's shape)
- Author skill: the `add-credentialed-skill` skill
- RFC: `docs/rfc/0006-skill-secrets-storage.md`
