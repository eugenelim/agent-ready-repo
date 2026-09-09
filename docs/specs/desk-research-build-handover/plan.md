# Plan: desk-research-build-handover

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** root [`AGENTS.md`](../../../AGENTS.md);
  [`docs/AGENTS.md`](../../AGENTS.md); [`web/AGENTS.md`](../../../web/AGENTS.md);
  [`docs-site/AGENTS.md`](../../../docs-site/AGENTS.md);
  [`docs/CONVENTIONS.md`](../../CONVENTIONS.md); the shipped
  [`install-to-ship-walkthrough`](../install-to-ship-walkthrough/spec.md), whose
  `install-to-ship walkthrough` suite this slice's cases sit beside.

## Approach

Add one handover entry to the pack README following the shape
`guides/architect/README.md:43` already ships, correct five mistyped link
targets, and turn one illustrative snippet from a link into code.

The link corrections point at existing files. The alternative — renaming the
files to match the links — would change published URLs and is refused by the
spec's Boundaries.

## Constraints

- Sites deploy under the `/agent-ready-repo` subpath; the canonical build order
  is `tools/build-site.py`, then `npm run build --prefix web`, then
  `npm run build --prefix docs-site` (`docs-site/AGENTS.md` § Build).
- `web/src/test/rendered-output.test.ts` runs only under `npm test --prefix web`;
  no `make` target invokes it. `tools/` suites run from the explicit file list at
  `Makefile:584`.
- `docs-site/src/content/docs/guides/` is generated. Edits go to `guides/`.
- Execution observations go to
  [`notes/verification-ledger.md`](notes/verification-ledger.md), never into this
  file once approved.

## Construction tests

All three cases live in `web/src/test/rendered-output.test.ts`, beside the
`install-to-ship walkthrough` suite. It already resolves `DOCS_ROOT`, emitted
pages, and `REPO_ROOT`, so AC2 can read authored Markdown from the same suite.

Design notes the implementer cannot infer:

- **AC1 must read the article body, not the document.** Starlight renders a
  site-wide sidebar on every guide page, and that sidebar *already* carries an
  anchor to `hand-an-intent-to-build` with the text "Hand an intent to build" —
  verified on the unchanged build, where the page holds exactly one such anchor
  and it sits outside `<main>`. A document-level query therefore passes before
  any edit is made. `<main>` is NOT a sufficient scope either: the emitted
  `<main>` also holds breadcrumbs, pagination, edit controls, and the docs
  footer. Scope to `.sl-markdown-content` — the container Starlight's
  `MarkdownContent.astro` wraps the page's own authored Markdown in, and the
  only occurrence of that class on the emitted page.

  **Assert the scope, not just the anchor.** The case must first require exactly
  one `.sl-markdown-content` on the page and then search only inside it, and must
  reject a matching anchor that has a `<details>` ancestor. An anchor inside a
  closed disclosure sits in the article body, binds the right text and target,
  and survives the deletion mutation — while the reader must find and open the
  disclosure first, which is not the "one click from the front door" the
  Objective promises. This is a different failure from the accepted CSS-
  concealment gap: that one needs a browser to detect, this one is visible in
  the emitted markup. Without
  that assertion the deletion mutation proves nothing about scoping: a verifier
  still scoped to `<main>` also passes the finished page and also fails when the
  README entry is deleted, because the chrome anchor lives outside `<main>`. The
  count assertion is also what makes a future Starlight rename fail loudly
  instead of silently matching nothing and passing on an empty scope —
  `docs-site/AGENTS.md` requires dependent contracts to be re-verified after a
  Starlight upgrade, and this is that contract.
- **AC1 binds text and target on one anchor.** Two independent assertions pass
  on a page where they belong to different elements.
- **AC2 reads inline links only, deliberately.** The criterion was narrowed to
  match what a regex can decide: a CommonMark grammar is not regex-shaped, and
  an "every link" claim built from two collectors is a coverage claim the slice
  cannot keep. The check strips fenced and indented code, collects inline
  `](target)`, drops absolute URLs, protocol-relative targets, `mailto:`, and
  bare `#fragment`, discards any `#fragment`, then resolves against the
  containing file's directory, accepting an existing file or a directory
  containing `README.md`. Query handling was removed from the criterion rather
  than left as an unexercised branch: the pack publishes no query-bearing link,
  so a verifier silently skipping `?` targets would pass any proof written for
  it. Stripping code first is what stops link-shaped text in
  a sample from being reported as a defect.
