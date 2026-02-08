#!/usr/bin/env python3
"""
Improved YAML Generation Workflow Example

This example demonstrates the recommended workflow for creating Home Assistant
automations using this toolkit.

Key Points:
- Home Assistant does NOT provide a standard API for creating automations
- The ONLY official method is: YAML files + reload service
- This toolkit makes YAML generation easy and reliable
"""

import time
from ha_automation import HAClient, DeviceDiscovery, AutomationManager


def example_1_simple_motion_light():
    """
    Example 1: Simple motion-activated light
    User says: "Turn on hallway light when motion detected at night"
    """
    print("\n" + "=" * 70)
    print("Example 1: Motion-Activated Night Light")
    print("=" * 70)

    # Initialize
    client = HAClient()
    discovery = DeviceDiscovery(client)
    manager = AutomationManager(client)

    # Discover devices
    print("Discovering devices...")
    discovery.discover_all()

    # Search for devices (supports Chinese and English)
    motion_sensors = discovery.search("motion") or discovery.get_motion_sensors()
    lights = discovery.search("light") or discovery.get_lights()

    if not motion_sensors or not lights:
        print("Error: Need at least one motion sensor and one light")
        return

    # Build configuration
    config = {
        "id": f"motion_light_{int(time.time())}",
        "alias": "Motion Activated Night Light",
        "description": "Turn on light when motion detected between 10PM-6AM",
        "trigger": [{
            "platform": "state",
            "entity_id": motion_sensors[0].entity_id,
            "to": "on"
        }],
        "condition": [{
            "condition": "time",
            "after": "22:00:00",
            "before": "06:00:00"
        }],
        "action": [{
            "service": "light.turn_on",
            "target": {"entity_id": lights[0].entity_id},
            "data": {"brightness_pct": 30}
        }],
        "mode": "single"
    }

    # Validate
    print("Validating configuration...")
    try:
        manager.validate_config(config)
        print("✓ Configuration is valid!")
    except ValueError as e:
        print(f"✗ Error: {e}")
        return

    # Generate YAML
    print("Generating YAML...")
    yaml_output = manager.generate_yaml(config)

    # Print with instructions
    manager.print_yaml_instructions(yaml_output)


def example_2_batch_generation():
    """
    Example 2: Generate multiple automations at once
    """
    print("\n" + "=" * 70)
    print("Example 2: Batch YAML Generation")
    print("=" * 70)

    client = HAClient()
    manager = AutomationManager(client)

    # Multiple automation configs
    configs = [
        {
            "id": "morning_lights",
            "alias": "Morning Lights",
            "description": "Turn on lights at 7 AM",
            "trigger": [{"platform": "time", "at": "07:00:00"}],
            "action": [{
                "service": "light.turn_on",
                "target": {"entity_id": "light.bedroom"},
                "data": {"brightness_pct": 80}
            }],
            "mode": "single"
        },
        {
            "id": "evening_lights",
            "alias": "Evening Lights",
            "description": "Turn on lights at sunset",
            "trigger": [{"platform": "sun", "event": "sunset"}],
            "action": [{
                "service": "light.turn_on",
                "target": {"entity_id": "light.living_room"}
            }],
            "mode": "single"
        },
        {
            "id": "night_lights_off",
            "alias": "Night Lights Off",
            "description": "Turn off all lights at 11 PM",
            "trigger": [{"platform": "time", "at": "23:00:00"}],
            "action": [{
                "service": "light.turn_off",
                "target": {"entity_id": "all"}
            }],
            "mode": "single"
        }
    ]

    # Generate YAML for all automations
    print("Generating YAML for 3 automations...")
    yaml_output = manager.generate_yaml_batch(configs)

    print("\n" + "=" * 70)
    print("Batch Generated Automations")
    print("=" * 70)
    print(yaml_output)
    print("=" * 70)
    print("\nCopy all three automations to your automations.yaml file!")


def example_3_interactive_builder():
    """
    Example 3: Interactive automation builder
    Helps user build automation step by step
    """
    print("\n" + "=" * 70)
    print("Example 3: Interactive Automation Builder")
    print("=" * 70)

    client = HAClient()
    discovery = DeviceDiscovery(client)
    manager = AutomationManager(client)

    print("\nDiscovering devices...")
    discovery.discover_all()

    # Show available motion sensors
    motion_sensors = discovery.get_motion_sensors()
    if not motion_sensors:
        print("No motion sensors found!")
        return

    print("\nAvailable motion sensors:")
    for i, sensor in enumerate(motion_sensors, 1):
        print(f"{i}. {sensor.friendly_name} ({sensor.entity_id})")

    # For demo, use first sensor
    selected_sensor = motion_sensors[0]
    print(f"\nUsing: {selected_sensor.friendly_name}")

    # Show available lights
    lights = discovery.get_lights()
    if not lights:
        print("No lights found!")
        return

    print("\nAvailable lights:")
    for i, light in enumerate(lights[:5], 1):
        print(f"{i}. {light.friendly_name} ({light.entity_id})")

    # For demo, use first light
    selected_light = lights[0]
    print(f"\nUsing: {selected_light.friendly_name}")

    # Build configuration interactively
    config = {
        "id": f"interactive_auto_{int(time.time())}",
        "alias": f"Motion {selected_sensor.friendly_name} → {selected_light.friendly_name}",
        "description": "Created with interactive builder",
        "trigger": [{
            "platform": "state",
            "entity_id": selected_sensor.entity_id,
            "to": "on"
        }],
        "action": [{
            "service": "light.turn_on",
            "target": {"entity_id": selected_light.entity_id},
            "data": {"brightness_pct": 50}
        }],
        "mode": "single"
    }

    # Validate and generate
    manager.validate_config(config)
    yaml_output = manager.generate_yaml(config)
    manager.print_yaml_instructions(yaml_output)


