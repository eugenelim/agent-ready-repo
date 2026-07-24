# Spec: Artifactory Publishing Workflow

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0072 (D1, D5), spec/package-catalogue-command
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

No canonical reference documents the correct upload sequence for publishing an AgentBundle catalogue to Artifactory. Without it, a CI operator can accidentally replace the mutable channel descriptor JSON before the immutable release archive is verified at its target URL — causing every client that fetches the descriptor in that window to 404 on the archive download. This spec delivers two documentation artifacts: (1) a Diátaxis how-to guide at `docs/guides/_shared/how-to/publish-to-artifactory.md` that defines the canonical five-step publish sequence (validate → upload archive → upload checksum → verify upload → upload channel JSON last), and (2) a disabled GitHub Actions workflow YAML template embedded in the guide that implements that sequence using JFrog CLI — clearly marked as a template requiring configuration before use and containing no real credentials or org endpoints. Artifactory stores and serves these artifacts but does not parse AgentBundle's pack layout; the guide states this boundary explicitly. This spec produces no code changes, no new Python modules, and no new runtime dependencies.

## Boundaries

### Always do

- Document the five-step sequence as a numbered list with steps in the exact order: (1) run `agentbundle package-catalogue` to produce archive + checksum + channel JSON locally, (2) upload the immutable release archive, (3) upload the SHA-256 checksum sidecar, (4) verify the upload by fetching the archive from Artifactory and comparing its SHA-256 against the sidecar, (5) upload the channel descriptor JSON last.
- Explain explicitly why channel JSON is uploaded last: the mutable channel pointer must not be replaced until the immutable archive is confirmed reachable and intact at its target URL; inverting steps 4 and 5 causes a window in which clients fetch a descriptor pointing to a missing or corrupt archive.
- State that Artifactory stores and serves the archive and channel descriptor unchanged — it does not parse, validate, or execute AgentBundle's pack layout (the `packs/`, `profiles/`, `docs/contracts/` hierarchy inside the archive).
- State that all Artifactory upload credentials must be supplied as environment secrets (GitHub Actions `${{ secrets.* }}` syntax or equivalent), never as literal values in workflow YAML or guide prose.
- Use `example.test` or `artifactory.example.test` for all hostnames in every example, code block, and command invocation in every file delivered by this spec.
- Cross-reference `agentbundle package-catalogue` as the producer of the three output files (`catalogue-<release>.tar.gz`, `catalogue-<release>.tar.gz.sha256`, `<channel>.json`).
- Cross-reference the channel descriptor schema (from `spec/https-catalogue-channels`) for the expected JSON structure at the channel URL.
- Write the guide in Diátaxis how-to format: task-oriented, starts with a goal/use-when statement, ends with a working published catalogue on Artifactory.
- Follow the header block format used by existing how-to guides in `docs/guides/_shared/how-to/`: the first three content lines after the title use the bold labels `**Use this when:**`, `**Prerequisites:**`, and `**Result:**` (matching `upgrade-packs.md` and sibling guides exactly).
- Note in the guide's Prerequisites section that `agentbundle package-catalogue` ships with `spec/package-catalogue-command` (ini-004 M5a); the guide documents the intended workflow regardless of whether that command is implemented yet.
- Name the exact `dist/artifactory/` output layout produced by `agentbundle package-catalogue`, matching RFC-0072 D5 and spec/package-catalogue-command.

### Ask first

- Adding a sixth or later step to the publish sequence.
- Changing the target path of the how-to guide (`docs/guides/_shared/how-to/publish-to-artifactory.md`).
- Adding upload instructions for an artifact server other than Artifactory (Nexus, S3, GitHub Packages, etc.).
- Changing the embedded workflow YAML template to use `curl` or a non-JFrog CLI upload mechanism.
- Promoting the workflow YAML template from a guide-embedded fenced code block to a live `.github/workflows/` file.
- Including a `schedule:` or `push:` trigger in the workflow YAML template.
- Adding a credential-storage section that recommends any storage mechanism other than CI/CD environment secrets.

### Never do

- Include a real Artifactory hostname (any hostname other than `example.test`, `artifactory.example.test`, or a subdomain thereof) in any file delivered by this spec.
- Include a literal credential value — a string matching `Bearer `, `X-JFrog-Art-Api:`, a literal token, password, or API key — in any file delivered by this spec. Credential references must use placeholder names (`${{ secrets.JFROG_TOKEN }}`) or the pattern `<your-token>`.
- Add a `push:` or `schedule:` GitHub Actions trigger to the workflow YAML template; the template must use `workflow_dispatch:` only so it cannot auto-execute if copied verbatim into `.github/workflows/`.
- Claim that Artifactory validates or interprets AgentBundle's pack layout — Artifactory is a generic artifact server.
- Introduce a new Python module, a new runtime dependency, or a new top-level repository directory.
- Upload the channel descriptor JSON before the archive is verified — this ordering error must be called out as a pitfall, not demonstrated.
- Skip the verify-upload step between uploading the checksum and updating the channel JSON.
- Reference any file path or CLI command that does not exist in the current codebase or that is introduced by a different spec without noting the dependency.

