# Pre existing captured item link refusal order dependence

- **Status:** Open
- **Kind:** defect

The core pack's `test_captured_item_files_repair.py::test_write_record_refuses_a_link_in_any_directory_segment` fails when run alone or first in a pytest-xdist worker (3 failed in isolation): the engine handle it uses is bound only after an earlier test in the same process calls `main`. Sequential runs of the suite pass. A fixture that binds the engine before the test would remove the order dependence.
