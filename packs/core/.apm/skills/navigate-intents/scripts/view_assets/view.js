'use strict';
/*
 * Offline intent graph view.
 *
 * Reads the one JSON data block in the page and builds the whole view with
 * createElement and textContent.  Record text is only ever placed in a text
 * node or in a value attribute, after the unsafe-character escape below, and
 * the fixed label tables are the only source of group, state, and trust
 * class labels.  No library, no build step, no network.
 */
(function () {
  var SCHEMA = 'intent-navigation.view.v1';
  // Assembled in parts so a page for an unrecognised remote carries no host text.
  var GITHUB_PREFIX = 'https://' + 'github' + '.com/';
  var FILTER_KEYS = ['q', 'level', 'kind', 'status'];

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

  // ---------------------------------------------------------------- labels
  var GROUP_LABELS = {
    parent: 'Parent',
    children: 'Child intents',
    briefs: 'Briefs',
    specs: 'Specs',
    relations: 'Delivery relations',
    diagnostics: 'Delivery diagnostics',
    relatedHere: 'Related, written here',
    relatedElsewhere: 'Related, written elsewhere',
    pointers: 'Pointers'
  };
  var GROUP_HELP = {
    parent: 'The Parent intent: pointer this intent writes, resolved or refused.',
    children: 'Intents whose resolved Parent intent: pointer names this intent.',
    briefs: 'Briefs whose resolved Parent intent: pointer names this intent.',
    specs: 'Specs whose resolved Discovery: pointer names this intent.',
    relations: 'Delivery links the resolver reports between this node, its briefs, and its specs.',
    diagnostics: 'Findings the delivery resolver reports about this intent.',
    relatedHere: 'Related intents: pointers this intent writes, resolved or refused.',
    relatedElsewhere: 'Resolved Related intents: pointers other intents write that name this intent.',
    pointers: 'Every pointer this brief or spec writes, resolved or refused.'
  };
  var GROUP_ORDER = ['parent', 'children', 'briefs', 'specs', 'relations', 'diagnostics',
    'relatedHere', 'relatedElsewhere', 'pointers'];
  var STATE_HELP = {
    dangling: 'The pointer names no live record.',
    retired_target: 'The pointer names a retired record.',
    kind_mismatch: 'The pointer names a record of a different kind than it declares.',
    out_of_type: 'The pointer names a record of a type this field does not accept.',
    multiple_values: 'The field carries more than one value.',
    cycle: 'The pointer would make an intent its own ancestor.',
    unparseable: 'The value is not a pointer the derivation can read.',
    self_reference: 'The pointer names the record that writes it.'
  };
  var TRUST_HELP = {
    delivery_contract: 'The delivery resolver reports this link from the records\' own contract.',
    pointer_checked: 'A pointer the derivation checked against a live record.',
    pointer_unchecked: 'A pointer written in a field, not checked beyond resolving it.'
  };
  var VIEWS = [
    { key: 'tree', name: 'Tree', noun: 'intents' },
    { key: 'outstanding', name: 'Outstanding', noun: 'items' },
    { key: 'refused', name: 'Refused edges', noun: 'edges' },
    { key: 'parentless', name: 'Parentless', noun: 'intents' }
  ];

  // ------------------------------------------------------------- utilities
  function own(obj, key) {
    return Object.prototype.hasOwnProperty.call(obj, key) ? obj[key] : undefined;
  }
  function isObj(v) { return v !== null && typeof v === 'object' && !Array.isArray(v); }
  function isStr(v) { return typeof v === 'string'; }
  function cmp(a, b) { return a < b ? -1 : (a > b ? 1 : 0); }
  function byId(a, b) { return cmp(a, b); }
  function sumValues(obj) {
    var total = 0;
    if (!isObj(obj)) { return total; }
    Object.keys(obj).forEach(function (k) {
      if (typeof obj[k] === 'number') { total += obj[k]; }
    });
    return total;
  }

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

  // ------------------------------------------------------------------ data
  var data = null;
  var nodes = new Map();
  var recordIds = [];
  var kidsOf = new Map();
  var relsByNode = new Map();
  var edgesFrom = new Map();
  var current = null;
  var expanded = new Set();
  var dom = {};

  function validData(d) {
    return isObj(d) && d.schema === SCHEMA && isObj(d.scope) && isObj(d.provenance) &&
      isObj(d.summary) && isObj(d.records) && isObj(d.outstanding) &&
      Array.isArray(d.nodes) && Array.isArray(d.edges) && isObj(d.source_links) &&
      d.nodes.every(function (n) { return isObj(n) && isStr(n.id); }) &&
      d.edges.every(function (e) { return isObj(e) && isStr(e.from); });
  }

  function rec(id) {
    var r = own(data.records, id);
    return isObj(r) ? r : null;
  }
  function resolvedParent(r) {
    var e = r && r.parent_edge;
    return isObj(e) && isStr(e.to) && !e.state ? e.to : null;
  }
  function addTo(map, key, value) {
    if (!map.has(key)) { map.set(key, []); }
    map.get(key).push(value);
  }

  function buildIndexes() {
    data.nodes.forEach(function (n) { nodes.set(n.id, n); });
    recordIds = Object.keys(data.records).sort(byId);
    recordIds.forEach(function (id) {
      var r = rec(id);
      var parent = resolvedParent(r);
      if (parent !== null && own(data.records, parent) !== undefined) { addTo(kidsOf, parent, id); }
      (Array.isArray(r.delivery_relations) ? r.delivery_relations : []).forEach(function (rel) {
        if (!isObj(rel)) { return; }
        [rel.intent, rel.brief, rel.spec].forEach(function (nid) {
          if (isStr(nid)) { addTo(relsByNode, nid, rel); }
        });
      });
    });
    kidsOf.forEach(function (list) { list.sort(byId); });
    data.edges.forEach(function (e) { addTo(edgesFrom, e.from, e); });
  }

  function deliveryUnavailable() { return data.outstanding.available === false; }

  // --------------------------------------------------------------- routing
  function parseRoute() {
    var p = new URLSearchParams(location.hash.replace(/^#/, ''));
    var view = p.get('view');
    var known = VIEWS.some(function (v) { return v.key === view; });
    return {
      view: known ? view : 'tree',
      node: p.get('node') || '',
      q: p.get('q') || '',
      level: p.get('level') || '',
      kind: p.get('kind') || '',
      status: p.get('status') || ''
    };
  }

  function hashFor(over) {
    var r = Object.assign({}, current, over);
    var p = new URLSearchParams();
    p.set('view', r.view);
    ['node', 'q', 'level', 'kind', 'status'].forEach(function (k) {
      if (r[k]) { p.set(k, r[k]); }
    });
    return '#' + p.toString();
  }

  function hasFilters(r) { return FILTER_KEYS.some(function (k) { return r[k] !== ''; }); }

  // ------------------------------------------------------------ small parts
  function labelChip(table, kind, key) {
    if (!isStr(key) || own(table, key) === undefined) { return null; }
    return el('span', 'chip label-' + kind, key);
  }
  function stateChip(key) {
    return labelChip(STATE_HELP, 'state', key);
  }
  function trustChip(key) {
    return labelChip(TRUST_HELP, 'trust', key);
  }

  function nodeLink(id, cls) {
    var a = el('a', cls || 'node-link', id);
    a.setAttribute('href', hashFor({ node: id }));
    a.setAttribute('data-node', id);
    return a;
  }
  function outsideRef(id) {
    var s = el('span', 'outside');
    add(s, el('span', 'value', id));
    add(s, el('span', 'mark mark-outside', 'outside this export'));
    return s;
  }
  function nodeRef(id, cls) {
    return nodes.has(id) ? nodeLink(id, cls) : outsideRef(id);
  }
  function viewLink(key, name) {
    var a = el('a', 'view-link', name);
    a.setAttribute('href', hashFor({ view: key }));
    a.setAttribute('data-view', key);
    return a;
  }

  function edgeValue(e) {
    if (isStr(e.value)) { return e.value; }
    var basis = e.basis;
    if (isObj(basis) && Array.isArray(basis.values)) {
      return basis.values.map(function (v) { return isObj(v) && isStr(v.value) ? v.value : ''; })
        .join(', ');
    }
    return '';
  }

  function edgeItem(e, withSource) {
    var li = el('li', 'edge');
    var line = add(li, el('div', 'row'));
    if (withSource) { add(line, nodeRef(e.from, 'node-link')); }
    add(line, el('span', 'value field', isStr(e.field) ? e.field : ''));
    if (e.state) {
      add(line, el('code', 'value pointer-value', edgeValue(e)));
      var sc = stateChip(e.state);
      if (sc) { add(line, sc); } else { add(line, el('span', 'value', String(e.state))); }
      add(line, el('span', 'mark mark-refused', 'refused'));
    } else if (isStr(e.to)) {
      add(line, nodeRef(e.to, 'node-link'));
    } else {
      add(line, el('code', 'value pointer-value', edgeValue(e)));
    }
    var tc = trustChip(e.trust_class);
    if (tc) { add(line, tc); }
    return li;
  }

  function describe(o) {
    if (!isObj(o)) { return String(o); }
    return Object.keys(o).sort().map(function (k) {
      var v = o[k];
      return k + ': ' + (isStr(v) ? v : JSON.stringify(v));
    }).join('; ');
  }

  function relationItem(rel) {
    var li = el('li', 'edge');
    var line = add(li, el('div', 'row'));
    add(line, el('span', 'value field', isStr(rel.type) ? rel.type : ''));
    [['intent', 'Intent'], ['brief', 'Brief'], ['spec', 'Spec']].forEach(function (pair) {
      var id = rel[pair[0]];
      if (!isStr(id)) { return; }
      var part = add(line, el('span', 'part'));
      add(part, el('span', 'part-name', pair[1]));
      add(part, nodeRef(id, 'node-link'));
    });
    if (isStr(rel.route)) { add(line, el('span', 'value', 'route ' + rel.route)); }
    var tc = trustChip(rel.trust_class);
    if (tc) { add(line, tc); }
    return li;
  }

  // ------------------------------------------------------------ source link
  function sourceBlock(id) {
    var wrap = el('span', 'source');
    var link = own(data.source_links, id);
    var n = nodes.get(id) || {};
    var url = isObj(link) && isStr(link.url) ? link.url : '';
    var kind = isObj(link) ? link.kind : '';
    if ((kind === 'commit' || kind === 'latest') && url.indexOf(GITHUB_PREFIX) === 0) {
      var a = add(wrap, el('a', 'source-link', 'Open on GitHub'));
      a.setAttribute('href', url);
      a.setAttribute('rel', 'noopener noreferrer');
      add(wrap, el('span', 'value', isStr(link.path) ? link.path : ''));
      if (kind === 'latest') {
        add(wrap, el('span', 'mark mark-latest', 'may be newer than this export'));
      } else if (isStr(data.provenance.commit)) {
        add(wrap, el('span', 'mark', 'at commit ' + data.provenance.commit.slice(0, 12)));
      }
    } else {
      add(wrap, el('span', 'value', isObj(link) && isStr(link.path) ? link.path : (n.path || '')));
      add(wrap, el('span', 'mark', 'no link available'));
    }
    return wrap;
  }

  // ----------------------------------------------------------------- list
  function intentRow(id, withToggle, seen) {
    var r = rec(id) || {};
    var n = nodes.get(id) || {};
    var li = el('li', 'item');
    var row = add(li, el('div', 'row'));
    var kids = withToggle ? (kidsOf.get(id) || []) : [];
    var sub = null;
    var toggle = null;
    if (kids.length) {
      toggle = add(row, el('button', 'toggle'));
      toggle.setAttribute('type', 'button');
      toggle.setAttribute('aria-expanded', 'false');
      text(toggle, 'Children (' + kids.length + ')');
      add(toggle, el('span', 'visually-hidden', ' of ' + id));
    }
    add(row, nodeLink(id, 'node-link row-link'));
    if (n.heading) { add(row, el('span', 'f-heading', n.heading)); }
    add(row, el('span', 'chip f-level', r.level || 'unrecorded'));
    if (r.kind) { add(row, el('span', 'chip f-kind', r.kind)); }
    add(row, el('span', 'chip f-status', r.status || ''));
    var pe = r.parent_edge;
    if (isObj(pe) && pe.state) {
      add(row, el('span', 'mark mark-refused f-refused', 'refused parent'));
      var sc = stateChip(pe.state);
      if (sc) { add(row, sc); }
    }
    if (toggle) {
      var setOpen = function (open) {
        if (open && sub === null) { sub = buildSubtree(id, seen); li.appendChild(sub); }
        if (sub !== null) { sub.hidden = !open; }
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        if (open) { expanded.add(id); } else { expanded.delete(id); }
      };
      toggle.addEventListener('click', function () {
        setOpen(toggle.getAttribute('aria-expanded') !== 'true');
      });
      if (expanded.has(id)) { setOpen(true); }
    }
    return li;
  }

  function buildSubtree(id, seen) {
    var ul = el('ul', 'tree subtree');
    (kidsOf.get(id) || []).forEach(function (kid) {
      if (seen.has(kid)) { return; }
      seen.add(kid);
      add(ul, intentRow(kid, true, seen));
    });
    return ul;
  }

  function treeRoots() {
    var roots = recordIds.filter(function (id) {
      var parent = resolvedParent(rec(id));
      return parent === null || own(data.records, parent) === undefined;
    });
    // Intents left over by an unresolved loop still appear once, as extra roots.
    var reach = new Set();
    var stack = roots.slice();
    while (stack.length) {
      var id = stack.pop();
      if (reach.has(id)) { continue; }
      reach.add(id);
      (kidsOf.get(id) || []).forEach(function (k) { stack.push(k); });
    }
    recordIds.forEach(function (id2) {
      if (!reach.has(id2)) { roots.push(id2); reach.add(id2); }
    });
    return roots.sort(byId);
  }

  function matchesFilters(id, route) {
    var r = rec(id) || {};
    var n = nodes.get(id) || {};
    if (route.level && (r.level || 'unrecorded').toLowerCase() !== route.level.toLowerCase()) {
      return false;
    }
    if (route.kind && (r.kind || '').toLowerCase() !== route.kind.toLowerCase()) { return false; }
    if (route.status && (r.status || '') !== route.status) { return false; }
    if (route.q) {
      var want = route.q.toLowerCase();
      var slug = (n.slug || '').toLowerCase();
      var heading = (n.heading || '').toLowerCase();
      if (slug.indexOf(want) === -1 && heading.indexOf(want) === -1) { return false; }
    }
    return true;
  }

  function describeFilters(route) {
    var parts = [];
    if (route.q) { parts.push('search "' + route.q + '"'); }
    if (route.level) { parts.push('level ' + route.level); }
    if (route.kind) { parts.push('kind ' + route.kind); }
    if (route.status) { parts.push('status "' + route.status + '"'); }
    return parts.join(', ');
  }

  function plainList(cls) { return el('ul', cls || 'tree'); }

  function emptyMessage(message) {
    var p = el('p', 'empty', message);
    return p;
  }

  function filteredEmpty(route) {
    var box = el('div', 'empty');
    add(box, el('p', '', 'No results. These filters emptied the list: ' + describeFilters(route) + '.'));
    var b = add(box, el('button', 'action', 'Clear filters'));
    b.setAttribute('type', 'button');
    b.addEventListener('click', function () {
      replaceRoute({ q: '', level: '', kind: '', status: '' });
      dom.q.focus();
    });
    return box;
  }

  function filterNote(route, shown, total, what) {
    return el('p', 'note', 'Filters apply to intents. Showing ' + shown + ' of ' + total + ' ' +
      what + ' for ' + describeFilters(route) + '.');
  }

  // Each view renderer returns { count, noun }.
  function renderTree(route) {
    var filtered = hasFilters(route);
    if (recordIds.length === 0) {
      dom.list.appendChild(emptyMessage('No intents were found in docs/product/intents.'));
      return { count: 0 };
    }
    if (filtered) {
      var ids = recordIds.filter(function (id) { return matchesFilters(id, route); });
      if (ids.length === 0) { dom.list.appendChild(filteredEmpty(route)); return { count: 0 }; }
      dom.list.appendChild(filterNote(route, ids.length, recordIds.length, 'intents'));
      var flat = add(dom.list, plainList());
      ids.forEach(function (id) { add(flat, intentRow(id, false, new Set())); });
      return { count: ids.length };
    }
    var seen = new Set();
    var ul = add(dom.list, plainList());
    treeRoots().forEach(function (id) {
      seen.add(id);
      add(ul, intentRow(id, true, seen));
    });
    return { count: recordIds.length };
  }

  function renderParentless(route) {
    var base = recordIds.filter(function (id) { return resolvedParent(rec(id)) === null; });
    if (base.length === 0) {
      dom.list.appendChild(emptyMessage('Every intent has a parent.'));
      return { count: 0 };
    }
    var ids = base.filter(function (id) { return matchesFilters(id, route); });
    if (ids.length === 0) { dom.list.appendChild(filteredEmpty(route)); return { count: 0 }; }
    if (hasFilters(route)) {
      dom.list.appendChild(filterNote(route, ids.length, base.length, 'parentless intents'));
    }
    var ul = add(dom.list, plainList());
    ids.forEach(function (id) { add(ul, intentRow(id, false, new Set())); });
    return { count: ids.length };
  }

  function unavailableStatement() {
    var p = el('p', 'notice');
    text(p, 'Delivery mapping was unavailable, so this export holds no delivery facts. Reason: ');
    add(p, el('span', 'value', isStr(data.outstanding.reason) ? data.outstanding.reason : ''));
    if (data.outstanding.limit !== undefined && data.outstanding.limit !== null) {
      text(p, ', limit ');
      add(p, el('span', 'value', String(data.outstanding.limit)));
    }
    text(p, '.');
    return p;
  }

  function chain(ancestors) {
    var wrap = el('div', 'chain');
    add(wrap, el('span', 'part-name', 'Under'));
    var list = Array.isArray(ancestors) ? ancestors.slice().reverse() : [];
    if (list.length === 0) { add(wrap, el('span', 'value', 'nothing')); return wrap; }
    list.forEach(function (a, i) {
      if (i > 0) { add(wrap, el('span', 'sep', '\u203A')); }
      if (!isObj(a) || !isStr(a.id)) { return; }
      var part = add(wrap, el('span', 'part'));
      add(part, nodeRef(a.id, 'node-link'));
      if (a.terminal) { add(part, el('span', 'mark mark-terminal', 'terminal')); }
    });
    return wrap;
  }

  function outstandingItem(it) {
    var li = el('li', 'item');
    var row = add(li, el('div', 'row'));
    add(row, nodeRef(it.id, 'node-link row-link'));
    add(row, el('span', 'chip f-type', it.type || ''));
    add(row, el('span', 'chip f-status', it.status || ''));
    if (it.type === 'intent') {
      add(row, el('span', 'chip f-level', it.level || 'unrecorded'));
      if (it.kind) { add(row, el('span', 'chip f-kind', it.kind)); }
    }
    if (it.type === 'spec') {
      var ul = add(li, el('ul', 'placements'));
      (Array.isArray(it.placements) ? it.placements : []).forEach(function (pl) {
        var pli = add(ul, el('li', 'placement'));
        var prow = add(pli, el('div', 'row'));
        add(prow, el('span', 'value field', pl.pointer_field || 'no pointer'));
        var pe = pl.parent_edge;
        if (isObj(pe) && pe.state) {
          add(prow, el('code', 'value pointer-value', edgeValue(pe)));
          var sc = stateChip(pe.state);
          if (sc) { add(prow, sc); }
          add(prow, el('span', 'mark mark-refused', 'refused'));
        } else if (pl.ancestors && pl.ancestors.length) {
          add(pli, chain(pl.ancestors));
        }
        if (isStr(pl.relation_type)) { add(prow, el('span', 'value', pl.relation_type)); }
      });
    } else {
      var pe2 = it.parent_edge;
      if (isObj(pe2) && pe2.state) {
        var prow2 = add(li, el('div', 'row'));
        add(prow2, el('span', 'value field', 'Parent intent'));
        add(prow2, el('code', 'value pointer-value', edgeValue(pe2)));
        var sc2 = stateChip(pe2.state);
        if (sc2) { add(prow2, sc2); }
        add(prow2, el('span', 'mark mark-refused', 'refused'));
      } else if (Array.isArray(it.ancestors) && it.ancestors.length) {
        add(li, chain(it.ancestors));
      } else {
        add(li, el('p', 'note', 'No parent.'));
      }
      (Array.isArray(it.refused_parent_edges) ? it.refused_parent_edges : []).forEach(function (e) {
        var rrow = add(li, el('div', 'row'));
        add(rrow, el('span', 'value field', 'Parent intent'));
        add(rrow, el('code', 'value pointer-value', edgeValue(e)));
        var sc3 = stateChip(e.state);
        if (sc3) { add(rrow, sc3); }
        add(rrow, el('span', 'mark mark-refused', 'refused'));
      });
    }
    return li;
  }

  function renderOutstanding(route) {
    if (deliveryUnavailable()) {
      dom.list.appendChild(unavailableStatement());
      return { count: 0, unavailable: true };
    }
    var filtered = hasFilters(route);
    function keep(it) {
      if (!isObj(it) || !isStr(it.id)) { return false; }
      return !filtered || (it.type === 'intent' && matchesFilters(it.id, route));
    }
    var placed = (Array.isArray(data.outstanding.placed) ? data.outstanding.placed : []).filter(keep);
    var noParent = (Array.isArray(data.outstanding.no_parent) ? data.outstanding.no_parent : []).filter(keep);
    var baseTotal = (data.outstanding.placed || []).length + (data.outstanding.no_parent || []).length;
    var total = placed.length + noParent.length;
    if (baseTotal === 0) {
      dom.list.appendChild(emptyMessage('Nothing is outstanding.'));
      return { count: 0 };
    }
    if (total === 0) { dom.list.appendChild(filteredEmpty(route)); return { count: 0 }; }
    if (filtered) {
      dom.list.appendChild(el('p', 'note', 'Filters apply to intents; briefs and specs are hidden while a filter is active.'));
    }
    [['Placed', placed], ['No parent', noParent]].forEach(function (pair) {
      var sec = add(dom.list, el('section', 'subsection'));
      add(sec, el('h3', 'subheading', pair[0] + ' (' + pair[1].length + ')'));
      if (pair[1].length === 0) {
        add(sec, el('p', 'empty', 'None.'));
        return;
      }
      var ul = add(sec, plainList());
      pair[1].forEach(function (it) { add(ul, outstandingItem(it)); });
    });
    return { count: total };
  }

  function renderRefused(route) {
    var all = data.edges.filter(function (e) { return e.state; });
    if (all.length === 0) {
      dom.list.appendChild(emptyMessage('Every pointer resolved.'));
      return { count: 0 };
    }
    var filtered = hasFilters(route);
    var edges = filtered ? all.filter(function (e) {
      return rec(e.from) !== null && matchesFilters(e.from, route);
    }) : all;
    if (edges.length === 0) { dom.list.appendChild(filteredEmpty(route)); return { count: 0 }; }
    if (filtered) {
      dom.list.appendChild(filterNote(route, edges.length, all.length, 'refused edges'));
    }
    var ul = add(dom.list, plainList());
    edges.forEach(function (e) { add(ul, edgeItem(e, true)); });
    return { count: edges.length };
  }

  var RENDERERS = {
    tree: renderTree,
    outstanding: renderOutstanding,
    refused: renderRefused,
    parentless: renderParentless
  };

  function viewName(key) {
    for (var i = 0; i < VIEWS.length; i++) { if (VIEWS[i].key === key) { return VIEWS[i]; } }
    return VIEWS[0];
  }

  function markSelected(route) {
    var rows = dom.list.querySelectorAll('a.row-link');
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].getAttribute('data-node') === route.node) {
        rows[i].setAttribute('aria-current', 'true');
      } else {
        rows[i].removeAttribute('aria-current');
      }
    }
  }

  function renderList(route, announce) {
    var view = viewName(route.view);
    clear(dom.list);
    dom.viewHeading.textContent = view.name;
    var result = RENDERERS[view.key](route);
    var summary;
    if (result.unavailable) {
      summary = 'delivery mapping unavailable';
    } else {
      summary = result.count + ' ' + (result.count === 1 ? view.noun.replace(/s$/, '') : view.noun);
    }
    dom.viewCount.textContent = summary;
    markSelected(route);
    if (announce) { dom.live.textContent = view.name + ' view, ' + summary; }
    performance.mark('list-updated');
  }

  // --------------------------------------------------------------- detail
  function group(parent, key, build) {
    var sec = add(parent, el('section', 'group'));
    add(sec, el('h3', 'subheading label-group', own(GROUP_LABELS, key)));
    build(sec);
    return sec;
  }
  function groupList(sec, items, make) {
    if (items.length === 0) { add(sec, el('p', 'empty', 'None.')); return; }
    var ul = add(sec, plainList('plain'));
    items.forEach(function (it) { add(ul, make(it)); });
  }
  function refLine(id) {
    var li = el('li', 'edge');
    add(add(li, el('div', 'row')), nodeRef(id, 'node-link'));
    return li;
  }
  function fact(dl, name, valueNode) {
    var row = add(dl, el('div', 'fact'));
    add(row, el('dt', 'fact-name', name));
    var dd = add(row, el('dd', 'fact-value'));
    dd.appendChild(valueNode);
  }
  function valueSpan(v) { return el('span', 'value', v); }

  function renderLegend() {
    var sec = add(dom.legend, el('section', 'group legend'));
    add(sec, el('h3', 'subheading', 'Legend'));
    var dl = add(sec, el('dl', 'legend-list'));
    GROUP_ORDER.forEach(function (key) {
      var row = add(dl, el('div', 'fact'));
      add(row, el('dt', 'fact-name label-group', own(GROUP_LABELS, key)));
      add(row, el('dd', 'fact-value', own(GROUP_HELP, key)));
    });
    Object.keys(STATE_HELP).forEach(function (key) {
      var row = add(dl, el('div', 'fact'));
      add(row, el('dt', 'fact-name label-state', key));
      add(row, el('dd', 'fact-value', own(STATE_HELP, key)));
    });
    Object.keys(TRUST_HELP).forEach(function (key) {
      var row = add(dl, el('div', 'fact'));
      add(row, el('dt', 'fact-name label-trust', key));
      add(row, el('dd', 'fact-value', own(TRUST_HELP, key)));
    });
  }

  function renderDetail(route) {
    clear(dom.detailBody);
    var id = route.node;
    dom.detailHeading.textContent = escapeDisplay(id || 'Details');
    if (!id) {
      add(dom.detailBody, el('p', 'note', 'Select an intent, brief, or spec to see its facts and edges.'));
      return;
    }
    var n = nodes.get(id);
    if (!n) {
      add(dom.detailBody, el('p', 'note', 'This node is not in the export.'));
      return;
    }
    var r = rec(id);
    var dl = add(dom.detailBody, el('dl', 'facts'));
    if (n.heading) { fact(dl, 'Heading', valueSpan(n.heading)); }
    fact(dl, 'Path', valueSpan(n.path || ''));
    fact(dl, 'Type', valueSpan(n.type || ''));
    if (r) {
      fact(dl, 'Level', valueSpan(r.level || 'unrecorded'));
      fact(dl, 'Kind', valueSpan(r.kind || 'none recorded'));
    }
    fact(dl, 'Status', valueSpan(r ? (r.status || '') : (n.status || '')));
    fact(dl, 'Source', sourceBlock(id));

    var unavailable = deliveryUnavailable();
    var body = dom.detailBody;
    if (r) {
      group(body, 'parent', function (sec) {
        groupList(sec, isObj(r.parent_edge) ? [r.parent_edge] : [], function (e) { return edgeItem(e, false); });
      });
      group(body, 'children', function (sec) { groupList(sec, r.children || [], refLine); });
      group(body, 'briefs', function (sec) { groupList(sec, r.briefs || [], refLine); });
      group(body, 'specs', function (sec) { groupList(sec, r.specs || [], refLine); });
      if (unavailable) {
        add(body, unavailableStatement());
      } else {
        group(body, 'relations', function (sec) {
          groupList(sec, r.delivery_relations || [], relationItem);
        });
        group(body, 'diagnostics', function (sec) {
          groupList(sec, r.delivery_diagnostics || [], function (d) {
            var li = el('li', 'edge');
            add(add(li, el('div', 'row')), el('span', 'value', describe(d)));
            return li;
          });
        });
      }
      group(body, 'relatedHere', function (sec) {
        groupList(sec, r.related_written_here || [], function (e) { return edgeItem(e, false); });
      });
      group(body, 'relatedElsewhere', function (sec) {
        groupList(sec, r.related_written_elsewhere || [], function (e) { return edgeItem(e, true); });
      });
    } else {
      group(body, 'pointers', function (sec) {
        groupList(sec, edgesFrom.get(id) || [], function (e) { return edgeItem(e, false); });
      });
      if (unavailable) {
        add(body, unavailableStatement());
      } else {
        group(body, 'relations', function (sec) {
          groupList(sec, relsByNode.get(id) || [], relationItem);
        });
      }
    }
  }

  // --------------------------------------------------------- page chrome
  function renderSummary() {
    var s = data.summary;
    dom.summaryList.textContent = '';
    var items = [
      ['Outstanding', s.outstanding, 'outstanding'],
      ['Refused edges', sumValues(s.refused_edges_by_state), 'refused'],
      ['Parentless intents', s.parentless_intents, 'parentless'],
      ['Intents', sumValues(s.intents_by_level), 'tree'],
      ['Briefs', s.briefs, null],
      ['Specs', s.specs, null]
    ];
    items.forEach(function (it) {
      var li = add(dom.summaryList, el('li', 'stat'));
      var holder = it[2] ? add(li, el('a', 'stat-link stat-nav')) : add(li, el('span', 'stat-link'));
      if (it[2]) { holder.setAttribute('href', hashFor({ view: it[2] })); }
      add(holder, el('span', 'stat-value', String(it[1])));
      add(holder, el('span', 'stat-label', it[0]));
    });
    var scoped = data.scope.from;
    dom.summaryScope.textContent = isStr(scoped) ? 'These counts cover the whole corpus, not only the scoped subtree.' : 'These counts cover the whole corpus.';
  }

  function renderMeta() {
    var p = data.provenance;
    dom.meta.textContent = escapeDisplay('Read-only snapshot generated ' + (p.generated_at || 'at an unknown time') + '. ' + (p.untrusted_data || ''));
    var from = data.scope.from;
    if (isStr(from)) {
      dom.banner.hidden = false;
      clear(dom.banner);
      text(dom.banner, 'Scoped export: this file shows ');
      add(dom.banner, nodeRef(from, 'node-link'));
      text(dom.banner, ' and every intent beneath it.');
    }
  }

  function renderNav(route) {
    clear(dom.viewList);
    VIEWS.forEach(function (v) {
      var li = add(dom.viewList, el('li', 'view-item'));
      var a = add(li, viewLink(v.key, v.name));
      if (v.key === route.view) { a.setAttribute('aria-current', 'page'); }
    });
  }

  function fillSelect(select, firstLabel, values) {
    var first = document.createElement('option');
    first.setAttribute('value', '');
    first.textContent = firstLabel;
    select.appendChild(first);
    values.forEach(function (v) {
      var o = document.createElement('option');
      o.setAttribute('value', v);
      o.textContent = escapeDisplay(v);
      select.appendChild(o);
    });
  }

  function buildFilters() {
    var levels = new Set();
    var kinds = new Set();
    var statuses = new Set();
    recordIds.forEach(function (id) {
      var r = rec(id);
      levels.add(r.level || 'unrecorded');
      if (r.kind) { kinds.add(r.kind); }
      statuses.add(r.status || '');
    });
    fillSelect(dom.level, 'Any level', Array.from(levels).sort(byId));
    fillSelect(dom.kind, 'Any kind', Array.from(kinds).sort(byId));
    fillSelect(dom.status, 'Any status', Array.from(statuses).sort(byId));
    dom.q.addEventListener('input', function () { replaceRoute({ q: dom.q.value }); });
    [['level', dom.level], ['kind', dom.kind], ['status', dom.status]].forEach(function (pair) {
      pair[1].addEventListener('change', function () {
        var over = {};
        over[pair[0]] = pair[1].value;
        replaceRoute(over);
      });
    });
  }

  function syncControls(route) {
    if (dom.q.value !== route.q) { dom.q.value = route.q; }
    dom.level.value = route.level;
    dom.kind.value = route.kind;
    dom.status.value = route.status;
  }

  function replaceRoute(over) {
    history.replaceState(null, '', hashFor(over));
    handleRoute();
  }

  function handleRoute() {
    var next = parseRoute();
    var prev = current;
    current = next;
    var viewChanged = prev === null || prev.view !== next.view;
    var filterChanged = prev === null || FILTER_KEYS.some(function (k) { return prev[k] !== next[k]; });
    var nodeChanged = prev === null || prev.node !== next.node;
    syncControls(next);
    renderNav(next);
    renderMeta();
    renderSummary();
    if (viewChanged || filterChanged) {
      renderList(next, prev !== null);
    } else if (nodeChanged) {
      markSelected(next);
    }
    renderDetail(next);
    if (prev !== null) {
      if (viewChanged) {
        dom.viewHeading.focus();
      } else if (nodeChanged) {
        dom.detailHeading.focus();
      }
    }
  }

  function showDamaged() {
    var main = byIdEl('main');
    var alertBox = el('div', 'alert', 'This file is damaged and cannot be shown. Export it again.');
    alertBox.setAttribute('role', 'alert');
    main.replaceChildren(alertBox);
    main.hidden = false;
  }

  function start() {
    var block = byIdEl('intent-data');
    try {
      data = JSON.parse(block.textContent);
    } catch (err) {
      data = null;
    }
    if (!validData(data)) { showDamaged(); return; }
    try {
      dom = {
        live: byIdEl('live'), meta: byIdEl('meta'), banner: byIdEl('scope-banner'),
        summarySection: byIdEl('summary-section'), summaryList: byIdEl('summary-list'),
        summaryScope: byIdEl('summary-scope'), viewList: byIdEl('view-list'),
        q: byIdEl('filter-q'), level: byIdEl('filter-level'), kind: byIdEl('filter-kind'),
        status: byIdEl('filter-status'), viewHeading: byIdEl('view-heading'),
        viewCount: byIdEl('view-count'), list: byIdEl('list'),
        detailHeading: byIdEl('detail-heading'), detailBody: byIdEl('detail-body'),
        legend: byIdEl('detail-legend')
      };
      buildIndexes();
      buildFilters();
      renderLegend();
      byIdEl('main').hidden = false;
      dom.summarySection.hidden = false;
      handleRoute();
      window.addEventListener('hashchange', handleRoute);
      performance.mark('view-ready');
    } catch (err) {
      showDamaged();
    }
  }

  start();
})();
