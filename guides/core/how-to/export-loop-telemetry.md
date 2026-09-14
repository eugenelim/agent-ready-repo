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
- **What is never sent:** anything not on that profile's allowlist. A field the
  engine adds later does not start flowing on its own — the profile has to name
  it first.
- **What a pack cannot see at all:** your prompts, the model's replies, and token
  counts. A pack never sees the model call, so it has nothing to send.
- **Where it goes:** the Collector you run. Point it at your own infrastructure,
  never at a vendor endpoint directly.

The sender is a separate distribution, `jsonl-otlp-exporter`. If you never
install it, nothing can send, whatever any configuration file says.

## Resolve the invocation

Run this from the repository root after installing `jsonl-otlp-exporter`:

```python
from pathlib import Path

from agentbundle.telemetry_layout import resolve

repo_root = Path.cwd()
user_layout = Path.home() / ".agentbundle" / "agentbundle-layout.toml"
resolved = resolve(repo_root, user_layout)

print("jsonl-otlp-export", *resolved.arguments)
```

The resolver reads `agentbundle-layout.toml` from the repository root and the
user layout path shown above. It writes nothing and does not run the sender.
Its output has this shape:

```text
jsonl-otlp-export --input <repo>/.loop-run/events.jsonl --root <repo> --config <resolved-layout> --profile <repo>/packs/core/.apm/skills/work-loop/profiles/work-loop.toml --service-name <resolved-name>
```

Copy the printed command and run it to start the separately installed sender.

`--config` names one file, and the sender reads only `[telemetry].endpoint` from
it. Every other setting is rendered as its own flag, which is why a value your
repository declares still reaches the sender when the endpoint came from your
user file. A `[telemetry]` setting with no flag is refused rather than ignored,
so a setting that would do nothing tells you instead of failing quietly.
