"""Check that ProtoLab's G1 config loads its own complete robot model."""

from dataclasses import asdict
from pathlib import Path
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from protomotions.robot_configs.g1 import G1RobotConfig
from protomotions.simulator.mujoco.simulator import MujocoSimulator
from protolab.robots.g1 import ProtoLabG1RobotConfig


class ProtoLabG1Tests(unittest.TestCase):
    def test_project_config_and_mjcf_load_without_upstream_assets(self):
        root = Path(__file__).resolve().parents[1]
        with patch.dict("os.environ", {"PROTOMOTIONS_ASSET_ROOT": str(root / "missing-upstream-assets")}):
            project = ProtoLabG1RobotConfig()
        upstream = G1RobotConfig()
        model_path = root / project.asset.asset_root / project.asset.asset_file_name
        upstream_model_path = (
            root / "external/ProtoMotions/protomotions/data/assets/mjcf/g1_holo_compat.xml"
        )

        self.assertEqual(model_path.read_bytes(), upstream_model_path.read_bytes())
        mesh_names = {
            node.attrib["file"]
            for node in ElementTree.parse(model_path).iter("mesh")
            if "file" in node.attrib
        }
        self.assertEqual(len(mesh_names), 35)
        self.assertTrue(all((model_path.parent.parent / "mesh/G1" / name).is_file() for name in mesh_names))
        loaded_model = MujocoSimulator._load_mjcf_stripped(str(model_path))
        self.assertEqual(loaded_model.nmesh, len(mesh_names))

        self.assertEqual(project.kinematic_info.dof_names, upstream.kinematic_info.dof_names)
        self.assertEqual(project.kinematic_info.body_names, upstream.kinematic_info.body_names)
        self.assertEqual(project.number_of_actions, upstream.number_of_actions)
        project_asset = asdict(project.asset)
        upstream_asset = asdict(upstream.asset)
        for key in ("asset_root", "asset_file_name"):
            project_asset.pop(key)
            upstream_asset.pop(key)
        self.assertEqual(project_asset, upstream_asset)


if __name__ == "__main__":
    unittest.main()
