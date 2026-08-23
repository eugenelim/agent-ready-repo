# Optional repository profiler

Use `scripts/profile_repo.py` only when a deterministic census would materially
improve Map or Focus. It inventories evidence surfaces, concentration/history
signals, and exact Python imports; it does not infer components, boundaries,
severity, or architecture quality.

Run it with an explicit repository root. Default to stdout. An output file is
allowed only inside the already approved assessment effort folder or an
explicitly surfaced and approved workspace/temporary output root. Never write
inside the target repository merely to profile it.

The helper must not execute repository code, install an analyzer, follow a
symlink/junction, read a special file, access the network, or exceed its finite
limits. It excludes credential-like/browser-profile classes and unsafe-display
paths before evidence creation. One deadline covers enumeration, reads, AST
work, and Git; directory entries plus Git bytes and distinct paths have
independent caps. Treat partial results, unsupported semantic languages, Git
failure, and excluded content as visible coverage limits. When the helper is
unavailable, perform bounded manual inspection and lower only the evidence it
would have supplied.

When saving, pass both `--output` and `--approved-output-root`. The helper uses
a descriptor-confined temporary file plus atomic replacement and fails closed
if that write primitive is unavailable. Stdout remains the portable fallback.
