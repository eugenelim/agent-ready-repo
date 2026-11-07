"""Fieldlog command line (excerpt)."""
import argparse


def note_add(text: str) -> None:
    print(f"note added: {text}")


def sync_now() -> None:
    print("sync: 1 sent, 0 received")


def sync_status() -> None:
    print("pending=0 last_sync=ok")


def main() -> None:
    parser = argparse.ArgumentParser(prog="fieldlog")
    sub = parser.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("note")
    add.add_argument("action", choices=["add"])
    add.add_argument("text")
    sync = sub.add_parser("sync")
    sync.add_argument("action", choices=["now", "status"])
    args = parser.parse_args()
    if args.cmd == "note":
        note_add(args.text)
    elif args.action == "now":
        sync_now()
    else:
        sync_status()
