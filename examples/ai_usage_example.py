#!/usr/bin/env python3
"""
Example: Creating automation from natural language using this toolkit.

This demonstrates how an AI assistant (like Claude Code) would use the toolkit
to create automations based on user's natural language descriptions.

User request (Chinese): "晚上10点后走廊有人移动就开灯，亮度30%"
User request (English): "Turn on hallway light at 30% brightness when motion detected after 10 PM"

AI understanding:
- Trigger: Motion sensor in hallway
- Condition: Time between 22:00 and 06:00
- Action: Turn on hallway light at 30% brightness
- Mode: Single (don't trigger again if already running)
"""

import time
from ha_automation import HAClient, DeviceDiscovery, AutomationManager


def create_motion_light_automation():
    """
    Example: Create motion-activated light automation.

    This demonstrates the complete workflow:
    1. Initialize clients
    2. Discover available devices
    3. Search for specific devices
    4. Create automation configuration
    5. Deploy to Home Assistant
    6. Verify creation
    """
    print("=" * 70)
    print("AI Automation Creation Example")
    print("=" * 70)
    print()

    # User's request (in Chinese)
    user_request = "晚上10点后走廊有人移动就开灯，亮度30%"
    print(f"User Request: {user_request}")
    print(f"English: Turn on hallway light at 30% when motion detected after 10 PM")
    print()

    # Step 1: Initialize
    print("Step 1: Initializing Home Assistant client...")
    try:
        client = HAClient()
        discovery = DeviceDiscovery(client)
        manager = AutomationManager(client)
        print("✓ Client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        print("\nMake sure you have a .env file with HA_URL and HA_TOKEN")
        return

    # Step 2: Discover devices
    print("\nStep 2: Discovering devices...")
    try:
        devices = discovery.discover_all()
        print(f"✓ Found {len(devices)} devices")

        # Show device summary
        motion_sensors = discovery.get_motion_sensors()
        lights = discovery.get_lights()
        print(f"  • {len(motion_sensors)} motion sensors")
        print(f"  • {len(lights)} lights")
    except Exception as e:
        print(f"✗ Failed to discover devices: {e}")
        return

    # Step 3: Find relevant devices for this automation
    print("\nStep 3: Finding relevant devices...")

    # Search for hallway motion sensor (supports Chinese and English)
    hallway_motion = discovery.search("走廊 motion")
    if not hallway_motion:
        hallway_motion = discovery.search("hallway motion")

    if not hallway_motion:
        print("✗ No hallway motion sensor found")
        print("\nAvailable motion sensors:")
        for sensor in motion_sensors[:5]:
            print(f"  - {sensor.friendly_name} ({sensor.entity_id})")
        print("\nPlease ensure you have a motion sensor in your hallway")
        print("or modify the search query in this script.")
        return

    motion_sensor = hallway_motion[0]
    print(f"✓ Found motion sensor: {motion_sensor.friendly_name}")
    print(f"  Entity ID: {motion_sensor.entity_id}")
    print(f"  Current state: {motion_sensor.state}")

    # Search for hallway light
    hallway_lights = discovery.search("走廊 light")
    if not hallway_lights:
        hallway_lights = discovery.search("hallway light")

    if not hallway_lights:
        print("✗ No hallway light found")
        print("\nAvailable lights:")
        for light in lights[:5]:
            print(f"  - {light.friendly_name} ({light.entity_id})")
        print("\nPlease ensure you have a light in your hallway")
        print("or modify the search query in this script.")
        return

    light = hallway_lights[0]
    print(f"✓ Found light: {light.friendly_name}")
    print(f"  Entity ID: {light.entity_id}")
    print(f"  Current state: {light.state}")

    # Step 4: Create automation configuration
    print("\nStep 4: Creating automation configuration...")

    # Generate unique ID using timestamp
    automation_id = f"night_hallway_lighting_{int(time.time())}"

    automation_config = {
        "id": automation_id,
        "alias": "夜间走廊照明",  # Chinese name
        "description": user_request,  # Store original request as description
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
                "after": "22:00:00",  # 10 PM
                "before": "06:00:00"  # 6 AM
            }
        ],
        "action": [
            {
                "service": "light.turn_on",
                "target": {
                    "entity_id": light.entity_id
                },
                "data": {
                    "brightness_pct": 30  # 30% brightness
                }
            }
        ],
        "mode": "single"  # Don't trigger again if already running
    }

    print("✓ Configuration created:")
    print(f"  ID: {automation_id}")
    print(f"  Name: {automation_config['alias']}")
    print(f"  Trigger: Motion sensor state changes to 'on'")
    print(f"  Condition: Time between 22:00 and 06:00")
    print(f"  Action: Turn on light at 30% brightness")

    # Step 5: Deploy to Home Assistant
    print("\nStep 5: Deploying automation to Home Assistant...")
    try:
        created_id = manager.create_automation_from_config(automation_config)
        print(f"✓ Automation created successfully!")
        print(f"  Automation ID: {created_id}")
        print(f"  Entity ID: automation.{created_id}")
    except Exception as e:
        print(f"✗ Failed to create automation: {e}")
        return

    # Step 6: Verify creation
    print("\nStep 6: Verifying automation...")
    try:
        # Wait a moment for HA to process
        time.sleep(1)

        # Get the automation details
        automation = manager.get_automation(f"automation.{created_id}")
        print(f"✓ Automation verified:")
        print(f"  Entity ID: {automation.entity_id}")
        print(f"  Name: {automation.friendly_name}")
        print(f"  State: {automation.state.upper()}")
        print(f"  Mode: {automation.mode}")

        # List all automations to show context
        all_automations = manager.list_automations()
        print(f"\n  Total automations in system: {len(all_automations)}")

    except Exception as e:
        print(f"⚠ Warning: Could not verify automation: {e}")
        print("  Automation may still be created successfully")

    # Summary
    print("\n" + "=" * 70)
    print("SUCCESS!")
    print("=" * 70)
    print(f"\nAutomation '{automation_config['alias']}' has been created.")
    print("\nHow to manage it:")
    print(f"  • View details: ha-automation show automation.{created_id}")
    print(f"  • Disable: ha-automation disable automation.{created_id}")
    print(f"  • Enable: ha-automation enable automation.{created_id}")
    print(f"  • Trigger manually: ha-automation trigger automation.{created_id}")
    print(f"  • Delete: ha-automation delete {created_id}")
    print("\nThe automation will trigger automatically when:")
    print("  1. Motion is detected in the hallway")
    print("  2. AND it's between 10 PM and 6 AM")
    print("  → Then the hallway light will turn on at 30% brightness")
    print()


def list_available_devices():
    """Helper function to list available devices for debugging."""
    print("\n" + "=" * 70)
    print("Available Devices in Your Home Assistant")
    print("=" * 70)

    try:
        client = HAClient()
        discovery = DeviceDiscovery(client)
        discovery.discover_all()

        # Show motion sensors
        motion_sensors = discovery.get_motion_sensors()
        print(f"\nMotion Sensors ({len(motion_sensors)}):")
        for sensor in motion_sensors:
            print(f"  • {sensor.friendly_name}")
            print(f"    Entity ID: {sensor.entity_id}")
            print(f"    State: {sensor.state}")

        # Show lights
        lights = discovery.get_lights()
        print(f"\nLights ({len(lights)}):")
        for light in lights[:10]:  # Show first 10
            print(f"  • {light.friendly_name}")
            print(f"    Entity ID: {light.entity_id}")
            print(f"    State: {light.state}")

        if len(lights) > 10:
            print(f"  ... and {len(lights) - 10} more lights")

    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run the example."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--list-devices":
        # Just list available devices
        list_available_devices()
    else:
        # Create the automation
        create_motion_light_automation()

        # Offer to show all devices
        print("\nTip: Run with --list-devices to see all available devices")


if __name__ == "__main__":
    main()
