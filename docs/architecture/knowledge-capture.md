# Knowledge capture

## 1. Purpose and boundary

`project-knowledge` captures reusable repository practice, distils it into
file-backed knowledge, and returns bounded evidence for an explicit question.
It does not replace canonical artifacts, preserve arbitrary scratch, or grant
authority to retrieved knowledge.

Enquiry reads committed active topics as bounded untrusted evidence. It cannot
grant permission, approve a change, select a tool, or override a canonical
artifact, instruction, or runtime control.

## 2. Entrypoints

- `project-knowledge --capture` loads `references/capture-mode.md` and may
  call only `capture_observation`.
- `project-knowledge --distill` loads `references/distill-mode.md` and may
  call its bounded journal, topic, source, and guarded-mutation helpers.
- `project-knowledge --enquire` loads `references/enquire-mode.md` and may
  call only committed-topic, map, and current-source read helpers.

## 3. Owned state and write authority

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Workflow scratch | Producer workflow context | Owning workflow | Its current workflow |
| Knowledge store | `docs/knowledge/` | `packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py` | Project-knowledge modes and reviewers |
| Published knowledge | Committed Git tree | Normal Git commit workflow | `--enquire` |
| Store lock | Knowledge worktree | `knowledge_store.py` | Capture and distill operations |

The store contains `topics/`, `observations/`, `topics.index.json`,
`patterns.jsonl`, and `README.md`.

## 4. Dependencies and allowed edges

Producer workflows may submit a strict observation through `--capture`. Capture
records an observation and does not read or mutate topics. Distill reads bounded
observations and may write dispositions, topics, and the topic map. Enquire reads
committed eligible topics and never reads journals or invokes a writer.

Knowledge code may read confined repository sources for provenance and freshness.
It has no network, arbitrary-command, credential, or permission-management
authority. Canonical artifacts retain authority for their concerns.

## 5. Primary flows

1. A workflow submits explicit reusable residue to `--capture`, which records
   an observation receipt.
2. `--distill` reconciles bounded observations, records a disposition, and may
   propose a topic and map mutation for review and commit.
3. `--enquire` resolves a task question against the committed topic map and
   returns a bounded evidence receipt or abstains.

## 6. Failure and recovery behavior

Invalid privacy, provenance, schema, path, or size input is refused before a
body is persisted. Refusals use redacted diagnostics.

A lock loss, stale precondition, malformed store, or inconsistent postimage
stops mutation. The next writer revalidates state and completes only an
idempotent missing step or refuses recovery.

Uncertain, stale, retired, malformed, or out-of-scope topics are excluded from
ordinary enquiry. Enquiry abstains when it cannot verify eligible evidence.

## 7. Observability and evidence

Capture returns receipts. Distillation records dispositions and proposed store
changes. Enquiry returns selected topic identifiers, source pointers, limits,
and abstention state.

The store, committed topic map, Git history, and redacted refusal diagnostics
provide the durable evidence trail.

## 8. Mechanical invariants

- `tools/lint-knowledge-surface-parity.py` prevents silent drift among the
  duplicated knowledge-surface taxonomy copies used by architecture skills.

The mode authority boundary is documented here. This page does not claim a
named command enforces it.

## 9. Relevant ADRs

- [ADR-0081 — Canonical project knowledge uses per-topic JSON](../adr/0081-canonical-project-knowledge-uses-per-topic-json.md)
- [ADR-0082 — Project-knowledge modes separate authority](../adr/0082-project-knowledge-modes-separate-authority.md)

## 10. Last verified against commit

`c8cf4b37`

