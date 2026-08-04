# RFC-0077: `distill-knowledge` — periodic curation and escalation for `docs/knowledge/patterns.jsonl`

<!-- Written for a cold reader who has not read the related RFCs. Coined terms
are glossed on first use inline. -->

- **Status:** Draft
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-02
- **Date closed:**
- **Decision weight:** heavy — crosses a security boundary: untrusted-file reads with symlink confinement, prompt-injection handling, and destructive edits to `patterns.jsonl`. Each of these risk triggers is enumerated in the decision-weight rule (`packs/governance-extras/.apm/skills/new-rfc/SKILL.md` § Risk triggers).
- **Related:**
  - [RFC-0064 INI-001](0064-ini-001-ai-native-ecosystem.md) — `workspace.toml` coordination artifact; the `[knowledge]` section and `on_closeout` trigger hook into the closeout flow specified here
  - [RFC-0025 work-loop light mode](0025-work-loop-light-mode-and-risk-based-escalation.md) — the capture step (`Capture learnings`) this skill sits downstream of
  - [`docs/knowledge/README.md`](../knowledge/README.md) — canonical schema + supersession convention for `patterns.jsonl`
  - [`tools/hooks/session-start.py`](../../tools/hooks/session-start.py) — loads `patterns.jsonl` at session start; consuming surface for curated entries

---

## Reviewer brief

- **Decision:** Add a `distill-knowledge` skill to the `core` pack that performs two operations over `docs/knowledge/patterns.jsonl` — (1) **curation** (deduplicate, group, edit, and remove entries via a mutation-gate living contract with operator approval; IDs are immutable) and (2) **escalation** (surface migration candidates to the operator for review). Extend `workspace.toml` with an opt-in `[knowledge]` section; section presence gates the `on_closeout` trigger (absent = off, present = on — no configuration keys ship in this RFC). Cadence scheduling (`distill_cadence`) is deferred to the INI-006 RFC.
- **Recommended outcome:** Accept D1–D7.
- **Change if accepted:**
  - New skill: `packs/core/.apm/skills/distill-knowledge/SKILL.md`
  - `workspace.toml` schema gains an optional `[knowledge]` section (section presence = trigger on; section absent = trigger off; no configuration keys in this RFC); the AC is owned by the `distill-knowledge` implementing spec (`docs/specs/distill-knowledge/`)
  - `workspace-status` skill gains an `on_closeout` offer: "run `distill-knowledge` before closing out?" (gated on `[knowledge]` section presence) — **note:** `workspace-status` uses a backend JSON layer (it does not re-read `workspace.toml` at runtime); the backend must export whether the `[knowledge]` section is present; contract tests required
  - Pack version bump: `packs/core/pack.toml` + `.claude-plugin/plugin.json`; adopter guide; pack README; marketing site and tech-doc changelog entries
