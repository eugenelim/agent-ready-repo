  // ----------------------------------------------------------- roadmap
  // The roadmap body: the list header already shows the title, count and sort key.
  function bodyRoadmap() {
    var ids = capabilityRecordIds();
    if (!ids.length) { add(dom.list, emptyLine(question('roadmap').empty)); }
    return ids.length;
  }
