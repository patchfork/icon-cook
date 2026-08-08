#!/usr/bin/env python3
"""Select, rename, and optimize icons from an upstream checkout."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

FLUENT_RE = re.compile(r"^ic_fluent_(?P<name>.+)_(?P<size>\d+)_(?P<style>[^_]+)\.svg$")
MATERIAL_RE = re.compile(
    r"^symbols/web/(?P<name>[^/]+)/materialsymbolsrounded/(?P<file>[^/]+)_24px\.svg$"
)


def read_changed(path: Path | None) -> list[str] | None:
    if path is None:
        return None
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def fluent_key(path: str | Path) -> tuple[str, str] | None:
    match = FLUENT_RE.match(PurePosixPath(path).name)
    return (match["name"], match["style"]) if match else None


def material_key(path: str | Path) -> str | None:
    match = MATERIAL_RE.match(PurePosixPath(path).as_posix())
    if match is None or match["file"] != match["name"]:
        return None
    return match["name"]


def select_fluent(source: Path, changed: list[str] | None) -> dict[str, Path]:
    affected = None if changed is None else {key for item in changed if (key := fluent_key(item))}
    selected: dict[tuple[str, str], tuple[int, Path]] = {}
    for candidate in source.glob("assets/*/SVG/*.svg"):
        match = FLUENT_RE.match(candidate.name)
        if not match:
            continue
        key = (match["name"], match["style"])
        if affected is not None and key not in affected:
            continue
        size = int(match["size"])
        if key not in selected or size > selected[key][0]:
            selected[key] = (size, candidate)
    return {f"{name}_{style}.svg": value[1] for (name, style), value in selected.items()}


def select_material(source: Path, changed: list[str] | None) -> dict[str, Path]:
    affected = None if changed is None else {key for item in changed if (key := material_key(item))}
    selected: dict[str, Path] = {}
    for candidate in source.glob("symbols/web/*/materialsymbolsrounded/*_24px.svg"):
        relative = candidate.relative_to(source).as_posix()
        key = material_key(relative)
        if key is None or (affected is not None and key not in affected):
            continue
        output_name = f"{key}.svg"
        if output_name in selected:
            raise ValueError(f"output collision for {output_name}")
        selected[output_name] = candidate
    return selected


def validate_svg(path: Path) -> None:
    root = ET.parse(path).getroot()
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError(f"not an SVG document: {path}")
    if "width" in root.attrib or "height" in root.attrib:
        raise ValueError(f"SVGO left dimensions on {path}")
    if "viewBox" not in root.attrib:
        raise ValueError(f"SVGO removed viewBox from {path}")


def optimize(selected: dict[str, Path], output: Path, svgo_config: Path) -> list[str]:
    output.mkdir(parents=True, exist_ok=True)
    if not selected:
        return []
    with tempfile.TemporaryDirectory(prefix="icon-cook-") as temp_name:
        temporary = Path(temp_name)
        for name, source in selected.items():
            shutil.copyfile(source, temporary / name)
        subprocess.run(
            ["npx", "--no-install", "svgo", "--config", str(svgo_config),
             "--folder", str(temporary), "--output", str(output)],
            check=True,
        )
    for name in selected:
        validate_svg(output / name)
    return sorted(selected)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("collection", choices=("fluent", "material-rounded"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--changed-file", type=Path)
    parser.add_argument("--output-list", type=Path, required=True)
    parser.add_argument("--svgo-config", type=Path, default=Path("svgo.config.mjs"))
    args = parser.parse_args()

    changed = read_changed(args.changed_file)
    selected = (
        select_fluent(args.source, changed)
        if args.collection == "fluent"
        else select_material(args.source, changed)
    )
    names = optimize(selected, args.output, args.svgo_config.resolve())
    args.output_list.write_text("".join(f"{name}\n" for name in names))
    print(f"Processed {len(names)} {args.collection} icons")


if __name__ == "__main__":
    main()
