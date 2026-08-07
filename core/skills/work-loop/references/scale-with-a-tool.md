# Scale with a tool, not turns — the resumable-tracking playbook

Loaded on demand from `work-loop` EXECUTE's *Scale with a tool, not turns*
subsection. Read it when a single task spans many similar items and is larger
than one context window comfortably holds: applying one change across N files,
extracting or transforming a large set, auditing every module against a rule.

The failure this prevents is concrete. Grinding through the items
conversationally — read item, edit item, read next item — fills the window with
the items themselves. Somewhere short of the last item the context turns over,
you lose the thread of which items are done, and the task stalls *looking*
finished while items 40–N were never touched. No amount of care in the per-item
edit fixes this; the problem is the loop's shape, not the edits.

The fix is to stop holding the work-list in your head and put it in a file. Three
moves:

1. **Enumerate.** Write a small script that lists the work items — `git ls-files
   '*.py'`, a glob, a query, a directory walk — and emits them as the rows of a
   tracking file. Enumeration is mechanical; do it once, in code, not by reading
   directories turn after turn.
2. **Track.** Each item gets a row with explicit per-item state — `pending`,
   `done`, `failed` — in a resumable file (see schema below). The tracking file,
   not the transcript, is the source of truth for what remains.
3. **Iterate idempotently.** Process each `pending` item, then flip its row to
   `done` (or `failed` with a reason). A re-run reads the file, skips everything
   already `done`, and picks up where it left off. **This idempotency is what
   guarantees 100% completion** — the loop can be interrupted, the context can
   turn over, the session can restart, and the next pass resumes exactly where
   the last stopped. Completion is "no `pending` rows left," a fact you read from
   the file, not a feeling.

The whole move converts *"this is too big for my context"* into *"this is
mechanical and resumable."* Those are very different problems: the first has no
good answer, the second is just a loop over a file.

## The tracking file

Two shapes work; pick by whether the per-item result carries data.

**`progress.jsonl` — one JSON object per line.** Append-friendly, survives
partial writes (a torn last line is one lost item, not a corrupt file), trivially
greppable. The default for anything machine-driven:

```jsonl
{"item": "packages/api/handlers.py", "status": "done", "note": "3 callsites updated"}
{"item": "packages/api/models.py", "status": "pending"}
{"item": "packages/web/client.py", "status": "failed", "note": "ambiguous import — needs a human"}
```

Minimum viable schema: an **item key** (stable, unique — a path, an id) and a
**status** in `{pending, done, failed}`. Add a `note` for the failed-item reason
or a one-line result; add whatever per-item output the downstream step needs
(a diff hash, an extracted value). Resist a wider schema than the task uses —
the file is scaffolding, not a database.

**A markdown checklist** — when a human will skim progress or the items are
coarse:

```markdown
- [x] packages/api/handlers.py — 3 callsites updated
- [ ] packages/api/models.py
- [!] packages/web/client.py — ambiguous import, needs a human
```

`[x]` done, `[ ]` pending, `[!]` (or a `FAILED:` prefix) for an item that needs
attention. Less robust to interruption than JSONL — a half-written line is
ambiguous — so prefer it for smaller or human-facing runs.

Either way: **the file lives on disk, not in the window**, and it is the thing
you re-read to answer "what's left." Treat it as scratch (gitignore it) unless
the audit result is itself a deliverable.

## Idempotency and resumability — the load-bearing properties

These are not optional polish; they are the reason the technique works.

- **Read-skip-process.** Every pass starts by reading the tracking file and
  skipping rows already `done`. A row flips to `done` *only after* its item's
  work is verified complete (the edit landed, the test passed) — never
  speculatively before. If the process dies between "did the work" and "wrote
  `done`," the item is re-done on resume; that re-do must be safe, which is why
  the per-item action should itself be idempotent (an edit that's a no-op when
  already applied, an upsert rather than an append).
- **Write after each item, not at the end.** Flush the status the moment an item
  finishes. Batching writes to the end of the run throws away the resumability
  the file exists to provide — a crash loses the whole batch.
