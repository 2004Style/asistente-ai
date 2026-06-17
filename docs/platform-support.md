# Platform Support Matrix

This matrix describes the supported actions across different operating systems.

| Capability | Linux (X11) | Linux (Wayland) | Windows (Win32) | macOS (Darwin) |
|------------|-------------|-----------------|-----------------|----------------|
| Keyboard   | xdotool     | Mock simulation | PyAutoGUI       | Mock simulation|
| Mouse      | xdotool     | Mock simulation | PyAutoGUI       | Mock simulation|
| Web Browser| webbrowser  | webbrowser      | webbrowser      | webbrowser     |
| Windows    | wmctrl      | IPC (Hyprland)  | win32 APIs      | AppleScript    |
| Terminal   | Sandbox     | Sandbox         | cmd/PowerShell  | osascript      |
