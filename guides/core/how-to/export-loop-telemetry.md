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
- **The log is best-effort, so read it as a sample and not as a ledger.** A phase
  change that cannot be written down still happens: the work-loop prints a
  warning to its error output and carries on rather than failing the transition.
  Once that warning has scrolled past, the only trace is a line that is not
  there. Do not raise an alert on a missing record, and do not read a gap as
  proof that a phase was skipped.
- **What is sent:** those lines, as
  OTLP logs,
  to the Collector address you configured. One log record per transition.
- **What each record carries — the whole list, not a summary.** Fourteen fields:

  | Field | In plain words |
  | --- | --- |
  | `spec` | **the path of the spec being worked on**, such as `docs/specs/my-feature`. This is a name you chose, and it leaves your machine. |
  | `run_id`, `seq` | which run this is, and where in it — together they let a receiver drop duplicates |
  | `from`, `to`, `event` | the phase it left, the phase it entered, and what moved it |
  | `at`, `phase_started_at`, `phase_s` | when the transition happened, when the phase began, how many seconds it lasted |
  | `result` | what a gate decided — `success`, `failure`, or nothing at all |
  | `awaiting_input` | whether the run has stopped to wait for a person |
  | `waived` | whether someone passed an override flag on this transition |
  | `budgets` | how many retries the run has used, and its limits |
  | `schema` | which version of this record shape it is |

  No message body is sent — the record has a set of named fields and nothing
  else.
Three words are used above and below, so here is what each means.

- A **Collector** is the OpenTelemetry receiver *you* run. It is the address you
  configure, and nothing here talks to a vendor directly.
- The **profile** is a small file this pack ships that says where each field
  goes. You do not write it.
- Its **allowlist** is the fixed list of fields the profile permits to be sent.

- **What the allowlist governs:** the fields sent as ordinary labels on the
  record. A field the engine adds later does not start flowing on its own — the
  profile has to name it first.
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
- **What this page cannot promise.** It describes what the sender puts on the
  wire. It says nothing about what your Collector then does — how long it keeps
  the records, who can read them, or where it forwards them. Those are its
  settings, not this one's, and they are worth checking before you turn this on.

The sender is a separate distribution, `jsonl-otlp-exporter`. If you never
install it, nothing can send, whatever any configuration file says.

## Turn it on

Two steps, and the first is the consent. Until you write an endpoint, nothing can
be sent no matter what else is installed.

**1. Name your Collector.** Create `agentbundle-layout.toml` at your repository
root:

```toml
[telemetry]
endpoint = "http://127.0.0.1:4318"
```

That address is your own Collector. Use the IPv4 loopback form rather than
`localhost` if you are running one in a container locally — `localhost` can
resolve to IPv6 first and be refused.

You may also set `service_name`, which becomes the name your backend files these
logs under. If you leave it out it defaults to `work-loop`.

This file is a team decision: a value here wins over the same setting in your
personal `~/.agentbundle/agentbundle-layout.toml`, because sending data off the
machine is not a personal preference. A setting the repository file leaves out
falls through to yours.

**2. Install the sender.** `jsonl-otlp-exporter` is a separate distribution. If
you never install it, nothing can send, whatever this file says.

There is no second switch for record contents, because there are none: the
records carry the named fields listed above and no message body.

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

That run sends what is in the file and exits. It measures the file once, when it
opens it, and stops at that many bytes — so a transition your work-loop appends
while the run is in flight, or any time after it, is not sent. This is deliberate:
against a work-loop appending faster than the sender drains, a run with no such
bound would never reach the end and never exit.

So a single run is a snapshot, not a feed. To keep sending as the loop runs, add
`--follow`, which keeps reading appended lines instead of stopping at the size it
first saw, and bound it with `--for <seconds>` so it ends on its own. A
successful one-shot run means every line present when it started was sent. It
does not mean export is running.

**That is the form to use.** If you would rather read the command than run it,
print it — but quote it, because these arguments carry values read from two TOML
files. This block stands on its own:

```python
import shlex
from pathlib import Path

from agentbundle.telemetry_layout import resolve

resolved = resolve(Path.cwd(), Path.home() / ".agentbundle")
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
