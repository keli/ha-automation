# AI Assistant Guide for Home Assistant Automation Toolkit

This toolkit helps AI assistants (like Claude Code, GitHub Copilot, etc.) create Home Assistant automations from natural language descriptions using the Home Assistant REST API.

## ⚠️ Critical Rules

### Always Use the API

**Key Principle**: Automations should ALWAYS be created via the Home Assistant API.

**Why:**
- ✅ Fully automated - no manual steps required
- ✅ Immediate feedback on success/failure
- ✅ Changes take effect immediately after reload
- ✅ Clean integration with Home Assistant's automation storage

**Correct Workflow:**
1. Create automation config dictionary in Python
2. Call `manager.create_or_update(config)` (recommended) or `manager.create_automation(config)`
3. Automation is automatically created/updated and reloaded
4. Verify success by checking automation state

**Wrong Approaches:**
- ❌ Never generate YAML for manual editing
- ❌ Never ask users to manually copy configurations
- ❌ Never bypass the API

### Use Fixed IDs for Sync Workflows

**Key Principle**: For scripts in `~/.config/ha-automation/automations/`, ALWAYS use fixed, descriptive IDs.

**Why:**
- ✅ `ha-automation sync` will update existing automations instead of creating duplicates
- ✅ Idempotent - running script multiple times doesn't create duplicates
- ✅ More semantic and easier to identify
- ✅ Enables proper version control of automations

**Correct Approach:**
```python
# ✅ CORRECT: Fixed ID
automation_config = {
    "id": "door_unlock_auto_lights",  # Fixed, descriptive ID
    "alias": "门外开锁自动开灯",
    ...
}

# Use create_or_update for idempotent operations
automation_id, was_created = manager.create_or_update(automation_config)
if was_created:
    print(f"✅ Created: {automation_id}")
else:
    print(f"✅ Updated: {automation_id}")
```

**Wrong Approach:**
```python
# ❌ WRONG: Time-based ID creates duplicates every time
automation_config = {
    "id": f"my_automation_{int(time.time())}",  # Different ID each time!
    ...
}
manager.create_automation(automation_config)  # Creates duplicate on each run
```

**When to use each method:**
- `manager.create_or_update(config)` - **Recommended** for `~/.config/ha-automation/automations/` scripts (idempotent)
- `manager.create_automation(config)` - Only for one-off creations or when you specifically want a new instance
- `manager.update_automation(id, config)` - Only when you know automation exists and want to update it

### File Organization

- ✅ **User's personal automations** → `~/.config/ha-automation/automations/` directory (default)
  - Device-specific configurations
  - Contains personal information (entity IDs)
  - Override with `HA_AUTOMATION_SCRIPTS_DIR` env var or `--directory` CLI flag

- ✅ **General examples** → `examples/` directory
  - Teaching examples
  - Reusable templates

## Architecture

```
User (natural language) → AI Assistant → Python Script → HA API → Automation Created
```

The AI assistant:
1. Understands what the user wants
2. Uses this toolkit to discover devices
3. **Creates automation config dictionary**
4. **Calls API to create automation**
5. Verifies automation was created
6. Reports success to user

## Quick Start for AI

### Step 1: Initialize Client

