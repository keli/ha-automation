# AI Assistant Guide for Home Assistant Automation Toolkit

This toolkit helps AI assistants (like Claude Code, GitHub Copilot, etc.) create Home Assistant automations from natural language descriptions.

## Architecture

```
User (natural language) → AI Assistant → Python Toolkit → YAML Generation → User Copies to File → HA Reload
```

The AI assistant:
1. Understands what the user wants
2. Uses this toolkit to discover devices
3. Generates automation configuration
4. **Outputs formatted YAML for user to copy**
5. User adds YAML to their `automations.yaml`
6. User reloads (or toolkit triggers reload via API)

## Why YAML Generation?

Home Assistant does NOT provide a standard REST API for creating automation configurations:
- ❌ REST API `/api/config/automation/config` is NOT part of the official API
- ❌ WebSocket API does NOT provide automation creation commands
- ✅ YAML files + reload service IS the official method (works in all installations)

## Quick Start for AI

### Step 1: Initialize Client

```python
from ha_automation import HAClient, DeviceDiscovery, AutomationManager

# Initialize (automatically loads from .env file)
client = HAClient()  # Reads HA_URL and HA_TOKEN from environment
discovery = DeviceDiscovery(client)
manager = AutomationManager(client)
```

### Step 2: Discover Available Devices

```python
# Discover all devices (cached for performance)
devices = discovery.discover_all()

# Search for specific devices
motion_sensors = discovery.get_motion_sensors()
lights = discovery.get_lights()
door_sensors = discovery.get_door_sensors()
temp_sensors = discovery.get_temperature_sensors()

# Search by name (supports Chinese and English)
hallway_devices = discovery.search("走廊")  # Search for "hallway"
bedroom_lights = discovery.search("bedroom light")

# Filter by domain
all_lights = discovery.get_by_domain('light')
all_sensors = discovery.get_by_domain('sensor')

# Filter by area
living_room = discovery.get_by_area("Living Room")
```

### Step 3: Generate YAML for User to Copy

```python
import yaml

# Define automation configuration
automation_config = {
    "id": "my_automation_123",  # Unique ID
    "alias": "Night Hallway Light",  # Human-readable name
    "description": "Turn on hallway light when motion detected at night",
    "trigger": [
        {
            "platform": "state",
            "entity_id": "binary_sensor.hallway_motion",
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
                "entity_id": "light.hallway"
            },
            "data": {
                "brightness_pct": 30
            }
        }
    ],
    "mode": "single"
}

# Generate YAML output (new helper method)
yaml_output = manager.generate_yaml(automation_config)

# Present to user
print("\n" + "="*60)
print("Add this to your automations.yaml file:")
print("="*60)
print(yaml_output)
print("="*60)
print("\nThen reload automations by:")
print("1. Click 'Reload Automations' in Home Assistant UI, OR")
print("2. Run: ha-automation reload")
```

## Common Automation Patterns

### Pattern 1: Motion-Activated Light

User says: "晚上10点后走廊有人移动就开灯，亮度30%"
(Turn on hallway light at 30% brightness when motion detected after 10 PM)

```python
# 1. Find devices
motion_sensor = discovery.search("走廊 motion")[0]  # or "hallway motion"
light = discovery.search("走廊 light")[0]  # or "hallway light"

# 2. Create automation
config = {
    "id": f"night_motion_light_{int(time.time())}",
    "alias": "夜间走廊照明",
    "description": "晚上10点后走廊有人移动就开灯，亮度30%",
    "trigger": [{
        "platform": "state",
        "entity_id": motion_sensor.entity_id,
        "to": "on"
    }],
    "condition": [{
        "condition": "time",
        "after": "22:00:00",
        "before": "06:00:00"
    }],
    "action": [{
        "service": "light.turn_on",
        "target": {"entity_id": light.entity_id},
        "data": {"brightness_pct": 30}
    }],
    "mode": "single"
}

# Generate YAML and show to user
yaml_output = manager.generate_yaml(config)
print(yaml_output)
print("\nCopy this to your automations.yaml file and reload!")
```

### Pattern 2: Time-Based Automation

User says: "每天晚上10点关闭所有灯"
(Turn off all lights at 10 PM every day)

```python
all_lights = discovery.get_lights()
light_ids = [light.entity_id for light in all_lights]

config = {
    "id": f"night_lights_off_{int(time.time())}",
    "alias": "晚上关灯",
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

# Generate YAML and show to user
yaml_output = manager.generate_yaml(config)
print(yaml_output)
print("\nCopy this to your automations.yaml file and reload!")
```

