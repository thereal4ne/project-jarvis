from plugin_manager import jarvis_tool
from automation import launch_app_or_resource

@jarvis_tool
def tool_launch_app(target_name: str) -> str:
    """Launch a Windows application, file, or website by name.
    Args:
        target_name: The name of the app to launch (e.g. 'spotify', 'chrome').
    """
    success, msg = launch_app_or_resource(target_name)
    return msg
