#!/usr/bin/env bash
# Make the Zenoh RMW loadable inside Isaac Sim, without poisoning Kit's Python.
#
# Isaac Sim's ROS 2 core (libisaacsim.ros2.core.jazzy.so) links against librmw.so,
# the RMW *dispatcher*, which dlopens whichever implementation RMW_IMPLEMENTATION
# names. It is therefore not Fast DDS specific, but it does not ship
# rmw_zenoh_cpp — those libraries have to come from the conda environment.
#
# Do NOT put $CONDA_PREFIX/lib on LD_LIBRARY_PATH wholesale. conda's libz is
# ABI-incompatible with the CPython that Kit embeds, so `import zlib` fails,
# every Python extension fails to load in a cascade, and the app aborts during
# startup with "No module named 'zlib'". Instead, expose only the handful of
# Zenoh-specific libraries through a shim directory; the rest of the ROS 2 stack
# (librmw.so, librosidl_*, librcutils, libament_index_cpp) is already present in
# Isaac Sim's own jazzy/lib.
#
# The shim lives in the workspace rather than under $CONDA_PREFIX so that it
# survives run_isaacsim.py, which strips conda entries from LD_LIBRARY_PATH.

set -euo pipefail

SHIM_DIR="${PIXI_PROJECT_ROOT}/.zenoh_shim"
ISAAC_ROS_LIB="${isaac_sim_package_path}/exts/isaacsim.ros2.core/jazzy/lib"

# Libraries that exist only in the conda environment. libfastcdr.so.2 is
# deliberately absent: Isaac Sim already ships a compatible copy.
ZENOH_LIBS=(
    libzenohc.so
    librmw_zenoh_cpp.so
    libtracetools.so
    liblttng-ust.so.1
    liblttng-ust-common.so.1
    liblttng-ust-tracepoint.so.1
)

# Fast DDS and Cyclone DDS ship inside Isaac Sim, so they need no shim.
if [[ "${RMW_IMPLEMENTATION:-}" == "rmw_zenoh_cpp" ]]; then
    mkdir -p "$SHIM_DIR"
    for lib in "${ZENOH_LIBS[@]}"; do
        src=$(ls "$CONDA_PREFIX/lib/$lib" 2>/dev/null | head -1 || true)
        if [[ -z "$src" ]]; then
            echo "isaac_ros_env: missing $lib in $CONDA_PREFIX/lib" >&2
            exit 1
        fi
        ln -sf "$(readlink -f "$src")" "$SHIM_DIR/$lib"
    done

    # Isaac Sim's own libs supply libyaml.so and the typesupport set; the shim
    # supplies the Zenoh RMW. Both are needed for the bridge to load.
    export LD_LIBRARY_PATH="$SHIM_DIR:$ISAAC_ROS_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

# Run whatever was passed, with the environment above in place. This script is
# used as a wrapper rather than sourced: pixi runs tasks under sh, where
# `source` does not exist, and the array syntax above needs bash anyway.
if [[ $# -gt 0 ]]; then
    exec "$@"
fi