- The illustrative snippet at `run-a-research-project-into-an-rfc.md:93` becomes
  inline code. It must not become a link to `docs/rfc/0041-notes/research.md`:
  the example's filename is deliberately fictional, and pointing it at a real
  unrelated file would make the example wrong in a new way.
- **Mutation proofs, one per branch that could silently be dropped.** AC1:
  delete the README handover entry and require AC1 to fail — this is what proves
  the check reads the article body rather than the sidebar or the page chrome.
  AC2: four mutations, each killing a different wrong verifier — a plain missing
  `.md` target; a missing directory target; a fragment-bearing missing target
  (kills a verifier that never strips fragments); and a link to `how-to/`, an
  existing directory with no `README.md` (kills a verifier that accepts any
  existing directory). A single mutation leaves the other three verifiers alive,
  which is how the previous narrow scan passed.

  **Place each AC2 mutation in a different file, and none of them in
  `README.md`.** Use `tutorials/`, `how-to/`, `explanation/`, and `reference/`.
  Four mutations all made in `README.md` are killed by a verifier that reads
  only `README.md` and never walks the pack.

  **Traversal is guaranteed structurally, not by mutation count.** Spreading
  mutations across four directories still only proves the verifier reads *those
  four files*; a verifier holding a hard-coded five-file list survives it, and
  chasing that with one mutation per file regresses without end. Two
  requirements close it instead:

  1. The enumeration is a **recursive walk of `guides/desk-research/`** that
     collects every `*.md` it finds. No literal file list, and no per-directory
     enumeration that a new subdirectory would escape.
  2. A **fifth mutation creates a new Markdown file** in the pack containing one
     broken inline link, and requires AC2 to fail. A hard-coded or
     directory-limited verifier cannot have been written against a file that did
     not exist when it was written, so this kills the whole family of selective
     verifiers at once. Delete the temporary file afterwards by removing it, and
     confirm the pack's file count returns to its prior value.

## Durable-output map

| Spec durable output | Task | Evidence at closeout |
| --- | --- | --- |
| User-facing promise (pack README) | T1 | AC1, AC3 cases; AC1's deletion mutation proof is T2's |
| Current product truth (two pack pages) | T1 | AC2 case; its four mutation proofs are T2's |

## Design (LLD)

### Design decisions

- **The handover entry goes in the pack README**, the pack's front door and the
  file the brief's S2 row names as dead-ending. A link buried in a tutorial
  would not satisfy "from the pack's own front door".
- **AC2 is scoped to `guides/desk-research/`.** The 2026-09-09 walk found no
  unresolvable in-tree link elsewhere under `guides/`, but widening the standing
  check is a separate cut, recorded in the spec's Follow-ons.

### Failure, edge cases & resilience

A link to a directory is legitimate when that directory carries a `README.md`;
the pack README already links to sibling packs that way. AC2 accepts it rather
than reporting it.

## Tasks

### T1: correct the pack's navigation and add the handover entry

- **Depends on:** none
- **Mode:** goal-based check
- **Implements:** AC1, AC2, AC3
- **Tests:** the AC1, AC2, and AC3 cases above. T2 owns their mutation proofs.
- **Approach:** add the handover entry to `guides/desk-research/README.md`
  following the architect precedent; correct the three README targets and the
  two tutorial targets to the filenames that exist; convert the illustrative
  RFC-companion link to inline code.

### T2: prove each check can fail

- **Depends on:** T1
- **Mode:** goal-based check
- **Implements:** the criteria's evidence, not new behavior
- **Tests:** the six mutation proofs named in § Construction tests — AC1's
  README-entry deletion, AC2's four target mutations, and AC2's new-file
  traversal mutation.
- **Approach:** for each, apply the mutation by editing, rebuild only as far as
  the check requires, run the case, and record the observed failure. Restore by
  editing — never `git checkout`, `git reset`, or `git stash`, which would also
  discard the slice's real work and the peer changes in this tree. A case that
  stays green under its mutation is not evidence and blocks the task.

### T3: verify

