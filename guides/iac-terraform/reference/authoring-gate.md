---
title: Authoring gate
summary: Commands, record fields, bounds and stop outcomes for governance and infrastructure review.
pack: iac-terraform
kind: reference
---

# Authoring gate

Check governing sources and review evidence with Python 3.11 or newer.
From the installed `generate-iac` skill directory, run:

```sh
python3 scripts/authoring_gate.py discover --root /protected/repo --target infrastructure/main.tf
python3 scripts/authoring_gate.py check-summary governance-summary.json --root /protected/repo
python3 scripts/authoring_gate.py check-review review-record.json --root /protected/repo --saved-plan saved.tfplan --checklist infrastructure-review.md
```

Replace `/protected/repo` with your approved repository root. All file arguments
are relative to it. Keep a copy of the canonical
[infrastructure-review checklist](../../../packs/iac-terraform/.apm/skills/generate-iac/references/infrastructure-review.md)
inside that root for `--checklist`. These commands read local files and print one
JSON object; they never run Terraform, fetch evidence, write files or apply changes.
The caller writes the summary and review record. Their shapes are internal
working records, with no published schema or stability promise.

## Discovery and bounds

`discover --root ROOT [--target PATH ...]` returns candidate `sources`, each with
`path`, `sha256` and byte `size`. It includes root `AGENTS.md` and scoped
`AGENTS.md` files along each target's path. Unrelated instruction trees are
excluded. Planned paths that do not yet exist can select the instruction chain.
Discovery does not decide which records are accepted or extract constraints.

Decision candidates come from `docs/adr`, `docs/decisions`,
`docs/architecture/decisions`, `adr` and `doc/adr`. Name other sources explicitly
in the summary. Discovery visits at most 500 files; each source is at most
262,144 bytes. It refuses unsafe entries rather than silently skipping them.

All file reads stay beneath the root. Absolute paths, drive paths, backslashes,
`.` or `..` segments, symlinks, hard links, non-regular files and changed file
identity during a read are refused. Summary and review JSON inputs are capped at
1,048,576 bytes and 32 nesting levels. Checklists, summary sources and discovery
sources each keep the 262,144-byte source limit. Saved plans and review evidence
files are hashed in bounded chunks under a separate 536,870,912-byte limit per
file. Files above either limit return `source-too-large`. Duplicate keys and
non-finite numbers are rejected.

## Governance summary fields

All four top-level lists are required. Unknown fields are rejected.

| Field | Entry fields | Meaning |
| --- | --- | --- |
| `sources` | `id`, `path`, `sha256`, `authority`; optional `status_line` | Unique source id, root-relative path, exact-byte digest and authority class. |
| `constraints` | `id`, `topic`, `requirement`, `source` | Unique constraint id and governing source id. |
| `unresolved` | Issue entries | Any non-empty list stops authoring. |
| `integrations` | `name`, `status` | Status is `used`, `refused` or `unavailable`. An empty list supports the direct path. |

Authority is `instruction`, `accepted` or `explicit-input`. An `accepted` source
needs `status_line` copied verbatim from a line in the source. After stripping
leading list markers, emphasis and an optional `status:` label, it must begin
with `accepted`, ignoring case. For example, `* Status: accepted` qualifies.
Digests accept 64 lowercase SHA-256 hex digits, with an optional `sha256:` prefix.

Two constraints with the same topic, different requirements and different source
ids produce `conflict`. Resolve semantic disagreements with the source owner and
record them; differently worded requirements need human judgment.

## Review record fields

All top-level fields below are required. Nested records also reject unknown fields.

| Field | Entry fields / values | Meaning |
| --- | --- | --- |
| `subject` | `id`, `sha256` | Exact saved-plan bytes passed with `--saved-plan`. |
| `rubric` | `id`, `sha256` | Exact canonical checklist bytes passed with `--checklist`. |
| `reviewers` | `id`, `kind` | Unique ids; kind is `local` or `core-agent`. |
| `evidence` | `id`, `path`, `sha256` | Unique ids and local files checked against exact-byte digests. |
| `areas` | `area`, `coverage`, `evidence`, `findings` | One entry per checklist area; evidence is a list of evidence ids. |
| `result` | `pass`, `blocked`, `insufficient-evidence` | Declared result must match the derived result. |

