#!/usr/bin/env python3
"""
Example: Generate automation YAML configuration for manual addition.

Since the REST API endpoint for creating automations programmatically is not
available in all Home Assistant installations, this example shows how to:
1. Use the toolkit to discover devices and build configuration
2. Generate properly formatted YAML output
3. Provide clear instructions for manual addition

This is the recommended approach when REST API automation creation is not available.

User request: "晚上10点后走廊有人移动就开灯，亮度30%"
"""

import time
from ha_automation import HAClient, DeviceDiscovery, AutomationManager


def generate_automation_yaml(user_request: str):
    """
    Generate automation YAML from user's natural language request.

    Args:
        user_request: User's description in natural language
    """
    print("=" * 70)
    print("Home Assistant Automation Generator")
    print("=" * 70)
    print()
    print(f"User Request: {user_request}")
    print()

    # Initialize
    print("Initializing and discovering devices...")
    try:
        client = HAClient()
        discovery = DeviceDiscovery(client)
        manager = AutomationManager(client)
        devices = discovery.discover_all()
        print(f"✓ Found {len(devices)} devices")
    except Exception as e:
        print(f"✗ Error: {e}")
        return

    # Search for relevant devices
    # For this example, we'll try to find hallway motion sensor and light
    print("\nSearching for relevant devices...")

    # Try Chinese first, then English
    motion_sensors = discovery.search("走廊 motion") or discovery.search("hallway motion")
    lights = discovery.search("走廊 light") or discovery.search("hallway light")

    if not motion_sensors:
        print("✗ No hallway motion sensor found")
        print("\nAvailable motion sensors:")
        all_motion = discovery.get_motion_sensors()
        for sensor in all_motion[:5]:
            print(f"  - {sensor.friendly_name} ({sensor.entity_id})")
        print("\nPlease select a motion sensor and update the script,")
        print("or use the first available one:")

        if all_motion:
            motion_sensors = [all_motion[0]]
            print(f"  Using: {motion_sensors[0].friendly_name}")
        else:
            print("No motion sensors available!")
            return

    if not lights:
        print("✗ No hallway light found")
        print("\nAvailable lights:")
        all_lights = discovery.get_lights()
        for light in all_lights[:5]:
            print(f"  - {light.friendly_name} ({light.entity_id})")
        print("\nPlease select a light and update the script,")
        print("or use the first available one:")

        if all_lights:
            lights = [all_lights[0]]
            print(f"  Using: {lights[0].friendly_name}")
        else:
            print("No lights available!")
            return

    motion_sensor = motion_sensors[0]
    light = lights[0]

    print(f"\n✓ Motion Sensor: {motion_sensor.friendly_name}")
    print(f"  Entity ID: {motion_sensor.entity_id}")
    print(f"✓ Light: {light.friendly_name}")
    print(f"  Entity ID: {light.entity_id}")

    # Generate automation configuration
    print("\nGenerating automation configuration...")

    automation_id = f"night_hallway_light_{int(time.time())}"

    config = {
        "id": automation_id,
        "alias": "夜间走廊照明",
        "description": user_request,
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

    # Validate configuration
    print("\n✓ Validating configuration...")
    try:
        manager.validate_config(config)
        print("✓ Configuration is valid!")
    except ValueError as e:
        print(f"✗ Validation error: {e}")
        return

    # Generate YAML using new helper method
    print("✓ Generating YAML...")
    yaml_output = manager.generate_yaml(config)

    # Print with new formatted instructions
    print("\n" + "=" * 70)
    print("SUCCESS! Automation configuration generated")
    print("=" * 70)
    print()
    print("This automation will:")
    print(f"  • Trigger when: {motion_sensor.friendly_name} detects motion")
    print("  • Only run between: 10:00 PM and 6:00 AM")
    print(f"  • Action: Turn on {light.friendly_name} at 30% brightness")
    print("  • Mode: Single (won't trigger again while running)")

    # Use new helper method for instructions
    manager.print_yaml_instructions(yaml_output)

    # Save to file as well
    output_file = "generated_automation.yaml"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Home Assistant Automation\n")
        f.write(f"# Generated from: {user_request}\n")
        f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("#\n")
        f.write("# Copy the content below to your automations.yaml file\n")
        f.write("\n")
        f.write(yaml_output)

    print(f"\n✓ Configuration also saved to: {output_file}")
    print()


def show_more_examples():
    """Show additional automation examples using the new helper methods."""
    print("\n" + "=" * 70)
    print("More Automation Examples")
    print("=" * 70)

    # Initialize manager for YAML generation
    try:
        client = HAClient()
        manager = AutomationManager(client)
    except Exception as e:
        print(f"Error initializing: {e}")
        return

    examples = [
        {
            "description": "每天早上7点打开卧室灯",
            "config": {
                "id": "morning_bedroom_light",
                "alias": "早晨卧室灯",
                "trigger": [{"platform": "time", "at": "07:00:00"}],
                "action": [{
                    "service": "light.turn_on",
                    "target": {"entity_id": "light.bedroom"},
                    "data": {"brightness_pct": 80}
                }]
            }
        },
        {
            "description": "温度超过26度开空调",
            "config": {
                "id": "auto_cooling",
                "alias": "自动降温",
                "trigger": [{
                    "platform": "numeric_state",
                    "entity_id": "sensor.temperature",
                    "above": 26
                }],
                "action": [{
                    "service": "climate.set_temperature",
                    "target": {"entity_id": "climate.living_room"},
                    "data": {"temperature": 24}
                }]
            }
        },
        {
            "description": "门打开时发送通知",
            "config": {
                "id": "door_notification",
                "alias": "开门提醒",
                "trigger": [{
                    "platform": "state",
                    "entity_id": "binary_sensor.front_door",
                    "to": "on"
                }],
                "action": [{
                    "service": "notify.notify",
                    "data": {
                        "message": "前门已打开",
                        "title": "门禁提醒"
                    }
                }]
            }
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}")
        print("-" * 70)
        # Use new helper method
        yaml_str = manager.generate_yaml(example['config'])
        print(yaml_str)


def main():
    """Main function."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--examples":
        show_more_examples()
    else:
        # Generate automation from user request
        user_request = "晚上10点后走廊有人移动就开灯，亮度30%"
        generate_automation_yaml(user_request)

        print("\nTip: Run with --examples to see more automation examples")


if __name__ == "__main__":
    main()
