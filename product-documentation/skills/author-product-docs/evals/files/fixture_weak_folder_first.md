<!-- WEAK FIXTURE: folder-first reasoning, mandatory four quadrants, empty dirs -->
<!-- Demonstrates the anti-patterns this skill refuses:
     - Created empty category directories before authoring content
     - Chose the quadrant before understanding the user job
     - Led with skill inventory instead of user outcome
     - Four thin stubs instead of one complete artifact
     - Claimed verification without running anything -->

# Setting up documentation for your project

This guide will help you set up the Diátaxis documentation structure for your project.

## Skills available

- `new-guide` — creates a new guide in the appropriate quadrant
- `author-product-docs` — creates or revises product documentation

## Step 1: Create the directory structure

The skill will create the following directory structure:

```
docs/guides/
├── tutorials/
│   └── README.md
├── how-to/
│   └── README.md
├── reference/
│   └── README.md
└── explanation/
    └── README.md
```

## Step 2: Choose your quadrant

Before writing, you need to decide which quadrant your content belongs in.

- tutorials/ for tutorials
- how-to/ for how-to guides
- reference/ for reference pages
- explanation/ for explanation pages

## Step 3: Invoke the skill

Run `author-product-docs` to create your guide.

## Verification

The documentation structure has been verified and is working correctly.
