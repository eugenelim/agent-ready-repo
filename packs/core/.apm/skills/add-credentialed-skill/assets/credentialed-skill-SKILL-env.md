# Template: credentialed-skill `auth: env`

For primitives whose credential is a plain environment variable
(`<NAMESPACE>_<KEY>` after uppercasing both). The catalogue contributes
naming convention and lint only — there is no runtime resolver. Copy
everything below the horizontal rule verbatim into your skill's
`SKILL.md` body. Replace `<your-skill-name>`, `<service>`,
`<namespace>`, `<KEY>` placeholders; leave the rest unchanged. The lint
(`tools/lint-credentialed-skills.sh`) checks for the verbatim phrases
inside the `### Security rules (non-negotiable)` section and verifies
each declared `<NAMESPACE>_<KEY>` is read at least once in `scripts/`.

Frontmatter shape:

```yaml
---
name: <your-skill-name>
description: <what triggers it>
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: env
  namespace: <namespace>
  keys: ["<KEY>"]
---
```

---

# Skill: <your-skill-name>

<one-line description of what the skill helps the user accomplish>

## How this skill works

This skill calls the `<service>` API via the credentialed primitive
at `scripts/cli.py`. The primitive reads `<NAMESPACE>_<KEY>` from the
process environment and constructs the API call inside its own
process. The LLM never sees the cleartext value as a tool argument.

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

## Usage

Invoke the primitive via `subprocess.run([sys.executable,
"scripts/cli.py", "<verb>", ...])`. The primitive resolves the env
var inside its own process and constructs the API call without
surfacing the value to the LLM.
