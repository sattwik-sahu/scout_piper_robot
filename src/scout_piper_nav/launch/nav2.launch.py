from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    params_file = LaunchConfiguration("params_file")
    use_sim_time = LaunchConfiguration("use_sim_time")

    tf_relay = ExecuteProcess(
        cmd=["python3", PathJoinSubstitution([FindPackageShare("scout_piper_nav"), "scripts", "tf_relay.py"])],
        output="screen",
    )
    cmd_relay = ExecuteProcess(
        cmd=["python3", PathJoinSubstitution([FindPackageShare("scout_piper_nav"), "scripts", "cmd_vel_relay.py"])],
        output="screen",
    )

    return LaunchDescription([
        DeclareLaunchArgument("params_file", default_value=PathJoinSubstitution([FindPackageShare("scout_piper_nav"), "config", "nav2_params.yaml"])),
        DeclareLaunchArgument("use_sim_time", default_value="true"),

        tf_relay,
        cmd_relay,

        Node(package="nav2_controller", executable="controller_server", name="controller_server", output="screen", parameters=[params_file, {"use_sim_time": use_sim_time}]),
        Node(package="nav2_planner", executable="planner_server", name="planner_server", output="screen", parameters=[params_file, {"use_sim_time": use_sim_time}]),
        Node(package="nav2_behaviors", executable="behavior_server", name="behavior_server", output="screen", parameters=[params_file, {"use_sim_time": use_sim_time}]),
        Node(package="nav2_bt_navigator", executable="bt_navigator", name="bt_navigator", output="screen", parameters=[params_file, {"use_sim_time": use_sim_time}]),
        Node(package="nav2_velocity_smoother", executable="velocity_smoother", name="velocity_smoother", output="screen", parameters=[params_file, {"use_sim_time": use_sim_time}]),

        Node(package="nav2_lifecycle_manager", executable="lifecycle_manager", name="lifecycle_manager_navigation", output="screen",
             parameters=[{"use_sim_time": use_sim_time, "autostart": True, "node_names": ["controller_server","planner_server","behavior_server","bt_navigator","velocity_smoother"]}]),
    ])
