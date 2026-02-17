"""Device discovery and search for Home Assistant."""

from typing import List, Optional
import json
from pathlib import Path
from .client import HAClient
from .models import Device


class DeviceDiscovery:
    """Discover and search Home Assistant devices."""

    def __init__(self, client: HAClient, cache_file: str = "device_cache.json"):
        """
        Initialize DeviceDiscovery.

        Args:
            client: HAClient instance
            cache_file: Path to cache file for storing discovered devices
        """
        self.client = client
        self.cache_file = Path(cache_file)
        self.devices: List[Device] = []

    def discover_all(self, force_refresh: bool = False) -> List[Device]:
        """
        Discover all devices from Home Assistant and cache them.

        Args:
            force_refresh: If True, ignore cache and fetch from HA

        Returns:
            List of Device objects

        Raises:
            RuntimeError: If cache not found and cannot fetch from HA
        """
        # Load from cache if it exists and refresh not forced
        if not force_refresh and self.cache_file.exists():
            self._load_cache()
            if self.devices:
                return self.devices

        # Cache not found or refresh forced - fetch from Home Assistant
        if not force_refresh and not self.cache_file.exists():
            raise RuntimeError(
                f"Device cache not found at {self.cache_file.absolute()}. "
                f"Please run 'ha-automation discover' first to create the cache."
            )

        # Fetch all states from Home Assistant
        try:
            all_states = self.client.get_states()
            self.devices = [Device.from_ha_state(state) for state in all_states]
            self._save_cache()
            return self.devices
        except Exception as e:
            raise RuntimeError(f"Failed to discover devices from Home Assistant: {e}")

    def search(self, query: str) -> List[Device]:
        """
        Search devices by name or entity_id.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching Device objects
        """
        if not self.devices:
            self.discover_all()

        query_lower = query.lower()
        return [
            device for device in self.devices
            if query_lower in device.friendly_name.lower()
            or query_lower in device.entity_id.lower()
        ]

    def get_by_domain(self, domain: str) -> List[Device]:
        """
        Get all devices of a specific domain.

        Args:
            domain: Domain name (e.g., 'light', 'sensor', 'switch')

        Returns:
            List of Device objects in that domain
        """
        if not self.devices:
            self.discover_all()

        return [device for device in self.devices if device.domain == domain]

    def get_lights(self) -> List[Device]:
        """
        Get all light devices.

        Returns:
            List of light Device objects
        """
        return self.get_by_domain('light')

    def get_switches(self) -> List[Device]:
        """
        Get all switch devices.

        Returns:
            List of switch Device objects
        """
        return self.get_by_domain('switch')

    def get_sensors(self) -> List[Device]:
        """
        Get all sensor devices.

        Returns:
            List of sensor Device objects
        """
        return self.get_by_domain('sensor')

    def get_binary_sensors(self) -> List[Device]:
        """
        Get all binary sensor devices.

        Returns:
            List of binary_sensor Device objects
        """
        return self.get_by_domain('binary_sensor')

    def get_motion_sensors(self) -> List[Device]:
        """
        Get all motion sensors.

        Returns:
            List of motion sensor Device objects
        """
        if not self.devices:
            self.discover_all()

        return [
            device for device in self.devices
            if device.domain == 'binary_sensor' and device.device_class == 'motion'
        ]

    def get_door_sensors(self) -> List[Device]:
        """
        Get all door/window sensors.

        Returns:
            List of door sensor Device objects
        """
        if not self.devices:
            self.discover_all()

        return [
            device for device in self.devices
            if device.domain == 'binary_sensor' and device.device_class in ['door', 'window', 'opening']
        ]

    def get_temperature_sensors(self) -> List[Device]:
        """
        Get all temperature sensors.

        Returns:
            List of temperature sensor Device objects
        """
        if not self.devices:
            self.discover_all()

        return [
            device for device in self.devices
            if device.domain == 'sensor' and device.device_class == 'temperature'
        ]

    def get_by_area(self, area: str) -> List[Device]:
        """
        Get all devices in a specific area.

        Args:
            area: Area name (case-insensitive)

        Returns:
            List of Device objects in that area
        """
        if not self.devices:
            self.discover_all()

        area_lower = area.lower()
        return [
            device for device in self.devices
            if device.area and area_lower in device.area.lower()
        ]

    def _save_cache(self):
        """Save discovered devices to JSON cache file."""
        try:
            data = [device.model_dump() for device in self.devices]
            self.cache_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            # Don't fail if caching fails, just warn
            print(f"Warning: Failed to save device cache: {e}")

    def _load_cache(self):
        """Load devices from JSON cache file."""
        try:
            data = json.loads(self.cache_file.read_text())
            self.devices = [Device(**device_dict) for device_dict in data]
        except Exception as e:
            # If cache loading fails, we'll just fetch fresh data
            print(f"Warning: Failed to load device cache: {e}")
            self.devices = []
