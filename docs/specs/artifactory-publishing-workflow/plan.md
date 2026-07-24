# Plan: Artifactory Publishing Workflow

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Two tasks. The first authors the how-to guide — it is the load-bearing artifact and contains both the five-step prose sequence and the embedded workflow YAML template. The second finalizes the `docs/specs/README.md` entry (updating "Spec-mode review pending" → "Spec-mode review Clean" after adversarial review passes). No code is written; all verification is goal-based grep, existence checks, and a Python line-number ordering assertion for the YAML template. The riskiest part is sequence-order correctness: steps 4 (verify upload) and 5 (upload channel JSON) must appear in the right order in both the prose section and the embedded YAML template, and the rationale for step 5 being last must be explicit and unambiguous.

## Constraints

- RFC-0072 D1: mutable channel descriptor JSON points to an immutable versioned archive; the archive must be uploaded and verified before the descriptor is replaced.
- RFC-0072 D5: output layout is `dist/artifactory/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz` (and `.sha256`), channels at `…/<bundle>/channels/<channel>.json`.
- spec/package-catalogue-command: the guide names the command flags (`--root`, `--bundle`, `--release`, `--channel`, `--output`) and the three output files exactly as that spec defines them.
- RFC-0072 security constraints: no credentials in any file; `example.test` placeholders only; no TLS-bypass option; no bearer token in prose; credential references use `${{ secrets.* }}` syntax only.
- Diátaxis how-to format: task-oriented, imperative voice, ends with the user having achieved the goal.
- Header block format: `**Use this when:**`, `**Prerequisites:**`, `**Result:**` — matching the exact label form used by sibling guides in `docs/guides/_shared/how-to/`.
- No new code, no new runtime dependency, no new top-level directory.

## Construction tests

**Integration tests:** none — this spec is docs-only; there is no runtime surface to drive.

**Manual verification (AC3 prose ordering):** after authoring, read the guide top-to-bottom and confirm:
- Steps 1–5 are numbered in the correct order in the prose.
- Step 1 invokes `agentbundle package-catalogue`; step 5 uploads the channel JSON.
- The rationale for uploading channel JSON last is stated in guide prose, not only as a YAML comment.
- Every hostname matches `*.example.test`.
- No credential literal appears; every credential reference uses `${{ secrets.<NAME> }}` or `<placeholder>` form.
- The YAML template has `on:\n  workflow_dispatch:` and no `push:` or `schedule:` key.

**Scripted ordering assertion (AC15 YAML step ordering):** the T1 Tests section includes a Python one-liner that extracts line numbers for the verify step and the channel-JSON upload step from within the fenced YAML block and asserts strict ordering.

## Design (LLD)

### Design decisions

- **Embed the workflow YAML template as a fenced code block in the guide, not as a `.github/workflows/` file.** Keeping the template inside the `docs/` namespace prevents GitHub Actions from auto-executing it if the repository is forked. The guide instructs the operator to copy the block to `.github/workflows/publish-catalogue.yml` and substitute the required configuration values. Traces to: AC11, AC12.
- **Use JFrog CLI server-ID form (`jf config add` + `jf rt u --server-id`) rather than the older `--url/--password` flag form.** The server-ID form is the current JFrog CLI v2 recommended pattern; it avoids passing credentials as flag arguments (which appear in `ps` output and shell history). The template uses `${{ secrets.JFROG_ACCESS_TOKEN }}` to populate the server configuration step. Traces to: AC13, AC14.
- **Verify upload with `jf rt dl` + `sha256sum` comparison, not `jf rt search`.** `jf rt dl` downloads the artifact; `sha256sum` (or `shasum -a 256`) compares it against the local sidecar. This confirms the artifact is actually retrievable and intact at the target URL — not merely that Artifactory accepted the upload. The verify step runs after both uploads but before the channel JSON write. Traces to: AC15, AC16.
- **Sequence rationale is stated in prose, not only as a YAML comment.** The guide contains a dedicated callout (blockquote or warning admonition) that names the failure mode (clients fetch a descriptor pointing to a missing archive during the window between descriptor update and archive upload), not just an instruction to follow the order. Traces to: AC4.
- **Note the forthcoming-command dependency in Prerequisites.** `agentbundle package-catalogue` is introduced by spec/package-catalogue-command (ini-004 M5a), which is currently Draft. The guide's Prerequisites section names this dependency so operators can set expectations. Traces to: spec Boundary "note the dependency" rule.

