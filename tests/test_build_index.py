import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_index import update_index


class BuildIndexTest(unittest.TestCase):
    def test_combines_fluent_metadata_and_flat_material_names(self):
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            index = root / "index.json"
            fluent_output = root / "icons/fli"
            material_output = root / "icons/msr"
            fluent_source = root / "upstream/fluent"
            metadata_dir = fluent_source / "assets/Access Time"
            svg_source = metadata_dir / "SVG"
            fluent_output.mkdir(parents=True)
            material_output.mkdir(parents=True)
            svg_source.mkdir(parents=True)

            (fluent_output / "access_time_filled.svg").write_text("<svg/>")
            (material_output / "align_flex_center.svg").write_text("<svg/>")
            (svg_source / "ic_fluent_access_time_24_filled.svg").write_text("<svg/>")
            (metadata_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "name": "Access Time",
                        "keyword": "fluent-icon",
                        "description": "Shows a clock",
                        "metaphor": ["number", "circle"],
                    }
                )
            )

            update_index(root, index, "fli", fluent_source)
            update_index(root, index, "msr")
            icons = json.loads(index.read_text())["icons"]

            fluent = icons[0]
            self.assertEqual(fluent["filename"], "access_time_filled.svg")
            self.assertEqual(fluent["path"], "icons/fli/access_time_filled.svg")
            self.assertEqual(fluent["filetype"], "svg")
            self.assertIn("clock", fluent["terms"])
            self.assertIn("circle", fluent["terms"])

            material = icons[1]
            self.assertEqual(material["filename"], "align_flex_center.svg")
            self.assertEqual(material["terms"], ["align", "center", "flex"])


if __name__ == "__main__":
    unittest.main()
