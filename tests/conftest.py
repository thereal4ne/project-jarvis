"""
tests/conftest.py — Shared pytest fixtures for Jarvis unit tests.

Rules:
  - No real API calls. All LLM/network interactions are mocked.
  - .env is never read. Tests are fully self-contained.
  - Temporary files (memory.json, screenshots) use pytest's tmp_path fixture.
"""

import os
import sys
import json
import pytest

# Ensure project root is on the path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def tmp_memory(tmp_path, monkeypatch):
    """Redirect memory.json to a temp directory for test isolation."""
    import memory
    fake_path = str(tmp_path / "memory.json")
    monkeypatch.setattr(memory, "MEMORY_FILE", fake_path)
    yield fake_path


@pytest.fixture
def tmp_screenshot_dir(tmp_path, monkeypatch):
    """Redirect screenshot save folder to a temp directory."""
    import config
    from config import JarvisConfig, ScreenshotConfig
    # Patch only the screenshot save_folder
    fake_cfg = config.JarvisConfig(
        screenshot=ScreenshotConfig(save_folder=str(tmp_path))
    )
    monkeypatch.setattr(config, "cfg", fake_cfg)
    yield tmp_path
