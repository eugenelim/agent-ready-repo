---
title: "Export loop telemetry"
summary: "Resolve this repository's telemetry settings and send its work-loop events to a Collector."
pack: core
kind: how-to
---

# Export loop telemetry

Use the catalogue resolver to build the exact `jsonl-otlp-export` arguments for
the repository you want to observe. A useful request to give your agent is:

> Resolve the loop telemetry invocation for this repository.

## What leaves your machine

Nothing, until you decide otherwise —
nothing is sent until you configure an endpoint.
This page describes a capability you install on purpose, not one that is already
running.

When you do configure an endpoint, here is exactly what goes and where.

- **What is read:** `.loop-run/events.jsonl` at your repository root. Your
  work-loop writes one line to it per phase change. The file is local and
  gitignored.
- **What is sent:** those lines, as
  OTLP logs,
  to the Collector address you configured. One log record per transition.
- **What each record carries:** the transition's timing, which phase it left and
  entered, what a gate decided, and the run's retry budgets. The exact field list
  is `docs/architecture/telemetry.md` § 5.1, and the mapping profile in this pack
  names every field that may be sent.
- **What the allowlist governs:** the fields sent as ordinary attributes. A field
  the engine adds later does not start flowing on its own — the profile has to
  name it first.
- **Four more fields are sent even though the allowlist does not name them**,
  because the profile routes each one to a destination of its own:
  - `at` becomes the record's **timestamp**;
  - `result` becomes its **severity**, and is **left off entirely when it has no
    mapping** — which is the case for the five routing transitions that decide
    nothing;
  - `run_id` and `seq` are sent **as attributes**, alongside the allowlisted
    ones, because together they are the record's identity and a consumer
    deduplicates on them.
- **What is never sent:** any field that is neither routed above nor named by the
  allowlist.
- **What a pack cannot see at all:** your prompts, the model's replies, and token
  counts. A pack never sees the model call, so it has nothing to send.
- **Where it goes:** the Collector you run. Point it at your own infrastructure,
  never at a vendor endpoint directly.

The sender is a separate distribution, `jsonl-otlp-exporter`. If you never
install it, nothing can send, whatever any configuration file says.

## Resolve the invocation

Run this from the repository root after installing `jsonl-otlp-exporter`:

```python
import shlex
from pathlib import Path

from agentbundle.telemetry_layout import resolve

repo_root = Path.cwd()
user_layout = Path.home() / ".agentbundle" / "agentbundle-layout.toml"
resolved = resolve(repo_root, user_layout)

# shlex.quote, not plain printing: these arguments carry values read from two
# TOML files, and a repository path with a space in it would otherwise split
# into two arguments. Quoting also means a value cannot end one command and
# begin another when this line is pasted into a shell.
print("jsonl-otlp-export", shlex.join(resolved.arguments))
```

**Prefer this form.** `resolved.arguments` is already a list, so hand it straight
to `subprocess`: no shell is involved, so no quoting question arises on any
platform.

```python
import subprocess

subprocess.run(["jsonl-otlp-export", *resolved.arguments], check=True)
```

The resolver reads `agentbundle-layout.toml` from the repository root and the
user layout path shown above. It writes nothing and does not run the sender.
Its output has this shape:

```text
jsonl-otlp-export --input <repo>/.loop-run/events.jsonl --root <repo> --config <resolved-layout> --profile <repo>/packs/core/.apm/skills/work-loop/profiles/work-loop.toml --service-name <resolved-name>
```

The printed form is quoted with `shlex.join`, which is **POSIX shell quoting**.
It is safe to paste into `sh`, `bash` or `zsh`. It is **not** safe for Windows
`cmd.exe`, where single quotes do not protect separators and a value such as
`x&whoami&x` would still run. On Windows, or in any script, use the `subprocess`
form above, which builds no shell command at all.

`--config` names one file, and the sender reads only `[telemetry].endpoint` from
it. Every other setting is rendered as its own flag, which is why a value your
repository declares still reaches the sender when the endpoint came from your
user file. A `[telemetry]` setting with no flag is refused rather than ignored,
so a setting that would do nothing tells you instead of failing quietly.
