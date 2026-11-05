# Usage

> ⚠️ **This workspace is under construction. Expect breaking changes.**

## Build

```bash
pixi run build   # description, MoveIt, Nav2 (symlink install)
pixi run test    # tests for those packages
```

Python is formatted and linted with ruff. The ament flake8 test is disabled.

`pixi run build-all` builds every package in the workspace, including the
simulation and legacy packages.

## Documentation

- `docs/bringup.md` — start Nav2 and MoveIt together
- `docs/navigation.md` — Nav2 stack
- `docs/isaacsim_urdf_synth_patch.md` — Isaac Sim URDF synthesis patch

## Launch

```bash
source install/setup.bash
ros2 launch scout_mini_piper_description scout_mini_piper.launch.py
# variants:
ros2 launch scout_mini_piper_description scout_mini_piper_small.launch.py
ros2 launch scout_mini_piper_description description.launch.py
```

## Planning arm movements with MoveIt

`scout_mini_piper_moveit` contains planning configuration and launch files only.
The robot bringup provides `robot_state_publisher`, the `controller_manager`, and
the controllers. MoveIt consumes their topics. To run Nav2 and MoveIt together,
see `docs/bringup.md`.

Planning groups: `manipulator` (lift and `joint1`–`joint6`) and `gripper`.

### Simulation (Isaac Sim)

1. Start Isaac Sim and press Play. The `ros2_control_manager` graph creates the
   controller manager.
2. Start the robot state publisher on simulation time:

   ```bash
   ros2 launch scout_mini_piper_description scout_mini_piper.launch.py \
     use_sim_time:=true gui:=false joint_state_publisher:=false
   ```

3. Load the controllers:

   ```bash
   ros2 launch scout_mini_piper_moveit spawn_controllers.launch.py
   ```

4. Start `move_group`:

   ```bash
   ros2 launch scout_mini_piper_moveit move_group.launch.py use_sim_time:=true
   ```

5. Start RViz:

   ```bash
   ros2 launch scout_mini_piper_moveit moveit_rviz.launch.py use_sim_time:=true
   ```

6. In RViz, open the MotionPlanning display, select the `manipulator` group. Set
   the goal with the interactive marker in the 3D view or with Goal State in the
   Planning tab, then use Plan and Execute.

<details>
<summary>Controller loading after Play</summary>

Isaac recreates the controller manager on every Play. Run step 3 after each
Stop/Play cycle. Before step 3, `ros2 control list_controllers` returns an empty
list; that is expected. The launch starts `joint_state_broadcaster`,
`manipulator_controller`, and `gripper_controller`. The spawner processes exit
after activation, so the command returns when the controllers are active.
</details>

<details>
<summary>Simulation time</summary>

Isaac publishes `/clock` and owns `world -> odom -> base_link`. Every node that
uses TF or message timestamps (`robot_state_publisher`, `move_group`, RViz) must
run with `use_sim_time:=true`. Do not start `static_virtual_joint_tfs`; it would
publish a second transform to `base_link`.
</details>

### Real robot

1. Start the robot bringup. It must provide:

   - `robot_state_publisher` with the same `scout_mini_piper` model,
   - `controller_manager` with the real hardware `SystemInterface`,
   - `joint_state_broadcaster` and the controllers from `ros2_controllers.yaml`,
   - TF with `base_link` in the tree, from wheel odometry and localization.

2. If the bringup does not spawn the MoveIt controllers:

   ```bash
   ros2 launch scout_mini_piper_moveit spawn_controllers.launch.py
   ```

3. Start `move_group`:

   ```bash
   ros2 launch scout_mini_piper_moveit move_group.launch.py
   ```

4. Start RViz:

   ```bash
   ros2 launch scout_mini_piper_moveit moveit_rviz.launch.py
   ```

5. In RViz, open the MotionPlanning display, select the `manipulator` group. Set
   the goal with the interactive marker in the 3D view or with Goal State in the
   Planning tab, then use Plan and Execute.

<details>
<summary>What the MoveIt launch files start</summary>

`move_group.launch.py` starts only the `move_group` node. It does not start
`robot_state_publisher`, `joint_state_publisher`, static TF, or a controller
manager. `moveit_rviz.launch.py` starts only RViz with the MoveIt MotionPlanning
display. The planning model is identical for the real and simulated robots.
</details>

<details>
<summary>Real hardware interface</summary>

The repository does not yet contain the `ros2_control` `SystemInterface` for the
lift, arm, gripper, and wheels. Implement it in a hardware package and load it
from the bringup. No MoveIt configuration changes are required when it is added.
</details>

### End-effector goal from the command line

RViz is the normal way to plan. The same goal can be sent to `/move_action`.
Positions are in `base_link` (`+x` forward, `+y` left).

<details>
<summary>Send and execute a pose goal</summary>

