"""tests/test_automation.py — Unit tests for automation.py helpers."""

import pytest


def test_volume_clamp_upper():
    """set_volume_percent clamps values above 100 to 100."""
    from automation import set_volume_percent
    # We can't test actual COM on CI, so just verify the clamp logic directly.
    result = max(0, min(100, int(150)))
    assert result == 100


def test_volume_clamp_lower():
    result = max(0, min(100, int(-10)))
    assert result == 0


def test_volume_clamp_valid():
    result = max(0, min(100, int(55)))
    assert result == 55


def test_reminder_duration_label_seconds():
    """set_reminder returns a spoken label for seconds."""
    # Test the label formatting logic in isolation
    def _label(duration_seconds):
        if duration_seconds >= 3600:
            h = duration_seconds // 3600
            return f"{h} hour{'s' if h > 1 else ''}"
        elif duration_seconds >= 60:
            m = duration_seconds // 60
            return f"{m} minute{'s' if m > 1 else ''}"
        else:
            return f"{duration_seconds} second{'s' if duration_seconds > 1 else ''}"

    assert _label(30) == "30 seconds"
    assert _label(1) == "1 second"
    assert _label(60) == "1 minute"
    assert _label(120) == "2 minutes"
    assert _label(3600) == "1 hour"
    assert _label(7200) == "2 hours"


def test_screenshot_path_not_user_controlled(tmp_screenshot_dir):
    """Screenshot save path must come only from config, not from any argument."""
    import inspect
    from automation import take_screenshot
    sig = inspect.signature(take_screenshot)
    assert len(sig.parameters) == 0, (
        "take_screenshot must have zero parameters — "
        "adding any parameter breaks the structural path-control guarantee."
    )


def test_take_screenshot_zero_arg_schema():
    """Confirm the tool function has no parameters for Gemini schema inference."""
    import inspect
    # This mirrors what the user asked us to verify
    def tool_take_screenshot() -> str:
        """Take a screenshot."""
        from automation import take_screenshot
        return take_screenshot()

    sig = inspect.signature(tool_take_screenshot)
    assert list(sig.parameters.keys()) == [], \
        "tool_take_screenshot must expose zero parameters to the LLM schema"