### Pattern 3: Temperature-Based Climate Control

User says: "温度超过26度就把空调设到24度"
(Set AC to 24°C when temperature exceeds 26°C)

```python
temp_sensor = discovery.get_temperature_sensors()[0]
climate = discovery.get_by_domain('climate')[0]

config = {
    "id": f"auto_cooling_{int(time.time())}",
    "alias": "自动降温",
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

# Generate YAML and show to user
yaml_output = manager.generate_yaml(config)
print(yaml_output)
print("\nCopy this to your automations.yaml file and reload!")
```

### Pattern 4: Door Open Alert

User says: "晚上11点后如果门打开就发通知"
(Send notification if door opens after 11 PM)

```python
door_sensor = discovery.get_door_sensors()[0]

config = {
    "id": f"night_door_alert_{int(time.time())}",
    "alias": "夜间开门提醒",
    "trigger": [{
        "platform": "state",
        "entity_id": door_sensor.entity_id,
        "to": "on"
    }],
    "condition": [{
        "condition": "time",
        "after": "23:00:00",
        "before": "06:00:00"
    }],
    "action": [{
        "service": "notify.notify",
        "data": {
            "message": "门在深夜被打开了！",
            "title": "安全提醒"
        }
    }],
    "mode": "single"
}

# Generate YAML and show to user
yaml_output = manager.generate_yaml(config)
print(yaml_output)
print("\nCopy this to your automations.yaml file and reload!")
```

### Pattern 5: Auto Turn Off After Duration

User says: "走廊灯开启5分钟后自动关闭"
(Turn off hallway light automatically after 5 minutes)

```python
light = discovery.search("走廊 light")[0]

config = {
    "id": f"auto_off_light_{int(time.time())}",
    "alias": "走廊灯自动关闭",
    "trigger": [{
        "platform": "state",
        "entity_id": light.entity_id,
        "to": "on",
        "for": "00:05:00"  # 5 minutes
    }],
    "action": [{
        "service": "light.turn_off",
        "target": {"entity_id": light.entity_id}
    }],
    "mode": "single"
}

# Generate YAML and show to user
yaml_output = manager.generate_yaml(config)
print(yaml_output)
print("\nCopy this to your automations.yaml file and reload!")
```

## Home Assistant Automation Reference

### Trigger Types

**State Trigger** - Entity state changes:
```python
{
    "platform": "state",
    "entity_id": "binary_sensor.motion",
    "to": "on",  # Optional: trigger only on specific state
    "from": "off",  # Optional: trigger only from specific state
    "for": "00:05:00"  # Optional: state must persist for duration
}
```

**Time Trigger** - Specific time:
```python
{
    "platform": "time",
    "at": "22:00:00"  # HH:MM:SS format
}
```

**Numeric State Trigger** - Numeric comparison:
```python
{
    "platform": "numeric_state",
    "entity_id": "sensor.temperature",
    "above": 26,  # Optional
    "below": 20,  # Optional
    "for": "00:10:00"  # Optional: must persist
}
```

**Template Trigger** - Complex conditions:
```python
{
    "platform": "template",
    "value_template": "{{ states('sensor.temperature') | float > 25 }}"
}
```

**Sun Trigger** - Sunrise/sunset:
```python
{
    "platform": "sun",
    "event": "sunset",  # or "sunrise"
    "offset": "-00:30:00"  # Optional: 30 min before sunset
}
```

### Condition Types

**Time Condition** - Time range:
```python
{
    "condition": "time",
    "after": "22:00:00",
    "before": "06:00:00",
    "weekday": ["mon", "tue", "wed", "thu", "fri"]  # Optional
}
```

**State Condition** - Entity in specific state:
```python
{
    "condition": "state",
    "entity_id": "light.living_room",
    "state": "off"
}
```

**Numeric State Condition** - Numeric comparison:
```python
{
    "condition": "numeric_state",
    "entity_id": "sensor.temperature",
    "above": 20,
    "below": 30
}
```

**Template Condition** - Complex logic:
```python
{
    "condition": "template",
    "value_template": "{{ is_state('sun.sun', 'below_horizon') }}"
}
```

**Sun Condition** - Before/after sunrise/sunset:
```python
{
    "condition": "sun",
    "after": "sunset",  # or "before": "sunrise"
    "after_offset": "-01:00:00"  # Optional
}
```

### Action Types

**Service Call** - Call any HA service:
```python
{
    "service": "light.turn_on",
    "target": {"entity_id": "light.living_room"},
    "data": {
        "brightness_pct": 80,
        "color_temp": 370,
        "transition": 2  # seconds
    }
}
```

