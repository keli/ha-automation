"""Core automation management operations."""

from typing import List, Optional, Dict, Any
import requests
from .client import HAClient
from .models import AutomationState, AutomationInfo


class AutomationManager:
    """Manages Home Assistant automations."""

    def __init__(self, client: HAClient):
        """
        Initialize AutomationManager.

        Args:
            client: HAClient instance
        """
        self.client = client

    def list_automations(self, state_filter: Optional[str] = None) -> List[AutomationState]:
        """
        List all automations.

        Args:
            state_filter: Optional filter by state ('on' or 'off')

        Returns:
            List of AutomationState objects
        """
        try:
            # Get all states
            all_states = self.client.get_states()

            # Filter to only automation domain
            automations = [
                state for state in all_states
                if state.get('entity_id', '').startswith('automation.')
            ]

            # Convert to AutomationState objects
            automation_states = []
            for state_dict in automations:
                try:
                    auto_state = AutomationState.from_ha_state(state_dict)

                    # Apply state filter if specified
                    if state_filter is None or auto_state.state == state_filter:
                        automation_states.append(auto_state)
                except Exception as e:
                    print(f"Warning: Failed to parse automation {state_dict.get('entity_id')}: {e}")
                    continue

            return automation_states
        except Exception as e:
            raise RuntimeError(f"Failed to list automations: {e}")

    def get_automation(self, entity_id: str) -> AutomationState:
        """
        Get details of a specific automation.

        Args:
            entity_id: Automation entity ID (e.g., automation.my_automation)

        Returns:
            AutomationState object

        Raises:
            ValueError: If automation not found
        """
        # Ensure entity_id has automation prefix
        if not entity_id.startswith('automation.'):
            entity_id = f'automation.{entity_id}'

        try:
            state = self.client.get_states(entity_id=entity_id)
            if not state:
                raise ValueError(f"Automation not found: {entity_id}")

            return AutomationState.from_ha_state(state)
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ValueError(f"Automation not found: {entity_id}")
            raise RuntimeError(f"Failed to get automation {entity_id}: {e}")

    def turn_on_automation(self, entity_id: str) -> bool:
        """
        Enable an automation.

        Args:
            entity_id: Automation entity ID

        Returns:
            True if successful
        """
        # Ensure entity_id has automation prefix
        if not entity_id.startswith('automation.'):
            entity_id = f'automation.{entity_id}'

        try:
            self.client.call_service(
                domain="automation",
                service="turn_on",
                service_data={"entity_id": entity_id}
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to turn on automation {entity_id}: {e}")

    def turn_off_automation(self, entity_id: str) -> bool:
        """
        Disable an automation.

        Args:
            entity_id: Automation entity ID

        Returns:
            True if successful
        """
        # Ensure entity_id has automation prefix
        if not entity_id.startswith('automation.'):
            entity_id = f'automation.{entity_id}'

        try:
            self.client.call_service(
                domain="automation",
                service="turn_off",
                service_data={"entity_id": entity_id}
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to turn off automation {entity_id}: {e}")

    def toggle_automation(self, entity_id: str) -> bool:
        """
        Toggle an automation on/off.

        Args:
            entity_id: Automation entity ID

        Returns:
            True if successful
        """
        # Ensure entity_id has automation prefix
        if not entity_id.startswith('automation.'):
            entity_id = f'automation.{entity_id}'

        try:
            self.client.call_service(
                domain="automation",
                service="toggle",
                service_data={"entity_id": entity_id}
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to toggle automation {entity_id}: {e}")

    def trigger_automation(self, entity_id: str, skip_condition: bool = False) -> bool:
        """
        Manually trigger an automation.

        Args:
            entity_id: Automation entity ID
            skip_condition: Whether to skip condition checks

        Returns:
            True if successful
        """
        # Ensure entity_id has automation prefix
        if not entity_id.startswith('automation.'):
            entity_id = f'automation.{entity_id}'

        try:
            service_data = {"entity_id": entity_id}
            if skip_condition:
                service_data["skip_condition"] = True

            self.client.call_service(
                domain="automation",
                service="trigger",
                service_data=service_data
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to trigger automation {entity_id}: {e}")

    def delete_automation(self, automation_id: str) -> bool:
        """
        Delete an automation.

        Note: This uses an undocumented API endpoint that may change in future HA versions.

        Args:
            automation_id: Automation ID (not entity_id, but the 'id' field)

        Returns:
            True if successful
        """
        # Build the URL for the delete endpoint
        url = f"{self.client.url}/api/config/automation/config/{automation_id}"

        headers = {
            "Authorization": f"Bearer {self.client.token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.delete(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                raise ValueError(f"Automation not found: {automation_id}")
            else:
                raise RuntimeError(
                    f"Failed to delete automation (HTTP {response.status_code}): "
                    f"{response.text}"
                )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to delete automation {automation_id}: {e}")

    def reload_automations(self) -> bool:
        """
        Reload all automations from YAML configuration.

        Returns:
            True if successful
        """
        try:
            self.client.call_service(
                domain="automation",
                service="reload"
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to reload automations: {e}")

    def get_automation_id(self, entity_id: str) -> Optional[str]:
        """
        Get the automation ID from entity_id.

        Args:
            entity_id: Automation entity ID

        Returns:
            Automation ID or None if not found
        """
        try:
            state = self.get_automation(entity_id)
            return state.automation_id
        except Exception:
            return None

    def create_automation(self, config: Dict[str, Any]) -> str:
        """
        Create new automation from configuration dictionary using Home Assistant API.

        Args:
            config: Automation configuration with:
                - id: unique ID (required)
                - alias: name (required)
                - trigger: list of triggers (required)
                - action: list of actions (required)
                - condition: optional conditions
                - description: optional description
                - mode: optional mode (default: single)

        Returns:
            automation_id (the 'id' field from config)

        Raises:
            ValueError: If required fields are missing
            RuntimeError: If creation fails

        Example:
            >>> config = {
            ...     "id": "my_automation_123",
            ...     "alias": "Night Light",
            ...     "trigger": [{"platform": "state", "entity_id": "binary_sensor.motion", "to": "on"}],
            ...     "action": [{"service": "light.turn_on", "target": {"entity_id": "light.hallway"}}],
            ...     "mode": "single"
            ... }
            >>> manager.create_automation(config)
            'my_automation_123'
        """
        # Validate required fields
        self.validate_config(config)

        try:
            # Create automation via API
            self.client.create_automation(config)

            # Reload automations to make it visible immediately
            self.reload_automations()

            return config['id']
        except Exception as e:
            raise RuntimeError(f"Failed to create automation: {e}")

    def update_automation(self, automation_id: str, config: Dict[str, Any]) -> bool:
        """
        Update existing automation configuration using Home Assistant API.

        Args:
            automation_id: Automation ID (not entity_id)
            config: Updated automation configuration

        Returns:
            True if successful

        Raises:
            RuntimeError: If update fails
        """
        # Validate config structure
        self.validate_config(config)

        try:
            self.client.update_automation(automation_id, config)
            self.reload_automations()
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to update automation {automation_id}: {e}")

    def _find_automation_by_id(self, automation_id: str) -> Optional[str]:
        """
        Find automation entity_id by its automation_id attribute.

        This handles cases where entity_id doesn't match the configured id
        (e.g., when Chinese alias is converted to pinyin by Home Assistant).

        Args:
            automation_id: The automation ID from config

        Returns:
            entity_id if found, None otherwise
        """
        try:
            all_automations = self.list_automations()
            for auto in all_automations:
                if auto.automation_id == automation_id:
                    return auto.entity_id
            return None
        except Exception:
            return None

    def create_or_update(self, config: Dict[str, Any]) -> tuple[str, bool]:
        """
        Create new automation or update if it already exists (idempotent operation).

        This method checks if an automation with the given ID exists:
        - If exists: updates it with the new configuration
        - If not exists: creates a new automation

        This is the recommended method for sync workflows where scripts should
        be idempotent and not create duplicates.

        Args:
            config: Automation configuration with required 'id' field

        Returns:
            Tuple of (automation_id, was_created) where:
                - automation_id: The automation ID
                - was_created: True if created, False if updated

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If operation fails

        Example:
            >>> config = {
            ...     "id": "my_automation",  # Fixed ID
            ...     "alias": "Night Light",
            ...     "trigger": [...],
            ...     "action": [...]
            ... }
            >>> automation_id, created = manager.create_or_update(config)
            >>> if created:
            ...     print(f"Created: {automation_id}")
            ... else:
            ...     print(f"Updated: {automation_id}")
        """
        # Validate config first
        self.validate_config(config)

        automation_id = config['id']

        # Try to find automation by its automation_id attribute
        # This handles cases where entity_id != "automation.{id}" due to alias conversion
        entity_id = self._find_automation_by_id(automation_id)
        if not entity_id:
            # Fallback: construct expected entity_id
            entity_id = f"automation.{automation_id}"

        try:
            # Check if automation exists
            existing = self.get_automation(entity_id)

            # Automation exists - update it
            self.update_automation(automation_id, config)
            return automation_id, False  # Not created (updated)

        except ValueError:
            # Automation doesn't exist - create it
            self.create_automation(config)
            return automation_id, True  # Created
        except Exception as e:
            raise RuntimeError(f"Failed to create or update automation {automation_id}: {e}")


    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate automation configuration structure.

        Args:
            config: Automation configuration dictionary

        Returns:
            True if valid

        Raises:
            ValueError: If configuration is invalid
        """
        # Required fields
        required_fields = ['id', 'alias', 'trigger', 'action']
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate trigger is a list
        if not isinstance(config['trigger'], list):
            raise ValueError("'trigger' must be a list")

        if len(config['trigger']) == 0:
            raise ValueError("'trigger' must have at least one trigger")

        # Validate action is a list
        if not isinstance(config['action'], list):
            raise ValueError("'action' must be a list")

        if len(config['action']) == 0:
            raise ValueError("'action' must have at least one action")

        # Validate condition if present
        if 'condition' in config:
            if not isinstance(config['condition'], list):
                raise ValueError("'condition' must be a list if provided")

        # Validate mode if present
        if 'mode' in config:
            valid_modes = ['single', 'restart', 'queued', 'parallel']
            if config['mode'] not in valid_modes:
                raise ValueError(
                    f"'mode' must be one of {valid_modes}, got '{config['mode']}'"
                )

        return True

