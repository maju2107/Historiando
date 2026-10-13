# Current Yara tools

Run from the Historiando root. Blender's Python script exports the current UV skin and rig to the canonical game file, retaining the authoring file and excluding the three RigCheck clips from the game export.

```powershell
& 'C:/Users/obran/AppData/Local/Microsoft/WindowsApps/blender-launcher.exe' --background --python-exit-code 1 --python tools/yara/export.py
```

Godot checks:

```powershell
& 'C:/Users/obran/Downloads/Godot_v4.7.1-stable_win64.exe/Godot_v4.7.1-stable_win64_console.exe' --headless --path . --script res://tools/yara/validate_player.gd
& 'C:/Users/obran/Downloads/Godot_v4.7.1-stable_win64.exe/Godot_v4.7.1-stable_win64_console.exe' --headless --path . --script res://tools/yara/validate_hair.gd
```

The validation JSON files go to `art/yara/validation/`. Existing shutdown resource-leak messages can cause a nonzero process exit after the checks pass; inspect each report's `issues` list. Existing unrelated whole-project rock_m.fbx import errors are separate.

`capture.gd` creates current action/close-up previews under `art/yara/previews/` with Vulkan Forward+. Launch it in a hidden helper process; it hides its root window itself. Exporting is only needed after a new model edit, not for this folder cleanup.
