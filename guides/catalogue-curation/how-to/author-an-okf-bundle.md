---
title: Author and compile an OKF bundle
summary: Declare pack-local OKF knowledge, compile its portable router Skill, and verify that generated output and catalogue discovery are current.
pack: catalogue-curation
kind: how-to
---

# Author and compile an OKF bundle

**Use this when:** A pack owns a body of reference knowledge that should ship
with a portable router Skill.
**Prerequisites:** The `catalogue-curation` pack, Python 3.11+, and the catalogue
tooling requirements, including `pyyaml>=6.0`.
**Result:** Canonical OKF 0.2 source, a compiler-owned router Skill and manifest,
and a clean drift check.

Ask your agent:

> Add a reference-only OKF bundle named `delivery-practices` to the `engineering`
> pack, compile it, and check that the committed output is current.

`compile-okf` and the OKF metadata `agentbundle show` reports are **pre-release**
and repository-scoped: treat the profile, the generated layout, and the
`--format json` OKF fields as subject to change, and do not build external
tooling on them yet.

The boundary is deliberately narrow: pack-local, reference-only OKF 0.2
knowledge compiled at authoring time. The compiler does not fetch remote
content, execute bundle code, or turn OKF metadata into runtime authority.

## 1. Declare the bundle

Add one profile and one or more bundles to the owning pack's `pack.toml`:

```toml
[pack.metadata.okf]
profile = "agentbundle-okf/v1"

[[pack.metadata.okf.bundles]]
id = "delivery-practices"
path = "okf/delivery-practices"
"router-skill" = "delivery-practices-reference"
```

The bundle ID and router Skill name use lowercase kebab case. The path is
pack-relative, lives below `okf/`, and has no leading slash, `..`, or trailing
slash. Keep every bundle and its generated output in the same pack.

## 2. Write canonical concepts

Create the bundle root at `packs/engineering/okf/delivery-practices/`, and write
its `index.md` by hand with the profile version and the bundle-wide licence:

```markdown
---
okf_version: "0.2"
license: "Apache-2.0 OR MIT"
---
# Delivery practices
```

This file is permanent hand-authored source, not a first-run placeholder. The
compiler never creates or rewrites it: with the bundle root `index.md` absent,
both write and check mode stop at `OKF011 index.md root index is missing` with
exit `1`. Keep both frontmatter fields for the life of the bundle — `license`
is what catalogue discovery reads, and a bundle root without it fails
`agentbundle show` with `missing content license` even though compilation
succeeds.

The compiler's own managed indexes are written elsewhere, under
`.apm/skills/<router>/references/okf/`. Those are the wholly generated files;
this one is yours.

Create each canonical concept under `concepts/`. For example,
`packs/engineering/okf/delivery-practices/concepts/release-readiness.md` can
start like this:

```markdown
---
title: "release-readiness"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "catalogue-original"
boundaries:
  - filesystem_read_untrusted
---
# release-readiness

Use when a maintainer needs to decide whether a release candidate has enough
evidence to proceed.

## Checks

- Confirm the declared acceptance criteria are satisfied.
- Record the exact verification commands and outcomes.
```

Treat concept files, the bundle-root `index.md`, other bundle files, and
`[pack.metadata.okf]` as source. The compiler owns the generated `index.md`
files beneath `.apm/skills/<router>/references/okf/`, the router itself, and the
pack's `.okf-generated.json`. Never hand-edit those outputs; change the source
concept or declaration and compile again.

All bundle prose, code fences, includes, executors, remote references, and
unknown extensions remain inert data. A router may read its delivered reference
tree, but it receives no tools or network access from the bundle.

## 3. Compile the selected pack

From this catalogue's root, run write mode for only the pack you changed:

```bash
python3 packs/catalogue-curation/.apm/skills/compile-okf/scripts/compile_okf.py \
  --root . \
  --pack engineering
```

Write mode preflights ownership, renders twice to detect non-determinism, and
then replaces only the selected pack's managed OKF output. Inspect the diff as
one source-and-generated change: the declaration, concepts, indexes, router,
and `.okf-generated.json` belong together.

If the command reports `OKF010`, stop. A compiler-owned path no longer matches
its manifest and generated markers, so the compiler will not overwrite it.
Decide which of two things the path is, then compile again:

- **Still generated output.** Restore it from canonical source by letting the
  next write replace it.
- **Now hand-authored.** Hand the file over to its author by making
  `<!-- agentbundle-okf: router-handoff=author-owned -->` its first body line,
  immediately after the frontmatter. The compiler then leaves it alone instead
  of claiming it, and stops treating it as generated output to replace.

## 4. Prove generated output is current

Run the same compiler in read-only check mode:

```bash
python3 packs/catalogue-curation/.apm/skills/compile-okf/scripts/compile_okf.py \
  --root . \
  --pack engineering \
  --check
```

Exit status `0` means the committed tree matches canonical source. Status `1`
means an input, schema, content, security, path, collision, or ownership error —
including an absent bundle-root `index.md`, which is `OKF011` at exit `1` in
both modes. Status `2` means output drift or non-deterministic rendering.

Diagnostics begin with a stable `OKF001`–`OKF012` identifier and a path. That
path is catalogue-relative for output and ownership diagnostics
(`OKF011 packs/engineering/.apm/skills/...`) but bundle-relative for
source-validation diagnostics (`OKF003 concepts/release-readiness.md`). When a
pack declares more than one bundle, a source diagnostic does not name which
bundle it came from; compile one bundle's worth of changes at a time if that
ambiguity bites.

Before opening a change, also run the catalogue's normal verification:

```bash
agentbundle catalogue verify --root .
```

## 5. Check the discovery result

Inspect the pack through the same read surface used by catalogue consumers:

```bash
agentbundle show engineering --format json
```

Unlike steps 3 and 4, this command has no catalogue argument — `show --root`
only locates the install-state file used when the catalogue cannot be resolved.
`show` reads whichever catalogue your installation already resolves to, so
confirm you are inspecting the tree you just compiled before trusting the
output. An editable install of this catalogue resolves to it already; otherwise
point your source at it for the check and put the setting back afterwards,
rather than leaving a relative source in user-global config where it would
silently repoint every later command.

For a live catalogue, confirm that:

- `knowledge` contains the bundle ID, `okf_version: "0.2"`, router Skill,
  concept count, content licence, and digest;
- `skill_metadata` identifies the generated router, its source bundle path in
  `generated_from`, profile, digest, and boundaries; and
- the ordinary `skills` inventory contains the router Skill name.

`show` is read-only and never runs the compiler or pack code. Installed-state
fallback cannot reconstruct rich catalogue metadata, so `pack_metadata`,
`skill_metadata`, and `knowledge` are `null` there.

## Common variations

**More than one knowledge domain in a pack.** Add another
`[[pack.metadata.okf.bundles]]` entry with a unique ID, path, and router Skill,
then compile the pack once.

**A router name changes.** Update the declaration and compile. Stale generated
output is removed only when its manifest digest and generated markers still
prove compiler ownership; otherwise the command stops with `OKF010`.

**A procedure should execute.** Stop at the reference-only router. Procedure
projection requires a separate reviewed declaration and content-addressed
approval record; Playbook execution and runtime authority are outside this
authoring workflow.

For the surrounding catalogue contract and schema links, see
[Catalogue format](../../_shared/reference/catalogue-format.md).
