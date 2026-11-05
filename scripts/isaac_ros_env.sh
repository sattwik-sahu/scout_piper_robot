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

    # Controller plugins are Isaac's and create publishers with Isaac's C++
    # typesupport handles. rmw_zenoh then asks for the FastRTPS typesupport and
    # dlopens lib<pkg>__rosidl_typesupport_fastrtps_{c,cpp}.so by name. That
    # search hits Isaac's jazzy/lib first, whose typesupport_identifier pointer
    # is not the one Zenoh (loaded from the conda prefix) compares against, so
    # create_publisher fails with "Type support not from this implementation".
    #
    # Do not fix this with shim symlinks. Those libraries have RPATH $ORIGIN,
    # and $ORIGIN of a symlink is the shim directory, so their dependencies
    # would still resolve to Isaac's copies. Preload the real conda files:
    # dlopen of the same SONAME then returns the already-loaded pixi copy, and
    # $ORIGIN stays the conda lib dir. This is the same mechanism rmw_env.sh
    # uses for librmw_zenoh_cpp.so, and it does not put $CONDA_PREFIX/lib on
    # LD_LIBRARY_PATH (which would load conda's libz and abort Kit).
    TYPESUPPORT_LIBS=(
        librosidl_typesupport_fastrtps_c.so
        librosidl_typesupport_fastrtps_cpp.so
        libaction_msgs__rosidl_typesupport_fastrtps_c.so
        libaction_msgs__rosidl_typesupport_fastrtps_cpp.so
        libbuiltin_interfaces__rosidl_typesupport_fastrtps_c.so
        libbuiltin_interfaces__rosidl_typesupport_fastrtps_cpp.so
        libcontrol_msgs__rosidl_typesupport_fastrtps_c.so
        libcontrol_msgs__rosidl_typesupport_fastrtps_cpp.so
        libgeometry_msgs__rosidl_typesupport_fastrtps_c.so
        libgeometry_msgs__rosidl_typesupport_fastrtps_cpp.so
        libsensor_msgs__rosidl_typesupport_fastrtps_c.so
        libsensor_msgs__rosidl_typesupport_fastrtps_cpp.so
        libservice_msgs__rosidl_typesupport_fastrtps_c.so
        libservice_msgs__rosidl_typesupport_fastrtps_cpp.so
        libstd_msgs__rosidl_typesupport_fastrtps_c.so
        libstd_msgs__rosidl_typesupport_fastrtps_cpp.so
        libtrajectory_msgs__rosidl_typesupport_fastrtps_c.so
        libtrajectory_msgs__rosidl_typesupport_fastrtps_cpp.so
        libunique_identifier_msgs__rosidl_typesupport_fastrtps_c.so
        libunique_identifier_msgs__rosidl_typesupport_fastrtps_cpp.so
    )
    for lib in "${TYPESUPPORT_LIBS[@]}"; do
        src=$(ls "$CONDA_PREFIX/lib/$lib" 2>/dev/null | head -1 || true)
        if [[ -z "$src" ]]; then
            echo "isaac_ros_env: missing $lib in $CONDA_PREFIX/lib" >&2
            exit 1
        fi
        export LD_PRELOAD="$(readlink -f "$src")${LD_PRELOAD:+:$LD_PRELOAD}"
    done
else
    # Non-Zenoh RMW (e.g. rmw_fastrtps_cpp): Isaac Sim ships a complete Fast DDS
    # stack in its own jazzy/lib, so no shim is needed, but that directory must
    # still be on LD_LIBRARY_PATH or librmw_fastrtps_cpp.so cannot be found.
    export LD_LIBRARY_PATH="$ISAAC_ROS_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

# Run whatever was passed, with the environment above in place. This script is
# used as a wrapper rather than sourced: pixi runs tasks under sh, where
# `source` does not exist, and the array syntax above needs bash anyway.
if [[ $# -gt 0 ]]; then
    exec "$@"
fi
