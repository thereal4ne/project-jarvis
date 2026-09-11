"""
hud.py — Animated floating orb HUD for Jarvis.

Design:
  - Runs on the main thread (tkinter requirement).
  - State changes come from other threads via set_hud_state() (thread-safe).
  - Enhanced animation: 3-layer glow rings, sine-wave easing, smooth colour
    interpolation between states, draggable window with position persistence.
  - Right-click still kills Jarvis instantly (os._exit) as before.
  - Position is read from config on start and saved to jarvis.ini on drag-end.
"""

from __future__ import annotations

import configparser
import math
import os
import threading
import tkinter as tk
from typing import Tuple

# ── Thread-safe state ─────────────────────────────────────────────────────────
_current_state = "idle"
_state_lock    = threading.Lock()


def set_hud_state(new_state: str) -> None:
    """Update the HUD animation state from any thread.

    Valid states: 'idle' | 'listening' | 'thinking' | 'speaking'
    """
    global _current_state
    with _state_lock:
        _current_state = new_state


def get_hud_state() -> str:
    with _state_lock:
        return _current_state


# ── Colour palette per state ──────────────────────────────────────────────────
# Each entry: (core_fill, ring1_colour, ring2_colour, ring3_colour, speed, amplitude)
_STATE_PALETTE = {
    "idle": {
        "core":   "#0c1a2e",
        "rings":  ["#0369a1", "#0284c7", "#38bdf8"],
        "speed":  0.04,
        "amp":    5,
    },
    "listening": {
        "core":   "#001a1a",
        "rings":  ["#0891b2", "#22d3ee", "#67e8f9"],
        "speed":  0.12,
        "amp":    9,
    },
    "thinking": {
        "core":   "#1c0a00",
        "rings":  ["#b45309", "#f59e0b", "#fcd34d"],
        "speed":  0.25,
        "amp":    11,
    },
    "speaking": {
        "core":   "#001230",
        "rings":  ["#1d4ed8", "#60a5fa", "#e0f2fe"],
        "speed":  0.18,
        "amp":    8,
    },
}


def _hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _lerp_colour(c1: str, c2: str, t: float) -> str:
    """Linear interpolation between two hex colours. t in [0, 1]."""
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _load_saved_position() -> Tuple[int, int]:
    """Read last HUD position from jarvis.ini [hud] saved_x / saved_y."""
    try:
        ini = os.path.join(os.path.dirname(__file__), "jarvis.ini")
        p = configparser.ConfigParser()
        p.read(ini)
        x = int(p.get("hud", "saved_x", fallback="-1"))
        y = int(p.get("hud", "saved_y", fallback="-1"))
        if x >= 0 and y >= 0:
            return x, y
    except Exception:
        pass
    return -1, -1


def _save_position(x: int, y: int) -> None:
    """Persist HUD position to jarvis.ini."""
    try:
        ini = os.path.join(os.path.dirname(__file__), "jarvis.ini")
        p = configparser.ConfigParser()
        p.read(ini)
        if not p.has_section("hud"):
            p.add_section("hud")
        p.set("hud", "saved_x", str(x))
        p.set("hud", "saved_y", str(y))
        with open(ini, "w") as f:
            p.write(f)
    except Exception:
        pass


class JarvisHUD:
    """Floating animated orb. Must be instantiated and run on the main thread."""

    SIZE = 110  # Canvas + window size in pixels

    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)    # Borderless
        self.root.attributes("-topmost", True)
        self.root.config(bg="black")
        self.root.wm_attributes("-transparentcolor", "black")

        # Position — restore saved, or default top-right
        sx, sy = _load_saved_position()
        if sx < 0:
            sw = self.root.winfo_screenwidth()
            sx = sw - self.SIZE - 40
            sy = 40
        self.root.geometry(f"{self.SIZE}x{self.SIZE}+{sx}+{sy}")

        self.canvas = tk.Canvas(
            self.root,
            width=self.SIZE, height=self.SIZE,
            bg="black", highlightthickness=0
        )
        self.canvas.pack()

        # Three glow ring layers (drawn largest → smallest so core is on top)
        cx = cy = self.SIZE // 2
        self._rings = [
            self.canvas.create_oval(cx-44, cy-44, cx+44, cy+44, fill="", outline="#38bdf8", width=1),
            self.canvas.create_oval(cx-34, cy-34, cx+34, cy+34, fill="", outline="#0284c7", width=2),
            self.canvas.create_oval(cx-24, cy-24, cx+24, cy+24, fill="#0c1a2e", outline="#0369a1", width=2),
        ]

        # Animation state
        self.tick            = 0
        self._prev_state     = "idle"
        self._transition_t   = 1.0   # 0.0 = start of transition, 1.0 = settled
        self._transition_spd = 0.08  # fraction of transition completed per tick

        # Dragging
        self._drag_x = 0
        self._drag_y = 0
        self.canvas.bind("<ButtonPress-1>",   self._on_drag_start)
        self.canvas.bind("<B1-Motion>",        self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>",  self._on_drag_end)

        # Right-click kill switch
        self.canvas.bind("<Button-3>", lambda _: os._exit(0))

        # Kick off animation
        self.root.after(40, self._animate)   # ~25 fps

    # ── Drag handlers ─────────────────────────────────────────────────────────

    def _on_drag_start(self, event: tk.Event) -> None:
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _on_drag_motion(self, event: tk.Event) -> None:
        nx = event.x_root - self._drag_x
        ny = event.y_root - self._drag_y
        self.root.geometry(f"+{nx}+{ny}")

    def _on_drag_end(self, event: tk.Event) -> None:
        _save_position(self.root.winfo_x(), self.root.winfo_y())

    # ── Animation loop ────────────────────────────────────────────────────────

    def _animate(self) -> None:
        state = get_hud_state()
        self.tick += 1

        # Smooth state transition interpolation
        if state != self._prev_state:
            self._prev_state = state
            self._transition_t = 0.0
        self._transition_t = min(1.0, self._transition_t + self._transition_spd)
        t = self._transition_t

        palette = _STATE_PALETTE.get(state, _STATE_PALETTE["idle"])
        cx = cy = self.SIZE // 2

        # Sine-wave breathing with easing
        wave = math.sin(self.tick * palette["speed"])
        amp  = palette["amp"] * t   # Amplitude ramps in as transition settles

        # Layer sizes: outer → middle → core
        sizes = [44 + wave * amp, 34 + wave * amp * 0.7, 24 + wave * amp * 0.4]
        rings_colours = palette["rings"]   # outer, mid, core outline

        for i, (ring_id, sz, colour) in enumerate(zip(self._rings, sizes, rings_colours)):
            width = [1, 2, 2][i]
            fill  = palette["core"] if i == 2 else ""
            self.canvas.coords(ring_id, cx-sz, cy-sz, cx+sz, cy+sz)
            self.canvas.itemconfig(ring_id, outline=colour, fill=fill, width=width)

        self.root.after(40, self._animate)

    def run(self) -> None:
        self.root.mainloop()


def start_hud() -> None:
    """Start the HUD on the calling thread (must be the main thread)."""
    app = JarvisHUD()
    app.run()
