"""Command-line interface for Home Assistant automation management."""

import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from datetime import datetime
from typing import Optional

from .client import HAClient
from .automation_manager import AutomationManager
from .device_discovery import DeviceDiscovery


console = Console()


def get_manager() -> AutomationManager:
    """Create and return an AutomationManager instance."""
    try:
        client = HAClient()
        return AutomationManager(client)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


def format_datetime(dt: Optional[datetime]) -> str:
    """Format datetime for display."""
    if not dt:
        return "Never"

    now = datetime.now(dt.tzinfo)
    diff = now - dt

    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return "Just now"


@click.group()
@click.version_option(version="1.0.0")
def main():
    """Home Assistant automation management CLI."""
    pass


@main.command()
@click.option('--state', type=click.Choice(['on', 'off'], case_sensitive=False),
              help='Filter by state')
@click.option('--json', 'output_json', is_flag=True,
              help='Output as JSON')
def list(state: Optional[str], output_json: bool):
    """List all automations."""
    manager = get_manager()

    try:
        automations = manager.list_automations(state_filter=state)

        if output_json:
            # JSON output
            output = [
                {
                    "entity_id": auto.entity_id,
                    "state": auto.state,
                    "friendly_name": auto.friendly_name,
                    "last_triggered": auto.last_triggered.isoformat() if auto.last_triggered else None,
                    "mode": auto.mode,
                    "current": auto.current
                }
                for auto in automations
            ]
            console.print(json.dumps(output, indent=2))
        else:
            # Rich table output
            table = Table(title="Home Assistant Automations", box=box.ROUNDED)
            table.add_column("Entity ID", style="blue", no_wrap=True)
            table.add_column("Name", style="black")
            table.add_column("State", justify="center")
            table.add_column("Mode", justify="center", style="magenta")
            table.add_column("Last Triggered", style="dim")

            for auto in automations:
                state_style = "[green]ON[/green]" if auto.state == "on" else "[red]OFF[/red]"
                table.add_row(
                    auto.entity_id,
                    auto.friendly_name or "—",
                    state_style,
                    auto.mode,
                    format_datetime(auto.last_triggered)
                )

            console.print(table)
            console.print(f"\n[bright_black]Total: {len(automations)} automation(s)[/bright_black]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command()
@click.argument('entity_id')
@click.option('--json', 'output_json', is_flag=True,
              help='Output as JSON')
def show(entity_id: str, output_json: bool):
    """Show details of a specific automation."""
    manager = get_manager()

    try:
        automation = manager.get_automation(entity_id)

        if output_json:
            # JSON output
            output = {
                "entity_id": automation.entity_id,
                "state": automation.state,
                "friendly_name": automation.friendly_name,
                "last_triggered": automation.last_triggered.isoformat() if automation.last_triggered else None,
                "mode": automation.mode,
                "current": automation.current,
                "max": automation.max,
                "automation_id": automation.automation_id
            }
            console.print(json.dumps(output, indent=2))
        else:
            # Rich panel output
            state_color = "green" if automation.state == "on" else "red"
            state_text = f"[{state_color}]{automation.state.upper()}[/{state_color}]"

            info = f"""
[blue]Entity ID:[/blue] {automation.entity_id}
[blue]Name:[/blue] {automation.friendly_name or '—'}
[blue]State:[/blue] {state_text}
[blue]Mode:[/blue] {automation.mode}
[blue]Current Runs:[/blue] {automation.current}
[blue]Max Runs:[/blue] {automation.max or 'N/A'}
[blue]Last Triggered:[/blue] {format_datetime(automation.last_triggered)}
[blue]Automation ID:[/blue] {automation.automation_id or 'N/A'}
            """.strip()

            panel = Panel(info, title=f"Automation: {automation.friendly_name or entity_id}",
                         border_style=state_color, box=box.ROUNDED)
            console.print(panel)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command()
@click.argument('entity_id')
def enable(entity_id: str):
    """Enable an automation."""
    manager = get_manager()

    try:
        with console.status(f"[blue]Enabling {entity_id}..."):
            manager.turn_on_automation(entity_id)
        console.print(f"[green]✓[/green] Automation enabled: {entity_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command()
@click.argument('entity_id')
def disable(entity_id: str):
    """Disable an automation."""
    manager = get_manager()

    try:
        with console.status(f"[blue]Disabling {entity_id}..."):
            manager.turn_off_automation(entity_id)
        console.print(f"[green]✓[/green] Automation disabled: {entity_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command()
@click.argument('entity_id')
def toggle(entity_id: str):
    """Toggle an automation on/off."""
    manager = get_manager()

    try:
        with console.status(f"[blue]Toggling {entity_id}..."):
            manager.toggle_automation(entity_id)
        console.print(f"[green]✓[/green] Automation toggled: {entity_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command()
@click.argument('entity_id')
@click.option('--skip-condition', is_flag=True,
              help='Skip condition checks when triggering')
def trigger(entity_id: str, skip_condition: bool):
    """Manually trigger an automation."""
    manager = get_manager()

    try:
        with console.status(f"[blue]Triggering {entity_id}..."):
            manager.trigger_automation(entity_id, skip_condition=skip_condition)
        console.print(f"[green]✓[/green] Automation triggered: {entity_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command()
@click.argument('automation_id')
@click.option('--force', is_flag=True,
              help='Skip confirmation prompt')
def delete(automation_id: str, force: bool):
    """
    Delete an automation.

    Note: Requires the automation ID (not entity_id).
    Use 'show' command to find the automation ID.
    """
    manager = get_manager()

    if not force:
        if not click.confirm(f"Are you sure you want to delete automation '{automation_id}'?"):
            console.print("[dark_orange]Deletion cancelled.[/dark_orange]")
            return

    try:
        with console.status(f"[blue]Deleting automation {automation_id}..."):
            manager.delete_automation(automation_id)
        console.print(f"[green]✓[/green] Automation deleted: {automation_id}")
        console.print("[dark_orange]Note:[/dark_orange] Run 'reload' command to refresh automations")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command()
def reload():
    """Reload all automations from YAML configuration."""
    manager = get_manager()

    try:
        with console.status("[blue]Reloading automations..."):
            manager.reload_automations()
        console.print("[green]✓[/green] Automations reloaded successfully")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command()
def test():
    """Test connection to Home Assistant."""
    try:
        client = HAClient()
        console.print(f"[blue]Testing connection to {client.url}...[/blue]")

        with console.status("[blue]Connecting..."):
            client.test_connection()
            config = client.get_config()

        console.print(f"[green]✓[/green] Connected successfully!")
        console.print(f"[blue]Location:[/blue] {config.get('location_name', 'Unknown')}")
        console.print(f"[blue]Version:[/blue] {config.get('version', 'Unknown')}")
        console.print(f"[blue]Host:[/blue] {client.host}:{client.port}")

    except Exception as e:
        console.print(f"[red]✗[/red] Connection failed: {e}")
        raise click.Abort()


@main.command()
@click.option('--no-refresh', is_flag=True, help='Use cached data instead of refreshing from Home Assistant')
def discover(no_refresh: bool):
    """Discover and cache all devices from Home Assistant."""
    try:
        client = HAClient()
        discovery = DeviceDiscovery(client)

        with console.status("[blue]Discovering devices..."):
            devices = discovery.discover_all(force_refresh=not no_refresh)

        # Group by domain
        by_domain = {}
        for device in devices:
            by_domain.setdefault(device.domain, []).append(device)

        console.print(f"\n[green]✓[/green] Found {len(devices)} devices:")
        for domain in sorted(by_domain.keys()):
            devs = by_domain[domain]
            console.print(f"  • {len(devs):3d} {domain}")

        console.print("\n[bright_black]Cache saved to device_cache.json[/bright_black]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command()
@click.argument('query', required=False)
@click.option('--type', 'device_type', help='Filter by domain (light, sensor, switch, etc.)')
@click.option('--area', help='Filter by area name')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--limit', type=int, default=50, help='Maximum number of devices to display (default: 50)')
def devices(query: Optional[str], device_type: Optional[str], area: Optional[str], output_json: bool, limit: int):
    """Search and list devices."""
    try:
        client = HAClient()
        discovery = DeviceDiscovery(client)
        discovery.discover_all()

        # Apply filters
        if device_type:
            results = discovery.get_by_domain(device_type)
        elif area:
            results = discovery.get_by_area(area)
        elif query:
            results = discovery.search(query)
        else:
            results = discovery.devices

        if output_json:
            # JSON output
            output = [
                {
                    "entity_id": device.entity_id,
                    "friendly_name": device.friendly_name,
                    "domain": device.domain,
                    "state": device.state,
                    "device_class": device.device_class,
                    "area": device.area
                }
                for device in results[:limit]
            ]
            console.print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            # Rich table output
            table = Table(title="Devices", box=box.ROUNDED)
            table.add_column("Entity ID", style="blue", no_wrap=True)
            table.add_column("Name", style="black")
            table.add_column("Domain", style="magenta")
            table.add_column("State", style="dim")
            table.add_column("Area", style="dark_cyan")

            for device in results[:limit]:
                table.add_row(
                    device.entity_id,
                    device.friendly_name,
                    device.domain,
                    device.state,
                    device.area or "—"
                )

            console.print(table)

            total = len(results)
            shown = min(total, limit)
            console.print(f"\n[bright_black]Showing {shown} of {total} devices[/bright_black]")
            if total > limit:
                console.print(f"[bright_black]Use --limit {total} to see all results[/bright_black]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command('validate')
@click.argument('yaml_file', type=click.Path(exists=True))
def validate(yaml_file):
    """
    Validate automation YAML file.

    Example:
        ha-automation validate my_automation.yaml
    """
    import yaml as yaml_lib

    manager = get_manager()

    try:
        # Read YAML file
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml_lib.safe_load(f)

        # Handle both single automation and list
        configs = data if isinstance(data, list) else [data]

        console.print(f"\n[blue]Validating {len(configs)} automation(s)...[/blue]\n")

        all_valid = True
        for i, config in enumerate(configs, 1):
            try:
                manager.validate_config(config)
                automation_name = config.get('alias', config.get('id', f'#{i}'))
                console.print(f"✓ [green]{automation_name}[/green] - Valid")
            except ValueError as e:
                automation_name = config.get('alias', config.get('id', f'#{i}'))
                console.print(f"✗ [red]{automation_name}[/red] - {e}")
                all_valid = False

        console.print()
        if all_valid:
            console.print("[green]All automations are valid![/green]")
        else:
            console.print("[red]Some automations have errors.[/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command('run')
@click.argument('script_path', type=click.Path(exists=True))
def run(script_path):
    """
    Execute a Python automation script.

    The script should use the ha_automation API to create automations.
    This replaces the old YAML import workflow with a fully automated API approach.

    Example:
        ha-automation run my_automations/door_unlock_lights.py
    """
    import subprocess
    import sys
    from pathlib import Path

    script = Path(script_path)

    console.print(f"[blue]Running:[/blue] {script.name}\n")

    try:
        # Run the Python script
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=script.parent
        )

        # Display output
        if result.stdout:
            console.print(result.stdout)

        if result.stderr:
            console.print(f"[dark_orange]{result.stderr}[/dark_orange]")

        if result.returncode != 0:
            console.print(f"\n[red]Script exited with code {result.returncode}[/red]")
            raise click.Abort()
        else:
            console.print("\n[green]✓[/green] Script completed successfully")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command('create-from-template')
@click.argument('template_name',
                type=click.Choice(['motion-light', 'time-based', 'temperature-control',
                                 'door-alert', 'auto-off'], case_sensitive=False))
def create_from_template(template_name):
    """
    Create automation from a pre-built template.

    Templates:
    - motion-light: Turn on lights when motion detected
    - time-based: Execute actions at specific times
    - temperature-control: Control climate based on temperature
    - door-alert: Send notifications when door opens
    - auto-off: Auto turn off devices after duration

    Example:
        ha-automation create-from-template motion-light
    """
    import time

    client = HAClient()
    manager = AutomationManager(client)
    discovery = DeviceDiscovery(client)

    try:
        # Discover devices
        with console.status("[blue]Discovering devices..."):
            discovery.discover_all()

        console.print(f"\n[blue]Creating automation from template:[/blue] {template_name}\n")

        if template_name == 'motion-light':
            # Get motion sensors
            motion_sensors = discovery.get_motion_sensors()
            if not motion_sensors:
                console.print("[red]No motion sensors found[/red]")
                raise click.Abort()

            console.print("[blue]Available motion sensors:[/blue]")
            for i, sensor in enumerate(motion_sensors, 1):
                console.print(f"  {i}. {sensor.friendly_name} ({sensor.entity_id})")

            sensor_idx = click.prompt("Select motion sensor", type=int) - 1
            if not (0 <= sensor_idx < len(motion_sensors)):
                console.print("[red]Invalid selection[/red]")
                raise click.Abort()

            # Get lights
            lights = discovery.get_lights()
            if not lights:
                console.print("[red]No lights found[/red]")
                raise click.Abort()

            console.print("\n[blue]Available lights:[/blue]")
            for i, light in enumerate(lights[:20], 1):  # Limit to 20 for readability
                console.print(f"  {i}. {light.friendly_name} ({light.entity_id})")

            light_idx = click.prompt("Select light", type=int) - 1
            if not (0 <= light_idx < len(lights)):
                console.print("[red]Invalid selection[/red]")
                raise click.Abort()

            # Get parameters
            brightness = click.prompt("Brightness (0-100)", type=int, default=30)
            time_after = click.prompt("Active after time (HH:MM:SS)", default="22:00:00")
            time_before = click.prompt("Active before time (HH:MM:SS)", default="06:00:00")
            name = click.prompt("Automation name", default="Motion Activated Light")

            # Build config
            config = {
                "id": f"motion_light_{int(time.time())}",
                "alias": name,
                "description": f"Turn on {lights[light_idx].friendly_name} when {motion_sensors[sensor_idx].friendly_name} detects motion",
                "trigger": [{
                    "platform": "state",
                    "entity_id": motion_sensors[sensor_idx].entity_id,
                    "to": "on"
                }],
                "condition": [{
                    "condition": "time",
                    "after": time_after,
                    "before": time_before
                }],
                "action": [{
                    "service": "light.turn_on",
                    "target": {"entity_id": lights[light_idx].entity_id},
                    "data": {"brightness_pct": brightness}
                }],
                "mode": "single"
            }

        elif template_name == 'time-based':
            # Get lights
            lights = discovery.get_lights()
            if not lights:
                console.print("[red]No lights found[/red]")
                raise click.Abort()

            console.print("[blue]Available lights:[/blue]")
            for i, light in enumerate(lights[:20], 1):
                console.print(f"  {i}. {light.friendly_name} ({light.entity_id})")

            light_idx = click.prompt("Select light", type=int) - 1
            if not (0 <= light_idx < len(lights)):
                console.print("[red]Invalid selection[/red]")
                raise click.Abort()

            trigger_time = click.prompt("Trigger time (HH:MM:SS)", default="22:00:00")
            action = click.prompt("Action", type=click.Choice(['turn_on', 'turn_off']), default='turn_off')
            name = click.prompt("Automation name", default="Time Based Light Control")

            config = {
                "id": f"time_based_{int(time.time())}",
                "alias": name,
                "description": f"{action.replace('_', ' ').title()} {lights[light_idx].friendly_name} at {trigger_time}",
                "trigger": [{
                    "platform": "time",
                    "at": trigger_time
                }],
                "action": [{
                    "service": f"light.{action}",
                    "target": {"entity_id": lights[light_idx].entity_id}
                }],
                "mode": "single"
            }

        else:
            console.print(f"[dark_orange]Template '{template_name}' not yet implemented[/dark_orange]")
            console.print("[bright_black]Coming soon: temperature-control, door-alert, auto-off[/bright_black]")
            return

        # Create automation via API
        console.print("\n[blue]Creating automation...[/blue]")
        automation_id = manager.create_automation(config)
        console.print(f"[green]✓[/green] Created: automation.{automation_id}")

        # Verify
        auto = manager.get_automation(f"automation.{automation_id}")
        console.print(f"[green]✓[/green] Status: {auto.state}")
        console.print(f"[blue]Name:[/blue] {auto.friendly_name}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command('update')
@click.argument('automation_id')
def update(automation_id):
    """
    Interactively update an existing automation.

    Example:
        ha-automation update my_automation_123
    """
    import yaml as yaml_lib

    manager = get_manager()

    try:
        # Get current automation
        entity_id = automation_id if automation_id.startswith('automation.') else f"automation.{automation_id}"
        auto = manager.get_automation(entity_id)

        console.print(f"\n[blue]Current automation:[/blue] {auto.friendly_name}")
        console.print(f"[blue]Entity ID:[/blue] {auto.entity_id}")
        console.print(f"[blue]State:[/blue] {auto.state}")
        console.print()

        # Get automation config
        config_entity_id = auto.automation_id or automation_id.replace('automation.', '')
        response = manager.client._request("GET", f"/api/config/automation/config/{config_entity_id}")
        current_config = response.json()

        console.print("[blue]Current configuration:[/blue]")
        console.print(yaml_lib.dump(current_config, default_flow_style=False, allow_unicode=True))

        console.print("\n[dark_orange]Note:[/dark_orange] Interactive editing not yet implemented.")
        console.print("[bright_black]For now, use Python scripts with manager.update_automation()[/bright_black]")
        console.print("\nExample:")
        console.print("  config = {current_config}")
        console.print("  config['alias'] = 'New Name'")
        console.print(f"  manager.update_automation('{config_entity_id}', config)")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command('sync')
@click.option('--directory', '-d', default='my_automations',
              help='Directory containing automation scripts (default: my_automations)')
@click.option('--dry-run', is_flag=True,
              help='Show what would be done without making changes')
@click.option('--clean', is_flag=True,
              help='Remove automations from HA that no longer have corresponding scripts')
def sync(directory: str, dry_run: bool, clean: bool):
    """
    Synchronize my_automations/ scripts with Home Assistant.

    This command:
    1. Scans the directory for Python automation scripts
    2. Runs each script to create/update automations via API
    3. Optionally removes orphaned automations (with --clean)

    Examples:
        # Sync all scripts in my_automations/
        ha-automation sync

        # Preview changes without applying them
        ha-automation sync --dry-run

        # Sync and remove automations without scripts
        ha-automation sync --clean

        # Sync a different directory
        ha-automation sync --directory custom_automations
    """
    import subprocess
    import sys
    import re
    from pathlib import Path

    scripts_dir = Path.cwd() / directory

    if not scripts_dir.exists():
        console.print(f"[red]Directory not found:[/red] {scripts_dir}")
        raise click.Abort()

    # Find all Python scripts
    script_files = sorted(scripts_dir.glob('*.py'))

    if not script_files:
        console.print(f"[dark_orange]No Python scripts found in {directory}/[/dark_orange]")
        return

    console.print(f"\n[blue]Found {len(script_files)} automation script(s) in {directory}/[/blue]\n")

    # In dry-run mode, first get all existing automations
    automation_map = {}
    if dry_run:
        try:
            manager = get_manager()
            existing_automations = manager.list_automations()
            automation_map = {auto.automation_id: auto for auto in existing_automations if auto.automation_id}
        except Exception as e:
            console.print(f"[dark_orange]Warning: Could not fetch existing automations: {e}[/dark_orange]\n")

    # Track results
    succeeded = []
    failed = []

    for script in script_files:
        console.print(f"[blue]Processing:[/blue] {script.name}")

        if dry_run:
            # Parse script to extract automation ID and alias
            try:
                with open(script, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for "id": "..." pattern in the script
                id_matches = re.findall(r'"id"\s*:\s*"([^"]+)"', content)
                alias_matches = re.findall(r'"alias"\s*:\s*"([^"]+)"', content)

                if id_matches:
                    auto_id = id_matches[0]
                    auto_alias = alias_matches[0] if alias_matches else "Unknown"

                    if auto_id in automation_map:
                        # Automation exists - would be updated
                        existing = automation_map[auto_id]
                        state_style = "[green]ON[/green]" if existing.state == "on" else "[red]OFF[/red]"
                        console.print(f"  [dark_orange]Would UPDATE:[/dark_orange] automation.{auto_id}")
                        console.print(f"    Name: {auto_alias}")
                        console.print(f"    Current: {existing.friendly_name} (State: {state_style})")
                    else:
                        # New automation - would be created
                        console.print(f"  [green]Would CREATE:[/green] automation.{auto_id}")
                        console.print(f"    Name: {auto_alias}")
                else:
                    console.print("  [bright_black]Could not extract automation ID from script[/bright_black]")

            except Exception as e:
                console.print(f"  [red]✗[/red] Error parsing script: {e}")

            console.print()
            continue

        try:
            # Run the script from current directory (project root)
            # This ensures device_cache.json is found in the correct location
            result = subprocess.run(
                [sys.executable, str(script.absolute())],
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
                timeout=30
            )

            if result.returncode == 0:
                console.print("  [green]✓[/green] Success")
                # Show output from script
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            console.print(f"    {line}")
                succeeded.append(script.name)
            else:
                console.print(f"  [red]✗[/red] Failed (exit code {result.returncode})")
                if result.stderr:
                    console.print(f"    [bright_black]{result.stderr[:200]}[/bright_black]")
                failed.append(script.name)

        except subprocess.TimeoutExpired:
            console.print("  [red]✗[/red] Timeout (>30s)")
            failed.append(script.name)
        except Exception as e:
            console.print(f"  [red]✗[/red] Error: {e}")
            failed.append(script.name)

        console.print()

    # Summary
    console.print("=" * 70)
    console.print("[blue]Sync Summary:[/blue]")
    console.print(f"  [green]✓[/green] Succeeded: {len(succeeded)}")
    console.print(f"  [red]✗[/red] Failed: {len(failed)}")

    if failed:
        console.print("\n[dark_orange]Failed scripts:[/dark_orange]")
        for name in failed:
            console.print(f"  • {name}")

    # Clean orphaned automations if requested
    if clean and not dry_run:
        console.print("\n[blue]Checking for orphaned automations...[/blue]")

        try:
            manager = get_manager()
            all_automations = manager.list_automations()

            # Get script base names (without .py extension)
            script_names = {script.stem for script in script_files}

            # Find automations that might be orphaned
            # Heuristic: automation IDs that start with script names
            orphaned = []
            for auto in all_automations:
                auto_id = auto.automation_id or ""
                # Check if automation ID matches any script name pattern
                is_from_script = any(
                    auto_id.startswith(name.replace('_', '_').lower())
                    for name in script_names
                )

                if not is_from_script and auto_id:
                    # Check if it looks like it was created by our scripts
                    # (has timestamp suffix pattern)
                    if '_' in auto_id and auto_id.split('_')[-1].isdigit():
                        orphaned.append(auto)

            if orphaned:
                console.print(f"\n[dark_orange]Found {len(orphaned)} potentially orphaned automation(s):[/dark_orange]")
                for auto in orphaned:
                    console.print(f"  • {auto.friendly_name} ({auto.automation_id})")

                if click.confirm("\nRemove these orphaned automations?", default=False):
                    for auto in orphaned:
                        try:
                            manager.delete_automation(auto.automation_id)
                            console.print(f"  [green]✓[/green] Deleted: {auto.friendly_name}")
                        except Exception as e:
                            console.print(f"  [red]✗[/red] Failed to delete {auto.friendly_name}: {e}")

                    # Reload after deletions
                    console.print("\n[blue]Reloading automations...[/blue]")
                    manager.reload_automations()
                    console.print("[green]✓[/green] Reloaded")
            else:
                console.print("  [green]No orphaned automations found[/green]")

        except Exception as e:
            console.print(f"[red]Error during cleanup:[/red] {e}")

    console.print()


if __name__ == '__main__':
    main()
