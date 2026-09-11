"""
boot_animation.py — Cinematic full-screen boot animation for Jarvis.

Layers (rendered back to front):
  1. Background particle network — atoms/nodes connected by glowing lines
  2. Rotating 3D wireframe planet — latitude/longitude lines in 3D projection
  3. Horizontal scanning line sweeping the full screen
  4. Typewriter boot-sequence text
  5. Progress bar at bottom

Pure tkinter Canvas — no extra dependencies.
Duration: ~5 seconds. Press Space or Esc to skip.

Enable/disable via jarvis.ini:
    [hud]
    boot_animation = true
"""

from __future__ import annotations

import math
import random
import time
import tkinter as tk
from typing import List, Tuple


# ── Colour palette ─────────────────────────────────────────────────────────────
BG          = "#010a12"         # Near-black teal
PRIMARY     = "#00d4ff"         # Bright cyan
DIM         = "#003850"         # Dark cyan (far lines, grid)
GLOW1       = "#004060"         # Glow ring 1
GLOW2       = "#002030"         # Glow ring 2
PARTICLE    = "#00ffff"         # Node bright
TEXT_MAIN   = "#00d4ff"         # Boot sequence text
TITLE       = "#ffffff"         # J.A.R.V.I.S title
SUBTITLE    = "#005070"         # Subtitle dim
SCAN        = "#004466"         # Scan line
SPHERE_NEAR = "#00d4ff"         # Sphere lines facing camera
SPHERE_FAR  = "#002840"         # Sphere lines facing away

DURATION    = 5.2               # Seconds before auto-close
FPS_TARGET  = 30                # Target frame rate
FRAME_MS    = 1000 // FPS_TARGET


# ── Boot text sequence ─────────────────────────────────────────────────────────
# (elapsed_seconds_to_appear, text)
BOOT_SEQUENCE: List[Tuple[float, str]] = [
    (0.6,  "NEURAL NETWORK ............. [ONLINE]"),
    (1.3,  "VOICE RECOGNITION .......... [ACTIVE]"),
    (2.0,  "THREAT ANALYSIS ............ [CLEAR]"),
    (2.7,  "MEMORY CORE ................ [LOADED]"),
    (3.4,  "ALL SYSTEMS OPERATIONAL"),
]


# ── 3D wireframe sphere ────────────────────────────────────────────────────────

def _sphere_point(
    lat_deg: float,
    lon_deg: float,
    rot_deg: float,
    radius: float,
    cx: float,
    cy: float,
) -> Tuple[float, float, float]:
    """Project a lat/lon sphere point to 2D screen space.

    Returns (screen_x, screen_y, z_world) where z_world > 0 = facing camera.
    Uses a simple perspective projection with a fixed focal length.
    """
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg + rot_deg)

    # 3D Cartesian on unit sphere
    x3 = math.cos(lat) * math.cos(lon)
    y3 = math.sin(lat)
    z3 = math.cos(lat) * math.sin(lon)

    # Perspective projection (focal = 4× radius)
    focal   = radius * 4.0
    z_shift = focal + z3 * radius
    scale   = focal / max(z_shift, 1)

    sx = cx + x3 * radius * scale
    sy = cy + y3 * radius * scale
    return sx, sy, z3


