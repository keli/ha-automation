# Home Assistant Automation Management

A Python CLI and library for managing Home Assistant automations programmatically.

**Designed for AI Assistants**: This toolkit provides clean APIs that AI assistants (like Claude Code, GitHub Copilot) can use to help users create and manage Home Assistant automations from natural language descriptions.

## Architecture

```
User (natural language) → AI Assistant → Python Toolkit → Home Assistant
```

The AI assistant understands what the user wants, and this toolkit provides the APIs to discover devices, generate automation configurations, and manage automations.

## Features

### Device Discovery & Search
- 🔍 Discover all devices in your Home Assistant
- 🔎 Search devices by name (supports Chinese and English)
- 🏷️ Filter by domain (light, sensor, switch, etc.)
- 📍 Filter by area/room
- 💾 Smart caching for performance

### Automation YAML Generation (Primary Feature)
- 📝 **Generate automation YAML from natural language descriptions**
- 🤖 **AI-friendly API for automation configuration**
- ✅ Validate automation structure
- 🎨 Beautiful YAML formatting with proper syntax
- 🌏 Support for Chinese and English
- 📋 Copy-paste ready output

### Automation Management
- 📋 List and view automations with detailed information
- ⚡ Enable/disable automations
- 🔄 Toggle automation states
- ▶️ Manually trigger automations
- 🔄 Reload automations from YAML

### Developer Experience
- 🎨 Beautiful terminal output with Rich
- 📊 JSON output for scripting
- 🐍 Python API for programmatic access
- 📚 Comprehensive documentation for AI assistants

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package in development mode:
```bash
pip install -e .
```

Once installed, the `ha-automation` CLI command will be available globally.

## Configuration

Create a `.env` file in the project root with your Home Assistant credentials:

```env
HA_URL=http://192.168.1.100:8123
HA_TOKEN=your_long_lived_access_token
```

### Getting a Long-Lived Access Token

1. Navigate to your Home Assistant profile page: `http://your-ha-url:8123/profile`
2. Scroll to the bottom to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Give it a name (e.g., "ha-automation")
5. Copy the token and add it to your `.env` file

## CLI Usage

### Test Connection

```bash
ha-automation test
```

### Device Discovery

```bash
# Discover and cache all devices
ha-automation discover

# Force refresh (ignore cache)
ha-automation discover --force

# Search for devices
ha-automation devices "motion"
ha-automation devices "走廊"  # Chinese search supported

# Filter by domain
ha-automation devices --type light
ha-automation devices --type sensor
ha-automation devices --type switch

# Filter by area
ha-automation devices --area "Living Room"

# JSON output
ha-automation devices --json

# Limit results
ha-automation devices --type light --limit 20
```

### List Automations

```bash
# List all automations
ha-automation list

# Filter by state
ha-automation list --state on
ha-automation list --state off

# Output as JSON
ha-automation list --json
```

### Show Automation Details

```bash
ha-automation show automation.my_automation
```

### Enable/Disable Automations

```bash
# Enable an automation
ha-automation enable automation.my_automation

# Disable an automation
ha-automation disable automation.my_automation

# Toggle automation state
ha-automation toggle automation.my_automation
```

### Trigger Automation

```bash
# Manually trigger an automation
ha-automation trigger automation.my_automation

# Trigger and skip conditions
ha-automation trigger automation.my_automation --skip-condition
```

### Delete Automation

```bash
# Delete automation (requires automation ID, not entity_id)
# Use 'show' command to find the automation ID first
ha-automation delete 1234567890

# Force delete without confirmation
ha-automation delete 1234567890 --force
```

### Reload Automations

```bash
# Reload all automations from YAML files
ha-automation reload
```

## Python API Usage

### Device Discovery

```python
from ha_automation import HAClient, DeviceDiscovery

# Initialize
client = HAClient()  # Reads from .env automatically
discovery = DeviceDiscovery(client)

# Discover all devices
devices = discovery.discover_all()
print(f"Found {len(devices)} devices")

# Search devices (supports Chinese and English)
motion_sensors = discovery.search("走廊 motion")
hallway_lights = discovery.search("hallway light")

# Get devices by domain
all_lights = discovery.get_lights()
all_sensors = discovery.get_sensors()
all_switches = discovery.get_switches()

# Get specific device types
motion_sensors = discovery.get_motion_sensors()
door_sensors = discovery.get_door_sensors()
temp_sensors = discovery.get_temperature_sensors()

# Filter by area
living_room_devices = discovery.get_by_area("Living Room")

# Access device information
for device in all_lights[:5]:
    print(f"{device.friendly_name}")
    print(f"  Entity ID: {device.entity_id}")
    print(f"  State: {device.state}")
    print(f"  Domain: {device.domain}")
```

### Automation Management

```python
from ha_automation import HAClient, AutomationManager

# Initialize client (reads from .env automatically)
client = HAClient()
manager = AutomationManager(client)

# List all automations
automations = manager.list_automations()
for auto in automations:
    print(f"{auto.entity_id}: {auto.state} - {auto.friendly_name}")

# Filter by state
enabled = manager.list_automations(state_filter="on")
disabled = manager.list_automations(state_filter="off")

# Get specific automation
auto = manager.get_automation("automation.my_automation")
print(f"State: {auto.state}")
print(f"Last triggered: {auto.last_triggered}")

# Enable/disable
manager.turn_on_automation("automation.my_automation")
manager.turn_off_automation("automation.my_automation")

# Toggle
manager.toggle_automation("automation.my_automation")

# Trigger manually
manager.trigger_automation("automation.my_automation", skip_condition=True)

# Delete (requires automation ID)
automation_id = auto.automation_id
if automation_id:
    manager.delete_automation(automation_id)

# Reload all automations
manager.reload_automations()
```