### Behavior & rules

Five-step sequence (load-bearing — steps must appear in this order in both prose and YAML):

1. **Validate and package** — `agentbundle package-catalogue --root <catalogue-root> --bundle <bundle> --release <release> --channel <channel> --output dist/artifactory`. Produces three files locally; the channel JSON is written locally but not yet uploaded.
2. **Upload the immutable release archive** — `jf rt u` targeting `<repository>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz`. This file is immutable once published; Artifactory should be configured to refuse overwrites on the `releases/` path prefix.
3. **Upload the SHA-256 checksum sidecar** — `jf rt u` targeting `<repository>/catalogues/<bundle>/releases/<release>/catalogue-<release>.tar.gz.sha256`.
4. **Verify the upload** — download the archive from Artifactory, compute its SHA-256, compare against the local sidecar. Failure at this step aborts the workflow before the channel JSON is touched.
5. **Upload the channel descriptor JSON last** — `jf rt u` targeting `<repository>/catalogues/<bundle>/channels/<channel>.json`. This is the mutable pointer; uploading it is the atomic act that makes the new release "current" for all clients following the channel.

### Dependencies & integration

- **spec/package-catalogue-command:** the guide references `agentbundle package-catalogue` flags and output layout as defined in that spec. Implementation of this guide spec does not require that spec to be implemented first — the guide documents the intended workflow regardless.
- **spec/https-catalogue-channels:** the guide cross-references the channel descriptor schema. The guide describes what the channel JSON contains but does not redefine the schema — it links to the source spec.
- **spec/organization-artifactory-bootstrap:** the guide may reference the Layer 3 org bootstrap as the mechanism that distributes the channel URL to developers, but does not describe its implementation.

## Tasks

### T1: Author `docs/guides/_shared/how-to/publish-to-artifactory.md`

**Depends on:** none

**Touches:** `docs/guides/_shared/how-to/publish-to-artifactory.md`, `docs/specs/artifactory-publishing-workflow/spec.md`, `docs/specs/artifactory-publishing-workflow/plan.md`

