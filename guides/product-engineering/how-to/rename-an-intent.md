---
title: "Rename an intent"
summary: Retire one intent path, issue its successor, and recover the transaction if it stops partway through.
pack: product-engineering
kind: how-to
---

# Rename an intent

Use this when an existing intent needs a different namespace token or filename,
but the old path must keep resolving as a retirement record.

Start like this:

```text
Rename this intent from FEAT to STRAT and show me how to recover if it stops.
```

You should end with a successor intent at the target token's next fresh ordinal,
a tombstone at the old path, citations and `workspace.toml` repointed to the
successor, and no in-place renumbering.

## Run the rename

From the repository root, run the installed Core operator:

```bash
python3 .agents/skills/work-intake/scripts/intent_rename.py rename docs/product/intents/FEAT-0001-checkout-redesign.md STRAT
```

The command reads the source intent, Git's tracked-file view, current citations,
`workspace.toml`, and its own transaction stage. It writes only the successor,
the old-path tombstone, affected citation files, `workspace.toml`, and
operation-owned stage files.

A successful run prints:

```text
committed:committed:<operation-id>
```

Here, `committed` means the filesystem transaction reached its complete state.
In this catalogue, the operator flow is not complete until you regenerate the
self-hosted projections and run the corpus check below.

The successor path is chosen by the allocator. Do not choose a number by hand
and do not move the source file yourself.

## Recover an interrupted rename

If the process stops partway through, choose the direction first. A later
`rename` that prints `refused:recovery-required` has found that unfinished
operation; recover it before renaming again.

- Use `forward` when you want the rename completed.
- Use `back` when you want the repository restored to the pre-rename state.

Then re-run the original request with the tombstone date the operation started
with. That is the UTC date of the interrupted run, shown as `2026-09-30` here:

```bash
python3 .agents/skills/work-intake/scripts/intent_rename.py recover forward docs/product/intents/FEAT-0001-checkout-redesign.md STRAT 2026-09-30
```

Recovery treats the saved record as untrusted. It rechecks the request, the Git
snapshot, the live paths, and the stage before it changes anything. If those do
not still describe the same operation, it refuses with one fixed token rather
than guessing.

## Check the result and finish the catalogue flow

Resolve the old path to confirm it is now a tombstone:

```bash
python3 .agents/skills/work-intake/scripts/intent_rename.py resolve docs/product/intents/FEAT-0001-checkout-redesign.md
```

You should see a diagnostic naming the tombstone and its successor. The next
two commands are required in this catalogue after a committed rename or a
forward recovery:

```bash
FORCE=1 make build-self
python3 .agents/skills/work-intake/scripts/intent_corpus_lint.py --dir docs/product/intents --root .
```

The first command regenerates tracked projections from their repointed `.apm/`
sources. The second must report `intent-corpus-lint: clean`. A non-zero result
means the rename is not complete for catalogue delivery, even when the
transaction already printed `committed`.

## What each result means

Every command prints one line: `<status>:<code>`, followed by `:<operation-id>`
when an operation was staged. `rename` and `recover` exit 0 only for
`committed` or `rolled_back`. A syntax error prints `refused:syntax-invalid`
and exits 2. Check the command against the forms above.

### The operation finished

| Output | What it means | What to do |
| --- | --- | --- |
| `committed:committed:<id>` | The rename is complete. | Finish the catalogue flow above. |
| `rolled_back:rolled-back:<id>` | The repository is back at its pre-rename state. | Nothing. Rename again when ready. |

### The operation stopped and can be recovered

| Output | What it means | What to do |
| --- | --- | --- |
| `partial:lock-release-failed:<id>` | The registry edit ran, but the operation could not prove the registry lock was still its own, so it left the lock in place. | Do not delete `.workspace-repair.lock` by hand. Run `recover` with the same source, token and date, choosing a direction. |
| `refused:recovery-required:<id>` | An earlier run stopped partway through. | Run `recover` first, then rename again. |
| `refused:transaction-refused` or `refused:transaction-refused:<id>` | An unexpected condition stopped the run. | With an id, run `recover` using the same source, token and date. Without one, nothing was staged; check that the source and the repository are readable, then retry. |

### The rename was refused before anything changed

| Output | What to do |
| --- | --- |
| `refused:source-missing`, `source-not-regular`, `source-unreadable` | Point at an existing, readable intent file. |
| `refused:source-outside-root` | Use a path under `docs/product/intents/`, relative to the repository root. |
| `refused:source-tombstone` | The source is already retired. Rename its successor instead; `resolve` names it. |
| `refused:source-unregistered`, `registry-unparseable`, `registry-ambiguous` | Fix `workspace.toml` so it parses and exactly one entry names the source. |
| `refused:token-unknown` | Use `VISION`, `STRAT`, `CAP` or `FEAT`. |
| `refused:root-unresolved` | Run the command from inside the repository. |
| `refused:path-dirty` | Commit or discard the uncommitted changes in the source, its citing files, or `workspace.toml`, then rename again. |
| `refused:successor-exists` | The allocated successor filename is already taken. Resolve that file first. |
| `refused:allocation-refused` | The allocator could not answer for the target namespace. Check that the intents corpus and the local `origin` refs are readable, then retry. |
| `refused:stage-budget` | The rename is larger than the operation's limits allow, for example too many or too large citing files. It cannot be done with this command. |
| `refused:git-environment-redirected` | Unset `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and similar variables, then retry. |
| `refused:filesystem-unsupported` | This platform lacks the no-follow, descriptor-relative file calls the operation needs. Run it on a POSIX system such as Linux or macOS. |

### Recovery was refused

| Output | What to do |
| --- | --- |
| `refused:recovery-missing` | No stage matches this source, token and date. Check the date is the UTC date of the interrupted run. If none exists, there is nothing to recover. |
| `refused:stage-unattributed:<id>` | A stage is present, but its record is damaged and names no request, so recovery will not use it. Leave it in place and ask a maintainer to inspect the stage with that id. |
| `refused:recovery-ambiguous` | More than one stage matches. Do not delete stages by hand; ask a maintainer to inspect them. |
| `refused:stage-unsealed:<id>` | The stage is incomplete and the files no longer match the pre-rename state, so recovery will not guess. Ask a maintainer to inspect. |
| `refused:direction-invalid`, `refused:invalid-date` | Use `forward` or `back`, and a `YYYY-MM-DD` date. |
| Any other `refused:` code, usually followed by `:<id>` | Recovery found that the files, the stage or the Git snapshot no longer describe the same operation, and changed nothing. The id names the stage it examined. Leave the stage in place and ask a maintainer to inspect it. |

### Resolve results

| Output | What it means |
| --- | --- |
| `resolve:live:<path>` | The path is a live intent. |
| `resolve:tombstone:<path>:<successor>` | The path is retired; the successor is live. |
| `resolve:tombstone-target-missing:<path>:<successor>` | The tombstone names a successor that does not exist. |
| `resolve:tombstone-target-is-tombstone:<path>:<successor>` | The successor is itself retired. Resolve it in turn. |
| `resolve:tombstone-target-refused:<path>`, sometimes followed by `:<successor>` | The successor could not be read safely. Its path is printed only when it is a safe path inside the intents folder. |
| `resolve:tombstone-retired:<path>` | The tombstone names no successor. |
| `resolve:tombstone-invalid:<path>` | The file carries `Tombstone:` but is malformed. |
| `resolve:resolve-refused` | The path is outside the intents parent or unreadable. |

The next likely request is to inspect the successor and confirm that its new
namespace matches the work it now represents.
