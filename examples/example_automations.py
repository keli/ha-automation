#!/usr/bin/env python3
"""
Example script demonstrating the Home Assistant Automation API.

This script shows how to use the ha_automation library programmatically.
"""

from ha_automation import HAClient, AutomationManager


def main():
    """Run automation management examples."""
    print("=" * 60)
    print("Home Assistant Automation Management - Example Script")
    print("=" * 60)
    print()

    # Initialize client (automatically loads from .env)
    try:
        client = HAClient()
        manager = AutomationManager(client)
    except Exception as e:
        print(f"Failed to initialize client: {e}")
        print("\nMake sure you have a .env file with HA_URL and HA_TOKEN")
        return

    # Test connection
    print("Testing connection...")
    try:
        if client.test_connection():
            config = client.get_config()
            print(f"✓ Connected to: {config.get('location_name', 'Unknown')}")
            print(f"  Version: {config.get('version', 'Unknown')}")
            print()
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return

    # List all automations
    print("Listing all automations:")
    print("-" * 60)
    try:
        automations = manager.list_automations()
        print(f"Found {len(automations)} automation(s)\n")

        for i, auto in enumerate(automations, 1):
            state_symbol = "●" if auto.state == "on" else "○"
            state_text = "ON " if auto.state == "on" else "OFF"

            print(f"{i}. {state_symbol} [{state_text}] {auto.friendly_name or auto.entity_id}")
            print(f"   Entity ID: {auto.entity_id}")
            print(f"   Mode: {auto.mode}")

            if auto.last_triggered:
                print(f"   Last triggered: {auto.last_triggered.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"   Last triggered: Never")

            print()

    except Exception as e:
        print(f"Error listing automations: {e}")
        return

    # Example: Get details of first automation
    if automations:
        print("\nGetting details of first automation:")
        print("-" * 60)
        try:
            first_auto = automations[0]
            details = manager.get_automation(first_auto.entity_id)

            print(f"Entity ID: {details.entity_id}")
            print(f"Name: {details.friendly_name}")
            print(f"State: {details.state}")
            print(f"Mode: {details.mode}")
            print(f"Current runs: {details.current}")
            print(f"Automation ID: {details.automation_id or 'N/A'}")
            print()

        except Exception as e:
            print(f"Error getting automation details: {e}")

    # Example: Filter automations by state
    print("\nListing only enabled automations:")
    print("-" * 60)
    try:
        enabled_automations = manager.list_automations(state_filter="on")
        print(f"Found {len(enabled_automations)} enabled automation(s)")

        for auto in enabled_automations[:5]:  # Show first 5
            print(f"  • {auto.friendly_name or auto.entity_id}")

        if len(enabled_automations) > 5:
            print(f"  ... and {len(enabled_automations) - 5} more")

        print()

    except Exception as e:
        print(f"Error filtering automations: {e}")

    # Example: Demonstrate toggle (commented out for safety)
    print("\nExample operations (commented out for safety):")
    print("-" * 60)
    print("# Toggle an automation:")
    print("# manager.toggle_automation('automation.my_automation')")
    print()
    print("# Enable an automation:")
    print("# manager.turn_on_automation('automation.my_automation')")
    print()
    print("# Disable an automation:")
    print("# manager.turn_off_automation('automation.my_automation')")
    print()
    print("# Manually trigger an automation:")
    print("# manager.trigger_automation('automation.my_automation', skip_condition=True)")
    print()
    print("# Delete an automation (requires automation ID):")
    print("# auto_id = manager.get_automation_id('automation.my_automation')")
    print("# if auto_id:")
    print("#     manager.delete_automation(auto_id)")
    print()
    print("# Reload all automations:")
    print("# manager.reload_automations()")
    print()

    print("=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
