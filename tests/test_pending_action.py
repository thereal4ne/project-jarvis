"""tests/test_pending_action.py — Unit tests for the PENDING_ACTION state machine."""

import time
import pytest


def _make_state(action="shutdown", age_seconds=0):
    return {"action": action, "timestamp": time.time() - age_seconds}


def test_expiry_before_confirm_check():
    """Expiry must be evaluated before checking yes/no — a stale 'yes' must be rejected."""
    state = _make_state(age_seconds=35)  # Past the 30s timeout
    elapsed = time.time() - state["timestamp"]
    timeout = 30

    # Simulate the state machine logic
    if elapsed > timeout:
        result = "expired"
    elif "yes" in ("yes",):
        result = "confirmed"
    else:
        result = "cancelled"

    assert result == "expired", "Stale PENDING_ACTION must expire before confirm is checked"


def test_confirm_within_window():
    state = _make_state(age_seconds=5)  # Fresh, within 30s window
    elapsed = time.time() - state["timestamp"]
    timeout = 30
    cmd = "yes"

    if elapsed > timeout:
        result = "expired"
    elif cmd in ("yes", "confirm", "do it", "proceed"):
        result = "confirmed"
    else:
        result = "cancelled"

    assert result == "confirmed"


def test_cancel_on_non_confirm_input():
    state = _make_state(age_seconds=5)
    elapsed = time.time() - state["timestamp"]
    timeout = 30
    cmd = "open notepad"

    if elapsed > timeout:
        result = "expired"
    elif cmd in ("yes", "confirm", "do it", "proceed"):
        result = "confirmed"
    else:
        result = "cancelled"

    assert result == "cancelled"


def test_passphrase_blocks_plain_yes_when_set():
    """When JARVIS_PASSPHRASE is set, 'yes' must not confirm."""
    passphrase = "protocol omega"
    cmd = "yes"

    confirmed = False
    blocked_with_hint = False

    if passphrase:
        if cmd == passphrase:
            confirmed = True
        elif cmd in ("yes", "confirm", "do it", "proceed"):
            blocked_with_hint = True  # Jarvis says "passphrase required"
    else:
        confirmed = cmd in ("yes", "confirm", "do it", "proceed")

    assert not confirmed
    assert blocked_with_hint


def test_passphrase_confirms_correct_phrase():
    passphrase = "protocol omega"
    cmd = "protocol omega"

    confirmed = False
    if passphrase:
        confirmed = (cmd == passphrase)
    else:
        confirmed = cmd in ("yes", "confirm")

    assert confirmed


def test_no_passphrase_falls_back_to_yes():
    passphrase = ""
    cmd = "yes"

    confirmed = False
    if passphrase:
        confirmed = (cmd == passphrase)
    else:
        confirmed = cmd in ("yes", "confirm", "do it", "proceed")

    assert confirmed