**Tests:**
- AC1: `test -f docs/guides/_shared/how-to/publish-to-artifactory.md && test -s docs/guides/_shared/how-to/publish-to-artifactory.md` exits 0.
- AC2: `grep -c '^\*\*Use this when:\*\*\|^\*\*Prerequisites:\*\*\|^\*\*Result:\*\*' docs/guides/_shared/how-to/publish-to-artifactory.md` returns 3.
- AC3 (presence): `grep -c '^1\.\|^2\.\|^3\.\|^4\.\|^5\.' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥5; `grep -c 'package-catalogue' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1. AC3 ordering verified by manual QA read-through (see Construction tests).
- AC4: `grep -c 'channel.*last\|last.*channel\|uploaded last' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1; `grep -c 'missing\|window\|unavailable\|404\|not yet' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1.
- AC5: `grep -cE 'tar\.gz\.sha256|\.tar\.gz|channel\.json|<channel>\.json' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥3.
- AC6: `grep -c 'dist/artifactory' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1.
- AC7: `grep -c 'package-catalogue' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1.
- AC8: `grep -c 'https-catalogue-channels\|HTTPS Catalogue Channels' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1.
- AC9: `grep -c 'does not parse\|does not interpret\|does not validate\|stores and serves' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1.
- AC10: `grep -c 'secrets\.' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1.
- AC11: `grep -c '\`\`\`yaml' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1; `grep -c 'TEMPLATE' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1.
- AC12: `grep -c 'workflow_dispatch' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1; `grep -E '^[ ]*push:|^[ ]*schedule:' docs/guides/_shared/how-to/publish-to-artifactory.md` returns zero hits.
- AC13: `grep -cE 'jf rt u|jf rt upload|jf artifactory upload' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥2.
- AC14: `grep -c '\${{ secrets\.' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1; `grep -E 'Bearer [A-Za-z0-9+/=]{8,}|X-JFrog-Art-Api: [A-Za-z0-9]{8,}' docs/guides/_shared/how-to/publish-to-artifactory.md` returns zero hits.
- AC15 (ordering in YAML block): run the following Python assertion:
  ```python
  python3 -c "
  import re, sys
  text = open('docs/guides/_shared/how-to/publish-to-artifactory.md').read()
  m = re.search(r'\x60\x60\x60yaml(.*?)\x60\x60\x60', text, re.DOTALL)
  assert m, 'no yaml fenced block found'
  lines = m.group(1).splitlines()
  def first_line(pat):
      return next((i for i, l in enumerate(lines) if re.search(pat, l)), None)
  pkg  = first_line(r'package-catalogue')
  arc  = first_line(r'jf rt u.*tar\.gz($|[^.])')
  chk  = first_line(r'jf rt u.*\.sha256')
  vfy  = first_line(r'sha256sum|shasum')
  chn  = first_line(r'jf rt u.*channels/.*\.json')
  assert all(x is not None for x in [pkg, arc, chk, vfy, chn]), f'missing step: pkg={pkg} arc={arc} chk={chk} vfy={vfy} chn={chn}'
  assert pkg < arc < chk < vfy < chn, f'wrong order: pkg={pkg} arc={arc} chk={chk} vfy={vfy} chn={chn}'
  print('AC15 ordering OK')
  "
  ```
  Note: `chn` matches `jf rt u.*channels/.*\.json` (not bare `channels/`) so only the upload step-5 command matches, not any earlier comment referencing the channels path.
- AC16: `grep -cE 'sha256sum|shasum' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1.
- AC17 (URL-context hostname check): `grep -oE 'https?://[a-zA-Z0-9._-]+' docs/guides/_shared/how-to/publish-to-artifactory.md | sed 's|https\?://||' | grep -vE '(^|\.)example\.test$'` returns zero lines (all URL hostnames are `example.test` or subdomains thereof; non-URL dotted tokens like file extensions or `secrets.NAME` are not captured by this pattern).
- AC18: `grep -E 'Bearer [A-Za-z0-9+/=]{8,}|X-JFrog-Art-Api: [A-Za-z0-9]{8,}' docs/guides/_shared/how-to/publish-to-artifactory.md` returns zero hits.
- AC19: `git diff --name-status $(git merge-base HEAD origin/main)..HEAD -- docs/guides/_shared/how-to/ | grep -v '^A.*publish-to-artifactory'` returns zero lines (only the new file is added; no existing file is modified).
- AC20: `git diff --name-only $(git merge-base HEAD origin/main)..HEAD | grep -v '^docs/'` returns zero lines.
- AC22: `grep -c 'package-catalogue-command\|ini-004\|M5a' docs/guides/_shared/how-to/publish-to-artifactory.md` returns ≥1 (anchored to specific spec identifiers only; generic phrases excluded to prevent false-positives from unrelated prose).

**Approach:**
- Create `docs/guides/_shared/how-to/publish-to-artifactory.md`.
- Write the three-line header block: `**Use this when:**`, `**Prerequisites:**`, `**Result:**` — exactly matching the sibling guide format.
- Write a brief intro paragraph stating the ordering constraint.
- Add a `> **Warning:** …` callout naming the failure mode (descriptor replaced before archive is available — clients see a 404 on archive download during the window).
- Write the five numbered steps using the command forms from the Design section, with `artifactory.example.test` as the hostname.
- Note in Prerequisites that `agentbundle package-catalogue` ships with spec/package-catalogue-command (ini-004 M5a).
- Add a credentials section directing the operator to store credentials as environment secrets.
- Add a cross-references section linking to `spec/https-catalogue-channels` for the channel descriptor schema and to `agentbundle package-catalogue --help` for command flags.
- Add a subsection "What Artifactory does (and doesn't do)" explicitly stating it stores/serves but does not parse the pack layout.
- Embed the GitHub Actions workflow YAML template as a fenced `yaml` code block with a leading `# TEMPLATE: requires configuration before use` comment, `on:\n  workflow_dispatch:` trigger, `jf config add` credential step using `${{ secrets.JFROG_ACCESS_TOKEN }}`, and the five steps in order including a `sha256sum` verify step.

