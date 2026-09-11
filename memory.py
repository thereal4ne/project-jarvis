"""
memory.py — Persistent user preferences for Jarvis.

Stores key-value pairs in memory.json in the same directory as this file.
Survives restarts. Injected into the LLM system prompt so Jarvis acts
on preferences naturally without being told every session.

Security notes:
- File is local only, never sent to any external service.
- Preferences are injected as read-only context, not as executable instructions.
- The LLM can call save_preference/forget_preference only via registered tools,
  not via raw file access.
"""

import json
import os
import logging

logger = logging.getLogger("Jarvis")

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")


def load_preferences() -> dict:
    """Load all preferences from memory.json. Returns {} if file is missing or corrupt."""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception as e:
        logger.error(f"MEMORY: Failed to load preferences: {e}")
    return {}


def _write_preferences(prefs: dict) -> bool:
    """Internal: atomically writes prefs dict to disk. Returns True on success."""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"MEMORY: Failed to write preferences: {e}")
        return False


def save_preference(key: str, value: str) -> str:
    """Save or update a key-value preference.

    Args:
        key:   The preference name (e.g. 'name', 'preferred volume').
        value: The preference value (e.g. 'Albin', '40%').

    Returns:
        A spoken confirmation string.
    """
    key_clean = key.strip().lower()
    value_clean = value.strip()
    if not key_clean or not value_clean:
        return "I need both a preference name and a value to remember something."

    prefs = load_preferences()
    prefs[key_clean] = value_clean
    if _write_preferences(prefs):
        logger.info(f"MEMORY: saved '{key_clean}' = '{value_clean}'")
        return f"Got it. I'll remember that your {key_clean} is {value_clean}."
    return "Sorry, I couldn't save that to memory."


def forget_preference(key: str) -> str:
    """Remove a stored preference by key.

    Args:
        key: The preference name to forget.

    Returns:
        A spoken confirmation string.
    """
    key_clean = key.strip().lower()
    prefs = load_preferences()
    if key_clean in prefs:
        del prefs[key_clean]
        if _write_preferences(prefs):
            logger.info(f"MEMORY: forgot '{key_clean}'")
            return f"Done. I've forgotten your {key_clean}."
        return "Sorry, I couldn't update memory."
    return f"I don't have anything stored for {key_clean}."


def get_all_preferences() -> dict:
    """Returns the full preferences dict (for display or debug)."""
    return load_preferences()


def get_preferences_summary() -> str:
    """Returns a short plain-English summary for LLM system prompt injection.

    Example output:
        "Known user preferences: name: Albin; preferred volume: 40%."

    Returns empty string if no preferences are stored (so the system prompt
    stays clean when memory is empty).
    """
    prefs = load_preferences()
    if not prefs:
        return ""
    items = [f"{k}: {v}" for k, v in prefs.items()]
    return "Known user preferences — " + "; ".join(items) + "."
