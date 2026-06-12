# path-and-file — filesystem paths, uploads, archive extraction

> **Loaded when:** the change builds a filesystem path from input, accepts file
> uploads, extracts archives, or serves files.
> **Standards:** CWE Top 25 (CWE-22 Path Traversal, CWE-73 External Control of
> File Name or Path) · OWASP Top 10:2025 A01 (Broken Access Control, of which
> path traversal is a member) · ASVS 5.0 V12 (File Handling) · Proactive
> Controls 2024 C3 (Validate all Inputs).
> **Delegation legend:** `tool` = scanner-owned · `hybrid` = scanner finds the
> flow, you judge the fix · `reason` = reviewer-only judgment.

## Spec-stage (proactive control)

At design time, the control is **confinement, not just traversal-blocking** —
the spec should require that resolved paths stay within a designated root
(canonicalize-then-verify-prefix), which is the CWE-73 depth, rather than the
shallower "reject `..`" (CWE-22). Name the allowed root and the rejection
behavior as criteria (ASVS 5.0 V12.1).

## Implementation checks

- `hybrid` **Path traversal (CWE-22).** Input containing `..`, absolute paths,
  or encoded separators reaching a file operation. A SAST taint rule finds the
  sink; you judge whether the fix actually confines.
- `reason` **Confinement (CWE-73) — the deeper miss.** Even with `..`
  stripped, the resolved real path must be verified to live under the intended
  root *after* canonicalization (resolve symlinks first, then check the
  prefix). Stripping `..` without a post-resolution prefix check is the gap
  that scanners and shallow fixes both miss.
- `reason` **Symlink escape.** A path that resolves through an attacker-placed
  symlink can leave the root; resolve links before the boundary check, and
  refuse to follow links into untrusted trees.
- `reason` **Zip-slip / archive extraction.** Each entry's destination must be
  validated to stay under the extraction root; an entry named `../../etc/...`
  writes outside it. Reject absolute and traversing entry names.
- `reason` **Upload handling.** Don't trust the client-supplied filename or
  content-type for storage path or execution decisions; generate the stored
  name, and store outside any executable/served root unless intended.

## Established-helper bypass

Path confinement is the canonical "rolled its own" trap. Resolve the repo's
sanctioned path-confinement / safe-join helper and flag any change that builds
a path with raw string joins or a bare `..`-strip instead of calling it — the
blessed helper is where canonicalize-then-verify-prefix is done correctly,
once.
