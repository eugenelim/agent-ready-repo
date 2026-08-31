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
| `CAT-D006` | Acquisition inactivity or download limit breached |
| `CAT-D007` | Archive member refused by the extraction filter or link policy |
| `CAT-D008` | Collection selection missing, unknown, duplicated, or applied to a direct pack; or a remote noninteractive install or upgrade missing `--yes` |
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
| `CAT-D019` | Publisher candidate value failed the output allowlist |

## Reading a refusal

A refusal names the offending path, not just the rule. Before a source root
exists — a malformed URL, for instance — the path is the source string you
supplied, reproduced exactly as you typed it.

Every value in a printed recovery command is shell-quoted, so you can paste
the line as-is even when a publisher chose an awkward skill name.

## Budget codes

Six codes report a measured budget rather than a defect. Each names the
budget it broke and that budget's limit. A value equal to a limit is
admitted; only a greater value refuses.

An integrity refusal is never reported as a budget breach: a symlink inside
a skill folder is a link, not an oversized one, and it carries its own code
and the path it was found at.

