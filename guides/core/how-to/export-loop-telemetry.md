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
