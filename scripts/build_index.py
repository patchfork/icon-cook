#!/usr/bin/env python3
"""Build the affected collection's portion of the root icon search index."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

TOKEN_RE = re.compile(r"[a-z0-9]+")
FLUENT_RE = re.compile(r"^ic_fluent_(?P<name>.+)_(?P<size>\d+)_(?P<style>[^_]+)\.svg$")
UNHELPFUL_TERMS = {"fluent", "icon"}


def terms_from(values: Iterable[Any]) -> list[str]:
    terms: set[str] = set()

    def add(value: Any) -> None:
        if isinstance(value, str):
            terms.update(TOKEN_RE.findall(value.lower()))
        elif isinstance(value, list):
            for item in value:
                add(item)

    for value in values:
        add(value)
    return sorted(terms - UNHELPFUL_TERMS)


def fluent_metadata(source: Path) -> dict[str, dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for metadata_path in source.glob("assets/*/metadata.json"):
        metadata = json.loads(metadata_path.read_text())
        for svg in (metadata_path.parent / "SVG").glob("*.svg"):
            match = FLUENT_RE.match(svg.name)
            if match:
                by_name[match["name"]] = metadata
    return by_name


def build_fluent(root: Path, source: Path) -> list[dict[str, Any]]:
    metadata = fluent_metadata(source)
    entries = []
    for svg in sorted((root / "icons/fli").glob("*.svg")):
        name, style = svg.stem.rsplit("_", 1)
        details = metadata.get(name, {})
        entries.append(
            {
                "collection": "fli",
                "name": name,
                "style": style,
                "terms": terms_from(
                    [
                        name,
                        details.get("name"),
                        details.get("keyword"),
                        details.get("description"),
                        details.get("metaphor"),
                    ]
                ),
                "filetype": "svg",
                "filename": svg.name,
                "path": svg.relative_to(root).as_posix(),
            }
        )
    return entries


def build_material(root: Path) -> list[dict[str, Any]]:
    entries = []
    for svg in sorted((root / "icons/msr").glob("*.svg")):
        entries.append(
            {
                "collection": "msr",
                "name": svg.stem,
                "style": "rounded",
                "terms": terms_from([svg.stem]),
                "filetype": "svg",
                "filename": svg.name,
                "path": svg.relative_to(root).as_posix(),
            }
        )
    return entries


def update_index(
    root: Path, index_path: Path, collection: str, source: Path | None = None
) -> int:
    existing: list[dict[str, Any]] = []
    if index_path.is_file():
        document = json.loads(index_path.read_text())
        if document.get("version") != 1 or not isinstance(document.get("icons"), list):
            raise ValueError(f"unsupported index format: {index_path}")
        existing = [entry for entry in document["icons"] if entry.get("collection") != collection]

    if collection == "fli":
        if source is None:
            raise ValueError("--source is required for Fluent metadata")
        replacement = build_fluent(root, source)
    else:
        replacement = build_material(root)

    icons = sorted(existing + replacement, key=lambda entry: (entry["collection"], entry["filename"]))
    index_path.write_text(json.dumps({"version": 1, "icons": icons}, indent=2) + "\n")
    return len(replacement)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("collection", choices=("fli", "msr"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--index", type=Path, default=Path("index.json"))
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()

    count = update_index(args.root.resolve(), args.index, args.collection, args.source)
    print(f"Indexed {count} {args.collection} icons in {args.index}")


if __name__ == "__main__":
    main()
