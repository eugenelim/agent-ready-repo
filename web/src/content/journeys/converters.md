---
pack: converters
scope: user
tagline: "Document conversion — between every format your team uses."
prerequisitePacks: []
whatChanges: "After installing converters, document conversion is a named operation with a verifiable output. `file-to-markdown` converts PDFs, DOCX, and images to clean Markdown. `msg-to-markdown` converts Outlook .msg and MIME .eml email. `mermaid-renderer` bakes Mermaid fence blocks to SVG or PNG. The four Markdown-to-* skills fill a named template and produce styled office output. `render-proof` renders a Markdown draft as an offline HTML proof for human review. A three-tier capability model ensures the floor works in locked-down environments."
skills:
  - name: file-to-markdown
    description: "Converts documents — PDF, DOCX, PPTX, XLSX, and images — to clean Markdown using a three-tier capability model (no-dep, local-tools, agent-vision)."
    humanTouches: 0
  - name: msg-to-markdown
    description: "Converts Outlook .msg and MIME .eml email to Markdown, preserving headers, body structure, and attachment inventory."
    humanTouches: 0
  - name: render-proof
    description: "Renders a Markdown file as a self-contained offline HTML proof artifact for human review — muted palette deliberately distinct from the publication look."
    humanTouches: 0
  - name: markdown-to-html
    description: "Produces a styled, self-contained HTML page from a Markdown source — shareable without external assets."
    humanTouches: 0
  - name: markdown-to-docx
    description: "Fills a branded Word template from a Markdown source — brand intact, no manual reformatting."
    humanTouches: 0
  - name: markdown-to-pptx
    description: "Fills a branded PowerPoint template from a Markdown source — slide structure derived from headings."
    humanTouches: 0
  - name: markdown-to-xlsx
    description: "Fills a branded Excel template from a Markdown source — tables and structured data mapped to sheets."
    humanTouches: 0
  - name: mermaid-renderer
    description: "Renders Mermaid fence blocks from a Markdown file to SVG or PNG — for tools that don't render Mermaid live."
    humanTouches: 0
humanGates:
  - id: G-output
    globalGate: null
    label: "Review the converted output"
    trigger: "After any converter skill reports completion"
    duration: "2–5 minutes"
    whatToCheck:
      - "Is all key content present — no silent truncation of large sections or long tables?"
      - "For office output: does the template apply correctly — brand, fonts, and structure intact, not plain Times New Roman?"
      - "For Markdown extraction: are code blocks, tables, and document structure preserved as intended?"
      - "For mermaid-renderer: does the rendered image match the diagram in the source — no missing nodes or broken edges?"
    whatGoodLooksLike: "An output that faithfully represents the source content in the target format, with structure and styling preserved — something you'd be comfortable sending to a stakeholder."
    whatBadLooksLike: "An output that passes the file-exists check but silently dropped a section or table. Or office output where the template wasn't applied — the agent reported success but the file opened in the wrong font."
    consequence: "Converter outputs are usually shared with stakeholders or used as input to another workflow. A silently incomplete conversion is discovered by the stakeholder, not the agent — and by then it's too late to re-run quietly."
typicalSession:
  agentTurns: "2–4"
  humanTouches: 1
  wallClockMinutes: "5–15"
docsUrl: /docs/guides/converters/
packUrl: /packs/converters/
relatedJourneys:
  - core
---

## Stage 1 — Invoke the converter

You name the source file and the target format. The agent invokes the appropriate skill: `file-to-markdown` for a PDF or Office document, `markdown-to-docx` or `markdown-to-pptx` for output artifacts, `mermaid-renderer` for diagrams embedded in a Markdown file.

**You:** Name the source file explicitly and confirm the target format. For office output, also name which template to use — the agent cannot discover your organization's brand template without you pointing to it. If the source is a large PDF and you only need a specific section, say so before the agent converts the whole document.

---

## Stage 2 — Tier selection (for file-to-markdown)

For document extraction, the agent selects the appropriate capability tier: Tier 1 (no external tools — pure text extraction), Tier 2 (local tools like Pandoc or Poppler), or Tier 3 (agent vision for scanned or image-heavy documents). It reports which tier was used and why.

**You:** Confirm the tier makes sense for the document type. If the document is a scanned PDF and the agent selects Tier 1, the extracted Markdown will contain garbled text — redirect to Tier 3 or flag the document as needing OCR before extraction.

---

## Stage 3 — Review the output

The agent reports where the output lands and emits a brief summary of what it converted.

**You:** Open the output file and review it at the G-output gate. The agent's report says "conversion complete" — what it cannot tell you is whether the resulting file is what you needed. Check for truncation, structure loss, and template application. If a section is missing, re-run with an explicit instruction to include it.
