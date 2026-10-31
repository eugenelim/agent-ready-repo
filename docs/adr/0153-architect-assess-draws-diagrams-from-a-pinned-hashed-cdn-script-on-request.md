# ADR-0153: The architect-assess HTML report draws diagrams from one pinned, hashed CDN script, only on request

- **Status:** Accepted
- **Date:** 2026-10-31
- **Areas:** architect, security
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** spec `architect-assess-html-diagrams` (delivers this); spec `architect-assess-html-report` (its decision note listed the options); spec `cdn-sri-mermaid` (the exact-version, integrity-hash precedent)

## Decision summary

- **Decision:** `render_html.py --diagrams` adds two script elements to the report: Mermaid 12.2.0 from `https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js`, bound by the integrity hash `sha384-8xUhuLNMjW/cI2Dacg3DR4WliYznvIg0LVG1stctThKD/YVrJFI9TNCFxft5NYgp` with `crossorigin="anonymous"` and `referrerpolicy="no-referrer"`, then one inline script of this pack's own. Without the flag the page has no script and no network reference.
- **Because:** readers want drawn diagrams, and the repository already loads Mermaid this way elsewhere; a flag keeps the offline, no-network default for reports built from untrusted repository text.
- **Applies to:** the `architect-assess` skill's HTML renderer only.
- **Tradeoff accepted:** a `--diagrams` report contacts `cdn.jsdelivr.net` each time it is opened and tells that host the reader's IP address, the time, and browser details; it shows source blocks when offline.
- **Revisit if:** an advisory is published against the pinned version, the CDN host changes, or a vendoring or local-file route becomes practical.

## Context

The renderer shipped with Mermaid fences shown as labelled source blocks, and its decision note recorded three options: a pinned CDN with an integrity hash, an optional local file, or vendoring. The 1 MiB per-file cap on direct-source installs blocks vendoring. The pinned version is the `mermaid` version `docs-site/package.json` already pins, so the repository's npm audit covers it. The pinned file's bytes match the npm tarball's `dist/mermaid.min.js`, whose tarball integrity equals the `docs-site` lockfile value.

## Decision

- **D1:** Drawing is opt-in through `--diagrams`; the agent passes it only when the user asks for drawn diagrams.
- **D2:** The pinned version, URL, and hash are constants in `render_html.py`; a roster test keeps the version equal to the `docs-site` pin and the hash equal to the value in this record.
- **D3:** The integrity attribute binds the bytes. The policy names the exact URL in `script-src` beside the SHA-256 of the inline script, and holds no other script source; `style-src` stays one hash.
- **D4:** The inline script sets Mermaid's `securityLevel` to `strict` in pack code, refuses unsafe fences before drawing, and adds a drawn SVG's styles to the page only after checking that they are scoped to that SVG. Any failure leaves the fence as source.
- **D5:** A bump of the pinned version is its own change: take the file from the npm tarball, check the tarball's integrity against the lockfile, compare the bytes the CDN serves, and update the constants and this record together.

## Consequences

**Positive:**
- Reports show drawn diagrams without shipping third-party code in the pack.
- The default report is unchanged and offline.

**Negative:**
- A drawn report depends on a third-party host being reachable, and discloses the open to it.
- The hash value lives in two places, the constant and this record, kept equal by a test.

**Revisit if:** an advisory is published against the pinned version, or the CDN host changes.

## Confirmation

- **Mode:** lint/CI
- **Signal:** the pin-parity roster test passes, and the browser ledger of the diagrams spec records that the tarball's integrity equals the lockfile value and that its `dist/mermaid.min.js` SHA-384 equals the constant.
- **Owner:** eugenelim

## Alternatives considered

- **An optional local `--mermaid-js` file.** Rejected for now: the reader must install and hash a build; revisit if offline drawing is wanted.
- **Vendoring the build in the pack.** Rejected: 5.5 MB exceeds the 1 MiB install cap and needs its own advisory path.
- **Drawing by default.** Rejected: each opened report would contact the CDN without the reader asking.
