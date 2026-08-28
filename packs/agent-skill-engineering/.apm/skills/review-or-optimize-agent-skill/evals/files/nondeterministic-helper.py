import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# Seeded defect, deliberately retained: the output varies per run, so the
# caller's contract cannot promise identical managed output (ASE-DET-01).
print(f"generated={datetime.now().isoformat()}")
