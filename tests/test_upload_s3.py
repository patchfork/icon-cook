import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.upload_s3 import load_configs


def valid_config(name="test"):
    return {
        "name": name,
        "endpoint_url": "https://objects.example.com",
        "region_name": "us-east-1",
        "bucket_name": "icons",
        "access_key_id": "access",
        "secret_access_key": "secret",
    }


class UploadS3ConfigTest(unittest.TestCase):
    def test_loads_gitignored_local_file(self):
        with tempfile.TemporaryDirectory() as root_name:
            path = Path(root_name) / "s3-configs.json"
            path.write_text(json.dumps([valid_config()]))
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(load_configs(path)[0]["bucket_name"], "icons")

    def test_environment_takes_precedence_over_file(self):
        with tempfile.TemporaryDirectory() as root_name:
            path = Path(root_name) / "s3-configs.json"
            path.write_text(json.dumps([valid_config("file")]))
            with patch.dict(os.environ, {"S3_CONFIGS": json.dumps([valid_config("env")])}):
                self.assertEqual(load_configs(path)[0]["name"], "env")

    def test_rejects_missing_s3_connection_field(self):
        config = valid_config()
        del config["endpoint_url"]
        with patch.dict(os.environ, {"S3_CONFIGS": json.dumps([config])}, clear=True):
            with self.assertRaises(SystemExit):
                load_configs(Path("unused.json"))

    def test_rejects_unknown_addressing_style(self):
        config = valid_config()
        config["addressing_style"] = "unknown"
        with patch.dict(os.environ, {"S3_CONFIGS": json.dumps([config])}, clear=True):
            with self.assertRaises(SystemExit):
                load_configs(Path("unused.json"))


if __name__ == "__main__":
    unittest.main()
