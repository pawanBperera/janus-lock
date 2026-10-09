"""
cli.py — command-line interface for Janus Lock.

Three commands, kept deliberately simple:

    python -m januslock.cli init <vault>       create a new vault
    python -m januslock.cli show <vault>       unlock and print contents
    python -m januslock.cli set  <vault>       unlock, replace contents

Each command prompts for the password interactively. We never take
passwords as command-line arguments, because those show up in your
shell history and in `ps` output — a real security footgun.
"""

import argparse
import getpass
import sys
from pathlib import Path

from januslock import storage


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.vault)
    if path.exists():
        print(f"Error: {path} already exists. Refusing to overwrite.", file=sys.stderr)
        return 1

    password = getpass.getpass("New master password: ")
    confirm = getpass.getpass("Confirm: ")

    if password != confirm:
        print("Error: passwords don't match.", file=sys.stderr)
        return 1
    if not password:
        print("Error: password can't be empty.", file=sys.stderr)
        return 1

    storage.create_vault(path, password)
    print(f"Created empty vault at {path}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    path = Path(args.vault)
    if not path.exists():
        print(f"Error: {path} not found.", file=sys.stderr)
        return 1

    password = getpass.getpass("Master password: ")
    try:
        plaintext, _, _ = storage.load_vault(path, password)
    except Exception:
        # Deliberately vague: don't tell attackers whether the password
        # was wrong or the file was corrupt. Same message for both.
        print("Error: wrong password or corrupted vault.", file=sys.stderr)
        return 1

    sys.stdout.write(plaintext.decode("utf-8", errors="replace"))
    if plaintext and not plaintext.endswith(b"\n"):
        print()
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    path = Path(args.vault)
    if not path.exists():
        print(f"Error: {path} not found.", file=sys.stderr)
        return 1

    password = getpass.getpass("Master password: ")
    try:
        _, key, salt = storage.load_vault(path, password)
    except Exception:
        print("Error: wrong password or corrupted vault.", file=sys.stderr)
        return 1

    print("Enter new contents. End with a line containing only '.'")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == ".":
            break
        lines.append(line)

    new_contents = ("\n".join(lines) + "\n").encode("utf-8")
    storage.save_vault(path, new_contents, key, salt)
    print("Saved.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="januslock",
        description="A small, local, encrypted file vault.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create a new empty vault")
    p_init.add_argument("vault", help="Path to the vault file (e.g. my.janus)")
    p_init.set_defaults(func=cmd_init)

    p_show = sub.add_parser("show", help="Unlock and print vault contents")
    p_show.add_argument("vault")
    p_show.set_defaults(func=cmd_show)

    p_set = sub.add_parser("set", help="Unlock and replace vault contents")
    p_set.add_argument("vault")
    p_set.set_defaults(func=cmd_set)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())