- **Affected surface:** `core` pack (new skill, minor version bump), `workspace-status` skill body + backend JSON layer (closeout check + section-presence extraction), `workspace.toml` schema (`[knowledge]` section — opt-in, backward-compatible), `docs/knowledge/README.md` (forward reference to mutation gate added; full living-contract update is a post-acceptance implementing-PR artifact, not part of this RFC)
- **Stakes:** Additive and reversible. The skill's output is a proposed list; it writes nothing to governance artifacts autonomously. The `[knowledge]` section is opt-in — repos without it are unaffected. The `docs/knowledge/README.md` change relaxes a previously-stated constraint (append-only) rather than adding a new one.
- **Review focus:** (1) D2 — living contract: should distill-knowledge be a mutation gate (edit/remove) or remain append-only? The living contract is recommended but operators who want immutability can simply not run the skill. (2) D4 — trigger owner: workspace-status surfaces the closeout offer; confirm this is the right owner versus work-loop or a separate hook.
- **Not in scope:** The **editorial** capture step (when and what to capture — that is `work-loop`'s responsibility). **In scope for the implementing PR:** the technical writer changes to `work-loop`'s append path — source format convention (`<initiative-slug>/<sub-artifact>`). Also not in scope: the harness-level cadence scheduler (INI-006 / control-plane work); a new knowledge schema or backend (`patterns.jsonl` is the canonical surface); automatic application of any escalation proposal without operator review.

---

## The ask

**Recommendation (BLUF):** Ship `distill-knowledge` as a core skill — a periodic curation and escalation pass over `docs/knowledge/patterns.jsonl` — so the knowledge base stays healthy and surfaced patterns eventually graduate to the durable artifacts (skills, conventions, lint rules) they warrant.

**Why now (SCQA — Situation → Complication → Question → Answer):**

*Situation:* `work-loop` (its enhanced capture step, landing in a parallel change) now automatically filters practitioner lessons into `docs/knowledge/patterns.jsonl` at loop end using an editorial gate ("would a senior engineer put this in an onboarding note?"). The `session-start` hook already reads the file and injects matching entries into every new session. The schema and supersession convention are established in `docs/knowledge/README.md`.

*Complication:* Append-only growth without periodic curation produces well-known decay: entries that say the same thing differently accumulate; scopes that no longer point at real paths mislead agents; patterns that have fired repeatedly enough to warrant a skill or convention stay buried in the JSONL without escalation. The `session-start` hook injects *all* matching entries — including superseded ones — until a curation pass retires them. As the number of entries grows from tens to hundreds, injection noise compounds.

*Question:* What curates and escalates `patterns.jsonl`?

*Answer:* A dedicated `distill-knowledge` skill that runs at a natural checkpoint (initiative completion or operator cadence), performs a structured curation pass, and emits a proposed migration list for operator review. It is not a background daemon; it is an operator-invoked skill with a clear input, a clear output, and a mandatory human gate before any escalation proposal becomes a change.

**Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
|----|----------|----------------|-----|-----------|-----------------|
| D1 | Where does the skill live — `core` pack or a new `knowledge-management` pack? | **`core`** | `patterns.jsonl` and `docs/knowledge/README.md` are seeded by `core`; every adopter already has the infrastructure. A separate pack creates an install dependency for a skill that benefits every repo. | This review | Confirm or redirect |
| D2 | Curation write rights — should `distill-knowledge` be append-only (new superseding entries only, no edits/deletes) or should it act as a mutation gate (edit in place, remove) with operator approval? | **Mutation gate with living contract** | Append-only keeps the file growing with noise indefinitely — superseded entries inject false context at session start; stale scopes mislead agents. `distill-knowledge` is the correct owner of mutations: it runs at a checkpoint, proposes changes, and requires operator approval before writing. New additions from `work-loop` and contributors remain append-only; only distill-knowledge may edit or remove. Gaps in IDs are valid; the linter enforces only uniqueness. `docs/knowledge/README.md` will be updated to reflect this contract in the implementing PR. | This review | Confirm or restrict to append-only |
| D3 | Escalation thresholds: what makes an entry a migration candidate? | **Four tiers** (see § Proposal — Escalation tiers) | Graduated tiers encode different cost/value signals: high recurrence → skill; universal applicability → always-inject; convention gap → CONVENTIONS.md; enforceable mechanically → lint. "3+ distinct source entries" is the recurring bar — a single occurrence isn't a pattern; two could be coincidence; three across distinct PRs/initiatives is an empirical signal of recurrence. | This review | Confirm thresholds or adjust |
| D4 | Trigger model: `on_closeout` (workspace-status closeout offer) only, or also operator cadence? | **`on_closeout` now; cadence key deferred to INI-006** | `workspace-status` (read-only) surfaces the closeout offer; the section removal is performed by the separate closeout write path (not workspace-status). The offer is the natural synchronous checkpoint. A periodic cadence (e.g. weekly) needs a scheduler out of scope for this RFC (INI-006). `distill_cadence` is not published in this RFC — it will be added in the INI-006 implementing RFC when a consumer exists. The `on_closeout` trigger is gated on `[knowledge]` section presence. | This review | Confirm or propose different trigger owner |
| D5 | Output form: proposed migration list (operator reviews each move) or direct application? | **Proposed migration list — operator reviews and approves each move** | Escalation candidates touch governance artifacts (CONVENTIONS.md, AGENTS.md, lint rules, skill bodies). Automatic edits to these surfaces create drift, bypass review, and break the RFC/ADR lifecycle. The human gate is non-negotiable. | This review | Confirm; no alternative recommended |
| D6 | How are entries appended after distill-knowledge starts handled? | **Single-writer precondition: the operator must not append entries while the skill runs; entries committed by a concurrent session in the Phase 1–Phase 3 window are not in the postimage and must be recovered from git history.** | `distill-knowledge` triggers after `work-loop` is complete — no concurrent writer is expected. No lock is used. The committed-preimage check catches uncommitted concurrent modifications; it does not catch concurrent commits. Entries lost in that narrow window survive in git history. This removes the need for any advisory lock or TOCTOU machinery. | This review | Confirm |
| D7 | ID format for new entries: sequential integers or random synthetic keys? | **Random 12-hex IDs (`K-[0-9a-f]{12}`)** | Sequential IDs require knowing the historical maximum — which may require a git history scan if the highest-ID entry was removed. Random short IDs are append-only by construction: generate with `secrets.token_hex(6)`, verify not in current file, done. Existing `K-\d{4,}` entries are grandfathered. The implementing PR updates `tools/lint-knowledge.py` to accept both formats (see § Follow-on artifacts). | This review | Confirm or stay sequential |

---

## Problem & goals

### The accumulation problem

`patterns.jsonl` is append-only by design — the convention is right for an audit trail. But append-only without curation means:

1. **Semantic duplication.** Two loops independently capture "always run `make lint-ruff` before opening a PR" as separate entries. Both inject on the same sessions; the second adds no signal.
2. **Stale scope.** A gotcha scoped to `packages/auth/**` stays in the file after `packages/auth/` is renamed or removed. Agents see it; the scope is dead.
3. **Supersession opacity.** An entry says "use `WidgetV1`." A later entry says "use `WidgetV2` (supersedes K-0012)." The `session-start` hook injects both; the agent sees a contradiction unless it reads the body carefully.
4. **Graduation gap.** An entry has been independently added by five different loops over three months. It should be a skill step or a CONVENTIONS.md line. No mechanism identifies it as a candidate.

### Goals

1. Keep `patterns.jsonl` free of duplicates, dead scopes, and unretired superseded entries.
2. Identify migration candidates — entries that warrant graduation to a more durable artifact — and surface them as a proposed list for operator review.
3. Run at a natural checkpoint (initiative close or operator cadence) rather than inline with every loop, so the curation overhead does not land on every PR.
4. Produce no autonomous changes to governance artifacts — every escalation is a proposal.

### Non-goals

- **The capture step.** Writing new entries to `patterns.jsonl` is `work-loop`'s job. `distill-knowledge` reads and curates; it does not originate entries.
- **The harness-level cadence scheduler.** `distill_cadence` is not declared in this RFC. It will be added to `workspace.toml` when the INI-006 control-plane scheduler ships. Until then the operator invokes the skill manually.
- **A new schema or backend.** `patterns.jsonl` (line-delimited JSON — one JSON object per line, no wrapping array, validated by `tools/lint-knowledge.py`) is the canonical surface. No migration.
- **Automatic application of any escalation proposal.** The migration list is a prompt to a human, not an action plan.

---

## Proposal

`distill-knowledge` performs exactly two operations per run: **curation** (maintain `patterns.jsonl` health) and **escalation** (surface migration candidates). Both operate over `docs/knowledge/patterns.jsonl`; neither autonomously touches any other governance artifact.

### Security requirements

#### Path confinement and write safety

Before reading any file, resolve its path and verify it stays within the repo root (realpath confinement); reject symlinks to outside the tree.

For every file path **created or written** by the skill — `patterns.jsonl` and temp files (`.distill-temp-*`):

- **Parent-component symlink check:** verify every parent path component from the repo root down to the file's immediate parent directory is a regular directory via `os.lstat()`; reject if any component is `S_ISLNK`. A symlinked parent (e.g., `docs/knowledge/` → `some/other/dir/`) passes root-confinement and final-component checks but redirects all writes to the symlinked location. **Windows junctions:** `os.lstat()` + `S_ISLNK` and `os.path.islink()` both return `False` for NTFS junction points (CPython #23407), and resolved-path containment alone passes a within-repo junction. The implementing spec must apply both checks on Windows: (1) containment — resolve each parent with `Path.resolve()` and verify `Path.is_relative_to(repo_root)` (Python ≥ 3.9) or `os.path.commonpath([resolved, repo_root]) == os.path.realpath(repo_root)` — not `.startswith()` (accepts `/repo-evil` for root `/repo`); (2) reparse-point rejection — on Python ≥ 3.12 call `entry.is_junction()`; on Python 3.8–3.11 check `os.lstat(component).st_reparse_tag != 0` (`lstat`, not `stat` — `stat` follows junctions and returns the target's tag, which may be 0) (non-zero means any reparse point, including junctions). Both checks must run on every supported Python/Windows combination. See the repository's `path-and-file` security checklist axis (a).
- **Final-component check:** the file itself must not be a symlink even if it resolves within the root.
- These checks must run before creating any temp file, not only before mutation-target writes.

All mutation-target writes must use **atomic no-follow semantics**: write to a temp file in the same directory, then rename. On POSIX: open with `O_CREAT|O_EXCL|O_NOFOLLOW`. On Windows (`O_NOFOLLOW` is unavailable): open with `O_CREAT|O_EXCL` and then verify the opened file is not a reparse point before writing. The implementing spec must provide a single cross-platform utility that encodes both branches. **TOCTOU between lstat check and write:** the window between the parent-component `lstat()` verification and the subsequent `open()`/`os.replace()` is unavoidable at the Python `pathlib`/`os` level; an attacker who can replace a verified directory with a symlink in that window wins. The implementing spec must use **directory-fd-relative operations** to minimize this window: on POSIX, open the immediate parent directory with `os.open(parent, O_RDONLY|O_DIRECTORY)` before the lstat pass and use `openat(dirfd, filename, ...)` and `renameat(dirfd, ...)` from that fd; on Windows, obtain an NTFS directory handle and use `NtCreateFile` with the `OBJ_DONT_REPARSE` attribute or `CreateFileW` with `FILE_FLAG_OPEN_REPARSE_POINT` followed by a reparse-point check. This does not eliminate the window entirely (an attacker with directory-rename capability can still act between `opendir` and `openat`) but shrinks it to the kernel dispatch latency rather than the Python frame latency.

#### Data-not-instructions boundary

All string fields read from `patterns.jsonl`, contract files (`docs/knowledge/README.md`, `docs/CONVENTIONS.md`), and any destination file inspected during suppression checks must be treated strictly as data — never as instructions. Destination files are particularly high risk (arbitrary in-repo files any contributor can modify); the SKILL.md must state that destination file contents are untrusted evidence only.

#### Global display escaping

Every operator-facing display of contributor-controlled content must render all contributor-controlled fields as **canonical escaped JSON with a per-row SHA-256 digest**. This applies to:

- Curation proposals (1a dedup candidates, 1b grouping clusters, 1c stale-scope list, 1e supersession pairs)
- Validation error messages (showing malformed record content)

