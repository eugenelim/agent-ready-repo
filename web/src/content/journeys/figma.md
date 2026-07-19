---
pack: figma
scope: user
tagline: "Read and render Figma designs — files, frames, variables."
prerequisitePacks:
  - credential-brokers
whatChanges: "After installing figma, your agent can read Figma files, render frame images, query variables, post comments, and convert FigJam connector graphs to Mermaid diagrams — all through the Figma REST API using a credential resolved via credential-brokers. The token never reaches the model; it resolves in-process at invocation time."
skills:
  - name: figma
    description: "Reads Figma files, nodes, metadata, versions, comments, variables, and dev resources; renders frame images; posts comments; converts FigJam connector graphs to Mermaid diagrams."
    humanTouches: 1
humanGates:
  - id: G-credential
    globalGate: null
    label: "Confirm the Figma credential"
    trigger: "Before any Figma API call is made"
    duration: "3–5 minutes"
    whatToCheck:
      - "Is the Figma Personal Access Token configured in credential-brokers? (The skill will fail with an auth error if the credential is absent or expired.)"
      - "Does the token have read access to the target file? (Figma tokens can be scoped — a viewer token cannot post comments.)"
      - "Is the file URL or file key correct — not a prototype link or a community file the token can't reach?"
      - "If posting comments: does the token have edit access to the target file?"
    whatGoodLooksLike: "A valid token in credential-brokers, confirmed against the correct scope, and a file key the agent can resolve."
    whatBadLooksLike: "A token that worked on a different file but is scoped to a team the current file is not in. Or a prototype share link where the agent needs the original file link. Or a token that expired since the last session."
    consequence: "Figma API errors are opaque — 'access denied' doesn't tell you whether the token is invalid, expired, or scoped incorrectly. Confirming the credential before the session starts avoids a mid-session block that requires you to interrupt, reconfigure, and restart."
  - id: G-output
    globalGate: null
    label: "Review extracted design data before acting on it"
    trigger: "After the figma skill returns a frame render, variable set, or design spec"
    duration: "5–10 minutes"
    whatToCheck:
      - "Does the rendered frame match the design you intended to extract — not a stale version or a different component?"
      - "For variables: are the values the current published values, or draft values from an unpublished variable set?"
      - "For FigJam-to-Mermaid conversion: does the resulting diagram reflect the actual connector graph — not a partial subgraph?"
      - "For dev resources: are the CSS values from the correct frame, not a sibling component with similar naming?"
    whatGoodLooksLike: "A frame render that matches the Figma canvas, a Mermaid diagram that preserves all connector relationships, and variable values that match the published design system state."
    whatBadLooksLike: "A frame render from the wrong variant or state — because Figma component instances can look identical in the file tree but render differently. Or a Mermaid conversion that drops connector labels because they were on a layer the agent didn't traverse."
    consequence: "Design data extracted incorrectly gets used to build the wrong thing. A wrong color value from the wrong component variant ships as a production style. Verifying at this gate costs five minutes; fixing the downstream result costs a full implementation loop."
typicalSession:
  agentTurns: "3–6"
  humanTouches: 2
  wallClockMinutes: "10–25"
docsUrl: /docs/guides/figma/
packUrl: /packs/figma/
relatedJourneys:
  - experience-design
  - credential-brokers
---

## Stage 1 — Configure the credential

Before the first API call, you confirm the Figma Personal Access Token is configured in credential-brokers. The agent checks that the credential resolves and reaches the target file.

**You:** Run `credential-brokers` setup if this is the first session, or confirm the existing token is still valid. Name the file key or file URL you want the agent to work with. This is a one-time setup per service — once the token is in place, every subsequent figma session resolves it automatically.

---

## Stage 2 — Read the design artifact

With the credential confirmed, the agent invokes the `figma` skill. It fetches the file structure, navigates to the target frame or component, and returns the design data — rendered image, node properties, variable values, or connector graph, depending on what you asked for.

**You:** Watch the fetch complete. If the agent returns data from the wrong frame — because a component name matches multiple instances in the file — redirect with the specific node ID or frame path. Figma's file tree uses human-readable names that aren't always unique; the node ID is the authoritative identifier.

---

## Stage 3 — Review and use

The agent presents the extracted artifact — a rendered frame image, a CSS variable set, a Mermaid connector diagram, or a structured property dump. You review it at the G-output gate before passing it to the next step in your workflow.

**You:** Check that the extracted artifact matches the design you intended to capture. For FigJam diagrams, verify that all connectors and labels are preserved. For variable values, confirm they match the published (not draft) design system state. Pass the reviewed artifact to the next step — typically a design implementation task using the `experience-design` or `core` pack.
