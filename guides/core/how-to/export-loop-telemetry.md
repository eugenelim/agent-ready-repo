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
- **One thing rides outside the records.** Each request carries a `resource`
  block naming the service the logs belong to — `service.name`. Its value is
  whatever you set for `service_name`, or, if you set nothing, the profile
  filename with its extension removed — `work-loop` for the profile this pack
  ships. It is the one string in the payload you choose yourself, so do not put
  anything in it you would not send.
- **What is never sent:** any field that is neither routed above, named by the
  allowlist, nor the `service.name` just described.
- **What a pack cannot see at all:** your prompts, the model's replies, and token
  counts. A pack never sees the model call, so it has nothing to send.
- **Where it goes:** the Collector you run. Point it at your own infrastructure,
  never at a vendor endpoint directly.

The sender is a separate distribution, `jsonl-otlp-exporter`. If you never
install it, nothing can send, whatever any configuration file says.

## Resolve the invocation

Run this from the repository root after installing `jsonl-otlp-exporter`. The
resolver reads `agentbundle-layout.toml` from the repository root and from your
user layout directory. It writes nothing and does not run the sender.

```python
import subprocess
from pathlib import Path

from agentbundle.telemetry_layout import resolve

repo_root = Path.cwd()
user_root = Path.home() / ".agentbundle"
# Both arguments are directories, not files. The resolver derives the
# `agentbundle-layout.toml` filename itself in each scope, so the caller
# cannot point it at some other file.
resolved = resolve(repo_root, user_root)

# `resolved.arguments` is already a list, so hand it straight to subprocess.
# No shell is involved, so no quoting question arises on any platform.
subprocess.run(["jsonl-otlp-export", *resolved.arguments], check=True)
```

**That is the form to use.** If you would rather read the command than run it,
print it — but quote it, because these arguments carry values read from two TOML
files:

```python
import shlex

print("jsonl-otlp-export", shlex.join(resolved.arguments))
```

which produces:

```text
jsonl-otlp-export --input <repo>/.loop-run/events.jsonl --root <repo> --config <resolved-layout> --profile <repo>/packs/core/.apm/skills/work-loop/profiles/work-loop.toml --service-name <resolved-name>
```

`shlex.join` is **POSIX shell quoting**. That printed line is safe to paste into
`sh`, `bash` or `zsh`. It is **not** safe for Windows `cmd.exe`, where single
quotes do not protect separators and a value such as `x&whoami&x` would still
run. On Windows, and in any script, use the `subprocess` form above.

`--config` names one file, and the sender reads only `[telemetry].endpoint` from
it. Every other setting is rendered as its own flag, which is why a value your
repository declares still reaches the sender when the endpoint came from your
user file. A `[telemetry]` setting with no flag is refused rather than ignored,
so a setting that would do nothing tells you instead of failing quietly.
