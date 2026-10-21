  // ---------------------------------------------------------------- owners
  // The owner key compares owners: runs of spaces and tabs become one space, the ends are
  // trimmed, and only A to Z are lowered. toLowerCase would also change other letters.
  function ownerKey(value) {
    if (!isStr(value)) { return ''; }
    return value.replace(/[ \t]+/g, ' ').replace(/^ | $/g, '').replace(/[A-Z]/g, function (c) {
      return String.fromCharCode(c.charCodeAt(0) + 32);
    });
  }
  // Code-point order, as the payload's ids and the option keys are ordered.
  function codePointCmp(a, b) {
    var x = Array.from(a);
    var y = Array.from(b);
    var n = Math.min(x.length, y.length);
    for (var i = 0; i < n; i++) {
      var d = x[i].codePointAt(0) - y[i].codePointAt(0);
      if (d !== 0) { return d < 0 ? -1 : 1; }
    }
    return cmp(x.length, y.length);
  }
  var OWNER_NONE = 'none';
  var NO_OWNER_TEXT = 'No owner recorded';
  var ownerChoices = null;
  // The options of the Owner control: Any owner, one per non-empty key (labelled by the owner of
  // the first node, by id, that holds the key), then No owner recorded when a node has no owner.
  function ownerOptions() {
    if (ownerChoices !== null) { return ownerChoices; }
    var labels = new Map();
    var holders = new Map();
    var anyEmpty = false;
    data.nodes.forEach(function (n) {
      var key = ownerKey(n.owner);
      if (key === '') { anyEmpty = true; return; }
      if (!labels.has(key) || codePointCmp(n.id, holders.get(key)) < 0) {
        labels.set(key, n.owner);
        holders.set(key, n.id);
      }
    });
    ownerChoices = [{ value: '', label: 'Any owner' }];
    Array.from(labels.keys()).sort(codePointCmp).forEach(function (key) {
      ownerChoices.push({ value: 'k:' + key, label: labels.get(key) });
    });
    if (anyEmpty) { ownerChoices.push({ value: OWNER_NONE, label: NO_OWNER_TEXT }); }
    return ownerChoices;
  }
  function ownerChoiceValid(value) {
    return value !== '' && ownerOptions().some(function (o) { return o.value === value; });
  }
  // A node is a matching record when its owner key is the chosen one. Any owner matches all.
  function ownerMatches(id, choice) {
    if (choice === '') { return true; }
    var n = nodes.get(id);
    var key = n ? ownerKey(n.owner) : '';
    return key === (choice === OWNER_NONE ? '' : choice.slice(2));
  }
  function ownerText(id) {
    var n = nodes.get(id);
    return n && ownerKey(n.owner) !== '' ? 'Owner: ' + n.owner : NO_OWNER_TEXT;
  }
  function ownerCell(id) { return el('span', 'c-owner', ownerText(id)); }

  function buildOwnerControl() {
    var field = dom.owner;
    var label = add(field, el('label', 'field', 'Owner'));
    label.setAttribute('for', 'owner');
    var select = add(field, el('select', 'control'));
    select.setAttribute('id', 'owner');
    ownerOptions().forEach(function (o) {
      var option = add(select, el('option', '', o.label));
      option.setAttribute('value', o.value);
    });
    select.addEventListener('change', function () { replaceRoute({ owner: select.value }); });
  }
  function syncOwnerControl(route) {
    var select = byIdEl('owner');
    if (select && select.value !== route.owner) { select.value = route.owner; }
  }

