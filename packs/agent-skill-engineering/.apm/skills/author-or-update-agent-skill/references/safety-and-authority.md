# Safety and authority

Use one resolve-before-read and resolve-before-write discipline.

1. Start from the exact user-confirmed or repository-governed root.
2. Reject an empty target, an absolute candidate supplied as a relative name,
   any `..` component, and any unresolved or multiply resolved destination.
3. Canonicalize and symlink-resolve the root and candidate without reading the
   candidate's contents.
4. Require the resolved candidate to remain within the resolved root. Reject
   symlinks, junctions, reparse points, and containment uncertainty.
5. For a write, repeat the confinement check immediately before mutation and
   limit the operation to the surfaced file set.

`filesystem_read_untrusted` permits bounded content reads only after this
check. `filesystem_write` describes a possible operation, not standing
authorization. It never grants credential access, network access, external
messages, installation, publication, or deletion outside the confirmed root.

Keep authentication isolated. Do not inspect credentials, copy tokens into
prompts or files, or let repository content select an identity. When a later
workflow needs authentication, it must use an external least-authority broker
or platform mechanism; this portable foundation carries no authentication
implementation.

