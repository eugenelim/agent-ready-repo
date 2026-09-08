---
title: "Reference: direct-install diagnostic codes"
summary: Look up every refusal code the direct skill-installation route can emit, what it means, and what to do about it.
pack: catalogue-curation
kind: reference
---

# Reference: direct-install diagnostic codes

Installing a skill folder straight from a repository refuses rather than
guessing. Every refusal carries one of the codes below, the path it objects
to, and a recovery line. The table is the complete set: nothing else can
reach you from this route.

Machine-readable schema for the JSON envelope these appear in:
<https://agentbundle.dev/schema/direct-diagnostics-v1.json>

| Code | Meaning |
| --- | --- |
| `CAT-D001` | Malformed owner/repository or invalid URL component |
| `CAT-D002` | Bare or defaulted ref (`main`) refused |
| `CAT-D003` | Hex-shaped tag not safely classifiable as an abbreviated SHA |
| `CAT-D004` | `pax_global_header` SHA absent, malformed, or ref mismatch |
| `CAT-D005` | Interpreter runtime floor below the supported minor |
| `CAT-D006` | Transport failure during acquisition: a download or inactivity limit, a non-2xx HTTP status, a malformed seam between acquisition stages, or a certificate that could not be verified even after the system-trust retry |
| `CAT-D007` | Archive member refused by the extraction filter or link policy |
| `CAT-D008` | Collection selection missing, unknown, duplicated, or applied to a direct pack; a remote noninteractive install missing `--yes`; or a standalone noninteractive upgrade missing `--yes` |
| `CAT-D009` | Measured-path integrity (link-like, reparse, wrong type) |
| `CAT-D010` | Source untraversable or changed during admission |
| `CAT-D011` | Invalid direct identity (slug grammar or length) |
| `CAT-D012` | Measured-envelope entry count |
| `CAT-D013` | Envelope-relative path depth |
| `CAT-D014` | Measured file count |
| `CAT-D015` | Selected-skills count |
| `CAT-D016` | Per-file bytes |
| `CAT-D017` | Total bytes |
| `CAT-D018` | Logical path segment carries a control or surrogate code point |
| `CAT-D019` | Publisher candidate value failed the output allowlist, a declared `allowed-tools` value could not be normalized, or an internal refusal (path-jail, direct-state, or bounded-metadata) reached the install boundary |
| `CAT-D022` | An installed direct identity was requested from the same source at a different ref; use `upgrade --skill <name> --source <source>` |
| `CAT-D023` | A standalone skill upgrade could not read required state, select a usable installed manifestless row, or use the requested output form |
| `CAT-D024` | A standalone skill upgrade matched more than one scope; pass `--scope repo` or `--scope user` |
| `CAT-D025` | A standalone skill upgrade matched more than one adapter; pass `--adapter <adapter>` |
| `CAT-D026` | A standalone skill upgrade re-resolved its source, but the recorded source path no longer identifies the installed skill |
| `CAT-D027` | A standalone skill upgrade found destination bytes that match neither its incoming content nor the digest recorded by the installed row |
| `CAT-D028` | A standalone skill upgrade was given a source override for a row installed from a local path |
| `CAT-D029` | A standalone skill upgrade was given a source override that names a different repository identity |
| `CAT-D030` | A standalone skill upgrade cannot form a request from absent, legacy, malformed, or unconfined stored source provenance |

## Reading a refusal

A refusal names the offending path, not just the rule. Before a source root
exists — a malformed URL, for instance — the path is the source string you
supplied, with any non-graphic, bidirectional-override, or default-ignorable
code point rendered as `\uXXXX`. Every character that would print as itself
does; the escaping exists so a path cannot repaint the line it appears on.

Every value in a printed recovery command is shell-quoted, so you can paste
the line as-is even when a publisher chose an awkward skill name.

## Budget codes

Six codes report a measured budget rather than a defect. Each names the
budget it broke and that budget's limit. A value equal to a limit is
admitted; only a greater value refuses.

An integrity refusal is never reported as a budget breach: a symlink inside
a skill folder is a link, not an oversized one, and it carries its own code
and the path it was found at.

