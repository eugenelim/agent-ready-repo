---
name: Figma
scope: user
tagline: "Read and render Figma designs — files, frames, variables."
skills:
  - figma
installCommand: "agentbundle install --pack figma --scope user"
docsUrl: /docs/guides/figma/
journeyUrl: /journeys/figma/
---

Figma installs a credentialed CLI primitive that reads from the Figma REST API: files, nodes, metadata, versions, comments, variables, and dev resources. It renders frame images, posts comments, and converts FigJam connector graphs to Mermaid diagrams. Requires a Figma Personal Access Token resolved via `credential-brokers`.