### Generate Automation YAML (Recommended Method)

**Important**: Home Assistant does NOT provide a standard API for creating automations programmatically. The `/api/config/automation/config` REST endpoint is an internal UI endpoint that is not guaranteed to exist.

**The official Home Assistant approach is YAML files.** This toolkit makes YAML generation easy:

```python
import yaml
from ha_automation import HAClient, DeviceDiscovery

# Initialize and discover devices
client = HAClient()
discovery = DeviceDiscovery(client)
discovery.discover_all()

# Find devices
motion = discovery.search("hallway motion")[0]
light = discovery.search("hallway light")[0]

# Build automation configuration
config = {
    "id": "night_hallway_light",
    "alias": "夜间走廊照明",
    "description": "Turn on hallway light when motion detected at night",
    "trigger": [{
        "platform": "state",
        "entity_id": motion.entity_id,
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

# Generate YAML
yaml_output = yaml.dump([config], default_flow_style=False, allow_unicode=True)
print(yaml_output)

# User can then copy this to their automations.yaml file
# and reload automations in Home Assistant
```

See [examples/generate_automation_yaml.py](examples/generate_automation_yaml.py) for a complete working example.

### Custom Connection

```python
# Specify credentials manually (instead of .env)
client = HAClient(
    url="http://192.168.1.100:8123",
    token="your_token_here"
)
manager = AutomationManager(client)
```

## Documentation

- **[README.md](README.md)** - Overview and quick start (this file)
- **[AI_GUIDE.md](AI_GUIDE.md)** - ⭐ **Complete guide for AI assistants with YAML workflow**

## Project Structure

```
ha-automation/
├── .env                          # Environment variables (not in git)
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Package configuration
├── README.md                     # This file
├── AI_GUIDE.md                   # Guide for AI assistants
├── CHANGELOG.md                  # Version history
├── ha_automation/
│   ├── __init__.py              # Package exports
│   ├── client.py                # Home Assistant API client wrapper
│   ├── models.py                # Data models (Pydantic)
│   ├── device_discovery.py      # Device discovery and search
│   ├── automation_manager.py   # Core automation operations (NEW: YAML helpers!)
│   └── cli.py                   # CLI interface (NEW: generate-yaml, validate!)
└── examples/
    ├── example_automations.py   # Example usage scripts
    ├── generate_automation_yaml.py  # YAML generation example (UPDATED!)
    ├── improved_yaml_workflow.py    # Complete workflow examples (NEW!)
    └── ai_usage_example.py      # AI assistant usage example
```

## Examples

See the [examples](examples/) directory for more detailed usage examples.

## For AI Assistants

This toolkit is designed to be used by AI assistants to help users create and manage Home Assistant automations from natural language descriptions.

**See [AI_GUIDE.md](AI_GUIDE.md)** for comprehensive documentation including:
- Quick start guide for AI assistants
- Common automation patterns with code examples
- Home Assistant trigger/condition/action reference
- Error handling and best practices
- Full workflow examples

Example workflow:
1. User describes automation in natural language (Chinese or English)
2. AI assistant uses `DeviceDiscovery` to find relevant devices
3. AI assistant generates automation configuration dictionary
4. AI assistant generates YAML output for user to add to Home Assistant
5. User copies YAML to automations.yaml and reloads

Run the example:
```bash
python examples/generate_automation_yaml.py
```

## Requirements

- Python 3.8+
- Home Assistant instance with REST API enabled
- Long-lived access token

## Dependencies

- `python-dotenv` - Environment variable management
- `click` - CLI framework
- `rich` - Beautiful terminal output
- `pydantic` - Data validation and models
- `requests` - HTTP library
- `pyyaml` - YAML generation (optional)

## Important: How Home Assistant Automation Creation Works

**The official Home Assistant way: YAML files + reload service**

This toolkit embraces the official approach:

**What this toolkit does:**
- ✅ Device discovery and intelligent search
- ✅ Generate perfectly formatted automation YAML
- ✅ Manage existing automations (list, enable/disable, trigger, reload)
- ✅ Validate automation configurations
- ✅ Provide AI-friendly APIs for natural language → YAML conversion

**What you do:**
1. Use this toolkit to generate YAML
2. Copy the YAML to your `automations.yaml` file
3. Reload automations (via this toolkit's `reload` command or HA UI)


## Troubleshooting

### Connection Issues

If you get connection errors:
1. Verify your `HA_URL` is correct and accessible
2. Check that your access token is valid
3. Ensure Home Assistant's REST API is enabled
4. Test with: `ha-automation test`

### Authentication Errors

If you get 401 Unauthorized:
1. Verify your token hasn't expired (tokens last 10 years)
2. Try generating a new long-lived access token
3. Check that the token is correctly set in `.env`

### Automation Not Found

If an automation isn't found:
1. Check the entity_id is correct (should start with `automation.`)
2. Run `ha-automation list` to see all available automations
3. Verify the automation exists in Home Assistant

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
