# Guide draft: readiness in the offline view

Draft text for `guides/core/how-to/navigate-intents.md` § Export an offline view. It is merged into the guide by plan task T7 and deleted from here in the same change. It exists before implementation so the user task can test the spec.

---

#### Show what is ready to work on

The view can show what `workspace-status` says is ready. Pipe its status command into the export:

```bash
python3 '<workspace-status-dir>/scripts/workspace_status.py' status --root <repo-root> \
  | python3 scripts/navigate_intents.py export --root <repo-root> --readiness -
```

Use the same `<repo-root>` on both sides. The export never runs `workspace-status` and never reads `workspace.toml`. It reads only what you pipe in.

With readiness checked, "What can I work on next?" lists the items `workspace-status` calls active, ready and blocked, in that order. Each blocked row shows the finding codes that stop it. One row can say "work-loop with no spec named resumes this" or "starts this". That row is the item `work-loop` picks when you start it without naming a spec. It reflects how `work-loop` chooses, not a priority. No row is marked when more than one item is active, because `work-loop` then asks which one to resume. No row is marked either when `workspace-status` reports a finding about the item it would pick. "What is broken?" also lists each workspace finding.

Without `--readiness -`, the list shows open work in a startable stage and says readiness was not checked.

If readiness cannot be checked, the export still writes the page. The page says readiness could not be checked and why: standard input could not be read, the input did not finish arriving within 60 seconds, the input was over 4 MiB, nothing was piped in, it was not valid JSON, the repository has no `workspace.toml`, it was not `workspace-status` status output, `workspace-status` reported a problem with `workspace.toml` itself, or the page would have been too large with it. The export's JSON result says the same in its `readiness` field.

The page takes only a few facts from the piped input: which list each item is in, its finding codes and their next-action text. It shows an item only if the view already loaded that file, and shows that file's own name and state. Anything else in the input is dropped.

Pipe only the `status` subcommand. The export refuses every other subcommand's output, and some of those subcommands change files.