```python
from ha_automation import HAClient, DeviceDiscovery, AutomationManager

# Initialize (automatically loads from ~/.config/ha-automation/config)
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

### Step 3: Create/Update Automation via API

**⚠️ IMPORTANT: Use fixed IDs, not time-based IDs!**

```python
# Define automation configuration with FIXED ID
automation_config = {
    "id": "night_hallway_light",  # ✅ Fixed ID - enables updates via sync
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

# Create or update automation via API (RECOMMENDED - idempotent)
try:
    automation_id, was_created = manager.create_or_update(automation_config)
    if was_created:
        print(f"✅ Created automation: {automation_id}")
    else:
        print(f"✅ Updated automation: {automation_id}")

    # Verify it was created/updated
    auto = manager.get_automation(f"automation.{automation_id}")
    print(f"✅ Verified: {auto.friendly_name} (state: {auto.state})")
except Exception as e:
    print(f"❌ Failed to create/update automation: {e}")
```

## Common Automation Patterns

### Pattern 1: Motion-Activated Light

User says: "晚上10点后走廊有人移动就开灯，亮度30%"
(Turn on hallway light at 30% brightness when motion detected after 10 PM)

```python
# 1. Find devices
motion_sensor = discovery.search("走廊 motion")[0]  # or "hallway motion"
light = discovery.search("走廊 light")[0]  # or "hallway light"

# 2. Create automation with FIXED ID
config = {
    "id": "night_motion_light_hallway",  # ✅ Fixed ID
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

# Create or update via API (idempotent)
automation_id, was_created = manager.create_or_update(config)
print(f"✅ {'Created' if was_created else 'Updated'}: automation.{automation_id}")
```

### Pattern 2: Time-Based Automation

User says: "每天晚上10点关闭所有灯"
(Turn off all lights at 10 PM every day)

```python
all_lights = discovery.get_lights()
light_ids = [light.entity_id for light in all_lights]

config = {
    "id": "night_lights_off",  # ✅ Fixed ID
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

automation_id, was_created = manager.create_or_update(config)
print(f"✅ {'Created' if was_created else 'Updated'}: automation.{automation_id}")
```

### Pattern 3: Temperature-Based Climate Control

User says: "温度超过26度就把空调设到24度"
(Set AC to 24°C when temperature exceeds 26°C)

```python
temp_sensor = discovery.get_temperature_sensors()[0]
climate = discovery.get_by_domain('climate')[0]

config = {
    "id": "auto_cooling",  # ✅ Fixed ID
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

automation_id, was_created = manager.create_or_update(config)
print(f"✅ {'Created' if was_created else 'Updated'}: automation.{automation_id}")
```

### Pattern 4: Door Open Alert

User says: "晚上11点后如果门打开就发通知"
(Send notification if door opens after 11 PM)

```python
door_sensor = discovery.get_door_sensors()[0]

config = {
    "id": "night_door_alert",  # ✅ Fixed ID
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

automation_id, was_created = manager.create_or_update(config)
print(f"✅ {'Created' if was_created else 'Updated'}: automation.{automation_id}")
```

### Pattern 5: Auto Turn Off After Duration

User says: "走廊灯开启5分钟后自动关闭"
(Turn off hallway light automatically after 5 minutes)

```python
light = discovery.search("走廊 light")[0]

config = {
    "id": "auto_off_light_hallway",  # ✅ Fixed ID
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

automation_id, was_created = manager.create_or_update(config)
print(f"✅ {'Created' if was_created else 'Updated'}: automation.{automation_id}")
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
3. **Use FIXED IDs** - ⚠️ Use fixed, descriptive IDs like `"night_hallway_light"`, NOT `f"automation_{int(time.time())}"`. Fixed IDs enable idempotent sync workflows.
4. **Be specific** - When multiple matches found, ask user to clarify which device
5. **Validate** - Check that required devices exist before creating automation
6. **Use descriptive names** - Set `alias` to clearly describe what automation does
7. **Add descriptions** - Use `description` field to explain automation in user's language
8. **Use create_or_update()** - Call `manager.create_or_update(config)` for idempotent operations (recommended for `~/.config/ha-automation/automations/` scripts)
9. **Verify creation** - After creation, verify with `manager.get_automation()`
10. **Handle errors gracefully** - Catch exceptions and provide clear error messages

## Error Handling

```python
from ha_automation import HAClient, DeviceDiscovery, AutomationManager

try:
    # Initialize
    client = HAClient()
    discovery = DeviceDiscovery(client)
    manager = AutomationManager(client)

    # Discover devices
    devices = discovery.discover_all()
    if not devices:
        print("No devices found. Please check Home Assistant connection.")
        exit(1)

    # Search for specific device
    lights = discovery.search("hallway light")
    if not lights:
        print("Could not find hallway light. Available lights:")
        for light in discovery.get_lights():
            print(f"  - {light.friendly_name} ({light.entity_id})")
        exit(1)

    # Create or update automation (idempotent)
    config = {
        "id": "test_automation",  # ✅ Fixed ID
        "alias": "Test Automation",
        "trigger": [{"platform": "state", "entity_id": lights[0].entity_id, "to": "on"}],
        "action": [{"service": "persistent_notification.create", "data": {"message": "Light turned on"}}]
    }

    automation_id, was_created = manager.create_or_update(config)
    print(f"✓ {'Created' if was_created else 'Updated'} automation: {automation_id}")

    # Verify it was created/updated
    auto = manager.get_automation(f"automation.{automation_id}")
    print(f"✓ Verified: {auto.friendly_name} (state: {auto.state})")

except ValueError as e:
    print(f"Validation error: {e}")
except RuntimeError as e:
    print(f"Runtime error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Full Workflow Example

```python
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

    # Create automation with FIXED ID
    config = {
        "id": "night_hallway_light",  # ✅ Fixed ID
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

    print("Creating/updating automation...")
    automation_id, was_created = manager.create_or_update(config)
    print(f"✓ {'Created' if was_created else 'Updated'}: automation.{automation_id}")

    # Verify creation
    auto = manager.get_automation(f"automation.{automation_id}")
    print(f"✓ Status: {auto.state}")
    print(f"✓ Name: {auto.friendly_name}")

# Use it
create_automation_from_description("晚上10点后走廊有人移动就开灯，亮度30%")
```

## CLI Commands Reference

The toolkit provides CLI commands for automation management:

```bash
# Discover and cache devices
ha-automation discover
ha-automation discover --force  # Force refresh

# Search devices
ha-automation devices "motion"
ha-automation devices --type light
ha-automation devices --area "Living Room"
ha-automation devices --json  # JSON output

# Sync all automation scripts in ~/.config/ha-automation/automations/ (Recommended!)
ha-automation sync                    # Run all scripts to create/update automations
ha-automation sync --dry-run         # Preview changes without applying
ha-automation sync --clean           # Also remove orphaned automations
ha-automation sync --directory /path/to/scripts  # Use custom directory

# Run a single automation script (API-based)
ha-automation run ~/.config/ha-automation/automations/door_unlock_lights.py

# Create automations from templates (Interactive, API-based)
ha-automation create-from-template motion-light
ha-automation create-from-template time-based
# Available templates: motion-light, time-based, temperature-control, door-alert, auto-off

# List automations
ha-automation list
ha-automation list --state on
ha-automation list --json

# Show automation details
ha-automation show automation.my_automation

# Update automation (shows current config)
ha-automation update my_automation_123

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

# Validate YAML file (for reference only)
ha-automation validate my_automation.yaml

# Test connection
ha-automation test
```

## Summary

This toolkit provides a clean API layer between AI assistants and Home Assistant. The AI assistant's job is to:

1. **Understand** user's natural language description
2. **Discover** devices using `DeviceDiscovery`
3. **Build** automation configuration dictionary
4. **Create** automation via `manager.create_automation(config)`
5. **Verify** automation was created successfully

The toolkit handles all the technical details:
- ✅ Home Assistant API communication
- ✅ Device discovery and search
- ✅ Configuration validation
- ✅ Automation creation and management
- ✅ Error handling and retry logic

**Remember**: Always use the API to create automations - it's fast, reliable, and fully automated!
