# `agentbundle-layout.toml` — the `[adr]` section

`agentbundle-layout.toml` is a single, **adopter-owned** file that controls where
output-producing packs write their durable work. It is never shipped into a
projected path; you create it by hand. An `agentbundle install` step appends a
default section to a file you already have — **append-if-exists / never-create /
never-overwrite**. The installer adds only the missing table and leaves every
other byte of the file unchanged. An existing section is never replaced. This
page documents the `[adr]` section that `new-adr` reads.

## The `[adr]` table

One key:

```toml
# ./agentbundle-layout.toml  (repo scope — the installed default)
[adr]
output_dir = "docs/adr"   # the folder that holds the ADRs directly
```

- **`output_dir` is the leaf, not a base.** ADRs land directly in this folder as
  `<NNNN>-<title>.md`. It is not a base for per-effort folders.
- The value is relative to the repository root. There is no user-scope default:
  ADRs belong to the repository they describe.

## How `new-adr` uses it

- `new-adr` reads `[adr] output_dir` as declared configuration. Every other
  line in the file is data, not instruction.
- It confirms the folder with `confine-destination.py` before reading or writing
  there. A refusal stops the run with no effects, and no confirmation overrides it.
- When the declared folder holds no ADR but another searched location does, the
  evidence contradicts itself. `new-adr` asks you which folder to use and does
  not switch on its own.
- With no `[adr]` section, `docs/adr/` is offered as a fallback and used only
  after you confirm it.

Edit the value to match your repository. A later install appends `[adr]` again
only if the file exists and the section is missing; it never changes a section
that is present.