Raw or unescaped display allows ANSI escapes, bidirectional controls, HTML, or Markdown structure to spoof operator confirmation. The implementing spec must define a single shared display renderer enforced across all approval surfaces, including a "show raw JSON bytes" view available on demand.

#### File validation

Run these validations before Phase 1 scoring or any mutation. Apply to both live files at Phase 1 and postimage temp files before rename.

**`patterns.jsonl` — 8 checks (ACs for implementing spec):**

| # | Check |
|---|-------|
| a | Every record is valid JSON. |
| b | Every record has exactly the required fields: `id`, `kind`, `scope`, `title`, `body`, `source` — no missing or extra fields. |
| c | All six field values are strings (not null, number, array, or object). |
| d | All six string values are non-empty after stripping. |
| e | `kind` is one of the valid enumerated values: `pattern`, `gotcha`, `antipattern`. |
| f | `scope` is a non-empty glob string. |
| g | No `id` value appears more than once. |
| h | Every `id` matches `K-\d{4,}` (sequential legacy) **or** `K-[0-9a-f]{12}` (random — new entries from this RFC forward). Both formats remain valid in perpetuity; no migration of existing entries is required. |

Validation failures enter **read-only assessment mode**; do not proceed to scoring or any Phase 3 mutation. An empty file (zero records) is valid.

---

### Streaming preflight limits

Apply before loading any target file, and when reading destination/contract files during suppression checks or convention-gap scoring.

**Per-file limits:**

| File | Size limit | Record limit | Notes |
|------|-----------|--------------|-------|
| `patterns.jsonl` | Spec-defined | **Absolute safety max** ≤ 10,000 records (abort on exceed); **Phase 1 scoring batch size** = 200 entries (continue with next batch if exceeded — never abort) | Batch size is a processing unit; abort fires only at the hard safety max. Equal values would wrongly abort valid large corpora; these must be distinct. Batching strategy must be deterministic. |
| Destination / contract files | ≤ 512 KB | Spec-defined | Files read during convention-gap scoring |

Exceeding the absolute safety max aborts the current phase with an operator-visible error naming the file and limit. Limits apply to input files at startup and to postimage temp files before rename.

---

### Execution sequence

Each run follows three phases in order.

#### Phase 1 — Pre-curation score

1. Read and validate `patterns.jsonl`.
2. **Build the supersession map** (full corpus): scan every entry body for `supersedes K-NNNN` citations; record `(citing entry → cited entry)` pairs.
3. **Pre-curation cycle check** (full corpus): validate the supersession graph for cycles. A detected cycle excludes all entries in the cycle from the supersession pre-pass and from 1e; surface as a data error.
4. **Deterministic full-corpus scoring:** Recurring (count distinct `source` initiative prefixes), Universal (scope == `"*"`), and Mechanically-enforceable (pattern match). These three tiers require no LLM call and run on the full corpus.
5. **Partition into batches of ≤ 200 entries** using the spec-defined deterministic strategy. Batching applies only to the LLM-intensive scoring in step 6; deterministic scores from step 4 are computed once and carried forward.
6. **LLM semantic scoring per batch:** Convention-gap detection (requires understanding entry intent vs. CONVENTIONS.md) and near-paraphrase detection for 1a grouping candidates. Merge results across batches. **Cross-batch semantic gap:** entries assigned to different batches are never compared to each other within that LLM call, so a near-paraphrase pair split across batch boundaries will not be detected in step 6 unless the batching strategy places them in the same batch or an additional cross-batch pass runs. The implementing spec must define an explicit cross-batch comparison strategy for near-paraphrase detection — options include (a) overlapping batches (each entry appears in two consecutive batches, O(n) calls), (b) a pre-clustering step that groups candidates by title-similarity before batching so candidates stay together, or (c) a second cross-batch pass limited to the candidates flagged by within-batch near-paraphrase detection. The implementing spec must select one and document the false-negative risk of its choice. **Owner:** implementing spec.
7. **Compute 1b grouping clusters** from the merged semantic results (runs once on the cross-batch merged output). Recurring-threshold check for Phase 2 gating uses the full-corpus scores from step 4.
8. No mutations written in Phase 1.

**Canonical supersession citation form:** `supersedes K-NNNN` (literal word `supersedes`, space, valid ID matching `K-\d{4,}` or `K-[0-9a-f]{12}`). This form is the only one the skill guarantees to detect. The implementing spec may define a broader parser as a best-effort fallback for legacy entries, but must update `docs/knowledge/README.md`, the adopter seed, and `work-loop`'s capture guidance to require the canonical form.

#### Phase 2 — Gated grouping decisions

For each 1b cluster containing an entry in the Recurring tier of the pre-curation escalation set, before offering compaction:

1. Present the Recurring escalation proposal to the operator.
2. Operator accepts, rejects, or defers ("decide next session"). Accepted or rejected → compaction may proceed. Deferred → skip compaction for that cluster this session.
3. Rejected or deferred proposals are omitted from the final migration list for this session.

#### Phase 3 — Curation and final migration list

**Committed-preimage requirement:** before any Phase 3 mutation (removal **or** edit-in-place), verify:
- `patterns.jsonl` is tracked by git: `git ls-files --error-unmatch <path>` must succeed. (`git diff --quiet` exits 0 for untracked files and does not detect this case.)
- `patterns.jsonl` has no uncommitted modifications: `git diff --quiet HEAD -- <path>`.
- If either fails, halt and instruct the operator to commit first.

**Curation order:**

| Step | Operation | Notes |
|------|-----------|-------|
| 1 | **Supersession pre-pass** | For each 1b cluster containing a cited entry: present the 1e retirement for that cited entry first. Approved → record retirement, remove from cluster. Rejected → cluster is ineligible for grouping. |
| 2 | **1a** — deduplication | |
| 3 | **Re-filter 1b clusters** | Remove entries already retired; drop clusters below three live entries (Phase 1 escalation scores retained). |
| 4 | **1b** — grouping (now unblocked) | |
| 5 | **Post-compaction cycle check** | Re-validate supersession graph after all 1a/1b citation retargeting. If a new cycle is found, **cancel the responsible 1a/1b compaction** — do not commit a known cycle. Surface as a data error; remaining steps may proceed. |
| 6 | **1c** — stale-scope retirement | |
| 7 | **1d** — scope tightening | |
| 7.5 | **Re-filter 1e candidates** | Drop any supersession pair where either the citing or the cited entry was removed in steps 1–7. Only pairs where both endpoints are still live proceed to step 8. |
| 8 | **1e** — remaining supersession retirements | |

After approved mutations: (i) recompute Recurring scores (drop entries removed by 1c/1e; if the cluster falls below the 3-source threshold, remove that Recurring proposal from the migration list); (ii) re-score Universal, Convention gap, and Mechanically-enforceable tiers against the final corpus.

**Supersession link preservation during 1a/1b:** after each removal, check the pre-curation supersession map:
- Removed entry was the **citing** entry and the survivor/merged entry lacks the citation → copy the citation to the survivor/merged entry.
- Removed entry was the **cited** entry removed by **1a** → retarget the citation to the survivor (`supersedes K-SURVIVOR`).
- Removed entry was the **cited** entry removed by **1b** → the supersession pre-pass (step 1) must have retired it first; if the cluster still contains it, it is ineligible for grouping.
- **Self-supersession guard:** discard any edge where both endpoints collapsed to the same ID after compaction.

**Postimage validation before rename:** run the 8-check `patterns.jsonl` validation plus size limits against the postimage temp file. On any failure: delete temp files and abort.

---

### Concurrency model