The seven areas are `decisions`, `schema`, `plan-effects`, `privilege`, `policy`,
`state-impact` and `reversibility`. Coverage is `covered` or `gap`. Each covered
area needs at least one local evidence id, and every cited evidence id must
resolve to a local file matching its digest. Each finding has a unique
`id`, `severity` (`blocker`, `concern`, `nit`) and `status` (`open`, `resolved`).

Missing areas, gaps or unresolved evidence derive `insufficient-evidence`.
With complete coverage, an open blocker derives `blocked`; otherwise the result
is `pass`. Reviewer kind grants no override. Changed plan or checklist bytes
invalidate the handoff even if the derived status says `pass`.

## Results and recovery

Read both `status` and `issues`. Exit **0** means `ready` for discovery or the
summary, or `pass` for review, with no issues. Exit **1** means a refused check.
Exit **2** means usage or unreadable input. A review can report `pass` with an
issue such as `subject-mismatch`; its exit status is still 1 and work must stop.
Outputs never echo input content.

| Issue code | Meaning and recovery |
| --- | --- |
| `unsafe-path` | Unsafe or unconfined file or target. Supply a safe regular file beneath the root. |
| `source-changed` | Source digest differs. Re-read the source and reassess constraints. |
| `source-too-large` | A file exceeds its size bound. Use a bounded source or evidence file. |
| `no-governing-source` | No sources listed. Supply governing instructions, decisions or explicit inputs. |
| `non-authoritative-source` | Constraint cites an absent source or unsupported authority. Establish its authority. |
| `conflict` | Distinct sources give different requirements for one topic. Resolve with the owner. |
| `unresolved-issue` | The unresolved list is non-empty. Resolve the recorded issues. |
| `integration-refused` | An optional integration refused. Resolve that refusal before continuing. |
| `authority-unverified` | Accepted status lacks a matching accepted source line. Verify the actual decision status. |
| `malformed-summary` | Summary has invalid structure, duplicate keys or ids, or invalid JSON. Correct the record. |
| `file-limit` | Discovery exceeds 500 files; output carries the code only and lists no discovered file name. Narrow sources explicitly; do not treat partial discovery as complete. |
| `malformed-record` | Review has invalid structure, enums, duplicate keys, ids or areas, or invalid JSON. Correct the record. |
| `unresolved-evidence` | A covered area has no verified evidence. Supply valid local evidence. |
| `result-mismatch` | Declared review result differs from derived coverage and blocker status. Correct the record and address its cause. |
| `subject-mismatch` | Saved-plan digest changed. Review the exact replacement plan. |
| `stale-rubric` | Checklist digest changed. Review against the current checklist. |
| `usage` | Invalid command arguments (exit 2). Use the command forms above. |
| `unreadable-input` | Input cannot be read (exit 2). Check root, file and permissions. |

A coverage gap or open blocker may yield `insufficient-evidence` or `blocked`
with an empty issue list. Stop on either result. Oversized JSON inputs report
`source-too-large` alongside `malformed-summary` or `malformed-record`.

## Optional integrations and proof limits

The direct path needs no governance index, bootstrap, template or core reviewer.
Optional integrations can add sources or reviewers; their sources face the same
checks. `unavailable` does not change a result. A refusal, failed check or blocker
must stop the affected step. Never retry through a weaker local fallback or
delete an integration refusal to obtain a pass.

The script proves structure, byte identity and recorded coverage. It cannot prove
that a source was read faithfully, identify semantic conflicts, establish producer
authenticity, or judge the quality of review evidence. It does not acquire a
provider schema or prove that infrastructure will work. Run schema acquisition,
format, validate, saved-plan inspection, policy and security checks separately.
No result grants apply or release approval. Drift checks cover managed resources
only; resources absent from state need a separate inventory.

Next, [validate the reviewed plan bundle](plan-bundle.md).
