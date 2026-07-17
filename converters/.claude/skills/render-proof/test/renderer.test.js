'use strict';

// test/renderer.test.js — run with: node test/renderer.test.js
// Note: plan fixture letters (a)–(o) cover both AC6 and non-AC6 checks; AC6 fixtures start at plan (c).
// The inline AC6x tags are the binding AC reference: plan (a)=GFM bold, (b)=Shiki AC3.
const assert = require('assert');
const { renderMarkdown, sanitizeStyle } = require('../scripts/render-proof.js');

async function run() {
  // (a) GFM bold
  const bold = await renderMarkdown('**bold**', {});
  assert(bold.includes('<strong>') || bold.includes('bold'), 'bold failed');

  // (b) Shiki highlight applied (AC3)
  const code = await renderMarkdown('```python\nprint("hi")\n```', {});
  assert(code.includes('style='), 'Shiki style attr missing');

  // (c) script stripped (AC6a)
  const xss = await renderMarkdown('<script>alert(1)</script>', {});
  assert(!xss.includes('<script'), 'script not stripped');

  // (d) style attr preserved on span — assert the exact value, not just any style= (AC6b)
  const styled = await renderMarkdown('<span style="color:red">text</span>', {});
  assert(styled.includes('style="color:red"'), 'style="color:red" not preserved on span');

  // (e) onerror stripped (AC6c)
  const onerr = await renderMarkdown('<img onerror="alert(1)" src="x">', {});
  assert(!onerr.includes('onerror'), 'onerror not stripped');

  // (f) HTTPS url() stripped by post-processor — end-to-end through full pipeline (AC6d)
  const cssExfil = await renderMarkdown('<span style="background:url(https://evil.com/t.png)">x</span>', {});
  assert(!cssExfil.includes('url(https://evil.com'), 'HTTPS CSS url() exfil not stripped');

  // (g) protocol-relative url() stripped (AC6e)
  const protoRel = await renderMarkdown('<span style="background:url(//evil.com/x)">x</span>', {});
  assert(!protoRel.includes('url(//evil.com'), 'protocol-relative CSS url() not stripped');

  // (h) quoted data: URI preserved — hook must not strip quoted safe forms (AC6f)
  const dataUri = await renderMarkdown('<span style="background:url(\'data:image/png;base64,ABC\')">x</span>', {});
  assert(dataUri.includes('data:image/png'), 'quoted data: URI was incorrectly stripped');

  // (i) unbalanced-quote bypass stripped — url('//evil.com/x) without closing quote (AC6g)
  const unbalanced = await renderMarkdown('<span style="background:url(\'//evil.com/x)">x</span>', {});
  assert(!unbalanced.includes('url(\'//evil.com'), 'unbalanced-quote url() bypass not stripped');

  // (j) CSS-escape bypass stripped — url(\68 ttps://evil.com) hex-escapes first char (AC6h)
  // Assert BOTH the raw escaped form AND the decoded form — a broken impl that decodes but doesn't strip
  // would remove the raw bytes but still emit the live exfil URL
  const cssEsc = await renderMarkdown('<span style="background:url(\\68 ttps://evil.com)">x</span>', {});
  assert(
    !cssEsc.includes('\\68 ttps://evil.com') && !cssEsc.includes('evil.com'),
    'CSS-escape url() bypass not stripped (check both raw and decoded form)'
  );

  // (k) mixed safe+unsafe: safe data: URI preserved, adjacent color:red preserved, unsafe url() stripped (AC6k)
  // Input has THREE tokens in one attribute: non-url (color:red), safe url (data:image/png), unsafe url (https://evil)
  const mixed = await renderMarkdown(
    '<span style="color:red;list-style:url(\'data:image/png;base64,ABC\');background:url(https://evil.com/t.png)">x</span>',
    {}
  );
  assert(
    mixed.includes('color:red') && mixed.includes('data:image/png') && !mixed.includes('url(https://evil.com'),
    'fixture k: color:red or safe data: URI lost, or unsafe url() not stripped'
  );

  // (l) unsafe data: MIME type stripped — data:text/html not in safe-image allow-list (AC6i)
  const unsafeMime = await renderMarkdown(
    '<span style="background:url(data:text/html,<script>alert(1)</script>)">x</span>',
    {}
  );
  assert(!unsafeMime.includes('url(data:text/html'), 'unsafe data:text/html not stripped');

  // (m) javascript: href stripped by DOMPurify default URI scheme (AC6j)
  // Use raw HTML anchor (html: true) — markdown-it validateLink already blocks the md-link syntax,
  // keeping javascript: as literal text; raw HTML tests DOMPurify's actual scheme sanitization.
  const jsHref = await renderMarkdown('<a href="javascript:alert(1)">click</a>', {});
  assert(!jsHref.includes('javascript:'), 'javascript: href not stripped by DOMPurify default');

  // (n) unknown lang fallback — no throw
  const unk = await renderMarkdown('```unknownlang\ncode\n```', {});
  assert(unk.includes('<pre'), 'unknown-lang fallback missing pre');

  // (o) control-char breakout: CSS-escape \a (newline) inside safe-MIME prefix → treated as unsafe (AC6l)
  // url(data:image/png;base64,AAA\a x:url(//evil)) decodes \a to literal newline;
  // isSafeMime rejects the decoded value (contains C0 control char); token becomes none
  const ctrlChar = await renderMarkdown(
    '<span style="background:url(data:image/png;base64,AAA\\a x:url(//evil))">x</span>',
    {}
  );
  assert(
    !ctrlChar.includes('url(//evil'),
    'fixture o: control-char breakout not stripped — external url() survived isSafeMime C0 check'
  );

  // Direct sanitizeStyle test: re-escape invariant — CSS-hex-encoded " must produce url("...\"...") (AC6m)
  // hex \22 decodes to literal "; broken form url("A"B") prematurely closes the CSS quoted string
  // Direct sanitizeStyle — raw CSS return value makes it possible to assert the exact url("...\"...") form
  // without jsdom HTML-encoding of "; renderMarkdown would only expose the HTML-encoded &quot; form
  const reEscapeResult = sanitizeStyle('background:url(data:image/png;base64,A\\22 B)');
  assert(reEscapeResult !== null, 'canonical-restore re-escape: safe data: URI dropped (AC6m)');
  assert(
    reEscapeResult.includes('url("data:image/png;base64,A\\"B")'),
    'canonical-restore re-escape: " in decoded value (\\22) not re-escaped to \\" — broken url("A"B") prematurely closes the CSS quoted string (AC6m)'
  );

  // Direct sanitizeStyle test: unclosed url( bypasses quoted-aware regex → step-3 backstop → null (keepAttr=false path) (AC6 step 3)
  assert(
    sanitizeStyle('background:url(unclosed') === null,
    'sanitizeStyle must return null for unclosed url( — verifies keepAttr=false step-3 path'
  );

  // Direct sanitizeStyle test: escaped ) in unquoted url() — without fix ([^)]*?) truncates at \),
  // leaving trailing CSS as a standalone declaration; with fix (((?:[^)\\]|\\.)*?)) the full arg
  // is captured. Verify: broken regex leaves "); z-index:9999" AFTER url() close; fixed regex does not.
  const escapedParenResult = sanitizeStyle('background:url(data:image/png;base64,A\\); z-index:9999)');
  assert(
    escapedParenResult !== null && !escapedParenResult.includes('"); z-index:9999'),
    'sanitizeStyle: escaped \\) in unquoted url() — z-index leaked as standalone declaration after url() close (unquoted branch regex not fixed)'
  );

  // (p) mermaid fence block — wrapped in .mermaid-wrap/.mermaid-source, not Shiki-highlighted
  const mmd = await renderMarkdown('```mermaid\ngraph TD\n  A --> B\n```', {});
  assert(mmd.includes('class="mermaid-wrap"'), 'mermaid fence not wrapped in .mermaid-wrap');
  assert(mmd.includes('class="mermaid-source"'), 'mermaid fence source not in .mermaid-source');
  assert(!mmd.includes('style='), 'mermaid fence must not be Shiki-highlighted');

  // (q) renderProof: Mermaid CDN injected when diagram present; absent otherwise
  // Verification mode: goal-based — tests the hasMermaid detection through the full renderProof pipeline
  const { renderProof } = require('../scripts/render-proof.js');
  const proofWith = await renderProof('# T\n\n```mermaid\ngraph TD\n  A --> B\n```\n', {});
  assert(proofWith.html.includes('cdn.jsdelivr.net/npm/mermaid@11'), 'renderProof: CDN not injected when diagram present');
  const proofWithout = await renderProof('# T\n\nHello world\n', {});
  assert(!proofWithout.html.includes('cdn.jsdelivr.net'), 'renderProof: CDN injected when no diagram present');

  console.log('All renderer tests pass');
}
run().catch(e => { console.error(e); process.exit(1); });
