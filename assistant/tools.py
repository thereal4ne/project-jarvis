import os
from dotenv import load_dotenv

load_dotenv()

# We keep tools static and straightforward for now, as per the scope control decision.
# In a real environment, these call `automation.py`.
# For tests (especially in CI), we can mock these easily.

try:
    from automation import (
        volume_mute, volume_up, volume_down,
        close_active_window, minimize_all_windows, lock_screen
    )
except ImportError:
    # Fallback for Ubuntu CI or missing dependencies
    volume_mute = lambda: "Muted"
    volume_up = lambda: "Volume Up"
    volume_down = lambda: "Volume Down"
    close_active_window = lambda: "Closed window"
    minimize_all_windows = lambda: "Minimized windows"
    lock_screen = lambda: "Screen locked"


def tool_volume_mute() -> str:
    """Toggle the system volume mute on or off."""
    return volume_mute()

def tool_volume_up() -> str:
    """Increase the system volume."""
    return volume_up()

def tool_volume_down() -> str:
    """Decrease the system volume."""
    return volume_down()

def tool_close_active_window() -> str:
    """Close the currently focused window."""
    return close_active_window()

def tool_minimize_all_windows() -> str:
    """Minimize all windows and show the desktop."""
    return minimize_all_windows()

def tool_lock_screen() -> str:
    """Lock the Windows screen immediately."""
    return lock_screen()

def tool_open_application(app_name: str) -> str:
    """Launch a Windows application. Pass the executable name like 'calc' or 'notepad'."""
    try:
        from automation import open_application
        return open_application(app_name)
    except ImportError:
        return f"Opened {app_name}"

def tool_request_pc_shutdown() -> str:
    """Request a PC shutdown. This arms a confirmation prompt — the user must
    confirm via the frontend to proceed. The LLM cannot trigger the shutdown directly.
    """
    return "__PENDING_ACTION_SHUTDOWN__"


ALL_TOOLS = [
    tool_volume_mute, tool_volume_up, tool_volume_down,
    tool_close_active_window, tool_minimize_all_windows,
    tool_lock_screen, tool_open_application, tool_request_pc_shutdown
]

TOOL_MAP = {fn.__name__: fn for fn in ALL_TOOLS}
