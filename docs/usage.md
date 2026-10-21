# Usage

> ⚠️ **This workspace is under construction. Expect breaking changes.**

## Build

```bash
pixi run build-scout   # builds scout_description + scout_with_piper_description (symlink install)
```

## Launch

```bash
source install/setup.bash
ros2 launch scout_with_piper_description scout_mini_piper.launch.py
# variants:
ros2 launch scout_with_piper_description scout_mini_piper_small.launch.py
ros2 launch scout_with_piper_description description.launch.py
```

## Configuration

All robot tunables live in `src/scout_with_piper_description/config/robot.yaml` (central config). Edit and relaunch — no rebuild needed (symlink install).

- `lift.*` — actuator mount, heights, platform offset.
- `left_camera.*` — `gripper_left_camera_link` transform (xyz/rpy) relative to `gripper_base_link`.

Override the file at launch:

```bash
ros2 launch scout_with_piper_description scout_mini_piper.launch.py robot_config_file:=/path/to/robot.yaml
```

## Notes

- Scout Mini uses indoor `wheel.dae` wheels (not rugged type1/type2).
- Meshes resolve via `scout_description` (now an ament package).