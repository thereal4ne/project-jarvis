import os
import glob
import importlib
import sys
from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger("JarvisPluginManager")

_TOOL_REGISTRY: Dict[str, Callable] = {}

def jarvis_tool(func: Callable) -> Callable:
    """
    Decorator to register a function as a Jarvis LLM tool.
    The function must have type hints and a Google-style or standard docstring,
    as it will be fed directly to the Gemini function-calling API.
    """
    _TOOL_REGISTRY[func.__name__] = func
    return func

def load_plugins() -> None:
    """
    Dynamically loads all .py files in the plugins/ directory,
    triggering their @jarvis_tool decorators.
    """
    plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
    if not os.path.exists(plugin_dir):
        return

    # Add the root project directory to sys.path if not there so plugins can import core modules
    root_dir = os.path.dirname(__file__)
    if root_dir not in sys.path:
        sys.path.append(root_dir)

    for file in glob.glob(os.path.join(plugin_dir, "*.py")):
        if os.path.basename(file).startswith("__"):
            continue
        
        module_name = f"plugins.{os.path.basename(file)[:-3]}"
        try:
            importlib.import_module(module_name)
            logger.info(f"Loaded plugin module: {module_name}")
        except Exception as e:
            logger.error(f"Failed to load plugin {module_name}: {e}")

def get_all_tools() -> List[Callable]:
    """Returns the list of all registered tool functions."""
    return list(_TOOL_REGISTRY.values())

def get_tool_map() -> Dict[str, Callable]:
    """Returns a dictionary mapping tool names to their callable functions."""
    return _TOOL_REGISTRY