- **`failed` is a first-class terminal state, not a retry-forever.** An item that
  can't be processed mechanically (genuine ambiguity, a judgment call, a
  pre-existing breakage) gets marked `failed` with a reason and the loop moves
  on. Completion is then "zero `pending`," with `failed` rows surfaced to a human
  as the explicit residue — far better than a loop that wedges on item 12 and
  never reaches 13–N. Don't auto-retry a `failed` item silently; that's how
  unattended loops burn money.
- **Completion is a file fact.** "Done" is `grep -c pending progress.jsonl`
  returning 0, not your sense that you've been at it a while. Report the tally —
  N done, M failed — from the file.

## When the per-item step needs judgment — shell out to the agent

If processing an item is purely mechanical (rename a symbol, rewrite an import),
the script does it directly and you never see the items. But when each item needs
a judgment call the script can't make — *does this docstring still describe what
the function does?*, *is this the right boundary to extract?* — keep the
enumeration-and-tracking skeleton and let the **script shell out to the agent
once per item**, feeding it that item and recording the agent's verdict in the
tracking file.

This is the same separation the loop uses elsewhere: a mechanical harness governs
*which* items run and *whether all of them did*; the agent supplies *judgment* on
one item at a time, with a fresh, small context each time. The tracking file
still owns completion — the per-item agent call is just how a `pending` row
becomes `done`. Some agents expose a native per-item or fresh-session facility for
exactly this; the [Unattended loops](../SKILL.md#unattended-afk-loops) section
covers when a fully unattended variant is appropriate (mechanical completion
criterion, reliable verification, a prior in-session pass). The technique here is
the *in-session* form: you're driving, the tool just keeps the list straight.

A worked shape — a script that walks files, calls the agent per file, records the
verdict:

```python
import json, subprocess
from pathlib import Path

progress = Path("progress.jsonl")
seen = set()                             # done + failed — both are terminal, don't redo
if progress.exists():
    for line in progress.read_text().splitlines():
        try:                             # tolerate a torn last line from a crashed write
            seen.add(json.loads(line)["item"])
        except json.JSONDecodeError:
            pass

for path in sorted(p for p in Path("packages").rglob("*.py") if str(p) not in seen):
    verdict = subprocess.run(            # one fresh per-item agent invocation
        ["your-agent", "--prompt", f"Audit {path} for stale docstrings; reply done|failed: <note>"],
        capture_output=True, text=True,
    ).stdout.strip()
    status, _, note = verdict.partition(":")
    with progress.open("a") as f:        # append after each item — resumable
        f.write(json.dumps({"item": str(path), "status": status.strip(), "note": note.strip()}) + "\n")
```

The exact invocation is your agent's; the shape — enumerate, skip-done, call,
append — is the point.

## Keep the tool, or delete it

Most of these scripts are **throwaway**, and that's correct — they exist to get one
large task across the line, and a deleted ten-line enumerator owes no maintenance.
Don't gold-plate a script you'll run twice.

Occasionally one earns a place in `tools/`: when the same enumeration recurs
(every release, every new module), when the tracking file becomes a deliverable
others read, or when the third time you write it (the same *three-times* bar that
promotes a workflow to a skill) tells you it's infrastructure, not scaffolding.
Promote it then, with a name and a docstring, through the normal change — not
preemptively. The default is throwaway; `tools/` is the exception you justify.

## Boundaries

- **Not for small or one-shot work.** A handful of items that fit in one window
  don't need a tracking file — just do them. The technique earns its overhead
  only when the item count exceeds what a context window holds.
- **The per-item action still runs the loop's discipline.** Each mechanical edit
  is still scoped, still gated; a tracking file doesn't license skipping GATES on
  the aggregate change. Run the gates on the whole diff before REVIEW as usual.
- **Doesn't replace REVIEW.** The tracking file proves *coverage* (every item was
  visited), not *correctness* (each edit was right). A clean tracking file and a
  green gate run still go through adversarial review like any other diff.
- **Distinct from Unattended loops.** That section is about *fresh-session-per-
  iteration* mechanics for AFK runs; this is an *in-session* technique you reach
  for while driving. They compose — an unattended loop often uses exactly this
  tracking file — but you don't need the unattended machinery to use it.