## Testing Strategy

This spec delivers documentation only. Two verification modes apply:

- **Goal-based checks** (primary mode): existence checks (`test -f <path>`), grep assertions for content presence, and structural pattern matches on the embedded workflow YAML. Used for: guide file existence (AC1), header labels (AC2), five-step keyword presence (AC3), callout/rationale presence (AC4), output paths (AC5, AC6), cross-references (AC7, AC8), Artifactory-as-server statement (AC9), credentials section (AC10), YAML fenced-block/TEMPLATE (AC11), YAML trigger (AC12), JFrog CLI usage (AC13), secrets syntax (AC14), verify-step presence (AC16), hostname restriction (AC17), credential literal absence (AC18), non-regression (AC19, AC20), README update (AC21), forthcoming-command note (AC22).
- **Manual QA** (for ordering): the load-bearing ordering constraint — that step 4 (verify) appears before step 5 (channel JSON) in both the prose section and the embedded YAML template — is verified by reading the guide top-to-bottom. Grep can verify that each step's keywords are present; it cannot reliably verify that the YAML steps appear in the correct serial order without a scripted line-number extractor. The plan's Construction-tests section records the manual read-through checklist; the plan's T1 also includes a Python ordering assertion for the YAML block that verifies step order programmatically (AC15). AC3 ordering (prose) is manual QA; AC15 ordering (YAML) uses both a presence grep and a scripted line-number check.

## Acceptance Criteria

<!-- Guide existence and structure -->
- [ ] AC1: `docs/guides/_shared/how-to/publish-to-artifactory.md` exists and is non-empty.
- [ ] AC2: The first three content lines after the title each begin with one of the bold labels `**Use this when:**`, `**Prerequisites:**`, `**Result:**` (exactly these strings, matching the sibling guides). Verified by `grep -c '^\*\*Use this when:\*\*\|^\*\*Prerequisites:\*\*\|^\*\*Result:\*\*'` returning 3.
- [ ] AC3: The guide contains at least five numbered list items (lines beginning `1.`, `2.`, `3.`, `4.`, `5.`) forming the publish sequence. Verified by goal-based grep for each step number (one or more per step). The prose step ordering (step 1 = package-catalogue, step 5 = channel JSON) and the fact that these five items form a single contiguous sequence are verified by manual QA read-through.
- [ ] AC4: The guide contains a sentence or callout that explicitly states the channel descriptor JSON is uploaded last. The rationale — that the mutable pointer must not be replaced until the immutable archive is verified reachable at its target URL — also appears in the guide.
- [ ] AC5: The guide names all three output files produced by `agentbundle package-catalogue`: `catalogue-<release>.tar.gz`, `catalogue-<release>.tar.gz.sha256`, and `<channel>.json` (or their parameterized equivalents using the `<bundle>`, `<release>`, and `<channel>` placeholder tokens).
- [ ] AC6: The guide names the output directory layout `dist/artifactory/catalogues/<bundle>/releases/<release>/` for the archive and sidecar, and `dist/artifactory/catalogues/<bundle>/channels/` for the channel descriptor.
- [ ] AC7: The guide contains a cross-reference to `agentbundle package-catalogue` identifying it as the tool that produces the three output files.
- [ ] AC8: The guide contains a cross-reference to the channel descriptor schema, identifying `spec/https-catalogue-channels` or the `HTTPS Catalogue Channels` spec as the source of the JSON structure.
- [ ] AC9: The guide contains a statement that Artifactory stores and serves the archive and channel descriptor without parsing or interpreting AgentBundle's pack layout (the `packs/`, `profiles/`, `docs/contracts/` hierarchy inside the archive).
- [ ] AC10: The guide contains a credentials section stating that Artifactory upload credentials must be supplied as environment secrets (GitHub Actions `${{ secrets.* }}` syntax or equivalent), not as literal values in workflow YAML or prose.

<!-- Workflow YAML template -->
- [ ] AC11: The guide contains a fenced code block with a `yaml` language tag holding a GitHub Actions workflow YAML template. The opening comment line of that block contains the text `TEMPLATE` and a note that configuration is required before use.
- [ ] AC12: The workflow YAML template does not contain a `push:` or `schedule:` key under `on:`. It uses `workflow_dispatch:` as the sole trigger.
- [ ] AC13: The workflow YAML template uses JFrog CLI (`jf rt u`, `jf rt upload`, or `jf artifactory upload`) for all upload steps; no `curl`-based upload appears in the template.
- [ ] AC14: Every Artifactory credential reference in the workflow YAML template uses GitHub Actions secrets syntax — `${{ secrets.<NAME> }}` — or an equivalent placeholder; no literal token, password, or API key value appears.
- [ ] AC15: The workflow YAML template steps appear in the five-step order: `agentbundle package-catalogue` → upload archive → upload checksum → verify upload → upload channel JSON. Ordering is verified by a Python line-number extraction script (see plan T1 Tests) that asserts the line number of the verify step is strictly less than the line number of the channel JSON upload step within the fenced YAML block.
- [ ] AC16: The workflow YAML template contains an explicit verify-upload step (containing the text `sha256sum` or `shasum`) between the checksum upload and the channel JSON upload. Verified by `grep -c 'sha256sum\|shasum' publish-to-artifactory.md` returning ≥1.

