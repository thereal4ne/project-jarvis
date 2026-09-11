"""tests/test_memory.py — Unit tests for memory.py (persistent preferences)."""

import json
import pytest


def test_save_and_load(tmp_memory):
    import memory
    result = memory.save_preference("name", "Albin")
    assert "Albin" in result

    prefs = memory.load_preferences()
    assert prefs["name"] == "Albin"


def test_save_normalises_key_to_lowercase(tmp_memory):
    import memory
    memory.save_preference("PREFERRED VOLUME", "50%")
    prefs = memory.load_preferences()
    assert "preferred volume" in prefs


def test_forget_existing_key(tmp_memory):
    import memory
    memory.save_preference("wake time", "7am")
    result = memory.forget_preference("wake time")
    assert "7am" in result or "wake time" in result
    prefs = memory.load_preferences()
    assert "wake time" not in prefs


def test_forget_nonexistent_key(tmp_memory):
    import memory
    result = memory.forget_preference("nonexistent")
    assert "nonexistent" in result


def test_empty_preferences_summary(tmp_memory):
    import memory
    summary = memory.get_preferences_summary()
    assert summary == ""


def test_preferences_summary_format(tmp_memory):
    import memory
    memory.save_preference("name", "Albin")
    summary = memory.get_preferences_summary()
    assert "name" in summary
    assert "Albin" in summary


def test_corrupt_json_returns_empty(tmp_memory):
    """A corrupt memory.json should return {} gracefully, not crash."""
    import memory
    with open(tmp_memory, "w") as f:
        f.write("this is not valid json{{{{")
    prefs = memory.load_preferences()
    assert prefs == {}


def test_overwrite_existing_key(tmp_memory):
    import memory
    memory.save_preference("name", "Old")
    memory.save_preference("name", "Albin")
    prefs = memory.load_preferences()
    assert prefs["name"] == "Albin"