**Delay** - Wait before next action:
```python
{
    "delay": "00:05:00"  # HH:MM:SS format
}
```

**Wait for Trigger** - Wait for condition:
```python
{
    "wait_for_trigger": [{
        "platform": "state",
        "entity_id": "binary_sensor.motion",
        "to": "off"
    }],
    "timeout": "00:05:00",  # Optional max wait time
    "continue_on_timeout": false  # Optional
}
```

**Choose** - Conditional actions (if-then-else):
```python
{
    "choose": [
        {
            "conditions": [{
                "condition": "state",
                "entity_id": "sun.sun",
                "state": "below_horizon"
            }],
            "sequence": [{
                "service": "light.turn_on",
                "target": {"entity_id": "light.outdoor"},
                "data": {"brightness_pct": 100}
            }]
        }
    ],
    "default": [{  # Optional else clause
        "service": "light.turn_on",
        "data": {"brightness_pct": 50}
    }]
}
```

### Automation Modes

- `single`: Only one instance at a time (default)
- `restart`: Restart automation if triggered again
- `queued`: Queue instances (set `max` for queue size)
- `parallel`: Allow multiple concurrent instances (set `max` for limit)

```python
{
    "mode": "queued",
    "max": 5  # Maximum 5 queued instances
}
```

## Common Services by Domain

### Lights (`light`)
- `light.turn_on` - Turn on light
- `light.turn_off` - Turn off light
- `light.toggle` - Toggle light state

Parameters for `turn_on`:
- `brightness_pct`: 0-100
- `brightness`: 0-255
- `color_temp`: Color temperature in mireds
- `rgb_color`: [R, G, B] array (0-255)
- `transition`: Transition time in seconds

### Switches (`switch`)
- `switch.turn_on`
- `switch.turn_off`
- `switch.toggle`

### Climate (`climate`)
- `climate.set_temperature` - Set target temperature
- `climate.set_hvac_mode` - Set mode (heat, cool, auto, off)
- `climate.set_fan_mode` - Set fan mode

### Notify (`notify`)
- `notify.notify` - Send notification

Parameters:
- `message`: Notification text
- `title`: Notification title
- `target`: Target device/person (optional)

### Media Player (`media_player`)
- `media_player.play_media`
- `media_player.media_pause`
- `media_player.volume_set`

## Tips for AI Assistants

1. **Always discover devices first** - Use `discovery.discover_all()` to see what's available
2. **Search flexibly** - Support both Chinese and English device names
3. **Use unique IDs** - Generate unique automation IDs with timestamp: `f"automation_{int(time.time())}"`
4. **Be specific** - When multiple matches found, ask user to clarify which device
5. **Validate** - Check that required devices exist before creating automation
6. **Use descriptive names** - Set `alias` to clearly describe what automation does
7. **Add descriptions** - Use `description` field to explain automation in user's language
8. **Generate clean YAML** - Use `manager.generate_yaml()` for properly formatted output
9. **Provide clear instructions** - Tell user exactly where to copy the YAML
10. **Offer to reload** - After user adds YAML, offer to run `manager.reload_automations()`

## Important: What NOT to Do

❌ **DO NOT** try to use `manager.create_automation_from_config()` - it uses an unreliable API endpoint
❌ **DO NOT** tell users to "enable default_config" or modify their HA configuration
❌ **DO NOT** promise that automations will be created automatically via API

✅ **DO** generate YAML and present it clearly to users
✅ **DO** explain this is the official Home Assistant method
✅ **DO** make the copy-paste workflow as smooth as possible

## Error Handling

```python
try:
    # Discover devices
    devices = discovery.discover_all()
    if not devices:
        print("No devices found. Please check Home Assistant connection.")
        return

    # Search for specific device
    lights = discovery.search("hallway light")
    if not lights:
        print("Could not find hallway light. Available lights:")
        for light in discovery.get_lights():
            print(f"  - {light.friendly_name} ({light.entity_id})")
        return

    # Create automation
    automation_id = # Generate YAML and show to user
yaml_output = manager.generate_yaml(config)
print(yaml_output)
print("\nCopy this to your automations.yaml file and reload!")
    print(f"✓ Created automation: {automation_id}")

    # Verify it was created
    automations = manager.list_automations()
    print(f"Total automations: {len(automations)}")

except ValueError as e:
    print(f"Validation error: {e}")
except RuntimeError as e:
    print(f"Runtime error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Full Workflow Example

```python
import time
from ha_automation import HAClient, DeviceDiscovery, AutomationManager

