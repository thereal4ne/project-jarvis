from plugin_manager import jarvis_tool
from automation import (
    media_play_pause,
    media_next,
    media_previous,
    volume_mute,
    volume_up,
    volume_down,
    close_active_window,
    minimize_all_windows,
    lock_screen,
    take_screenshot,
    set_volume_percent,
    write_to_clipboard
)

@jarvis_tool
def tool_media_play_pause() -> str:
    """Toggle play or pause for the current media session (music, video, etc.)."""
    return media_play_pause()

@jarvis_tool
def tool_media_next() -> str:
    """Skip to the next track in the current media session."""
    return media_next()

@jarvis_tool
def tool_media_previous() -> str:
    """Go back to the previous track in the current media session."""
    return media_previous()

@jarvis_tool
def tool_volume_mute() -> str:
    """Toggle the system volume mute on or off."""
    return volume_mute()

@jarvis_tool
def tool_volume_up() -> str:
    """Increase the system volume."""
    return volume_up()

@jarvis_tool
def tool_volume_down() -> str:
    """Decrease the system volume."""
    return volume_down()

@jarvis_tool
def tool_close_active_window() -> str:
    """Close the currently focused window."""
    return close_active_window()

@jarvis_tool
def tool_minimize_all_windows() -> str:
    """Minimize all windows and show the desktop."""
    return minimize_all_windows()

@jarvis_tool
def tool_lock_screen() -> str:
    """Lock the Windows screen immediately."""
    return lock_screen()

@jarvis_tool
def tool_take_screenshot() -> str:
    """Take a screenshot of the full screen and save it to the Desktop.
    Takes no arguments — the save path is determined by config only,
    never by user or LLM input.
    """
    return take_screenshot()

@jarvis_tool
def tool_set_volume(percent: int) -> str:
    """Set the system master volume to an exact percentage.
    Args:
        percent: Volume level from 0 to 100.
    """
    return set_volume_percent(percent)

@jarvis_tool
def tool_write_clipboard(text: str) -> str:
    """Write a response or generated text to the user's clipboard so they can paste it.
    Args:
        text: The text to place into the clipboard.
    """
    return write_to_clipboard(text)
