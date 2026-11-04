#!/usr/bin/env python3
"""Create a consistent local snapshot of a NEXUS SQLite database."""
import argparse
import sqlite3
from pathlib import Path


def backup_database(source, destination):
    src = Path(source).expanduser().resolve()
    dst = Path(destination).expanduser().resolve()
    if src == dst:
        raise ValueError("backup destination must differ from the active database")
    if src.exists() and dst.exists() and src.samefile(dst):
        raise ValueError("backup destination aliases the active database")
    if not src.is_file():
        raise FileNotFoundError(f"database not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(src) as live, sqlite3.connect(dst) as snapshot:
        live.backup(snapshot)
    return dst


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="active NEXUS SQLite database")
    parser.add_argument("destination", help="snapshot path (created or replaced)")
    args = parser.parse_args()
    print(backup_database(args.source, args.destination))


if __name__ == "__main__":
    main()
