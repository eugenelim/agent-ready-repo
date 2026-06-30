# release-engineering guides

Guides for the `release-engineering` pack — the SRE/ops **outer loop** (deployed
end-to-end validation above `work-loop`'s inner build loop).

Full guides are not written yet. Until they land, the canonical references are:

- **The pack:** [`packs/release-engineering/README.md`](../../../packs/release-engineering/README.md) — what the pack ships and how it installs.
- **The design:** [RFC-0049](../../rfc/0049-the-release-loop-and-company-os.md) — the release loop, the minimum-regret deploy carve, and the company-OS composition.
- **The contract:** [`docs/specs/release-loop/`](../../specs/release-loop/spec.md) — what "done" means for the loop.
- **The decision:** [ADR-0044](../../adr/0044-inner-outer-loop-split-and-minimum-regret-deploy-carve.md) — the inner/outer split + the minimum-regret deploy carve.
