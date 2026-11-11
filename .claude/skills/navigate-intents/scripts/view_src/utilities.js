  // ------------------------------------------------------------- utilities
  function own(obj, key) {
    return Object.prototype.hasOwnProperty.call(obj, key) ? obj[key] : undefined;
  }
  function isObj(v) { return v !== null && typeof v === 'object' && !Array.isArray(v); }
  function isStr(v) { return typeof v === 'string'; }
  function arr(v) { return Array.isArray(v) ? v : []; }
  function cmp(a, b) { return a < b ? -1 : (a > b ? 1 : 0); }
  function plural(n, noun) { return n + ' ' + (n === 1 ? noun[0] : noun[1]); }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) { node.className = cls; }
    if (text !== undefined && text !== null) { node.textContent = escapeDisplay(text); }
    return node;
  }
  function add(parent, child) { parent.appendChild(child); return child; }
  function byIdEl(id) { return document.getElementById(id); }
  function clear(node) { while (node.firstChild) { node.removeChild(node.firstChild); } }
  function text(parent, value) { parent.appendChild(document.createTextNode(escapeDisplay(value))); }
  function button(cls, label) {
    var b = el('button', cls, label);
    b.setAttribute('type', 'button');
    return b;
  }

