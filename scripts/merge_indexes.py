#!/usr/bin/env python3
"""Merge collection index fragments into the root icon index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_index(path: Path) -> list[dict[str, Any]]:
    document = json.loads(path.read_text())
    if document.get("version") != 1 or not isinstance(document.get("icons"), list):
        raise ValueError(f"unsupported index format: {path}")
    return document["icons"]


def merge_indexes(index_path: Path, fragments: list[Path]) -> int:
    icons = read_index(index_path) if index_path.is_file() else []
    for fragment in fragments:
        if not fragment.is_file():
            continue
        replacement = read_index(fragment)
        collections = {entry["collection"] for entry in replacement}
        icons = [entry for entry in icons if entry.get("collection") not in collections]
        icons.extend(replacement)

    icons.sort(key=lambda entry: (entry["collection"], entry["filename"]))
    index_path.write_text(json.dumps({"version": 1, "icons": icons}, indent=2) + "\n")
    return len(icons)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("fragments", nargs="*", type=Path)
    args = parser.parse_args()
    count = merge_indexes(args.index, args.fragments)
    print(f"Merged {count} icons into {args.index}")


if __name__ == "__main__":
    main()
