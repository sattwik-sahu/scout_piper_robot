# biolab-isaacsim_ws

ROS 2 workspace for the Scout Mini + telescoping lift + Piper arm mobile manipulator, with Isaac Sim bringup.

## Quick start

```bash
pixi install
pixi run build
source install/setup.bash
ros2 launch scout_mini_piper_description scout_mini_piper.launch.py
```

## Packages

- `scout_mini_piper_description` — URDF, meshes, and launch files
- `scout_mini_piper_moveit` — MoveIt configuration and launch files
- `scout_mini_piper_navigation` — Nav2 configuration and launch files

Vendored packages (`scout_description`, `isaacsim_bringup`) keep their upstream
names.

## Documentation

- `docs/usage.md` — build, configuration, MoveIt planning
- `docs/bringup.md` — start Nav2 and MoveIt together
- `docs/navigation.md` — Nav2 stack
- `docs/isaacsim_urdf_synth_patch.md` — Isaac Sim URDF synthesis patch

## Status

Done:

- [x] Scout Mini + lift + Piper description (xacro and central `robot.yaml`)
- [x] Isaac Sim asset and `ros2_control` manager
- [x] Odometry and TF (`world -> odom -> base_link`)
- [x] Nav2 configuration (costmaps, planner, controller, collision monitor)
- [x] MoveIt configuration (SRDF, kinematics, joint limits, controllers)
- [x] MoveIt plan and execute in simulation (arm and gripper)
- [x] Controller spawning and Zenoh/FastRTPS typesupport preload for Isaac
- [x] Isaac URDF synthesis patch
- [x] Documentation for simulation and real robot

Next:

- [ ] Implement the `ros2_control` hardware interface for the real robot
- [ ] Configure 3D perception with MoveIt
- [ ] Add intelligent manipulation
