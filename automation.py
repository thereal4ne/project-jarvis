"""
automation.py — Safe, hardcoded system automation tools for Jarvis.

Design principles:
- Every function is a direct Python call with no shell execution or string injection.
- Media keys use ctypes hardware-level virtual key codes (VK_*), not pyautogui,
  so they work regardless of which window is currently focused.
- Shutdown is intentionally NOT exposed here. It is handled by a two-step
  PENDING_ACTION state machine in jarvis.py.
"""

import ctypes
import logging
import subprocess

logger = logging.getLogger("Jarvis")

def open_application(app_name: str) -> str:
    """Attempt to launch a basic Windows application by name."""
    try:
        # Launch independently so it doesn't block the backend
        subprocess.Popen(f"start {app_name}", shell=True)
        return f"Opening {app_name}."
    except Exception as e:
        logger.error(f"open_application failed: {e}")
        return f"Could not open {app_name}."

# ─── Windows Virtual Key Codes for hardware-level media/volume ───────────────
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_VOLUME_MUTE      = 0xAD
VK_VOLUME_UP        = 0xAF
VK_VOLUME_DOWN      = 0xAE

KEYEVENTF_KEYUP = 0x0002


def _send_vk(vk_code: int) -> None:
    """Sends a hardware-level virtual keypress via keybd_event (legacy API).
    Works globally regardless of which window is focused.
    If this ever becomes unreliable, the modern equivalent is SendInput.
    """
    user32 = ctypes.windll.user32
    user32.keybd_event(vk_code, 0, 0, 0)
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


# ─── Media Controls ───────────────────────────────────────────────────────────

def media_play_pause() -> str:
    """Toggle play/pause in the active media session (Spotify, YouTube, etc.)."""
    try:
        _send_vk(VK_MEDIA_PLAY_PAUSE)
        logger.info("AUTOMATION: media_play_pause")
        return "Done."
    except Exception as e:
        logger.error(f"media_play_pause failed: {e}")
        return "Sorry, I couldn't control media playback."


def media_next() -> str:
    """Skip to the next track in the active media session."""
    try:
        _send_vk(VK_MEDIA_NEXT_TRACK)
        logger.info("AUTOMATION: media_next")
        return "Skipping to next track."
    except Exception as e:
        logger.error(f"media_next failed: {e}")
        return "Sorry, I couldn't skip the track."


def media_previous() -> str:
    """Go back to the previous track in the active media session."""
    try:
        _send_vk(VK_MEDIA_PREV_TRACK)
        logger.info("AUTOMATION: media_previous")
        return "Going back to previous track."
    except Exception as e:
        logger.error(f"media_previous failed: {e}")
        return "Sorry, I couldn't go back a track."


# ─── Volume Controls ──────────────────────────────────────────────────────────

def volume_mute() -> str:
    """Toggle system volume mute."""
    try:
        _send_vk(VK_VOLUME_MUTE)
        logger.info("AUTOMATION: volume_mute")
        return "Volume muted."
    except Exception as e:
        logger.error(f"volume_mute failed: {e}")
        return "Sorry, I couldn't toggle mute."


def volume_up() -> str:
    """Increase system volume by two steps."""
    try:
        _send_vk(VK_VOLUME_UP)
        _send_vk(VK_VOLUME_UP)
        logger.info("AUTOMATION: volume_up")
        return "Volume up."
    except Exception as e:
        logger.error(f"volume_up failed: {e}")
        return "Sorry, I couldn't raise the volume."


def volume_down() -> str:
    """Decrease system volume by two steps."""
    try:
        _send_vk(VK_VOLUME_DOWN)
        _send_vk(VK_VOLUME_DOWN)
        logger.info("AUTOMATION: volume_down")
        return "Volume down."
    except Exception as e:
        logger.error(f"volume_down failed: {e}")
        return "Sorry, I couldn't lower the volume."


# ─── Window Management ────────────────────────────────────────────────────────