```bash
ros2 action send_goal /move_action moveit_msgs/action/MoveGroup '{
  request: {
    group_name: manipulator,
    num_planning_attempts: 10,
    allowed_planning_time: 10.0,
    max_velocity_scaling_factor: 0.6,
    max_acceleration_scaling_factor: 0.5,
    pipeline_id: ompl,
    planner_id: RRTConnect,
    start_state: {is_diff: true},
    goal_constraints: [{
      position_constraints: [{
        header: {frame_id: base_link},
        link_name: gripper_base_link,
        target_point_offset: {x: 0.0, y: 0.0, z: 0.0},
        constraint_region: {
          primitives: [{type: 1, dimensions: [0.01, 0.01, 0.01]}],
          primitive_poses: [{position: {x: 0.506, y: 0.2, z: 0.449}, orientation: {w: 1.0}}]
        },
        weight: 1.0
      }],
      orientation_constraints: [{
        header: {frame_id: base_link},
        link_name: gripper_base_link,
        orientation: {x: 0.0, y: -0.042, z: 0.0, w: 0.999},
        absolute_x_axis_tolerance: 0.2,
        absolute_y_axis_tolerance: 0.2,
        absolute_z_axis_tolerance: 0.3,
        weight: 1.0
      }]
    }]
  },
  planning_options: {plan_only: false, look_around: false, replan: true, replan_attempts: 3}
}'
```

- `constraint_region` is a 1 cm box around the target. The end effector must
  finish inside it.
- `orientation` is the target quaternion. The tolerances are in radians.
- `plan_only: false` plans and executes. Set it to `true` to inspect the plan.
- `max_velocity_scaling_factor` and `max_acceleration_scaling_factor` are
  fractions of the limits in `joint_limits.yaml`.
</details>

<details>
<summary>Send a joint-space goal (home)</summary>

The SRDF `home` state is `lift_joint` and `joint1`–`joint6` at zero. The
MoveGroup action takes joint constraints, not the state name.

```bash
ros2 action send_goal /move_action moveit_msgs/action/MoveGroup '{
  request: {
    group_name: manipulator,
    num_planning_attempts: 10,
    allowed_planning_time: 10.0,
    max_velocity_scaling_factor: 0.6,
    max_acceleration_scaling_factor: 0.5,
    pipeline_id: ompl,
    planner_id: RRTConnect,
    start_state: {is_diff: true},
    goal_constraints: [{
      joint_constraints: [
        {joint_name: lift_joint, position: 0.0, tolerance_above: 0.01, tolerance_below: 0.01, weight: 1.0},
        {joint_name: joint1, position: 0.0, tolerance_above: 0.01, tolerance_below: 0.01, weight: 1.0},
        {joint_name: joint2, position: 0.0, tolerance_above: 0.01, tolerance_below: 0.01, weight: 1.0},
        {joint_name: joint3, position: 0.0, tolerance_above: 0.01, tolerance_below: 0.01, weight: 1.0},
        {joint_name: joint4, position: 0.0, tolerance_above: 0.01, tolerance_below: 0.01, weight: 1.0},
        {joint_name: joint5, position: 0.0, tolerance_above: 0.01, tolerance_below: 0.01, weight: 1.0},
        {joint_name: joint6, position: 0.0, tolerance_above: 0.01, tolerance_below: 0.01, weight: 1.0}
      ]
    }]
  },
  planning_options: {plan_only: false, look_around: false, replan: true, replan_attempts: 3}
}'
```
</details>

<details>
<summary>Open and close the gripper</summary>

The gripper uses `gripper_controller` directly. Open is `0.0, 0.0`; closed is
`-0.05, +0.05`.

```bash
ros2 action send_goal /gripper_controller/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory "{
    trajectory: {
      joint_names: [gripper_left_joint, gripper_right_joint],
      points: [{positions: [-0.05, 0.05], time_from_start: {sec: 0, nanosec: 500000000}}]
    }
  }"
```

Replace the positions with `[0.0, 0.0]` to open.
</details>

### Checks before planning

```bash
ros2 control list_controllers
ros2 action list | grep follow_joint_trajectory
ros2 run tf2_ros tf2_echo base_link gripper_base_link
```

All three controllers must be `active`, both `follow_joint_trajectory` action
servers must exist, and the transform must resolve with current timestamps.

### Simulation-only setup

- `scripts/isaac_ros_env.sh` preloads the FastRTPS typesupport libraries that
  Zenoh and Isaac's in-process controller manager must share.
- The Isaac `urdf_synth.py` patch and its verification are documented in
  `docs/isaacsim_urdf_synth_patch.md`.

## Configuration

All robot tunables live in `src/scout_mini_piper_description/config/robot.yaml` (central config). Edit and relaunch — no rebuild needed (symlink install).

- `lift.*` — actuator mount, heights, platform offset.
- `left_camera.*` — `gripper_left_camera_link` transform (xyz/rpy) relative to `gripper_base_link`.

Override the file at launch:

```bash
ros2 launch scout_mini_piper_description scout_mini_piper.launch.py robot_config_file:=/path/to/robot.yaml
```

## Notes

- Scout Mini uses indoor `wheel.dae` wheels (not rugged type1/type2).
- Meshes resolve via `scout_description` (now an ament package).