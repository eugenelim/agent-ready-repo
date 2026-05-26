# Template: credentialed-skill `auth: sso-cookie`

For primitives whose credential is a session cookie acquired through
a headed-browser SSO flow. The `credential-brokers` pack ships
`sso-broker.py` at `~/.agentbundle/bin/`; your skill subprocess-invokes
it with `get-cookies <profile>` and receives the path to a serialised
cookie jar (never the values). Copy everything below the horizontal
rule verbatim into your skill's `SKILL.md` body. Replace
`<your-skill-name>`, `<service>`, `<sso-profile>` placeholders; leave
the rest unchanged. The lint (`tools/lint-credentialed-skills.sh`)
checks for the verbatim phrases inside the `### Security rules
(non-negotiable)` section and verifies your `scripts/`
subprocess-invokes the broker at the canonical `Path.home() /
".agentbundle" / "bin" / "sso-broker.py"` location.

Frontmatter shape:

```yaml
---
name: <your-skill-name>
description: <what triggers it>
metadata:
  credentialed: true
  primitive-class: credentialed-cli
  auth: sso-cookie
  sso_profile: <sso-profile>
---
```

Register the profile once before running your skill:

```
python3 ~/.agentbundle/bin/sso-broker.py register <sso-profile> \
    --login-url <login-url> --success-url-pattern <pattern>
```

---

# Skill: <your-skill-name>

<one-line description of what the skill helps the user accomplish>

## How this skill works

This skill calls the `<service>` API via the credentialed primitive
at `scripts/cli.py`. The primitive subprocess-invokes the SSO broker
at `~/.agentbundle/bin/sso-broker.py` with `get-cookies <sso-profile>`
and receives the path to a serialised cookie jar in the OS keychain
(or 0600 dotfile floor on Linux). The broker performs the headed
browser flow on first use and on `test`-detected expiry; the cookie
*values* never reach the LLM.

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

## Usage

The primitive's Python entry point invokes the broker via subprocess:

```python
import subprocess
import sys
from pathlib import Path

broker = Path.home() / ".agentbundle" / "bin" / "sso-broker.py"
result = subprocess.run(
    [sys.executable, str(broker), "get-cookies", "<sso-profile>"],
    capture_output=True,
    text=True,
    env={**os.environ},
)
cookie_jar_path = result.stdout.strip()
```

The primitive loads the jar internally, constructs the authenticated
request, and constructs the API call without surfacing the cookie
values to the LLM.
