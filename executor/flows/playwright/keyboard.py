"""VS Code keyboard shortcut constants.

Single source of truth for all shortcuts used by helper modules.
If VS Code changes a binding, update it here only.
"""

# Command Palette & Quick Open
COMMAND_PALETTE = "Control+Shift+KeyP"
QUICK_OPEN = "Control+KeyP"

# Editor
NEW_FILE = "Control+KeyN"
SAVE_FILE = "Control+KeyS"
SAVE_FILE_AS = "Control+Shift+KeyS"
CLOSE_EDITOR = "Control+KeyW"
CLOSE_ALL_EDITORS = "Control+KeyK Control+KeyW"  # chord

# Sidebar
TOGGLE_SIDEBAR = "Control+KeyB"
FOCUS_EXPLORER = "Control+Shift+KeyE"
FOCUS_SEARCH = "Control+Shift+KeyF"
FOCUS_SOURCE_CONTROL = "Control+Shift+KeyG"
FOCUS_DEBUG = "Control+Shift+KeyD"
FOCUS_EXTENSIONS = "Control+Shift+KeyX"

# Panel & Terminal
TOGGLE_TERMINAL = "Control+Backquote"
TOGGLE_PANEL = "Control+KeyJ"

# Navigation
FOCUS_EDITOR = "Escape"


# === Activation triggers ===

# Output panel (extension log monitoring)
FOCUS_OUTPUT = "Control+Shift+KeyU"

# Problems panel (diagnostics)
FOCUS_PROBLEMS = "Control+Shift+KeyM"

# Debug lifecycle
START_DEBUG = "F5"
STOP_DEBUG = "Shift+F5"
STEP_OVER = "F10"
STEP_INTO = "F11"

# Settings (onConfiguration events)
OPEN_SETTINGS = "Control+Comma"
OPEN_SETTINGS_JSON = ""  # command palette fallback

# Notebook (onNotebook triggers)
# No direct shortcut; use command palette fallback.

# Zen mode / layout (some extensions listen to layout events)
TOGGLE_FULLSCREEN = "F11"

# Editor actions
FORMAT_DOCUMENT = "Control+Shift+KeyI"  # triggers formatter extensions
GO_TO_DEFINITION = "F12"  # triggers language server extensions
TRIGGER_SUGGEST = "Control+Space"  # triggers completion providers
RENAME_SYMBOL = "F2"  # triggers rename providers

# Multi-cursor / selection (rare activation trigger, but some extensions listen)
SELECT_ALL = "Control+KeyA"

# Integrated terminal
NEW_TERMINAL = "Control+Shift+Backquote"
