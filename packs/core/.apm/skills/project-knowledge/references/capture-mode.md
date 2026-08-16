# Capture Mode

Validate one captured-observation producer request and hand it to `capture_observation`.

This mode reads one strict JSON request from standard input, writes only the derived captured-observation journal partition, and returns the capture receipt. It cannot read topics, query observation journals, or choose storage paths.
