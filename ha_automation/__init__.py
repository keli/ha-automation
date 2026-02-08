"""Home Assistant Automation Management Library."""

from .client import HAClient
from .automation_manager import AutomationManager
from .device_discovery import DeviceDiscovery
from .models import AutomationState, AutomationConfig, AutomationInfo, Device

__version__ = "1.0.0"
__all__ = [
    "HAClient",
    "AutomationManager",
    "DeviceDiscovery",
    "AutomationState",
    "AutomationConfig",
    "AutomationInfo",
    "Device",
]