def create_automation_from_description(description: str):
    """
    Example: Parse user description and create automation.

    Args:
        description: User's natural language description (Chinese or English)
    """
    # Initialize
    client = HAClient()
    discovery = DeviceDiscovery(client)
    manager = AutomationManager(client)

    # Discover devices
    print("Discovering devices...")
    devices = discovery.discover_all()
    print(f"Found {len(devices)} devices")

    # Parse user intent (this is where AI does the work!)
    # Example: "晚上10点后走廊有人移动就开灯，亮度30%"

    # Find relevant devices
    motion_sensors = discovery.search("走廊 motion")
    lights = discovery.search("走廊 light")

    if not motion_sensors:
        print("Error: No hallway motion sensor found")
        return

    if not lights:
        print("Error: No hallway light found")
        return

    motion_sensor = motion_sensors[0]
    light = lights[0]

    print(f"Using motion sensor: {motion_sensor.friendly_name}")
    print(f"Using light: {light.friendly_name}")

    # Create automation
    config = {
        "id": f"night_hallway_light_{int(time.time())}",
        "alias": "夜间走廊照明",
        "description": description,
        "trigger": [{
            "platform": "state",
            "entity_id": motion_sensor.entity_id,
            "to": "on"
        }],
        "condition": [{
            "condition": "time",
            "after": "22:00:00",
            "before": "06:00:00"
        }],
        "action": [{
            "service": "light.turn_on",
            "target": {"entity_id": light.entity_id},
            "data": {"brightness_pct": 30}
        }],
        "mode": "single"
    }

    print("Creating automation...")
    automation_id = # Generate YAML and show to user
yaml_output = manager.generate_yaml(config)
print(yaml_output)
print("\nCopy this to your automations.yaml file and reload!")
    print(f"✓ Created: automation.{automation_id}")

    # Show result
    auto = manager.get_automation(f"automation.{automation_id}")
    print(f"Status: {auto.state}")
    print(f"Name: {auto.friendly_name}")

# Use it
create_automation_from_description("晚上10点后走廊有人移动就开灯，亮度30%")
```

## CLI Commands Reference

The toolkit also provides CLI commands for manual testing:

```bash
# Discover and cache devices
ha-automation discover
ha-automation discover --force  # Force refresh

# Search devices
ha-automation devices "motion"
ha-automation devices --type light
ha-automation devices --area "Living Room"
ha-automation devices --json  # JSON output

# List automations
ha-automation list
ha-automation list --state on
ha-automation list --json

# Show automation details
ha-automation show automation.my_automation

# Control automations
ha-automation enable automation.my_automation
ha-automation disable automation.my_automation
ha-automation toggle automation.my_automation

# Trigger manually
ha-automation trigger automation.my_automation
ha-automation trigger automation.my_automation --skip-condition

# Delete automation
ha-automation delete <automation_id>

# Reload all automations
ha-automation reload

# Test connection
ha-automation test
```

## Configuration Validation

Always validate configurations before generating YAML:

```python
# Validate before generating
try:
    manager.validate_config(config)
    yaml_output = manager.generate_yaml(config)
except ValueError as e:
    print(f"Configuration error: {e}")
    return
```

The validator checks:
- Required fields (id, alias, trigger, action)
- Trigger/action are non-empty lists
- Condition is list if present
- Mode is valid (single, restart, queued, parallel)

## CLI Commands for YAML Generation

```bash
# Generate YAML from command-line parameters
ha-automation generate-yaml \
  --motion-sensor binary_sensor.hallway_motion \
  --light light.hallway \
  --name "Night Hallway Light" \
  --brightness 30 \
  --time-after "22:00:00" \
  --time-before "06:00:00"

# Validate YAML file
ha-automation validate my_automation.yaml
```

## Summary

This toolkit provides a clean API layer between AI assistants and Home Assistant. The AI assistant's job is to:

1. **Understand** user's natural language description
2. **Discover** devices using `DeviceDiscovery`
3. **Build** automation configuration dictionary
4. **Generate** YAML using `manager.generate_yaml(config)`
5. **Present** formatted YAML to user with clear copy-paste instructions
6. **Optionally reload** after user confirms they've added the YAML

The toolkit handles all the technical details:
- ✅ Home Assistant API communication
- ✅ Device discovery and search
- ✅ Configuration validation
- ✅ YAML formatting with proper syntax
- ✅ Automation management (list, enable/disable, reload)

**Remember**: Home Assistant doesn't provide an API to create automations. YAML generation is the official method, and this toolkit makes it easy.
