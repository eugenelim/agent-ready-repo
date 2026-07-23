---
pack: converters
scope: user
tagline: "Document conversion — between every format your team uses."
prerequisitePacks: []
contract:
  useItWhen: "You need to convert a document between formats — PDF or DOCX to Markdown, Markdown to styled Office output, or Mermaid diagrams to images."
  youProvide: "The source file, the target format, and (for office output) the branded template to fill."
  youReceive: "A converted output file in the target format, with structure and styling preserved."
  yourDecisions:
    - "Review the converted output"
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

## 1. Invoke the converter

- **You provide:** the source file, the target format, and (for office output) the branded template to fill.
- **Agent does:** invokes the appropriate skill — `file-to-markdown` for a PDF or Office document, `markdown-to-docx` or `markdown-to-pptx` for output artifacts, `mermaid-renderer` for diagrams embedded in a Markdown file.
- **You do:** confirm the target format and, for office output, the template to use; if the source is a large PDF and you only need a specific section, say so before the agent converts the whole document.
- **Output:** a conversion job initiated with the correct skill and parameters.

---

## 2. Select the extraction tier

- **Agent does:** selects the appropriate capability tier — Tier 1 (no external tools, pure text extraction), Tier 2 (local tools like Pandoc or Poppler), or Tier 3 (agent vision for scanned or image-heavy documents) — and reports which tier was used and why.
- **You do:** confirm the tier makes sense for the document type; if the document is a scanned PDF and the agent selects Tier 1, redirect to Tier 3 or flag the document as needing OCR before extraction.
- **Output:** an extraction tier selected and applied to the source document.

---

## 3. Review the output

- **Agent does:** reports where the output lands and emits a brief summary of what it converted.
- **You decide:** open the output file at the G-output gate and review it — check for truncation, structure loss, and template application; if a section is missing, re-run with an explicit instruction to include it.
- **Output:** a verified conversion artifact ready to share or use in a downstream workflow.
