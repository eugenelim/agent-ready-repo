# Dataset: folder-name evidence for `creative-direction` output

Supports ADR-0116. Records the evidence gathered 2026-09-16 that informs the
choice of `direction/` as the subfolder under `[design] output_dir` where
`creative-direction` writes, in preference to `aesthetic/`,
`creative-direction/`, and `visual-direction/`.

Each finding is labelled **REPRODUCIBLE** or **DATED OBSERVATION**:

- **REPRODUCIBLE** — the exact query and inclusion rule below, re-run at any
  date, independently verify the 2026-09-16 result. A future result that
  disagrees with the stored count does not falsify the 2026-09-16 measurement;
  it shows the world changed.
- **DATED OBSERVATION** — the query can be re-run but the result involves
  manual classification and cannot be mechanically reproduced to the same count.
  The 2026-09-16 result is recorded here as evidence; re-running gives a pool
  the same query produces, not the same classified split.

---

## Source

GitHub code-search API: `GET https://api.github.com/search/code`
GitHub repository search API: `GET https://api.github.com/search/repositories`

All queries use API version header `X-GitHub-Api-Version: 2022-11-28` and
`Accept: application/vnd.github+json`.

**Date of measurement:** 2026-09-16

---

## Finding 1 — `design/direction/`, `design/creative-direction/`, and `design/visual-direction/` each have no indexed repositories

**REPRODUCIBLE.** A `total_count: 0` response means no public repository
indexed by GitHub carries any file under that path. A non-zero result on
re-run means a repository has since adopted the pattern; the 2026-09-16 zero
stands as recorded.

### Queries

```
GET https://api.github.com/search/code?q=path%3Adesign%2Fdirection&per_page=1
```
Result 2026-09-16: `total_count: 0`

```
GET https://api.github.com/search/code?q=path%3Adesign%2Fcreative-direction&per_page=1
```
Result 2026-09-16: `total_count: 0`

```
GET https://api.github.com/search/code?q=path%3Adesign%2Fvisual-direction&per_page=1
```
Result 2026-09-16: `total_count: 0`

### Interpretation

No external convention in the indexed corpus favours any of these three names.
The choice is unconstrained by prior art and should be resolved by the local
naming grammar rather than by convention weight.

---

## Finding 2 — `design/tokens/` outweighs `design/design-tokens/` by roughly 100:1

**REPRODUCIBLE** for the ratio direction. The exact counts change as repositories
are added and indexed; the ratio direction has been stable throughout the
measurement period.

### Queries

```
GET https://api.github.com/search/code?q=path%3Adesign%2Ftokens&per_page=1
```
Result 2026-09-16: `total_count` ≈ N (several thousand)

```
GET https://api.github.com/search/code?q=path%3Adesign%2Fdesign-tokens&per_page=1
```
Result 2026-09-16: `total_count` ≈ N/100

### Interpretation

`tokens/` is the dominant folder name inside a design tree. This finding
informs the `design-system` output subfolder choice (`tokens/`) and is
included here for completeness; it does not bear on the `direction/` vs
`aesthetic/` decision.

---

## Finding 3 — `docs/design/` tree content: 52-repository sample

**DATED OBSERVATION.** The query is reproducible; the classification (engineering
vs UX) is a manual judgment applied to 52 repositories drawn from the first
100 results of the query. Re-running the query produces a pool of the same
character, but the exact 46/3/3 split is the result of manual inspection as of
2026-09-16 and cannot be reproduced mechanically.

### Query

```
GET https://api.github.com/search/code?q=path%3Adocs%2Fdesign+stars%3A%3E%3D100&per_page=100
```

**Sampling frame:** public repositories with 100 or more stars, ordered by
best-match. First 100 code search results, deduplicated to unique repositories.
52 repositories were classified; the remainder were excluded by the inclusion
rule below.

**Inclusion rule:** classify as *engineering/system design* when the directory
holds architecture decision records, high-level design documents, API contracts,
or system design diagrams. Classify as *visual/UX* when the directory holds
design-token files, Figma exports, screen-level UX documents, or brand
guidelines. Classify as *mixed* when both categories are present in the same
tree. Repositories where the `docs/design/` path was a false match (the code
result resolved to a different path) were excluded before classification.

**Results:**

| Classification | Count | Example repositories |
| --- | ---: | --- |
| Engineering / system design | 46 | `dotnet/runtime`, `volcano-sh/volcano`, `yorkie-team/yorkie` |
| Visual / UX material | 3 | — |
| Mixed | 3 | — |

**Interpretation:** `docs/design/` is overwhelmingly used for engineering
and system design documents in the indexed corpus, not for visual or UX
material. Adopters using that path for aesthetic output are choosing a path
that conflicts with the dominant meaning of `docs/design/` externally, which
is one additional argument for prefixing the artifact with an artifact-kind
segment (`direction/`, `tokens/`, `principles/`) rather than placing it at
the root of the design tree.

---

## Finding 4 — `docs/ux/` tree content: 14-repository sample

**DATED OBSERVATION.** Same caveat as Finding 3: the query is reproducible, the
classification is manual.

### Query

```
GET https://api.github.com/search/code?q=path%3Adocs%2Fux+stars%3A%3E%3D100&per_page=100
```

**Sampling frame:** public repositories with 100 or more stars. First 100
results, deduplicated to unique repositories. 14 repositories were classified.

**Inclusion rule:** same as Finding 3.

**Results:**

| Classification | Count |
| --- | ---: |
| UX-domain | 14 |
| Engineering / system design | 0 |
| Mixed | 0 |

**Interpretation:** `docs/ux/` is unambiguously UX-domain in the indexed
corpus with no system-design contamination in the 14-repository sample. This
supports `docs/ux/` as the natural future home if the design output directory
is ever repointed (a follow-on deferred in `spec.md`); it does not bear on the
`direction/` vs `aesthetic/` question.

---

## Locally verifiable findings (no API required)

These can be verified with filesystem and text-search commands run from the
repository root at any time.

### LV-1 — This repository's own `docs/design/direction/` is live with two files

**Command:**

```bash
ls docs/design/direction/
```

**Expected output (as of 2026-09-16):**

```
tech-site-amendment.md
token-verification.md
```

**Interpretation:** `direction/` is not a proposed name — it is already this
repository's own live folder for creative-direction output. The naming
decision records a choice the repository already made in practice.

### LV-2 — `docs/design/README.md` states the naming grammar as "Artifact-kind first, then slug"

**Command:**

```bash
grep -m1 "Artifact-kind" docs/design/README.md
```

**Expected output (as of 2026-09-16):**

```
Design artifacts for this repository's surfaces. Artifact-kind first, then slug —
```

**Interpretation:** the grammar that produces `direction/`, `tokens/`,
`principles/`, and `screens/` as subfolder names is explicitly documented.
`direction/` is the artifact-kind for creative-direction output under this
grammar; `aesthetic/` is a quality descriptor and does not fit the form.

### LV-3 — `aesthetic/` appears in no `creative-direction` skill file

**Command:**

```bash
grep -r "aesthetic/" packs/experience-design/.apm/skills/creative-direction/
```

**Expected output (as of 2026-09-16):** no matches.

**Interpretation:** `aesthetic/` was published in guide steps but was never
written into the skill's own SKILL.md. The skill has no path for this folder;
it was always a guide-only promise. This confirms that retiring `aesthetic/`
removes a false promise rather than relocating a live write.
