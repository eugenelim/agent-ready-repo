# Template: credentialed-skill `auth: cli`

For primitives that shell out to a vendor-authenticated binary
(`gh`, `aws`, `kubectl`, `gcloud`, …). The vendor's CLI owns the
credential; this catalogue contributes lint and invariants only.
Copy everything below the horizontal rule verbatim into your skill's
`SKILL.md` body. Replace `<your-skill-name>`, `<service>`,
`<vendor-cli>` placeholders; leave the rest unchanged. The lint
(`tools/lint-credentialed-skills.sh`) checks for the verbatim phrases
inside the `### Security rules (non-negotiable)` section.

Frontmatter shape:

```yaml
---
name: <your-skill-name>
description: <what triggers it>
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: cli
---
```

---

# Skill: <your-skill-name>

<one-line description of what the skill helps the user accomplish>

## How this skill works

This skill calls the `<service>` API by invoking the vendor CLI
`<vendor-cli>` as a subprocess. The vendor CLI's own auth store
(e.g. `~/.config/<vendor-cli>/`) owns the credential; this skill
never reads or writes it.

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

## Usage

Invoke the vendor CLI via `subprocess.run(["<vendor-cli>", ...])`.
The vendor CLI resolves the credential inside its own process and
constructs the API call without surfacing the token to the LLM.
