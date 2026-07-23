---
pack: figma
scope: user
tagline: "Read and render Figma designs — files, frames, variables."
prerequisitePacks:
  - credential-brokers
contract:
  useItWhen: "You need to read or extract design artifacts from a Figma file — frames, variables, connector graphs, or dev specs — to feed a design or build task."
  youProvide: "A Figma file URL or key and the artifact you want to extract."
  youReceive: "Extracted design data — rendered frame images, CSS variable sets, Mermaid connector diagrams, or structured property dumps."
  yourDecisions:
    - "Confirm the Figma credential"
    - "Review extracted design data before acting on it"
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

## 1. Configure the credential

- **You provide:** the target Figma file URL or key, and a Personal Access Token if not already in credential-brokers.
- **Agent does:** verifies the credential resolves via credential-brokers and can reach the target file.
- **You do:** run credential-brokers setup if this is the first session, or confirm the existing token is still valid — once in place, every subsequent figma session resolves it automatically.
- **You decide:** confirm the Figma credential at G-credential before any API call is made.
- **Output:** a confirmed credential resolving to the target file.

---

## 2. Read the design artifact

- **Agent does:** invokes the `figma` skill; fetches the file structure, navigates to the target frame or component, and returns design data — rendered image, node properties, variable values, or connector graph.
- **You do:** watch the fetch complete; if the agent returns data from the wrong frame, redirect with the specific node ID or frame path — human-readable names in Figma's file tree aren't always unique.
- **Output:** raw design data from the target frame or component.

---

## 3. Review and use

- **Agent does:** presents the extracted artifact — rendered frame image, CSS variable set, Mermaid connector diagram, or structured property dump.
- **You do:** check the artifact matches the intended design; for FigJam diagrams, verify all connectors and labels are preserved; for variable values, confirm they match the published design system state.
- **You decide:** review extracted design data at G-output before passing it to the next workflow step.
- **Output:** a reviewed design artifact ready to pass to the next workflow step.
