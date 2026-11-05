# Isaac Sim URDF synthesis patch

Isaac Sim's `ros2_control_manager` exports a URDF from the USD stage before it
creates the `controller_manager`. In Isaac Sim 6.2.0 the root selection in
`_prune_to_control_tree` drops the fixed joints that connect the lift tube, the
arm, and the gripper. The exported URDF then has several roots, urdfdom rejects
it, and no `controller_manager` is created.

Apply the patch to the installed Isaac Sim file, not to the USD asset.

## File

```bash
ISAAC_DIR=/mnt/toshiba_hdd/software/isaacsim/isaac-sim_6.2.0
PATCH_FILE="$ISAAC_DIR/exts/isaacsim.ros2.control/isaacsim/ros2/control/urdf_synth.py"
```

`$isaac_sim_package_path` resolves to the same install. `~/isaacsim` is the same
inode as `$ISAAC_DIR`, so patching one path patches both.

## Apply

```bash
cd "$(dirname "$PATCH_FILE")"
cp -n urdf_synth.py urdf_synth.py.bak
```

Replace the root computation in `_prune_to_control_tree`:

```diff
-    control_children = {c for _, c in control_edges}
+    # A link is a root only if no joint at all feeds it. Testing against the
+    # driven joints' children alone mislabels links that hang off a fixed joint
+    # (lift tube on the chassis, arm on the lift rod, gripper on the last arm
+    # link): they look like extra roots, the BFS below then discards the fixed
+    # joints that connect them, and the URDF ends up with several root links,
+    # which urdfdom rejects ("Two root links found").
+    all_children = {c for p, c in (parent_child(j) for j in joints) if p and c}
     roots: list[str] = []
     for p, _ in control_edges:
-        if p not in control_children and p not in roots:
+        if p not in all_children and p not in roots:
             roots.append(p)
```

Validate and clear stale bytecode:

```bash
python3 -m py_compile "$PATCH_FILE"
```

Restart Isaac Sim. The module is imported at startup, so Stop/Play does not
reload it.

## Verify

Press Play with the controller manager graph pointed at `/World/scout_mini_piper`,
then check the exported URDF:

```bash
ls -dt /tmp/ros2_control_urdf_* | head -1
pixi run check_urdf /tmp/ros2_control_urdf_<pid>_<id>/robot.urdf
```

Expected:

```text
Successfully Parsed XML
root Link: base_link has 6 child(ren)
```

The model must have 20 links, 19 joints, and exactly one root. If `check_urdf`
still reports two roots, the patch did not load; restart Isaac Sim again.

## Re-apply after an Isaac Sim reinstall or upgrade

The patch is outside this repository. Keep `urdf_synth.py.bak` until the
patched behavior has been verified, then re-apply this diff to the new install.
