# biolab-isaacsim_ws

> ⚠️ **WARNING: This repository is under construction.** Breaking changes may (and probably will) fuck you up. Pin your commits and expect things to move.

ROS 2 workspace for the Scout (v2 / mini) + telescoping lift + Piper arm mobile manipulator, with Isaac Sim bringup.

## Quick start

```bash
pixi install
pixi run build-scout
source install/setup.bash
ros2 launch scout_with_piper_description scout_mini_piper.launch.py
```

See `docs/usage.md` for configuration and launch details.