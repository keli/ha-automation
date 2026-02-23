# Home Assistant Automation Management

A Python CLI and library for managing Home Assistant automations programmatically.

**Designed for AI Assistants**: This toolkit provides clean APIs that AI assistants (like Claude Code, Codex) can use to help users create and manage Home Assistant automations from natural language descriptions.

## Architecture

```
User (natural language) → AI Assistant → Python Toolkit → Home Assistant
```

## Features

- 🔍 Device discovery and search (supports Chinese and English)
- 🚀 Create and update automations directly via Home Assistant REST API
- 📋 List, enable/disable, trigger, and delete automations
- 🔄 Sync a directory of Python automation scripts to Home Assistant
- 🎨 Beautiful terminal output with Rich

## Installation

```bash
pip install ha-automation
```

Once installed, the `ha-automation` CLI command will be available globally.

## Quick Start

```bash
# Initialize a new workspace
ha-automation init

# Follow the prompts to configure your HA URL and token,
# then sync your scripts to Home Assistant
ha-automation sync
```

## Configuration

Credentials are stored in `.ha-config` in your workspace directory (created by `ha-automation init`), or in `~/.config/ha-automation/config` as a fallback.

```
HA_URL=http://192.168.1.100:8123
HA_TOKEN=your_long_lived_access_token
```

### Getting a Long-Lived Access Token

1. Go to your Home Assistant profile: `http://your-ha-url:8123/profile`
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token", give it a name, and copy it

## CLI Usage

### Workspace

```bash
# Initialize a new automation workspace
ha-automation init [directory]

# Test connection to Home Assistant
ha-automation test
```

### Device Discovery

```bash
ha-automation discover
ha-automation discover --force          # Force refresh cache

ha-automation devices "motion"
ha-automation devices "走廊"            # Chinese search supported
ha-automation devices --type light
ha-automation devices --area "Living Room"
ha-automation devices --json
```

### Automations

```bash
ha-automation list
ha-automation list --state on
ha-automation show automation.my_automation

# Enable/disable/toggle accept entity_id or automation_id
ha-automation enable my_automation_id
ha-automation disable automation.my_automation
ha-automation toggle my_automation_id
ha-automation trigger my_automation_id
ha-automation trigger my_automation_id --skip-condition

ha-automation delete 1234567890
ha-automation delete 1234567890 --force
ha-automation reload
```

### Scripts

```bash
# List local automation scripts and their status
ha-automation scripts
ha-automation scripts --directory /path/to/automations

# Run a single script
ha-automation run my_script.py

# Sync all enabled scripts to Home Assistant
ha-automation sync
ha-automation sync --dry-run
ha-automation sync --clean              # Remove orphaned automations

# Enable/disable a script (controls whether it's synced)
ha-automation script-enable my_script.py
ha-automation script-disable my_script.py
```

## Python API

```python
from ha_automation import HAClient, DeviceDiscovery, AutomationManager

client = HAClient()  # Reads credentials automatically
discovery = DeviceDiscovery(client)
manager = AutomationManager(client)

# Discover devices
discovery.discover_all()
lights = discovery.search("living room light")
motion = discovery.search("走廊 motion")

# Create or update an automation
config = {
    "id": "my_automation",
    "alias": "My Automation",
    "trigger": [{"platform": "state", "entity_id": motion[0].entity_id, "to": "on"}],
    "action": [{"service": "light.turn_on", "target": {"entity_id": lights[0].entity_id}}],
    "mode": "single"
}
automation_id, was_created = manager.create_or_update(config)
```

## For AI Assistants

See [AGENTS.md](AGENTS.md) for comprehensive documentation including automation patterns, trigger/condition/action reference, and workflow examples.

## Requirements

- Python 3.8+
- Home Assistant with REST API enabled
- Long-lived access token

## License

MIT License
