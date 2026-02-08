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
            table.add_column("Entity ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="white")
            table.add_column("State", justify="center")
            table.add_column("Mode", justify="center", style="magenta")
            table.add_column("Last Triggered", style="yellow")

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
            console.print(f"\n[dim]Total: {len(automations)} automation(s)[/dim]")

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
[cyan]Entity ID:[/cyan] {automation.entity_id}
[cyan]Name:[/cyan] {automation.friendly_name or '—'}
[cyan]State:[/cyan] {state_text}
[cyan]Mode:[/cyan] {automation.mode}
[cyan]Current Runs:[/cyan] {automation.current}
[cyan]Max Runs:[/cyan] {automation.max or 'N/A'}
[cyan]Last Triggered:[/cyan] {format_datetime(automation.last_triggered)}
[cyan]Automation ID:[/cyan] {automation.automation_id or 'N/A'}
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
        with console.status(f"[cyan]Enabling {entity_id}..."):
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
        with console.status(f"[cyan]Disabling {entity_id}..."):
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
        with console.status(f"[cyan]Toggling {entity_id}..."):
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
        with console.status(f"[cyan]Triggering {entity_id}..."):
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
            console.print("[yellow]Deletion cancelled.[/yellow]")
            return

    try:
        with console.status(f"[cyan]Deleting automation {automation_id}..."):
            manager.delete_automation(automation_id)
        console.print(f"[green]✓[/green] Automation deleted: {automation_id}")
        console.print("[yellow]Note:[/yellow] Run 'reload' command to refresh automations")
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
        with console.status("[cyan]Reloading automations..."):
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
        console.print(f"[cyan]Testing connection to {client.url}...[/cyan]")

        with console.status("[cyan]Connecting..."):
            client.test_connection()
            config = client.get_config()

        console.print(f"[green]✓[/green] Connected successfully!")
        console.print(f"[cyan]Location:[/cyan] {config.get('location_name', 'Unknown')}")
        console.print(f"[cyan]Version:[/cyan] {config.get('version', 'Unknown')}")
        console.print(f"[cyan]Host:[/cyan] {client.host}:{client.port}")

    except Exception as e:
        console.print(f"[red]✗[/red] Connection failed: {e}")
        raise click.Abort()


@main.command()
@click.option('--force', is_flag=True, help='Force refresh from Home Assistant')
def discover(force: bool):
    """Discover and cache all devices from Home Assistant."""
    try:
        client = HAClient()
        discovery = DeviceDiscovery(client)

        with console.status("[cyan]Discovering devices..."):
            devices = discovery.discover_all(force_refresh=force)

        # Group by domain
        by_domain = {}
        for device in devices:
            by_domain.setdefault(device.domain, []).append(device)

        console.print(f"\n[green]✓[/green] Found {len(devices)} devices:")
        for domain in sorted(by_domain.keys()):
            devs = by_domain[domain]
            console.print(f"  • {len(devs):3d} {domain}")

        console.print(f"\n[dim]Cache saved to device_cache.json[/dim]")

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
            table.add_column("Entity ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="white")
            table.add_column("Domain", style="magenta")
            table.add_column("State", style="yellow")
            table.add_column("Area", style="blue")

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
            console.print(f"\n[dim]Showing {shown} of {total} devices[/dim]")
            if total > limit:
                console.print(f"[dim]Use --limit {total} to see all results[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@main.command('generate-yaml')
@click.option('--motion-sensor', help='Motion sensor entity ID')
@click.option('--light', help='Light entity ID')
@click.option('--brightness', type=int, default=30, help='Light brightness percentage (default: 30)')
@click.option('--time-after', default='22:00:00', help='Active after time (default: 22:00:00)')
@click.option('--time-before', default='06:00:00', help='Active before time (default: 06:00:00)')
@click.option('--name', help='Automation name/alias')
@click.option('--id', 'automation_id', help='Automation ID (auto-generated if not provided)')
def generate_yaml(motion_sensor, light, brightness, time_after, time_before, name, automation_id):
    """
    Generate automation YAML from parameters.

    This is a simple example command. For complex automations,
    use the Python API directly.

    Example:
        ha-automation generate-yaml \\
            --motion-sensor binary_sensor.hallway_motion \\
            --light light.hallway \\
            --name "Night Hallway Light" \\
            --brightness 30
    """
    import time

    manager = get_manager()

    # Generate auto ID if not provided
    if not automation_id:
        automation_id = f"auto_generated_{int(time.time())}"

    # Generate auto name if not provided
    if not name:
        name = f"Auto Generated {automation_id}"

    try:
        # Build configuration
        config = {
            "id": automation_id,
            "alias": name,
            "description": f"Generated by ha-automation CLI",
            "mode": "single"
        }

        # Add trigger if motion sensor provided
        if motion_sensor:
            config["trigger"] = [{
                "platform": "state",
                "entity_id": motion_sensor,
                "to": "on"
            }]
        else:
            config["trigger"] = []

        # Add time condition if specified
        if time_after or time_before:
            config["condition"] = [{
                "condition": "time",
                "after": time_after,
                "before": time_before
            }]

        # Add action if light provided
        if light:
            config["action"] = [{
                "service": "light.turn_on",
                "target": {"entity_id": light},
                "data": {"brightness_pct": brightness}
            }]
        else:
            config["action"] = []

        # Validate
        try:
            manager.validate_config(config)
        except ValueError as e:
            console.print(f"[yellow]Warning:[/yellow] {e}")
            console.print("[yellow]Generated YAML may be incomplete.[/yellow]\n")

        # Generate YAML
        yaml_output = manager.generate_yaml(config)

        # Print with instructions
        manager.print_yaml_instructions(yaml_output)

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

        console.print(f"\n[cyan]Validating {len(configs)} automation(s)...[/cyan]\n")

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


if __name__ == '__main__':
    main()
