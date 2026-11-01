# Diagram rendering in the HTML report: decided (2026-10-31)

**Chosen:** option 1, a pinned CDN with an integrity hash, as an opt-in `--diagrams` flag on `render_html.py`, using the `mermaid` version `docs-site` pins. The decision and its security posture are recorded in ADR-0153, and the build is specified in `docs/specs/architect-assess-html-diagrams/spec.md`. Drawing is opt-in; the default report stays offline. The notes below are the options as measured on 2026-10-30.

The HTML renderer in this spec shows Mermaid fences as labeled source blocks and runs no script. Drawing them in the browser needs a Mermaid build, and the options below were measured on 2026-10-30.

## Measured facts

- The `mermaid@12.2.0` npm tarball's `dist/mermaid.min.js` is 5,494,801 bytes.
- It contains the string `<!--`, so a rule that refuses to inline a script containing `<!--` would reject every report.
- It contains no `</script`.
- Direct-source installs cap one pack file at 1 MiB (`DIRECT_MAX_FILE_BYTES` in `packages/agentbundle/agentbundle/direct_source.py`). `find packs -path '*/.apm/*' -size +512k -type f` listed no file on 2026-10-30; rerun it before relying on this.
- `docs-site/package.json` pinned `mermaid` on 2026-10-30 (read it for the current value), and its lockfile carries the registry integrity value, so `tools/audit-npm.py` audits that version.
- The repository's existing HTML precedent loads Mermaid from a CDN with an exact version and an SRI hash (`docs/specs/cdn-sri-mermaid/spec.md`, pinned `mermaid@11.16.0`).

## Options

1. **Pinned CDN with SRI** — matches the precedent and keeps the pack small. A report makes an outside request every time it is opened and fails offline. Each report would tell the CDN host who opened it and when, and would fail offline, which weighs against it for reports built from untrusted repository text.
2. **Optional local file** — the renderer accepts `--mermaid-js <path>` for a Mermaid build the user installed from their own lockfile, checks its hash against the value they pass, inlines it under a script-hash CSP, and records the version and hash in the report notice. The pack ships no third-party code.
3. **Vendored in the pack** — blocked until the 1 MiB install cap is resolved, and it needs an ADR and an advisory path.

## Security requirements that apply to any option that runs script

`securityLevel: 'strict'` set only by pack code; refuse fences containing `%%{`, a frontmatter `config:` block, or `click … call|callback`; cap each fence at 64 KB; a CSP whose `script-src` lists only sha256 hashes (or the SRI-pinned origin) with every fetch directive `'none'`; browser QA that a planted script is blocked.
