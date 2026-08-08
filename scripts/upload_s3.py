#!/usr/bin/env python3
"""Upload a list of generated icons to every configured S3-compatible bucket."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_FILE = Path("config/s3-configs.json")
REQUIRED_FIELDS = {
    "name",
    "endpoint_url",
    "region_name",
    "bucket_name",
    "access_key_id",
    "secret_access_key",
}
ADDRESSING_STYLES = {"auto", "path", "virtual"}


def load_configs(config_file: Path) -> list[dict[str, Any]]:
    raw = os.environ.get("S3_CONFIGS")
    source = "S3_CONFIGS"
    if not raw:
        source = str(config_file)
        if not config_file.is_file():
            raise SystemExit(
                f"S3_CONFIGS is not set and the config file does not exist: {config_file}"
            )
        raw = config_file.read_text()

    try:
        configs = json.loads(raw)
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid JSON in {source}: {error}") from error

    if not isinstance(configs, list) or not configs:
        raise SystemExit(f"{source} must contain a non-empty JSON array")
    for index, config in enumerate(configs):
        if not isinstance(config, dict):
            raise SystemExit(f"{source}[{index}] must be a JSON object")
        missing = REQUIRED_FIELDS - config.keys()
        if missing:
            raise SystemExit(f"{source}[{index}] is missing: {', '.join(sorted(missing))}")
        for field in REQUIRED_FIELDS:
            if not isinstance(config[field], str) or not config[field].strip():
                raise SystemExit(f"{source}[{index}].{field} must be a non-empty string")
        addressing_style = config.get("addressing_style", "auto")
        if addressing_style not in ADDRESSING_STYLES:
            allowed = ", ".join(sorted(ADDRESSING_STYLES))
            raise SystemExit(
                f"{source}[{index}].addressing_style must be one of: {allowed}"
            )
    return configs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--file-list", type=Path, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(os.environ.get("S3_CONFIGS_FILE", DEFAULT_CONFIG_FILE)),
        help="local JSON config used when S3_CONFIGS is not set",
    )
    args = parser.parse_args()

    import boto3
    from botocore.config import Config

    names = [line.strip() for line in args.file_list.read_text().splitlines() if line.strip()]
    if not names:
        print("No icons to upload")
        return

    for target in load_configs(args.config):
        client = boto3.client(
            "s3",
            endpoint_url=target["endpoint_url"],
            aws_access_key_id=target["access_key_id"],
            aws_secret_access_key=target["secret_access_key"],
            aws_session_token=target.get("session_token"),
            region_name=target["region_name"],
            config=Config(
                signature_version=target.get("signature_version", "s3v4"),
                s3={"addressing_style": target.get("addressing_style", "auto")},
            ),
        )
        for name in names:
            source = args.directory / name
            if not source.is_file():
                raise SystemExit(f"generated icon is missing: {source}")
            key = f"{args.prefix.rstrip('/')}/{name}"
            client.upload_file(
                str(source),
                target["bucket_name"],
                key,
                ExtraArgs={"ContentType": "image/svg+xml"},
            )
        print(f"Uploaded {len(names)} icons to {target['name']}")


if __name__ == "__main__":
    main()