**Done when:** all AC1–AC22 goal-based checks pass (except AC3 ordering and AC21 which are addressed by manual QA and T2 respectively); manual QA read-through confirms prose step order (AC3 ordering) is correct; the Python AC15 ordering assertion script exits 0.

### T2: Finalize `docs/specs/README.md` entry

**Depends on:** T1

**Touches:** `docs/specs/README.md`

**Tests:**
- AC21: `grep 'artifactory-publishing-workflow' docs/specs/README.md | grep -c 'Spec-mode review Clean'` returns 1 (the specific row is updated); `grep 'artifactory-publishing-workflow' docs/specs/README.md | grep -c 'pending'` returns 0 (the `pending` marker is removed).

**Approach:**
- After adversarial review passes, update the `artifactory-publishing-workflow` row in `docs/specs/README.md`: change `Spec-mode review pending.` → `Spec-mode review Clean (adversarial 4 passes → 0).` in the row's notes column; also update `20 ACs` → `22 ACs`.

**Done when:** both AC21 assertions pass.

## Rollout

Documentation-only change. No infrastructure, no deployment sequencing, no feature flags, no migrations. The guide is live as soon as it is merged to the default branch. It does not require `agentbundle package-catalogue` (spec/package-catalogue-command) to be implemented before merging — the guide is intentionally authored ahead of the implementation, as docs-first documentation.

## Risks

- **Sequence order drift between prose and YAML template.** If the numbered steps in the guide and the YAML template steps diverge, an operator following one will see a different order than the other. Mitigation: AC15 uses a Python line-number ordering assertion; AC3 ordering is verified by manual QA; the manual Construction-tests checklist cross-checks both in one pass.
- **JFrog CLI syntax staleness.** JFrog CLI command syntax evolves across major versions. The guide uses the current JFrog CLI v2 server-ID form. Mitigation: the guide's YAML template includes a comment to check JFrog CLI documentation for the installed version; the template is clearly marked as a starting point.
- **AC15 ordering assertion is brittle to renamed YAML steps.** If the YAML template does not use the literal patterns the Python regex expects (`package-catalogue`, `jf rt u.*tar\.gz`, etc.), the assertion script fails. Mitigation: the Approach above specifies the literal command forms; the assertion patterns are derived from those forms.

## Changelog

- 2026-07-24: initial plan
- 2026-07-24: revised after adversarial review pass 1 — fixed AC2 header label (`Use this when:` not `Use it when:`); revised Testing Strategy to declare manual QA for AC3 prose ordering; added Python ordering assertion for AC15 (YAML step ordering); rewrote AC17 as positive hostname check; reconciled AC18 credential regex; fixed AC19/AC20 to use branch-base git diff; reframed T2 as "finalize README entry"; added AC21 for README review-status update.
- 2026-07-24: revised after adversarial review pass 2 — rewrote AC17 to URL-context hostname check (`grep -oE 'https?://…'`); fixed AC21 grep to be row-scoped (not global count); anchored Python AC15 `chn` pattern to `jf rt u.*channels/.*\.json` to avoid false-positive on early comments; added AC22 for forthcoming-command note; updated T2 test to match revised AC21; updated Done-when clause in T1.
- 2026-07-24: revised after adversarial review pass 3 — anchored AC22 grep to spec identifiers only (`package-catalogue-command|ini-004|M5a`); relaxed AC17 hostname filter to allow bare `example.test` (`(^|\.)example\.test$`); relaxed AC15 `arc` pattern to `tar\.gz($|[^.])` to handle lines ending on the archive filename.
