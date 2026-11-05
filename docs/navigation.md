# Navigation (Nav2)

`scout_mini_piper_navigation` starts the Nav2 servers and a depth-to-point-cloud
node. It does not start `robot_state_publisher`, the controller manager, or
localization.

## Prerequisites

Simulation:

- Isaac Sim is playing. It publishes `/clock`, `/odom`, and
  `world -> odom -> base_link`.
- `robot_state_publisher` runs with `use_sim_time:=true`.
- The gripper camera publishes `/mini_piper/gripper_camera/left/depth` and
  `/mini_piper/gripper_camera/left/camera_info`.

Real robot:

- A base driver publishes `/odom` and a TF tree containing `base_link`.
- The depth camera publishes the topics above, or the costmap observation source
  in `nav2_params.yaml` is changed.

## Start

```bash
# simulation
ros2 launch scout_mini_piper_navigation navigation.launch.py use_sim_time:=true

# real robot
ros2 launch scout_mini_piper_navigation navigation.launch.py use_sim_time:=false
```

<details>
<summary>What the launch starts</summary>

- `nav2_bringup/navigation_launch.py` with `autostart:=true`. This starts
  `controller_server`, `smoother_server`, `planner_server`, `route_server`,
  `behavior_server`, `bt_navigator`, `waypoint_follower`,
  `velocity_smoother`, and `collision_monitor`.
- `depth_image_proc::PointCloudXyzNode`, which converts the gripper depth image
  to `/mini_piper/gripper_camera/left/depth/points`.

The costmaps are rolling windows in `world`, with a voxel layer fed by that point
cloud and an inflation layer. No map server or AMCL is used.

`collision_monitor` takes `/cmd_vel_smoothed` and publishes
`/mini_piper/cmd_vel`, which the base controller consumes.
</details>

## Send a goal

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{
  pose: {
    header: {frame_id: world},
    pose: {
      position: {x: 1.0, y: 0.0, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
    }
  }
}"
```

Replace the position and orientation with the target pose in `world`.

## Verify

```bash
ros2 action list | grep navigate_to_pose
ros2 lifecycle get /bt_navigator
ros2 topic hz /odom
ros2 topic echo /cmd_vel_smoothed --once
```

`/bt_navigator` must be `active`. The goal action returns a status; a failed
goal without a path usually means the costmap has no valid start or goal cell.

## Map-based navigation

The provided configuration is map-free: both costmaps are rolling windows and
use the depth point cloud. For navigation on a saved map, start
`nav2_bringup/bringup_launch.py` with a map and a localization source (AMCL or
`slam_toolbox`) instead of `navigation.launch.py`, and add the static layer to
the global costmap.
