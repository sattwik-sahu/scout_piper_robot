"""RViz with the MoveIt MotionPlanning display.

Start after robot_state_publisher and move_group are running. Pass
use_sim_time:=true when a simulator publishes /clock, matching the other nodes.
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

    rviz_parameters = [
        moveit_config.planning_pipelines,
        moveit_config.robot_description_kinematics,
        moveit_config.joint_limits,
        {"use_sim_time": use_sim_time},
    ]

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="Use /clock from a simulator",
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                output="log",
                arguments=["-d", str(moveit_config.package_path / "config/moveit.rviz")],
                parameters=rviz_parameters,
            ),
        ]
    )
