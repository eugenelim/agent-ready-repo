# Assessment output layout

Saving is optional. Resolve `[architecture] output_dir` in this order:

1. `./agentbundle-layout.toml` relative to the repository root;
2. `~/.agentbundle/agentbundle-layout.toml`, whose value must be absolute or
   `~`-anchored;
3. ask whether to use a repo path (suggest `docs/architecture/`) or an explicit
   personal/vault path. Never choose silently.

Anchor the value to the layout file, reject any `..`, realpath-resolve it, and
surface the absolute destination before the first write. A repo configuration
that resolves outside the repo or follows a symlink outside its intended root
requires explicit confirmation. Create
`<output_dir>/<topic-slug>/assessment.md`, keeping any approved profiler evidence
beside it. Never write configuration or an assessment without approval.