<!-- Security and placeholder enforcement -->
- [ ] AC17: Every URL-context hostname in any file delivered by this spec is `example.test` or a subdomain thereof. Verified by extracting only URL-embedded hostnames: `grep -oE 'https?://[a-zA-Z0-9._-]+' docs/guides/_shared/how-to/publish-to-artifactory.md | sed 's|https\?://||' | grep -vE '(^|\.)example\.test$'` returns zero lines. Non-URL dotted tokens (file extensions like `.json`, `.gz`, `.sha256`; variable references like `secrets.JFROG_ACCESS_TOKEN`) are not hostnames and are not in scope for this check.
- [ ] AC18: No literal credential string — a value matching `Bearer [A-Za-z0-9+/=]{8,}` or `X-JFrog-Art-Api: [A-Za-z0-9]{8,}`, i.e. a real-looking token not wrapped in `${{ secrets.` or `<` angle-bracket placeholder notation — appears in any file delivered by this spec.

<!-- Scope, non-regression, and meta -->
- [ ] AC19: No file under `docs/guides/_shared/how-to/` that existed before this spec is modified. Only `publish-to-artifactory.md` is added. Verified by `git diff --name-status $(git merge-base HEAD origin/main)..HEAD -- docs/guides/_shared/how-to/` showing only an `A` (add) entry for `publish-to-artifactory.md`.
- [ ] AC20: No new Python module, `pyproject.toml` dependency, or top-level repository directory is introduced by this spec. Verified by `git diff --name-only $(git merge-base HEAD origin/main)..HEAD` containing only paths under `docs/` and no paths under `packages/` or project root.
- [ ] AC21: The `artifactory-publishing-workflow` row in `docs/specs/README.md` contains `Spec-mode review Clean` (updated from `pending` after adversarial review passes). Verified by `grep 'artifactory-publishing-workflow' docs/specs/README.md | grep -c 'Spec-mode review Clean'` returning 1, and `grep 'artifactory-publishing-workflow' docs/specs/README.md | grep -c 'pending'` returning 0.
- [ ] AC22: The guide's Prerequisites section contains text noting that `agentbundle package-catalogue` ships with `spec/package-catalogue-command` (ini-004 M5a), so the guide's intended operator audience understands the command is introduced by a separate spec. Verified by `grep -c 'package-catalogue-command\|ini-004\|M5a' docs/guides/_shared/how-to/publish-to-artifactory.md` returning ≥1. (Generic terms like `not yet` or `forthcoming` are excluded from the check to avoid false-positives from unrelated prose.)

## Assumptions

- Technical: `docs/guides/_shared/how-to/` is the correct target directory for cross-pack how-to guides serving agentbundle maintainers. (source: existing guides in that directory; RFC-0072 § Affected surface names `docs/guides/`)
- Technical: JFrog CLI v2 `jf rt upload` (alias `jf rt u`) and `jf rt download` are the current official JFrog CLI commands for uploading to and downloading from an Artifactory generic repository. The flag form `--url`, `--user`, `--password` has been superseded by server-ID configuration (`jf config add`); the guide uses the server-ID form. (source: user confirmation 2026-07-24)
- Technical: The `dist/artifactory/` output layout produced by `agentbundle package-catalogue` is fully defined in RFC-0072 D5 and spec/package-catalogue-command AC3. The guide mirrors that layout without modification. (source: spec/package-catalogue-command AC3; RFC-0072 §D5)
- Technical: Python 3.11 stdlib-only constraint from RFC-0031 applies to code, not to documentation. This spec adds no code. (source: RFC-0031 Principle 3)
- Process: RFC-0072 is Accepted; D1 (mutable channel descriptor → immutable archive pattern) and D5 (CLI surfaces including `agentbundle package-catalogue`) are both ratified. (source: RFC-0072 status: Accepted)
- Product: The how-to guide targets CI operators and pack maintainers who own an org Artifactory fork, not end users installing packs. The guide assumes the operator has already configured the org Artifactory fork (`spec/organization-artifactory-bootstrap`) and produced a local dist layout (`spec/package-catalogue-command`). (source: user confirmation 2026-07-24)
- Product: Embedding the workflow YAML template as a fenced code block inside the guide (rather than as a separate `.github/workflows/` file) is the correct approach: it keeps the template in the documentation namespace and prevents GitHub Actions from auto-executing it if the repo is forked. (source: user confirmation 2026-07-24)
