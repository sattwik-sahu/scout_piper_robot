"""Start move_group against whatever robot bringup is already running.

Works unchanged on the real robot and in simulation:
  * use_sim_time false (default): real robot clock
  * use_sim_time true: Isaac/Nav2 publishes /clock and owns world -> odom -> base_link

It deliberately does not start robot_state_publisher, joint_state_publisher,
static_virtual_joint_tfs or a controller manager. Those belong to the robot
bringup, so MoveIt only consumes their topics.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")

    moveit_config = MoveItConfigsBuilder(
        "scout_mini_piper", package_name="scout_mini_piper_moveit"
    ).to_moveit_configs()

    params = moveit_config.to_dict()
    params.update(
        {
            "use_sim_time": use_sim_time,
            "publish_robot_description_semantic": True,
            "allow_trajectory_execution": True,
            "publish_planning_scene": True,
            "publish_geometry_updates": True,
            "publish_state_updates": True,
            "publish_transforms_updates": True,
            "monitor_dynamics": False,
        }
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="Use /clock from a simulator",
            ),
            Node(
                package="moveit_ros_move_group",
                executable="move_group",
                output="screen",
                parameters=[params],
            ),
        ]
    )
