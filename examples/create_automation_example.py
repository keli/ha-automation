#!/usr/bin/env python3
"""
Example: Creating Home Assistant automations via API.

This demonstrates how to create automations programmatically using the
Home Assistant REST API through this toolkit.

User request (Chinese): "晚上10点后走廊有人移动就开灯，亮度30%"
User request (English): "Turn on hallway light at 30% brightness when motion detected after 10 PM"

AI understanding:
- Trigger: Motion sensor in hallway
- Condition: Time between 22:00 and 06:00
- Action: Turn on hallway light at 30% brightness
- Mode: Single (don't trigger again if already running)

IMPORTANT: This example uses create_or_update() for idempotent operations.
Running the script multiple times will update the same automation instead
of creating duplicates.
"""

import time
from ha_automation import HAClient, DeviceDiscovery, AutomationManager


def create_motion_light_automation():
    """
    Example: Create motion-activated light automation via API.

    This demonstrates the complete workflow:
    1. Initialize clients
    2. Discover available devices
    3. Search for specific devices
    4. Create automation configuration
    5. Create automation via API
    6. Verify creation
    """

    print("="*70)
    print("Creating Motion-Activated Light Automation")
    print("="*70)

    # Step 1: Initialize
    print("\n[Step 1] Initializing clients...")
    client = HAClient()  # Reads HA_URL and HA_TOKEN from .env
    discovery = DeviceDiscovery(client)
    manager = AutomationManager(client)
    print("✓ Clients initialized")

    # Step 2: Discover devices
    print("\n[Step 2] Discovering devices...")
    devices = discovery.discover_all()
    print(f"✓ Found {len(devices)} devices")

    # Step 3: Search for required devices
    print("\n[Step 3] Searching for hallway devices...")

    # Search for motion sensor (supports Chinese and English)
    motion_sensors = discovery.search("走廊 motion")
    if not motion_sensors:
        motion_sensors = discovery.search("hallway motion")

    if not motion_sensors:
        print("❌ Error: No hallway motion sensor found")
        print("\nAvailable motion sensors:")
        for sensor in discovery.get_motion_sensors():
            print(f"  - {sensor.friendly_name} ({sensor.entity_id})")
        return

    # Search for light
    lights = discovery.search("走廊 light")
    if not lights:
        lights = discovery.search("hallway light")

    if not lights:
        print("❌ Error: No hallway light found")
        print("\nAvailable lights:")
        for light in discovery.get_lights()[:10]:  # Show first 10
            print(f"  - {light.friendly_name} ({light.entity_id})")
        return

    motion_sensor = motion_sensors[0]
    light = lights[0]

    print(f"✓ Using motion sensor: {motion_sensor.friendly_name}")
    print(f"✓ Using light: {light.friendly_name}")

    # Step 4: Create automation configuration
    print("\n[Step 4] Creating automation configuration...")

    automation_config = {
        "id": "example_night_motion_light",  # ✅ Fixed ID - enables updates
        "alias": "夜间走廊照明",
        "description": "晚上10点后走廊有人移动就开灯，亮度30%",
        "trigger": [
            {
                "platform": "state",
                "entity_id": motion_sensor.entity_id,
                "to": "on"
            }
        ],
        "condition": [
            {
                "condition": "time",
                "after": "22:00:00",
                "before": "06:00:00"
            }
        ],
        "action": [
            {
                "service": "light.turn_on",
                "target": {
                    "entity_id": light.entity_id
                },
                "data": {
                    "brightness_pct": 30
                }
            }
        ],
        "mode": "single"
    }

    print(f"✓ Configuration created with ID: {automation_config['id']}")

    # Step 5: Create or update automation via API (idempotent)
    print("\n[Step 5] Creating/updating automation via API...")
    try:
        automation_id, was_created = manager.create_or_update(automation_config)
        action = "created" if was_created else "updated"
        print(f"✓ Automation {action}: {automation_id}")
    except Exception as e:
        print(f"❌ Failed to create/update automation: {e}")
        return

    # Step 6: Verify automation was created
    print("\n[Step 6] Verifying automation...")
    try:
        # Wait a moment for reload to complete
        time.sleep(2)

        auto = manager.get_automation(f"automation.{automation_id}")
        print(f"✓ Automation verified!")
        print(f"  Entity ID: {auto.entity_id}")
        print(f"  Name: {auto.friendly_name}")
        print(f"  State: {auto.state}")
        print(f"  Description: {auto.description or 'N/A'}")
    except Exception as e:
        print(f"⚠️  Could not verify immediately: {e}")
        print(f"  This is normal - the automation may take a moment to appear")

    print("\n" + "="*70)
    print("SUCCESS! Automation created successfully")
    print("="*70)
    print(f"\nYou can now:")
    print(f"  • View it in Home Assistant UI")
    print(f"  • Test it by triggering the motion sensor")
    print(f"  • Edit it via: ha-automation show automation.{automation_id}")
    print(f"  • Delete it via: manager.delete_automation('{automation_id}')")
    print("="*70)


