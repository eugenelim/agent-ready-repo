---
pack: monorepo-extras
scope: repo
tagline: "Package scaffolding for monorepos."
prerequisitePacks: []
contract:
  useItWhen: "You're adding a new package to an existing monorepo and need it correctly scaffolded and wired from the start."
  youProvide: "The package name, a one-sentence description of its role, and the project's naming and build conventions."
  youReceive: "A package skeleton — directory layout, AGENTS.md, build configuration, and test wiring — committed and CI-verified."
  yourDecisions:
    - "Review the scaffolded package before first commit"
whatChanges: "After installing monorepo-extras, adding a new package to your monorepo runs through `new-package` — a structured scaffold that produces the correct directory layout, AGENTS.md, build configuration, and test wiring in one step. The alternative is doing it by hand from a peer package, which consistently misses the build system wiring."
skills:
  - name: new-package
    description: "Scaffolds a new package in a monorepo with the correct structure, AGENTS.md, and build configuration — wired to the project's existing conventions."
    humanTouches: 1
humanGates:
  - id: G-review
    globalGate: "G4"
    label: "Review the scaffolded package before first commit"
    trigger: "After new-package produces the package skeleton"
    duration: "5–10 minutes"
    whatToCheck:
      - "Is the package name and directory slug correct — consistent with the naming convention of existing packages?"
      - "Is the AGENTS.md populated with the package's actual purpose, commands, and any known gotchas — not the template placeholder text?"
      - "Is the build configuration wired correctly — does `npm run build` or the project's equivalent command work from the package root?"
      - "Are the test command and test directory correct — not pointing to a parent package's test suite?"
    whatGoodLooksLike: "A package that builds from its own root, has a meaningful AGENTS.md, and follows the naming and layout conventions of the existing packages in the monorepo."
    whatBadLooksLike: "A package whose AGENTS.md still reads 'TODO: describe this package.' Or a package whose test command runs the wrong test suite because the `jest.config.js` points to the wrong root. These are the two most common post-scaffold defects."
    consequence: "A scaffold that passes the G-review gate and then fails the first real build is the most expensive outcome — you've committed structural debt to the repo. The review gate is five minutes; fixing structural wiring after the first three PRs have extended the scaffolded pattern is much more expensive."
typicalSession:
  agentTurns: "3–5"
  humanTouches: 1
  wallClockMinutes: "10–20"
docsUrl: /docs/guides/monorepo-extras/
packUrl: /packs/monorepo-extras/
relatedJourneys:
  - core
  - governance-extras
---

### 1. Name and describe the new package

- **You provide:** the package name (using the project's naming convention — kebab-case, domain-qualified, etc.), a one-sentence description of its role and who uses it, and whether an existing package serves as the closest structural analogue.
- **Agent does:** activates new-package; asks for the package name and brief description; checks existing packages in the repo for the closest structural analogue.
- **Output:** a confirmed package name, role description, and structural analogue.

---

### 2. Scaffold, wire, and gate the package

- **Agent does:** produces the package skeleton — directory structure, package.json (or equivalent), AGENTS.md, build configuration, and test directory; populates AGENTS.md with the package name, description, and correct build and test commands.
- **You do:** at the G-review gate, check the two things most likely to be wrong: the AGENTS.md still has placeholder text, and the test command points to the wrong root; both are easy to catch here and expensive to fix after other packages have extended the scaffolded pattern.
- **You decide:** review the scaffolded package before first commit.
- **Output:** a reviewed, corrected scaffold ready for commit.

---

### 3. Commit and verify CI wiring

- **Agent does:** commits the scaffold, pushes the branch, and verifies that CI output shows the new package's tests running.
- **You do:** watch the CI run complete; if the new package's tests don't appear in CI output, the test wiring is incomplete — add the explicit CI step if needed (common cause: CI uses a hard-coded package list rather than a glob).
- **Output:** scaffold committed with CI wiring confirmed.
