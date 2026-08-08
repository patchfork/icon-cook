import tempfile
import unittest
from pathlib import Path

from scripts.sync_icons import (
    find_changed_outputs,
    material_key,
    select_fluent,
    select_material,
    validate_svg,
)


class SyncIconsTest(unittest.TestCase):
    def test_fluent_prefers_24_over_larger_sizes(self):
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            svg = root / "assets" / "Access Time" / "SVG"
            svg.mkdir(parents=True)
            for name in (
                "ic_fluent_access_time_20_filled.svg",
                "ic_fluent_access_time_24_filled.svg",
                "ic_fluent_access_time_48_filled.svg",
                "ic_fluent_access_time_20_regular.svg",
            ):
                (svg / name).write_text("<svg/>")
            selected = select_fluent(root, None)
            self.assertEqual(selected["access_time_filled.svg"].name,
                             "ic_fluent_access_time_24_filled.svg")
            self.assertIn("access_time_regular.svg", selected)

    def test_fluent_falls_back_to_28_then_nearest_size(self):
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            svg = root / "assets" / "Access Time" / "SVG"
            svg.mkdir(parents=True)
            for size in (20, 28, 48):
                (svg / f"ic_fluent_access_time_{size}_filled.svg").write_text("<svg/>")
            selected = select_fluent(root, None)
            self.assertEqual(selected["access_time_filled.svg"].name,
                             "ic_fluent_access_time_28_filled.svg")

    def test_fluent_changed_file_regenerates_all_sizes_for_logical_icon(self):
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            svg = root / "assets" / "Access Time" / "SVG"
            svg.mkdir(parents=True)
            for size in (20, 24):
                (svg / f"ic_fluent_access_time_{size}_filled.svg").write_text("<svg/>")
            changed = ["assets/Access Time/SVG/ic_fluent_access_time_20_filled.svg"]
            selected = select_fluent(root, changed)
            self.assertEqual(selected["access_time_filled.svg"].name,
                             "ic_fluent_access_time_24_filled.svg")

    def test_material_uses_icon_name(self):
        path = "symbols/web/3d_rotation/materialsymbolsrounded/3d_rotation_24px.svg"
        self.assertEqual(material_key(path), "3d_rotation")
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            icon = root / path
            icon.parent.mkdir(parents=True)
            icon.write_text("<svg/>")
            self.assertEqual(select_material(root, None), {"3d_rotation.svg": icon})

    def test_material_ignores_non_default_axis_variants(self):
        path = "symbols/web/home/materialsymbolsrounded/home_fill1_24px.svg"
        self.assertIsNone(material_key(path))

    def test_svg_validation_requires_viewbox_without_dimensions(self):
        with tempfile.TemporaryDirectory() as root_name:
            icon = Path(root_name) / "icon.svg"
            icon.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"/>')
            validate_svg(icon)
            icon.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="24" viewBox="0 0 24 24"/>')
            with self.assertRaises(ValueError):
                validate_svg(icon)

    def test_only_new_or_content_changed_outputs_are_uploaded(self):
        with tempfile.TemporaryDirectory() as root_name:
            output = Path(root_name)
            (output / "unchanged.svg").write_bytes(b"same")
            (output / "modified.svg").write_bytes(b"new")
            (output / "added.svg").write_bytes(b"new")
            previous = {
                "unchanged.svg": b"same",
                "modified.svg": b"old",
                "added.svg": None,
            }
            self.assertEqual(
                find_changed_outputs(previous, output),
                ["added.svg", "modified.svg"],
            )


if __name__ == "__main__":
    unittest.main()
