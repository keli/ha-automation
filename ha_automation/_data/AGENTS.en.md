# AI Assistant Guide for Home Assistant Automation Toolkit

## Key Rules

### 1. Always use the toolkit API

```python
from ha_automation import HAClient, DeviceDiscovery, AutomationManager

client = HAClient()       # reads ~/.config/ha-automation/config automatically
discovery = DeviceDiscovery(client)
manager = AutomationManager(client)
```

- Use `HAClient` to query device states, logs, etc.
- Use `manager.create_or_update(config)` to create/update automations (idempotent)
- Do NOT use raw `requests` / `curl` to call HA REST API directly
- Do NOT generate YAML for the user to paste manually

### 2. Use stable IDs (no timestamps)

```python
# Correct
{"id": "night_hallway_light", ...}
manager.create_or_update(config)   # idempotent, safe to re-run

# Wrong
{"id": f"automation_{int(time.time())}", ...}  # creates duplicates every run
```

### 3. File locations

- Automation scripts -> `automations/` directory in this project
- HA connection config -> `.ha-config` in project root (contains token, gitignored - **do not read or modify**)

`ha-automation sync` auto-detects the `automations/` subdirectory under the current directory.

### 4. Verify devices and state semantics before scripting (required)

- Before creating/updating any automation script, you must first inspect devices that match user intent
- Run at least once: `ha-automation devices "<keyword>"` (run multiple keywords when needed)
- For candidate entities, verify:
  - correct `entity_id`
  - matching `domain` (`sensor` / `switch` / `binary_sensor`, etc.)
  - state semantics match the requirement (for example, whether "bright" means a text state, `on`, or a numeric threshold)
- Do not write conditions based on name guessing alone
- If names are ambiguous, hardcode the confirmed `entity_id` in script with a short comment

---

## Standard Workflow

```python
# 1. Discover devices
devices = discovery.discover_all()
lights = discovery.get_lights()
sensors = discovery.get_motion_sensors()
results = discovery.search("hallway")
by_domain = discovery.get_by_domain('switch')
by_area = discovery.get_by_area("Living Room")

# 2. Build config (stable ID)
config = {
    "id": "my_automation",
    "alias": "Automation name",
    "description": "Description",
    "trigger": [...],
    "condition": [...],   # optional
    "action": [...],
    "mode": "single"      # single / restart / queued / parallel
}

# 3. Create or update
automation_id, was_created = manager.create_or_update(config)
print(f"{'Created' if was_created else 'Updated'}: automation.{automation_id}")
```

Minimum validation flow before script changes (required):

1. Use `ha-automation devices "<keyword>"` to identify candidate entities
2. Use `client.get_states(entity_id="...")` to verify state values and attributes
3. Implement trigger/condition/action only after aligning semantics with user intent

---

## HA Config Reference

### Trigger

```python
# State change
{"platform": "state", "entity_id": "...", "to": "on", "from": "off", "for": "00:05:00"}

# Time
{"platform": "time", "at": "22:00:00"}

# Numeric threshold
{"platform": "numeric_state", "entity_id": "...", "above": 26, "below": 20}

# Template
{"platform": "template", "value_template": "{{ states('sensor.temp') | float > 25 }}"}

# Sun
{"platform": "sun", "event": "sunset", "offset": "-00:30:00"}

# event-domain entities (e.g. Xiaomi wireless buttons): use state trigger, NOT event trigger
{"platform": "state", "entity_id": "event.xiaomi_xxx_click"}
```

### Condition

```python
{"condition": "time", "after": "22:00:00", "before": "06:00:00", "weekday": ["mon","tue"]}
{"condition": "state", "entity_id": "...", "state": "off"}
{"condition": "numeric_state", "entity_id": "...", "above": 20, "below": 30}
{"condition": "template", "value_template": "{{ is_state('sun.sun', 'below_horizon') }}"}
{"condition": "sun", "after": "sunset", "after_offset": "-01:00:00"}
```

### Action

```python
# Service calls
{"service": "light.turn_on", "target": {"entity_id": "light.xxx"}, "data": {"brightness_pct": 80}}
{"service": "switch.turn_off", "target": {"entity_id": ["switch.a", "switch.b"]}}
{"service": "notify.notify", "data": {"message": "...", "title": "..."}}
{"service": "climate.set_temperature", "target": {"entity_id": "..."}, "data": {"temperature": 24}}

# Delay
{"delay": "00:05:00"}

# Conditional branch
{"choose": [{"conditions": [...], "sequence": [...]}], "default": [...]}
```

---

## CLI Commands

```bash
ha-automation scripts                        # list local scripts and their enabled state
ha-automation script-disable <script>        # disable a script (skipped during sync)
ha-automation script-enable <script>         # enable a script
ha-automation run <script>                   # run a single script

ha-automation sync                           # sync all enabled scripts to HA
ha-automation sync --dry-run                 # preview changes

ha-automation discover                       # discover and cache devices
ha-automation devices "<keyword>"            # search devices

ha-automation list                           # list all automations
ha-automation show automation.xxx            # show details
ha-automation trigger automation.xxx         # manually trigger
ha-automation enable/disable automation.xxx  # enable/disable
ha-automation delete <id>                    # delete
ha-automation reload                         # reload all automations
ha-automation test                           # test connection

ha-automation logbook                        # logbook: last 24 hours
ha-automation logbook -e automation.xxx      # filter by entity
ha-automation logbook --hours 48             # custom time window
```

---

## Notes

- **Xiaomi event-domain entities** (wireless buttons): use `platform: state`, NOT `platform: event` with `event_type: xiaomi_home_event`
- Query HA state with `client.get_states(entity_id="...")`, not bash + requests
- When device names are ambiguous, hardcode the `entity_id` directly with a comment explaining its purpose