def _lerp_color(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex colours."""
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ── Main animation class ───────────────────────────────────────────────────────

class BootAnimation:

    PARTICLE_COUNT = 55
    MAX_LINK_DIST  = 160     # Max distance to draw a line between particles

    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=BG)
        self.root.title("JARVIS")

        self.W  = self.root.winfo_screenwidth()
        self.H  = self.root.winfo_screenheight()
        self.cx = self.W / 2
        self.cy = self.H / 2

        self.canvas = tk.Canvas(
            self.root,
            width=self.W, height=self.H,
            bg=BG, highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Particles: [x, y, vx, vy]
        self.particles: List[List[float]] = [
            [
                random.uniform(50, self.W - 50),
                random.uniform(50, self.H - 50),
                random.uniform(-0.6, 0.6),
                random.uniform(-0.6, 0.6),
            ]
            for _ in range(self.PARTICLE_COUNT)
        ]

        # Pre-compute sphere wireframe point sets (lat/lon every 20°)
        # We only store (lat, lon) — actual screen coords computed per frame with rotation
        self.sphere_r   = min(self.W, self.H) * 0.18
        self.lat_lines  = list(range(-80, 81, 20))     # 9 latitude circles
        self.lon_lines  = list(range(0, 360, 20))      # 18 longitude circles
        self.seg_steps  = 72                           # Points per circle

        self.rotation   = 0.0     # Degrees, incremented per frame
        self.rot_speed  = 0.4     # Degrees per frame
        self.scan_y     = 0.0
        self.start_time = time.time()
        self.tick       = 0

        # Key bindings to skip
        self.root.bind("<Escape>", lambda _: self._close())
        self.root.bind("<space>",  lambda _: self._close())

        self.root.after(FRAME_MS, self._frame)

    # ── Per-frame rendering ────────────────────────────────────────────────────

    def _frame(self) -> None:
        elapsed = time.time() - self.start_time
        if elapsed >= DURATION:
            self._close()
            return

        self.tick      += 1
        self.rotation  += self.rot_speed
        self.scan_y     = (self.scan_y + 4) % self.H

        c = self.canvas
        c.delete("all")

        self._draw_particles(c)
        self._draw_sphere(c)
        self._draw_scan_line(c)
        self._draw_ui(c, elapsed)

        self.root.after(FRAME_MS, self._frame)

    # ── Layer 1: Particle network ──────────────────────────────────────────────

    def _draw_particles(self, c: tk.Canvas) -> None:
        pts = self.particles

        # Update positions
        for p in pts:
            p[0] += p[2]
            p[1] += p[3]
            if p[0] < 0 or p[0] > self.W: p[2] *= -1; p[0] = max(0, min(self.W, p[0]))
            if p[1] < 0 or p[1] > self.H: p[3] *= -1; p[1] = max(0, min(self.H, p[1]))

        # Draw connecting lines
        n = len(pts)
        for i in range(n):
            for j in range(i + 1, n):
                dx = pts[i][0] - pts[j][0]
                dy = pts[i][1] - pts[j][1]
                d  = math.hypot(dx, dy)
                if d < self.MAX_LINK_DIST:
                    t     = 1.0 - d / self.MAX_LINK_DIST
                    color = _lerp_color(DIM, PRIMARY, t * 0.6)
                    c.create_line(pts[i][0], pts[i][1], pts[j][0], pts[j][1],
                                  fill=color, width=1)

        # Draw nodes with 2-layer glow
        for p in pts:
            x, y = p[0], p[1]
            c.create_oval(x - 5, y - 5, x + 5, y + 5, fill=GLOW1,    outline="")
            c.create_oval(x - 2, y - 2, x + 2, y + 2, fill=PARTICLE,  outline="")

    # ── Layer 2: Rotating 3D wireframe sphere ──────────────────────────────────

    def _draw_sphere(self, c: tk.Canvas) -> None:
        cx, cy   = self.cx, self.cy
        r        = self.sphere_r
        rot      = self.rotation
        steps    = self.seg_steps

        # ── Latitude circles ──
        for lat in self.lat_lines:
            prev = None
            for si in range(steps + 1):
                lon = (si / steps) * 360
                sx, sy, z3 = _sphere_point(lat, lon, rot, r, cx, cy)
                if prev is not None:
                    # Colour by depth: bright if facing camera, dark if behind
                    depth = (z3 + 1) / 2   # 0..1
                    color = _lerp_color(SPHERE_FAR, SPHERE_NEAR, depth)
                    # Don't draw lines crossing behind the sphere
                    if abs(prev[2] - z3) < 0.5:
                        c.create_line(prev[0], prev[1], sx, sy,
                                      fill=color, width=1)
                prev = (sx, sy, z3)

        # ── Longitude circles ──
        for lon_base in self.lon_lines:
            prev = None
            for si in range(steps // 2 + 1):
                lat = -90 + si * (180 / (steps // 2))
                sx, sy, z3 = _sphere_point(lat, lon_base, rot, r, cx, cy)
                if prev is not None:
                    depth = (z3 + 1) / 2
                    color = _lerp_color(SPHERE_FAR, SPHERE_NEAR, depth)
                    if abs(prev[2] - z3) < 0.5:
                        c.create_line(prev[0], prev[1], sx, sy,
                                      fill=color, width=1)
                prev = (sx, sy, z3)

        # ── Pulsing bright equator ──
        pulse = 0.5 + 0.5 * math.sin(self.tick * 0.08)
        eq_color = _lerp_color(PRIMARY, "#ffffff", pulse * 0.4)
        prev = None
        for si in range(steps + 1):
            lon = (si / steps) * 360
            sx, sy, z3 = _sphere_point(0, lon, rot, r, cx, cy)
            if prev is not None and (z3 + prev[2]) > -0.2:
                c.create_line(prev[0], prev[1], sx, sy,
                              fill=eq_color, width=2)
            prev = (sx, sy, z3)

        # ── Centre glow behind sphere ──
        gr = r * 0.35
        c.create_oval(cx - gr, cy - gr, cx + gr, cy + gr, fill=GLOW2, outline="")
        gr2 = r * 0.15
        c.create_oval(cx - gr2, cy - gr2, cx + gr2, cy + gr2, fill=GLOW1, outline="")

    # ── Layer 3: Scanning line ─────────────────────────────────────────────────

    def _draw_scan_line(self, c: tk.Canvas) -> None:
        sy = self.scan_y
        c.create_line(0, sy, self.W, sy, fill=SCAN, width=2)
        for dy in range(1, 6):
            fade = _lerp_color(BG, SCAN, max(0, 1 - dy * 0.22))
            if sy - dy >= 0:
                c.create_line(0, sy - dy, self.W, sy - dy, fill=fade, width=1)
            if sy + dy < self.H:
                c.create_line(0, sy + dy, self.W, sy + dy, fill=fade, width=1)

    # ── Layer 4+5: UI / text overlay ──────────────────────────────────────────

    def _draw_ui(self, c: tk.Canvas, elapsed: float) -> None:
        cx  = self.cx
        cy  = self.cy
        r   = self.sphere_r

        # ── Title above the sphere ──
        title_y = cy - r - 55
        c.create_text(cx, title_y,
                      text="J.A.R.V.I.S",
                      font=("Courier", 48, "bold"),
                      fill=TITLE)
        c.create_text(cx, title_y + 38,
                      text="JUST A RATHER VERY INTELLIGENT SYSTEM",
                      font=("Courier", 11),
                      fill=SUBTITLE)

        # Horizontal separator lines flanking title
        sep_y = title_y + 55
        c.create_line(cx - 260, sep_y, cx + 260, sep_y, fill=DIM, width=1)

        # ── Boot sequence text below the sphere ──
        text_start_y = cy + r + 30
        for i, (trigger, msg) in enumerate(BOOT_SEQUENCE):
            if elapsed >= trigger:
                # Last item gets bright colour
                colour = TITLE if i == len(BOOT_SEQUENCE) - 1 else TEXT_MAIN
                c.create_text(cx, text_start_y + i * 22,
                              text=msg,
                              font=("Courier", 12),
                              fill=colour)

        # ── Corner brackets (decorative HUD corners) ──
        self._draw_corners(c)

        # ── Progress bar at very bottom ──
        progress = min(1.0, elapsed / DURATION)
        bw, bh   = 500, 3
        bx       = cx - bw // 2
        by       = self.H - 50
        c.create_rectangle(bx, by, bx + bw, by + bh,
                           fill=DIM, outline=DIM)
        fill_w = int(bw * progress)
        if fill_w > 0:
            c.create_rectangle(bx, by, bx + fill_w, by + bh,
                               fill=PRIMARY, outline="")
        c.create_text(cx, by + 18,
                      text="SPACE / ESC to skip",
                      font=("Courier", 9),
                      fill="#002030")

    def _draw_corners(self, c: tk.Canvas) -> None:
        """Draw HUD-style bracket corners at screen edges."""
        m = 40    # Margin from edge
        s = 30    # Bracket arm length
        col = DIM

        corners = [
            # Top-left
            [(m, m + s, m, m), (m, m, m + s, m)],
            # Top-right
            [(self.W - m, self.H - m - s, self.W - m, self.H - m),
             (self.W - m, self.H - m, self.W - m - s, self.H - m)],
            # Bottom-left
            [(m, m + s, m, m), (m, m, m + s, m)],
            # Bottom-right
            [(self.W - m, m + s, self.W - m, m),
             (self.W - m, m, self.W - m - s, m)],
        ]

        # Top-left
        c.create_line(m, m, m + s, m, fill=col, width=2)
        c.create_line(m, m, m, m + s, fill=col, width=2)
        # Top-right
        c.create_line(self.W - m, m, self.W - m - s, m, fill=col, width=2)
        c.create_line(self.W - m, m, self.W - m, m + s, fill=col, width=2)
        # Bottom-left
        c.create_line(m, self.H - m, m + s, self.H - m, fill=col, width=2)
        c.create_line(m, self.H - m, m, self.H - m - s, fill=col, width=2)
        # Bottom-right
        c.create_line(self.W - m, self.H - m, self.W - m - s, self.H - m, fill=col, width=2)
        c.create_line(self.W - m, self.H - m, self.W - m, self.H - m - s, fill=col, width=2)

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def _close(self) -> None:
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self) -> None:
        self.root.mainloop()


# ── Public entry point ─────────────────────────────────────────────────────────

def play_boot_animation() -> None:
    """Play the full-screen boot animation synchronously.

    Blocks until the animation finishes or the user presses Space/Esc.
    If anything fails, silently passes so Jarvis still starts normally.
    """
    try:
        anim = BootAnimation()
        anim.run()
    except Exception:
        pass   # Never let a cosmetic feature break startup
