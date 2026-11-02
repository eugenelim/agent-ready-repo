/*
 * Draws the Mermaid fences the renderer marked for drawing. The page's policy allows this
 * file by hash, so it is one plain script. Every failure leaves the fence as source and says
 * so on its label; nothing here trusts the diagram text, Mermaid's output, or the page's own
 * element ids. Outside a browser the file only exports its pure checks, for the test table.
 */
(function () {
  'use strict';

  var DRAWN_LABEL = 'Diagram (source below)';
  var FAILED_LABEL = 'Diagram source (not drawn)';
  var SVG_ELEMENTS = [
    'svg', 'g', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon',
    'text', 'tspan', 'defs', 'marker', 'title', 'desc', 'clipPath', 'filter',
    'feDropShadow', 'linearGradient', 'stop', 'symbol'
  ];
  var GROUPING_RULES = ['CSSMediaRule', 'CSSSupportsRule', 'CSSLayerBlockRule', 'CSSContainerRule'];
  var LEAF_RULES = ['CSSStyleRule', 'CSSKeyframesRule', 'CSSKeyframeRule'];
  var BANNED_PROPERTIES = [
    'position', 'float', 'top', 'right', 'bottom', 'left', 'transform', 'z-index', 'translate',
    'rotate', 'scale'
  ];
  var BANNED_PROPERTY_FAMILIES = ['margin', 'inset', 'offset'];
  var KEYFRAME_NAMES = ['dash', 'edge-animation-frame'];

  function propertyBanned(name) {
    if (BANNED_PROPERTIES.indexOf(name) !== -1) {
      return true;
    }
    return BANNED_PROPERTY_FAMILIES.some(function (family) {
      return name === family || name.indexOf(family + '-') === 0;
    });
  }

  function propertiesAllowed(rule) {
    var declarations = rule.style;
    if (!declarations) {
      return true;
    }
    for (var i = 0; i < declarations.length; i += 1) {
      if (propertyBanned(declarations[i])) {
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

  function ownsId(value, id) {
    return value === id || value.indexOf(id + '-') === 0 || value.indexOf(id + '_') === 0;
  }

  function referencesOnlyTheDocument(value) {
    var matches = value.match(/url\([^)]*\)/gi) || [];
    return matches.every(function (match) {
      return /^url\(\s*['"]?#/i.test(match);
    });
  }

  function localName(name) {
    return name.slice(name.lastIndexOf(':') + 1).toLowerCase();
  }

  function attributeRefused(name, value) {
    var local = localName(name);
    if (local === 'href' || local === 'src' || local.indexOf('on') === 0) {
      return true;
    }
    return !referencesOnlyTheDocument(value);
  }

  if (typeof document === 'undefined') {
    if (typeof module !== 'undefined' && module.exports) {
      module.exports = {
        selectorList: selectorList,
        selectorsConfined: selectorsConfined,
        targetsTheRoot: targetsTheRoot,
        ownsId: ownsId,
        referencesOnlyTheDocument: referencesOnlyTheDocument,
        attributeRefused: attributeRefused,
        propertiesAllowed: propertiesAllowed,
        propertyBanned: propertyBanned
      };
    }
    return;
  }

  var holders = [];

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

  // An inline style becomes a rule in the same checked sheet, marked important because an
  // inline style outranks every sheet rule, so the drawing keeps the look Mermaid gave it
  // while every declaration goes through the same confinement.
  function inlineStyleRule(element, id, number, isRoot) {
    var style = element.style;
    if (!style) {
      return null;
    }
    var parts = [];
    for (var i = 0; i < style.length; i += 1) {
      var name = style.item(i);
      parts.push(name + ': ' + style.getPropertyValue(name) + ' !important');
    }
    if (!parts.length) {
      return '';
    }
    var selector = '#' + id;
    if (!isRoot) {
      element.setAttribute('data-mmd', String(number));
      selector += ' [data-mmd="' + number + '"]';
    }
    return selector + ' { ' + parts.join('; ') + ' }\n';
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
    var inline = '';
    for (var i = 0; i < elements.length; i += 1) {
      var element = elements[i];
      if (SVG_ELEMENTS.indexOf(element.localName) === -1) {
        return null;
      }
      var attributes = Array.prototype.slice.call(element.attributes);
      for (var j = 0; j < attributes.length; j += 1) {
        if (attributes[j].name.toLowerCase() === 'style') {
          continue;
        }
        if (attributeRefused(attributes[j].name, attributes[j].value)) {
          return null;
        }
      }
      if (element.hasAttribute('style')) {
        var rule = inlineStyleRule(element, id, i, element === root);
        if (rule === null) {
          return null;
        }
        inline += rule;
        element.removeAttribute('style');
      }
    }
    // The page's style policy drops the max-width Mermaid would add, so a drawing would stretch to
    // the column. Draw it at its own width instead; the sheet's max-width keeps it inside the page.
    var box = (root.getAttribute('viewBox') || '').split(/[\s,]+/);
    var natural = parseFloat(box[2]);
    if (isFinite(natural) && natural > 0) {
      root.setAttribute('width', String(Math.round(natural)));
    }
    prefixIds(elements, id);
    return { root: root, css: css + inline };
  }

  function refreshTabStop(holder) {
    if (holder.scrollWidth > holder.clientWidth) {
      holder.setAttribute('tabindex', '0');
    } else {
      holder.removeAttribute('tabindex');
    }
  }

  function place(block, root, number, total) {
    var holder = document.createElement('div');
    holder.className = 'diagram-render';
    holder.setAttribute('role', 'region');
    var source = block.querySelector('.source-scroll');
    var named = source ? source.getAttribute('aria-label') : null;
    holder.setAttribute(
      'aria-label',
      'Drawn diagram ' + number + ' of ' + total +
        (named && named.indexOf('Source: ') === 0 ? ': ' + named.slice(8) : '')
    );
    holder.appendChild(document.importNode(root, true));
    block.insertBefore(holder, source);
    holders.push(holder);
    refreshTabStop(holder);
    var label = block.querySelector('.diagram-label');
    if (label) {
      label.textContent = DRAWN_LABEL;
    }
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
    try {
      window.mermaid.initialize({
        startOnLoad: false,
        securityLevel: 'strict',
        suppressErrorRendering: true,
        htmlLabels: false,
        maxTextSize: 50000,
        maxEdges: 500,
        theme: 'neutral'
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
        place(block, cleaned.root, n + 1, found.length);
      } catch (error) {
        fail(block, [id, 'd' + id]);
      }
    }
  }

  function start() {
    drawAll().catch(function () {
      blocks().forEach(function (block) {
        fail(block, []);
      });
    });
  }

  window.addEventListener('resize', function () {
    holders.forEach(refreshTabStop);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
