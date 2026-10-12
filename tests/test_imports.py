"""Import and ownership checks; no simulator is launched."""
import importlib
from pathlib import Path
import unittest


class ImportTests(unittest.TestCase):
    def test_upstream_and_downstream_are_separate(self):
        upstream = importlib.import_module("protomotions")
        downstream = importlib.import_module("protolab")
        upstream_path = Path(upstream.__file__).resolve()
        downstream_path = Path(downstream.__file__).resolve()
        source = Path(__file__).resolve().parents[1] / "src"
        self.assertNotEqual(upstream_path.parent, downstream_path.parent)
        self.assertTrue(downstream_path.is_relative_to(source / "protolab"))
        self.assertFalse(upstream_path.is_relative_to(source))


if __name__ == "__main__":
    unittest.main()
