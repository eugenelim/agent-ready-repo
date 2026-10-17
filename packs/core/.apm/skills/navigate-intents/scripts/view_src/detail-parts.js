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

  // Each distinct value the intent writes in Depends on, by written position: the resolved ones
  // (from its edges' basis) and the refused or out-of-scope ones (its pointer diagnostics).
  function dependsWrittenHere(id) {
    var items = [];
    (depEdgesFrom.get(id) || []).forEach(function (e) {
      var values = isObj(e.basis) ? arr(e.basis.values) : [];
      values.forEach(function (v) {
        if (isObj(v) && isStr(v.value)) {
          items.push({ value: v.value, form: v.form, position: posOf(v), trust: e.trust_class, to: e.to });
        }
      });
    });
    (depPointers.get(id) || []).forEach(function (d) {
      items.push({ value: isStr(d.value) ? d.value : '', form: d.form, position: posOf(d),
        trust: d.trust_class, state: d.state });
    });
    return items.sort(function (a, b) { return (a.position - b.position) || cmp(a.value, b.value); });
  }
  function dependsHereItem(it) {
    var li = el('li', 'edge');
    var line = add(li, el('div', 'edge-line'));
    add(line, el('code', 'value', it.value));
    var fc = formChip(it.form);
    if (fc) { add(line, fc); }
    if (isStr(it.to)) {
      add(line, namedIntent(it.to));
    } else {
      add(line, stateChip(it.state) || el('span', 'value', String(it.state)));
    }
    var tc = trustChip(it.trust);
    if (tc) { add(line, tc); }
    return li;
  }
  // Intents whose resolved edge names this one, once each, in name order.
  function dependsWrittenElsewhere(id) {
    var seen = new Map();
    (depEdgesTo.get(id) || []).forEach(function (e) { if (!seen.has(e.from)) { seen.set(e.from, e); } });
    return Array.from(seen.keys()).sort(byName).map(function (from) { return seen.get(from); });
  }
  function dependsElsewhereItem(e) {
    var li = el('li', 'edge');
    var line = add(li, el('div', 'edge-line'));
    add(line, namedIntent(e.from));
    var tc = trustChip(e.trust_class);
    if (tc) { add(line, tc); }
    return li;
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
      group(box, 'dependsHere', function (sec) { groupList(sec, dependsWrittenHere(id), dependsHereItem); });
      group(box, 'dependsElsewhere', function (sec) {
        groupList(sec, dependsWrittenElsewhere(id), dependsElsewhereItem);
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

