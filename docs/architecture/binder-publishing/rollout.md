# Testing, CI, and open questions

> Test requirements, CI wiring, extension constraints, and unresolved decisions.
> Part of [binder publishing architecture](README.md).

## Test and eval layout

Tests live at `packs/binder-publishing/tests/skills/publish-binder/`, outside
the `.apm/` runtime boundary. Activation evals live at
`.apm/skills/publish-binder/evals/`.

## Unit tests

Unit coverage must include:

- schema versioning; unknown fields; `--allow-unknown-fields`; `[x-vendor]`
  passthrough; and rejection of `[policy] profile` and `[policy] shortcodes`;
- all content-root resolution branches; exit 6 for home, filesystem root, and
  ancestors of `~/.agentbundle/` or the installed pack; extension checks on every
  node read, including explicit paths;
- configuration precedence; identity normalization; case collisions; status-map
  normalization; deterministic ordering; weights; `before`/`after`; cycles;
  ambiguity; missing required and optional sources; duplicates; supersession;
  exclusions; duplicate IDs; colliding publication directories; and child-binder
  cycles;
- frontmatter discard-and-rebuild; executable-fence neutralization; byte-identical
  Mermaid fence bodies; D46 opening-delimiter annotation; Mermaid
  directive/click/callback rejection; and allowed label forms;
- staged-name determinism; link rewriting; line-offset mapping over generated,
  CRLF, and BOM input; asset allowlists; resource ceilings; path traversal;
  absolute paths; symlink escape; and self-path write refusal;
- emitted ordinals, including `null` for an unnumbered chapter and
  `data-ordinal` exclusion from title and search-index text;
- list-form renderer argv with `-f` as its only path element and mandatory
  `--strict`; child-environment allowlisting that excludes planted secrets;
- TOML injection rejection and emitter resilience; renderer-interpretable title
  rejection; source-H1 fallback for invalid labels; closed single-pass parameter
  substitution; and unresolved substitution failure;
- publication ownership, `publication-dir` confinement, heading-shift warnings,
  scan-exclusion handling, cross-device publication detection, exit-code mapping,
  and a golden index unchanged by `build` (invariant 16);
- renderer-version lookup through `importlib.metadata.version`, never
  `zensical.__version__`.

## Integration tests

Run Z1–Z4 regression assertions against one shared fixture. The built tree must
contain no remote subresource reference in `src`, stylesheet or preconnect
`href`, `@import`, or off-host `url()`.

Integration coverage must test renderer present, absent, and wrong version;
generated `zensical.toml`; nested part navigation; local search; previous/next
links; an untransformed Mermaid fence; vendored `mermaid.min.js` loaded before
the theme bundle; ANSI-stripped diagnostic mapping; and exit 7 before invoking
the renderer for a missing nav target or reported strict-build issue.

Test idempotent rebuilds, stale publication checks, pack-version changes,
interrupted builds, workspace-lock serialization, concurrent different binders,
publication-lock serialization, and cross-device replacement. Assert that the
published tree contains `binder-stamp.json` but not `binder-index.json`, that the
stamp contains no diagnostics, and that a source edit makes `check --published`
return 9.

Hash the content root before and after a build. Only `stage/`, the publication,
and its three named siblings may change. `clean` must remain confined.

Renderer-dependent tests skip with a clear reason when Zensical is absent. CI
installs Zensical and runs them as required tests.

## CI provisioning

The repository enumerates pack test roots. Add
`packs/binder-publishing/tests/` to the pytest invocation in
`.github/workflows/catalogue-tooling-ci-gates.yml`.

| Requirement | CI change |
| --- | --- |
| Pack tests | Add the pack test root to the pytest command. |
| Renderer | Install `zensical==0.0.53`. |
| Browser assertions | Provision a headless browser for Z6. |
| Egress assertions | Provision a Linux egress detector and a negative control that proves denial is effective. |

Z1–Z4 are the CI floor if browser or egress provisioning is unavailable. Do not
claim Z5 or Z6 as CI coverage until their instruments run in the workflow.

## Portability acceptance test

1. Create a clean temporary directory with no Git repository, `pack.toml`,
   `site.toml`, docs site, or catalogue files.
2. Write four Markdown files, including one portable Mermaid fence, and a
   `binder.toml` using explicit paths.
3. Expose the pack from a read-only projected copy.
4. Run `resolve` and compare `binder-index.json` with a byte-identical golden.
5. Run `build` and assert `index.html`, chapter HTML, local `search.json`, and a
   Mermaid block with source-identical fence content.
6. Assert every source SHA-256 and the pack tree hash are unchanged.
7. Assert that no path outside the temporary directory changed.
8. Assert that the built tree has no remote subresource request.

## Multi-pack fixture

Build one fixture from a frontmatter survey, frontmatter-free RFC and ADR with
`.binder.toml` sidecars, an architecture design containing Mermaid, a spec and
plan, and unannotated Markdown. A producer writes a template into the fixture
`recipes_dir`; `binder build` resolves it as an ordinary recipe.

The run must import nothing from a producing pack and open no path beneath any
other skill directory. Level-0, Level-1, and sidecar items must resolve in the
same binder.

## Accessibility smoke checks

Parse rendered HTML to require an `alt` attribute on every image, `<html lang>`,
a skip link, focus-visible theme styling, and non-skipping headings except a
recorded H6 clamp. Empty image alt text is valid and recorded in diagnostics.

Static Mermaid checks require compiler-owned, HTML-escaped `data-a11y-name` on
each named diagram and reject `%%{` and newlines in that value. The static check
must compare attribute presence with `renderer-plan.json`; it must not claim an
absent derivable name is valid. V1 names diagrams by ordinal only. D46 requires
the theme to lift those attributes into the rendered SVG; Z6 verifies the
reader-visible result in a browser. If the vendored bundle fails, the fence source
remains visible as preformatted text.

## Activation evals

`evals/eval_queries.json` covers positive binder requests and near misses routed
to `markdown-to-html`, `render-proof`, `mermaid-renderer`, and
`architect-design`. Negative activation cases are required because neighbouring
converter skills overlap on Markdown rendering.

## Safe extension points

Additional renderers, output formats, selector expressiveness, overlay semantics,
child binders, artifact-kind and status vocabularies, producer declarations, site
integration depth, and theme customization may extend the design without changing
the v1 core contract.

## Open questions

- **U2:** Confirm that the pack belongs within the Charter domain.
- **U3:** Confirm a new `binder-publishing` pack rather than a `converters` skill.
- **U4:** Confirm the pack name `binder-publishing` and skill name `publish-binder`.
- **U9:** Confirm the default publication directory, currently `build/binders`.
- **U10:** Confirm whether a content-root `binder.toml` is the argument-less build default.
- **U11:** Resolve the `.apm/shared-libs/` guidance conflict before fixing the pack shape.
- **U12:** Resolve the `agentbundle-layout.toml` schema/appender mismatch before documenting adopter configuration.
- **U13:** Ratify the exact alpha Zensical pin for the published binder contract.
