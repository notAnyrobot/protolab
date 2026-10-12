"""Bounded standalone IsaacLab/PhysX free-fall and reset check, no remote assets."""
from isaaclab.app import AppLauncher
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--visualizer', choices=['none', 'kit'], default='none')
args = parser.parse_args()
app = AppLauncher(headless=args.visualizer == 'none', device='cuda:0', visualizer=[args.visualizer]).app
try:
    import torch
    import isaaclab.sim as sim_utils
    from isaaclab.assets import RigidObject, RigidObjectCfg
    from isaaclab_physx.physics import PhysxCfg
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(device='cuda:0', dt=0.01, physics=PhysxCfg()))
    cube = RigidObject(RigidObjectCfg(
        prim_path='/World/TestCube',
        spawn=sim_utils.CuboidCfg(size=(0.1, 0.1, 0.1),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg()),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(0.0, 0.0, 1.0)),
    ))
    sim.reset()
    initial = cube.data.root_pos_w.torch.clone()
    print('VALIDATION_INITIAL', initial.tolist(), 'device', initial.device, flush=True)
    assert initial.is_cuda
    for step in range(30):
        cube.write_data_to_sim()
        sim.step()
        cube.update(0.01)
    final = cube.data.root_pos_w.torch.clone()
    assert torch.isfinite(final).all()
    assert 0.2 < float(initial[0, 2]-final[0, 2]) < 0.8, (initial, final)
    print('VALIDATION_FALL_PASS', final.tolist(), flush=True)
    cube.write_root_pose_to_sim_index(root_pose=cube.data.default_root_pose.torch.clone())
    cube.write_root_velocity_to_sim_index(root_velocity=cube.data.default_root_vel.torch.clone())
    cube.reset()
    cube.write_data_to_sim()
    sim.step()
    cube.update(0.01)
    reset = cube.data.root_pos_w.torch.clone()
    assert torch.isfinite(reset).all()
    assert float(reset[0,2]) > 0.95, reset
    print('VALIDATION_RESET_PASS', reset.tolist(), flush=True)
finally:
    app.close()
