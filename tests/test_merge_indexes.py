import json
import tempfile
import unittest
from pathlib import Path

from scripts.merge_indexes import merge_indexes


def write_index(path, icons):
    path.write_text(json.dumps({"version": 1, "icons": icons}))


class MergeIndexesTest(unittest.TestCase):
    def test_replaces_only_collections_present_in_fragments(self):
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            index = root / "index.json"
            fragment = root / "fluent.json"
            write_index(
                index,
                [
                    {"collection": "fli", "filename": "old.svg"},
                    {"collection": "msr", "filename": "material.svg"},
                ],
            )
            write_index(fragment, [{"collection": "fli", "filename": "new.svg"}])

            merge_indexes(index, [fragment, root / "missing.json"])
            icons = json.loads(index.read_text())["icons"]

            self.assertEqual(
                [(icon["collection"], icon["filename"]) for icon in icons],
                [("fli", "new.svg"), ("msr", "material.svg")],
            )


if __name__ == "__main__":
    unittest.main()
