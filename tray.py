"""
tray.py — Windows system tray icon for Jarvis.

Design:
  - Runs in its own daemon thread so it never blocks the main HUD thread.
  - Tray icon is generated programmatically via Pillow — no external assets needed.
  - Right-click menu: Show/Hide Orb | Quit Jarvis
  - "Quit" routes through os._exit(0), identical to saying "goodbye" — no shortcuts
    or bypasses around the PENDING_ACTION shutdown lock. PC shutdown is NOT in the menu.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Callable, Optional

logger = logging.getLogger("Jarvis")


def _make_icon_image(size: int = 64, color: tuple = (0, 180, 255)):
    """Generate a simple glowing dot as the tray icon image using Pillow."""
    from PIL import Image, ImageDraw, ImageFilter

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer glow ring
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(*color, 80),
    )
    # Inner bright core
    inner = size // 4
    draw.ellipse(
        [inner, inner, size - inner, size - inner],
        fill=(*color, 220),
    )
    # Soft blur for glow effect
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    return img


class JarvisTray:
    """System tray icon controller.

    Usage:
        tray = JarvisTray(on_quit=lambda: os._exit(0))
        tray.start()   # non-blocking, runs in daemon thread
    """

    def __init__(
        self,
        on_quit: Callable,
        get_hud_visible: Optional[Callable[[], bool]] = None,
        set_hud_visible: Optional[Callable[[bool], None]] = None,
    ):
        self._on_quit         = on_quit
        self._get_hud_visible = get_hud_visible
        self._set_hud_visible = set_hud_visible
        self._icon            = None

    def _build_menu(self):
        """Build the right-click context menu."""
        import pystray

        items = []

        # Show/Hide Orb — only if HUD callbacks are wired
        if self._get_hud_visible and self._set_hud_visible:
            def toggle_orb(icon, item):
                current = self._get_hud_visible()
                self._set_hud_visible(not current)
                logger.info(f"TRAY: orb visibility toggled to {not current}")

            items.append(pystray.MenuItem("Show / Hide Orb", toggle_orb))
            items.append(pystray.Menu.SEPARATOR)

        # Quit — identical path to saying "goodbye"
        def quit_jarvis(icon, item):
            logger.info("TRAY: Quit selected")
            icon.stop()
            self._on_quit()

        items.append(pystray.MenuItem("Quit Jarvis", quit_jarvis))
        return pystray.Menu(*items)

    def start(self) -> None:
        """Start the tray icon in a background daemon thread."""
        def _run():
            try:
                import pystray
                icon_image = _make_icon_image()
                self._icon = pystray.Icon(
                    name="Jarvis",
                    icon=icon_image,
                    title="Jarvis",
                    menu=self._build_menu(),
                )
                logger.info("TRAY: icon started")
                self._icon.run()
            except Exception as e:
                logger.error(f"TRAY: failed to start: {e}")

        t = threading.Thread(target=_run, daemon=True, name="Tray-Icon")
        t.start()
        logger.info("TRAY: thread launched")

    def update_tooltip(self, text: str) -> None:
        """Update the tray icon tooltip text."""
        if self._icon:
            try:
                self._icon.title = text
            except Exception:
                pass
