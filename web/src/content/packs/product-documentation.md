---
name: Product Documentation
pluginInstallable: true
scope: repo
tagline: "Stop shipping docs that disagree with your code: write and check every page, from README to release notes, against what the product actually does."
skills:
  - author-product-docs
installCommand: "agentbundle install --pack product-documentation"
docsUrl: /docs/guides/product-documentation/
journeyUrl: /journeys/product-documentation/
---

You want docs a newcomer can follow and that match what your library, CLI, API, app, or service does today. Paste this into your agent:

```
Audit this project's docs and tell me which stages of the reader journey are missing
```

You get a journey gap report: one row per reader stage, from discovering the product to contributing to it, each marked covered, partial, missing, or not applicable. Ask for a README, quickstart, how-to, reference, troubleshooting page, release notes, or migration guide, and the agent reads your code, manifests, and existing docs first. It writes where your repository already keeps docs, and it uses Diátaxis (tutorial / how-to / reference / explanation) as a page contract, not a directory structure. The `author-product-docs` skill does this work.
