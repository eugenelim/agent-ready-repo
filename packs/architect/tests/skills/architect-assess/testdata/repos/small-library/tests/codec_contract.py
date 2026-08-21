"""Public contract test fixture (not collected by the catalogue suite)."""

from token_codec import decode, encode


def check_round_trip() -> None:
    key = b"fixture-key"
    assert decode(encode("payload", key), key) == "payload"
