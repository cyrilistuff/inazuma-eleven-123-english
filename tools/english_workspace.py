#!/usr/bin/env python3
"""Prepare and inspect the separate English dialogue workspace.

This never copies the upstream Spanish translation into English fields and
never builds a patch. The existing Spanish corpus supplies only Japanese keys.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("event_id", "japones", "en_final", "estado")
PLACEHOLDER = re.compile(r"%(?:s|d)")


def read_csv(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not set(required).issubset(reader.fieldnames):
            raise ValueError(f"{path}: expected columns {', '.join(required)}")
        return list(reader)


def key(row: dict[str, str]) -> tuple[str, str]:
    return row["event_id"], row["japones"]


def workspace(game: str) -> tuple[Path, Path]:
    return (
        ROOT / "translation" / game / "dialogo.csv",
        ROOT / "translation" / "en" / game / "dialogo.csv",
    )


def initialize(game: str) -> None:
    source, target = workspace(game)
    source_rows = read_csv(source, ("event_id", "japones"))
    existing = read_csv(target, FIELDS) if target.exists() else []
    by_key: dict[tuple[str, str], dict[str, str]] = {}
    for row in existing:
        if key(row) in by_key:
            raise ValueError(f"{target}: duplicate key {key(row)!r}")
        by_key[key(row)] = {field: row[field] for field in FIELDS}

    rows = []
    seen = set()
    for source_row in source_rows:
        identity = key(source_row)
        if identity in seen:
            continue
        seen.add(identity)
        rows.append(by_key.pop(identity, {
            "event_id": identity[0], "japones": identity[1],
            "en_final": "", "estado": "pending",
        }))
    if by_key:
        raise ValueError(f"{target}: {len(by_key)} English keys absent from source; review before merging")

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(target)
    print(f"{game}: {len(rows)} unique Japanese keys; {len(rows) - len(existing)} new -> {target}")


def status(game: str) -> int:
    _, target = workspace(game)
    rows = read_csv(target, FIELDS)
    states = Counter(row["estado"] for row in rows)
    translated = sum(bool(row["en_final"].strip()) for row in rows)
    errors = []
    seen: dict[tuple[str, str], str] = {}
    for number, row in enumerate(rows, start=2):
        english = row["en_final"].strip()
        identity = key(row)
        if identity in seen:
            errors.append(f"row {number}: duplicate key {identity!r}")
            if english != seen[identity]:
                errors.append(f"row {number}: divergent English translation for duplicate key")
        else:
            seen[identity] = english
        if english and row["estado"] not in {"review", "approved"}:
            errors.append(f"row {number}: translated text needs review or approved status")
        if not english and row["estado"] != "pending":
            errors.append(f"row {number}: empty English text must be pending")
        if english and Counter(PLACEHOLDER.findall(row["japones"])) != Counter(PLACEHOLDER.findall(english)):
            errors.append(f"row {number}: %s/%d placeholders differ from Japanese")
    print(f"{game}: {translated}/{len(rows)} unique keys translated; states {dict(states)}")
    for error in errors[:20]:
        print(error, file=sys.stderr)
    if len(errors) > 20:
        print(f"...and {len(errors) - 20} more errors", file=sys.stderr)
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "status"))
    parser.add_argument("--game", choices=("ie1", "ie2"), default="ie1")
    args = parser.parse_args()
    try:
        if args.command == "init":
            initialize(args.game)
        else:
            return status(args.game)
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
