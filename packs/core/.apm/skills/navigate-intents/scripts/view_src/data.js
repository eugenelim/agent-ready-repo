  // ------------------------------------------------------------------ data
  var data = null;
  var readiness = null;
  var nodes = new Map();
  var recordIds = [];
  var kidsOf = new Map();
  var relsByNode = new Map();
  var intentBySlug = new Map();
  var edgesFrom = new Map();
  var openById = new Map();
  var beneath = new Map();
  // Dependency records, indexed once: edges by waiting intent, neighbours each way, pointer
  // diagnostics by source, and the payload's cycle diagnostics by member.
  var depEdgesFrom = new Map();
  var depOut = new Map();
  var depIn = new Map();
  var depEdgesTo = new Map();
  var depPointers = new Map();
  var depCycles = new Map();
  var depCycleList = [];
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

  function validFinding(f) {
    return isObj(f) && isStr(f.code) && isStr(f.next_action) && typeof f.known === 'boolean';
  }
  // The shape the export writes.  A member that fails it is read as unchecked, never as damage.
  function validReadiness(r) {
    if (!isObj(r)) { return false; }
    if (r.checked === false) {
      return r.reason === 'not_requested' || (isStr(r.reason) && own(REASON_TEXT, r.reason) !== undefined);
    }
    var s = r.start;
    return r.checked === true && Array.isArray(r.active) && r.active.every(isStr) &&
      Array.isArray(r.ready) && r.ready.every(isStr) && Array.isArray(r.blocked) &&
      r.blocked.every(function (b) {
        return isObj(b) && isStr(b.id) && Array.isArray(b.findings) && b.findings.every(validFinding);
      }) && isObj(s) && own(START_RULES, s.rule) === true && (s.id === null || isStr(s.id)) &&
      typeof s.held === 'boolean' && Number.isInteger(s.active_count) && s.active_count >= 0;
  }
  // An export made before this member existed has none: that is the quiet default.
  function readReadiness(raw) {
    if (raw === undefined) { return { checked: false, reason: 'not_requested' }; }
    return validReadiness(raw) ? raw : { checked: false, reason: 'wrong_schema' };
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

  function indexDependencies() {
    var dep = isObj(data.dependencies) ? data.dependencies : {};
    arr(dep.edges).forEach(function (e) {
      if (!isObj(e) || !isStr(e.from) || !isStr(e.to)) { return; }
      addTo(depEdgesFrom, e.from, e);
      addTo(depEdgesTo, e.to, e);
      addTo(depOut, e.from, e.to);
      addTo(depIn, e.to, e.from);
    });
    arr(dep.diagnostics).forEach(function (d) {
      if (!isObj(d)) { return; }
      if (d.state === 'cycle' && Array.isArray(d.members)) {
        var cycle = { members: d.members.filter(isStr).sort(byName) };
        if (!cycle.members.length) { return; }
        depCycleList.push(cycle);
        cycle.members.forEach(function (m) { addTo(depCycles, m, cycle); });
      } else if (isStr(d.from) && isStr(d.state)) {
        addTo(depPointers, d.from, d);
      }
    });
    depPointers.forEach(function (list) {
      list.sort(function (a, b) { return posOf(a) - posOf(b); });
    });
  }
  function posOf(item) { return typeof item.position === 'number' ? item.position : 0; }

  function buildIndexes() {
    readiness = readReadiness(data.readiness);
    data.nodes.forEach(function (n) { nodes.set(n.id, n); });
    indexDependencies();
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