def close_active_window() -> str:
    """Close the currently focused window (sends Alt+F4)."""
    try:
        user32 = ctypes.windll.user32
        VK_F4  = 0x73
        VK_MENU = 0x12  # Alt key
        KEYEVENTF_EXTENDEDKEY = 0x0001

        user32.keybd_event(VK_MENU, 0, KEYEVENTF_EXTENDEDKEY, 0)
        user32.keybd_event(VK_F4, 0, 0, 0)
        user32.keybd_event(VK_F4, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
        logger.info("AUTOMATION: close_active_window")
        return "Closing the active window."
    except Exception as e:
        logger.error(f"close_active_window failed: {e}")
        return "Sorry, I couldn't close the window."


def minimize_all_windows() -> str:
    """Minimize all windows and show the desktop (Win+D)."""
    try:
        user32 = ctypes.windll.user32
        VK_WIN = 0x5B   # Left Windows key
        VK_D   = 0x44
        KEYEVENTF_EXTENDEDKEY = 0x0001

        user32.keybd_event(VK_WIN, 0, KEYEVENTF_EXTENDEDKEY, 0)
        user32.keybd_event(VK_D, 0, 0, 0)
        user32.keybd_event(VK_D, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_WIN, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
        logger.info("AUTOMATION: minimize_all_windows")
        return "Showing the desktop."
    except Exception as e:
        logger.error(f"minimize_all_windows failed: {e}")
        return "Sorry, I couldn't minimize the windows."


# ─── System Controls ─────────────────────────────────────────────────────────

def lock_screen() -> str:
    """Lock the Windows session immediately. Safe and reversible."""
    try:
        ctypes.windll.user32.LockWorkStation()
        logger.info("AUTOMATION: lock_screen")
        return "Locking the screen."
    except Exception as e:
        logger.error(f"lock_screen failed: {e}")
        return "Sorry, I couldn't lock the screen."


def execute_shutdown() -> str:
    """Executes an immediate system shutdown.
    
    IMPORTANT: This must ONLY be called from the deterministic PENDING_ACTION
    confirmation lock in jarvis.py. It must never be registered as an LLM tool.
    The LLM only has access to request_pc_shutdown(), which arms the pending state.
    """
    try:
        subprocess.run(["shutdown", "/s", "/t", "10"], check=True)
        logger.info("AUTOMATION: execute_shutdown — confirmed by user")
        return "Shutting down in 10 seconds. Goodbye, sir."
    except Exception as e:
        logger.error(f"execute_shutdown failed: {e}")
        return "Sorry, I couldn't initiate shutdown."


# ─── Clipboard Write ─────────────────────────────────────────────────────────

def write_to_clipboard(text: str) -> str:
    """Place text into the system clipboard. Safe output-only operation."""
    try:
        import pyperclip
        pyperclip.copy(text)
        logger.info(f"AUTOMATION: write_to_clipboard ({len(text)} chars)")
        return "I've copied that to your clipboard. You can paste it anywhere with Ctrl+V."
    except ImportError:
        return "Clipboard write unavailable. Please run: pip install pyperclip"
    except Exception as e:
        logger.error(f"write_to_clipboard failed: {e}")
        return "Sorry, I couldn't write to the clipboard."


# ─── Screenshot ───────────────────────────────────────────────────────────────

def take_screenshot() -> str:
    """Capture the full screen and save to the configured folder.

    Zero arguments by design — the LLM can trigger a screenshot but can
    NEVER influence where it is saved. The save path is derived entirely
    from config (config.screenshot.save_folder + timestamp). This guarantee
    is structural (no params in function OR tool schema), not policy-only.
    """
    try:
        from PIL import ImageGrab
        from datetime import datetime
        from config import cfg

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename  = f"jarvis_screenshot_{timestamp}.png"
        save_dir  = os.path.expanduser(cfg.screenshot.save_folder)
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)

        img = ImageGrab.grab()
        img.save(save_path)
        logger.info(f"AUTOMATION: take_screenshot -> {save_path}")
        return f"Screenshot saved as {filename} on your Desktop."
    except ImportError:
        return "Screenshot unavailable. Please run: pip install Pillow"
    except Exception as e:
        logger.error(f"take_screenshot failed: {e}")
        return "Sorry, I couldn't take a screenshot."


# ─── Precise Volume Control ───────────────────────────────────────────────────

def set_volume_percent(percent: int) -> str:
    """Set the Windows master volume to an exact percentage using pycaw.

    Uses Windows Core Audio API (WASAPI) via pycaw — far more reliable than
    counting VK_VOLUME_UP/DOWN keypresses, which don't know the current level.

    Args:
        percent: Target volume level, 0–100. Clamped silently to that range.
    """
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        percent = max(0, min(100, int(percent)))   # Clamp: never go out of range
        devices   = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume    = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(percent / 100.0, None)
        logger.info(f"AUTOMATION: set_volume_percent({percent})")
        return f"Volume set to {percent} percent."
    except ImportError:
        return "Precise volume control unavailable. Please run: pip install pycaw"
    except Exception as e:
        logger.error(f"set_volume_percent failed: {e}")
        return "Sorry, I couldn't set the volume."
