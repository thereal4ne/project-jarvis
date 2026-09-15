from plugin_manager import jarvis_tool
from memory import save_preference, forget_preference
from automation import set_reminder

@jarvis_tool
def tool_save_preference(key: str, value: str) -> str:
    """Save a user preference to persistent memory so Jarvis remembers it across sessions.
    Args:
        key:   The preference name, e.g. 'name', 'preferred volume', 'wake time'.
        value: The preference value, e.g. 'Albin', '40 percent', '7am'.
    """
    return save_preference(key, value)

@jarvis_tool
def tool_forget_preference(key: str) -> str:
    """Remove a previously saved user preference from memory.
    Args:
        key: The preference name to forget.
    """
    return forget_preference(key)

@jarvis_tool
def tool_set_reminder(duration_seconds: int, message: str) -> str:
    """Set a timed reminder that Jarvis will speak aloud after the delay.
    Args:
        duration_seconds: How many seconds until the reminder fires.
        message: What to remind the user about.
    """
    return set_reminder(duration_seconds, message)
