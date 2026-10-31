/*
 * Draws the Mermaid fences the renderer marked for drawing. The page's policy allows this
 * file by hash, so it is plain script with no module syntax. Every failure leaves the fence
 * as source and says so on its label; nothing here trusts the diagram text, Mermaid's output,
 * or the page's own element ids.
 */
(function () {
  'use strict';

  var FAILED_LABEL = 'Diagram source (not drawn)';
  var SVG_ELEMENTS = [
    'svg', 'g', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon',
    'text', 'tspan', 'defs', 'marker', 'title', 'desc', 'clipPath', 'filter',
    'feDropShadow', 'linearGradient', 'stop', 'symbol'
  ];
  var GROUPING_RULES = ['CSSMediaRule', 'CSSSupportsRule', 'CSSLayerBlockRule', 'CSSContainerRule'];
  var LEAF_RULES = ['CSSStyleRule', 'CSSKeyframesRule', 'CSSKeyframeRule'];
  var BANNED_PROPERTIES = [
    'position', 'inset', 'top', 'right', 'bottom', 'left', 'float', 'transform', 'z-index',
    'translate', 'rotate', 'scale', 'offset', 'offset-path', 'offset-distance',
    'offset-position', 'margin', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left'
  ];
  var KEYFRAME_NAMES = ['dash', 'edge-animation-frame'];

  function blocks() {
    return Array.prototype.slice.call(document.querySelectorAll('.diagram.diagram-drawn'));
  }

  function fail(block, ids) {
    var label = block.querySelector('.diagram-label');
    if (label) {
      label.textContent = FAILED_LABEL;
    }
    ids.forEach(function (id) {
      var left = document.getElementById(id);
      if (left && left.parentNode) {
        left.parentNode.removeChild(left);
      }
    });
  }

  function mermaidReady() {
    var lib = window.mermaid;
    return Boolean(lib) && typeof lib.initialize === 'function' && typeof lib.render === 'function';
  }

  function sheetsSupported() {
    return typeof CSSStyleSheet === 'function' && 'adoptedStyleSheets' in document;
  }

  function propertiesAllowed(rule) {
    var declarations = rule.style;
    if (!declarations) {
      return true;
    }
    for (var i = 0; i < declarations.length; i += 1) {
      if (BANNED_PROPERTIES.indexOf(declarations[i]) !== -1) {
        return false;
      }
    }
    return true;
  }

  // Splits at the commas the CSS parser splits at: quoted text and escaped characters are
  // data. Returns null when the list cannot be split with certainty.
  function selectorList(text) {
    var depth = 0;
    var quote = '';
    var parts = [];
    var current = '';
    for (var i = 0; i < text.length; i += 1) {
      var char = text.charAt(i);
      if (char === '\\') {
        current += char + text.charAt(i + 1);
        i += 1;
        continue;
      }
      if (quote) {
        if (char === quote) {
          quote = '';
        }
        current += char;
        continue;
      }
      if (char === '"' || char === "'") {
        quote = char;
      } else if (char === '(' || char === '[') {
        depth += 1;
      } else if (char === ')' || char === ']') {
        depth -= 1;
      }
      if (char === ',' && depth === 0) {
        parts.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    if (quote || depth !== 0) {
      return null;
    }
    parts.push(current.trim());
    return parts;
  }

  function selectorsConfined(parts, id) {
    var root = '#' + id;
    return parts.every(function (selector) {
      if (selector.indexOf('~') !== -1 || selector.indexOf('+') !== -1) {
        return false;
      }
      if (selector.indexOf(root) !== 0) {
        return false;
      }
      var next = selector.charAt(root.length);
      return next === '' || next === ' ' || next === '>';
    });
  }

  // Only the outer svg takes part in page layout, and no HTML element can sit inside the
  // drawing, so a positioning property matters on the root rule and on keyframes alone.
  function targetsTheRoot(parts, id) {
    return parts.some(function (selector) {
      return selector === '#' + id || /(^|[ >])svg$/.test(selector);
    });
  }

  function ruleAllowed(rule, id) {
    var kind = rule.constructor && rule.constructor.name;
    if (GROUPING_RULES.indexOf(kind) !== -1) {
      return Array.prototype.every.call(rule.cssRules, function (inner) {
        return ruleAllowed(inner, id);
      });
    }
    if (LEAF_RULES.indexOf(kind) === -1) {
      return false;
    }
    if (kind === 'CSSStyleRule') {
      if (rule.cssRules && rule.cssRules.length > 0) {
        return false;
      }
      var parts = selectorList(rule.selectorText);
      if (!parts || !selectorsConfined(parts, id)) {
        return false;
      }
      return targetsTheRoot(parts, id) ? propertiesAllowed(rule) : true;
    }
    if (kind === 'CSSKeyframesRule') {
      if (KEYFRAME_NAMES.indexOf(rule.name) === -1) {
        return false;
      }
      return Array.prototype.every.call(rule.cssRules, function (inner) {
        return ruleAllowed(inner, id);
      });
    }
    return propertiesAllowed(rule);
  }

  function buildSheet(css, id) {
    if (/@import/i.test(css)) {
      return null;
    }
    var sheet = new CSSStyleSheet();
    sheet.replaceSync(css);
    var ok = Array.prototype.every.call(sheet.cssRules, function (rule) {
      return ruleAllowed(rule, id);
    });
    return ok ? sheet : null;
  }

  function referencesOnlyTheDocument(value) {
    var matches = value.match(/url\([^)]*\)/gi) || [];
    return matches.every(function (match) {
      return /^url\(\s*['"]?#/i.test(match);
    });
  }

  function ownsId(value, id) {
    return value === id || value.indexOf(id + '-') === 0 || value.indexOf(id + '_') === 0;
  }

  function prefixIds(elements, id) {
    var renamed = {};
    elements.forEach(function (element) {
      var current = element.getAttribute('id');
      if (current !== null && !ownsId(current, id)) {
        renamed[current] = id + '-' + current;
        element.setAttribute('id', renamed[current]);
      }
    });
    elements.forEach(function (element) {
      Array.prototype.slice.call(element.attributes).forEach(function (attribute) {
        var value = attribute.value.replace(
          /url\(\s*(['"]?)#([^'")\s]+)\1\s*\)/g,
          function (whole, quote, target) {
            return Object.prototype.hasOwnProperty.call(renamed, target)
              ? 'url(' + quote + '#' + renamed[target] + quote + ')'
              : whole;
          }
        );
        if (value !== attribute.value) {
          element.setAttribute(attribute.name, value);
        }
      });
    });
  }

  function cleanSvg(svgText, id) {
    var parsed = new DOMParser().parseFromString(svgText, 'image/svg+xml');
    var root = parsed.documentElement;
    if (!root || root.localName !== 'svg' || parsed.getElementsByTagName('parsererror').length) {
      return null;
    }
    if (root.getAttribute('id') !== id) {
      return null;
    }
    var css = '';
    Array.prototype.slice.call(root.getElementsByTagName('style')).forEach(function (node) {
      css += node.textContent + '\n';
      node.parentNode.removeChild(node);
    });
    var elements = [root].concat(Array.prototype.slice.call(root.getElementsByTagName('*')));
    for (var i = 0; i < elements.length; i += 1) {
      var element = elements[i];
      if (SVG_ELEMENTS.indexOf(element.localName) === -1) {
        return null;
      }
      element.removeAttribute('style');
      var attributes = Array.prototype.slice.call(element.attributes);
      for (var j = 0; j < attributes.length; j += 1) {
        var name = attributes[j].name.toLowerCase();
        if (name === 'href' || name === 'xlink:href' || name === 'src' || name.indexOf('on') === 0) {
          return null;
        }
        if (!referencesOnlyTheDocument(attributes[j].value)) {
          return null;
        }
      }
    }
    prefixIds(elements, id);
    return { root: root, css: css };
  }

  function place(block, root) {
    var holder = document.createElement('div');
    holder.className = 'diagram-render';
    holder.setAttribute('role', 'region');
    holder.setAttribute('tabindex', '0');
    var source = block.querySelector('.source-scroll');
    var named = source ? source.getAttribute('aria-label') : null;
    holder.setAttribute(
      'aria-label',
      named && named.indexOf('Source: ') === 0 ? 'Drawn diagram: ' + named.slice(8) : 'Drawn diagram'
    );
    holder.appendChild(document.importNode(root, true));
    block.insertBefore(holder, source);
  }

  async function drawAll() {
    var found = blocks();
    if (!found.length) {
      return;
    }
    if (!mermaidReady() || !sheetsSupported()) {
      found.forEach(function (block) {
        fail(block, []);
      });
      return;
    }
    var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    try {
      window.mermaid.initialize({
        startOnLoad: false,
        securityLevel: 'strict',
        suppressErrorRendering: true,
        htmlLabels: false,
        maxTextSize: 50000,
        maxEdges: 500,
        theme: dark ? 'dark' : 'neutral'
      });
    } catch (error) {
      found.forEach(function (block) {
        fail(block, []);
      });
      return;
    }
    for (var n = 0; n < found.length; n += 1) {
      var block = found[n];
      var id = 'mmd_d' + (n + 1);
      try {
        var code = block.querySelector('code');
        var result = await window.mermaid.render(id, code.textContent);
        var cleaned = cleanSvg(result.svg, id);
        if (!cleaned) {
          fail(block, [id, 'd' + id]);
          continue;
        }
        var sheet = buildSheet(cleaned.css, id);
        if (!sheet) {
          fail(block, [id, 'd' + id]);
          continue;
        }
        document.adoptedStyleSheets = document.adoptedStyleSheets.concat([sheet]);
        place(block, cleaned.root);
      } catch (error) {
        fail(block, [id, 'd' + id]);
      }
    }
  }

  drawAll().catch(function () {
    blocks().forEach(function (block) {
      fail(block, []);
    });
  });
})();