`distill-knowledge` triggers after `work-loop` is complete — the initiative work queue is empty and no concurrent session is appending to `patterns.jsonl`. The skill runs sequentially inside a single agent session.

**Snapshot at Phase 1.** The skill reads `patterns.jsonl` once and operates on that in-memory snapshot throughout Phases 2 and 3. Entries appended after Phase 1 are not curated in this run; they are curated on the next invocation.

**Single-writer precondition.** The operator must not append entries to `patterns.jsonl` while the skill is running. No lock is used. The committed-preimage check (the Committed-preimage requirement in § Phase 3) detects uncommitted modifications made by another session before Phase 3 writes; it does not detect entries committed by a concurrent session between Phase 1 and Phase 3 write-out. An entry committed in that narrow window is absent from the postimage and is lost from `patterns.jsonl`; it can be recovered from git history and re-added on the next run.

**Atomic writes at Phase 3.** Write the curated corpus to a temp file in the same directory (realpath-verified), validate the postimage, then call `os.replace`. A crash during the write leaves either the old file or the new file — never a partial write.

**Crash recovery.** Restart the session. Git history contains every entry that existed before the run; there is no journal or lock file to clean up. Any leftover `.distill-temp-*` files in the knowledge directory can be deleted safely on restart.

**ID allocation.** New entries use **random 12-hex IDs** of the form `K-[0-9a-f]{12}` (e.g., `K-a3f9b2c1d2e3`). Generate a random value with `secrets.token_hex(6)`, prepend `K-`, and verify the result is not already present in the current `patterns.jsonl` (single O(n) scan). Re-draw on collision (expected frequency: negligible). No historical scan, no watermark, and no sequential counter are needed. Existing `K-\d{4,}` entries are grandfathered; no migration is required.

---

### Operation 1 — Curation

Curation maintains the health of `patterns.jsonl` itself. **New additions from `work-loop` and contributors remain append-only; only `distill-knowledge` may edit or remove entries, and only after operator approval (D2). IDs are immutable — gaps from removals are valid. Git commit is the audit trail for all removals.**

**1a. Deduplication.** Two or more entries are duplicates if their `title` and `scope` are semantically equivalent (exact or near-paraphrase). The skill presents both entries' full content to the operator and proposes keeping the richer one. **Exception — supersession pairs:** if the two entries also form a supersession pair (one entry's body contains `supersedes K-NNNN` pointing at the other), do not apply the richer-entry heuristic — the citing/newer entry is always the candidate to keep. Route such pairs to 1e rather than 1a. On approval: remove the weaker entry.

**Supersession citation preservation:** before removing the weaker entry, check whether its body contains a `supersedes K-NNNN` citation. If so and the surviving entry's body does not already contain the same citation, either (a) add the citation to the surviving entry's body before writing, or (b) carry it forward as a pre-curation supersession candidate to 1e.

**Source provenance preservation:** before removing the weaker entry, check whether its normalized initiative prefix (see source field normalization in § Evidence) differs from the survivor's. If it does, the survivor's `source` field must be updated to record the additional provenance so future Recurring-tier scoring can count it. The implementing spec must define the multi-source accumulation format for the `source` field (a structured delimited list — not comma-joined raw values). The Recurring scorer reads only the `source` field for counting; body footnotes are for human recovery only and are not parsed for scoring.

**1b. Grouping.** A cluster of three or more entries with overlapping `scope` globs and related `body` content can be collapsed into one richer entry. The merged entry's `source` field is set to `"distill-knowledge: merged K-NNNN,K-MMMM,K-PPPP"` (naming the compacted IDs). The merged entry's `body` must include a parenthetical note: `(merged from K-NNNN source: <orig>, K-MMMM source: <orig>, K-PPPP source: <orig>)` so the original provenance is recoverable from the entry itself. On approval: remove the clustered entries, write the merged entry (with a **freshly generated random 12-hex ID** per D7) at the end of the file. The merged entry starts fresh for Recurring scoring — the Phase 2 gating constraint ensures any Recurring escalation for the cluster was already resolved before compaction. The body footnote is for human provenance recovery only; it is **not** parsed by the Recurring scorer. Only the `source` field is scored. **Constraint:** if the cluster satisfies the Recurring threshold, resolve the Recurring escalation before compacting (see Phase 2 gating).

**1c. Stale-scope retirement.** An entry whose `scope` glob matches no file in the current working tree is a candidate for removal. **Working-tree revalidation:** immediately before writing each approved 1c removal, re-check whether the scope now matches any file — another process may have created a matching file between Phase 1's tree walk and Phase 3's write. If the scope now matches files, abort that specific retirement and notify the operator. On approval: remove the entry.

**1d. Scope tightening.** An entry with `"scope": "*"` (repo-wide) but a `body` referencing a specific package, file, or subsystem gets a proposed scope narrowing. On approval: edit the entry in place to use the tighter glob. Note: tightening `"*"` removes Universal-tier eligibility; tightening also changes Convention-gap destinations. The skill surfaces this to the operator as part of the proposal so they can decide whether to re-add the entry to the escalation queue under the new scope.

**1e. Supersession retirement.** When a newer entry's body cites an older entry by ID (`supersedes K-0012`), the older entry is a supersession candidate if it still exists and its scope has live matches (not already caught by 1c). **Supersession graph validation:**
- **Pre-curation check (Phase 1, step 3):** validate the pre-curation graph for cycles. Detected cycles exclude all member entries from the pre-pass and from 1e; surface as a data error.
- **Post-compaction check (Phase 3, step 5):** re-validate after all 1a/1b citation retargeting. If a new cycle is detected, cancel the responsible compaction step (do not commit the known cycle).

On operator approval: remove the superseded entry.

