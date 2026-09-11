"""
tts_cache.py — Pre-generated audio cache for a fixed set of system phrases.

Privacy / data-hygiene design:
    This module caches a SMALL, EXPLICITLY NAMED set of phrases only.
    It is NOT a general-purpose memoization of speak().

    Caching arbitrary LLM responses would:
      1. Create a growing folder of MP3s = silent audio transcript of all conversations.
      2. Provide zero performance benefit (LLM responses are rarely identical twice).

    The structural guard is CACHEABLE_PHRASES:
      - ensure_cache(key) returns None for any key NOT in this dict.
      - speak_cached(key) only accepts keys that exist here.
      - The general speak() path in jarvis.py never imports or calls this module.

    Only startup / fixed shutdown messages belong here.

Cache invalidation:
    Cache filename = SHA-256(phrase + voice)[:16].mp3
    Changing the voice in jarvis.ini automatically invalidates old cache files
    because the hash changes. Old .mp3 files are left on disk but never played.
    Run `del cache\\*.mp3` to purge stale files manually if needed.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from typing import Optional

logger = logging.getLogger("Jarvis")

# ── Cache directory ────────────────────────────────────────────────────────────
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")

# ── Fixed phrase registry ──────────────────────────────────────────────────────
# This dict is the ONLY source of truth for what is cacheable.
# To add a phrase: add a key here. To remove: delete the key.
# Do NOT call ensure_cache() with arbitrary strings from outside this module.
CACHEABLE_PHRASES: dict[str, str] = {
    "startup":            "Jarvis online. All systems secure and ready.",
    "goodbye":            "Goodbye, sir!",
    "shutdown_confirmed": "Shutting down in 10 seconds. Goodbye, sir.",
}


def _cache_path(key: str, voice: str) -> str:
    """Compute the deterministic MP3 path for a given key + voice combination."""
    phrase = CACHEABLE_PHRASES[key]
    digest = hashlib.sha256(f"{phrase}{voice}".encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{digest}.mp3")


async def _generate_mp3(phrase: str, voice: str, out_path: str) -> None:
    """Generate an MP3 for `phrase` using Edge TTS and save it to `out_path`."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(phrase, voice)
        await communicate.save(out_path)
        logger.info(f"TTS_CACHE: generated '{out_path}'")
    except Exception as e:
        logger.error(f"TTS_CACHE: generation failed: {e}")
        raise


def ensure_cache(key: str, voice: str) -> Optional[str]:
    """Return the path to the cached MP3 for `key`, generating it if needed.

    Args:
        key:   A key that must exist in CACHEABLE_PHRASES. Returns None otherwise.
        voice: Edge TTS voice name (e.g. "en-GB-RyanNeural").

    Returns:
        Absolute path to the MP3 file, or None if key is unknown or generation fails.
    """
    if key not in CACHEABLE_PHRASES:
        # Structural guard — unknown keys never get cached.
        logger.warning(f"TTS_CACHE: rejected unknown key '{key}'")
        return None

    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(key, voice)

    if os.path.exists(path):
        return path

    # Generate synchronously (called at startup, blocking is acceptable here).
    try:
        asyncio.run(_generate_mp3(CACHEABLE_PHRASES[key], voice, path))
        return path if os.path.exists(path) else None
    except Exception:
        return None


def speak_cached(key: str, play_fn) -> bool:
    """Speak a cached phrase by key using the provided play function.

    Args:
        key:     A key in CACHEABLE_PHRASES.
        play_fn: Callable that accepts a file path and plays the MP3 synchronously.
                 (Typically `_play_mp3_mci` from jarvis.py.)

    Returns:
        True if the cached file was played, False if cache miss or error.
    """
    from config import cfg

    path = ensure_cache(key, cfg.voice.tts_voice)
    if path and os.path.exists(path):
        try:
            play_fn(path)
            logger.info(f"TTS_CACHE: played cached '{key}'")
            return True
        except Exception as e:
            logger.warning(f"TTS_CACHE: playback failed for '{key}': {e}")
    return False


def warm_cache(voice: str) -> None:
    """Pre-generate all CACHEABLE_PHRASES at startup.

    Called once during main() so the first spoken phrase is instant.
    Runs synchronously — acceptable since it happens before the HUD starts.
    """
    logger.info("TTS_CACHE: warming cache...")
    for key in CACHEABLE_PHRASES:
        result = ensure_cache(key, voice)
        status = "OK" if result else "FAILED"
        logger.info(f"TTS_CACHE: warm '{key}' -> {status}")