- **Depends on:** T1, T2
- **Mode:** goal-based check
- **Implements:** all criteria
- **Tests:** none new.
- **Approach:** rebuild in canonical order, then run `npm test --prefix web`,
  the touched `tools/` suites, `make site-link-check`, and `git diff --check`.
  Confirm the new cases executed rather than skipped — the suite is
  `skipIf`-guarded, so a green run alone proves nothing. Record every command
  and result in the ledger.

## Rollout

Big bang, single PR; reversible by revert. No state, migration, flag, or
infrastructure.

## Risks

- **A non-inline link form enters the pack later and AC2 does not see it.**
  Accepted and stated in the spec: AC2 claims inline links only, the pack
  currently has 56 inline links and no other form, and the general case is the
  registered Follow-on detector.
- **A future in-tree link breaks and only the emitted fallback shows it.** AC2
  guards this pack at source; the standing emitted-side detector was cut and is
  a registered Follow-on. Accepted, and stated in the spec.

## Changelog

- 2026-09-09 — Initial plan drafted from brief slice S2, after the six broken
  links were measured across `guides/`.
- 2026-09-09 — Round 2. AC1 could pass with no implementation at all: the
  Starlight sidebar already carries a `hand-an-intent-to-build` anchor with
  matching text on every guide page, so a document-level query was green on the
  unchanged build. AC1 now reads `<main>` and carries a deletion mutation proof.
  AC2's claim was narrowed from "every relative Markdown link" to "every inline
  Markdown link", because the enumeration was regex-shaped while the pipeline is
  CommonMark; the pack's 56 links are all inline, and the general case is the
  Follow-on detector. The cut detector's Follow-on now cites a captured
  observation id and a `[backlog]` entry rather than prose alone.
- 2026-09-09 — Rescoped on owner decision after spec review: the standing
  emitted-fallback detector (former AC3) is cut to a Follow-on, leaving the
  handover entry plus the six link repairs. AC2's mechanism was enumerated more
  widely after directory targets and fragment-bearing targets were found to
  escape the previous `.md`-only scan. (Round 2 then narrowed the *claim* to
  inline links; see the entry above.) The hidden-anchor gap AC1 shares
  with its sibling is now stated in the spec rather than left implicit.
- 2026-09-09 — Round 3 (five findings, four from prior repairs). `<main>` was
  not a sufficient scope for AC1 either: the emitted `<main>` also holds
  breadcrumbs, pagination, edit controls and the docs footer, so AC1 now targets
  `.sl-markdown-content`. AC2's query branch was REMOVED from the criterion
  rather than given a fifth mutation, because the pack publishes no
  query-bearing link and any proof for that branch would have been
  unfalsifiable; a fourth mutation was added for an existing directory without a
  `README.md`, which kills a verifier accepting any directory. The five mutation
  proofs were described but assigned to no task, so T2 now owns them and T3 is
  verification. The cut detector's registration was a legacy non-dispatchable
  `{slug, source, summary}` record — the shape `workspace.toml`'s own header
  forbids — and is now a minimum intent plus a canonical `[backlog]` entry.
- 2026-09-09 — Round 4 (three findings, all from prior repairs; down from five).
  The AC1 deletion mutation could not distinguish `<main>` scoping from
  article-body scoping, because the chrome anchor sits outside `<main>` and the
  mutation fails for both — so the case must now assert exactly one
  `.sl-markdown-content` and search only inside it, which also turns a future
  Starlight rename into a loud failure rather than an empty scope. The four AC2
  mutations, if all placed in `README.md`, were killed by a verifier that never
  walks the pack; each is now assigned to a different subdirectory so the proofs
  test traversal rather than only target resolution. The spec's own Follow-on
  still said S3-S5 were unconfirmed after the brief and workspace were
  reconciled.
- 2026-09-09 — Round 5 (three findings). AC2's traversal proof was repaired
  structurally rather than by adding mutations: one mutation per directory only
  proves four files are read, and one-per-file regresses without end, so the
  enumeration is now required to be a recursive walk and a sixth mutation
  creates a *new* file the verifier cannot have been written against — which
  kills the whole selective-verifier family at once. AC1 now rejects an anchor
  inside a collapsed disclosure: it sits in the article body, binds text and
  target, and survives the deletion mutation, while the reader must open the
  disclosure first, which is not the promised one click. The follow-on intent
  overclaimed its detection signature as "precisely the fallback"; an authored
  absolute link into this repository's own guide tree emits the same shape, so
  the intent now states the ambiguity and carries the three disambiguation
  routes as an open question.