**Living contract (D2).** These operations make `patterns.jsonl` a living document: append-only for additions; distill-knowledge-mediated for maintenance. IDs are immutable once assigned — gaps are valid. The implementing PR must update four surfaces in sync: `docs/knowledge/README.md`, `packs/core/seeds/docs/knowledge/README.md` (the adopter seed — **required**: Risk #5's content-validation gate checks for the mutation-gate marker; if this seed is not updated, every fresh install fails closed immediately), `docs/CONVENTIONS.md` (revise "append-only" to "append-only for additions; `distill-knowledge` is the mutation gate"), and `packs/core/seeds/docs/CONVENTIONS.md`. Updating only the README leaves contradictory guidance on every fresh install.

---

### Operation 2 — Escalation

Escalation identifies entries whose maturity warrants moving to a more durable artifact. The skill applies four tiers in order; an entry may match more than one tier.

#### Escalation tiers (D3)

| Tier | Signal | Proposed destination |
|------|--------|----------------------|
| **Recurring** | Entry's `source` values span 3+ distinct initiatives or PRs (inferred from the `source` field across entries sharing the same `title` or a near-paraphrase, or appearing independently in 3+ entries) | If the entry describes a **multi-step workflow** performed repeatedly: propose as a new skill via `new-spec`. Otherwise: propose addition to an existing skill body, `docs/CONVENTIONS.md` (via `new-rfc` if RFC-governed), or a lint rule. Cite the entry cluster in either case. |
| **Universal** | Entry's `scope` is `"*"` (or near-`*`), `kind: "pattern"`, no qualifier limiting it to a specific file path or tech stack | Propose promotion to always-injected context (e.g. AGENTS.md preamble or `session-start.py` hardcoded block) |
| **Convention gap** | Entry describes a team convention or process rule not reflected in `docs/CONVENTIONS.md`, the relevant `AGENTS.md`, or an adopter-facing guide | Propose addition to `docs/CONVENTIONS.md` (via `new-rfc` if this repo's conventions are RFC-governed — operator follows the repo's normal change process), the relevant `AGENTS.md`, or `guides/_shared/` (operator selects destination and scope — internal convention vs. adopter doc) |
| **Mechanically enforceable** | Entry describes a constraint that can be verified by a linter (file naming, import shape, config key presence, forbidden pattern), or encoded in a test or in foundation code | Propose a new lint rule, a test, or a change to a foundation utility / base class; entry stays in `patterns.jsonl` until the enforcement mechanism is confirmed passing |

**Destination scope is per-repo, not per-catalogue.** When `distill-knowledge` runs in an adopter's repo, escalation destinations are that repo's `docs/CONVENTIONS.md`, `AGENTS.md`, test suite, foundation code, and `guides/` subtree — not the upstream catalogue's docs.

Entries that match none of these tiers — genuinely non-obvious, scope-bounded, not yet recurring — stay in `patterns.jsonl` without action.

#### Escalation output

The skill emits a **proposed migration list** — a **fenced plain-text block** (not a Markdown table) listing candidates, **one object per (entry, tier) combination**, rendered using the canonical JSON+SHA-256 renderer defined in the Global display escaping section above. Each record shows: entry `id`, tier, recommended destination, and a one-line rationale, all as canonical escaped JSON with a per-record SHA-256 digest.

Fenced display prevents `|`, raw HTML, Markdown image/link syntax, and backtick sequences in contributor-controlled fields from being interpreted by the rendering host. No ad-hoc sanitizer is permitted. Include an explicit record count before the fenced block so the operator can verify the list is complete.

An entry satisfying multiple tiers gets one row per tier, each independently approvable. No change is written to any governance artifact until the operator explicitly approves it.

**Before emitting the list**, filter or remap all entries retired in the current run: entries removed by 1c or 1e are dropped; entries removed by 1a are dropped (the surviving entry retains the row under its own ID if applicable); entries removed by 1b are dropped and surviving escalation proposals are remapped to the merged entry's new ID.

The migration list is a prompt to action, not an action. Approved rows become the operator's own PRs; the skill does not author those changes.

---

### Escalation completion

When the operator accepts a proposal from the migration list, they add it to `workspace.toml` as a `[backlog]` item using `capture-work` (the skill that writes `workspace.toml`; `workspace-status` is read-only). `distill-knowledge` does not write to `workspace.toml` and does not scan it for completion.

**Operator-driven cleanup.** When an escalated entry has been implemented (the lesson now lives in a skill, a lint rule, a convention, or a guide), the operator invokes the skill's cleanup step explicitly, naming the K-ID to retire: "K-NNNN is implemented — remove it." The skill presents the entry for confirmation, then removes it on approval. Git commit is the record. No automated detection of workspace.toml state is required.

**Suppression.** If an entry's escalation signal no longer fires (its scope became stale, it was deduplicated, or the destination artifact now plainly encodes the lesson), distill-knowledge simply omits it from the migration list. No suppression state file is needed.

---

### Triggers (D4)

**`on_closeout`** — synchronous trigger. `workspace-status` (not `work-loop`) owns the initiative closeout flow: when all specs under an initiative reach `Shipped` status and the work queue is empty, it surfaces "ready to close out? Run closeout to remove this section." At that same moment it also offers: "Run `distill-knowledge` before closing out?" This fires once per initiative closeout, before the section is removed. The operator may decline.

The trigger is gated on `[knowledge]` section presence. A repo without a `[knowledge]` section is unaffected — the closeout flow does not offer the skill. An operator who wants the trigger off removes the section. No configuration keys ship in this RFC: section present = on, section absent = off. (`distill_cadence` and `distill_on_closeout` will be added in future RFCs when a second caller actually needs to differ.)

The `[knowledge]` section is **opt-in**. A repo without it is unaffected by this skill — no trigger fires, no offer is made. Adding the section opts in.

**Manual invocation** is always available: the operator types `/distill-knowledge` (or the equivalent invocation for their harness) at any time, regardless of `[knowledge]` section presence.

### Adopter-agnostic by construction

`docs/knowledge/patterns.jsonl` and `docs/knowledge/README.md` are seeded by the `core` pack on every `agentbundle install`. The schema (`id`, `kind`, `scope`, `title`, `body`, `source`) is uniform across every adopter repo. The distillation operations — dedup, group, retire stale scopes, escalate — are content-agnostic: they apply the same protocol regardless of what the entries say. The content differs per repo; the protocol does not. Note: the full living-contract README update ships in the implementing PR (see Follow-on artifacts and Risk #5), not in this RFC.

---

## Options considered

### D1 — Skill home

*Axis: where to house the skill, across a MECE set of packaging options.*

| Option | What it is | Trade-offs | Selected? |
|--------|------------|------------|-----------|
| **`core` pack** | New skill alongside `work-loop`, `new-spec`, etc. | Every adopter already has `core`; no install step; the knowledge infrastructure it curates is already core-seeded. Cost: `core` grows by one skill. | **Yes** |
| **New `knowledge-management` pack** | A standalone opt-in pack | Clean separation; opt-in. Cost: creates an install dependency for a benefit every repo wants; fragmenting maintenance of a single `patterns.jsonl` surface across two packs adds friction without a clear benefit threshold. | No |
| **`governance-extras` pack** | Alongside `new-adr`, `new-rfc` | Governance-extras is repo-scope and targets governance docs; knowledge curation is practitioner-layer, not governance. Wrong home. | No |
| **Do nothing** | Rely on manual hand-curation | Free. Cost: the accumulation problem compounds with every loop; senior engineers spend time on mechanical dedup instead of higher-value work; no escalation path means patterns graduate only if someone remembers to check. | No — the cost of delay is ongoing quality decay |

**Selected: `core` pack.**

### D2 — Curation write rights

*Axis: whether `distill-knowledge` may mutate `patterns.jsonl` (edit/remove/reindex) or only append.*

| Option | What it is | Trade-offs | Selected? |
|--------|------------|------------|-----------|
| **Append-only (original convention)** | distill-knowledge appends a new superseding entry; never edits or removes | Zero mutation risk; history is always preserved. Cost: superseded entries keep injecting at session start (noise); stale-scope entries keep injecting misleading context; the file grows indefinitely; a 500-entry file injects far more noise than a curated 80-entry one. | No |
| **Mutation gate with living contract (recommended)** | distill-knowledge may edit in place and remove — all operator-approved; additions from work-loop remain append-only; git commit is the audit trail; IDs are immutable and gaps are valid | Keeps the injection surface clean; gives agents accurate context. Cost: requires operator to review and approve each mutation. | **Yes** |
| **`supersedes` field + soft-deletion flag** | Add `"supersedes"` and `"retired": true` fields to the schema | Machine-checkable by linter; session-start can filter `retired: true` entries without removing them. Cost: schema bump; linter update; two new field decisions (required vs. optional, behavior on absent flag); the file still grows; reindexing is not addressed. | No |

**Selected: mutation gate with living contract.**

### D3 — Escalation thresholds

*Axis: what evidence level triggers a migration proposal.*

| Option | What it is | Trade-offs | Selected? |
|--------|------------|------------|-----------|
| **1+ occurrence** | Any entry is a migration candidate | Catches everything. Cost: escalates observations, not patterns — the proposal list floods with noise on every run. | No |
| **2+ distinct sources** | Two independent captures trigger escalation | Lower noise than 1+. Cost: two occurrences may still be coincidence; the Recurring tier exists precisely to distinguish signal from noise. | No |
| **3+ distinct sources (recommended)** | Three independent captures trigger Recurring escalation; all four tiers apply their own signals | Empirically: three is the minimum threshold in established pattern-language traditions and in the "rule of three" refactoring heuristic. Universal/Convention/Enforceable tiers fire on qualitative signals, not a count. | **Yes** |
| **5+ distinct sources** | Higher confidence bar | Fewer false positives. Cost: high-value patterns stay buried longer; in a repo with low loop frequency, 5 sources may take years. | No |

**Selected: 3+ distinct sources for the Recurring tier; qualitative signal for Universal, Convention gap, Enforceable tiers.**

### D4 — Trigger model

*Axis: when distill-knowledge runs and who surfaces the offer.*

| Option | What it is | Trade-offs | Selected? |
|--------|------------|------------|-----------|
| **`on_closeout` via workspace-status** | workspace-status surfaces the closeout offer; distill-knowledge offer is added alongside it | Correct lifecycle owner (workspace-status owns the closeout **flow**, not work-loop); synchronous; no scheduler dependency. | **Yes (synchronous trigger)** |
| **`on_initiative_done` via work-loop** | work-loop sets `status = "done"` and offers distill-knowledge | Incorrect: the real closeout removes the section; there is no `status = "done"` state in the schema (RFC-0064). | No |
| **Cadence only** | Periodic scheduled run | Steady-state maintenance rhythm. Cost: requires INI-006 / control-plane scheduler, which is out of scope for this RFC. | Deferred |
| **`on_closeout` now + cadence deferred (recommended)** | `on_closeout` ships now; `distill_cadence` key deferred entirely to the INI-006 RFC | Delivers value immediately; no silently inert configuration; INI-006 adds the cadence key when a consumer exists. | **Yes** |
| **Manual only** | Operator invokes on demand | Always available as a fallback; not a replacement for triggered curation. | Baseline (always available; not the primary path) |

**Selected: `on_closeout` (workspace-status) now; `distill_cadence` key deferred entirely to INI-006. The `on_closeout` trigger is gated on `[knowledge]` section presence — absent section = off.**

### D5 — Output form

*Axis: how distill-knowledge delivers escalation candidates to the operator.*

| Option | What it is | Trade-offs | Selected? |
|--------|------------|------------|-----------|
| **Proposed migration list (recommended)** | The skill emits a human-reviewed fenced list of candidates; the operator approves each entry individually; no governance artifact is modified until the operator acts | Keeps governance artifacts under intentional human control. Cost: operator must take follow-up action; proposals can accumulate unacted-on. | **Yes** |
| **Direct application** | The skill writes directly to CONVENTIONS.md, AGENTS.md, lint rules, or skill bodies based on escalation tier | Eliminates the approval step; all escalation proposals become changes immediately. Cost: automated edits to governance artifacts create drift, bypass review, and break the RFC/ADR lifecycle — an erroneous escalation modifies policy without human review. | No |
| **Do nothing / always offline** | Escalation output is suppressed; skill only curates patterns.jsonl, never surfaces migration candidates | Simpler skill contract. Cost: migration candidates silently accumulate in patterns.jsonl indefinitely, defeating the escalation goal entirely. | No |

**Selected: proposed migration list — operator reviews and approves each move. Escalation candidates touch governance artifacts; the human gate is non-negotiable.**

### D6 — Entries appended after Phase 1 snapshot

*Axis: how to handle appends to `patterns.jsonl` that land after the Phase 1 snapshot.*

`distill-knowledge` triggers after `work-loop` is complete; no concurrent writer is expected. The skill takes a snapshot at Phase 1 and operates on it throughout; Phase 3 writes only the curated snapshot. The operator must not append entries while the skill is running. An entry committed by a concurrent session in the Phase 1–Phase 3 window is not in the postimage; it survives in git history and can be re-added on the next run. No advisory lock is used.

**Selected: single-writer precondition (D6). No advisory lock or TOCTOU machinery is needed.**

### D7 — ID format for new entries

*Axis: sequential integers vs. random synthetic keys for new `patterns.jsonl` entries.*

Sequential IDs (`K-\d{4,}`) require knowing the historical maximum, which may not be present in the live file if the highest-ID entry was removed. A git-history scan works but adds complexity and introduces a POSIX-tool dependency.

Random 12-hex IDs (`K-[0-9a-f]{12}`) are append-only by construction: generate a value, verify it is not already in the current file, write. No historical knowledge required. Existing `K-\d{4,}` entries are grandfathered; the linter and CI accept both formats by updating check (h) to `K-\d{4,}|K-[0-9a-f]{12}`.

**Selected: random 12-hex IDs for new entries (D7). Existing entries are grandfathered.**

---

## Risks & what would make this wrong

**Pre-mortem:**

1. **Empty `patterns.jsonl` at first run.** The skill runs on initiative close before `work-loop`'s enhanced capture has landed in the codebase. The file has zero entries; the skill reports "nothing to distill." Mitigation: the skill handles an empty or absent `patterns.jsonl` gracefully (exits with "No entries to process — file is empty or not present") and does not error.

2. **Escalation list accumulates without operator action.** The migration list is a proposed list, not a task queue. If the operator never acts on it, entries that warrant graduation stay in `patterns.jsonl` indefinitely. Mitigation: the skill surfaces the list at initiative close — an active human moment — so the proposal is not buried. Unactioned proposals are not a correctness problem; the entries remain functional in `patterns.jsonl`. The risk is opportunity cost, not data corruption.

3. **Curation introduces a regression: a retired entry was actually still valid.** An entry is retired on stale-scope grounds; later someone adds back the same package at the same path. Mitigation: the committed-preimage requirement ensures the complete entry text is always in git history and can be recovered via `git log -S <id> -- docs/knowledge/patterns.jsonl`. A future loop can re-add the lesson if the scope re-appears.

4. **Near-paraphrase detection produces false positives.** Two entries with similar `title` values are flagged as duplicates but are actually making a subtly different point. Mitigation: the deduplication step is always operator-reviewed — the skill presents both entries' full content and asks for an explicit decision before removing the weaker entry. The operator can reject the proposal.

5. **Upgrading adopters may retain stale append-only contracts.** `deliver_seeds()` writes companion files when seeds differ, but an operator can delete the companion without accepting the living-contract wording — or never receive a companion if they customized the file before the upgrade. Companion absence is therefore not proof of contract acceptance. Mitigation: the skill must **fail closed using content validation** — at startup it reads both `docs/knowledge/README.md` and `docs/CONVENTIONS.md` and checks whether each contains the living-contract marker phrase (the implementing spec must define the canonical phrase, e.g. `"distill-knowledge is the mutation gate"`). If either file lacks the marker, the skill enters **read-only assessment mode** (reports what it would do, proposes nothing, executes no mutations) and lists the specific files the operator must update. Companion files (`README.upstream.md`, `CONVENTIONS.upstream.md`) serve as a diagnostic hint — the skill may surface them as "a new version is available" — but the primary gate is the live-file content check. This is an AC for the implementing spec and must be tested against all combinations (both stale, README only stale, CONVENTIONS only stale, companions deleted but wording not updated). **Runtime gitignore check:** verify at startup that `.distill-temp-*` is covered by the live `.gitignore`; if not, enter read-only assessment mode.

6. **`source` field parsing is inconsistent.** The `source` field is free-form (`PR#42`, `ADR-0007`, `issue#13`, initiative slug). "3+ distinct sources" requires parsing these values into normalized identifiers; inconsistent formats may undercount. Mitigation: the spec defines a normalized form for the `source` field when `work-loop` captures entries. PR numbers are not available at capture time (learnings are captured before the PR is opened; direct merges never receive one). The required capture-time identifier is `<initiative-slug>/<sub-artifact>` (e.g., `INI-037/spec.md`, `INI-037/loop-2`, `INI-037/closeout`), where `<sub-artifact>` is the specific spec, loop iteration, or equivalent distinguisher within the initiative. A bare initiative slug (e.g., `INI-037`) is valid only when the initiative produces at most one capture; if two or more entries from the same initiative carry an identical source string, they count as **one** distinct source for Recurring-tier purposes, so a sub-artifact is required whenever multiple independent observations come from the same initiative. **Recurring counts normalize to initiative prefix:** when counting distinct sources for the Recurring tier, the skill strips the `/<sub-artifact>` suffix and counts by initiative prefix only — `INI-037/spec.md`, `INI-037/loop-2`, and `INI-037/closeout` all resolve to `INI-037` and count as one distinct source, not three. Three sub-artifacts from the same initiative do not satisfy the threshold; three distinct initiative prefixes (or initiative-free identifiers such as `PR-42` or `ADR-0007`) are required. Sub-artifacts are stored in the `source` field for traceability but do not inflate the Recurring count. The implementing spec must update work-loop's capture guidance to use the sub-artifact form. Entries from before the convention are treated as one distinct source each, which biases toward escalation. **Initiative-free fallback:** for captures outside any initiative context (one-off light-mode loops, direct merges with no active workspace), use a capture-time identifier without an initiative slug — for example, a spec path (`spec/my-feature/spec.md`) or a loop identifier (`loop/2026-08-03`). Initiative-free identifiers are not subject to initiative-prefix normalization: each distinct string counts as one distinct source for Recurring-tier purposes. The implementing spec must document the recommended initiative-free form.

**Key assumptions (falsifiable):**

- *The `session-start` hook injects all matching entries, including unretired superseded ones.* If the hook already filters superseded entries, the accumulation problem is less severe. This is falsifiable by reading `tools/hooks/session-start.py`. If false, the motivation for curation weakens (though deduplication and graduation remain valuable).
- *Three distinct sources is a useful empirical threshold.* If the repo's loop frequency is low, 3 sources may never be reached for genuinely recurring patterns. This is falsifiable after one quarter of use: if the Recurring escalation tier fires zero times for real patterns, the threshold should be lowered.
- *The `[knowledge]` section in `workspace.toml` does not need RFC-0069 seeding to function.* The section is optional; repos without it use defaults. A seed is useful but not required for correctness.

**Drawbacks:**

- `distill-knowledge` adds one more thing for the operator to review at initiative close. The `on_closeout` trigger is gated on `[knowledge]` section presence; opt out by removing the section. The default-on-when-section-present behavior still adds a step. Mitigated by the skill's short typical runtime (a few seconds on files under 500 entries) and the fact that a "nothing to distill" result requires zero review time.
- The skill's curation quality depends on the operator's judgment: near-paraphrase detection, scope-tightening proposals, and escalation tier assignments are all subject to operator confirmation. The skill is a structured prompt to a human, not an automated decision. This is a feature, not a bug — but it means the skill's value scales with how engaged the operator is.

---

## Evidence & prior art

**Spike / de-risk result:**

The live `docs/knowledge/patterns.jsonl` corpus was inspected directly: it contains 10 entries (K-0001 through K-0010), all with non-empty `source` fields following the form `PR#<name> / commit <hash>` or `docs/specs/<name> (RFC-NNN …)`. No entries have empty `source` fields. Earlier drafts referenced a seed entry with an empty source; that referred to `packs/core/seeds/docs/knowledge/patterns.jsonl` (the blank seed shipped to new adopters), not the live repo corpus.

**`source` field normalization.** The live corpus uses several formats: `PR#<name> / commit <hash>`, `PR #77`, `PR for <desc>`, and `docs/specs/<name> (RFC-NNN …)`. Counting commit hashes would treat multiple commits from one PR as independent sources, violating D3's distinct-PR/initiative intent. The normalization must be PR/initiative-level: extract the PR number or initiative slug as the canonical unit; treat unrecognized formats as one distinct source each (biases toward escalation). The implementing spec must define this normalization precisely and include regression tests against the K-0001–K-0010 source formats.

**Scope glob implementation.** `session-start.py`'s `_emit_knowledge` does NOT enumerate the working tree — it filters by a single caller-supplied scope string. Stale-scope detection requires a new working-tree walk; this is confirmed by reading `session-start.py::_emit_knowledge`.

**Repo precedent:**

- [`docs/knowledge/README.md`](../knowledge/README.md): defines the schema and the curation philosophy. This RFC adds a forward reference to the mutation gate; the full living-contract update is deferred to the implementing PR and ships alongside the skill.
- [RFC-0025](0025-work-loop-light-mode-and-risk-based-escalation.md): established the `Capture learnings` step in `work-loop`, which directs practitioner lessons to `patterns.jsonl`. `distill-knowledge` is the downstream curation layer.
- [RFC-0064 INI-001](0064-ini-001-ai-native-ecosystem.md): established `workspace.toml` as the coordination artifact; the `[knowledge]` section is an additive extension to its schema. INI-006 (the control-plane initiative) is cited as the deferred dependency for cadence scheduling.
- `tools/hooks/session-start.py`: the consuming surface that injects matching entries per session; the motivation for keeping the file clean.

**External prior art:**

No web search was available in this session. The design draws on two well-established practices:

- **Zettelkasten method (permanent-notes model):** the distinction between fleeting notes (raw observations, analogous to `session-scratch`) and permanent notes (curated entries in `patterns.jsonl`) is the conceptual model. Periodic promotion from fleeting to permanent is the curation gesture; periodic review of permanent notes for connections and graduation to a Folgezettel (follow-up card or external reference) maps to escalation.
- **Rule of three (refactoring heuristic):** "the first time you do something, just do it. The second time you do something similar, wince at the duplication, but do the duplicate thing. The third time you do something similar, refactor." The Recurring escalation threshold of 3 distinct sources is the knowledge-base analog.

No citations fabricated; both are pattern-level observations, not fetched links.

---

## Open questions

1. **Scope glob matching — six sub-decisions for the implementing spec.** Stale-scope retirement requires enumerating working-tree files and checking each entry's `scope` glob against the result. `session-start.py`'s `_emit_knowledge` does not do this; it filters by a caller-supplied scope string, never by walking the tree. Six open decisions: **(a) Placement:** `tools/knowledge_utils.py` is repo-local tooling and is not installed into an adopter's tree. The skill's stale-scope logic runs inside the LLM session (the SKILL.md instructs the agent), not via a Python module call — so the SKILL.md must describe the matching protocol verbally, not rely on a `tools/` import. A `tools/knowledge_utils.py` is still appropriate as a CI lint aid (wired to `tools/lint-knowledge.py`), but the implementing spec must not assume it is callable from the skill runtime. **(b) Semantics:** `session-start.py` uses `fnmatch.fnmatch` where `*` crosses path separators; the skill must specify the same semantics (not `pathlib.rglob`, which is segment-bounded). **(c) Comma-separated scopes:** K-0009 uses a comma-separated multi-scope value; `session-start.py::_emit_knowledge` compares `--scope` against the entire string (no splitting), so a scoped call never matches a multi-scope entry. The implementing spec **must** address both consumers: for stale-scope detection, split comma-separated values and treat each segment independently — an entry retires only if every segment matches zero files; for injection, either (i) curation normalizes the stored scope (removes comma-separated values from the file — for example by turning them into separate entries or choosing the primary segment), or (ii) `session-start.py::_emit_knowledge` is updated in a follow-on to split comma-separated scopes before matching. Both options must be explicitly decided; leaving the injection consumer unaddressed keeps the entry uninjected for all scoped calls. This applies to existing entries regardless of future capture normalization. The spec must record which option is chosen. **(d) Performance:** enumerating the working tree once per run and testing all entries against the cached path set avoids one `os.walk` per entry (500 entries = 500 full traversals without this). The implementing spec must specify single-walk caching. **(e) Tree-walk confinement:** `os.walk(followlinks=False)` does not protect against NTFS junctions on Windows. For every directory yielded by the walk, the implementing spec must resolve the directory's real path and verify it falls within the repo root before descending; directories that resolve outside the root must be pruned and excluded from the path set. This prevents outside-root file names from appearing in the stale-scope match list and from falsely keeping entries alive. Additionally, on Windows an NTFS junction pointing to an ancestor directory inside the repository has its resolved real path within the root — the root-confinement check passes — yet `os.walk(followlinks=False)` still descends the junction, creating an infinite ancestor cycle. The implementing spec must maintain a **visited-resolved-directory set**: before processing any directory's entries, compute `os.path.realpath` of the directory and check whether it is already in the visited set; if it is, skip the directory without descending. Add it to the set before descending. **(f) Gitignored-file exclusion:** the path set built from `os.walk` must exclude gitignored paths; ignored residue (e.g., `__pycache__`, build output) can persist under a deleted package's path after the package is removed, causing a false match that prevents 1c from proposing stale-scope retirement and making results differ between a developer checkout and a clean clone. The implementing spec must build the path set from git-tracked files plus non-ignored untracked files: use `git ls-files` for tracked files, and for untracked files filter through `git check-ignore --stdin` to exclude ignored paths. The single-walk cache must be post-filtered before any stale-scope glob matching runs. **Owner:** implementing spec. **Decide by:** spec authoring.

2. **`[knowledge]` section seeding.** RFC-0069 is Accepted (2026-07-22) with its implementing spec Shipped; D2 intentionally selected a minimal `[backlog]`-only seed and declared schema changes out of scope. The `[knowledge]` seeding question therefore routes to this RFC's own follow-on spec (`docs/specs/distill-knowledge/`), not RFC-0069. **Recommended default:** add a commented-out `[knowledge]` section to the `workspace.toml` seed via the implementing spec, following EXCLUDED_PATTERNS / REQUIRED_PLACEHOLDERS conventions established by RFC-0069. **Owner:** this RFC's implementing spec. **Decide by:** spec authoring.

---

## Follow-on artifacts

On acceptance:

- **New skill:** `packs/core/.apm/skills/distill-knowledge/SKILL.md` — the `distill-knowledge` skill per D1–D7. The SKILL.md frontmatter should include `metadata.boundaries` declaring `filesystem_read_untrusted` and `filesystem_write` as **informational metadata** for catalogue tooling (`docs/architecture/security.md` § Boundary metadata describes this as a future-enforcement signal, not a current runtime router). The security controls themselves — path confinement, data-not-instructions boundary, display escaping — must be implemented inside the skill body, not delegated to `metadata.boundaries` for enforcement.
- **`workspace-status` skill + backend update:** add an `on_closeout` offer to the closeout check — "Run `distill-knowledge` before closing out?" — gated on `[knowledge]` section presence in `workspace.toml`. Requires updating the backend workspace-toml serializer to extract and export whether the `[knowledge]` section is present in its JSON output (the skill reads backend JSON, not raw `workspace.toml`). Contract tests for: absent section, section present.
- **`workspace.toml` schema extension:** `[knowledge]` section (no configuration keys in this RFC) — acceptance criteria owned by the `distill-knowledge` implementing spec (`docs/specs/distill-knowledge/`). (`distill_on_closeout` and `distill_cadence` are deferred to future RFCs when a second caller needs to differ.) Three schema surfaces must be updated in parity and tested together: (a) `packs/core/.apm/skills/workspace-status/SKILL.md` absent-file initializer (the template shown to operators creating a new `workspace.toml` via `workspace-status`); (b) `guides/core/reference/workspace-toml-schema.md` (the reference doc listing all recognized sections and keys); (c) the seeded `workspace.toml` template (per OQ2 above). Repos initialized via `workspace-status` and repos seeded from the template must receive an identical schema surface for the `[knowledge]` section.
- **Convention and seed updates:** `docs/knowledge/README.md` (full living contract — update the schema table `id` row to show both formats; add D7 ID guidance: generation command `python3 -c "import secrets; print('K-' + secrets.token_hex(6))"`, uniqueness check, both-formats-accepted note), `packs/core/seeds/docs/knowledge/README.md` (adopter seed — must include the mutation-gate marker so fresh installs pass the contract validation gate), `docs/CONVENTIONS.md` (§ patterns.jsonl — revise "append-only" to "append-only for additions; `distill-knowledge` is the mutation gate"), and `packs/core/seeds/docs/CONVENTIONS.md` (same). All four must ship in the same PR as the skill.
- **`packs/core/.apm/skills/work-loop/SKILL.md` writer update:** update work-loop's knowledge-capture path to use the `<initiative-slug>/<sub-artifact>` source format convention.
- **`.gitignore` updates (live and seeded):** both the repo-root `.gitignore` and the seeded `.gitignore` must add `.distill-temp-*` so transient temp files from an interrupted run are never accidentally staged.
- **`tools/lint-knowledge.py` update:** (a) strengthen field-type checks: current `isinstance(..., str)` guards allow non-string `id` and `kind` values to pass CI undetected; the linter must explicitly reject records where any required field is not a string; (b) update check (h) to accept both ID formats: `K-\d{4,}` (legacy) and `K-[0-9a-f]{12}` (D7 random). Include tests for non-string `id`, non-string `kind`, and both ID format variants.
- **`agentbundle` catalogue leak guards:** add `K-[0-9a-f]{12}` to the adopter-clean blocklist patterns in `packages/agentbundle/agentbundle/catalogue_tooling/lint.py` (`_SEEDS_BLOCKLIST_PATTERNS`) and `catalogue_tooling/verify.py` (`_APM_SKILL_BLOCKLIST`), and mirror the pattern in `packages/agentbundle/tests/integration/test_install_snapshot.py` (`BLOCKLIST_REGEXES`). This prevents random knowledge IDs from leaking into adopter seeds. Requires an agentbundle patch release with Gate G compliance (version bump in `version.py` + `pyproject.toml`, `CHANGELOG.md` entry, `Engine-Change-RFC: RFC-0077` commit trailer). Co-land with the `tools/lint-knowledge.py` update above.
- **Pack version bump:** `packs/core/pack.toml` + `.claude-plugin/plugin.json` — minor version bump.
- **Pack README:** `packs/core/README.md` — add `distill-knowledge` to the skill roster with a one-line description.
- **Adopter guide (how-to):** `guides/_shared/how-to/curate-knowledge-patterns.md` — a short how-to covering when to run the skill, how to read the migration list, and how to act on each escalation tier. Audience: adopters managing a repo with `patterns.jsonl`.
- **Tech doc (maintainer guide):** `docs/guides/how-to/distill-knowledge-operations.md` — covers schema upgrade notes, the shared glob-match utility, and adding a new escalation tier. Audience: repo maintainers.
- **Marketing site (`web/`):** release note or feature card in the current-release section — "Knowledge curation: `distill-knowledge` keeps `patterns.jsonl` healthy and surfaces graduation candidates."
- **Changelog:** `docs/product/changelog.md` — `[Unreleased]` entry.
- **Pack evals:** `packs/core/pack.toml` `[pack.evals]` update — activation queries for `/distill-knowledge` and behavioral/judge evals per `packs/AGENTS.md` § Pack evals. Required for every new user-triggered `core` skill.
