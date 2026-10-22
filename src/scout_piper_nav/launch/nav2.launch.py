from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    params_file = LaunchConfiguration("params_file")
    use_sim_time = LaunchConfiguration("use_sim_time")

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("nav2_bringup"), "launch", "navigation_launch.py"])
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "params_file": params_file,
            "namespace": "mini_piper",
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("params_file", default_value=PathJoinSubstitution([FindPackageShare("scout_piper_nav"), "config", "nav2_params.yaml"])),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        nav2_launch,
    ])
