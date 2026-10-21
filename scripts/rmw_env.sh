#!/usr/bin/env bash
# RMW defaults for the workspace.
#
# This lives in an activation *script* rather than [activation.env] on purpose.
# Entries in [activation.env] are applied unconditionally and cannot be
# overridden from the command line, so `RMW_IMPLEMENTATION=rmw_fastrtps_cpp pixi
# run ros2 topic list` would silently keep using Zenoh. A shell script can
# respect a value the caller already exported.

# Zenoh by default; any caller-provided value wins.
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_zenoh_cpp}"

# Preload the Zenoh plugin only when Zenoh is the selected RMW. Preloading it
# unconditionally makes an rmw_fastrtps_cpp session initialise Zenoh anyway,
# which produces confusing zenoh_config warnings and hides the real middleware.
if [[ "$RMW_IMPLEMENTATION" == "rmw_zenoh_cpp" ]]; then
    export LD_PRELOAD="$CONDA_PREFIX/lib/librmw_zenoh_cpp.so${LD_PRELOAD:+:$LD_PRELOAD}"
fi