def create_time_based_automation():
    """
    Example: Create time-based automation.

    User request: "每天晚上10点关闭所有灯"
    (Turn off all lights at 10 PM every day)
    """

    print("\n" + "="*70)
    print("Creating Time-Based Automation")
    print("="*70)

    # Initialize
    client = HAClient()
    discovery = DeviceDiscovery(client)
    manager = AutomationManager(client)

    # Get all lights
    print("\n[1] Finding all lights...")
    all_lights = discovery.get_lights()
    light_ids = [light.entity_id for light in all_lights]
    print(f"✓ Found {len(light_ids)} lights")

    # Create or update automation
    print("\n[2] Creating/updating automation...")
    config = {
        "id": "example_night_lights_off",  # ✅ Fixed ID
        "alias": "晚上关灯",
        "description": "每天晚上10点关闭所有灯",
        "trigger": [{
            "platform": "time",
            "at": "22:00:00"
        }],
        "action": [{
            "service": "light.turn_off",
            "target": {"entity_id": light_ids}
        }],
        "mode": "single"
    }

    try:
        automation_id, was_created = manager.create_or_update(config)
        action = "Created" if was_created else "Updated"
        print(f"✓ {action}: automation.{automation_id}")

        # Verify
        time.sleep(2)
        auto = manager.get_automation(f"automation.{automation_id}")
        print(f"✓ Verified: {auto.friendly_name}")

        print("\n" + "="*70)
        print("SUCCESS!")
        print("="*70)

    except Exception as e:
        print(f"❌ Error: {e}")


def create_temperature_automation():
    """
    Example: Create temperature-based automation.

    User request: "温度超过26度就把空调设到24度"
    (Set AC to 24°C when temperature exceeds 26°C)
    """

    print("\n" + "="*70)
    print("Creating Temperature-Based Automation")
    print("="*70)

    # Initialize
    client = HAClient()
    discovery = DeviceDiscovery(client)
    manager = AutomationManager(client)

    # Find devices
    print("\n[1] Finding temperature sensor and climate device...")
    temp_sensors = discovery.get_temperature_sensors()
    climate_devices = discovery.get_by_domain('climate')

    if not temp_sensors:
        print("❌ No temperature sensors found")
        return

    if not climate_devices:
        print("❌ No climate devices found")
        return

    temp_sensor = temp_sensors[0]
    climate = climate_devices[0]

    print(f"✓ Using sensor: {temp_sensor.friendly_name}")
    print(f"✓ Using climate: {climate.friendly_name}")

    # Create or update automation
    print("\n[2] Creating/updating automation...")
    config = {
        "id": "example_auto_cooling",  # ✅ Fixed ID
        "alias": "自动降温",
        "description": "温度超过26度就把空调设到24度",
        "trigger": [{
            "platform": "numeric_state",
            "entity_id": temp_sensor.entity_id,
            "above": 26
        }],
        "action": [{
            "service": "climate.set_temperature",
            "target": {"entity_id": climate.entity_id},
            "data": {"temperature": 24}
        }],
        "mode": "single"
    }

    try:
        automation_id, was_created = manager.create_or_update(config)
        action = "Created" if was_created else "Updated"
        print(f"✓ {action}: automation.{automation_id}")

        # Verify
        time.sleep(2)
        auto = manager.get_automation(f"automation.{automation_id}")
        print(f"✓ Verified: {auto.friendly_name}")

        print("\n" + "="*70)
        print("SUCCESS!")
        print("="*70)

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n🤖 Home Assistant Automation API Examples\n")

    # Example 1: Motion-activated light
    create_motion_light_automation()

    # Uncomment to run other examples:
    # create_time_based_automation()
    # create_temperature_automation()

    print("\n✨ Done! Check your Home Assistant to see the new automation.\n")
