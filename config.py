"""
config.py — Centralized, typed configuration for Jarvis.

Architecture:
  - JarvisConfig is a frozen dataclass (immutable after load).
  - Loaded once at startup via load_config() and shared as a module-level singleton.
  - All modules import `cfg` from this file — nothing reads jarvis.ini or os.environ
    directly (except this module and the .env loader in jarvis.py).

Boundary rule (ENFORCED BY CONVENTION, documented here):
  - jarvis.ini  → safe to git-track. Contains tuning parameters only.
  - .env        → NEVER git-tracked. Contains secrets (API keys, passphrase).
  - These two files serve different purposes and must never be merged.
"""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, field
from typing import List

# Path to the config file — sits alongside this module.
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "jarvis.ini")

# Default search folders (used when jarvis.ini has no [search] folders entry).
_DEFAULT_HOME = os.path.expanduser("~")
_DEFAULT_SEARCH_FOLDERS: List[str] = [
    os.path.join(_DEFAULT_HOME, "Desktop"),
    os.path.join(_DEFAULT_HOME, "Documents"),
    os.path.join(_DEFAULT_HOME, "Downloads"),
]


@dataclass(frozen=True)
class GeneralConfig:
    model_name: str = "gemini-2.0-flash"
    history_turns: int = 8
    pending_action_timeout: int = 30


@dataclass(frozen=True)
class VoiceConfig:
    tts_voice: str = "en-GB-RyanNeural"
    # Fixed set of phrases to pre-cache. Kept small and explicit — this is NOT
    # a general memoization list. See tts_cache.py for the privacy reasoning.
    cache_phrases: List[str] = field(default_factory=lambda: [
        "Jarvis online. All systems secure and ready.",
        "Goodbye, sir!",
        "Shutting down in 10 seconds. Goodbye, sir.",
    ])


@dataclass(frozen=True)
class HUDConfig:
    position:       str  = "top-right"   # "top-right" | "top-left" | "bottom-right" | "bottom-left"
    size:           int  = 100           # Orb canvas size in pixels
    boot_animation: bool = True          # Play cinematic boot animation on startup


@dataclass(frozen=True)
class SearchConfig:
    folders: List[str] = field(default_factory=lambda: list(_DEFAULT_SEARCH_FOLDERS))
    search_depth: int = 2


@dataclass(frozen=True)
class ScreenshotConfig:
    # Save folder is config-only — never derived from user/LLM input.
    save_folder: str = os.path.join(_DEFAULT_HOME, "Desktop")


@dataclass(frozen=True)
class JarvisConfig:
    general: GeneralConfig = field(default_factory=GeneralConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    hud: HUDConfig = field(default_factory=HUDConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    screenshot: ScreenshotConfig = field(default_factory=ScreenshotConfig)


def _parse_list(raw: str) -> List[str]:
    """Parse a semicolon-separated string into a list, filtering empty strings."""
    return [item.strip() for item in raw.split(";") if item.strip()]


def load_config() -> JarvisConfig:
    """Load jarvis.ini and return a JarvisConfig. Missing keys fall back to defaults.

    This function is deliberately tolerant — a missing file or missing section
    returns a fully-default config rather than crashing, so Jarvis works
    out-of-the-box without requiring a config file.
    """
    parser = configparser.ConfigParser()
    parser.read(_CONFIG_PATH, encoding="utf-8")

    def get(section: str, key: str, fallback: str) -> str:
        return parser.get(section, key, fallback=fallback)

    # [general]
    general = GeneralConfig(
        model_name=get("general", "model_name", "gemini-3.6-flash"),
        history_turns=int(get("general", "history_turns", "8")),
        pending_action_timeout=int(get("general", "pending_action_timeout", "30")),
    )

    # [voice]
    raw_cache = get("voice", "cache_phrases", "")
    cache_list = _parse_list(raw_cache) if raw_cache else VoiceConfig().cache_phrases
    voice = VoiceConfig(
        tts_voice=get("voice", "tts_voice", "en-GB-RyanNeural"),
        cache_phrases=cache_list,
    )

    # [hud]
    hud = HUDConfig(
        position=get("hud", "position", "top-right"),
        size=int(get("hud", "size", "100")),
        boot_animation=get("hud", "boot_animation", "true").lower() != "false",
    )

    # [search]
    raw_folders = get("search", "folders", "")
    search_folders = _parse_list(raw_folders) if raw_folders else list(_DEFAULT_SEARCH_FOLDERS)
    search = SearchConfig(
        folders=search_folders,
        search_depth=int(get("search", "search_depth", "2")),
    )

    # [screenshot]
    screenshot = ScreenshotConfig(
        save_folder=os.path.expanduser(
            get("screenshot", "save_folder", os.path.join(_DEFAULT_HOME, "Desktop"))
        )
    )

    return JarvisConfig(
        general=general,
        voice=voice,
        hud=hud,
        search=search,
        screenshot=screenshot,
    )


def load_shortcuts() -> dict:
    """Load user-defined Fast Path shortcuts from jarvis.ini [shortcuts].

    Format in jarvis.ini:
        [shortcuts]
        standup = open chrome;open notion
        morning = time;date

    Each key is a trigger phrase (lowercased). The value is a semicolon-separated
    list of commands that will be run through handle_command() sequentially.

    Returns:
        Dict mapping lowercase trigger phrase -> list of command strings.
        Empty dict if no [shortcuts] section exists.
    """
    parser = configparser.ConfigParser()
    parser.read(_CONFIG_PATH, encoding="utf-8")
    if not parser.has_section("shortcuts"):
        return {}
    return {
        key.strip().lower(): [cmd.strip() for cmd in value.split(";") if cmd.strip()]
        for key, value in parser.items("shortcuts")
    }


# Module-level singletons — import these everywhere.
cfg: JarvisConfig       = load_config()
SHORTCUTS: dict         = load_shortcuts()
