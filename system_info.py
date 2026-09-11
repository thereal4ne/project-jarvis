"""
system_info.py — Local system stats and process management for Jarvis.

Design principles:
  - All queries are local-only via psutil. Zero network, zero LLM.
  - Process kill requires explicit name matching (no wildcard/fuzzy kill).
  - is_process_running() and get_*() are safe read-only calls.
  - kill_process() is intentionally NOT exposed as an LLM tool — Fast Path only.
    The LLM cannot be prompted into killing arbitrary processes.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("Jarvis")


# ── Read-only system stats ────────────────────────────────────────────────────

def get_ram_usage() -> str:
    """Returns a spoken summary of current RAM usage."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        used_gb  = mem.used  / (1024 ** 3)
        total_gb = mem.total / (1024 ** 3)
        pct      = mem.percent
        logger.info(f"SYSINFO: RAM {pct:.0f}%")
        return (
            f"RAM is at {pct:.0f} percent — "
            f"{used_gb:.1f} of {total_gb:.1f} gigabytes used."
        )
    except Exception as e:
        logger.error(f"get_ram_usage failed: {e}")
        return "Sorry, I couldn't read memory stats."


def get_cpu_usage() -> str:
    """Returns a spoken summary of current CPU usage (0.5s sample)."""
    try:
        import psutil
        pct   = psutil.cpu_percent(interval=0.5)
        cores = psutil.cpu_count(logical=True)
        freq  = psutil.cpu_freq()
        freq_str = f" at {freq.current / 1000:.1f} GHz" if freq else ""
        logger.info(f"SYSINFO: CPU {pct:.0f}%")
        return f"CPU is at {pct:.0f} percent across {cores} logical cores{freq_str}."
    except Exception as e:
        logger.error(f"get_cpu_usage failed: {e}")
        return "Sorry, I couldn't read CPU stats."


def get_disk_usage(path: str = "C:\\") -> str:
    """Returns a spoken summary of disk usage for the given drive."""
    try:
        import psutil
        disk      = psutil.disk_usage(path)
        free_gb   = disk.free  / (1024 ** 3)
        total_gb  = disk.total / (1024 ** 3)
        used_pct  = disk.percent
        logger.info(f"SYSINFO: Disk {path} {used_pct:.0f}%")
        return (
            f"Drive C has {free_gb:.0f} gigabytes free out of "
            f"{total_gb:.0f} gigabytes total — {used_pct:.0f} percent used."
        )
    except Exception as e:
        logger.error(f"get_disk_usage failed: {e}")
        return "Sorry, I couldn't read disk stats."


def get_battery() -> str:
    """Returns a spoken battery status, or a message if no battery is detected."""
    try:
        import psutil
        batt = psutil.sensors_battery()
        if batt is None:
            return "No battery detected — running on mains power."
        pct      = batt.percent
        plugged  = batt.power_plugged
        status   = "plugged in and charging" if plugged else "on battery"
        secs_left = batt.secsleft
        if not plugged and secs_left and secs_left > 0:
            h, m = divmod(secs_left // 60, 60)
            time_str = f", roughly {h}h {m}m remaining" if h else f", roughly {m} minutes remaining"
        else:
            time_str = ""
        logger.info(f"SYSINFO: Battery {pct:.0f}% {status}")
        return f"Battery is at {pct:.0f} percent, {status}{time_str}."
    except Exception as e:
        logger.error(f"get_battery failed: {e}")
        return "Sorry, I couldn't read battery status."


def get_full_system_summary() -> str:
    """Returns a combined spoken summary of RAM, CPU, and battery."""
    parts = [get_cpu_usage(), get_ram_usage(), get_battery()]
    return " ".join(parts)


# ── Process management ────────────────────────────────────────────────────────

def _find_processes(name: str) -> list:
    """Return a list of psutil.Process objects whose name fuzzy-matches `name`.

    Matching rules:
      - Case-insensitive
      - The query must be a substring of the process name (not the other way)
      - .exe suffix is stripped for comparison
    """
    import psutil
    name_lower = name.strip().lower().replace(".exe", "")
    matches = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            proc_name = (proc.info["name"] or "").lower().replace(".exe", "")
            if name_lower in proc_name:
                matches.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return matches


def is_process_running(name: str) -> str:
    """Check whether a named process is currently running."""
    matches = _find_processes(name)
    if matches:
        pids = ", ".join(str(p.pid) for p in matches[:3])
        count = len(matches)
        noun = "instance" if count == 1 else "instances"
        logger.info(f"SYSINFO: is_process_running('{name}') -> {count} found")
        return f"Yes, {name} is running — {count} {noun} found (PID {pids})."
    logger.info(f"SYSINFO: is_process_running('{name}') -> not found")
    return f"No, {name} doesn't appear to be running."


def kill_process(name: str) -> str:
    """Terminate all processes matching `name`.

    SECURITY: This is intentionally NOT registered as an LLM tool.
    It is called only from the PENDING_ACTION confirmation path in jarvis.py,
    which requires explicit user confirmation before calling this function.
    """
    import psutil
    matches = _find_processes(name)
    if not matches:
        return f"No process matching {name} is running."

    killed, failed = 0, 0
    for proc in matches:
        try:
            proc.terminate()
            killed += 1
            logger.info(f"SYSINFO: killed PID {proc.pid} ({proc.info.get('name', '?')})")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"SYSINFO: could not kill PID {proc.pid}: {e}")
            failed += 1

    if failed:
        return f"Killed {killed} instance(s) of {name}, but {failed} couldn't be terminated — access denied."
    return f"Done. Terminated {killed} instance(s) of {name}."
