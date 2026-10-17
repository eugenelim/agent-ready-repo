/*
 * Offline intent graph view, organised around four session-start questions.
 *
 * Reads the one JSON data block in the page and builds the whole view with
 * createElement and textContent.  Record text is only ever placed in a text
 * node or in an attribute value, after the unsafe-character escape below, and
 * fixed tables are the only source of question, group, state, trust class and
 * next-step text.  No library, no build step, no network.
 */
  var SCHEMA = 'intent-navigation.view.v1';
  // A fixed literal.  A link is only ever built for a URL that starts with it.
  var GITHUB_PREFIX = 'https://github.com/';

  // Code points the text output escapes, as inclusive ranges.
  var UNSAFE_RANGES = [
    [0x00, 0x09], [0x0B, 0x0C], [0x0E, 0x1F], [0x7F, 0x9F],
    [0xAD, 0xAD], [0x61C, 0x61C], [0x180E, 0x180E],
    [0x200B, 0x200F], [0x202A, 0x202E], [0x2060, 0x2064],
    [0x2066, 0x2069], [0x206A, 0x206F], [0xFEFF, 0xFEFF],
    [0xFFF9, 0xFFFB], [0xE0000, 0xE007F]
  ];

  function isUnsafe(cp) {
    for (var i = 0; i < UNSAFE_RANGES.length; i++) {
      if (cp >= UNSAFE_RANGES[i][0] && cp <= UNSAFE_RANGES[i][1]) { return true; }
    }
    return false;
  }

  function escapeDisplay(value) {
    var s = String(value);
    var out = '';
    for (var ch of s) {
      var cp = ch.codePointAt(0);
      if (isUnsafe(cp)) {
        var hex = cp.toString(16).toUpperCase();
        while (hex.length < 4) { hex = '0' + hex; }
        out += '[U+' + hex + ']';
      } else {
        out += ch;
      }
    }
    return out;
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { escapeDisplay: escapeDisplay };
  }
  if (typeof document === 'undefined') { return; }

