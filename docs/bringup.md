# Bringup: Nav2 and MoveIt

This is the full stack for the mobile manipulator: Nav2 for the base and MoveIt
for the arm and gripper. Start the robot bringup first; it owns
`robot_state_publisher`, the controller manager, and TF.

## Simulation (Isaac Sim)

1. Start Isaac Sim and press Play.

2. Start the robot state publisher on simulation time:

   ```bash
   ros2 launch scout_mini_piper_description scout_mini_piper.launch.py \
     use_sim_time:=true gui:=false joint_state_publisher:=false
   ```

3. Load the MoveIt controllers:

   ```bash
   ros2 launch scout_mini_piper_moveit spawn_controllers.launch.py
   ```

4. Start Nav2:

   ```bash
   ros2 launch scout_mini_piper_navigation navigation.launch.py use_sim_time:=true
   ```

5. Start MoveIt:

   ```bash
   ros2 launch scout_mini_piper_moveit move_group.launch.py use_sim_time:=true
   ```

6. Optional: start RViz.

   ```bash
   ros2 launch scout_mini_piper_moveit moveit_rviz.launch.py use_sim_time:=true
   ```

## Real robot

1. Start the robot bringup. It must provide:

   - `robot_state_publisher` with the `scout_mini_piper` model,
   - `controller_manager` with the real hardware `SystemInterface`,
   - `joint_state_broadcaster`, `manipulator_controller`, `gripper_controller`,
   - `/odom` and a TF tree containing `base_link`,
   - the gripper depth camera topics, or a costmap observation source.

2. If the bringup does not spawn the MoveIt controllers:

   ```bash
   ros2 launch scout_mini_piper_moveit spawn_controllers.launch.py
   ```

3. Start Nav2:

   ```bash
   ros2 launch scout_mini_piper_navigation navigation.launch.py use_sim_time:=false
   ```

4. Start MoveIt:

   ```bash
   ros2 launch scout_mini_piper_moveit move_group.launch.py
   ```

5. Optional: start RViz.

   ```bash
   ros2 launch scout_mini_piper_moveit moveit_rviz.launch.py
   ```

## Interface for downstream actions

| Action or service | Type | Use |
|---|---|---|
| `/navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | navigate the base to a pose in `world` |
| `/move_action` | `moveit_msgs/action/MoveGroup` | plan and execute arm or gripper goals |
| `/compute_ik` | `moveit_msgs/srv/GetPositionIK` | inverse kinematics for a pose |
| `/compute_fk` | `moveit_msgs/srv/GetPositionFK` | forward kinematics for a joint state |
| `/manipulator_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | direct arm trajectory, bypasses planning |
| `/gripper_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | direct gripper trajectory |

MoveIt planning groups: `manipulator` (lift and `joint1`–`joint6`) and
`gripper`. The end-effector link is `gripper_base_link`.

## Verify before sending goals

```bash
ros2 control list_controllers
ros2 action list | grep -E 'navigate_to_pose|follow_joint_trajectory|move_action'
ros2 lifecycle get /bt_navigator
ros2 run tf2_ros tf2_echo world base_link
ros2 topic hz /odom
ros2 topic hz /joint_states
```

Expected:

- all three controllers `active`,
- `/navigate_to_pose`, `/move_action`, and both `follow_joint_trajectory`
  actions present,
- `/bt_navigator` `active`,
- `world -> base_link` resolves with current timestamps,
- `/odom` and `/joint_states` update.

## Restart behavior

- Isaac Sim recreates the controller manager on every Play. Run step 3 again after
  each Stop/Play cycle.
- `move_group` and Nav2 can stay running across a Play, but they log a clock jump
  and clear the TF buffer. Restart them if planning or navigation fails after a
  restart.
- All nodes must agree on `use_sim_time`. Do not mix simulation time and wall
  clock.
