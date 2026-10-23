from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    # ========= Arguments ==========
    params_file_arg = LaunchConfiguration(variable_name="params_file")
    use_sim_time_arg = LaunchConfiguration(variable_name="use_sim_time")

    # ========= Launch Descriptions =========
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare(package="nav2_bringup"),
                    "launch",
                    "navigation_launch.py",
                ],
            )
        ),
        launch_arguments=[
            ("use_sim_time", use_sim_time_arg),
            ("params_file", params_file_arg),
            # nav2_bringup's built-in autostart fires the lifecycle manager with no
            # grace period; with rmw_zenoh its change_state service calls can race
            # service discovery and abort bringup intermittently
            # (ros2/rmw_zenoh#783). We disable it and bring the nodes up ourselves,
            # after a delay, with our own lifecycle manager.
            ("autostart", "false"),
        ],
    )
    lifecycle_nodes = [
        "controller_server",
        "smoother_server",
        "planner_server",
        "route_server",
        "behavior_server",
        "velocity_smoother",
        "collision_monitor",
        "bt_navigator",
        "waypoint_follower",
        "docking_server",
    ]
    lifecycle_manager_launch = TimerAction(
        period=5.0,
        actions=[
            Node(
                package="nav2_lifecycle_manager",
                executable="lifecycle_manager",
                name="lifecycle_manager_navigation",
                output="screen",
                parameters=[
                    {"use_sim_time": use_sim_time_arg},
                    {"autostart": True},
                    {"bond_timeout": 10.0},
                    {"node_names": lifecycle_nodes},
                ],
            ),
        ],
    )
    depth_container_launch = ComposableNodeContainer(
        name="depth_processor_container",
        namespace="",
        package="rclcpp_components",
        executable="component_container",
        composable_node_descriptions=[
            ComposableNode(
                package="depth_image_proc",
                plugin="depth_image_proc::PointCloudXyzNode",
                name="point_cloud_xyz_node",
                remappings=[
                    ("image_rect", "/mini_piper/gripper_camera/left/depth"),
                    ("camera_info", "/mini_piper/gripper_camera/left/camera_info"),
                    ("points", "/mini_piper/gripper_camera/left/depth/points"),
                ],
            )
        ],
        output="screen",
    )
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "params_file",
                default_value=PathJoinSubstitution(
                    [
                        FindPackageShare("scout_piper_navigation"),
                        "config",
                        "nav2_params.yaml",
                    ]
                ),
            ),
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            nav2_launch,
            lifecycle_manager_launch,
            depth_container_launch,
        ]
    )