def example_4_validation_demo():
    """
    Example 4: Configuration validation
    Shows how to validate automation configs before generating YAML
    """
    print("\n" + "=" * 70)
    print("Example 4: Configuration Validation")
    print("=" * 70)

    client = HAClient()
    manager = AutomationManager(client)

    # Valid configuration
    valid_config = {
        "id": "valid_auto",
        "alias": "Valid Automation",
        "trigger": [{"platform": "state", "entity_id": "light.bedroom", "to": "on"}],
        "action": [{"service": "light.turn_off", "target": {"entity_id": "light.living_room"}}],
        "mode": "single"
    }

    print("\nValidating a correct configuration...")
    try:
        manager.validate_config(valid_config)
        print("✓ Configuration is valid!")
    except ValueError as e:
        print(f"✗ Error: {e}")

    # Invalid configurations
    invalid_configs = [
        {
            "name": "Missing ID",
            "config": {
                "alias": "Test",
                "trigger": [],
                "action": []
            }
        },
        {
            "name": "Empty trigger list",
            "config": {
                "id": "test",
                "alias": "Test",
                "trigger": [],  # Empty!
                "action": [{"service": "light.turn_on"}]
            }
        },
        {
            "name": "Invalid mode",
            "config": {
                "id": "test",
                "alias": "Test",
                "trigger": [{"platform": "state", "entity_id": "light.bedroom"}],
                "action": [{"service": "light.turn_on"}],
                "mode": "invalid_mode"  # Bad!
            }
        }
    ]

    print("\nTesting invalid configurations:")
    for item in invalid_configs:
        print(f"\n  Testing: {item['name']}")
        try:
            manager.validate_config(item['config'])
            print("    ✗ Should have failed!")
        except ValueError as e:
            print(f"    ✓ Caught error: {e}")


def example_5_chinese_workflow():
    """
    Example 5: Chinese language workflow
    演示中文工作流程
    """
    print("\n" + "=" * 70)
    print("示例 5: 中文自动化创建流程")
    print("=" * 70)

    client = HAClient()
    discovery = DeviceDiscovery(client)
    manager = AutomationManager(client)

    print("\n正在发现设备...")
    discovery.discover_all()

    # 搜索中文设备名称
    motion_sensors = discovery.search("走廊") or discovery.search("motion")
    lights = discovery.search("走廊灯") or discovery.get_lights()

    if not motion_sensors or not lights:
        print("未找到合适的设备")
        return

    # 创建中文配置
    config = {
        "id": f"chinese_auto_{int(time.time())}",
        "alias": "夜间走廊照明",
        "description": "晚上10点到早上6点,检测到走廊有人移动时自动开灯",
        "trigger": [{
            "platform": "state",
            "entity_id": motion_sensors[0].entity_id,
            "to": "on"
        }],
        "condition": [{
            "condition": "time",
            "after": "22:00:00",
            "before": "06:00:00"
        }],
        "action": [{
            "service": "light.turn_on",
            "target": {"entity_id": lights[0].entity_id},
            "data": {"brightness_pct": 30}
        }],
        "mode": "single"
    }

    print("验证配置...")
    manager.validate_config(config)
    print("✓ 配置有效!")

    print("\n生成 YAML...")
    yaml_output = manager.generate_yaml(config)

    print("\n" + "=" * 70)
    print("📋 请复制下面的 YAML 配置:")
    print("=" * 70)
    print(yaml_output)
    print("=" * 70)
    print("\n📝 使用步骤:")
    print("1. 打开 Home Assistant 的配置目录")
    print("2. 编辑 automations.yaml 文件")
    print("3. 将上面的 YAML 添加到文件中")
    print("4. 保存文件")
    print("5. 在 HA 界面重新加载自动化:")
    print("   设置 → 自动化 → ⋮ → 重新加载自动化")
    print("=" * 70)


def main():
    """Run all examples."""
    import sys

    examples = {
        "1": ("Simple Motion Light", example_1_simple_motion_light),
        "2": ("Batch Generation", example_2_batch_generation),
        "3": ("Interactive Builder", example_3_interactive_builder),
        "4": ("Validation Demo", example_4_validation_demo),
        "5": ("Chinese Workflow / 中文流程", example_5_chinese_workflow),
    }

    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if choice in examples:
            name, func = examples[choice]
            print(f"\nRunning: {name}")
            func()
        else:
            print("Invalid example number")
            print("\nAvailable examples:")
            for key, (name, _) in examples.items():
                print(f"  {key}: {name}")
    else:
        print("\nHome Assistant Automation YAML Generation Examples")
        print("=" * 70)
        print("\nAvailable examples:")
        for key, (name, _) in examples.items():
            print(f"  {key}: {name}")
        print("\nUsage: python improved_yaml_workflow.py [example_number]")
        print("Example: python improved_yaml_workflow.py 1")
        print("\nRunning all examples...\n")

        # Run all examples
        for key, (name, func) in examples.items():
            try:
                func()
            except Exception as e:
                print(f"\nError in {name}: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()
