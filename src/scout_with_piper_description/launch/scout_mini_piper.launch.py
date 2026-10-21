from pathlib import Path

import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

# Individually overridable lift settings. CLI value wins; empty means "take the
# value from the YAML file" (or the xacro default if the key is absent).
LIFT_KEYS = [
    "lift_parent_link",
    "lift_xyz",
    "lift_rpy",
    "lift_home_height",
    "lift_max_height",
    "lift_platform_link",
    "lift_platform_xyz",
    "lift_mesh_dir",
    "left_camera_xyz",
    "left_camera_rpy",
]

# YAML key path -> launch arg name. Single source of truth for the mapping.
YAML_MAP = {
    "lift_parent_link": ("lift", "mount", "parent_link"),
    "lift_xyz": ("lift", "mount", "xyz"),
    "lift_rpy": ("lift", "mount", "rpy"),
    "lift_home_height": ("lift", "home_height"),
    "lift_max_height": ("lift", "max_height"),
    "lift_platform_link": ("lift", "platform", "link"),
    "lift_platform_xyz": ("lift", "platform", "xyz"),
    "lift_mesh_dir": ("lift", "mesh_dir"),
    "left_camera_xyz": ("left_camera", "xyz"),
    "left_camera_rpy": ("left_camera", "rpy"),
}


def _dig(mapping, path):
    """Fetch a nested key, returning None when any level is absent."""
    node = mapping
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def _as_xyz_string(value):
    """Lists/tuples become the space separated form xacro expects."""
    if isinstance(value, (list, tuple)):
        return " ".join(str(float(v)) for v in value)
    return str(value)


def _load_robot_yaml(path):
    file_path = Path(path).expanduser()
    if not file_path.is_file():
        raise RuntimeError(f"robot_config_file not found: {file_path}")
    with file_path.open() as handle:
        data = yaml.safe_load(handle) or {}
    if "lift" not in data:
        raise RuntimeError(f"{file_path}: missing top-level 'lift:' section")
    return data


def _resolve_lift_values(context):
    """CLI argument if given, else the YAML file, else nothing (xacro default)."""
    params_file = context.perform_substitution(LaunchConfiguration("robot_config_file"))
    lift = _load_robot_yaml(params_file) if params_file else {}

    resolved = {}
    for arg_name, yaml_path in YAML_MAP.items():
        override = context.perform_substitution(LaunchConfiguration(arg_name)).strip()
        if override:
            resolved[arg_name] = override
            continue
        value = _dig(lift, yaml_path)
        if value is None:
            continue
        resolved[arg_name] = (
            _as_xyz_string(value) if isinstance(value, (list, tuple)) else str(value)
        )
    return resolved


def _validate(resolved):
    """Catch physically impossible geometry before xacro silently produces junk."""
    problems = []
    warnings = []

    home = resolved.get("lift_home_height")
    max_h = resolved.get("lift_max_height")
    platform_xyz = resolved.get("lift_platform_xyz", "0 0 0.02")

    try:
        platform_z = float(platform_xyz.split()[2])
    except (ValueError, IndexError):
        problems.append(f"lift_platform_xyz must be 'x y z', got {platform_xyz!r}")
        platform_z = 0.02

    if home is not None and max_h is not None:
        try:
            home_f, max_f = float(home), float(max_h)
            if max_f <= home_f:
                problems.append(
                    f"lift_max_height ({max_f}) must be greater than "
                    f"lift_home_height ({home_f})"
                )
            tube_length = home_f - platform_z
            travel = max_f - home_f
            if tube_length <= 0.0:
                problems.append(
                    f"home_height ({home_f}) must exceed platform z offset "
                    f"({platform_z}); tube length would be {tube_length}"
                )
            elif travel > tube_length + 1e-9:
                warnings.append(
                    f"travel ({travel:.3f} m) exceeds tube length "
                    f"({tube_length:.3f} m): the rod cannot telescope that far "
                    f"and would come fully out of the tube"
                )
        except ValueError as exc:
            problems.append(f"lift heights must be numbers: {exc}")

    for message in problems:
        raise RuntimeError(f"Invalid lift configuration: {message}")
    for message in warnings:
        print(f"[WARN] lift_actuator: {message}")


def _launch_setup(context, *args, **kwargs):
    resolved = _resolve_lift_values(context)
    _validate(resolved)

    xacro_cmd = [
        PathJoinSubstitution([FindExecutable(name="xacro")]),
        " ",
        PathJoinSubstitution(
            [
                FindPackageShare("scout_with_piper_description"),
                "urdf",
                "scout_mini_piper.xacro",
            ]
        ),
    ]
    for key in LIFT_KEYS:
        if key in resolved:
            # Quote everything: values may contain spaces (xyz triples).
            xacro_cmd += [" ", key, ':="', resolved[key], '"']

    robot_description = ParameterValue(Command(xacro_cmd), value_type=str)
    use_sim_time = LaunchConfiguration("use_sim_time")
    gui = LaunchConfiguration("gui")

    return [
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[
                {
                    "use_sim_time": use_sim_time,
                    "robot_description": robot_description,
                }
            ],
            output="screen",
        ),
        # Node(
        #     package="joint_state_publisher",
        #     executable="joint_state_publisher",
        #     condition=UnlessCondition(gui),
        # ),
        Node(
            package="joint_state_publisher_gui",
            executable="joint_state_publisher_gui",
            condition=IfCondition(gui),
        ),
    ]


def generate_launch_description():
    default_params = PathJoinSubstitution(
        [
            FindPackageShare("scout_with_piper_description"),
            "config",
            "robot.yaml",
        ]
    )

    declared = [
        DeclareLaunchArgument(
            "robot_config_file",
            default_value=default_params,
            description="YAML file holding the lift dimensions",
        )
    ]
    for key in LIFT_KEYS:
        declared.append(
            DeclareLaunchArgument(
                key,
                default_value="",
                description=f"Override for {key}; empty means use the YAML value",
            )
        )
    declared += [
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use /clock from sim",
        ),
        DeclareLaunchArgument(
            "gui",
            default_value="true",
            description="Joint sliders (gui) vs static zeros",
        ),
        OpaqueFunction(function=_launch_setup),
    ]
    return LaunchDescription(declared)
