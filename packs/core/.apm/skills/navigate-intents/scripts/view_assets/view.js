'use strict';
/*
 * Offline intent graph view, organised around four session-start questions.
 *
 * Reads the one JSON data block in the page and builds the whole view with
 * createElement and textContent.  Record text is only ever placed in a text
 * node or in an attribute value, after the unsafe-character escape below, and
 * fixed tables are the only source of question, group, state, trust class and
 * next-step text.  No library, no build step, no network.
 */
(function () {
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
    parent: 'The intent above this one (the Parent intent field), resolved or refused.',
    children: 'Intents that name this one as their parent (their Parent intent field).',
    briefs: 'Briefs that name this intent as their parent (their Parent intent field).',
    specs: 'Specs that name this intent as their source (their Discovery field).',
    relations: 'Links that show how this node is delivered, through its briefs and specs.',
    diagnostics: 'Problems the delivery resolver found with this intent.',
    relatedHere: 'Other intents this one lists as related (the Related intents field), resolved or refused.',
    relatedElsewhere: 'Other intents that list this one as related (their Related intents field).',
    pointers: 'Every pointer this brief or spec writes. A pointer is a field that names another record. Each is resolved or refused.'
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
  // State marks: the glyph is decoration, the word beside it is what is read.
  var MARKS = {
    active: { glyph: '\u25CF', help: 'In progress: a spec being built or a brief being delivered.' },
    approved: { glyph: '\u25C6', help: 'Approved, accepted, or a brief ready for its slices.' },
    draft: { glyph: '\u25C7', help: 'Open and still being shaped.' },
    broken: { glyph: '\u2715', help: 'A pointer that did not resolve, or a delivery problem.' },
    stale: { glyph: '\u25B3', help: 'The linked file may be newer than this snapshot.' },
    done: { glyph: '\u2713', help: 'Finished or closed: not open work.' }
  };
  var MARK_ORDER = ['active', 'approved', 'draft', 'broken', 'stale', 'done'];
  var ACTIVE_WORDS = { Implementing: true, Executing: true };
  var APPROVED_WORDS = { Approved: true, Accepted: true, Ready: true };
  var NAME_LABELS = ['Spec: ', 'Brief: ', 'Intent: ', 'Feature: ', 'Capability: ', 'Outcome: ',
    'Opportunity: '];
  var TYPE_NAMES = { intent: 'Intent', brief: 'Brief', spec: 'Spec' };
  var TYPE_GROUPS = [['intent', 'Intents'], ['brief', 'Briefs'], ['spec', 'Specs']];

  var QUESTIONS = [
    { key: 'next', name: 'What can I work on next?', title: 'In a startable stage',
      lead: 'Readiness not checked in this snapshot.', sort: 'By stage, then name',
      empty: 'Nothing is in a startable stage.', noun: ['item', 'items'] },
    { key: 'capabilities', name: 'What is still open under a capability?',
      title: 'Capabilities with open work', lead: 'Pick a capability to see the open work beneath it.',
      sort: 'By open count, then name', empty: 'No capability has open work beneath it.',
      noun: ['capability', 'capabilities'] },
    { key: 'noparent', name: 'What has no parent?', title: 'Open with no parent',
      lead: 'Open items whose parent pointer is absent or did not resolve.',
      sort: 'By type, then name', empty: 'Every open item has a parent.', noun: ['item', 'items'],
      filters: ['type', 'level'] },
    { key: 'broken', name: 'What is broken?', title: 'Broken pointers and delivery problems',
      lead: 'Pointers that did not resolve, and problems the delivery resolver found.',
      sort: 'By name', empty: 'Nothing is broken.', noun: ['entry', 'entries'] },
    { key: 'browse', name: 'Browse all intents', title: 'All intents',
      lead: 'Every live intent under its parent.', sort: 'Under each parent, by name',
      empty: 'No intents were found.', noun: ['intent', 'intents'],
      filters: ['level', 'kind', 'status'] }
  ];
  var FILTER_LABELS = { type: ['Type', 'Any type'], level: ['Level', 'Any level'],
    kind: ['Kind', 'Any kind'], status: ['Status', 'Any status'] };
  var ROUTE_KEYS = ['q', 'node', 'search', 'type', 'level', 'kind', 'status'];
  var FILTER_KEYS = ['type', 'level', 'kind', 'status'];

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

  // ------------------------------------------------------------------ data
  var data = null;
  var nodes = new Map();
  var recordIds = [];
  var kidsOf = new Map();
  var relsByNode = new Map();
  var intentBySlug = new Map();
  var edgesFrom = new Map();
  var openById = new Map();
  var beneath = new Map();
  var current = null;
  var expanded = new Set();
  var dom = {};
  var listScroll = 0;
  var followedDetailLink = false;
  var wide = null;
  var shownCount = null;

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
  function deliveryUnavailable() { return data.outstanding.available === false; }

  // A delivery relation always writes its intent as intent:<slug>, while the node id may start
  // with outcome:, opportunity:, or capability:.  Resolve it to the exported node of that slug.
  function intentNodeId(id) {
    if (!isStr(id) || nodes.has(id) || id.indexOf('intent:') !== 0) { return id; }
    var found = intentBySlug.get(id.slice('intent:'.length));
    return found === undefined ? id : found;
  }

  function displayName(id) {
    var n = nodes.get(id);
    if (!n) { return id; }
    var h = isStr(n.heading) ? n.heading.trim() : '';
    for (var i = 0; i < NAME_LABELS.length; i++) {
      if (h.indexOf(NAME_LABELS[i]) === 0) { h = h.slice(NAME_LABELS[i].length).trim(); break; }
    }
    return h !== '' ? h : (slugOf(n) || id);
  }
  // Briefs and specs carry no slug field; their id is the slug behind a type prefix.
  function slugOf(n) {
    if (isStr(n.slug) && n.slug !== '') { return n.slug; }
    var cut = n.id.indexOf(':');
    return cut === -1 ? n.id : n.id.slice(cut + 1);
  }
  var nameKeys = new Map();
  function nameKey(id) {
    var k = nameKeys.get(id);
    if (k === undefined) { k = displayName(id).toLowerCase(); nameKeys.set(id, k); }
    return k;
  }
  function byName(a, b) { return cmp(nameKey(a), nameKey(b)) || cmp(a, b); }

  function statusOf(id) {
    var r = rec(id);
    if (r) { return isStr(r.status) ? r.status : ''; }
    var n = nodes.get(id);
    return n && isStr(n.status) ? n.status : '';
  }
  function statusWord(id) {
    var m = /^[A-Za-z]+/.exec(statusOf(id));
    return m === null ? '' : m[0];
  }
  function typeOf(id) {
    var n = nodes.get(id);
    return n && isStr(n.type) ? n.type : '';
  }
  function isOpen(id) { return openById.has(id); }

  function markKey(id) {
    var word = statusWord(id);
    if (own(ACTIVE_WORDS, word)) { return 'active'; }
    if (own(APPROVED_WORDS, word)) { return 'approved'; }
    if (!deliveryUnavailable() && !isOpen(id)) { return 'done'; }
    return 'draft';
  }

  function markEl(key, word) {
    var wrap = el('span', 'mark');
    wrap.setAttribute('data-mark', key);
    var g = add(wrap, el('span', 'mark-g', MARKS[key].glyph));
    g.setAttribute('aria-hidden', 'true');
    add(wrap, el('span', 'mark-w', word));
    return wrap;
  }
  function stateMark(id) {
    var word = statusWord(id);
    return markEl(markKey(id), word !== '' ? word : 'No status');
  }

  // Every ancestor list of a node, nearest first.  An open item carries its own; any other node
  // walks resolved parent pointers, stopping on a repeat.
  function ancestorLists(id) {
    var it = openById.get(id);
    if (it) {
      if (it.type === 'spec') {
        return arr(it.placements).map(function (pl) { return isObj(pl) ? arr(pl.ancestors) : []; })
          .filter(function (l) { return l.length > 0; });
      }
      return arr(it.ancestors).length ? [arr(it.ancestors)] : [];
    }
    var lists = [];
    var starts = [];
    if (rec(id)) {
      var p = resolvedParent(rec(id));
      if (p !== null) { starts.push(p); }
    } else {
      (edgesFrom.get(id) || []).forEach(function (e) {
        if (!e.state && isStr(e.to) && (e.field === 'Parent intent' || e.field === 'Brief' ||
          e.field === 'Discovery')) { starts.push(e.field === 'Discovery' ? intentNodeId(e.to) : e.to); }
      });
    }
    starts.forEach(function (start) {
      var list = [];
      var seen = new Set([id]);
      var at = start;
      while (at !== null && !seen.has(at)) {
        seen.add(at);
        list.push({ id: at });
        if (rec(at)) {
          at = resolvedParent(rec(at));
        } else {
          var up = (edgesFrom.get(at) || []).filter(function (e) {
            return !e.state && isStr(e.to) && e.field === 'Parent intent';
          });
          at = up.length ? up[0].to : null;
        }
      }
      lists.push(list);
    });
    return lists;
  }

  function buildIndexes() {
    data.nodes.forEach(function (n) { nodes.set(n.id, n); });
    recordIds = Object.keys(data.records).sort(cmp);
    recordIds.forEach(function (id) {
      var n = nodes.get(id);
      if (n && isStr(n.slug) && !intentBySlug.has(n.slug)) { intentBySlug.set(n.slug, id); }
    });
    recordIds.forEach(function (id) {
      var r = rec(id);
      var parent = resolvedParent(r);
      if (parent !== null && own(data.records, parent) !== undefined) { addTo(kidsOf, parent, id); }
      arr(r.delivery_relations).forEach(function (rel) {
        if (!isObj(rel)) { return; }
        [rel.intent, rel.brief, rel.spec].forEach(function (nid) {
          if (isStr(nid)) { addTo(relsByNode, nid, rel); }
        });
      });
    });
    kidsOf.forEach(function (list) { list.sort(byName); });
    data.edges.forEach(function (e) { addTo(edgesFrom, e.from, e); });
    if (!deliveryUnavailable()) {
      arr(data.outstanding.placed).concat(arr(data.outstanding.no_parent)).forEach(function (it) {
        if (isObj(it) && isStr(it.id) && !openById.has(it.id)) { openById.set(it.id, it); }
      });
      openById.forEach(function (it, id) {
        var seen = new Set();
        ancestorLists(id).forEach(function (list) {
          list.forEach(function (a) {
            if (isObj(a) && isStr(a.id) && !seen.has(a.id)) { seen.add(a.id); addTo(beneath, a.id, id); }
          });
        });
      });
    }
  }

  // ----------------------------------------------------------- the lists
  var STAGES = [['spec', 'Implementing'], ['spec', 'Approved'], ['brief', 'Executing'],
    ['brief', 'Ready'], ['intent', 'Accepted']];

  function hasNothingBeneath(id) {
    var r = rec(id);
    return r !== null && arr(r.children).length === 0 && arr(r.briefs).length === 0 &&
      arr(r.specs).length === 0;
  }
  function stageOf(id) {
    var type = typeOf(id);
    var word = statusWord(id);
    for (var i = 0; i < STAGES.length; i++) {
      if (STAGES[i][0] === type && STAGES[i][1] === word) {
        return (type !== 'intent' || hasNothingBeneath(id)) ? i : -1;
      }
    }
    return -1;
  }
  function startableIds() {
    var ids = [];
    openById.forEach(function (_it, id) { if (stageOf(id) >= 0) { ids.push(id); } });
    return ids.sort(function (a, b) { return (stageOf(a) - stageOf(b)) || byName(a, b); });
  }
  function openCount(id) { return (beneath.get(id) || []).length; }
  function capabilityIds() {
    return recordIds.filter(function (id) {
      return (rec(id).level || '') === 'capability' && openCount(id) > 0;
    }).sort(function (a, b) { return (openCount(b) - openCount(a)) || byName(a, b); });
  }
  function noParentIds() {
    if (deliveryUnavailable()) { return []; }
    return arr(data.outstanding.no_parent).filter(function (it) {
      return isObj(it) && isStr(it.id) && nodes.has(it.id);
    }).map(function (it) { return it.id; });
  }
  function brokenEntries() {
    var list = [];
    data.edges.forEach(function (e) {
      if (e.state) { list.push({ holder: e.from, edge: e }); }
    });
    if (!deliveryUnavailable()) {
      recordIds.forEach(function (id) {
        arr(rec(id).delivery_diagnostics).forEach(function (d) {
          if (isObj(d)) { list.push({ holder: id, diag: d }); }
        });
      });
    }
    return list.sort(function (a, b) { return byName(a.holder, b.holder); });
  }

  function questionCount(key) {
    if (key === 'browse') { return recordIds.length; }
    if (key === 'broken') { return brokenEntries().length; }
    if (deliveryUnavailable()) { return null; }
    if (key === 'next') { return startableIds().length; }
    if (key === 'capabilities') { return capabilityIds().length; }
    return noParentIds().length;
  }

  // --------------------------------------------------------------- routing
  function question(key) {
    for (var i = 0; i < QUESTIONS.length; i++) { if (QUESTIONS[i].key === key) { return QUESTIONS[i]; } }
    return QUESTIONS[0];
  }
  function parseRoute() {
    var p = new URLSearchParams(location.hash.replace(/^#/, ''));
    var route = {};
    ROUTE_KEYS.forEach(function (k) { route[k] = p.get(k) || ''; });
    route.q = question(route.q).key;
    return route;
  }
  function hashFor(over) {
    var r = Object.assign({}, current, over);
    var p = new URLSearchParams();
    ROUTE_KEYS.forEach(function (k) { if (r[k]) { p.set(k, r[k]); } });
    return '#' + p.toString();
  }
  function replaceRoute(over) {
    history.replaceState(null, '', hashFor(over));
    handleRoute();
  }
  function questionHash(key) {
    var over = { q: key, node: '', search: '' };
    FILTER_KEYS.forEach(function (k) { over[k] = ''; });
    return hashFor(over);
  }

  // ------------------------------------------------------------ small parts
  function helpId(kind, key) { return 'help-' + kind + '-' + key; }
  function labelChip(table, kind, key) {
    if (!isStr(key) || own(table, key) === undefined) { return null; }
    var chip = el('span', 'chip label-' + kind, key);
    // The key stays the visible text; its plain-words sentence is the chip's description.
    chip.setAttribute('aria-describedby', helpId(kind, key));
    return chip;
  }
  function stateChip(key) { return labelChip(STATE_HELP, 'state', key); }
  function trustChip(key) { return labelChip(TRUST_HELP, 'trust', key); }

  function nodeLink(id, cls) {
    var a = el('a', cls || 'node-link', displayName(id));
    a.setAttribute('href', hashFor({ node: id }));
    a.setAttribute('data-node', id);
    return a;
  }
  function outsideRef(id) {
    var s = el('span', 'outside');
    add(s, el('span', 'value', id));
    add(s, el('span', 'note-inline', 'outside this export'));
    return s;
  }
  function nodeRef(id, cls) { return nodes.has(id) ? nodeLink(id, cls) : outsideRef(id); }

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
    var line = add(li, el('div', 'edge-line'));
    if (withSource) { add(line, nodeRef(e.from, 'node-link')); }
    add(line, el('span', 'field', isStr(e.field) ? e.field : ''));
    if (e.state) {
      add(line, el('code', 'value', edgeValue(e)));
      var sc = stateChip(e.state);
      add(line, sc || el('span', 'value', String(e.state)));
    } else if (isStr(e.to)) {
      add(line, nodeRef(e.to, 'node-link'));
    } else {
      add(line, el('code', 'value', edgeValue(e)));
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
    var line = add(li, el('div', 'edge-line'));
    add(line, el('span', 'field', isStr(rel.type) ? rel.type : ''));
    [['intent', 'Intent'], ['brief', 'Brief'], ['spec', 'Spec']].forEach(function (pair) {
      var id = rel[pair[0]];
      if (!isStr(id)) { return; }
      add(line, el('span', 'part-name', pair[1]));
      add(line, nodeRef(pair[0] === 'intent' ? intentNodeId(id) : id, 'node-link'));
    });
    if (isStr(rel.route)) { add(line, el('span', 'value', 'route ' + rel.route)); }
    var tc = trustChip(rel.trust_class);
    if (tc) { add(line, tc); }
    return li;
  }

  function sourceBlock(id) {
    var wrap = el('p', 'source');
    var link = own(data.source_links, id);
    var n = nodes.get(id) || {};
    var url = isObj(link) && isStr(link.url) ? link.url : '';
    var kind = isObj(link) ? link.kind : '';
    var path = isObj(link) && isStr(link.path) ? link.path : (n.path || '');
    if ((kind === 'commit' || kind === 'latest') && url.indexOf(GITHUB_PREFIX) === 0) {
      var a = add(wrap, el('a', 'source-link', 'Open on GitHub'));
      a.setAttribute('href', url);
      a.setAttribute('rel', 'noopener noreferrer');
      add(wrap, el('span', 'value', path));
      if (kind === 'latest') {
        add(wrap, markEl('stale', 'may be newer than this export'));
      } else if (isStr(data.provenance.commit)) {
        add(wrap, el('span', 'note-inline', 'at commit ' + data.provenance.commit.slice(0, 12)));
      }
    } else {
      add(wrap, el('span', 'value', path));
      add(wrap, el('span', 'note-inline', 'no link available'));
    }
    return wrap;
  }

  // ------------------------------------------------------------------ rows
  var contexts = new Map();
  function contextText(id) {
    var known = contexts.get(id);
    if (known === undefined) { known = buildContext(id); contexts.set(id, known); }
    return known;
  }
  function buildContext(id) {
    var type = typeOf(id);
    var label = own(TYPE_NAMES, type) || type;
    var r = rec(id);
    if (r) { label += ' \u00B7 ' + (r.level || 'unrecorded'); }
    var lists = ancestorLists(id);
    if (lists.length && lists[0].length && isObj(lists[0][0]) && isStr(lists[0][0].id)) {
      var up = lists[0][0].id;
      label += ' \u00B7 under ' + (nodes.has(up) ? displayName(up) : up + ' outside this export');
    }
    if (r && isObj(r.parent_edge) && r.parent_edge.state) {
      var st = r.parent_edge.state;
      label += ' \u00B7 refused parent: ' + (own(STATE_HELP, st) !== undefined ? st : 'unrecognised');
    }
    return label;
  }

  // The context is a string, or a node when part of it needs its own element (a diagnostic code).
  function rowLink(id, mark, context) {
    var a = el('a', 'row-link');
    a.setAttribute('href', hashFor({ node: id }));
    a.setAttribute('data-node', id);
    add(a, el('span', 'c-name', displayName(id)));
    var state = add(a, el('span', 'c-state'));
    add(state, mark);
    if (isStr(context)) {
      add(a, el('span', 'c-context', context));
    } else {
      add(add(a, el('span', 'c-context')), context);
    }
    if (current !== null && current.node === id) { a.setAttribute('aria-current', 'true'); }
    return a;
  }
  function itemRow(id) {
    var li = el('li', 'row');
    add(li, rowLink(id, stateMark(id), contextText(id)));
    return li;
  }
  // A long list renders its first rows at once and the rest in later batches, so typing stays
  // responsive. Rows append below within their own list; a later group can shift down while
  // earlier batches land.
  var ROW_BATCH = 150;
  var listGeneration = 0;
  function rows(ids) {
    var ul = el('ul', 'rows');
    var generation = listGeneration;
    function fill(from) {
      if (generation !== listGeneration) { return; }
      var end = Math.min(ids.length, from + ROW_BATCH);
      for (var i = from; i < end; i++) { add(ul, itemRow(ids[i])); }
      if (end < ids.length) { setTimeout(function () { fill(end); }, 0); }
    }
    fill(0);
    return ul;
  }

  // ------------------------------------------------------------- list bodies
  function unavailableStatement() {
    var p = el('p', 'notice');
    text(p, 'Can\'t list open work: delivery mapping incomplete. Reason: ');
    add(p, el('span', 'value', isStr(data.outstanding.reason) ? data.outstanding.reason : 'unknown'));
    if (data.outstanding.limit !== undefined && data.outstanding.limit !== null) {
      text(p, ', limit ');
      add(p, el('span', 'value', String(data.outstanding.limit)));
    }
    text(p, '.');
    return p;
  }
  function emptyLine(message) { return el('p', 'empty', message); }

  function grouped(ids) {
    var frag = document.createDocumentFragment();
    TYPE_GROUPS.forEach(function (pair) {
      var these = ids.filter(function (id) { return typeOf(id) === pair[0]; }).sort(byName);
      if (!these.length) { return; }
      add(frag, el('h3', 'group-head', pair[1]));
      add(frag, rows(these));
    });
    return frag;
  }

  function filterOptions(key, ids) {
    var values = new Set();
    ids.forEach(function (id) {
      var r = rec(id);
      if (key === 'type') { values.add(typeOf(id)); }
      if (key === 'level' && r) { values.add(r.level || 'unrecorded'); }
      if (key === 'kind' && r && r.kind) { values.add(r.kind); }
      if (key === 'status' && r) { values.add(r.status || ''); }
    });
    return Array.from(values).sort(cmp);
  }
  function passes(id, route) {
    var r = rec(id);
    if (route.type && typeOf(id) !== route.type) { return false; }
    if (route.level && (!r || (r.level || 'unrecorded').toLowerCase() !== route.level.toLowerCase())) {
      return false;
    }
    if (route.kind && (!r || (r.kind || '').toLowerCase() !== route.kind.toLowerCase())) { return false; }
    if (route.status && (!r || (r.status || '') !== route.status)) { return false; }
    return true;
  }
  function activeFilters(route, q) {
    return (q.filters || []).filter(function (k) { return route[k] !== ''; });
  }
  function describeFilters(route, keys) {
    return keys.map(function (k) { return FILTER_LABELS[k][0].toLowerCase() + ' "' + route[k] + '"'; })
      .join(', ');
  }
  // The control is removed by the render its click causes, so focus is placed on a target that
  // stays: the list title (it takes focus), or the search field.
  function clearControl(label, over, focusTarget) {
    var b = button('action', label);
    b.addEventListener('click', function () {
      replaceRoute(over);
      focusTarget().focus();
    });
    return b;
  }
  function filteredEmpty(route, keys) {
    var box = el('div', 'empty');
    add(box, el('p', '', 'Nothing matches ' + describeFilters(route, keys) + '.'));
    var over = {};
    FILTER_KEYS.forEach(function (k) { over[k] = ''; });
    add(box, clearControl('Clear filters', over, function () { return dom.listTitle; }));
    return box;
  }

  function buildFilters(q, route, pool) {
    clear(dom.filters);
    var keys = q.filters || [];
    dom.filters.hidden = keys.length === 0 || route.search !== '';
    keys.forEach(function (key) {
      var field = add(dom.filters, el('div', 'field'));
      var id = 'filter-' + key;
      var label = add(field, el('label', '', FILTER_LABELS[key][0]));
      label.setAttribute('for', id);
      var select = add(field, el('select', 'control'));
      select.setAttribute('id', id);
      var first = add(select, el('option', '', FILTER_LABELS[key][1]));
      first.setAttribute('value', '');
      filterOptions(key, pool).forEach(function (v) {
        var o = add(select, el('option', '', key === 'type' ? (own(TYPE_NAMES, v) || v) : v));
        o.setAttribute('value', v);
      });
      select.value = route[key];
      select.addEventListener('change', function () {
        var over = {};
        over[key] = select.value;
        replaceRoute(over);
      });
    });
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
    return roots.sort(byName);
  }

  function treeRow(id, seen) {
    var li = el('li', 'row tree-row');
    var kids = kidsOf.get(id) || [];
    var sub = null;
    var toggle = null;
    if (kids.length) {
      toggle = add(li, button('toggle'));
      toggle.setAttribute('aria-expanded', 'false');
      var g = add(toggle, el('span', 'toggle-g', '\u25B8'));
      g.setAttribute('aria-hidden', 'true');
      add(toggle, el('span', 'visually-hidden', 'Show ' + kids.length + ' beneath ' + displayName(id)));
    } else {
      add(li, el('span', 'toggle-spacer')).setAttribute('aria-hidden', 'true');
    }
    add(li, rowLink(id, stateMark(id), contextText(id)));
    if (toggle) {
      var setOpen = function (open) {
        if (open && sub === null) {
          sub = el('ul', 'rows subtree');
          kids.forEach(function (kid) {
            if (seen.has(kid)) { return; }
            seen.add(kid);
            add(sub, treeRow(kid, seen));
          });
          li.appendChild(sub);
        }
        if (sub !== null) { sub.hidden = !open; }
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        toggle.firstChild.textContent = open ? '\u25BE' : '\u25B8';
        if (open) { expanded.add(id); } else { expanded.delete(id); }
      };
      toggle.addEventListener('click', function () {
        setOpen(toggle.getAttribute('aria-expanded') !== 'true');
      });
      if (expanded.has(id)) { setOpen(true); }
    }
    return li;
  }

  function brokenRow(entry) {
    var li = el('li', 'row');
    var context;
    if (entry.edge) {
      context = (isStr(entry.edge.field) ? entry.edge.field : 'Pointer') + ': ' +
        (own(STATE_HELP, entry.edge.state) !== undefined ? entry.edge.state : 'refused');
    } else {
      context = el('span');
      text(context, 'Delivery diagnostic: ');
      add(context, el('span', 'value', isStr(entry.diag.code) ? entry.diag.code : 'unknown'));
    }
    add(li, rowLink(entry.holder, markEl('broken', 'Broken'), context));
    return li;
  }

  // Each body builder fills dom.list and returns the count it shows.
  function bodyNext() {
    if (deliveryUnavailable()) { add(dom.list, unavailableStatement()); return null; }
    var ids = startableIds();
    if (!ids.length) { add(dom.list, emptyLine(question('next').empty)); return 0; }
    add(dom.list, rows(ids));
    return ids.length;
  }
  function bodyCapabilities() {
    if (deliveryUnavailable()) { add(dom.list, unavailableStatement()); return null; }
    var ids = capabilityIds();
    if (!ids.length) { add(dom.list, emptyLine(question('capabilities').empty)); return 0; }
    var ul = add(dom.list, el('ul', 'rows'));
    ids.forEach(function (id) {
      var li = add(ul, el('li', 'row'));
      add(li, rowLink(id, stateMark(id), contextText(id) + ' \u00B7 ' + openCount(id) + ' open'));
    });
    return ids.length;
  }
  function bodyNoParent(route) {
    if (deliveryUnavailable()) { add(dom.list, unavailableStatement()); return null; }
    var base = noParentIds();
    buildFilters(question('noparent'), route, base);
    if (!base.length) { add(dom.list, emptyLine(question('noparent').empty)); return 0; }
    var ids = base.filter(function (id) { return passes(id, route); });
    var keys = activeFilters(route, question('noparent'));
    if (!ids.length) { add(dom.list, filteredEmpty(route, keys)); return 0; }
    add(dom.list, grouped(ids));
    return ids.length;
  }
  function bodyBroken() {
    var entries = brokenEntries();
    if (deliveryUnavailable()) {
      add(dom.list, el('p', 'notice', 'Delivery diagnostics were unavailable: delivery mapping incomplete. Broken pointers are listed below.'));
    }
    if (!entries.length) { add(dom.list, emptyLine(question('broken').empty)); return 0; }
    var ul = add(dom.list, el('ul', 'rows'));
    entries.forEach(function (entry) { add(ul, brokenRow(entry)); });
    return entries.length;
  }
  function bodyBrowse(route) {
    var q = question('browse');
    buildFilters(q, route, recordIds);
    if (!recordIds.length) { add(dom.list, emptyLine(q.empty)); return 0; }
    var keys = activeFilters(route, q);
    if (keys.length) {
      var ids = recordIds.filter(function (id) { return passes(id, route); }).sort(byName);
      if (!ids.length) { add(dom.list, filteredEmpty(route, keys)); return 0; }
      add(dom.list, rows(ids));
      return ids.length;
    }
    var seen = new Set();
    var ul = add(dom.list, el('ul', 'rows tree'));
    treeRoots().forEach(function (id) {
      seen.add(id);
      add(ul, treeRow(id, seen));
    });
    return recordIds.length;
  }
  function bodySearch(route) {
    var want = route.search.toLowerCase();
    var ids = searchIndex().filter(function (entry) {
      return entry.slug.indexOf(want) !== -1 || entry.heading.indexOf(want) !== -1;
    }).map(function (entry) { return entry.id; });
    if (!ids.length) {
      var box = add(dom.list, el('div', 'empty'));
      add(box, el('p', '', 'Nothing matches the search "' + route.search + '".'));
      add(box, clearControl('Clear search', { search: '' }, function () { return dom.search; }));
      return 0;
    }
    add(dom.list, rows(ids));
    return ids.length;
  }
  // Every node once, already in name order, with its lowercased slug and heading.
  var searchEntries = null;
  function searchIndex() {
    if (searchEntries === null) {
      searchEntries = data.nodes.map(function (n) {
        return { id: n.id, slug: slugOf(n).toLowerCase(),
          heading: (isStr(n.heading) ? n.heading : '').toLowerCase() };
      }).sort(function (a, b) { return byName(a.id, b.id); });
    }
    return searchEntries;
  }
  var BODIES = { next: bodyNext, capabilities: bodyCapabilities, noparent: bodyNoParent,
    broken: bodyBroken, browse: bodyBrowse };

  function emptyCorpus() { return data.nodes.length === 0; }

  function renderList(route, announce) {
    var q = question(route.q);
    listGeneration += 1;
    clear(dom.list);
    clear(dom.filters);
    dom.filters.hidden = true;
    var count;
    if (route.search !== '') {
      dom.listTitle.textContent = escapeDisplay('Search results for "' + route.search + '"');
      dom.listLead.textContent = 'Intents, briefs and specs whose name or id contains the search.';
      dom.listSort.textContent = 'By name';
      count = bodySearch(route);
    } else if (emptyCorpus()) {
      dom.listTitle.textContent = q.title;
      dom.listLead.textContent = q.key === 'next' ? q.lead : '';
      dom.listSort.textContent = q.sort;
      var box = add(dom.list, el('div', 'empty'));
      add(box, el('p', '', 'No intents, briefs or specs found under this root.'));
      add(box, el('p', 'note', 'The export reads docs/product/intents, docs/product/briefs and docs/specs.'));
      count = 0;
    } else {
      dom.listTitle.textContent = q.title;
      dom.listLead.textContent = q.lead;
      dom.listSort.textContent = q.sort;
      count = BODIES[q.key](route);
    }
    shownCount = count;
    var noun = route.search !== '' ? ['result', 'results'] : q.noun;
    dom.listCount.textContent = count === null ? 'Count unavailable' : plural(count, noun);
    if (announce) {
      dom.live.textContent = escapeDisplay(dom.listTitle.textContent + ', ' + dom.listCount.textContent);
    }
    performance.mark('list-updated');
  }

  function markSelected(route) {
    var links = dom.list.querySelectorAll('a.row-link');
    for (var i = 0; i < links.length; i++) {
      if (links[i].getAttribute('data-node') === route.node) {
        links[i].setAttribute('aria-current', 'true');
      } else {
        links[i].removeAttribute('aria-current');
      }
    }
  }

  // ---------------------------------------------------------------- detail
  function nextStep(id) {
    if (deliveryUnavailable()) {
      return 'No next step shown: delivery mapping was incomplete, so this snapshot cannot tell what is open.';
    }
    var type = typeOf(id);
    var word = statusWord(id);
    if (!isOpen(id)) { return 'Nothing to do. It is ' + (word !== '' ? word : 'not open') + '.'; }
    if (type === 'spec') {
      if (word === 'Implementing') { return 'Continue building it with the work-loop skill. It is already being built.'; }
      if (word === 'Approved') { return 'Build it with the work-loop skill. It is approved, and work-loop checks readiness before it starts.'; }
      return 'Finish the spec with the new-spec skill. It needs approval before it is built.';
    }
    if (type === 'brief') {
      return 'Work on it with the author-delivery-brief skill in continue mode. Briefs are delivered through their slices.';
    }
    if (word === 'Accepted') {
      if (hasNothingBeneath(id)) {
        return 'Decompose it with the intent skill. It is accepted but has nothing beneath it yet.';
      }
      return openCount(id) > 0 ? 'Pick an item from Open beneath. Its work is already decomposed.' :
        'Close it with the close-work skill if its outcome is met. Everything beneath it is finished.';
    }
    return 'Keep shaping it with the intent skill. It is not accepted yet.';
  }

  function brokenOf(id) {
    var list = (edgesFrom.get(id) || []).filter(function (e) { return e.state; })
      .map(function (e) { return { holder: id, edge: e }; });
    if (!deliveryUnavailable() && rec(id)) {
      arr(rec(id).delivery_diagnostics).forEach(function (d) {
        if (isObj(d)) { list.push({ holder: id, diag: d }); }
      });
    }
    return list;
  }

  function part(title) {
    var sec = add(dom.detailBody, el('section', 'part'));
    add(sec, el('h3', 'part-head', title));
    return sec;
  }

  function stateLine(id) {
    var p = el('p', 'state-line');
    add(p, stateMark(id));
    var open = deliveryUnavailable() ? null : openCount(id);
    text(p, ' \u00B7 ' + (own(TYPE_NAMES, typeOf(id)) || typeOf(id)) + ' \u00B7 ' +
      (open === null ? 'open work unknown' : open + ' open beneath') + ' \u00B7 ' +
      brokenOf(id).length + ' broken');
    return p;
  }

  function factList(dl, name, value) {
    var row = add(dl, el('div', 'fact'));
    add(row, el('dt', 'fact-name', name));
    add(add(row, el('dd', 'fact-value')), el('span', 'value', value));
  }
  function group(parent, key, build) {
    var sec = add(parent, el('section', 'group'));
    add(sec, el('h4', 'group-label label-group', own(GROUP_LABELS, key)));
    build(sec);
  }
  function groupList(sec, items, make) {
    if (items.length === 0) { add(sec, el('p', 'empty', 'None.')); return; }
    var ul = add(sec, el('ul', 'plain'));
    items.forEach(function (it) { add(ul, make(it)); });
  }
  function refLine(id) {
    var li = el('li', 'edge');
    add(add(li, el('div', 'edge-line')), nodeRef(id, 'node-link'));
    return li;
  }

  function unavailableDetail() {
    var p = el('p', 'notice');
    text(p, 'Delivery mapping was unavailable, so this export holds no delivery facts. Reason: ');
    add(p, el('span', 'value', isStr(data.outstanding.reason) ? data.outstanding.reason : 'unknown'));
    text(p, '.');
    return p;
  }

  function recordDetails(id) {
    var n = nodes.get(id);
    var r = rec(id);
    var box = add(dom.detailBody, el('details', 'record'));
    add(box, el('summary', '', 'Record details'));
    var dl = add(box, el('dl', 'facts'));
    factList(dl, 'Id', id);
    factList(dl, 'Path', n.path || '');
    factList(dl, 'Type', n.type || '');
    if (r) {
      factList(dl, 'Level', r.level || 'unrecorded');
      factList(dl, 'Kind', r.kind || 'none recorded');
    }
    factList(dl, 'Status', statusOf(id));
    var unavailable = deliveryUnavailable();
    if (r) {
      group(box, 'parent', function (sec) {
        groupList(sec, isObj(r.parent_edge) ? [r.parent_edge] : [], function (e) { return edgeItem(e, false); });
      });
      group(box, 'children', function (sec) { groupList(sec, arr(r.children), refLine); });
      group(box, 'briefs', function (sec) { groupList(sec, arr(r.briefs), refLine); });
      group(box, 'specs', function (sec) { groupList(sec, arr(r.specs), refLine); });
      if (unavailable) {
        add(box, unavailableDetail());
      } else {
        group(box, 'relations', function (sec) { groupList(sec, arr(r.delivery_relations), relationItem); });
        group(box, 'diagnostics', function (sec) {
          groupList(sec, arr(r.delivery_diagnostics), function (d) {
            var li = el('li', 'edge');
            add(add(li, el('div', 'edge-line')), el('span', 'value', describe(d)));
            return li;
          });
        });
      }
      group(box, 'relatedHere', function (sec) {
        groupList(sec, arr(r.related_written_here), function (e) { return edgeItem(e, false); });
      });
      group(box, 'relatedElsewhere', function (sec) {
        groupList(sec, arr(r.related_written_elsewhere), function (e) { return edgeItem(e, true); });
      });
    } else {
      group(box, 'pointers', function (sec) {
        groupList(sec, edgesFrom.get(id) || [], function (e) { return edgeItem(e, false); });
      });
      if (unavailable) {
        add(box, unavailableDetail());
      } else {
        group(box, 'relations', function (sec) { groupList(sec, relsByNode.get(id) || [], relationItem); });
      }
    }
  }

  var STAGE_NOUNS = [['Implementing spec', 'Implementing specs'], ['Approved spec', 'Approved specs'],
    ['Executing brief', 'Executing briefs'], ['Ready brief', 'Ready briefs'],
    ['Accepted intent with nothing beneath', 'Accepted intents with nothing beneath']];
  // A plain count of what the list holds, from fixed words and numbers only.
  function listSummary(route) {
    if (shownCount === null || emptyCorpus()) { return ''; }
    if (route.search === '' && route.q === 'next') {
      var per = STAGES.map(function () { return 0; });
      startableIds().forEach(function (id) { per[stageOf(id)] += 1; });
      var parts = [];
      per.forEach(function (n, i) { if (n > 0) { parts.push(plural(n, STAGE_NOUNS[i])); } });
      return parts.length ? 'In this list: ' + parts.join(', ') + '.' : '';
    }
    var noun = route.search !== '' ? ['result', 'results'] : question(route.q).noun;
    return 'This list holds ' + plural(shownCount, noun) + '.';
  }

  function renderDetail(route) {
    clear(dom.detailBody);
    var id = route.node;
    dom.main.toggleAttribute('data-picked', id !== '' && nodes.has(id));
    if (!id) {
      dom.detailHeading.textContent = 'Details';
      add(dom.detailBody, el('p', 'note', 'Pick an item to see its next step.'));
      var summary = listSummary(route);
      if (summary !== '') { add(dom.detailBody, el('p', 'list-summary', summary)); }
      return;
    }
    if (!nodes.has(id)) {
      dom.detailHeading.textContent = 'Details';
      add(dom.detailBody, el('p', 'note', 'That item is not in this snapshot.'));
      return;
    }
    dom.detailHeading.textContent = escapeDisplay(displayName(id));
    var back = add(dom.detailBody, button('action back-link', 'Back to list'));
    back.addEventListener('click', function () { backToList(id); });
    add(dom.detailBody, stateLine(id));

    add(part('Next step'), el('p', 'next-step', nextStep(id)));

    var openSec = part('Open beneath');
    var under = deliveryUnavailable() ? null : (beneath.get(id) || []);
    if (under === null) {
      add(openSec, el('p', 'empty', 'Open work unknown: delivery mapping incomplete.'));
    } else if (!under.length) {
      add(openSec, el('p', 'empty', 'Nothing open beneath.'));
    } else {
      TYPE_GROUPS.forEach(function (pair) {
        var these = under.filter(function (u) { return typeOf(u) === pair[0]; }).sort(byName);
        if (!these.length) { return; }
        add(openSec, el('h4', 'group-label', pair[1]));
        var ul = add(openSec, el('ul', 'plain'));
        these.forEach(function (u) {
          var li = add(ul, el('li', 'beneath-row'));
          add(li, nodeLink(u, 'node-link'));
          add(li, stateMark(u));
        });
      });
    }

    var brokenSec = part('What is broken');
    var broken = brokenOf(id);
    if (deliveryUnavailable()) { add(brokenSec, el('p', 'note', 'Delivery diagnostics were unavailable.')); }
    if (!broken.length) {
      add(brokenSec, el('p', 'empty', 'Nothing broken here.'));
    } else {
      var bl = add(brokenSec, el('ul', 'plain'));
      broken.forEach(function (b) {
        var li = add(bl, el('li', 'edge'));
        if (b.edge) {
          add(li, edgeItem(b.edge, false).firstChild);
          if (own(STATE_HELP, b.edge.state) !== undefined) {
            add(li, el('p', 'meaning', own(STATE_HELP, b.edge.state)));
          }
        } else {
          var line = add(li, el('div', 'edge-line'));
          add(line, el('span', 'field', 'Delivery diagnostic'));
          add(line, el('span', 'value', isStr(b.diag.code) ? b.diag.code : 'unknown'));
          add(li, el('p', 'meaning', describe(b.diag)));
        }
      });
    }

    var sits = part('Where it sits');
    var lists = ancestorLists(id);
    if (!lists.length) {
      add(sits, el('p', 'empty', 'No parent.'));
    } else {
      lists.forEach(function (list) {
        var trail = add(sits, el('p', 'trail'));
        list.slice().reverse().forEach(function (a, i) {
          if (i > 0) { add(trail, el('span', 'sep', ' \u203A ')).setAttribute('aria-hidden', 'true'); }
          if (!isObj(a) || !isStr(a.id)) { return; }
          var step = add(trail, el('span', 'trail-step'));
          add(step, nodeRef(a.id, 'node-link'));
          if (nodes.has(a.id)) { text(step, ' '); add(step, stateMark(a.id)); }
        });
      });
    }

    add(part('Open the file'), sourceBlock(id));
    recordDetails(id);
  }

  function rowLinkFor(id) {
    var links = dom.list.querySelectorAll('a.row-link');
    for (var i = 0; i < links.length; i++) {
      if (links[i].getAttribute('data-node') === id) { return links[i]; }
    }
    return null;
  }

  function backToList(id) {
    location.hash = hashFor({ node: '' });
    // The list is hidden while a row is picked; show it now so the row can take focus.
    dom.main.removeAttribute('data-picked');
    window.scrollTo(0, listScroll);
    var target = rowLinkFor(id);
    (target || dom.listTitle).focus();
  }

  // ------------------------------------------------------------ page chrome
  // The time to the minute in UTC; any other form is shown as written.
  function generatedText(value) {
    if (!isStr(value) || value === '') { return 'at an unknown time'; }
    var m = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]00:00)$/.exec(value);
    return m === null ? value : m[1] + ' ' + m[2] + ' UTC';
  }
  function sumValues(obj) {
    var total = 0;
    if (!isObj(obj)) { return total; }
    Object.keys(obj).forEach(function (k) { if (typeof obj[k] === 'number') { total += obj[k]; } });
    return total;
  }

  function renderMeta() {
    var s = data.summary;
    var scoped = isStr(data.scope.from);
    dom.meta.textContent = escapeDisplay('Read-only snapshot generated ' +
      generatedText(data.provenance.generated_at) + '. ' + sumValues(s.intents_by_level) +
      ' intents, ' + s.briefs + ' briefs and ' + s.specs + ' specs' +
      (scoped ? ' in the whole corpus' : '') +
      '. Record text is shown as plain text and never run.');
    if (scoped) {
      dom.banner.hidden = false;
      clear(dom.banner);
      text(dom.banner, 'Scoped export: the questions cover ');
      add(dom.banner, nodeRef(data.scope.from, 'node-link'));
      text(dom.banner, ' and everything beneath it. The totals above cover the whole corpus.');
    }
  }

  // The five links are built once, so a link that has focus keeps it across routes; a route only
  // moves aria-current.  The counts come from the data, which never changes, so they are set here.
  function buildNav() {
    QUESTIONS.forEach(function (q) {
      var li = add(dom.questions, el('li', 'question'));
      var a = add(li, el('a', 'question-link'));
      a.setAttribute('href', questionHash(q.key));
      a.setAttribute('data-q', q.key);
      add(a, el('span', 'q-name', q.name));
      if (q.key !== 'browse') {
        var count = emptyCorpus() ? 0 : questionCount(q.key);
        add(a, el('span', 'q-count', count === null ? 'unknown' : String(count)));
      }
    });
  }
  function markNav(route) {
    var links = dom.questions.querySelectorAll('a.question-link');
    for (var i = 0; i < links.length; i++) {
      if (links[i].getAttribute('data-q') === route.q) {
        links[i].setAttribute('aria-current', 'page');
      } else {
        links[i].removeAttribute('aria-current');
      }
    }
  }

  function renderKey() {
    var dl = add(dom.keyBody, el('dl', 'key-list'));
    function row(term, def, id) {
      var r = add(dl, el('div', 'fact'));
      var dt = add(r, el('dt', 'fact-name'));
      add(dt, term);
      var dd = add(r, el('dd', 'fact-value', def));
      if (id) { dd.setAttribute('id', id); }
    }
    MARK_ORDER.forEach(function (key) {
      var words = { active: 'Implementing, Executing', approved: 'Approved, Accepted, Ready',
        draft: 'Draft and other open states', broken: 'Broken', stale: 'Stale', done: 'Closed states' };
      row(markEl(key, words[key]), MARKS[key].help);
    });
    GROUP_ORDER.forEach(function (key) {
      row(el('span', 'label-group', own(GROUP_LABELS, key)), own(GROUP_HELP, key));
    });
    [['state', STATE_HELP], ['trust', TRUST_HELP]].forEach(function (pair) {
      Object.keys(pair[1]).forEach(function (key) {
        row(el('span', 'chip label-' + pair[0], key), own(pair[1], key), helpId(pair[0], key));
      });
    });
  }

  function handleRoute() {
    var next = parseRoute();
    var prev = current;
    current = next;
    var listChanged = prev === null || ['q', 'search'].concat(FILTER_KEYS).some(function (k) {
      return prev[k] !== next[k];
    });
    var nodeChanged = prev === null || prev.node !== next.node;
    if (dom.search.value !== next.search) { dom.search.value = next.search; }
    markNav(next);
    // A filter select is rebuilt with the list; keep the reader on the one they were using.
    var held = document.activeElement;
    var heldFilter = held && held.closest && held.closest('#filters') ? held.id : '';
    if (listChanged) {
      renderList(next, prev !== null);
      if (heldFilter !== '') {
        var again = byIdEl(heldFilter);
        if (again) { again.focus(); }
      }
    } else if (nodeChanged) {
      markSelected(next);
    }
    if (nodeChanged || listChanged) { renderDetail(next); }
    if (prev !== null && nodeChanged && !listChanged && next.node !== '' && nodes.has(next.node)) {
      var fromDetail = followedDetailLink;
      followedDetailLink = false;
      if (wide.matches && !fromDetail) {
        dom.live.textContent = escapeDisplay('Showing ' + displayName(next.node));
      } else {
        dom.detailHeading.focus();
      }
    } else if (prev !== null && prev.node !== '' && next.node === '' && !wide.matches) {
      // The detail that held focus is gone (browser Back, for one): return to the picked row.
      var active = document.activeElement;
      // Focus inside the detail is about to be lost: the zone is hidden by this very render.
      if (!active || active === document.body || (active.closest && active.closest('.detail'))) {
        window.scrollTo(0, listScroll);
        (rowLinkFor(prev.node) || dom.listTitle).focus();
      }
    }
  }

  function showDamaged() {
    var main = byIdEl('main');
    var alertBox = el('div', 'alert', 'This file is damaged and cannot be shown. Export it again.');
    alertBox.setAttribute('role', 'alert');
    main.replaceChildren(alertBox);
    byIdEl('app').hidden = false;
    byIdEl('questions-nav').hidden = true;
    var field = byIdEl('search').parentNode;
    field.parentNode.removeChild(field);
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
        search: byIdEl('search'), questions: byIdEl('question-list'), main: byIdEl('main'),
        listTitle: byIdEl('list-title'), listLead: byIdEl('list-lead'),
        listCount: byIdEl('list-count'), listSort: byIdEl('list-sort'),
        filters: byIdEl('filters'), keyBody: byIdEl('key-body'), list: byIdEl('list'),
        detailHeading: byIdEl('detail-heading'), detailBody: byIdEl('detail-body'),
        skip: byIdEl('skip-details')
      };
      wide = window.matchMedia('(min-width: 40rem)');
      buildIndexes();
      renderMeta();
      renderKey();
      buildNav();
      dom.search.addEventListener('input', function () {
        // Below 40rem a picked item hides the list, so a search drops the pick to show its results.
        var over = { search: dom.search.value };
        if (!wide.matches && dom.search.value !== '') { over.node = ''; }
        replaceRoute(over);
      });
      dom.search.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape' && dom.search.value !== '') {
          ev.preventDefault();
          replaceRoute({ search: '' });
        }
      });
      dom.skip.addEventListener('click', function () { dom.detailHeading.focus(); });
      dom.detailBody.addEventListener('click', function (ev) {
        var link = ev.target.closest ? ev.target.closest('a.node-link') : null;
        // A link to the item already shown changes no route, so it must not mark the next one.
        if (link && link.getAttribute('href') !== location.hash) { followedDetailLink = true; }
      });
      dom.list.addEventListener('click', function (ev) {
        var link = ev.target.closest ? ev.target.closest('a.row-link') : null;
        if (link) { followedDetailLink = false; listScroll = window.scrollY; }
      });
      byIdEl('app').hidden = false;
      handleRoute();
      window.addEventListener('hashchange', handleRoute);
      performance.mark('view-ready');
    } catch (err) {
      showDamaged();
      // The alert is the reader's message; the error stays visible to whoever debugs the page.
      console.error('Intent view could not render:', err);
    }
  }

  start();
})();
