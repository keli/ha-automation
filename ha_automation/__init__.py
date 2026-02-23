"""Home Assistant Automation Management Library."""

from .client import HAClient
from .automation_manager import AutomationManager
from .device_discovery import DeviceDiscovery
from .models import AutomationState, AutomationConfig, AutomationInfo, Device

try:
    from importlib.metadata import version
    __version__ = version("ha-automation")
except Exception:
    __version__ = "unknown"
__all__ = [
    "HAClient",
    "AutomationManager",
    "DeviceDiscovery",
    "AutomationState",
    "AutomationConfig",
    "AutomationInfo",
    "Device",
]
