#!/usr/bin/env python3
"""
Example automation script.

Describe what this automation does here, then ask Claude Code to help you
customize it for your specific devices and needs.

Run with:
    ha-automation run example_automation.py
    # or sync all scripts:
    ha-automation sync
"""

from ha_automation import HAClient, DeviceDiscovery, AutomationManager

client = HAClient()
discovery = DeviceDiscovery(client)
manager = AutomationManager(client)

# Discover devices (uses cache after first run)
discovery.discover_all()

# Find your devices - search by name (supports Chinese and English)
# lights = discovery.search("living room light")
# sensors = discovery.search("走廊 motion")
# switches = discovery.get_by_domain("switch")

# Build your automation config
config = {
    "id": "my_example_automation",   # Fixed ID - rerunning updates instead of duplicating
    "alias": "My Example Automation",
    "description": "Replace this with your automation description",
    "trigger": [
        {
            "platform": "time",
            "at": "22:00:00"
        }
    ],
    "condition": [],
    "action": [
        # Add your actions here, for example:
        # {"service": "light.turn_off", "target": {"entity_id": "light.living_room"}}
    ],
    "mode": "single"
}

automation_id, was_created = manager.create_or_update(config)
print(f"{'Created' if was_created else 'Updated'}: automation.{automation_id}")
