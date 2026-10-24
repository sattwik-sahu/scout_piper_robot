from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    params_file = LaunchConfiguration("params_file")
    use_sim_time = LaunchConfiguration("use_sim_time")

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("nav2_bringup"),
                    "launch",
                    "navigation_launch.py",
                ]
            )
        ),
        launch_arguments={
            "params_file": params_file,
            "use_sim_time": use_sim_time,
            "autostart": "true",
        }.items(),
    )

    depth_publisher = ComposableNodeContainer(
        name="depth_processor_container",
        namespace="",
        package="rclcpp_components",
        executable="component_container",
        output="screen",
        composable_node_descriptions=[
            ComposableNode(
                package="depth_image_proc",
                plugin="depth_image_proc::PointCloudXyzNode",
                name="point_cloud_xyz_node",
                remappings=[
                    (
                        "image_rect",
                        "/mini_piper/gripper_camera/left/depth",
                    ),
                    (
                        "camera_info",
                        "/mini_piper/gripper_camera/left/camera_info",
                    ),
                    (
                        "points",
                        "/mini_piper/gripper_camera/left/depth/points",
                    ),
                ],
            )
        ],
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
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
            ),
            nav2,
            depth_publisher,
        ]
    )
