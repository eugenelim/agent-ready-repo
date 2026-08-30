# Retrieval evaluation

A corpus that has never been measured has no retrieval quality, only intent.

Declare the prompts and their expected topics **before** the run that measures
them. An expectation written after the observation records what happened, not
what should.

Measure with a context that has not seen the expectations. A measurer who knows
the intended answer reproduces it, and the record becomes a restatement of hope.

Carry a negative set: prompts from outside the corpus's subject that should
return nothing. Without them precision cannot be falsified, and a corpus that
answers everything scores perfectly. Pin the negative set's size on both sides,
or the bar can always be met by dropping prompts.

Bind the record to the tree it measured — the authoring source, the router, and
the generated tree — so a stale record cannot read as a passing one.

Treat every prompt where two topics both fire as a corpus defect, not a
measurement error. The fix is a routing signal, not a re-run.
